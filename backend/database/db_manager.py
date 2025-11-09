"""
Database Manager for SQLite operations
Handles metadata storage for templates, documents, and feedback
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = 'data/app.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Create and return a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema and run migrations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Run migrations
        self._run_migrations(conn, cursor)
        
        # Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                config_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                field_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                extraction_result TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates (id)
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                original_value TEXT,
                corrected_value TEXT NOT NULL,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_for_training BOOLEAN DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        # Model training history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                model_path TEXT NOT NULL,
                training_samples INTEGER,
                accuracy REAL,
                precision_score REAL,
                recall_score REAL,
                f1_score REAL,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates (id)
            )
        ''')
        
        # Strategy performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                strategy_type TEXT NOT NULL,
                field_name TEXT,
                accuracy REAL DEFAULT 0.0,
                total_extractions INTEGER DEFAULT 0,
                correct_extractions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(id),
                UNIQUE(template_id, strategy_type, field_name)
            )
        ''')
        
        # Strategy performance indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_strategy_performance_template ON strategy_performance(template_id)
        ''')
        
        # Strategy performance indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_strategy_performance_strategy ON strategy_performance(strategy_type)
        ''')

        conn.commit()
        conn.close()
    
    # Template operations
    def create_template(self, name: str, filename: str, config_path: str, field_count: int = 0) -> int:
        """Create a new template record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO templates (name, filename, config_path, field_count)
            VALUES (?, ?, ?, ?)
        ''', (name, filename, config_path, field_count))
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return template_id
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get template by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_templates(self) -> List[Dict]:
        """Get all templates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Document operations
    def create_document(self, template_id: int, filename: str, file_path: str) -> int:
        """Create a new document record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (template_id, filename, file_path)
            VALUES (?, ?, ?)
        ''', (template_id, filename, file_path))
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return document_id
    
    def update_document_extraction(self, document_id: int, extraction_result: str, status: str = 'extracted'):
        """Update document with extraction results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE documents 
            SET extraction_result = ?, status = ?
            WHERE id = ?
        ''', (extraction_result, status, document_id))
        conn.commit()
        conn.close()
    
    def get_document(self, document_id: int) -> Optional[Dict]:
        """Get document by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # Feedback operations
    def create_feedback(self, document_id: int, field_name: str, 
                       original_value: str, corrected_value: str, 
                       confidence_score: float = None) -> int:
        """Create feedback record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (document_id, field_name, original_value, 
                                corrected_value, confidence_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (document_id, field_name, original_value, corrected_value, confidence_score))
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return feedback_id
    
    def get_feedback_for_training(self, template_id: int, unused_only: bool = True) -> List[Dict]:
        """Get feedback data for model training"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT f.* FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        '''
        if unused_only:
            query += ' AND f.used_for_training = 0'
        
        cursor.execute(query, (template_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_feedback(self, template_id: int) -> List[Dict]:
        """Get all feedback for a template (for evaluation)"""
        return self.get_feedback_for_training(template_id, unused_only=False)
    
    def get_feedback_by_document(self, document_id: int) -> List[Dict]:
        """Get all feedback for a specific document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback WHERE document_id = ?', (document_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_validated_documents(self, template_id: int) -> List[Dict]:
        """
        Get validated documents with high-confidence extractions
        These are documents that were validated, including those with minor corrections
        
        Strategy:
        - Include documents with status='validated' 
        - Include documents with few corrections (< 30% of fields)
        - This provides more positive training examples
        
        Args:
            template_id: Template ID
            
        Returns:
            List of validated documents with extraction results
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ✅ FIX: Include validated documents even if they have some feedback
        # This provides more training data for fields that were correct
        query = '''
            SELECT d.* FROM documents d
            WHERE d.template_id = ?
            AND d.status = 'validated'
            AND d.extraction_result IS NOT NULL
        '''
        
        cursor.execute(query, (template_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_feedback_used(self, feedback_ids: List[int]):
        """Mark feedback as used for training"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(feedback_ids))
        cursor.execute(f'''
            UPDATE feedback 
            SET used_for_training = 1
            WHERE id IN ({placeholders})
        ''', feedback_ids)
        conn.commit()
        conn.close()
    
    # Training history operations
    def create_training_record(self, template_id: int, model_path: str, 
                              training_samples: int, metrics: Dict[str, float]) -> int:
        """Create training history record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO training_history 
            (template_id, model_path, training_samples, accuracy, 
             precision_score, recall_score, f1_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (template_id, model_path, training_samples, 
              metrics.get('accuracy'), metrics.get('precision'),
              metrics.get('recall'), metrics.get('f1')))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id
    
    def get_training_history(self, template_id: int) -> List[Dict]:
        """Get training history for a template"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM training_history 
            WHERE template_id = ?
            ORDER BY trained_at DESC
        ''', (template_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def _run_migrations(self, conn, cursor):
        """Run database migrations from migrations folder"""
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            return
        
        # Create migrations tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get applied migrations
        cursor.execute('SELECT filename FROM migrations')
        applied = {row[0] for row in cursor.fetchall()}
        
        # Get all migration files
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        # Apply new migrations
        for filename in migration_files:
            if filename not in applied:
                filepath = os.path.join(migrations_dir, filename)
                print(f"Applying migration: {filename}")
                with open(filepath, 'r') as f:
                    migration_sql = f.read()
                    cursor.executescript(migration_sql)
                cursor.execute('INSERT INTO migrations (filename) VALUES (?)', (filename,))
                conn.commit()
                print(f"✓ Migration {filename} applied")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        affected = cursor.rowcount
        lastrowid = cursor.lastrowid
        conn.commit()
        conn.close()
        return lastrowid if 'INSERT' in query.upper() else affected
