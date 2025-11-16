from typing import Optional, Dict, Any, List
import json

from database.db_manager import DatabaseManager


class JobRepository:
    """Simple job queue repository for background tasks (e.g. auto_training)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def enqueue_auto_training_job(self, template_id: int, model_folder: str) -> int:
        """Create a new auto_training job if none is active for this template."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        payload = json.dumps({
            "template_id": template_id,
            "model_folder": model_folder,
        })

        cursor.execute(
            """
            INSERT INTO jobs (type, template_id, payload, status)
            VALUES (?, ?, ?, 'pending')
            """,
            ("auto_training", template_id, payload),
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def has_active_auto_training_job(self, template_id: int) -> bool:
        """Check if there is a pending or running auto_training job for this template."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM jobs
            WHERE type = 'auto_training'
              AND template_id = ?
              AND status IN ('pending', 'running')
            """,
            (template_id,),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def fetch_next_pending_auto_training(self) -> Optional[Dict[str, Any]]:
        """Fetch next pending auto_training job (for worker)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, type, template_id, payload, status, attempts
            FROM jobs
            WHERE type = 'auto_training' AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            """,
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    def mark_running(self, job_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'running', attempts = attempts + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        conn.commit()
        conn.close()

    def mark_completed(self, job_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        conn.commit()
        conn.close()

    def mark_failed(self, job_id: int, error: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Copy to failed_jobs
        cursor.execute(
            """
            INSERT INTO failed_jobs (job_id, type, template_id, payload, error)
            SELECT id, type, template_id, payload, ?
            FROM jobs WHERE id = ?
            """,
            (error, job_id),
        )

        # Update job status
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (error, job_id),
        )

        conn.commit()
        conn.close()
