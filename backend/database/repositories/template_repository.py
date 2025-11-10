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

        cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))

        conn.commit()
        conn.close()
