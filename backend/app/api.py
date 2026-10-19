"""
REST API for the web frontend. Mirrors the MCP tool surface in
app/mcp_server.py -- both call the same functions in app/core.py.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import core

app = FastAPI(title="SpendGuard API")

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
