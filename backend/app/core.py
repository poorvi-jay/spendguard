"""
Shared business logic. Both app/mcp_server.py (for agent clients) and
app/api.py (for the web frontend) call into these functions so the two
interfaces can never disagree about what the guard decided.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from app import catalog, guard, paypal_client
from app.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- settings -------------------------------------------------------------


def get_settings() -> dict:
    row = get_connection().execute("SELECT * FROM settings WHERE id = 1").fetchone()
    settings = dict(row)
    settings["blocked_categories"] = json.loads(settings["blocked_categories"])
    return settings


def update_settings(**fields) -> dict:
    if "blocked_categories" in fields:
        fields["blocked_categories"] = json.dumps(fields["blocked_categories"])
    if not fields:
        return get_settings()

    conn = get_connection()
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE settings SET {assignments} WHERE id = 1", list(fields.values()))
    conn.commit()
    return get_settings()


def spent_this_month() -> float:
    conn = get_connection()
    month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM audit_log "
        "WHERE decision = 'approved' AND created_at LIKE ?",
        (f"{month_prefix}%",),
    ).fetchone()
    return row["total"]


# ---- sessions ---------------------------------------------------------------
# One active session at a time, which is enough for a single-user hackathon
# demo. Multi-session / multi-user support is a follow-up, not scaffolded here.


def start_session(original_request: str) -> dict:
    conn = get_connection()
    conn.execute("UPDATE sessions SET is_active = 0 WHERE is_active = 1")
    session_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO sessions (id, original_request, created_at, is_active) VALUES (?, ?, ?, 1)",
        (session_id, original_request, _now()),
    )
    conn.commit()
    return {"session_id": session_id, "original_request": original_request}


def get_active_session() -> Optional[dict]:
    row = get_connection().execute("SELECT * FROM sessions WHERE is_active = 1").fetchone()
    return dict(row) if row else None


# ---- catalog ----------------------------------------------------------------


def search_products(query: str = "", max_price: Optional[float] = None) -> list[dict]:
    return catalog.search_products(query, max_price)


def get_product(product_id: str) -> Optional[dict]:
    return catalog.get_product(product_id)


# ---- checkout -----------------------------------------------------------------
# This is necessarily two steps: PayPal requires the buyer to approve the
# order in PayPal's own UI before anything can be authorized, so "checkout"
# can only start that process. confirm_purchase() finishes it once approval
# has happened (via the return_url redirect or the webhook).


def _log(session_id: Optional[str], product: dict, decision: str, reason: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (session_id, product_id, product_name, amount, decision, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, product["id"], product["name"], product["price"], decision, reason, _now()),
    )
    conn.commit()


def checkout(product_id: str) -> dict:
    session = get_active_session()
    if not session:
        return {"status": "error", "reason": "No active session. Call start_session(original_request) first."}

    product = catalog.get_product(product_id)
    if not product:
        return {"status": "error", "reason": f"Unknown product_id '{product_id}'."}

    settings = get_settings()
    rule_result = guard.check_rules(product, settings, spent_this_month())

    if rule_result.decision != "pass":
        _log(session["id"], product, rule_result.decision, rule_result.reason)
        return {
            "status": rule_result.decision,
            "reason": rule_result.reason,
            "alternative": rule_result.alternative,
        }

    order = paypal_client.create_order(product["price"])
    conn = get_connection()
    conn.execute(
        "INSERT INTO orders (order_id, session_id, product_id, amount, status, created_at) "
        "VALUES (?, ?, ?, ?, 'pending_approval', ?)",
        (order["order_id"], session["id"], product_id, product["price"], _now()),
    )
    conn.commit()

    return {
        "status": "pending_approval",
        "order_id": order["order_id"],
        "approval_url": order["approval_url"],
        "note": "Open approval_url, approve as the sandbox buyer, then call confirm_purchase(order_id).",
    }


def confirm_purchase(order_id: str) -> dict:
    conn = get_connection()
    order_row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    if not order_row:
        return {"status": "error", "reason": f"Unknown order_id '{order_id}'."}
    order = dict(order_row)

    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (order["session_id"],)).fetchone()
    product = catalog.get_product(order["product_id"])

    authorization_id = paypal_client.authorize_order(order_id)
    conn.execute(
        "UPDATE orders SET status = 'authorized', authorization_id = ? WHERE order_id = ?",
        (authorization_id, order_id),
    )
    conn.commit()

    intent_result = guard.check_intent(product, session["original_request"])

    if intent_result.matches:
        paypal_client.capture_authorization(authorization_id)
        conn.execute("UPDATE orders SET status = 'captured' WHERE order_id = ?", (order_id,))
        conn.commit()
        _log(session["id"], product, "approved", intent_result.reason)
        return {"status": "approved", "reason": intent_result.reason}

    paypal_client.void_authorization(authorization_id)
    conn.execute("UPDATE orders SET status = 'voided' WHERE order_id = ?", (order_id,))
    conn.commit()
    _log(session["id"], product, "blocked", intent_result.reason)
    return {"status": "blocked", "reason": intent_result.reason}


# ---- reporting ----------------------------------------------------------------


def get_spending_summary() -> dict:
    settings = get_settings()
    spent = spent_this_month()
    return {
        "monthly_budget": settings["monthly_budget"],
        "spent_this_month": spent,
        "remaining_budget": settings["monthly_budget"] - spent,
        "savings_goal_name": settings["savings_goal_name"],
        "savings_goal_target": settings["savings_goal_target"],
        "savings_goal_saved": settings["savings_goal_saved"],
    }


def get_audit_log() -> list[dict]:
    rows = get_connection().execute("SELECT * FROM audit_log ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]
