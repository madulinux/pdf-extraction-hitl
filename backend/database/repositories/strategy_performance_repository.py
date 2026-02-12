"""
Strategy Performance Repository

Handles database operations for strategy performance tracking.
"""

from typing import Dict, List, Optional
from datetime import datetime


class StrategyPerformanceRepository:
    """Repository for strategy performance data"""
    
    def __init__(self, db_manager):
        """
        Initialize repository
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager

    def _current_user_id(self):
        try:
            from flask import g

            return getattr(g, 'user_id', None)
        except Exception:
            return None
    
    def update_performance(
        self,
        template_id: int,
        field_name: str,
        strategy_type: str,
        was_correct: bool
    ) -> None:
        """
        Update performance metrics for a strategy
        
        Args:
            template_id: Template ID
            field_name: Field name
            strategy_type: Strategy type (e.g., 'crf', 'rule_based', 'position_based')
            was_correct: Whether the extraction was correct
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        
        try:
            # Check if record exists
            cursor.execute("""
                SELECT id, total_extractions, correct_extractions
                FROM strategy_performance
                WHERE template_id = ? AND field_name = ? AND strategy_type = ?
            """, (template_id, field_name, strategy_type))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing record
                record_id = row['id']
                total = row['total_extractions'] + 1
                correct = row['correct_extractions'] + (1 if was_correct else 0)
                accuracy = correct / total if total > 0 else 0.0
                
                cursor.execute("""
                    UPDATE strategy_performance
                    SET total_extractions = ?,
                        correct_extractions = ?,
                        accuracy = ?,
                        last_updated = ?,
                        updated_by = ?
                    WHERE id = ?
                """, (total, correct, accuracy, datetime.now().isoformat(), user_id, record_id))
            else:
                # Insert new record
                total = 1
                correct = 1 if was_correct else 0
                accuracy = correct / total
                
                cursor.execute("""
                    INSERT INTO strategy_performance (
                        template_id, field_name, strategy_type,
                        total_extractions, correct_extractions, accuracy,
                        last_updated,
                        created_by, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id, field_name, strategy_type,
                    total, correct, accuracy,
                    datetime.now().isoformat(),
                    user_id, user_id
                ))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_field_performance(
        self,
        template_id: int,
        field_name: str
    ) -> List[Dict]:
        """
        Get performance for all strategies for a specific field
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            List of performance records
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT strategy_type, accuracy, total_extractions, correct_extractions
                FROM strategy_performance
                WHERE template_id = ? AND field_name = ?
                ORDER BY accuracy DESC
            """, (template_id, field_name))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'strategy_type': row['strategy_type'],
                    'accuracy': row['accuracy'],
                    'total_extractions': row['total_extractions'],
                    'correct_extractions': row['correct_extractions']
                })
            
            return results
        finally:
            conn.close()
    
    def get_template_performance(
        self,
        template_id: int
    ) -> List[Dict]:
        """
        Get performance for all fields and strategies for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            List of performance records
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT field_name, strategy_type, accuracy, 
                       total_extractions, correct_extractions, last_updated
                FROM strategy_performance
                WHERE template_id = ?
                ORDER BY field_name, accuracy DESC
            """, (template_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'field_name': row['field_name'],
                    'strategy_type': row['strategy_type'],
                    'accuracy': row['accuracy'],
                    'total_extractions': row['total_extractions'],
                    'correct_extractions': row['correct_extractions'],
                    'last_updated': row['last_updated']
                })
            
            return results
        finally:
            conn.close()
