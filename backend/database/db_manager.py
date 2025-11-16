"""
Database Manager for SQLite operations
Handles metadata storage for templates, documents, and feedback
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


class DatabaseManager:
    # Flag to ensure migrations only run once per process
    _migrations_applied = False

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Run migrations only once per process to avoid contention and
        # expensive DDL on every DatabaseManager() construction.
        if not DatabaseManager._migrations_applied:
            self.init_database()
            DatabaseManager._migrations_applied = True

    def get_connection(self):
        """Create and return a database connection"""
        # Configure SQLite for better concurrency:
        # - timeout: wait for a while if the database is locked
        # - check_same_thread=False: allow usage from different threads
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row

        # Use WAL mode to improve concurrent reads while a writer is active.
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            # PRAGMA failures should not break normal operation
            pass

        return conn

    def init_database(self):
        """Initialize database schema and run migrations"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Run migrations
        self._run_migrations(conn, cursor)

        conn.commit()
        conn.close()


    def _run_migrations(self, conn, cursor):
        """Run database migrations from migrations folder"""
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        if not os.path.exists(migrations_dir):
            return

        # Create migrations tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Get applied migrations
        cursor.execute("SELECT filename FROM migrations")
        applied = {row[0] for row in cursor.fetchall()}

        # Get all migration files (.sql and .py)
        migration_files = sorted(
            [f for f in os.listdir(migrations_dir) if f.endswith((".sql", ".py"))]
        )

        # Apply new migrations
        for filename in migration_files:
            if filename not in applied:
                filepath = os.path.join(migrations_dir, filename)
                print(f"Applying migration: {filename}")

                if filename.endswith(".sql"):
                    # SQL migration
                    with open(filepath, "r") as f:
                        migration_sql = f.read()
                        cursor.executescript(migration_sql)
                elif filename.endswith(".py"):
                    # Python migration
                    import importlib.util

                    spec = importlib.util.spec_from_file_location("migration", filepath)
                    migration_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_module)

                    # Run upgrade function
                    if hasattr(migration_module, "upgrade"):
                        migration_module.upgrade(conn)

                cursor.execute(
                    "INSERT INTO migrations (filename) VALUES (?)", (filename,)
                )
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
        return lastrowid if "INSERT" in query.upper() else affected

    def get_page_of_data_filtered(
        self,
        table_name: str,
        join: str = None,
        page: int = 1,
        page_size: int = 10,
        select: str = "*",
        search: str = None,
        sort_by: str = None,
        sort_order: str = "ASC",
        available_filter: List[str] = [],
        filters: List[dict] = [],
    ) -> List[Dict]:
        offset = (page - 1) * page_size
        query = f"SELECT {select} FROM {table_name}"
        parameters = []
        conn = self.get_connection()
        cursor = conn.cursor()

        if join:
            query += f" {join}"

        if filters:
            for i, f in enumerate(filters):
                if (
                    f["field"] not in available_filter
                    or f["value"] is None
                    or f["value"] == ""
                ):
                    continue
                if f["operator"] not in ["=", "!=", ">", "<", ">=", "<="]:
                    f["operator"] = "="
                if "WHERE" not in query:
                    query += " WHERE "
                else:
                    query += " AND "
                query += f"{f['field']} {f['operator']} ?"
                parameters.append(f["value"])

        if search:
            if "WHERE" not in query:
                query += " WHERE "
            else:
                query += " AND "
            query += "filename LIKE ?"
            parameters.append(f"%{search}%")

        if sort_by:
            query += f" ORDER BY {sort_by} {sort_order}"

        query += " LIMIT ? OFFSET ?"
        parameters.append(page_size)
        parameters.append(offset)
        try:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            raise e

    def get_total_items_count_filtered(
        self,
        table_name: str,
        search: str = None,
        available_filter: List[str] = [],
        filters: List[dict] = [],
    ) -> int:
        query = f"SELECT COUNT(*) FROM {table_name}"
        parameters = []
        conn = self.get_connection()
        cursor = conn.cursor()
        if filters:
            for i, f in enumerate(filters):
                if (
                    f["field"] not in available_filter
                    or f["value"] is None
                    or f["value"] == ""
                ):
                    continue
                if f["operator"] not in ["=", "!=", ">", "<", ">=", "<="]:
                    f["operator"] = "="
                if "WHERE" not in query:
                    query += " WHERE "
                else:
                    query += " AND "
                query += f"{f['field']} {f['operator']} ?"
                parameters.append(f["value"])

        if search:
            if "WHERE" not in query:
                query += " WHERE "
            else:
                query += " AND "
            query += "filename LIKE ?"
            parameters.append(f"%{search}%")

        try:
            cursor.execute(query, parameters)
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            raise e
