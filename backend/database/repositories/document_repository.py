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

    def create(self, template_id: int, filename: str, file_path: str) -> int:
        """Create a new document"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO documents (template_id, filename, file_path, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (template_id, filename, file_path),
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

        try:
            cursor.execute(
                """
                SELECT documents.*, templates.name as template_name 
                FROM documents 
                LEFT JOIN templates ON documents.template_id = templates.id 
                WHERE documents.id = ?
                """,
                (document_id,),
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
                )
            return None
        except Exception as e:
            raise e
        finally:
            conn.close()

    def find_validated_documents(self, template_id: int) -> List[Document]:
        """Find validated documents for a specific template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT documents.*
            FROM documents
            JOIN templates ON documents.template_id = templates.id
            WHERE documents.template_id = ?
            AND documents.status = 'validated'
            """,
            (template_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [Document(**row) for row in rows]

    def find_by_template_id(self, template_id: int) -> List[Dict]:
        """Find documents for a specific template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT documents.*
            FROM documents
            JOIN templates ON documents.template_id = templates.id
            WHERE documents.template_id = ?
            ORDER BY documents.created_at ASC
            """,
            (template_id,),
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
        available_filter = ["template_id", "filename", "file_path", "status"]
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

        cursor.execute(
            """
            UPDATE documents
            SET extraction_result = ?, status = ?, extraction_time_ms = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (extraction_result, status, extraction_time_ms, document_id),
        )

        conn.commit()
        conn.close()

    def update_status(self, document_id: int, status: str):
        """Update document status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        validated_at = datetime.now() if status == "validated" else None
        try:
            cursor.execute(
                """
                UPDATE documents
                SET status = ?, validated_at = ?
                WHERE id = ?
                """,
                (status, validated_at, document_id),
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

        try:
            cursor.execute(
                """
                UPDATE documents
                SET extraction_result = ?
                WHERE id = ?
                """,
                (json.dumps(extraction_result), document_id),
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
