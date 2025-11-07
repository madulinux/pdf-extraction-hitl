"""
Extraction Repository
Data access layer for documents and feedback
"""
from typing import Optional, List, Dict
from datetime import datetime
import sqlite3
import json

from .models import Document, Feedback


class DocumentRepository:
    """Repository for document data access"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create(self, template_id: int, filename: str, file_path: str) -> int:
        """Create a new document"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (template_id, filename, file_path, status)
            VALUES (?, ?, ?, 'pending')
        ''', (template_id, filename, file_path))
        
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return document_id
    
    def find_by_id(self, document_id: int) -> Optional[Document]:
        """Find document by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, template_id, filename, file_path, extraction_result, status, created_at, updated_at
            FROM documents
            WHERE id = ?
        ''', (document_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Document(
            id=row['id'],
            template_id=row['template_id'],
            filename=row['filename'],
            file_path=row['file_path'],
            extraction_result=row['extraction_result'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def find_all(self) -> List[Document]:
        """Find all documents"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, template_id, filename, file_path, extraction_result, status, created_at, updated_at
            FROM documents
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            documents.append(Document(
                id=row['id'],
                template_id=row['template_id'],
                filename=row['filename'],
                file_path=row['file_path'],
                extraction_result=row['extraction_result'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        
        return documents
    
    def update_extraction(self, document_id: int, extraction_result: str, status: str):
        """Update document extraction result"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents
            SET extraction_result = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (extraction_result, status, document_id))
        
        conn.commit()
        conn.close()
    
    def update_status(self, document_id: int, status: str):
        """Update document status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, document_id))
        
        conn.commit()
        conn.close()
    
    def update_extraction_result(self, document_id: int, extraction_result: dict):
        """
        Update extraction_result with corrected values
        Used after user validation/correction
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents
            SET extraction_result = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(extraction_result), document_id))
        
        conn.commit()
        conn.close()


