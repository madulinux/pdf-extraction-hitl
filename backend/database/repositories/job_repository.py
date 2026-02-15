from typing import Optional, Dict, Any, List
import json

from database.db_manager import DatabaseManager


class JobRepository:
    """Simple job queue repository for background tasks (e.g. auto_training)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _current_user_id(self):
        try:
            from flask import g

            return getattr(g, 'user_id', None)
        except Exception:
            return None

    def enqueue_auto_training_job(self, template_id: int, model_folder: str, is_first_training: bool = False) -> int:
        """Create a new auto_training job if none is active for this template."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        payload = json.dumps({
            "template_id": template_id,
            "model_folder": model_folder,
            "is_first_training": is_first_training,
        })

        cursor.execute(
            """
            INSERT INTO jobs (type, template_id, payload, status, created_by, updated_by)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            ("auto_training", template_id, payload, user_id, user_id),
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def enqueue_manual_training_job(
        self, 
        template_id: int, 
        model_folder: str,
        use_all_feedback: bool = True,
        is_incremental: bool = False
    ) -> int:
        """
        Create a new manual training job (triggered by user via API).
        
        Args:
            template_id: Template ID to train
            model_folder: Path to model folder
            use_all_feedback: Use all feedback or only unused
            is_incremental: Incremental training mode
            
        Returns:
            Job ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        payload = json.dumps({
            "template_id": template_id,
            "model_folder": model_folder,
            "use_all_feedback": use_all_feedback,
            "is_incremental": is_incremental,
            "trigger": "manual"  # Mark as manual trigger
        })

        cursor.execute(
            """
            INSERT INTO jobs (type, template_id, payload, status, created_by, updated_by)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            ("auto_training", template_id, payload, user_id, user_id),
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

    def reset_stale_running_jobs(self, max_age_minutes: int = 30) -> int:
        """Mark running jobs as failed if they have not been updated recently.

        This prevents jobs from getting stuck in 'running' forever if the worker
        crashes or restarts mid-job.

        Returns:
            Number of jobs updated.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE jobs
            SET status = 'failed',
                last_error = COALESCE(last_error, 'stale running job reset by worker'),
                updated_at = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE status = 'running'
              AND updated_at IS NOT NULL
              AND updated_at < datetime('now', ?)
            """,
            (self._current_user_id(), f'-{int(max_age_minutes)} minutes'),
        )

        updated = cursor.rowcount
        conn.commit()
        conn.close()
        return updated

    def mark_running(self, job_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        user_id = self._current_user_id()
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'running', attempts = attempts + 1, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
            """,
            (user_id, job_id),
        )
        conn.commit()
        conn.close()

    def mark_completed(self, job_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        user_id = self._current_user_id()
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
            """,
            (user_id, job_id),
        )
        conn.commit()
        conn.close()

    def mark_failed(self, job_id: int, error: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        # Copy to failed_jobs
        cursor.execute(
            """
            INSERT INTO failed_jobs (job_id, type, template_id, payload, error, created_by, updated_by)
            SELECT id, type, template_id, payload, ?, ?, ?
            FROM jobs WHERE id = ?
            """,
            (error, user_id, user_id, job_id),
        )

        # Update job status
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
            """,
            (error, user_id, job_id),
        )

        conn.commit()
        conn.close()
