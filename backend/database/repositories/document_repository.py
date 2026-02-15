from typing import Dict, List, Optional, Tuple
from datetime import datetime
from core.extraction.models import Document
import math
from database.db_manager import DatabaseManager
import json
from datetime import datetime


class DocumentRepository:
    """Repository for document data"""

    def __init__(self, db_manager: DatabaseManager):
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

    def _is_admin(self) -> bool:
        try:
            from flask import g

            user_id = getattr(g, 'user_id', None)
            if user_id is None:
                return True

            return getattr(g, 'user_role', None) == 'admin'
        except Exception:
            return True

    def create(self, template_id: int, filename: str, file_path: str, experiment_phase: str) -> int:
        """Create a new document"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        try:
            cursor.execute(
                """
                INSERT INTO documents (template_id, filename, file_path, status, experiment_phase, created_by, updated_by)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """,
                (template_id, filename, file_path, experiment_phase, user_id, user_id),
            )

            document_id = cursor.lastrowid
            conn.commit()
            return document_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def find_by_id(self, document_id: int) -> Optional[Document]:
        """Find document by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        try:
            cursor.execute(
                """
                SELECT documents.*, templates.name as template_name 
                FROM documents 
                LEFT JOIN templates ON documents.template_id = templates.id 
                WHERE documents.id = ?
                  AND (? = 1 OR documents.created_by = ?)
                """,
                (document_id, 1 if is_admin else 0, user_id),
            )

            row = cursor.fetchone()
            if row:
                return Document(
                    id=row["id"],
                    template_id=row["template_id"],
                    filename=row["filename"],
                    file_path=row["file_path"],
                    extraction_result=row["extraction_result"],
                    extraction_time_ms=row["extraction_time_ms"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    validated_at=row["validated_at"] if "validated_at" in row.keys() else None,
                    used_for_training=row["used_for_training"] if "used_for_training" in row.keys() else 0,
                    experiment_phase=row["experiment_phase"] if "experiment_phase" in row.keys() else None,
                )
            return None
        except Exception as e:
            raise e
        finally:
            conn.close()

    def find_validated_documents(self, template_id: int, unused_only: bool = False) -> List[Document]:
        """Find validated documents for a specific template
        
        Args:
            template_id: Template ID to filter by
            unused_only: If True, only return documents with used_for_training=0
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        if unused_only:
            cursor.execute(
                """
                SELECT documents.*
                FROM documents
                JOIN templates ON documents.template_id = templates.id
                WHERE documents.template_id = ?
                  AND documents.status = 'validated'
                  AND documents.used_for_training = 0
                  AND (? = 1 OR documents.created_by = ?)
                """,
                (template_id, 1 if is_admin else 0, user_id),
            )
        else:
            cursor.execute(
                """
                SELECT documents.*
                FROM documents
                JOIN templates ON documents.template_id = templates.id
                WHERE documents.template_id = ?
                  AND documents.status = 'validated'
                  AND (? = 1 OR documents.created_by = ?)
                """,
                (template_id, 1 if is_admin else 0, user_id),
            )

        rows = cursor.fetchall()
        conn.close()

        return [Document(**row) for row in rows]

    def find_by_template_id(self, template_id: int) -> List[Dict]:
        """Find documents for a specific template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        cursor.execute(
            """
            SELECT documents.*
            FROM documents
            JOIN templates ON documents.template_id = templates.id
            WHERE documents.template_id = ?
              AND (? = 1 OR documents.created_by = ?)
            ORDER BY documents.created_at ASC
            """,
            (template_id, 1 if is_admin else 0, user_id),
        )

        rows = cursor.fetchall()
        conn.close()

        return rows

    def find_by_template_and_phase(self, template_id: int, experiment_phase: str = None) -> List[Dict]:
        """
        Find documents for a specific template and optional experiment phase
        
        Args:
            template_id: Template ID
            experiment_phase: Experiment phase filter
                - None: Production documents only (experiment_phase IS NULL)
                - 'baseline': Baseline experiment documents
                - 'adaptive': Adaptive learning documents
                - 'all': All documents regardless of phase
        
        Returns:
            List of document dictionaries
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        if experiment_phase == 'all':
            # Get all documents regardless of phase
            cursor.execute(
                """
                SELECT documents.*
                FROM documents
                WHERE documents.template_id = ?
                  AND (? = 1 OR documents.created_by = ?)
                ORDER BY documents.created_at ASC
                """,
                (template_id, 1 if is_admin else 0, user_id),
            )
        elif experiment_phase:
            # Get specific phase
            cursor.execute(
                """
                SELECT documents.*
                FROM documents
                WHERE documents.template_id = ? AND documents.experiment_phase = ?
                  AND (? = 1 OR documents.created_by = ?)
                ORDER BY documents.created_at ASC
                """,
                (template_id, experiment_phase, 1 if is_admin else 0, user_id),
            )
        else:
            # Default: production only (NULL)
            cursor.execute(
                """
                SELECT documents.*
                FROM documents
                WHERE documents.template_id = ? AND documents.experiment_phase IS NULL
                  AND (? = 1 OR documents.created_by = ?)
                ORDER BY documents.created_at ASC
                """,
                (template_id, 1 if is_admin else 0, user_id),
            )

        rows = cursor.fetchall()
        conn.close()

        return rows

    def find_all(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str = None,
        filters: List[dict] = [],
    ) -> Tuple[List[Document], int]:
        available_filter = ["template_id", "filename", "file_path", "status", "created_by"]

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        if not is_admin and user_id is not None:
            filters = list(filters) if filters else []
            filters.append({"field": "documents.created_by", "operator": "=", "value": user_id})

        try:
            total_items_count = self.db.get_total_items_count_filtered(
                table_name="documents",
                search=search,
                available_filter=available_filter,
                filters=filters,
            )

            total_pages = math.ceil(total_items_count / page_size)

            data = self.db.get_page_of_data_filtered(
                join="JOIN templates ON documents.template_id = templates.id",
                select="documents.*, templates.name as template_name",
                table_name="documents",
                search=search,
                available_filter=available_filter,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by="created_at",
                sort_order="DESC",
            )
            return data, total_pages
        except Exception as e:
            raise e

    def count_filtered(self, search: str = None, filters: List[dict] = []) -> int:
        available_filter = ["template_id", "filename", "file_path", "status", "created_by"]

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        if not is_admin and user_id is not None:
            filters = list(filters) if filters else []
            filters.append({"field": "documents.created_by", "operator": "=", "value": user_id})

        return self.db.get_total_items_count_filtered(
            table_name="documents",
            search=search,
            available_filter=available_filter,
            filters=filters,
        )

    def update_extraction(
        self,
        document_id: int,
        extraction_result: str,
        status: str,
        extraction_time_ms: int = 0,
    ):
        """Update document extraction result"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        cursor.execute(
            """
            UPDATE documents
            SET extraction_result = ?, status = ?, extraction_time_ms = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
        """,
            (extraction_result, status, extraction_time_ms, user_id, document_id),
        )

        conn.commit()
        conn.close()

    def update_status(self, document_id: int, status: str):
        """Update document status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        validated_at = datetime.now() if status == "validated" else None
        user_id = self._current_user_id()
        try:
            cursor.execute(
                """
                UPDATE documents
                SET status = ?, validated_at = ?, updated_by = ?
                WHERE id = ?
                """,
                (status, validated_at, user_id, document_id),
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_extraction_result(self, document_id: int, extraction_result: dict):
        """Update extraction_result with corrected values"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()

        try:
            cursor.execute(
                """
                UPDATE documents
                SET extraction_result = ?, updated_by = ?
                WHERE id = ?
                """,
                (json.dumps(extraction_result), user_id, document_id),
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