class FeedbackRepository:
    """Repository for feedback data access"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def upsert(
        self,
        document_id: int,
        corrections: Dict,
        original_data: Dict,
        confidence_scores: Dict,
        feedback_path: str
    ) -> List[int]:
        """
        Upsert feedback records (one per field)
        Updates existing feedback or creates new
        
        Args:
            document_id: Document ID
            corrections: Dictionary of {field_name: corrected_value}
            original_data: Dictionary of {field_name: original_value}
            confidence_scores: Dictionary of {field_name: confidence}
            feedback_path: Path to feedback JSON file
            
        Returns:
            List of feedback IDs
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        feedback_ids = []
        
        for field_name, corrected_value in corrections.items():
            original_value = original_data.get(field_name, '')
            confidence = confidence_scores.get(field_name, 0.0)
            
            # Check if feedback already exists for this document+field
            cursor.execute('''
                SELECT id FROM feedback
                WHERE document_id = ? AND field_name = ?
            ''', (document_id, field_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # UPDATE existing feedback
                cursor.execute('''
                    UPDATE feedback
                    SET original_value = ?,
                        corrected_value = ?,
                        confidence_score = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        used_for_training = 0
                    WHERE id = ?
                ''', (original_value, corrected_value, confidence, existing['id']))
                
                feedback_ids.append(existing['id'])
            else:
                # INSERT new feedback
                cursor.execute('''
                    INSERT INTO feedback (
                        document_id, 
                        field_name, 
                        original_value, 
                        corrected_value, 
                        confidence_score,
                        used_for_training
                    )
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (
                    document_id, 
                    field_name, 
                    original_value,
                    corrected_value,
                    confidence
                ))
                
                feedback_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        
        return feedback_ids
    
    def find_for_training(self, template_id: int, unused_only: bool = True) -> List[dict]:
        """Find feedback for training"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                f.id, 
                f.document_id, 
                f.field_name,
                f.original_value,
                f.corrected_value,
                f.confidence_score,
                f.used_for_training,
                f.created_at
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        '''
        
        if unused_only:
            query += ' AND f.used_for_training = 0'
        
        cursor.execute(query, (template_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_high_confidence_extractions(
        self, 
        template_id: int, 
        confidence_threshold: float = 0.90,
        limit: int = None
    ) -> List[dict]:
        """
        Get high-confidence extractions that can be used as training data
        These are extractions without feedback but with high confidence scores
        
        Args:
            template_id: Template ID
            confidence_threshold: Minimum confidence (default 0.90 = 90%)
            limit: Maximum number of records to return
            
        Returns:
            List of high-confidence extraction records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                d.id as document_id,
                d.extraction_result
            FROM documents d
            LEFT JOIN feedback f ON d.id = f.document_id
            WHERE d.template_id = ?
            AND d.status = 'extracted'
            AND f.id IS NULL
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, (template_id,))
        rows = cursor.fetchall()
        conn.close()
        
        # Parse extraction results and filter by confidence
        high_conf_data = []
        for row in rows:
            import json
            extraction_result = json.loads(row['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            confidence_scores = extraction_result.get('confidence_scores', {})
            
            for field_name, value in extracted_data.items():
                confidence = confidence_scores.get(field_name, 0.0)
                
                if confidence >= confidence_threshold:
                    high_conf_data.append({
                        'document_id': row['document_id'],
                        'field_name': field_name,
                        'extracted_value': value,
                        'confidence_score': confidence,
                        'source': 'high_confidence_extraction'
                    })
        
        return high_conf_data
    
    def get_training_data(
        self,
        template_id: int,
        min_samples: int = 20,
        use_high_confidence: bool = True,
        confidence_threshold: float = 0.90
    ) -> dict:
        """
        Get training data using hybrid approach:
        1. Prioritize feedback data (ground truth)
        2. Supplement with high-confidence extractions if needed
        
        Args:
            template_id: Template ID
            min_samples: Minimum samples needed per field
            use_high_confidence: Whether to use high-confidence extractions
            confidence_threshold: Threshold for high-confidence (default 0.90)
            
        Returns:
            Dictionary with training data and metadata
        """
        # 1. Get feedback data (PRIORITY)
        feedback_data = self.find_for_training(template_id, unused_only=False)
        
        training_data = {
            'feedback': feedback_data,
            'high_confidence': [],
            'metadata': {
                'feedback_count': len(feedback_data),
                'high_confidence_count': 0,
                'total_count': len(feedback_data),
                'strategy': 'feedback_only'
            }
        }
        
        # 2. Check if we need more data
        if use_high_confidence and len(feedback_data) < min_samples:
            needed = min_samples - len(feedback_data)
            
            high_conf_data = self.get_high_confidence_extractions(
                template_id=template_id,
                confidence_threshold=confidence_threshold,
                limit=needed * 2  # Get more to filter
            )
            
            training_data['high_confidence'] = high_conf_data
            training_data['metadata']['high_confidence_count'] = len(high_conf_data)
            training_data['metadata']['total_count'] = len(feedback_data) + len(high_conf_data)
            training_data['metadata']['strategy'] = 'hybrid'
        
        return training_data
    
    def find_by_document_id(self, document_id: int) -> List[dict]:
        """
        Get all feedback for a specific document
        Used to show correction history in UI
        
        Args:
            document_id: Document ID
            
        Returns:
            List of feedback records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                document_id,
                field_name,
                original_value,
                corrected_value,
                confidence_score,
                used_for_training,
                created_at,
                updated_at
            FROM feedback
            WHERE document_id = ?
            ORDER BY created_at DESC
        ''', (document_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def mark_as_used(self, feedback_ids: List[int]):
        """Mark feedback as used for training"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(feedback_ids))
        cursor.execute(f'''
            UPDATE feedback
            SET used_for_training = 1
            WHERE id IN ({placeholders})
        ''', feedback_ids)
        
        conn.commit()
        conn.close()
