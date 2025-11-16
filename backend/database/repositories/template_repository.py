from database.db_manager import DatabaseManager
from core.templates.models import Template
from typing import Optional, List
from datetime import datetime


class TemplateRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self, name: str, filename: str, config_path: str, field_count: int
    ) -> int:
        """Create a new template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO templates (name, filename, config_path, field_count)
            VALUES (?, ?, ?, ?)
        """,
            (name, filename, config_path, field_count),
        )

        template_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return template_id

    def find_by_name(self, template_name: str) -> Optional[Template]:
        """Find template by name"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, filename, config_path, field_count, created_at, updated_at, status
            FROM templates
            WHERE name = ?
        """,
            (template_name,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Template(
            id=row["id"],
            name=row["name"],
            filename=row["filename"],
            config_path=row["config_path"],
            field_count=row["field_count"],
            status=row["status"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def find_by_id(self, template_id: int) -> Optional[Template]:
        """Find template by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, filename, config_path, field_count, created_at, updated_at, status
            FROM templates
            WHERE id = ?
        """,
            (template_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Template(
            id=row["id"],
            name=row["name"],
            filename=row["filename"],
            config_path=row["config_path"],
            field_count=row["field_count"],
            status=row["status"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def find_all(self) -> List[Template]:
        """Find all templates"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, filename, config_path, field_count, created_at, updated_at, status
            FROM templates
            ORDER BY created_at DESC
        """
        )

        rows = cursor.fetchall()
        conn.close()

        templates = []
        for row in rows:
            templates.append(
                Template(
                    id=row["id"],
                    name=row["name"],
                    filename=row["filename"],
                    config_path=row["config_path"],
                    field_count=row["field_count"],
                    status=row["status"],
                    created_at=(
                        datetime.fromisoformat(row["created_at"])
                        if row["created_at"]
                        else None
                    ),
                    updated_at=(
                        datetime.fromisoformat(row["updated_at"])
                        if row["updated_at"]
                        else None
                    ),
                )
            )

        return templates

    def update(self, template_id: int, **kwargs):
        """Update template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        if fields:
            values.append(template_id)
            query = f"UPDATE templates SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

        conn.close()

    def delete(self, template_id: int):
        """Delete template"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # --- PHASE 1: Collect IDs ---
            # Get template_configs ids
            cursor.execute(
                "SELECT id FROM template_configs WHERE template_id = ?", (template_id,)
            )
            template_configs = cursor.fetchall()
            # Extract IDs into a list
            template_config_ids = [config["id"] for config in template_configs]

            # If no template configs exist, just delete the template itself and return
            if not template_config_ids:
                cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
                conn.commit()
                return True

            # Get ALL field_configs ids for all related template configs
            # Using the correct WHERE IN syntax
            field_config_placeholders = ", ".join(["?"] * len(template_config_ids))
            cursor.execute(
                f"SELECT id FROM field_configs WHERE config_id IN ({field_config_placeholders})",
                tuple(template_config_ids),
            )
            field_configs = cursor.fetchall()
            field_configs_ids = [field_config["id"] for field_config in field_configs]

            # Get ALL field_locations ids for all related field configs
            field_location_ids = []
            if field_configs_ids:
                field_config_placeholders_loc = ", ".join(
                    ["?"] * len(field_configs_ids)
                )
                cursor.execute(
                    f"SELECT id FROM field_locations WHERE field_config_id IN ({field_config_placeholders_loc})",
                    tuple(field_configs_ids),
                )
                field_locations = cursor.fetchall()
                field_location_ids = [loc["id"] for loc in field_locations]

            # --- PHASE 2: Perform Deletions (Batching outside loops) ---

            if field_location_ids:
                field_location_placeholders = ", ".join(["?"] * len(field_location_ids))
                # FIX: Use dynamic placeholders instead of "%s" directly
                cursor.execute(
                    f"DELETE FROM field_contexts WHERE field_location_id IN ({field_location_placeholders})",
                    tuple(field_location_ids),
                )

            if field_configs_ids:
                field_config_placeholders_del = ", ".join(
                    ["?"] * len(field_configs_ids)
                )
                # FIX: Use dynamic placeholders instead of "%s" directly
                cursor.execute(
                    f"DELETE FROM learned_patterns WHERE field_config_id IN ({field_config_placeholders_del})",
                    tuple(field_configs_ids),
                )
                # FIX: Use dynamic placeholders instead of "%s" directly
                cursor.execute(
                    f"DELETE FROM field_locations WHERE field_config_id IN ({field_config_placeholders_del})",
                    tuple(field_configs_ids),
                )

            # Delete remaining records tied to template_config_ids (which are guaranteed to exist here)
            config_id_placeholders = ", ".join(["?"] * len(template_config_ids))
            cursor.execute(
                f"DELETE FROM config_change_history WHERE config_id IN ({config_id_placeholders})",
                tuple(template_config_ids),
            )
            cursor.execute(
                f"DELETE FROM field_configs WHERE config_id IN ({config_id_placeholders})",
                tuple(template_config_ids),
            )
            cursor.execute(
                f"DELETE FROM template_configs WHERE template_id = ?",
                (template_id,),
            )

            # Delete records tied directly to template_id
            cursor.execute(
                "DELETE FROM pattern_learning_jobs WHERE template_id = ?",
                (template_id,),
            )

            cursor.execute(
                "DELETE FROM strategy_performance WHERE template_id = ?", (template_id,)
            )
            cursor.execute(
                "DELETE FROM training_history WHERE template_id = ?", (template_id,)
            )
            cursor.execute(
                "DELETE FROM data_quality_metrics WHERE template_id = ?", (template_id,)
            )

            # Get all documents ids
            cursor.execute(
                "SELECT id FROM documents WHERE template_id = ?", (template_id,)
            )
            documents = cursor.fetchall()
            # Extract IDs into a list
            document_ids = [doc["id"] for doc in documents]
            document_ids_placeholders = ", ".join(["?"] * len(document_ids))

            cursor.execute(
                f"DELETE FROM feedback WHERE document_id IN ({document_ids_placeholders})",
                tuple(document_ids),
            )

            cursor.execute(
                "DELETE FROM documents WHERE template_id = ?", (template_id,)
            )

            cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            # In a real application, you might want to log the exception before raising
            raise e
        finally:
            cursor.close()
            conn.close()
