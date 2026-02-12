from typing import Dict, List
from database.db_manager import DatabaseManager


class FeedbackRepository:
    """Repository for feedback data access"""

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

    def upsert(
        self,
        document_id: int,
        corrections: Dict,
        original_data: Dict,
        confidence_scores: Dict,
        feedback_path: str,
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
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        feedback_ids = []

        for field_name, corrected_value in corrections.items():
            original_value = original_data.get(field_name, "")
            confidence = confidence_scores.get(field_name, 0.0)

            # Check if feedback already exists for this document+field
            cursor.execute(
                """
                SELECT id FROM feedback
                WHERE document_id = ? AND field_name = ?
            """,
                (document_id, field_name),
            )

            existing = cursor.fetchone()

            if existing:
                # UPDATE existing feedback
                cursor.execute(
                    """
                    UPDATE feedback
                    SET original_value = ?,
                        corrected_value = ?,
                        confidence_score = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = ?,
                        used_for_training = 0
                    WHERE id = ?
                """,
                    (original_value, corrected_value, confidence, user_id, existing["id"]),
                )

                feedback_ids.append(existing["id"])
            else:
                # INSERT new feedback
                cursor.execute(
                    """
                    INSERT INTO feedback (
                        document_id, 
                        field_name, 
                        original_value, 
                        corrected_value, 
                        confidence_score,
                        created_by,
                        updated_by,
                        used_for_training
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        document_id,
                        field_name,
                        original_value,
                        corrected_value,
                        confidence,
                        user_id,
                        user_id,
                    ),
                )

                feedback_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        return feedback_ids

    def find_for_training(
        self, template_id: int, unused_only: bool = True
    ) -> List[dict]:
        """Find feedback for training"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        query = """
            SELECT f.* FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        """

        query += " AND (? = 1 OR d.created_by = ?)"

        if unused_only:
            query += " AND f.used_for_training = 0"

        cursor.execute(query, (template_id, 1 if is_admin else 0, user_id))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_high_confidence_extractions(
        self, template_id: int, confidence_threshold: float = 0.90, limit: int = None
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
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        query = """
            SELECT 
                d.id as document_id,
                d.extraction_result
            FROM documents d
            LEFT JOIN feedback f ON d.id = f.document_id
            WHERE d.template_id = ?
            AND d.status = 'extracted'
            AND f.id IS NULL
            AND (? = 1 OR d.created_by = ?)
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (template_id, 1 if is_admin else 0, user_id))
        rows = cursor.fetchall()
        conn.close()

        # Parse extraction results and filter by confidence
        high_conf_data = []
        for row in rows:
            import json

            extraction_result = json.loads(row["extraction_result"])
            extracted_data = extraction_result.get("extracted_data", {})
            confidence_scores = extraction_result.get("confidence_scores", {})

            for field_name, value in extracted_data.items():
                confidence = confidence_scores.get(field_name, 0.0)

                if confidence >= confidence_threshold:
                    high_conf_data.append(
                        {
                            "document_id": row["document_id"],
                            "field_name": field_name,
                            "extracted_value": value,
                            "confidence_score": confidence,
                            "source": "high_confidence_extraction",
                        }
                    )

        return high_conf_data

    def get_training_data(
        self,
        template_id: int,
        min_samples: int = 20,
        use_high_confidence: bool = True,
        confidence_threshold: float = 0.90,
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
            "feedback": feedback_data,
            "high_confidence": [],
            "metadata": {
                "feedback_count": len(feedback_data),
                "high_confidence_count": 0,
                "total_count": len(feedback_data),
                "strategy": "feedback_only",
            },
        }

        # 2. Check if we need more data
        if use_high_confidence and len(feedback_data) < min_samples:
            needed = min_samples - len(feedback_data)

            high_conf_data = self.get_high_confidence_extractions(
                template_id=template_id,
                confidence_threshold=confidence_threshold,
                limit=needed * 2,  # Get more to filter
            )

            training_data["high_confidence"] = high_conf_data
            training_data["metadata"]["high_confidence_count"] = len(high_conf_data)
            training_data["metadata"]["total_count"] = len(feedback_data) + len(
                high_conf_data
            )
            training_data["metadata"]["strategy"] = "hybrid"

        return training_data

    def find_by_template_id(self, template_id: int) -> List[dict]:
        """
        Get all feedback for a specific template
        Used to show correction history in UI

        Args:
            template_id: Template ID

        Returns:
            List of feedback records
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        cursor.execute(
            """
            SELECT 
                f.*
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
              AND (? = 1 OR d.created_by = ?)
            ORDER BY f.created_at ASC
            """,
            (template_id, 1 if is_admin else 0, user_id),
        )

        rows = cursor.fetchall()
        conn.close()

        return rows

    def find_by_document_id(self, document_id: int) -> List[dict]:
        """
        Get all feedback for a specific document
        Used to show correction history in UI

        Args:
            document_id: Document ID

        Returns:
            List of feedback records
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        cursor.execute(
            """
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
              AND (? = 1 OR document_id IN (SELECT id FROM documents WHERE id = ? AND created_by = ?))
            ORDER BY created_at DESC
        """,
            (document_id, 1 if is_admin else 0, document_id, user_id),
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def mark_as_used(self, feedback_ids: List[int]):
        """Mark feedback as used for training"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(feedback_ids))
        cursor.execute(
            f"""
            UPDATE feedback
            SET used_for_training = 1
            WHERE id IN ({placeholders})
        """,
            feedback_ids,
        )

        conn.commit()
        conn.close()

    def find_by_document_ids(self, document_ids: List[int]) -> List[dict]:
        """
        Get all feedback for a list of document IDs
        Used for filtering feedback by experiment phase
        
        Args:
            document_ids: List of document IDs
        
        Returns:
            List of feedback records
        """
        if not document_ids:
            return []
        
        conn = self.db.get_connection()
        cursor = conn.cursor()

        user_id = self._current_user_id()
        is_admin = self._is_admin()

        placeholders = ",".join("?" * len(document_ids))
        params = list(document_ids)
        query = f"""
            SELECT 
                f.*
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE f.document_id IN ({placeholders})
              AND (? = 1 OR d.created_by = ?)
            ORDER BY f.created_at ASC
            """
        params.extend([1 if is_admin else 0, user_id])
        cursor.execute(query, params)

        rows = cursor.fetchall()
        conn.close()

        return rows
