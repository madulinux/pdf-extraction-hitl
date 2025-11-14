"""
Pattern Cleaner Service
Automatically deactivates or removes poorly performing learned patterns
"""
import logging
from typing import Dict, List, Optional
from database.db_manager import DatabaseManager
from database.repositories.config_repository import ConfigRepository


class PatternCleaner:
    """Handles cleanup of poorly performing learned patterns"""
    
    def __init__(self, db_manager: DatabaseManager, config_repository: Optional[ConfigRepository] = None):
        """
        Initialize pattern cleaner
        
        Args:
            db_manager: DatabaseManager instance
            config_repository: ConfigRepository instance (optional)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db_manager
        self.config_repo = config_repository
        
        if not self.config_repo:
            self.config_repo = ConfigRepository(self.db)
        
        # Cleanup thresholds
        self.min_usage_for_evaluation = 10  # Minimum usage before evaluating
        self.min_success_rate = 0.3  # 30% success rate minimum
        self.negative_confidence_threshold = -0.2  # Deactivate if confidence < -0.2
        self.max_inactive_days = 30  # Remove if inactive for 30 days
    
    def cleanup_poor_patterns(
        self,
        template_id: Optional[int] = None,
        field_name: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Clean up poorly performing patterns
        
        Args:
            template_id: Optional template ID to filter
            field_name: Optional field name to filter
            dry_run: If True, only report what would be cleaned
            
        Returns:
            Dict with cleanup results
        """
        self.logger.info(f"🧹 Starting pattern cleanup (dry_run={dry_run})")
        
        results = {
            'deactivated': [],
            'deleted': [],
            'kept': [],
            'total_evaluated': 0
        }
        
        try:
            # Get all active patterns
            patterns = self._get_patterns_for_cleanup(template_id, field_name)
            results['total_evaluated'] = len(patterns)
            
            self.logger.info(f"Found {len(patterns)} patterns to evaluate")
            
            for pattern in patterns:
                action = self._evaluate_pattern(pattern)
                
                if action == 'deactivate':
                    if not dry_run:
                        self._deactivate_pattern(pattern['id'])
                    results['deactivated'].append({
                        'id': pattern['id'],
                        'field_name': pattern['field_name'],
                        'pattern': pattern['pattern'][:50],
                        'reason': self._get_deactivation_reason(pattern)
                    })
                    
                elif action == 'delete':
                    if not dry_run:
                        self._delete_pattern(pattern['id'])
                    results['deleted'].append({
                        'id': pattern['id'],
                        'field_name': pattern['field_name'],
                        'pattern': pattern['pattern'][:50],
                        'reason': 'Inactive for too long'
                    })
                    
                else:
                    results['kept'].append(pattern['id'])
            
            self.logger.info(
                f"✅ Cleanup complete: "
                f"{len(results['deactivated'])} deactivated, "
                f"{len(results['deleted'])} deleted, "
                f"{len(results['kept'])} kept"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during pattern cleanup: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_patterns_for_cleanup(
        self,
        template_id: Optional[int],
        field_name: Optional[str]
    ) -> List[Dict]:
        """Get patterns that need evaluation"""
        
        query = """
            SELECT 
                lp.id,
                lp.pattern,
                lp.pattern_type,
                lp.usage_count,
                lp.success_count,
                lp.confidence_boost,
                lp.is_active,
                lp.last_used_at,
                lp.added_at,
                fc.field_name,
                c.template_id
            FROM learned_patterns lp
            JOIN field_configs fc ON lp.field_config_id = fc.id
            JOIN template_configs c ON fc.config_id = c.id
            WHERE 1=1
        """
        
        params = []
        
        if template_id:
            query += " AND c.template_id = ?"
            params.append(template_id)
        
        if field_name:
            query += " AND fc.field_name = ?"
            params.append(field_name)
        
        query += " ORDER BY lp.usage_count DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def _evaluate_pattern(self, pattern: Dict) -> str:
        """
        Evaluate if pattern should be kept, deactivated, or deleted
        
        Returns:
            'keep', 'deactivate', or 'delete'
        """
        usage_count = pattern.get('usage_count', 0)
        success_count = pattern.get('success_count', 0)
        confidence_boost = pattern.get('confidence_boost', 0.0)
        is_active = pattern.get('is_active', 1)
        last_used_at = pattern.get('last_used_at')
        
        # Rule 1: Delete if inactive for too long
        if not is_active and last_used_at:
            from datetime import datetime, timedelta
            try:
                last_used = datetime.fromisoformat(last_used_at)
                days_inactive = (datetime.now() - last_used).days
                
                if days_inactive > self.max_inactive_days:
                    return 'delete'
            except:
                pass
        
        # Rule 2: Not enough usage to evaluate
        if usage_count < self.min_usage_for_evaluation:
            return 'keep'
        
        # Rule 3: Calculate success rate
        success_rate = success_count / usage_count if usage_count > 0 else 0.0
        
        # Rule 4: Deactivate if very negative confidence
        if confidence_boost < self.negative_confidence_threshold:
            self.logger.warning(
                f"⚠️ Pattern {pattern['id']} has negative confidence: {confidence_boost:.3f}"
            )
            return 'deactivate'
        
        # Rule 5: Deactivate if low success rate
        if success_rate < self.min_success_rate:
            self.logger.warning(
                f"⚠️ Pattern {pattern['id']} has low success rate: {success_rate:.1%}"
            )
            return 'deactivate'
        
        return 'keep'
    
    def _get_deactivation_reason(self, pattern: Dict) -> str:
        """Get human-readable reason for deactivation"""
        usage_count = pattern.get('usage_count', 0)
        success_count = pattern.get('success_count', 0)
        confidence_boost = pattern.get('confidence_boost', 0.0)
        
        success_rate = success_count / usage_count if usage_count > 0 else 0.0
        
        reasons = []
        
        if confidence_boost < self.negative_confidence_threshold:
            reasons.append(f"negative confidence ({confidence_boost:.3f})")
        
        if success_rate < self.min_success_rate:
            reasons.append(f"low success rate ({success_rate:.1%})")
        
        return ", ".join(reasons) if reasons else "unknown"
    
    def _deactivate_pattern(self, pattern_id: int):
        """Deactivate a pattern"""
        query = """
            UPDATE learned_patterns
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self.db.execute_update(query, (pattern_id,))
        self.logger.info(f"🔴 Deactivated pattern {pattern_id}")
    
    def _delete_pattern(self, pattern_id: int):
        """Delete a pattern permanently"""
        query = "DELETE FROM learned_patterns WHERE id = ?"
        self.db.execute_update(query, (pattern_id,))
        self.logger.info(f"🗑️ Deleted pattern {pattern_id}")
    
    def get_cleanup_report(
        self,
        template_id: Optional[int] = None
    ) -> Dict:
        """
        Get report of patterns that need cleanup
        
        Args:
            template_id: Optional template ID to filter
            
        Returns:
            Dict with statistics
        """
        patterns = self._get_patterns_for_cleanup(template_id, None)
        
        report = {
            'total_patterns': len(patterns),
            'needs_deactivation': 0,
            'needs_deletion': 0,
            'healthy': 0,
            'details': []
        }
        
        for pattern in patterns:
            action = self._evaluate_pattern(pattern)
            
            if action == 'deactivate':
                report['needs_deactivation'] += 1
                report['details'].append({
                    'id': pattern['id'],
                    'field_name': pattern['field_name'],
                    'pattern': pattern['pattern'][:50],
                    'action': 'deactivate',
                    'reason': self._get_deactivation_reason(pattern),
                    'usage_count': pattern.get('usage_count', 0),
                    'success_count': pattern.get('success_count', 0),
                    'confidence_boost': pattern.get('confidence_boost', 0.0)
                })
            elif action == 'delete':
                report['needs_deletion'] += 1
                report['details'].append({
                    'id': pattern['id'],
                    'field_name': pattern['field_name'],
                    'pattern': pattern['pattern'][:50],
                    'action': 'delete',
                    'reason': 'Inactive for too long'
                })
            else:
                report['healthy'] += 1
        
        return report


def get_pattern_cleaner(db_manager: DatabaseManager) -> PatternCleaner:
    """Factory function to get PatternCleaner instance"""
    return PatternCleaner(db_manager)
