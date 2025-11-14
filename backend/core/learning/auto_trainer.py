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
    MIN_NEW_DOCUMENTS = 1  # Minimum new documents to trigger retraining
    # MIN_HOURS_SINCE_LAST_TRAINING = 1  # Minimum hours between trainings
    FULL_RETRAIN_INTERVAL = 5  # Full retrain every N documents to use ALL feedback
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.feedback_repo = FeedbackRepository(db_manager)
        self.template_repo = TemplateRepository(db_manager)
        self.model_service = ModelService(db_manager)
    
    def check_and_train(self, template_id: int, model_folder: str = 'models') -> Optional[Dict]:
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
            print(f"⚠️  Template {template_id} not found")
            return None
        
        # 2. Get feedback statistics (document-based)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Count DISTINCT documents with unused feedback
        cursor.execute('''
            SELECT COUNT(DISTINCT f.document_id)
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.used_for_training = 0
        ''', (template_id,))
        unused_documents = cursor.fetchone()[0]
        
        # Get total fields per document for context
        cursor.execute('''
            SELECT COUNT(*) as field_count
            FROM feedback
            WHERE document_id IN (
                SELECT id FROM documents WHERE template_id = ? LIMIT 1
            )
        ''', (template_id,))
        fields_per_doc = cursor.fetchone()[0] or 9
        conn.close()
        
        print(f"\n🤖 AUTO-TRAINING CHECK for template {template_id}")
        print(f"   Unused documents: {unused_documents}")
        print(f"   Fields per document: ~{fields_per_doc}")
        print(f"   Total unused feedback: ~{unused_documents * fields_per_doc}")
        print(f"   Threshold: {self.MIN_NEW_DOCUMENTS} documents")
        
        # 3. Check if enough new documents
        if unused_documents < self.MIN_NEW_DOCUMENTS:
            print(f"   ⏸️  Not enough new documents (need {self.MIN_NEW_DOCUMENTS - unused_documents} more)")
            return None
        
        # 4. Check time since last training
        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
        if not os.path.exists(model_path):
            print(f"   ⏸️  Model not found for template {template_id}")
            return None
        #     last_modified = datetime.fromtimestamp(os.path.getmtime(model_path))
            # hours_since = (datetime.now() - last_modified).total_seconds() / 3600
            
            # print(f"   Last training: {hours_since:.1f} hours ago")
            # print(f"   Minimum interval: {self.MIN_HOURS_SINCE_LAST_TRAINING} hours")
            
            # if hours_since < self.MIN_HOURS_SINCE_LAST_TRAINING:
            #     print(f"   ⏸️  Too soon to retrain (wait {self.MIN_HOURS_SINCE_LAST_TRAINING - hours_since:.1f} more hours)")
            #     return None
        
        # 5. Determine training mode: Full or Incremental
        # Get total documents to check if periodic full retrain needed
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT f.document_id)
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        ''', (template_id,))
        total_documents = cursor.fetchone()[0]
        conn.close()
        
        # Check if periodic full retrain needed
        should_full_retrain = (total_documents % self.FULL_RETRAIN_INTERVAL) < unused_documents
        
        # 6. Trigger auto-retraining
        print(f"\n✅ AUTO-TRAINING TRIGGERED!")
        
        if should_full_retrain:
            print(f"   Mode: FULL RETRAIN (periodic refresh)")
            print(f"   Reason: Reached {total_documents} documents (interval: {self.FULL_RETRAIN_INTERVAL})")
            print(f"   Will use ALL feedback for optimal accuracy")
            use_all = True
            is_incr = False
        else:
            print(f"   Mode: INCREMENTAL (using only new feedback)")
            print(f"   Documents to train: {unused_documents}")
            print(f"   Estimated feedback: ~{unused_documents * fields_per_doc}")
            use_all = False
            is_incr = True
        
        print(f"   Starting training...")
        
        try:
            result = self.model_service.retrain_model(
                template_id=template_id,
                use_all_feedback=use_all,
                model_folder=model_folder,
                is_incremental=is_incr
            )
            
            print(f"\n🎉 AUTO-TRAINING COMPLETED!")
            print(f"   Training samples: {result['training_samples']}")
            print(f"   Test accuracy: {result['test_metrics']['accuracy']*100:.2f}%")
            
            return result
            
        except Exception as e:
            print(f"\n❌ AUTO-TRAINING FAILED: {e}")
            return None
    
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
        
        print(f"\n🔍 CHECKING {len(templates)} TEMPLATES FOR AUTO-TRAINING")
        print("=" * 80)
        
        for template in templates:
            template_id = template['id']
            result = self.check_and_train(template_id, model_folder)
            results[template_id] = result
        
        # Summary
        trained_count = sum(1 for r in results.values() if r is not None)
        print(f"\n📊 AUTO-TRAINING SUMMARY")
        print(f"   Templates checked: {len(templates)}")
        print(f"   Templates trained: {trained_count}")
        print(f"   Templates skipped: {len(templates) - trained_count}")
        
        return results


def get_auto_training_service(db_manager: DatabaseManager = None) -> AutoTrainingService:
    """Get auto-training service instance"""
    if db_manager is None:
        db_manager = DatabaseManager()
    return AutoTrainingService(db_manager)
