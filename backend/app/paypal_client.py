"""
Thin client around the PayPal Orders v2 API, using the
authorize -> (capture | void) flow so SpendGuard's guard decision
is what actually moves money, not the agent.

Flow:
  1. create_order()        -> order_id, approval_url (buyer approves in PayPal's UI)
  2. authorize_order()      -> authorization_id (called after the buyer approves)
  3. capture_authorization() or void_authorization() -> the guard's final call
"""

import time

import httpx

from app.config import PAYPAL_API_BASE, PAYPAL_CANCEL_URL, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_RETURN_URL, require_paypal_credentials

_token_cache = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    require_paypal_credentials()

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    response = httpx.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }


def create_order(amount: float, currency: str = "USD") -> dict:
    """Creates an order with intent=AUTHORIZE. Returns order_id and the buyer approval URL."""
    body = {
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
            }
        ],
        "application_context": {
            "return_url": PAYPAL_RETURN_URL,
            "cancel_url": PAYPAL_CANCEL_URL,
            "user_action": "PAY_NOW",
        },
    }
    response = httpx.post(f"{PAYPAL_API_BASE}/v2/checkout/orders", headers=_headers(), json=body, timeout=20)
    response.raise_for_status()
    data = response.json()

    approval_url = next((link["href"] for link in data["links"] if link["rel"] == "approve"), None)
    return {"order_id": data["id"], "approval_url": approval_url, "status": data["status"]}


def authorize_order(order_id: str) -> str:
    """Call after the buyer has approved the order in PayPal's UI. Returns the authorization_id."""
    response = httpx.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/authorize", headers=_headers(), json={}, timeout=20
    )
    response.raise_for_status()
    data = response.json()
    return data["purchase_units"][0]["payments"]["authorizations"][0]["id"]


def capture_authorization(authorization_id: str) -> dict:
    response = httpx.post(
        f"{PAYPAL_API_BASE}/v2/payments/authorizations/{authorization_id}/capture",
        headers=_headers(),
        json={},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def void_authorization(authorization_id: str) -> None:
    response = httpx.post(
        f"{PAYPAL_API_BASE}/v2/payments/authorizations/{authorization_id}/void",
        headers=_headers(),
        timeout=20,
    )
    response.raise_for_status()
