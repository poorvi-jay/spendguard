import sqlite3
import threading
from pathlib import Path

from app.config import DB_PATH

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
_local = threading.local()
_initialized = False
_init_lock = threading.Lock()


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_PATH.read_text())
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
