"""
Data Quality Metrics Repository

Handles database operations for data quality validation results.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class DataQualityRepository:
    """Repository for data quality metrics"""
    
    def __init__(self, db_manager):
        """
        Initialize repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager

    def _current_user_id(self):
        try:
            from flask import g

            return getattr(g, 'user_id', None)
        except Exception:
            return None
    
    def save_metrics(
        self,
        template_id: int,
        validation_type: str,
        total_samples: int,
        diversity_metrics: Dict[str, Any],
        leakage_results: Dict[str, Any],
        recommendations: List[str],
        validation_duration: float,
        train_samples: Optional[int] = None,
        test_samples: Optional[int] = None,
        triggered_by: str = 'training',
        notes: Optional[str] = None
    ) -> int:
        """
        Save data quality metrics to database
        
        Args:
            template_id: Template ID
            validation_type: Type of validation ('training', 'on_demand', 'scheduled')
            total_samples: Total number of samples
            diversity_metrics: Diversity validation results
            leakage_results: Leakage detection results
            recommendations: List of recommendations
            validation_duration: Time taken for validation (seconds)
            train_samples: Number of training samples
            test_samples: Number of test samples
            triggered_by: What triggered this validation
            notes: Optional notes
            
        Returns:
            ID of created record
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        
        cursor.execute('''
            INSERT INTO data_quality_metrics (
                template_id, validation_type, total_samples,
                train_samples, test_samples,
                diversity_score, unique_sequences,
                structure_diversity, content_diversity,
                leakage_detected, leakage_similarity_max,
                leakage_samples_checked, leakage_samples_flagged,
                label_distribution, recommendations,
                validation_duration_seconds, status,
                triggered_by, notes,
                created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            validation_type,
            total_samples,
            train_samples,
            test_samples,
            diversity_metrics.get('diversity_score'),
            diversity_metrics.get('unique_sequences'),
            diversity_metrics.get('structure_diversity'),
            diversity_metrics.get('content_diversity'),
            leakage_results.get('leakage_detected', False),
            leakage_results.get('max_similarity'),
            leakage_results.get('samples_checked'),
            len(leakage_results.get('leakage_detected_samples', [])),
            json.dumps(diversity_metrics.get('label_distribution', {})),
            json.dumps(recommendations),
            validation_duration,
            'completed',
            triggered_by,
            notes
            ,user_id,
            user_id
        ))
        
        metric_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return metric_id
    
    def get_latest_by_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get latest data quality metrics for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            Latest metrics or None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM data_quality_metrics
            WHERE template_id = ?
            ORDER BY validation_date DESC
            LIMIT 1
        ''', (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    def get_all_by_template(
        self,
        template_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all data quality metrics for a template
        
        Args:
            template_id: Template ID
            limit: Maximum number of records to return
            
        Returns:
            List of metrics
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM data_quality_metrics
            WHERE template_id = ?
            ORDER BY validation_date DESC
            LIMIT ?
        ''', (template_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_by_id(self, metric_id: int) -> Optional[Dict[str, Any]]:
        """
        Get data quality metrics by ID
        
        Args:
            metric_id: Metric ID
            
        Returns:
            Metrics or None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM data_quality_metrics
            WHERE id = ?
        ''', (metric_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    def get_all_templates_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of latest metrics for all templates
        
        Returns:
            List of template summaries
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM latest_data_quality_metrics
            ORDER BY validation_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        return {
            'id': row['id'],
            'template_id': row['template_id'],
            'template_name': row.get('template_name'),  # From view
            'validation_type': row['validation_type'],
            'validation_date': row['validation_date'],
            'total_samples': row['total_samples'],
            'train_samples': row['train_samples'],
            'test_samples': row['test_samples'],
            'diversity_score': row['diversity_score'],
            'unique_sequences': row['unique_sequences'],
            'structure_diversity': row['structure_diversity'],
            'content_diversity': row['content_diversity'],
            'leakage_detected': bool(row['leakage_detected']),
            'leakage_similarity_max': row['leakage_similarity_max'],
            'leakage_samples_checked': row['leakage_samples_checked'],
            'leakage_samples_flagged': row['leakage_samples_flagged'],
            'label_distribution': json.loads(row['label_distribution']) if row['label_distribution'] else {},
            'recommendations': json.loads(row['recommendations']) if row['recommendations'] else [],
            'validation_duration_seconds': row['validation_duration_seconds'],
            'status': row['status'],
            'error_message': row['error_message'],
            'triggered_by': row['triggered_by'],
            'notes': row['notes']
        }
