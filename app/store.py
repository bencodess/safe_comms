import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, db_path: str = "safecomms.db") -> None:
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
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    public_key TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    recipient_id INTEGER NOT NULL,
                    ciphertext TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(recipient_id) REFERENCES users(id)
                )
                """
            )

    def create_user(self, username: str, public_key: str):
        token = secrets.token_urlsafe(32)
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO users(username, token, public_key) VALUES (?, ?, ?)",
                (username, token, public_key),
            )
            user_id = cur.lastrowid
        return {"id": user_id, "username": username, "token": token, "public_key": public_key}

    def get_user_by_username(self, username: str):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def get_user_by_token(self, token: str):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
            return dict(row) if row else None

    def update_public_key(self, user_id: int, public_key: str):
        with self._conn() as conn:
            conn.execute("UPDATE users SET public_key = ? WHERE id = ?", (public_key, user_id))

    def insert_message(
        self,
        sender_id: int,
        recipient_id: int,
        ciphertext: str,
        nonce: str,
        algorithm: str,
    ):
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO messages(sender_id, recipient_id, ciphertext, nonce, algorithm)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sender_id, recipient_id, ciphertext, nonce, algorithm),
            )
            message_id = cur.lastrowid
            row = conn.execute(
                """
                SELECT m.id, su.username AS from_username, ru.username AS to_username,
                       m.ciphertext, m.nonce, m.algorithm, m.created_at
                FROM messages m
                JOIN users su ON su.id = m.sender_id
                JOIN users ru ON ru.id = m.recipient_id
                WHERE m.id = ?
                """,
                (message_id,),
            ).fetchone()
            return dict(row)

    def inbox_for_user(self, user_id: int):
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT m.id, su.username AS from_username, ru.username AS to_username,
                       m.ciphertext, m.nonce, m.algorithm, m.created_at
                FROM messages m
                JOIN users su ON su.id = m.sender_id
                JOIN users ru ON ru.id = m.recipient_id
                WHERE m.recipient_id = ?
                ORDER BY m.id DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]
