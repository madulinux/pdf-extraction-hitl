from database.db_manager import DatabaseManager
from core.templates.models import Template
from typing import Optional, List, Dict
from datetime import datetime


class TrainingRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _current_user_id(self):
        try:
            from flask import g

            return getattr(g, 'user_id', None)
        except Exception:
            return None

    def create(
        self,
        template_id: int,
        model_path: str,
        training_samples: int,
        metrics: Dict[str, float],
    ):
        """Create training history record"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        cursor.execute(
            """
            INSERT INTO training_history 
            (template_id, model_path, training_samples, accuracy, 
             precision_score, recall_score, f1_score, created_by, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                template_id,
                model_path,
                training_samples,
                metrics.get("accuracy"),
                metrics.get("precision"),
                metrics.get("recall"),
                metrics.get("f1"),
                user_id,
                user_id,
            ),
        )
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    def find_training_history(self, template_id: int) -> Optional[List[Dict]]:
        """Get training history for a template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM training_history 
            WHERE template_id = ?
            ORDER BY trained_at DESC
            """,
            (template_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
