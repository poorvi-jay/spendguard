import sqlite3
import threading
from pathlib import Path

from app.config import DB_PATH

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
_local = threading.local()

# Columns added after the first schema shipped. CREATE TABLE IF NOT EXISTS
# won't add them to an existing database, so add any that are missing.
_ADDED_COLUMNS = [
    ("settings", "monthly_savings", "REAL NOT NULL DEFAULT 300.0"),
    ("orders", "decision_reason", "TEXT"),
    ("audit_log", "order_id", "TEXT"),
    ("audit_log", "alternative_id", "TEXT"),
]
_initialized = False
_init_lock = threading.Lock()


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_PATH.read_text())
    for table, column, definition in _ADDED_COLUMNS:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")
    conn.commit()


def get_connection() -> sqlite3.Connection:
    global _initialized

    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _local.conn = conn

    if not _initialized:
        with _init_lock:
            if not _initialized:
                _init_schema(conn)
                _initialized = True

    return conn
