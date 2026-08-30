from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "messages.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room TEXT NOT NULL,
    sender TEXT NOT NULL,
    type TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room, id);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def init_db() -> None:
    with connect():
        pass


def insert_message(
    room: str, sender: str, msg_type: str, text: str, created_at: str
) -> dict:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO messages (room, sender, type, text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (room, sender, msg_type, text, created_at),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, room, sender, type, text, created_at FROM messages WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return dict(row)


def list_messages(room: str, after: int, limit: int = 100) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, room, sender, type, text, created_at
            FROM messages
            WHERE room = ? AND id > ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (room, after, limit),
        ).fetchall()
    return [dict(row) for row in rows]
