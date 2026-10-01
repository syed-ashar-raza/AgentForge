import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class MemoryStore:
    def __init__(self, database_path: str | Path, limit: int = 20) -> None:
        self.database_path = Path(database_path)
        self.limit = limit
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memories (role, content, created_at)
                VALUES (?, ?, ?)
                """,
                (role, content, datetime.now(UTC).isoformat()),
            )

            connection.execute(
                """
                DELETE FROM memories
                WHERE id NOT IN (
                    SELECT id FROM memories
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (self.limit,),
            )

    def recent(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (self.limit,),
            ).fetchall()

        rows.reverse()
        return [{"role": role, "content": content} for role, content in rows]

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM memories")