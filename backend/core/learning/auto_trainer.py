"""
Auto-Training Service
Automatically triggers model retraining when sufficient new feedback is collected
"""
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.template_repository import TemplateRepository
from core.learning.services import ModelService
import logging

class AutoTrainingService:
    """
    Service for automatic model retraining based on feedback accumulation
    """
    
    # ✅ IMPROVED: Use document count instead of feedback count
    # Rationale:
    # - Different templates have different field counts (5-30 fields)
    # - Feedback count is inconsistent across templates
    # - Document count ensures consistent training quality
    # 
    # Example:
    # - Template A (9 fields): 20 docs = 180 feedback → Good training
    # - Template B (25 fields): 1 doc = 25 feedback → BAD training!
    # 
    # Solution: Threshold based on DOCUMENT count, not feedback count
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        self.template_repo = TemplateRepository(db_manager)
        self.model_service = ModelService(db_manager)
        
        # Load config from environment (centralized in config.py)
        self.MIN_NEW_DOCUMENTS = int(os.getenv('MIN_NEW_DOCUMENTS', '5'))
        self.FULL_RETRAIN_INTERVAL = int(os.getenv('FULL_RETRAIN_INTERVAL', '20'))
        
        self.logger.info(f"Auto-training config: MIN_NEW_DOCUMENTS={self.MIN_NEW_DOCUMENTS}, FULL_RETRAIN_INTERVAL={self.FULL_RETRAIN_INTERVAL}")
    
    def check_and_train(self, template_id: int, model_folder: str = 'models', force_first_training: bool = False) -> Optional[Dict]:
        """
        Check if auto-retraining should be triggered and execute if conditions are met
        
        Args:
            template_id: Template ID to check
            model_folder: Folder where models are stored
            
        Returns:
            Training result if triggered, None otherwise
        """
        # 1. Check if template exists
        template = self.template_repo.find_by_id(template_id)
        if not template:
            self.logger.error(f"❌ Template {template_id} not found")
            return None
        
        # 2. Get validated documents statistics
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # ✅ Count validated documents that haven't been used for training yet
        # This approach works for both:
        # - Documents with corrections (have feedback records)
        # - Documents validated as "all correct" (no feedback records)
        cursor.execute('''
            SELECT COUNT(*)
            FROM documents
            WHERE template_id = ? 
              AND status = 'validated'
              AND used_for_training = 0
        ''', (template_id,))
        unused_documents = cursor.fetchone()[0]
        
        # Get total validated documents
        cursor.execute('''
            SELECT COUNT(*)
            FROM documents
            WHERE template_id = ? AND status = 'validated'
        ''', (template_id,))
        total_validated = cursor.fetchone()[0]
        
        conn.close()
        
        self.logger.info(f"\n🤖 Auto-training check: template {template_id} ({unused_documents} new validated docs, {total_validated} total)")
        
        # 3. Check if enough new documents
        if unused_documents < self.MIN_NEW_DOCUMENTS:
            self.logger.info(f"   ⏸️  Not enough new validated documents ({unused_documents} < {self.MIN_NEW_DOCUMENTS})")
            return None
        
        # 4. Check if model exists
        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
        model_exists = os.path.exists(model_path)
        
        if not model_exists and not force_first_training:
            self.logger.error(f"❌ Model {model_path} not found (use force_first_training=True for initial training)")
            return None
        
        # For first training, proceed even if model doesn't exist
        if not model_exists:
            self.logger.info(f"🆕 First training - model will be created at {model_path}")
        #     last_modified = datetime.fromtimestamp(os.path.getmtime(model_path))
            # hours_since = (datetime.now() - last_modified).total_seconds() / 3600
            
            # print(f"   Last training: {hours_since:.1f} hours ago")
            # print(f"   Minimum interval: {self.MIN_HOURS_SINCE_LAST_TRAINING} hours")
            
            # if hours_since < self.MIN_HOURS_SINCE_LAST_TRAINING:
            #     print(f"   ⏸️  Too soon to retrain (wait {self.MIN_HOURS_SINCE_LAST_TRAINING - hours_since:.1f} more hours)")
            #     return None
        
        # 5. Determine training mode: Full or Incremental
        # Check if periodic full retrain needed based on total validated documents
        should_full_retrain = (total_validated % self.FULL_RETRAIN_INTERVAL) < unused_documents
        
        # 6. Trigger auto-retraining
        if should_full_retrain:
            self.logger.info(f"\n✅ Auto-training: FULL retrain ({total_validated} docs)")
            use_all = True
            is_incr = False
        else:
            self.logger.info(f"\n✅ Auto-training: INCREMENTAL ({unused_documents} new docs)")
            use_all = False
            is_incr = True
        
        conn = None
        try:
            result = self.model_service.retrain_model(
                template_id=template_id,
                use_all_feedback=use_all,
                model_folder=model_folder,
                is_incremental=is_incr
            )
            
            # Handle None metrics from incremental training without evaluation
            accuracy = result['test_metrics'].get('accuracy')
            if accuracy is not None:
                self.logger.info(f"✅ Auto-training completed: {result['training_samples']} samples, {accuracy*100:.2f}% accuracy")
            else:
                self.logger.info(f"✅ Auto-training completed: {result['training_samples']} samples (metrics not evaluated)")
            
            # ✅ TRANSACTION: Mark validated documents and their feedback as used for training
            # Only commit if everything succeeds (training + logging)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Mark documents
            cursor.execute('''
                UPDATE documents
                SET used_for_training = 1
                WHERE template_id = ? AND status = 'validated' AND used_for_training = 0
            ''', (template_id,))
            updated_docs = cursor.rowcount
            
            # Mark feedback records for these documents
            cursor.execute('''
                UPDATE feedback
                SET used_for_training = 1
                WHERE document_id IN (
                    SELECT id FROM documents 
                    WHERE template_id = ? AND status = 'validated'
                )
                AND used_for_training = 0
            ''', (template_id,))
            updated_feedback = cursor.rowcount
            
            # ✅ COMMIT only after all operations succeed
            conn.commit()
            
            self.logger.info(f"   Marked {updated_docs} documents and {updated_feedback} feedback records as used for training")
            
            return result
            
        except Exception as e:
            # ✅ ROLLBACK transaction if any error occurs
            if conn:
                conn.rollback()
                self.logger.warning("   Transaction rolled back - documents not marked as used")
            
            self.logger.error(f"❌ Auto-training failed: {e}")
            # Re-raise exception so worker can properly handle it and mark job as failed
            raise
        finally:
            # ✅ Always close connection
            if conn:
                conn.close()
    
    def check_all_templates(self, model_folder: str = 'models') -> Dict[int, Optional[Dict]]:
        """
        Check and train all templates that meet auto-training criteria
        
        Args:
            model_folder: Folder where models are stored
            
        Returns:
            Dictionary of template_id -> training result
        """
        results = {}
        
        # Get all templates
        templates = self.template_repo.find_all()
        
        print(f"\n🔍 Checking {len(templates)} templates for auto-training...")
        
        for template in templates:
            template_id = template['id']
            result = self.check_and_train(template_id, model_folder)
            results[template_id] = result
        
        # Summary
        trained_count = sum(1 for r in results.values() if r is not None)
        print(f"\n📊 Summary: {trained_count}/{len(templates)} templates trained")
        
        return results


def get_auto_training_service(db_manager: DatabaseManager = None) -> AutoTrainingService:
    """Get auto-training service instance"""
    if db_manager is None:
        db_manager = DatabaseManager()
    return AutoTrainingService(db_manager)
