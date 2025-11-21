"""
Extraction Service
Business logic for document extraction
"""

import logging
from typing import Dict, Any
from core.extraction.extractor import DataExtractor
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.template_repository import TemplateRepository
from database.repositories.training_repository import TrainingRepository
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import re
import threading
import time
from shared.exceptions import NotFoundError, ValidationError

from database.db_manager import DatabaseManager
from core.extraction.hybrid_strategy import HybridExtractionStrategy

# ✅ Global lock and cooldown tracking for auto-retrain
_retrain_lock = threading.Lock()
_last_retrain_time = {}  # template_id -> timestamp


class ExtractionService:
    """Service layer for extraction operations"""

    def __init__(
        self,
        document_repo: DocumentRepository,
        feedback_repo: FeedbackRepository,
        template_repo: TemplateRepository,
        training_repo: TrainingRepository,
        upload_folder: str,
        model_folder: str,
        feedback_folder: str,
    ):
        self.logger = logging.getLogger(__name__)
        self.document_repo = document_repo
        self.feedback_repo = feedback_repo
        self.template_repo = template_repo
        self.training_repo = training_repo
        self.upload_folder = upload_folder
        self.model_folder = model_folder
        self.feedback_folder = feedback_folder
        self.db = DatabaseManager()  # Initialize DB manager for config loading

    def extract_document(
        self,
        file: FileStorage,
        template_id: int,
        template_config_path: str = None,  # Now optional, will use DB
        experiment_phase: str = None,  # NEW: For experiment tracking
    ) -> Dict[str, Any]:
        """
        Extract data from filled PDF document

        Args:
            file: Uploaded PDF file
            template_id: Template ID to use
            template_config_path: Path to template configuration (optional, for backward compatibility)
            experiment_phase: Experiment phase ('baseline', 'adaptive', or None for production)

        Returns:
            Extraction results with document info
        """
        # Load template config from database or JSON
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(
            db_manager=self.db,
            template_folder=(
                os.path.dirname(template_config_path) if template_config_path else None
            ),
        )

        config = config_loader.load_config(template_id, template_config_path)
        if not config:
            raise ValidationError(
                f"Failed to load configuration for template {template_id}"
            )

        # Save uploaded document
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)

        # Create document record
        document_id = self.document_repo.create(
            template_id=template_id,
            filename=filename,
            file_path=filepath,
            experiment_phase=experiment_phase,  # NEW: Track experiment phase
        )

        # Check if model exists for this template
        # For baseline experiment, force rule-based only (no model)
        if experiment_phase == "baseline":
            model_path = None
            # print(f"🔍 [ExtractionService] Baseline phase: forcing rule-based extraction")
        else:
            model_path = os.path.join(
                self.model_folder, f"template_{template_id}_model.joblib"
            )
            # print(f"🔍 [ExtractionService] Checking model: {model_path}")
            if not os.path.exists(model_path):
                # print(f"❌ [ExtractionService] Model NOT found: {model_path}")
                model_path = None
            # else:

        # print(f"✅ [ExtractionService] Model found: {model_path}")

        # Extract data
        # print(f"🔍 [ExtractionService] Creating DataExtractor with model_path: {model_path}")
        try:
            extractor = DataExtractor(config, model_path)
            results = extractor.extract(filepath)
        except Exception as e:
            self.logger.error(f"❌ [ExtractionService] Error during extraction: {e}")
            import traceback

            traceback.print_exc()
            raise

        # Update document with results
        extraction_time_ms = results.get(
            "extraction_time_ms", 0
        )  # ✅ NEW: Get extraction time
        self.document_repo.update_extraction(
            document_id=document_id,
            extraction_result=json.dumps(results),
            status="extracted",
            extraction_time_ms=extraction_time_ms,  # ✅ NEW: Save extraction time
        )

        return {
            "document_id": document_id,
            "results": results,
            "template_id": template_id,
        }

    def re_extract_document(self, document_id: int) -> Dict[str, Any]:
        """
        Re-extract an existing document (for experiment re-evaluation with updated model)

        Args:
            document_id: Document ID to re-extract

        Returns:
            Extraction results
        """
        # Get document
        document = self.document_repo.find_by_id(document_id)
        if not document:
            raise ValidationError(f"Document {document_id} not found")

        # Get file path
        filepath = document.file_path
        if not os.path.exists(filepath):
            raise ValidationError(f"File not found: {filepath}")

        # Load template config
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(db_manager=self.db)
        config = config_loader.load_config(document.template_id)
        if not config:
            raise ValidationError(
                f"Failed to load configuration for template {document.template_id}"
            )

        # Check if model exists for this template
        model_path = os.path.join(
            self.model_folder, f"template_{document.template_id}_model.joblib"
        )
        if not os.path.exists(model_path):
            model_path = None

        # Extract data
        try:
            extractor = DataExtractor(config, model_path)
            results = extractor.extract(filepath)
        except Exception as e:
            self.logger.error(f"❌ [ExtractionService] Error during re-extraction: {e}")
            raise

        # Update document with new results
        # Keep status as "validated" if it was already validated
        # This preserves the validation state for training purposes
        new_status = document.status if document.status == "validated" else "extracted"
        
        extraction_time_ms = results.get("extraction_time_ms", 0)
        self.document_repo.update_extraction(
            document_id=document_id,
            extraction_result=json.dumps(results),
            status=new_status,  # Preserve validated status
            extraction_time_ms=extraction_time_ms,
        )

        return {
            "document_id": document_id,
            "results": results,
            "template_id": document.template_id,
        }

    def save_corrections(self, document_id: int, corrections: Dict) -> Dict[str, Any]:
        """
        Save user corrections as feedback and trigger adaptive learning

        Args:
            document_id: Document ID
            corrections: Corrections dictionary

        Returns:
            Feedback info
        """
        # Get document
        document = self.document_repo.find_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document with ID {document_id} not found")

        # Load original extraction results
        original_results = json.loads(document.extraction_result)
        extracted_data = original_results.get("extracted_data", {})
        confidence_scores = original_results.get("confidence_scores", {})

        # ✅ FILTER: Only keep corrections where value actually changed
        actual_corrections = {}
        for field_name, corrected_value in corrections.items():
            if field_name not in extracted_data:
                self.logger.error(
                    f"❌ [ExtractionService] Field '{field_name}' not found in extracted data"
                )
                continue

            original_value = extracted_data.get(field_name, "")

            # Normalize for comparison (strip whitespace, normalize internal spaces)
            original_normalized = re.sub(r"\s+", " ", str(original_value).strip())
            corrected_normalized = re.sub(r"\s+", " ", str(corrected_value).strip())

            # Only save if values are different
            if original_normalized != corrected_normalized:
                actual_corrections[field_name] = corrected_value
                # Convert to string and safely slice for display
                # orig_display = str(original_value)[:50] if original_value else ""
                # corr_display = str(corrected_value)[:50] if corrected_value else ""
                # self.logger.info(f"  📝 Correction for '{field_name}': '{orig_display}' → '{corr_display}'")
            # else:
            # orig_display = str(original_value)[:50] if original_value else ""
            # self.logger.info(f"  ⏭️  Skipping '{field_name}': No change ('{orig_display}')")

        # If no actual corrections, skip feedback saving
        # if not actual_corrections:
        #     self.logger.warning(f"⚠️  No actual corrections for document {document_id}. Skipping feedback.")
        #     # Still mark as validated
        #     self.document_repo.update_status(document_id, "validated")
        #     return {
        #         "feedback_ids": [],
        #         "document_id": document_id,
        #         "corrections_count": 0,
        #         "skipped": True,
        #         "reason": "No actual changes detected",
        #     }

        # Save feedback (only actual corrections)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        feedback_filename = f"feedback_{document_id}_{timestamp}.json"
        feedback_path = os.path.join(self.feedback_folder, feedback_filename)

        feedback_data = {
            "document_id": document_id,
            "template_id": document.template_id,
            "original_results": original_results,
            "corrections": actual_corrections,  # ✅ Only actual corrections
            "timestamp": timestamp,
        }

        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=2)

        # Store feedback in database (one record per corrected field)
        # Uses UPSERT: updates existing feedback or creates new

        feedback_ids = self.feedback_repo.upsert(
            document_id=document_id,
            corrections=actual_corrections,  # ✅ Only actual corrections
            original_data=extracted_data,  # ✅ Pass original values
            confidence_scores=confidence_scores,  # ✅ Pass confidence scores
            feedback_path=feedback_path,
        )

        # ✅ KEEP original extraction_result unchanged in documents table
        # Corrected values are stored in feedback table
        # This preserves the original extraction for comparison and metrics

        # Note: To get validated data, query:
        # 1. Get extraction_result from documents table (original)
        # 2. Get corrections from feedback table
        # 3. Merge: use corrected_value if exists, else use original

        # Optional: Update metadata to mark as validated
        updated_results = original_results.copy()
        if "metadata" not in updated_results:
            updated_results["metadata"] = {}
        updated_results["metadata"]["validated"] = True
        updated_results["metadata"]["validated_at"] = timestamp
        updated_results["metadata"]["corrections_count"] = len(
            actual_corrections
        )  # ✅ Only actual corrections

        # Save metadata update (but keep extracted_data unchanged)
        self.document_repo.update_extraction_result(document_id, updated_results)

        # Update document status
        self.document_repo.update_status(document_id, "validated")

        # 🤖 AUTO-TRAINING: Trigger training if enabled
        # This ensures experiment scripts also trigger training
        auto_training_result = None
        try:
            # Check if AUTO_TRAINING is enabled (from environment or config)
            auto_training_enabled = os.getenv("AUTO_TRAINING", "True").lower() == "true"

            if auto_training_enabled:
                from core.learning.services import ModelService

                model_service = ModelService(self.db)

                model_service.trigger_adaptive_learning(
                    document_id, extracted_data, actual_corrections
                )

                from core.learning.auto_trainer import get_auto_training_service

                auto_trainer = get_auto_training_service(self.db)
                template_id = document.template_id

                # Check if model exists (for first training)
                model_path = os.path.join(
                    self.model_folder, f"template_{template_id}_model.joblib"
                )
                is_first_training = not os.path.exists(model_path)

                # Try to trigger training (will check thresholds internally)
                training_result = auto_trainer.check_and_train(
                    template_id=template_id,
                    model_folder=self.model_folder,
                    force_first_training=is_first_training,  # Allow first training
                )

                if training_result:
                    auto_training_result = {
                        "status": "completed",
                        "training_samples": training_result.get("training_samples", 0),
                        "accuracy": training_result.get("test_metrics", {}).get(
                            "accuracy", 0
                        ),
                    }
                    self.logger.info(
                        f"✅ Auto-training triggered for template {template_id}"
                    )
                else:
                    auto_training_result = {
                        "status": "skipped",
                        "message": "Training conditions not met",
                    }
        except Exception as e:
            self.logger.warning(f"⚠️  Auto-training failed: {e}")
            auto_training_result = {"status": "failed", "error": str(e)}

        # Return result with learning info
        result = {
            "feedback_ids": feedback_ids,
            "document_id": document_id,
            "corrections_count": len(actual_corrections),
            "all_fields": extracted_data,  # ✅ All extracted fields
            "corrected_fields": actual_corrections,  # ✅ Only corrected fields
        }

        if auto_training_result:
            result["auto_training"] = auto_training_result

        return result

    def get_all_documents(
        self, page: int = 1, page_size: int = 10, search: str = None, template_id=None
    ):
        if page_size < 1 or page_size > 100:
            page_size = 100
        if page < 1:
            page = 1

        """Get paginated documents"""
        documents, total_pages = self.document_repo.find_all(
            page,
            page_size,
            search,
            [{"field": "template_id", "operator": "=", "value": template_id}],
        )
        return documents, {
            "total_pages": total_pages,
            "page": page,
        }

    def get_document_by_id(self, document_id: int) -> Dict:
        """
        Get document by ID with parsed results and feedback history

        Args:
            document_id: Document ID

        Returns:
            Document data with feedback history or None if not found
        """
        document = self.document_repo.find_by_id(document_id)

        if not document:
            return None

        result = document.to_dict()

        # Parse extraction results if available
        if document.extraction_result:
            result["extraction_result"] = json.loads(document.extraction_result)

        # Get feedback history for this document
        feedback_history = self.feedback_repo.find_by_document_id(document_id)
        result["feedback_history"] = feedback_history

        return result
