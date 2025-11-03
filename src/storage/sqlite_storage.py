"""SQLite storage backend for local data persistence."""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager


class SQLiteStorage:
    """Storage backend for SQLite database."""

    def __init__(self, db_path: Path):
        """Initialize SQLite storage.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get a database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create results table (flexible schema with JSON)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_task_id
                ON results(task_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_table_name
                ON results(table_name)
            """)

            conn.commit()

    def save_task(
        self,
        task_id: str,
        title: str,
        content: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Save task information.

        Args:
            task_id: Unique task identifier
            title: Task title
            content: Task content
            description: Optional task description
            metadata: Optional metadata dictionary
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (id, title, description, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                title,
                description,
                content,
                json.dumps(metadata) if metadata else None,
                now,
                now,
            ))

            conn.commit()

    def append_results(
        self,
        task_id: str,
        table_name: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """Append results to the database.

        Args:
            task_id: Task identifier
            table_name: Logical table name for organizing results
            data: List of result dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            for item in data:
                cursor.execute("""
                    INSERT INTO results (task_id, table_name, data, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_id,
                    table_name,
                    json.dumps(item),
                    now,
                ))

            conn.commit()

    def get_results(
        self,
        task_id: Optional[str] = None,
        table_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve results from the database.

        Args:
            task_id: Optional task ID filter
            table_name: Optional table name filter
            limit: Optional limit on number of results

        Returns:
            List of result dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM results WHERE 1=1"
            params = []

            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)

            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = json.loads(row['data'])
                result['_id'] = row['id']
                result['_task_id'] = row['task_id']
                result['_created_at'] = row['created_at']
                results.append(result)

            return results

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information.

        Args:
            task_id: Task identifier

        Returns:
            Task dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                }

            return None

    def delete_results(
        self,
        task_id: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> int:
        """Delete results from the database.

        Args:
            task_id: Optional task ID filter
            table_name: Optional table name filter

        Returns:
            Number of rows deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "DELETE FROM results WHERE 1=1"
            params = []

            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)

            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)

            cursor.execute(query, params)
            conn.commit()

            return cursor.rowcount
