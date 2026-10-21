"""
Shared business logic. Both app/mcp_server.py (for agent clients) and
app/api.py (for the web frontend) call into these functions so the two
interfaces can never disagree about what the guard decided.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

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
# demo. The pinned request is what the intent check compares against, so an
# agent must not be able to swap it mid-task: agents can only start a session
# when none is active, and only the user (the web app, replace=True) can
# replace one. A session ends on its first approved purchase, or after
# SESSION_TTL.

SESSION_TTL = timedelta(hours=2)


def start_session(original_request: str, replace: bool = False) -> dict:
    active = get_active_session()
    if active and not replace:
        return {
            "status": "error",
            "reason": (
                f"A shopping session is already active for: '{active['original_request']}'. "
                "Only the user can replace it, from the SpendGuard app."
            ),
            "session_id": active["id"],
            "original_request": active["original_request"],
        }

    conn = get_connection()
    conn.execute("UPDATE sessions SET is_active = 0 WHERE is_active = 1")
    session_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO sessions (id, original_request, created_at, is_active) VALUES (?, ?, ?, 1)",
        (session_id, original_request, _now()),
    )
    conn.commit()
    return {"status": "started", "session_id": session_id, "original_request": original_request}


def end_session(session_id: Optional[str] = None) -> None:
    conn = get_connection()
    if session_id:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
    else:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE is_active = 1")
    conn.commit()


def get_active_session() -> Optional[dict]:
    row = get_connection().execute("SELECT * FROM sessions WHERE is_active = 1").fetchone()
    if not row:
        return None

    session = dict(row)
    if datetime.now(timezone.utc) - datetime.fromisoformat(session["created_at"]) > SESSION_TTL:
        end_session(session["id"])
        return None
    return session


# ---- catalog ----------------------------------------------------------------


def search_products(query: str = "", max_price: Optional[float] = None) -> list[dict]:
    return catalog.search_products(query, max_price)


def get_product(product_id: str) -> Optional[dict]:
    return catalog.get_product(product_id)


# ---- checkout -----------------------------------------------------------------
# This is necessarily two steps: PayPal requires the buyer to approve the
# order in PayPal's own UI before anything can be authorized, so "checkout"
# can only start that process. confirm_purchase() finishes it once approval
# has happened (via the return_url redirect, the webhook, or the agent).


def _log(
    session_id: Optional[str], product: dict, decision: str, reason: str, order_id: Optional[str] = None
) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (session_id, order_id, product_id, product_name, amount, decision, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, order_id, product["id"], product["name"], product["price"], decision, reason, _now()),
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
    impact = guard.goal_impact(product["price"], settings)

    if rule_result.decision != "pass":
        _log(session["id"], product, rule_result.decision, rule_result.reason)
        return {
            "status": rule_result.decision,
            "reason": rule_result.reason,
            "alternative": rule_result.alternative,
            "goal_impact": impact,
        }

    try:
        order = paypal_client.create_order(product["price"])
    except httpx.HTTPStatusError as e:
        # Surface PayPal's failure to the agent instead of a bare "Error executing tool".
        return {"status": "error", "reason": f"PayPal rejected the request: {e.response.status_code} {e.request.url}"}
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
        "goal_impact": impact,
        "note": "Open approval_url, approve as the sandbox buyer, then call confirm_purchase(order_id).",
    }


def _decide(product: dict, original_request: str) -> tuple[str, str]:
    """The guard's final call on an authorized order: (decision, reason)."""
    # Budget may have moved since checkout (another purchase captured in
    # between), so the rules run again before any money moves.
    rule_result = guard.check_rules(product, get_settings(), spent_this_month())
    if rule_result.decision != "pass":
        return "blocked", rule_result.reason

    # Fail closed: if the intent check can't run, the money must not move,
    # and the authorization must not be left dangling either.
    try:
        intent_result = guard.check_intent(product, original_request)
    except Exception as e:
        return "blocked", f"Intent check failed, blocking by default: {e}"

    return ("approved" if intent_result.matches else "blocked"), intent_result.reason


def confirm_purchase(order_id: str) -> dict:
    conn = get_connection()
    order_row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    if not order_row:
        return {"status": "error", "reason": f"Unknown order_id '{order_id}'."}
    order = dict(order_row)

    if order["status"] in ("captured", "voided"):
        return {
            "status": "approved" if order["status"] == "captured" else "blocked",
            "reason": order["decision_reason"],
            "already_decided": True,
        }

    # Claim the order first, so the PayPal return redirect and the agent
    # confirming at the same moment can't authorize it twice.
    claimed = conn.execute(
        "UPDATE orders SET status = 'confirming' WHERE order_id = ? AND status = 'pending_approval'", (order_id,)
    ).rowcount
    conn.commit()
    if not claimed:
        return {"status": "in_progress", "reason": "This order is already being confirmed. Try again in a moment."}

    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (order["session_id"],)).fetchone()
    product = catalog.get_product(order["product_id"])

    try:
        authorization_id = paypal_client.authorize_order(order_id)
    except httpx.HTTPStatusError as e:
        conn.execute("UPDATE orders SET status = 'pending_approval' WHERE order_id = ?", (order_id,))
        conn.commit()
        if e.response.status_code == 422:
            return {
                "status": "awaiting_approval",
                "reason": "The buyer hasn't approved this order in PayPal yet. "
                "Approve it at the approval_url from checkout, then call confirm_purchase again.",
            }
        raise

    conn.execute(
        "UPDATE orders SET status = 'authorized', authorization_id = ? WHERE order_id = ?",
        (authorization_id, order_id),
    )
    conn.commit()

    decision, reason = _decide(product, session["original_request"])

    if decision == "approved":
        paypal_client.capture_authorization(authorization_id)
        status = "captured"
    else:
        paypal_client.void_authorization(authorization_id)
        status = "voided"

    conn.execute("UPDATE orders SET status = ?, decision_reason = ? WHERE order_id = ?", (status, reason, order_id))
    conn.commit()
    _log(session["id"], product, decision, reason, order_id)
    if decision == "approved":
        end_session(session["id"])

    return {"status": decision, "reason": reason}


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
        "monthly_savings": settings["monthly_savings"],
    }


def get_audit_log() -> list[dict]:
    rows = get_connection().execute("SELECT * FROM audit_log ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]
