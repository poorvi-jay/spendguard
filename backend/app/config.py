import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Explicit path so MCP clients like Claude Desktop, which launch the server
# from their own working directory, still pick up backend/.env.
load_dotenv(BACKEND_DIR / ".env")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()  # pasted dashboard values often carry a trailing newline
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
PAYPAL_API_BASE = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")
# Render sets RENDER_EXTERNAL_URL to the service's public URL.
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", f"{PUBLIC_URL}/checkout/return")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", f"{PUBLIC_URL}/checkout/cancel")

LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

_db_path = Path(os.getenv("DB_PATH", "spendguard.db"))
DB_PATH = str(_db_path if _db_path.is_absolute() else BACKEND_DIR / _db_path)
CATALOG_PATH = BACKEND_DIR / "data" / "catalog.json"

# Shared secret for the hosted /mcp endpoint. Unset means no check, which is
# only meant for local development.
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")
# Password for the web app and REST API (the user, as opposed to agents).
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
# Render sets RENDER=true; there, a missing secret fails closed instead of open.
ON_RENDER = bool(os.getenv("RENDER"))


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
