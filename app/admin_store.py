from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AdminStore:
    def __init__(self, db_path: str = "safecomms_admin.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    path TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolved_by TEXT
                )
                """
            )

    def report_error(self, source: str, path: str, message: str) -> dict:
        now = utc_now()
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO error_reports(source, path, message, created_at, resolved_at, resolved_by)
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (source, path, message, now),
            )
            row = conn.execute("SELECT * FROM error_reports WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_error_reports(self, include_resolved: bool = True) -> list[dict]:
        q = "SELECT * FROM error_reports"
        if not include_resolved:
            q += " WHERE resolved_at IS NULL"
        q += " ORDER BY id DESC"
        with self._conn() as conn:
            rows = conn.execute(q).fetchall()
        return [dict(r) for r in rows]

    def resolve_error(self, report_id: int, resolved_by: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                """
                UPDATE error_reports
                SET resolved_at = ?, resolved_by = ?
                WHERE id = ? AND resolved_at IS NULL
                """,
                (utc_now(), resolved_by, report_id),
            )
        return cur.rowcount > 0

    def delete_error(self, report_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM error_reports WHERE id = ?", (report_id,))
        return cur.rowcount > 0
