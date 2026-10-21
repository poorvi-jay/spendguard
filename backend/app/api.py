"""
The web app (static/index.html), its REST API, and the MCP server over
streamable HTTP at /mcp for remote agents. All call the same app/core.py.
"""

import hmac
from contextlib import asynccontextmanager
from typing import Literal, Optional
from urllib.parse import parse_qs, urlencode

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from app import agent, core
from app.config import APP_PASSWORD, BACKEND_DIR, MCP_AUTH_TOKEN, ON_RENDER
from app.mcp_server import mcp

# Stateless so any instance can answer any request and a restart drops no
# client sessions. host="0.0.0.0" turns off the SDK's localhost-only Host
# check, which would reject Render's public hostname; the token check below
# is what keeps /mcp private instead.
mcp_app = mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="SpendGuard API", lifespan=lifespan)

# The page itself, Render's health check, and PayPal sending a browser back
# after approval (it can't carry a token).
OPEN_PATHS = {"/", "/health", "/checkout/return", "/checkout/cancel"}


class TokenMiddleware:
    """/mcp needs MCP_AUTH_TOKEN; every other route needs APP_PASSWORD. Separate
    secrets, so an agent holding the MCP token can't use the REST API to
    replace the user's pinned session. Either goes in a bearer header or
    ?token= (some MCP clients can only be given a URL)."""

    def __init__(self, asgi_app):
        self.app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] not in OPEN_PATHS:
            expected = MCP_AUTH_TOKEN if scope["path"].startswith("/mcp") else APP_PASSWORD
            if not expected and ON_RENDER:
                return await _reject(send, 503, b"server secret not configured")
            if expected:
                headers = dict(scope["headers"])
                supplied = headers.get(b"authorization", b"").decode().removeprefix("Bearer ").strip()
                if not supplied:
                    supplied = parse_qs(scope.get("query_string", b"").decode()).get("token", [""])[0]
                if not hmac.compare_digest(supplied.encode(), expected.encode()):
                    return await _reject(send, 401, b"missing or invalid token")
        await self.app(scope, receive, send)


async def _reject(send, status: int, message: bytes) -> None:
    await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"error": "' + message + b'"}'})


app.add_middleware(TokenMiddleware)


class SettingsUpdate(BaseModel):
    monthly_budget: Optional[float] = None
    per_purchase_cap: Optional[float] = None
    blocked_categories: Optional[list[str]] = None
    savings_goal_name: Optional[str] = None
    savings_goal_target: Optional[float] = None
    savings_goal_saved: Optional[float] = None
    monthly_savings: Optional[float] = None


class StartSessionBody(BaseModel):
    original_request: str


class CheckoutBody(BaseModel):
    product_id: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatBody(BaseModel):
    messages: list[ChatMessage]


@app.get("/")
def index():
    return FileResponse(BACKEND_DIR / "static" / "index.html")


@app.post("/chat")
def chat(body: ChatBody):
    if not body.messages or body.messages[0].role != "user":
        raise HTTPException(status_code=422, detail="The conversation must start with a user message.")
    return agent.chat([m.model_dump() for m in body.messages])


@app.get("/settings")
def get_settings():
    return core.get_settings()


@app.put("/settings")
def update_settings(body: SettingsUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return core.update_settings(**fields)


@app.post("/session")
def start_session(body: StartSessionBody):
    # The web app is the user, so it may replace an active session. Agents
    # going through MCP can't (see core.start_session).
    return core.start_session(body.original_request, replace=True)


@app.get("/session")
def get_session():
    return core.get_active_session()


@app.delete("/session")
def end_session():
    core.end_session()
    return {"status": "ended"}


@app.get("/products")
def search_products(query: str = "", max_price: Optional[float] = None):
    return core.search_products(query, max_price)


@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = core.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Unknown product_id '{product_id}'.")
    return product


@app.post("/checkout")
def checkout(body: CheckoutBody):
    return core.checkout(body.product_id)


@app.post("/checkout/{order_id}/confirm")
def confirm_purchase(order_id: str):
    return core.confirm_purchase(order_id)


@app.get("/checkout/return")
def checkout_return(token: str):
    """PayPal redirects the buyer here (return_url) after approval. `token`
    is the order_id, so the guard decides right away, then the web app shows
    the decision. confirm_purchase is idempotent, so an agent confirming the
    same order later just gets this same decision back."""
    result = core.confirm_purchase(token)
    return RedirectResponse(
        "/?" + urlencode({"order": token, "status": result["status"], "reason": result.get("reason") or ""}),
        status_code=303,
    )


@app.get("/checkout/cancel")
def checkout_cancel():
    return RedirectResponse("/?" + urlencode({"status": "cancelled", "reason": "You cancelled in PayPal."}), 303)


@app.get("/summary")
def get_spending_summary():
    return core.get_spending_summary()


@app.get("/audit-log")
def get_audit_log():
    return core.get_audit_log()


@app.get("/health")
def health():
    return {"status": "ok"}


# Last, so every route above wins; this only serves /mcp.
app.mount("/", mcp_app)
