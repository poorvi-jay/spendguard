"""
REST API for the web frontend, plus the MCP server over streamable HTTP at
/mcp for remote agents. Both call the same functions in app/core.py.
"""

import hmac
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import core
from app.config import MCP_AUTH_TOKEN
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


class MCPTokenMiddleware:
    """Requires MCP_AUTH_TOKEN on /mcp, as a bearer header or ?token= (some
    MCP clients can only be given a URL)."""

    def __init__(self, asgi_app):
        self.app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/mcp") and MCP_AUTH_TOKEN:
            headers = dict(scope["headers"])
            supplied = headers.get(b"authorization", b"").decode().removeprefix("Bearer ").strip()
            if not supplied:
                supplied = parse_qs(scope.get("query_string", b"").decode()).get("token", [""])[0]
            if not hmac.compare_digest(supplied, MCP_AUTH_TOKEN):
                await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error": "missing or invalid MCP token"}'})
                return
        await self.app(scope, receive, send)


app.add_middleware(MCPTokenMiddleware)

# TODO narrow this to the deployed frontend origin before submitting.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    """Manual completion trigger -- used by the web app after the buyer
    returns from PayPal's approval page. Real webhook handling for Render
    is in /webhooks/paypal below."""
    return core.confirm_purchase(order_id)


@app.get("/checkout/return")
def checkout_return(token: str):
    """PayPal redirects the buyer here (return_url) after approval. `token`
    is the order_id, so the guard can decide right away. confirm_purchase is
    idempotent, so an agent confirming the same order later just gets this
    same decision back."""
    return {"order_id": token, **core.confirm_purchase(token)}


@app.get("/checkout/cancel")
def checkout_cancel():
    return {"status": "cancelled"}


@app.post("/webhooks/paypal")
def paypal_webhook(event: dict):
    # TODO verify the webhook signature (PAYPAL-TRANSMISSION-SIG etc.) before
    # trusting this in anything beyond a sandbox demo.
    if event.get("event_type") == "CHECKOUT.ORDER.APPROVED":
        order_id = event["resource"]["id"]
        return core.confirm_purchase(order_id)
    return {"status": "ignored", "event_type": event.get("event_type")}


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
