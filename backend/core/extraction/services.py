"""
Extraction Service
Business logic for document extraction
"""

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
    ) -> Dict[str, Any]:
        """
        Extract data from filled PDF document

        Args:
            file: Uploaded PDF file
            template_id: Template ID to use
            template_config_path: Path to template configuration (optional, for backward compatibility)

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
            template_id=template_id, filename=filename, file_path=filepath
        )

        # Check if model exists for this template
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
            print(f"❌ [ExtractionService] Error during extraction: {e}")
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
            "filename": filename,
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
                print(
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
                orig_display = str(original_value)[:50] if original_value else ""
                corr_display = str(corrected_value)[:50] if corrected_value else ""
                print(
                    f"  📝 Correction for '{field_name}': '{orig_display}' → '{corr_display}'"
                )
            else:
                orig_display = str(original_value)[:50] if original_value else ""
                print(f"  ⏭️  Skipping '{field_name}': No change ('{orig_display}')")

        # If no actual corrections, skip feedback saving
        if not actual_corrections:
            print(
                f"⚠️  No actual corrections for document {document_id}. Skipping feedback."
            )
            # Still mark as validated
            self.document_repo.update_status(document_id, "validated")
            return {
                "feedback_ids": [],
                "document_id": document_id,
                "corrections_count": 0,
                "skipped": True,
                "reason": "No actual changes detected",
            }

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

        # 🎯 ADAPTIVE LEARNING: Learn from feedback
        # This improves future extractions for this template
        try:
            # Load template config from database or JSON
            from core.templates.config_loader import get_config_loader
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            template = self.template_repo.find_by_id(document.template_id)

            if template:
                config_loader = get_config_loader(db_manager=db)
                config = config_loader.load_config(
                    template_id=document.template_id,
                    config_path=template.config_path,
                )

                if config:
                    # Check if model exists
                    model_path = os.path.join(
                        self.model_folder,
                        f"template_{document.template_id}_model.joblib",
                    )
                    if not os.path.exists(model_path):
                        model_path = None

                    # Create extractor and learn from feedback (only actual corrections)
                    extractor = DataExtractor(config, model_path)
                    extractor.learn_from_feedback(original_results, actual_corrections)

        except Exception as e:
            print(f"⚠️  Adaptive learning failed: {e}")

        # Return result with learning info
        return {
            "feedback_ids": feedback_ids,
            "document_id": document_id,
            "corrections_count": len(actual_corrections),
            "all_fields": extracted_data,  # ✅ All extracted fields
            "corrected_fields": actual_corrections,  # ✅ Only corrected fields
        }

    def _check_and_trigger_retraining(self, template_id: int, db):
        """
        Check if automatic retraining should be triggered with safeguards

        Triggers retraining when:
        1. Unused feedback >= 100 records (batch threshold)
        2. Model exists (not first training)
        3. No recent training (< 1 hour ago) - GLOBAL LOCK
        4. SAFEGUARD: New model must have accuracy >= current model - 5%

        Args:
            template_id: Template ID
            db: Database manager instance
        """
        global _retrain_lock, _last_retrain_time

        # ✅ CRITICAL: Try to acquire lock (non-blocking)
        # If another thread is retraining, skip immediately
        if not _retrain_lock.acquire(blocking=False):
            print(f"\n🔒 [Auto-Retrain] Another retrain in progress, skipping...")
            return

        try:
            # ✅ SAFEGUARD 0: Check cooldown (prevent rapid retraining)
            MIN_RETRAIN_INTERVAL_SECONDS = 3600  # 1 hour
            current_time = time.time()
            last_retrain = _last_retrain_time.get(template_id, 0)
            time_since_last = current_time - last_retrain

            if time_since_last < MIN_RETRAIN_INTERVAL_SECONDS:
                remaining = MIN_RETRAIN_INTERVAL_SECONDS - time_since_last
                print(f"\n⏳ [Auto-Retrain] Cooldown active")
                print(f"   Last retrain: {time_since_last/60:.1f} min ago")
                print(f"   Remaining: {remaining/60:.1f} min")
                return

            # Get unused feedback count
            unused_feedback = self.feedback_repo.find_for_training(
                template_id, unused_only=True
            )
            unused_count = len(unused_feedback)

            print(f"\n🔍 [Auto-Retrain Check] Template {template_id}:")
            print(f"   Unused feedback: {unused_count}")

            # ✅ SAFEGUARD 1: Higher threshold (100 instead of 50)
            RETRAIN_THRESHOLD = 100
            if unused_count < RETRAIN_THRESHOLD:
                print(
                    f"   ⏳ Threshold not reached ({unused_count}/{RETRAIN_THRESHOLD})"
                )
                return

            # Check if model exists (skip first training)
            model_path = os.path.join(
                self.model_folder, f"template_{template_id}_model.joblib"
            )
            if not os.path.exists(model_path):
                print(
                    f"   ⏭️  No existing model, skipping auto-retrain (use manual training first)"
                )
                return

            # ✅ SAFEGUARD 2: Get current model accuracy
            training_history = self.training_repo.find_by_template_id(template_id)
            current_accuracy = 0.0
            if training_history:
                current_accuracy = training_history[0].get("accuracy", 0.0)
                print(f"   📊 Current model accuracy: {current_accuracy*100:.2f}%")

            # ✅ SAFEGUARD 3: Backup current model before retraining
            import shutil

            backup_path = model_path.replace(".joblib", "_backup.joblib")
            if os.path.exists(model_path):
                shutil.copy2(model_path, backup_path)
                print(f"   💾 Backed up current model to: {backup_path}")

            # Trigger retraining
            print(f"\n🚀 [Auto-Retrain] Triggering automatic retraining...")
            print(f"   Reason: {unused_count} unused feedback records")

            from core.learning import ModelService

            model_service = ModelService(db)

            result = model_service.retrain_model(
                template_id=template_id,
                use_all_feedback=True,  # ✅ Use ALL feedback for stability
                model_folder=self.model_folder,
                is_incremental=False,  # ✅ Full retrain for better quality
                force_validation=False,
            )

            new_accuracy = result.get("test_metrics", {}).get("accuracy", 0.0)

            # ✅ SAFEGUARD 4: Validate new model accuracy
            MIN_ACCURACY_DROP = 0.05  # Allow max 5% drop
            if new_accuracy < (current_accuracy - MIN_ACCURACY_DROP):
                print(f"\n⚠️ [Auto-Retrain] REJECTED - Accuracy dropped too much!")
                print(f"   Current: {current_accuracy*100:.2f}%")
                print(f"   New: {new_accuracy*100:.2f}%")
                print(f"   Drop: {(current_accuracy - new_accuracy)*100:.2f}%")
                print(f"   Threshold: {MIN_ACCURACY_DROP*100:.2f}%")

                # Restore backup
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, model_path)
                    print(f"   ↩️  Restored backup model")

                return

            print(f"\n✅ [Auto-Retrain] Completed successfully!")
            print(f"   Training samples: {result['training_samples']}")
            print(f"   Current accuracy: {current_accuracy*100:.2f}%")
            print(f"   New accuracy: {new_accuracy*100:.2f}%")
            print(f"   Change: {(new_accuracy - current_accuracy)*100:+.2f}%")
            print(f"   Model: {result['model_path']}")

            # ✅ Update last retrain timestamp
            _last_retrain_time[template_id] = time.time()

            # Clean up backup if successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
                print(f"   🗑️  Removed backup (new model accepted)")

        except Exception as e:
            print(f"⚠️ [Auto-Retrain] Failed: {e}")
            # Restore backup if exists
            backup_path = os.path.join(
                self.model_folder, f"template_{template_id}_model_backup.joblib"
            )
            model_path = os.path.join(
                self.model_folder, f"template_{template_id}_model.joblib"
            )
            if os.path.exists(backup_path):
                import shutil

                shutil.copy2(backup_path, model_path)
                print(f"   ↩️  Restored backup model due to error")

            # Don't fail the whole operation if auto-retrain fails
            import traceback

            traceback.print_exc()

        finally:
            # ✅ CRITICAL: Always release lock
            _retrain_lock.release()
            print(f"🔓 [Auto-Retrain] Lock released")

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
