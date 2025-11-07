"""
Performance Metrics Service
Tracks and analyzes system performance over time
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


class PerformanceMetrics:
    """Service for tracking and analyzing performance metrics"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_template_metrics(self, template_id: int) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a template
        
        Returns:
            Dictionary with metrics including:
            - Overall accuracy
            - Field-level performance
            - Strategy distribution
            - Improvement over time
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all documents for this template
        cursor.execute('''
            SELECT 
                id,
                extraction_result,
                status,
                created_at
            FROM documents
            WHERE template_id = ?
            ORDER BY created_at ASC
        ''', (template_id,))
        
        documents = cursor.fetchall()
        
        # Get all feedback for this template
        cursor.execute('''
            SELECT 
                f.document_id,
                f.field_name,
                f.original_value,
                f.corrected_value,
                f.confidence_score,
                f.created_at
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            ORDER BY f.created_at ASC
        ''', (template_id,))
        
        feedbacks = cursor.fetchall()
        conn.close()
        
        # Calculate metrics
        metrics = {
            'overview': self._calculate_overview(documents, feedbacks),
            'field_performance': self._calculate_field_performance(feedbacks),
            'strategy_distribution': self._calculate_strategy_distribution(documents),
            'accuracy_over_time': self._calculate_accuracy_over_time(documents, feedbacks),
            'feedback_stats': self._calculate_feedback_stats(feedbacks),
        }
        
        return metrics
    
    def _calculate_overview(self, documents: List, feedbacks: List) -> Dict[str, Any]:
        """Calculate overall metrics"""
        total_docs = len(documents)
        validated_docs = sum(1 for d in documents if d['status'] == 'validated')
        total_corrections = len(feedbacks)
        
        # Calculate overall accuracy
        if total_docs > 0 and feedbacks:
            # Group feedback by document
            feedback_by_doc = defaultdict(list)
            for fb in feedbacks:
                feedback_by_doc[fb['document_id']].append(fb)
            
            # Calculate accuracy per document
            accuracies = []
            for doc in documents:
                doc_feedbacks = feedback_by_doc.get(doc['id'], [])
                if doc_feedbacks:
                    # Parse extraction result
                    try:
                        result = json.loads(doc['extraction_result'])
                        total_fields = len(result.get('extracted_data', {}))
                        incorrect_fields = len(doc_feedbacks)
                        correct_fields = max(0, total_fields - incorrect_fields)
                        
                        if total_fields > 0:
                            accuracy = correct_fields / total_fields
                            accuracies.append(accuracy)
                    except:
                        pass
            
            overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        else:
            overall_accuracy = 0.0
        
        return {
            'total_documents': total_docs,
            'validated_documents': validated_docs,
            'total_corrections': total_corrections,
            'overall_accuracy': round(overall_accuracy, 3),
            'validation_rate': round(validated_docs / total_docs, 3) if total_docs > 0 else 0.0
        }
    
    def _calculate_field_performance(self, feedbacks: List) -> Dict[str, Any]:
        """Calculate per-field performance metrics"""
        field_stats = defaultdict(lambda: {
            'total_extractions': 0,
            'corrections': 0,
            'avg_confidence': []
        })
        
        for fb in feedbacks:
            field_name = fb['field_name']
            field_stats[field_name]['total_extractions'] += 1
            
            # Count as correction if values differ
            if fb['original_value'] != fb['corrected_value']:
                field_stats[field_name]['corrections'] += 1
            
            # Track confidence
            if fb['confidence_score'] is not None:
                field_stats[field_name]['avg_confidence'].append(fb['confidence_score'])
        
        # Calculate accuracy per field
        result = {}
        for field_name, stats in field_stats.items():
            total = stats['total_extractions']
            correct = total - stats['corrections']
            accuracy = correct / total if total > 0 else 0.0
            
            avg_conf = (
                sum(stats['avg_confidence']) / len(stats['avg_confidence'])
                if stats['avg_confidence'] else 0.0
            )
            
            result[field_name] = {
                'accuracy': round(accuracy, 3),
                'total_extractions': total,
                'corrections': stats['corrections'],
                'avg_confidence': round(avg_conf, 3)
            }
        
        return result
    
    def _calculate_strategy_distribution(self, documents: List) -> Dict[str, int]:
        """Calculate distribution of extraction strategies"""
        strategy_counts = defaultdict(int)
        
        for doc in documents:
            try:
                result = json.loads(doc['extraction_result'])
                methods = result.get('extraction_methods', {})
                
                for field_name, method in methods.items():
                    strategy_counts[method] += 1
            except:
                pass
        
        return dict(strategy_counts)
    
    def _calculate_accuracy_over_time(
        self, 
        documents: List, 
        feedbacks: List
    ) -> List[Dict[str, Any]]:
        """Calculate accuracy improvement over time"""
        if not documents:
            return []
        
        # Group feedback by document
        feedback_by_doc = defaultdict(list)
        for fb in feedbacks:
            feedback_by_doc[fb['document_id']].append(fb)
        
        # Calculate accuracy for each document
        timeline = []
        for doc in documents:
            doc_feedbacks = feedback_by_doc.get(doc['id'], [])
            
            try:
                result = json.loads(doc['extraction_result'])
                total_fields = len(result.get('extracted_data', {}))
                incorrect_fields = len(doc_feedbacks)
                correct_fields = max(0, total_fields - incorrect_fields)
                
                if total_fields > 0:
                    accuracy = correct_fields / total_fields
                    
                    timeline.append({
                        'timestamp': doc['created_at'],
                        'accuracy': round(accuracy, 3),
                        'document_id': doc['id'],
                        'total_fields': total_fields,
                        'correct_fields': correct_fields
                    })
            except:
                pass
        
        return timeline
    
    def _calculate_feedback_stats(self, feedbacks: List) -> Dict[str, Any]:
        """Calculate feedback statistics"""
        if not feedbacks:
            return {
                'total_feedback': 0,
                'feedback_by_field': {},
                'recent_feedback': []
            }
        
        # Group by field
        by_field = defaultdict(int)
        for fb in feedbacks:
            by_field[fb['field_name']] += 1
        
        # Get recent feedback (last 10)
        recent = []
        for fb in sorted(feedbacks, key=lambda x: x['created_at'], reverse=True)[:10]:
            recent.append({
                'field_name': fb['field_name'],
                'original_value': fb['original_value'],
                'corrected_value': fb['corrected_value'],
                'timestamp': fb['created_at']
            })
        
        return {
            'total_feedback': len(feedbacks),
            'feedback_by_field': dict(by_field),
            'recent_feedback': recent
        }
    
    def should_request_validation(
        self, 
        extraction_result: Dict[str, Any],
        threshold: float = 0.7
    ) -> tuple[bool, str]:
        """
        Active Learning: Determine if document needs validation
        
        Args:
            extraction_result: Extraction result dictionary
            threshold: Confidence threshold for auto-accept
            
        Returns:
            (should_validate, reason)
        """
        confidence_scores = extraction_result.get('confidence_scores', {})
        
        if not confidence_scores:
            return True, "No confidence scores available"
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        
        # Check for low confidence
        if avg_confidence < threshold:
            return True, f"Low average confidence ({avg_confidence:.2f} < {threshold})"
        
        # Check for any very low confidence fields
        min_confidence = min(confidence_scores.values())
        if min_confidence < 0.5:
            low_fields = [
                field for field, conf in confidence_scores.items() 
                if conf < 0.5
            ]
            return True, f"Very low confidence in fields: {', '.join(low_fields)}"
        
        # Check for strategy diversity (if all same strategy, might be template issue)
        methods = extraction_result.get('extraction_methods', {})
        unique_methods = set(methods.values())
        
        if len(unique_methods) == 1 and 'rule-based' in unique_methods:
            return True, "All fields extracted by rule-based (template may need review)"
        
        # High confidence - can auto-accept
        return False, f"High confidence ({avg_confidence:.2f})"
