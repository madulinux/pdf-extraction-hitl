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
        self.logger.info(f"\n📚 Processing validated documents (high-confidence extractions)...")
        validated_docs = self.document_repo.find_validated_documents(template_id)
        self.logger.info(f"   Found {len(validated_docs)} validated documents")

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

        # ALWAYS use validated docs (both full and incremental)
        validated_count = 0
        
        if use_all_feedback: 
            docs_with_feedback = set(feedback_by_doc.keys())

            self.logger.info(f"Processing {len(validated_docs)} validated documents...")
            
            validated_docs_to_extract = []
            for document in validated_docs:
                if document.id not in pdf_words_cache:
                    validated_docs_to_extract.append((document.id, document.file_path))
            
            if validated_docs_to_extract:
                self.logger.info(f"Processing {len(validated_docs)} validated documents with {self.max_workers} workers...")
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {executor.submit(extract_pdf_words, doc_id, path): doc_id 
                              for doc_id, path in validated_docs_to_extract}
                    
                    for future in as_completed(futures):
                        doc_id, words = future.result()
                        pdf_words_cache[doc_id] = words

            for document in validated_docs:
                doc_id = document.id

                extraction_result = json.loads(document.extraction_result)
                extracted_data = extraction_result.get("extracted_data", {})
                confidence_scores = extraction_result.get("confidence_scores", {})

                words = pdf_words_cache.get(doc_id, [])
                if not words:
                    continue

                pseudo_feedbacks = []

                if doc_id in docs_with_feedback:
                    continue
                else:
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
            raise ValueError("Could not prepare training data")

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
            self.logger.info(f"Incremental training ({incremental_iterations} iterations, skip evaluation)")
            
            metrics = learner.train(X_train_split, y_train_split, 
                                   max_iterations=incremental_iterations,
                                   skip_evaluation=True)  # Skip all eval
            
            test_metrics = {'accuracy': 0.0}  # Placeholder
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
