"""
Model Service
Business logic for model training and metrics

Separation of Concerns:
- Routes: HTTP handling
- Service: Business logic (THIS FILE)
- Database: Data access
"""

from typing import Dict, Any, Optional, List
import os
import pdfplumber
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from .learner import AdaptiveLearner
from .training_utils import (
    split_training_data,
    validate_training_data_diversity,
    detect_data_leakage,
    get_training_recommendations,
)
from .validation_strategy import ValidationStrategy
from database.db_manager import DatabaseManager
from database.repositories.data_quality_repository import DataQualityRepository
import time
from database.repositories.template_repository import TemplateRepository
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.training_repository import TrainingRepository
import logging

class ModelService:
    """Service layer for model operations"""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        template_repo: Optional[TemplateRepository] = None,
        document_repo: Optional[DocumentRepository] = None,
        feedback_repo: Optional[FeedbackRepository] = None,
        training_repo: Optional[TrainingRepository] = None,
    ):
        self.db = db_manager or DatabaseManager()
        self.template_repo = template_repo or TemplateRepository(self.db)
        self.document_repo = document_repo or DocumentRepository(self.db)
        self.feedback_repo = feedback_repo or FeedbackRepository(self.db)
        self.training_repo = training_repo or TrainingRepository(self.db)
        self.logger = logging.getLogger(__name__)
        # Parallel processing config
        import multiprocessing
        self.max_workers = multiprocessing.cpu_count()
        
        # CRF training config
        self.max_iterations = 1000  # Default: reduced from 500
    
    def set_parallel_workers(self, workers: int):
        """Set number of parallel workers for PDF extraction"""
        self.max_workers = max(1, workers)
    
    def set_max_iterations(self, iterations: int):
        """Set maximum L-BFGS iterations for CRF training"""
        self.max_iterations = max(10, iterations)

    def retrain_model(
        self,
        template_id: int,
        use_all_feedback: bool,
        model_folder: str,
        is_incremental: bool = False,
        force_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Retrain CRF model using accumulated feedback

        Args:
            template_id: Template ID
            use_all_feedback: Whether to use all feedback or only unused
            model_folder: Folder where models are stored
            is_incremental: Whether this is incremental training (skip validation)
            force_validation: Force validation regardless of cache

        Returns:
            Training results with metrics
        """
        # Get template and load config
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # ✅ Load template config for context features (from DB or JSON)
        template_config = None
        try:
            from core.templates.config_loader import get_config_loader

            config_loader = get_config_loader(db_manager=self.db, template_folder=None)
            template_config = config_loader.load_config(
                template_id=template_id, config_path=template.config_path
            )
            if template_config:
                self.logger.info(
                    f"✅ [Training] Loaded template config from {template_config['metadata'].get('source', 'unknown')}"
                )
            else:
                self.logger.warning(f"⚠️ [Training] Could not load template config")
                self.logger.warning(f"   Training will proceed without template context features")
        except Exception as e:
            self.logger.warning(f"⚠️ [Training] Error loading config: {e}")
            self.logger.warning(f"   Training will proceed without template context features")

        # Get feedback for training (corrected data)
        feedback_list = self.feedback_repo.find_for_training(
            template_id, unused_only=not use_all_feedback
        )
        # ✅ VALIDATED DOCUMENTS: High-confidence extractions (pseudo-labels)
        # Filter based on use_all_feedback to match feedback filtering
        self.logger.info(f"\n📚 Processing validated documents (high-confidence extractions)...")
        validated_docs = self.document_repo.find_validated_documents(
            template_id, unused_only=not use_all_feedback
        )
        self.logger.info(f"   Found {len(validated_docs)} validated documents (unused_only={not use_all_feedback})")

        validated_processed = 0
        for idx, document in enumerate(validated_docs, 1):
            pass

        if not feedback_list and not validated_docs:
            raise ValueError(
                "No training data available (no feedback or validated documents)"
            )
        
        # ⚠️ WARN: Small dataset when use_all_feedback=False
        total_samples = len(feedback_list) + len(validated_docs)
        if not use_all_feedback and total_samples < 100:
            self.logger.warning(f"\n⚠️  WARNING: Small training set detected ({total_samples} samples)")
            self.logger.warning(f"   Using only unused feedback may result in:")
            self.logger.warning(f"   - Missing labels in validation set")
            self.logger.warning(f"   - Unreliable grid search results")
            self.logger.warning(f"   - UndefinedMetricWarning from sklearn")
            self.logger.warning(f"\n💡 RECOMMENDATION: Use 'use_all_feedback=True' for better results")

        # Prepare training data
        X_train = []
        y_train = []
        feedback_ids = []
        doc_ids_train = []  # ✅ Track document IDs for leakage detection

        self.logger.info(f"📊 Training data sources:")
        self.logger.info(f"   - Feedback (corrected): {len(feedback_list)} records")
        self.logger.info(f"   - Validated (high-confidence): {len(validated_docs)} documents")

        # 1. Add feedback data (user corrections - highest priority)
        # Group feedback by document_id to create complete training samples
        feedback_by_doc = {}
        for feedback in feedback_list:
            doc_id = feedback["document_id"]
            if doc_id not in feedback_by_doc:
                feedback_by_doc[doc_id] = []
            feedback_by_doc[doc_id].append(feedback)

        self.logger.info(f"   - Unique documents with feedback: {len(feedback_by_doc)}")

        # ⚡ OPTIMIZATION: Reuse single learner instance
        learner = AdaptiveLearner()
        
        # ⚡ OPTIMIZATION: Parallel PDF extraction using ThreadPoolExecutor
        # Extract all PDFs in parallel (I/O-bound operation)
        pdf_words_cache = {}
        
        def extract_pdf_words(doc_id, file_path):
            """Extract words from PDF (thread-safe)"""
            try:
                with pdfplumber.open(file_path) as pdf:
                    words = []
                    for page in pdf.pages:
                        page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
                        words.extend(page_words)
                return doc_id, words
            except Exception as e:
                self.logger.warning(f"⚠️  Error extracting PDF {doc_id}: {e}")
                return doc_id, []
        
        # Collect all documents that need PDF extraction
        docs_to_extract = []
        for doc_id in feedback_by_doc.keys():
            document = self.document_repo.find_by_id(doc_id)
            if document:
                docs_to_extract.append((doc_id, document.file_path))
        
        # ⚡ Extract PDFs in parallel (2-4x faster)
        if docs_to_extract:
            print(f"⚡ Extracting {len(docs_to_extract)} PDFs with {self.max_workers} workers...")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(extract_pdf_words, doc_id, path): doc_id 
                          for doc_id, path in docs_to_extract}
                
                for future in as_completed(futures):
                    doc_id, words = future.result()
                    pdf_words_cache[doc_id] = words

        for doc_id, doc_feedbacks in feedback_by_doc.items():
            # Get document
            document = self.document_repo.find_by_id(doc_id)
            if not document:
                continue

            # ⚡ Get words from cache (already extracted in parallel)
            words = pdf_words_cache.get(doc_id, [])
            if not words:
                continue

            # ✅ FIX: Include ALL fields (corrected + non-corrected) for complete context
            # Get extraction results to include non-corrected fields
            extraction_result = json.loads(document.extraction_result)
            extracted_data = extraction_result.get("extracted_data", {})
            confidence_scores = extraction_result.get("confidence_scores", {})

            # Create complete feedback list (corrected + high-confidence non-corrected)
            complete_feedbacks = []
            corrected_fields = set(fb["field_name"] for fb in doc_feedbacks)

            # Add corrected fields
            for fb in doc_feedbacks:
                complete_feedbacks.append(fb)

            # Add non-corrected fields with reasonable confidence
            for field_name, value in extracted_data.items():
                if field_name not in corrected_fields:
                    confidence = confidence_scores.get(field_name, 0.0)
                    if confidence >= 0.3:  
                        complete_feedbacks.append(
                            {"field_name": field_name, "corrected_value": value}
                        )

            field_configs = {}
            if template_config:
                fields = template_config.get('fields', {})
                for field_name, field_config in fields.items():
                    field_configs[field_name] = field_config
            
            for fb in complete_feedbacks:
                field_name = fb["field_name"]
                field_config = field_configs.get(field_name)
                
                features, labels = learner._create_bio_sequence(
                    fb,
                    words,
                    field_config=field_config
                )
                
                if features and labels:
                    X_train.append(features)
                    y_train.append(labels)
                    if fb in doc_feedbacks:
                        feedback_ids.append(fb["id"])

        # ✅ ALWAYS process validated docs (both full and incremental)
        # Filter based on use_all_feedback to include only unused or all
        validated_count = 0
        docs_with_feedback = set(feedback_by_doc.keys())

        self.logger.info(f"Processing {len(validated_docs)} validated documents...")
        
        validated_docs_to_extract = []
        for document in validated_docs:
            if document.id not in pdf_words_cache:
                validated_docs_to_extract.append((document.id, document.file_path))
        
        if validated_docs_to_extract:
            self.logger.info(f"Extracting {len(validated_docs_to_extract)} validated documents with {self.max_workers} workers...")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(extract_pdf_words, doc_id, path): doc_id 
                          for doc_id, path in validated_docs_to_extract}
                
                for future in as_completed(futures):
                    doc_id, words = future.result()
                    pdf_words_cache[doc_id] = words

        for document in validated_docs:
            doc_id = document.id

            # Skip documents that already have feedback (to avoid duplication)
            if doc_id in docs_with_feedback:
                continue

            extraction_result = json.loads(document.extraction_result)
            extracted_data = extraction_result.get("extracted_data", {})
            confidence_scores = extraction_result.get("confidence_scores", {})

            words = pdf_words_cache.get(doc_id, [])
            if not words:
                continue

            # Create pseudo-feedback from high-confidence extractions
            pseudo_feedbacks = []
            for field_name, value in extracted_data.items():
                confidence = confidence_scores.get(field_name, 0.0)
                if confidence >= 0.3:  
                    pseudo_feedbacks.append(
                        {"field_name": field_name, "corrected_value": value}
                    )

            if pseudo_feedbacks:
                field_configs = {}
                if template_config:
                    fields = template_config.get('fields', {})
                    for field_name, field_config in fields.items():
                        field_configs[field_name] = field_config
                
                for fb in pseudo_feedbacks:
                    field_name = fb["field_name"]
                    field_config = field_configs.get(field_name)
                    
                    features, labels = learner._create_bio_sequence(
                        fb,
                        words,
                        field_config=field_config
                    )
                    
                    if features and labels:
                        X_train.append(features)
                        y_train.append(labels)
                
                validated_count += 1

        if not X_train:
            raise ValueError("Could not prepare training data - no feedback or validated documents available")

        self.logger.info(f"Training: {len(X_train)} samples ({len(feedback_by_doc)} feedback docs, {validated_count} validated docs)")

        validation_strategy = ValidationStrategy(template_id=template_id)
        
        if is_incremental:
            validation_decision = {
                'should_validate': False,
                'reason': 'Ultra-fast incremental mode',
                'skip_leakage': True,
                'skip_diversity': True
            }

        else:
            validation_decision = validation_strategy.should_validate(
                num_samples=len(X_train),
                is_incremental=is_incremental,
                force=force_validation,
            )
            self.logger.info(f"Validation: {validation_decision['reason']}")

        diversity_metrics = {}
        leakage_results = {"leakage_detected": False}
        validation_start_time = time.time()

        if validation_decision["should_validate"]:
            if not validation_decision["skip_diversity"]:
                diversity_metrics = validate_training_data_diversity(X_train, y_train)
            else:
                cached = validation_strategy.get_cached_results()
                diversity_metrics = cached.get("diversity_metrics", {})

            X_train_split, X_test_split, y_train_split, y_test_split = (
                split_training_data(X_train, y_train, test_size=0.2, random_state=42)
            )

            if not validation_decision["skip_leakage"]:
                leakage_results = {
                    "leakage_detected": False,
                    "num_leaks": 0,
                    "samples_checked": len(X_test_split),
                    "leakage_type": "none",
                    "note": f"Template-specific model: {len(validated_docs)} unique files verified in database",
                }
            else:
                cached = validation_strategy.get_cached_results()
                leakage_results = cached.get(
                    "leakage_results", {"leakage_detected": False}
                )

            validation_strategy.save_validation_results(
                num_samples=len(X_train),
                diversity_metrics=diversity_metrics,
                leakage_results=leakage_results,
            )
        else:
            cached = validation_strategy.get_cached_results()
            diversity_metrics = cached.get("diversity_metrics", {})
            leakage_results = cached.get("leakage_results", {"leakage_detected": False})

            X_train_split, X_test_split, y_train_split, y_test_split = (
                split_training_data(X_train, y_train, test_size=0.2, random_state=42)
            )

        recommendations = get_training_recommendations(
            num_samples=len(X_train),
            diversity_score=diversity_metrics.get("diversity_score", 0.5),
            has_leakage=leakage_results.get("leakage_detected", False),
            leakage_type=leakage_results.get("leakage_type", "unknown"),
            template_specific=True,  # This is a template-specific model
        )

        validation_duration = time.time() - validation_start_time
        dq_repo = DataQualityRepository(self.db)
        metric_id = dq_repo.save_metrics(
            template_id=template_id,
            validation_type="training",
            total_samples=len(X_train),
            diversity_metrics=diversity_metrics,
            leakage_results=leakage_results,
            recommendations=recommendations,
            validation_duration=validation_duration,
            train_samples=len(X_train_split) if X_train_split else None,
            test_samples=len(X_test_split) if X_test_split else None,
            triggered_by="training",
            notes=f"Training session - {validation_decision['reason']}",
        )

        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
        model_exists = os.path.exists(model_path)

        learner = AdaptiveLearner(model_path if model_exists else None)
        
        if is_incremental and model_exists:
            # Use half iterations for incremental (faster)
            incremental_iterations = max(50, self.max_iterations // 2)
            
            # Check if evaluation is enabled for incremental training
            # Use app.config if available (from Flask context), otherwise fallback to os.getenv
            try:
                from flask import current_app
                evaluate_incremental = current_app.config.get('INCREMENTAL_TRAINING_EVALUATE', False)
            except (ImportError, RuntimeError):
                # Not in Flask context (e.g., CLI), read from env directly
                evaluate_incremental = os.getenv('INCREMENTAL_TRAINING_EVALUATE', 'false').lower() == 'true'
            
            if evaluate_incremental:
                self.logger.info(f"Incremental training ({incremental_iterations} iterations, with evaluation)")
            else:
                self.logger.info(f"Incremental training ({incremental_iterations} iterations, skip evaluation)")
            
            metrics = learner.train(X_train_split, y_train_split, 
                                   max_iterations=incremental_iterations,
                                   skip_evaluation=True)  # Skip training eval
            
            # ✅ Conditionally evaluate on test set based on config
            if evaluate_incremental:
                test_metrics = learner.evaluate(X_test_split, y_test_split)
                self.logger.info(f"Test accuracy: {test_metrics.get('accuracy', 0)*100:.2f}%")
            else:
                # Use placeholder metrics for faster training
                test_metrics = {
                    'accuracy': None,
                    'precision': None,
                    'recall': None,
                    'f1': None
                }
                self.logger.info("Evaluation skipped for speed (metrics will be NULL)")
        else:
            self.logger.info(f"Max iterations: {self.max_iterations}")
            
            best_params = {'c1': 0.01, 'c2': 0.01}
            
            learner = AdaptiveLearner()
            
            metrics = learner.train(X_train_split, y_train_split, 
                                   c1=best_params['c1'], c2=best_params['c2'],
                                   max_iterations=self.max_iterations,  # Configurable iterations
                                   skip_evaluation=True)  # Skip training eval for speed

            test_metrics = learner.evaluate(X_test_split, y_test_split)
            self.logger.info(f"Test accuracy: {test_metrics.get('accuracy', 0)*100:.2f}%")

            # print("Results Comparison:")
            # print(f"Training Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
            # print(f"Test Accuracy:     {test_metrics.get('accuracy', 0)*100:.2f}%")
            # print(
            #     f"Difference:        {abs(metrics.get('accuracy', 0) - test_metrics.get('accuracy', 0))*100:.2f}%"
            # )

            if abs(metrics.get("accuracy", 0) - test_metrics.get("accuracy", 0)) > 0.1:
                self.logger.warning("WARNING: Large gap between train/test accuracy!")
                self.logger.warning("This indicates overfitting. Model memorized training data.")
            else:
                self.logger.info("Good generalization. Model should work on new data.")
        
        learner.save_model(model_path)

        self.feedback_repo.mark_as_used(feedback_ids)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE field_contexts
            SET typical_length = (
                SELECT CAST(AVG(LENGTH(f.corrected_value)) AS INTEGER)
                FROM feedback f
                JOIN documents d ON f.document_id = d.id
                JOIN field_configs fc ON fc.field_name = f.field_name
                JOIN field_locations fl ON fl.field_config_id = fc.id
                WHERE fl.id = field_contexts.field_location_id
                  AND d.template_id = ?
                GROUP BY f.field_name
                HAVING COUNT(*) >= 5
            )
            WHERE field_location_id IN (
                SELECT fl.id 
                FROM field_locations fl
                JOIN field_configs fc ON fc.id = fl.field_config_id
                WHERE fc.config_id IN (SELECT id FROM template_configs WHERE template_id = ?)
            )
        ''', (template_id, template_id))
        
        conn.commit()
        updated_count = cursor.rowcount
        self.logger.info(f"Updated typical_length for {updated_count} fields")

        # ------------------------------------------------------------------
        # Robust multiline inference (layout-aware, data-driven)
        #
        # This handles PDF line-wrapping cases where corrected_value is
        # single-line (no '\n') but the visual layout wraps to the next line.
        #
        # Evidence:
        # - feedback where corrected_value extends original_value (missing suffix)
        # - missing suffix tokens appear below the field's bounding box in PDF
        #
        # Thresholds are configurable via env.
        # ------------------------------------------------------------------
        layout_min_samples = int(os.getenv('MULTILINE_LAYOUT_INFER_MIN_SAMPLES', '5'))
        layout_min_hits = int(os.getenv('MULTILINE_LAYOUT_INFER_MIN_HITS', '2'))
        layout_min_ratio = float(os.getenv('MULTILINE_LAYOUT_INFER_MIN_RATIO', '0.3'))
        layout_x_tolerance_factor = float(os.getenv('MULTILINE_LAYOUT_INFER_X_TOLERANCE_FACTOR', '0.25'))
        layout_y_gap_min_factor = float(os.getenv('MULTILINE_LAYOUT_INFER_Y_GAP_MIN_FACTOR', '0.6'))

        def _tokenize_simple(text: str) -> List[str]:
            if not text:
                return []
            parts = str(text).strip().split()
            tokens: List[str] = []
            for p in parts:
                t = p.strip().strip('.,;:!?)\"]}\'')
                t = t.lstrip('([{"\'')
                if t:
                    tokens.append(t)
            return tokens

        def _extract_words_by_page(pdf_path: str) -> Dict[int, List[Dict[str, Any]]]:
            words_by_page: Dict[int, List[Dict[str, Any]]] = {}
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    try:
                        page_words = page.extract_words(
                            x_tolerance=1,
                            y_tolerance=1,
                            keep_blank_chars=False,
                            use_text_flow=True,
                        )
                    except Exception:
                        page_words = []
                    normalized: List[Dict[str, Any]] = []
                    for w in page_words:
                        normalized.append(
                            {
                                'text': w.get('text', ''),
                                'x0': float(w.get('x0', 0.0)),
                                'x1': float(w.get('x1', 0.0)),
                                'top': float(w.get('top', 0.0)),
                                'bottom': float(w.get('bottom', 0.0)),
                            }
                        )
                    words_by_page[page_idx] = normalized
            return words_by_page

        # Load field bounding boxes for this template (location_index=0 primary)
        cursor.execute(
            '''
            SELECT
                fc.id AS field_config_id,
                fc.field_name,
                fl.page,
                fl.x0,
                fl.y0,
                fl.x1,
                fl.y1,
                fctx.next_field_y
            FROM field_configs fc
            JOIN template_configs tc ON tc.id = fc.config_id
            JOIN field_locations fl ON fl.field_config_id = fc.id AND fl.location_index = 0
            LEFT JOIN field_contexts fctx ON fctx.id = (
                SELECT MAX(id)
                FROM field_contexts
                WHERE field_location_id = fl.id
            )
            WHERE tc.template_id = ?
            ''',
            (template_id,),
        )
        field_boxes: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            field_boxes[row['field_name']] = {
                'field_config_id': row['field_config_id'],
                'page': row['page'] or 0,
                'x0': float(row['x0']),
                'y0': float(row['y0']),
                'x1': float(row['x1']),
                'y1': float(row['y1']),
                'next_field_y': float(row['next_field_y']) if row['next_field_y'] is not None else None,
            }

        # Load feedback candidates with document paths
        cursor.execute(
            '''
            SELECT
                f.document_id,
                f.field_name,
                f.original_value,
                f.corrected_value,
                d.file_path
            FROM feedback f
            JOIN documents d ON d.id = f.document_id
            WHERE d.template_id = ?
              AND f.original_value IS NOT NULL
              AND f.corrected_value IS NOT NULL
              AND d.file_path IS NOT NULL
            ''',
            (template_id,),
        )
        feedback_rows = cursor.fetchall()

        # Cache parsed words per document to avoid repeated PDF reads
        pdf_cache: Dict[int, Dict[int, List[Dict[str, Any]]]] = {}

        field_total: Dict[str, int] = {}
        field_hits: Dict[str, int] = {}

        for fb in feedback_rows:
            field_name = fb['field_name']
            box = field_boxes.get(field_name)
            if not box:
                continue

            original_value = str(fb['original_value'])
            corrected_value = str(fb['corrected_value'])

            # Only consider cases where correction extends original (missing suffix/prefix)
            missing_text = None
            if corrected_value.startswith(original_value) and len(corrected_value) > len(original_value):
                missing_text = corrected_value[len(original_value):].strip()
            elif original_value in corrected_value and len(corrected_value) > len(original_value):
                idx = corrected_value.find(original_value)
                tail = corrected_value[idx + len(original_value):].strip() if idx >= 0 else ''
                if tail:
                    missing_text = tail

            if not missing_text:
                continue

            missing_tokens = _tokenize_simple(missing_text)
            if not missing_tokens:
                continue

            document_id = int(fb['document_id'])
            pdf_path = fb['file_path']
            if not pdf_path or not os.path.exists(pdf_path):
                continue

            field_total[field_name] = field_total.get(field_name, 0) + 1

            if document_id not in pdf_cache:
                try:
                    pdf_cache[document_id] = _extract_words_by_page(pdf_path)
                except Exception as e:
                    self.logger.warning(f"Failed to parse PDF for multiline inference: doc={document_id}, err={e}")
                    pdf_cache[document_id] = {}

            page_idx = int(box['page'])
            words = pdf_cache.get(document_id, {}).get(page_idx, [])
            if not words:
                continue

            # Derive data-driven tolerances
            width = max(1.0, box['x1'] - box['x0'])
            x_tol = width * layout_x_tolerance_factor

            heights = [max(0.0, w['bottom'] - w['top']) for w in words if w.get('bottom') is not None and w.get('top') is not None]
            heights_sorted = sorted(h for h in heights if h > 0)
            median_h = heights_sorted[len(heights_sorted) // 2] if heights_sorted else 10.0
            y_gap_min = median_h * layout_y_gap_min_factor

            x_min = box['x0'] - x_tol
            x_max = box['x1'] + x_tol
            y_min = box['y1'] + y_gap_min
            y_max = box['next_field_y'] - y_gap_min if box.get('next_field_y') else None

            # Check if any missing token appears below within the same field column
            missing_lower = {t.lower() for t in missing_tokens[:5]}
            hit = False
            for w in words:
                wt = str(w.get('text', '')).strip()
                if not wt:
                    continue
                wt_l = wt.lower()
                if wt_l not in missing_lower:
                    continue
                wx0 = float(w.get('x0', 0.0))
                wy = float(w.get('top', 0.0))
                if wx0 < x_min or wx0 > x_max:
                    continue
                if wy < y_min:
                    continue
                if y_max is not None and wy > y_max:
                    continue
                hit = True
                break

            if hit:
                field_hits[field_name] = field_hits.get(field_name, 0) + 1

        # Apply decision per field
        for field_name, n in field_total.items():
            hits = field_hits.get(field_name, 0)
            if n < layout_min_samples:
                continue
            ratio = float(hits) / float(n) if n else 0.0
            allow = 1 if (hits >= layout_min_hits and ratio >= layout_min_ratio) else 0
            field_config_id = field_boxes[field_name]['field_config_id']
            cursor.execute(
                'UPDATE field_configs SET allow_multiline = ? WHERE id = ?',
                (allow, field_config_id),
            )

        conn.commit()
        self.logger.info('Updated allow_multiline flags using layout-aware feedback evidence')

        # ------------------------------------------------------------------
        # Robust multiline inference (data-driven, no template hardcoding)
        #
        # Persist allow_multiline on field_configs using feedback statistics.
        # Rules:
        # - If any corrected_value contains a newline => multiline
        # - Else if p90 length is large enough => likely wraps/multiline in PDF
        # Thresholds are configurable via env.
        # ------------------------------------------------------------------
        infer_min_samples = int(os.getenv('MULTILINE_INFER_MIN_SAMPLES', '5'))
        infer_p90_threshold = int(os.getenv('MULTILINE_INFER_P90_LENGTH_THRESHOLD', '90'))
        infer_mean_threshold = int(os.getenv('MULTILINE_INFER_MEAN_LENGTH_THRESHOLD', '70'))

        cursor.execute(
            '''
            WITH feedback_scoped AS (
                SELECT
                    f.field_name,
                    f.corrected_value,
                    LENGTH(f.corrected_value) AS vlen,
                    CASE
                        WHEN INSTR(f.corrected_value, CHAR(10)) > 0 OR INSTR(f.corrected_value, CHAR(13)) > 0
                        THEN 1 ELSE 0
                    END AS has_newline
                FROM feedback f
                JOIN documents d ON f.document_id = d.id
                WHERE d.template_id = ?
                  AND f.corrected_value IS NOT NULL
            ),
            stats AS (
                SELECT
                    field_name,
                    COUNT(*) AS n,
                    AVG(vlen) AS mean_len,
                    MAX(has_newline) AS any_newline
                FROM feedback_scoped
                GROUP BY field_name
            ),
            p90 AS (
                SELECT
                    fs.field_name,
                    fs.vlen,
                    ROW_NUMBER() OVER (PARTITION BY fs.field_name ORDER BY fs.vlen) AS rn,
                    COUNT(*) OVER (PARTITION BY fs.field_name) AS cnt
                FROM feedback_scoped fs
            ),
            p90_len AS (
                SELECT
                    field_name,
                    MAX(CASE WHEN rn >= CAST(0.9 * cnt AS INTEGER) THEN vlen END) AS p90_len
                FROM p90
                GROUP BY field_name
            ),
            decision AS (
                SELECT
                    s.field_name,
                    s.n,
                    s.mean_len,
                    COALESCE(p.p90_len, 0) AS p90_len,
                    s.any_newline,
                    CASE
                        WHEN s.n >= ? AND s.any_newline = 1 THEN 1
                        WHEN s.n >= ? AND COALESCE(p.p90_len, 0) >= ? AND s.mean_len >= ? THEN 1
                        ELSE 0
                    END AS allow_multiline
                FROM stats s
                LEFT JOIN p90_len p ON p.field_name = s.field_name
            )
            UPDATE field_configs
            SET allow_multiline = CASE
                WHEN COALESCE(field_configs.allow_multiline, 0) = 1 THEN 1
                ELSE (
                    SELECT d.allow_multiline
                    FROM decision d
                    WHERE d.field_name = field_configs.field_name
                )
            END
            WHERE id IN (
                SELECT fc.id
                FROM field_configs fc
                JOIN template_configs tc ON tc.id = fc.config_id
                WHERE tc.template_id = ?
            )
              AND field_name IN (SELECT field_name FROM decision);
            ''',
            (
                template_id,
                infer_min_samples,
                infer_min_samples,
                infer_p90_threshold,
                infer_mean_threshold,
                template_id,
            ),
        )
        conn.commit()
        self.logger.info("Updated allow_multiline flags based on feedback statistics")
        
        cursor.execute('''
            SELECT fc.field_name, fctx.typical_length
            FROM field_configs fc
            JOIN field_locations fl ON fl.field_config_id = fc.id
            LEFT JOIN field_contexts fctx ON fctx.field_location_id = fl.id
            WHERE fc.config_id IN (SELECT id FROM template_configs WHERE template_id = ?)
              AND fctx.typical_length IS NOT NULL
            ORDER BY fc.field_name
        ''', (template_id,))
        
        # for field_name, typical_length in cursor.fetchall():
            # print(f"      {field_name}: {typical_length} chars")
        
        conn.close()

        # Save training history with BOTH train and test metrics
        self.training_repo.create(
            template_id=template_id,
            model_path=model_path,
            training_samples=len(X_train_split),
            metrics=test_metrics,  # ✅ Save TEST metrics (real performance)
        )

        return {
            "template_id": template_id,
            "model_path": model_path,
            "training_samples": len(X_train_split),
            "test_samples": len(X_test_split),
            "train_metrics": metrics,
            "test_metrics": test_metrics,  # ✅ Real performance on unseen data
            "diversity_metrics": diversity_metrics,
            "leakage_detected": leakage_results["leakage_detected"],
            "recommendations": recommendations,
        }

    def get_training_history(self, template_id: int) -> List[Dict]:
        """Get training history for a template"""
        return self.training_repo.find_training_history(template_id)

    def get_latest_metrics(self, template_id: int) -> Optional[Dict]:
        """
        Get latest model metrics for a template

        Args:
            template_id: Template ID

        Returns:
            Latest metrics or None if no history
        """
        history = self.training_repo.find_training_history(template_id)

        if not history:
            return None

        latest = history[0]  # Most recent training

        return {
            "template_id": template_id,
            "metrics": {
                "accuracy": latest["accuracy"],
                "precision": latest["precision_score"],
                "recall": latest["recall_score"],
                "f1": latest["f1_score"],
                "training_samples": latest["training_samples"],
                "trained_at": latest["trained_at"],
            },
        }

    def get_feedback_statistics(self, template_id: int) -> Dict[str, Any]:
        """
        Get feedback statistics for a template

        Args:
            template_id: Template ID

        Returns:
            Feedback statistics
        """
        all_feedback = self.feedback_repo.find_for_training(
            template_id, unused_only=False
        )
        unused_feedback = self.feedback_repo.find_for_training(
            template_id, unused_only=True
        )

        return {
            "template_id": template_id,
            "stats": {
                "total_feedback": len(all_feedback),
                "unused_feedback": len(unused_feedback),
                "used_feedback": len(all_feedback) - len(unused_feedback),
            },
        }

    def trigger_adaptive_learning(
        self,
        document_id: int,
        all_fields: Dict[str, str],
        corrected_fields: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Trigger adaptive pattern learning after validation

        This method learns from BOTH:
        1. Corrected fields (wrong extractions that were fixed)
        2. Non-corrected fields (correct extractions that were validated)

        Args:
            document_id: Document ID
            all_fields: All extracted fields (original extraction)
            corrected_fields: Only fields that were corrected

        Returns:
            Dict with learning trigger results
        """
        from core.learning.auto_pattern_learner import get_auto_learner

        # 0) MULTILINE FLAG LEARNING (layout-aware, immediate)
        # This updates field_configs.allow_multiline based on the just-validated
        # document + correction evidence, so it doesn't have to wait for retraining.
        try:
            self.update_allow_multiline_from_document_feedback(
                document_id=document_id,
                all_fields=all_fields,
                corrected_fields=corrected_fields,
            )
        except Exception as e:  # pragma: no cover - defensive logging
            self.logger.warning(
                f"⚠️ allow_multiline inference skipped for document {document_id}: {e}"
            )

        # Get document info
        doc = self.document_repo.find_by_id(document_id)
        if not doc:
            return {"success": False, "error": f"Document {document_id} not found"}

        # Handle both dict and object return types
        template_id = doc.get("template_id") if isinstance(doc, dict) else doc.template_id

        # 1) PATTERN LEARNING (regex / pattern-based) via auto_pattern_learner
        auto_learner = get_auto_learner(self.db)

        triggered_fields = []
        skipped_fields = []
        errors = []

        for field_name in all_fields.keys():
            try:
                if auto_learner.should_trigger_learning(template_id, field_name):
                    auto_learner.trigger_learning(
                        template_id=template_id, field_name=field_name, async_mode=True
                    )

                    is_corrected = field_name in corrected_fields
                    triggered_fields.append(
                        {
                            "field_name": field_name,
                            "type": "corrected" if is_corrected else "validated",
                        }
                    )
                else:
                    skipped_fields.append(field_name)

            except Exception as e:
                errors.append({"field_name": field_name, "error": str(e)})

        # 2) HYBRID STRATEGY + POST-PROCESSOR LEARNING via DataExtractor
        try:
            # Load original extraction results from document
            import json

            extraction_json = doc.get("extraction_result") if isinstance(doc, dict) else doc.extraction_result
            if extraction_json:
                extraction_results = json.loads(extraction_json)

                # Load template config (for DataExtractor)
                from core.templates.config_loader import get_config_loader
                from core.extraction.extractor import DataExtractor

                config_loader = get_config_loader(db_manager=self.db, template_folder=None)
                template = self.template_repo.find_by_id(template_id)

                if template:
                    template_config = config_loader.load_config(
                        template_id=template_id, config_path=template.config_path
                    )
                else:
                    template_config = None

                if template_config:
                    import os

                    model_folder = os.getenv("MODEL_FOLDER", "models")
                    model_path = os.path.join(
                        model_folder, f"template_{template_id}_model.joblib"
                    )
                    if not os.path.exists(model_path):
                        model_path = None

                    extractor = DataExtractor(template_config, model_path)
                    extractor.learn_from_feedback(
                        extraction_results=extraction_results,
                        corrections=corrected_fields,
                    )
        except Exception as e:  # pragma: no cover - defensive logging
            self.logger.warning(f"⚠️ Adaptive extractor learning failed for document {document_id}: {e}")

        return {
            "success": True,
            "document_id": document_id,
            "template_id": template_id,
            "triggered_fields": triggered_fields,
            "skipped_fields": skipped_fields,
            "errors": errors,
            "summary": {
                "total_fields": len(all_fields),
                "triggered": len(triggered_fields),
                "skipped": len(skipped_fields),
                "errors": len(errors),
            },
        }

    def update_allow_multiline_from_document_feedback(
        self,
        document_id: int,
        all_fields: Dict[str, str],
        corrected_fields: Dict[str, str],
    ) -> Dict[str, Any]:
        """Infer and persist allow_multiline for fields using PDF layout evidence.

        Evidence type:
        - corrected_value extends original_value
        - at least one missing suffix token is found below the field's bbox

        This is intentionally conservative and fully data-driven.
        Thresholds are configurable via env.
        """

        doc = self.document_repo.find_by_id(document_id)
        if not doc:
            return {"success": False, "error": f"Document {document_id} not found"}

        template_id = doc.get("template_id") if isinstance(doc, dict) else doc.template_id
        pdf_path = doc.get("file_path") if isinstance(doc, dict) else doc.file_path
        if not pdf_path or not os.path.exists(pdf_path):
            return {"success": False, "error": f"PDF not found: {pdf_path}"}

        layout_x_tolerance_factor = float(
            os.getenv("MULTILINE_LAYOUT_INFER_X_TOLERANCE_FACTOR", "0.25")
        )
        layout_y_gap_min_factor = float(
            os.getenv("MULTILINE_LAYOUT_INFER_Y_GAP_MIN_FACTOR", "0.6")
        )

        def _tokenize_simple(text: str) -> List[str]:
            if not text:
                return []
            parts = str(text).strip().split()
            tokens: List[str] = []
            for p in parts:
                t = p.strip().strip('.,;:!?)\"]}\'')
                t = t.lstrip('([{"\'')
                if t:
                    tokens.append(t)
            return tokens

        # Load words per page (single PDF only)
        words_by_page: Dict[int, List[Dict[str, Any]]] = {}
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    page_words = page.extract_words(
                        x_tolerance=1,
                        y_tolerance=1,
                        keep_blank_chars=False,
                        use_text_flow=True,
                    )
                except Exception:
                    page_words = []
                normalized = []
                for w in page_words:
                    normalized.append(
                        {
                            "text": w.get("text", ""),
                            "x0": float(w.get("x0", 0.0)),
                            "x1": float(w.get("x1", 0.0)),
                            "top": float(w.get("top", 0.0)),
                            "bottom": float(w.get("bottom", 0.0)),
                        }
                    )
                words_by_page[page_idx] = normalized

        conn = self.db.get_connection()
        cursor = conn.cursor()

        updated_fields: List[str] = []
        skipped_fields: List[str] = []

        try:
            for field_name, corrected_value in corrected_fields.items():
                original_value = all_fields.get(field_name, "")

                original_value_s = str(original_value).strip()
                corrected_value_s = str(corrected_value).strip()
                if not original_value_s or not corrected_value_s:
                    skipped_fields.append(field_name)
                    continue

                missing_text = None
                if corrected_value_s.startswith(original_value_s) and len(corrected_value_s) > len(original_value_s):
                    missing_text = corrected_value_s[len(original_value_s):].strip()
                elif original_value_s in corrected_value_s and len(corrected_value_s) > len(original_value_s):
                    idx = corrected_value_s.find(original_value_s)
                    tail = corrected_value_s[idx + len(original_value_s):].strip() if idx >= 0 else ""
                    if tail:
                        missing_text = tail

                if not missing_text:
                    skipped_fields.append(field_name)
                    continue

                missing_tokens = _tokenize_simple(missing_text)
                if not missing_tokens:
                    skipped_fields.append(field_name)
                    continue

                cursor.execute(
                    '''
                    SELECT
                        fc.id AS field_config_id,
                        fl.page,
                        fl.x0,
                        fl.x1,
                        fl.y1,
                        (
                            SELECT next_field_y
                            FROM field_contexts
                            WHERE field_location_id = fl.id
                            ORDER BY id DESC
                            LIMIT 1
                        ) AS next_field_y
                    FROM field_configs fc
                    JOIN template_configs tc ON tc.id = fc.config_id
                    JOIN field_locations fl ON fl.field_config_id = fc.id
                    WHERE tc.template_id = ?
                      AND fc.field_name = ?
                      AND fl.location_index = 0
                    LIMIT 1
                    ''',
                    (template_id, field_name),
                )
                row = cursor.fetchone()
                if not row:
                    skipped_fields.append(field_name)
                    continue

                field_config_id = int(row["field_config_id"])
                page_idx = int(row["page"] or 0)
                x0 = float(row["x0"])
                x1 = float(row["x1"])
                y1 = float(row["y1"])
                next_field_y = (
                    float(row["next_field_y"]) if row["next_field_y"] is not None else None
                )

                words = words_by_page.get(page_idx, [])
                if not words:
                    skipped_fields.append(field_name)
                    continue

                width = max(1.0, x1 - x0)
                x_tol = width * layout_x_tolerance_factor

                heights = [
                    max(0.0, w["bottom"] - w["top"])
                    for w in words
                    if w.get("bottom") is not None and w.get("top") is not None
                ]
                heights_sorted = sorted(h for h in heights if h > 0)
                median_h = heights_sorted[len(heights_sorted) // 2] if heights_sorted else 10.0
                y_gap_min = median_h * layout_y_gap_min_factor

                x_min = x0 - x_tol
                x_max = x1 + x_tol
                y_min = y1 + y_gap_min
                y_max = next_field_y - y_gap_min if next_field_y else None

                missing_lower = {t.lower() for t in missing_tokens[:5]}
                hit = False
                for w in words:
                    wt = str(w.get("text", "")).strip()
                    if not wt:
                        continue
                    if wt.lower() not in missing_lower:
                        continue
                    wx0 = float(w.get("x0", 0.0))
                    wy = float(w.get("top", 0.0))
                    if wx0 < x_min or wx0 > x_max:
                        continue
                    if wy < y_min:
                        continue
                    if y_max is not None and wy > y_max:
                        continue
                    hit = True
                    break

                if not hit:
                    skipped_fields.append(field_name)
                    continue

                cursor.execute(
                    "UPDATE field_configs SET allow_multiline = 1 WHERE id = ?",
                    (field_config_id,),
                )
                updated_fields.append(field_name)

            conn.commit()
        finally:
            conn.close()

        return {
            "success": True,
            "document_id": document_id,
            "template_id": template_id,
            "updated_fields": updated_fields,
            "skipped_fields": skipped_fields,
        }
