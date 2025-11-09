"""
Strategy Performance Service

Business logic for strategy performance tracking and analysis.
"""
from typing import Dict, Any, List, Optional
from database.db_manager import DatabaseManager
from database.repositories.strategy_performance_repository import StrategyPerformanceRepository


class StrategyPerformanceService:
    """Service layer for strategy performance operations"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.repo = StrategyPerformanceRepository(self.db)
    
    def get_template_performance(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Get all performance data for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            List of performance records
        """
        return self.repo.get_template_performance(template_id)
    
    def get_field_performance(self, template_id: int, field_name: str) -> List[Dict[str, Any]]:
        """
        Get performance for all strategies for a specific field
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            List of performance records sorted by accuracy
        """
        return self.repo.get_field_performance(template_id, field_name)
    
    def get_strategy_stats(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Get aggregated statistics for each strategy
        
        Args:
            template_id: Template ID
            
        Returns:
            List of strategy statistics
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    strategy_type,
                    COUNT(DISTINCT field_name) as total_fields,
                    ROUND(AVG(accuracy) * 100, 2) as avg_accuracy_pct,
                    SUM(total_extractions) as total_extractions,
                    SUM(correct_extractions) as total_correct
                FROM strategy_performance
                WHERE template_id = ?
                GROUP BY strategy_type
                ORDER BY avg_accuracy_pct DESC
            """, (template_id,))
            
            stats = []
            for row in cursor.fetchall():
                # Get best and worst fields for this strategy
                cursor.execute("""
                    SELECT field_name, accuracy
                    FROM strategy_performance
                    WHERE template_id = ? AND strategy_type = ?
                    ORDER BY accuracy DESC
                    LIMIT 1
                """, (template_id, row['strategy_type']))
                best = cursor.fetchone()
                
                cursor.execute("""
                    SELECT field_name, accuracy
                    FROM strategy_performance
                    WHERE template_id = ? AND strategy_type = ?
                    ORDER BY accuracy ASC
                    LIMIT 1
                """, (template_id, row['strategy_type']))
                worst = cursor.fetchone()
                
                stats.append({
                    'strategy_type': row['strategy_type'],
                    'total_fields': row['total_fields'],
                    'avg_accuracy': row['avg_accuracy_pct'],
                    'total_extractions': row['total_extractions'],
                    'total_correct': row['total_correct'],
                    'best_field': best['field_name'] if best else None,
                    'best_field_accuracy': round(best['accuracy'] * 100, 2) if best else None,
                    'worst_field': worst['field_name'] if worst else None,
                    'worst_field_accuracy': round(worst['accuracy'] * 100, 2) if worst else None
                })
            
            return stats
        finally:
            conn.close()
    
    def get_field_comparison(self, template_id: int, field_name: str) -> Dict[str, Any]:
        """
        Compare all strategies for a specific field
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            Comparison data with best strategy
        """
        performances = self.repo.get_field_performance(template_id, field_name)
        
        if not performances:
            return {
                'field_name': field_name,
                'strategies': [],
                'best_strategy': None,
                'best_accuracy': 0.0
            }
        
        # Format for response
        strategies = [
            {
                'strategy_type': p['strategy_type'],
                'accuracy': round(p['accuracy'] * 100, 2),
                'total_extractions': p['total_extractions'],
                'correct_extractions': p['correct_extractions']
            }
            for p in performances
        ]
        
        best = performances[0]  # Already sorted by accuracy DESC
        
        return {
            'field_name': field_name,
            'strategies': strategies,
            'best_strategy': best['strategy_type'],
            'best_accuracy': round(best['accuracy'] * 100, 2)
        }
    
    def get_all_fields_comparison(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Get comparison for all fields
        
        Args:
            template_id: Template ID
            
        Returns:
            List of field comparisons
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all unique fields
            cursor.execute("""
                SELECT DISTINCT field_name
                FROM strategy_performance
                WHERE template_id = ?
                ORDER BY field_name
            """, (template_id,))
            
            fields = [row['field_name'] for row in cursor.fetchall()]
            
            # Get comparison for each field
            comparisons = []
            for field_name in fields:
                comparison = self.get_field_comparison(template_id, field_name)
                comparisons.append(comparison)
            
            return comparisons
        finally:
            conn.close()
    
    def update_performance(
        self,
        template_id: int,
        field_name: str,
        strategy_type: str,
        was_correct: bool
    ) -> None:
        """
        Update performance for a strategy
        
        Args:
            template_id: Template ID
            field_name: Field name
            strategy_type: Strategy type
            was_correct: Whether extraction was correct
        """
        self.repo.update_performance(template_id, field_name, strategy_type, was_correct)
