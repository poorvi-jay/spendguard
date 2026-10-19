import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Explicit path so MCP clients like Claude Desktop, which launch the server
# from their own working directory, still pick up backend/.env.
load_dotenv(BACKEND_DIR / ".env")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_API_BASE = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "http://localhost:8000/checkout/return")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "http://localhost:8000/checkout/cancel")

LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

_db_path = Path(os.getenv("DB_PATH", "spendguard.db"))
DB_PATH = str(_db_path if _db_path.is_absolute() else BACKEND_DIR / _db_path)
CATALOG_PATH = BACKEND_DIR / "data" / "catalog.json"


def require_paypal_credentials() -> None:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise RuntimeError(
            "PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set. "
            "Copy backend/.env.example to backend/.env and fill in your sandbox app credentials."
        )


def require_llm_credentials() -> None:
    if not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY is not set. Copy backend/.env.example to backend/.env and fill it in."
        )
