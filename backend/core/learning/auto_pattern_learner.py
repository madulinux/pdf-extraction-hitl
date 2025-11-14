"""
Auto Pattern Learner

Automatically triggers pattern learning after feedback submission.
Runs in background to avoid blocking user requests.
"""
import logging
from typing import Dict, Optional
from datetime import datetime
import threading


class AutoPatternLearner:
    """
    Automatically learns patterns from feedback
    """
    
    def __init__(self, db_manager, config_repository=None):
        """
        Initialize auto pattern learner
        
        Args:
            db_manager: DatabaseManager instance
            config_repository: ConfigRepository instance (optional)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db_manager
        self.config_repo = config_repository
        
        if not self.config_repo:
            from database.repositories.config_repository import ConfigRepository
            self.config_repo = ConfigRepository(self.db)
        
        # Learning thresholds
        self.min_feedback_count = 5  # Minimum feedback before learning
        self.min_pattern_frequency = 3  # Minimum pattern frequency
        self.max_patterns_per_field = 5  # Maximum patterns to apply
    
    def should_trigger_learning(
        self,
        template_id: int,
        field_name: str
    ) -> bool:
        """
        Check if pattern learning should be triggered
        
        ✅ NEW: Trigger based on DOCUMENT COUNT instead of feedback count
        This is more reliable because:
        - Documents with validated data contribute to learning
        - Not all documents have feedback (correct extractions don't need feedback)
        - Consistent with learning from validated data
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            True if learning should be triggered
        """
        try:
            # Count validated documents since last learning
            # Include both: documents with feedback + documents without feedback (validated)
            query = """
                SELECT COUNT(DISTINCT d.id) as document_count
                FROM documents d
                WHERE d.template_id = ?
                  AND d.status = 'validated'
                  AND d.created_at > COALESCE(
                      (SELECT MAX(completed_at) 
                       FROM pattern_learning_jobs 
                       WHERE template_id = ? 
                         AND field_name = ? 
                         AND status = 'completed'),
                      '2000-01-01'
                  )
            """
            
            result = self.db.execute_query(
                query,
                (template_id, template_id, field_name)
            )
            
            document_count = result[0]['document_count'] if result else 0
            
            if document_count >= self.min_feedback_count:  # Reuse threshold (5 documents)
                self.logger.info(
                    f"✅ Trigger condition met for {field_name}: "
                    f"{document_count} new validated documents (threshold: {self.min_feedback_count})"
                )
                return True
            else:
                self.logger.debug(
                    f"⏳ Not enough documents for {field_name}: "
                    f"{document_count}/{self.min_feedback_count}"
                )
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking trigger condition: {e}")
            return False
    
    def trigger_learning(
        self,
        template_id: int,
        field_name: str,
        async_mode: bool = True
    ) -> Optional[Dict]:
        """
        Trigger pattern learning for a field
        
        Args:
            template_id: Template ID
            field_name: Field name
            async_mode: Run in background thread
            
        Returns:
            Result dict or None if async
        """
        if async_mode:
            # Run in background thread
            thread = threading.Thread(
                target=self._run_learning,
                args=(template_id, field_name),
                daemon=True
            )
            thread.start()
            self.logger.info(f"🚀 Started background learning for {field_name}")
            return None
        else:
            # Run synchronously
            return self._run_learning(template_id, field_name)
    
    def _run_learning(
        self,
        template_id: int,
        field_name: str
    ) -> Dict:
        """
        Run pattern learning process
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            Result dict
        """
        try:
            self.logger.info(f"🔍 Starting pattern learning for {field_name}")
            
            # Import here to avoid circular dependency
            from core.extraction.rule_optimizer import RulePatternOptimizer
            
            optimizer = RulePatternOptimizer(
                db_manager=self.db,
                config_repository=self.config_repo
            )
            
            # Analyze patterns
            analysis = optimizer.analyze_feedback_patterns(
                template_id=template_id,
                field_name=field_name,
                min_frequency=self.min_pattern_frequency
            )
            
            if not analysis or not analysis.get('suggestions'):
                self.logger.info(f"ℹ️ No patterns discovered for {field_name}")
                return {
                    'success': True,
                    'patterns_discovered': 0,
                    'patterns_applied': 0,
                    'message': 'No patterns discovered'
                }
            
            # Get top patterns
            suggestions = analysis['suggestions'][:self.max_patterns_per_field]
            
            self.logger.info(
                f"💡 Discovered {len(analysis['suggestions'])} patterns, "
                f"applying top {len(suggestions)}"
            )
            
            # Apply patterns to database
            result = optimizer.apply_patterns_to_db(
                template_id=template_id,
                field_name=field_name,
                patterns=suggestions,
                job_type='auto'
            )
            
            if result.get('success'):
                self.logger.info(
                    f"✅ Pattern learning completed for {field_name}: "
                    f"{result.get('patterns_added', 0)} patterns applied"
                )
                
                # ✅ NEW: Auto-cleanup poorly performing patterns after learning
                try:
                    from core.learning.pattern_cleaner import get_pattern_cleaner
                    
                    cleaner = get_pattern_cleaner(self.db)
                    cleanup_result = cleaner.cleanup_poor_patterns(
                        template_id=template_id,
                        field_name=field_name,
                        dry_run=False
                    )
                    
                    if cleanup_result.get('deactivated') or cleanup_result.get('deleted'):
                        self.logger.info(
                            f"🧹 Pattern cleanup: "
                            f"{len(cleanup_result.get('deactivated', []))} deactivated, "
                            f"{len(cleanup_result.get('deleted', []))} deleted"
                        )
                        result['cleanup'] = cleanup_result
                    
                except Exception as e:
                    self.logger.warning(f"Pattern cleanup failed: {e}")
                    # Don't fail learning if cleanup fails
                
            else:
                self.logger.error(
                    f"❌ Pattern learning failed for {field_name}: "
                    f"{result.get('error', 'Unknown error')}"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during pattern learning: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_learning_for_template(
        self,
        template_id: int,
        async_mode: bool = True
    ) -> Dict:
        """
        Trigger learning for all fields in a template
        
        Args:
            template_id: Template ID
            async_mode: Run in background
            
        Returns:
            Summary dict
        """
        try:
            # Get all fields with sufficient feedback
            query = """
                SELECT 
                    f.field_name,
                    COUNT(*) as feedback_count
                FROM feedback f
                JOIN documents d ON f.document_id = d.id
                WHERE d.template_id = ?
                  AND f.created_at > COALESCE(
                      (SELECT MAX(completed_at) 
                       FROM pattern_learning_jobs 
                       WHERE template_id = ? 
                         AND field_name = f.field_name 
                         AND status = 'completed'),
                      '2000-01-01'
                  )
                GROUP BY f.field_name
                HAVING COUNT(*) >= ?
            """
            
            fields = self.db.execute_query(
                query,
                (template_id, template_id, self.min_feedback_count)
            )
            
            if not fields:
                self.logger.info(f"No fields ready for learning in template {template_id}")
                return {
                    'success': True,
                    'fields_processed': 0,
                    'message': 'No fields ready for learning'
                }
            
            self.logger.info(
                f"🎯 Triggering learning for {len(fields)} fields in template {template_id}"
            )
            
            results = []
            for field in fields:
                field_name = field['field_name']
                result = self.trigger_learning(
                    template_id=template_id,
                    field_name=field_name,
                    async_mode=async_mode
                )
                if result:  # Only if sync mode
                    results.append({
                        'field_name': field_name,
                        'result': result
                    })
            
            return {
                'success': True,
                'fields_processed': len(fields),
                'results': results if results else None
            }
            
        except Exception as e:
            self.logger.error(f"Error triggering template learning: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
_auto_learner_instance = None


def get_auto_learner(db_manager=None):
    """
    Get singleton auto learner instance
    
    Args:
        db_manager: DatabaseManager instance (required for first call)
        
    Returns:
        AutoPatternLearner instance
    """
    global _auto_learner_instance
    
    if _auto_learner_instance is None:
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        
        _auto_learner_instance = AutoPatternLearner(db_manager)
    
    return _auto_learner_instance
