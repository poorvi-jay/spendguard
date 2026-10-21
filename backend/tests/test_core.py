from datetime import datetime, timedelta, timezone

import httpx

from app import core
from app.db import get_connection

REQUEST = "Get me an unscented moisturiser under $25"


def _order_status(order_id):
    return get_connection().execute("SELECT status FROM orders WHERE order_id = ?", (order_id,)).fetchone()[0]


# ---- sessions -----------------------------------------------------------------


def test_agent_cannot_replace_active_session():
    core.start_session(REQUEST)
    result = core.start_session("Buy the lavender moisturiser")
    assert result["status"] == "error"
    assert core.get_active_session()["original_request"] == REQUEST


def test_user_can_replace_active_session():
    core.start_session(REQUEST)
    core.start_session("Buy a book", replace=True)
    assert core.get_active_session()["original_request"] == "Buy a book"


def test_session_expires():
    session = core.start_session(REQUEST)
    old = (datetime.now(timezone.utc) - core.SESSION_TTL - timedelta(minutes=1)).isoformat()
    get_connection().execute("UPDATE sessions SET created_at = ? WHERE id = ?", (old, session["session_id"]))
    assert core.get_active_session() is None
    assert core.start_session("Buy a book")["status"] == "started"


def test_checkout_needs_a_session(paypal):
    assert core.checkout("moist-01")["status"] == "error"
    assert paypal.calls == []


# ---- checkout + confirm -------------------------------------------------------------


def test_rule_failure_never_reaches_paypal(paypal):
    core.start_session(REQUEST)
    result = core.checkout("wine-01")
    assert result["status"] == "blocked"
    assert paypal.calls == []


def test_checkout_reports_goal_impact(paypal):
    core.start_session(REQUEST)
    result = core.checkout("moist-01")
    assert result["status"] == "pending_approval"
    assert result["goal_impact"]["days_delayed"] > 0


def test_paypal_error_is_reported_not_raised(monkeypatch):
    def fail(amount):
        request = httpx.Request("POST", "https://api-m.sandbox.paypal.com/v1/oauth2/token")
        raise httpx.HTTPStatusError("401", request=request, response=httpx.Response(401, request=request))

    monkeypatch.setattr(core.paypal_client, "create_order", fail)
    core.start_session(REQUEST)
    result = core.checkout("moist-01")
    assert result["status"] == "error"
    assert "401" in result["reason"]


def test_matching_purchase_is_captured_and_ends_session(paypal, intent):
    core.start_session(REQUEST)
    order_id = core.checkout("moist-01")["order_id"]

    assert core.confirm_purchase(order_id)["status"] == "approved"
    assert paypal.actions() == ["create", "authorize", "capture"]
    assert _order_status(order_id) == "captured"
    assert core.get_active_session() is None
    assert core.get_spending_summary()["spent_this_month"] == 18.50


def test_mismatched_purchase_is_voided(paypal, intent):
    intent.matches = False
    core.start_session(REQUEST)
    order_id = core.checkout("moist-02")["order_id"]

    assert core.confirm_purchase(order_id)["status"] == "blocked"
    assert paypal.actions() == ["create", "authorize", "void"]
    assert core.get_active_session() is not None  # agent can try another product
    assert core.get_audit_log()[0]["order_id"] == order_id


def test_intent_check_error_fails_closed(paypal, intent):
    intent.error = RuntimeError("LLM down")
    core.start_session(REQUEST)
    order_id = core.checkout("moist-01")["order_id"]

    result = core.confirm_purchase(order_id)
    assert result["status"] == "blocked"
    assert "LLM down" in result["reason"]
    assert paypal.actions()[-1] == "void"


def test_confirm_is_idempotent(paypal, intent):
    core.start_session(REQUEST)
    order_id = core.checkout("moist-01")["order_id"]
    core.confirm_purchase(order_id)

    again = core.confirm_purchase(order_id)
    assert again["status"] == "approved"
    assert again["already_decided"] is True
    assert paypal.actions().count("authorize") == 1


def test_confirm_before_buyer_approval(paypal, intent):
    paypal.approved = False
    core.start_session(REQUEST)
    order_id = core.checkout("moist-01")["order_id"]

    assert core.confirm_purchase(order_id)["status"] == "awaiting_approval"
    assert _order_status(order_id) == "pending_approval"

    paypal.approved = True
    assert core.confirm_purchase(order_id)["status"] == "approved"


def test_rules_rerun_at_confirm(paypal, intent):
    core.start_session(REQUEST)
    order_id = core.checkout("moist-01")["order_id"]
    core.update_settings(monthly_budget=10.0)  # budget shrank after checkout

    result = core.confirm_purchase(order_id)
    assert result["status"] == "blocked"
    assert paypal.actions()[-1] == "void"


def test_accepting_spendguards_nudge_is_approved(paypal, intent):
    intent.matches = False  # the intent check alone would reject earbuds for a headphones request
    core.start_session("Buy me the Studio Pro noise-cancelling headphones")
    assert core.checkout("head-02")["alternative"]["id"] == "head-01"

    order_id = core.checkout("head-01")["order_id"]
    result = core.confirm_purchase(order_id)
    assert result["status"] == "approved"
    assert "alternative" in result["reason"]


def test_unsuggested_swap_still_needs_intent_match(paypal, intent):
    intent.matches = False
    core.start_session("Buy me the Studio Pro noise-cancelling headphones")
    order_id = core.checkout("book-01")["order_id"]
    assert core.confirm_purchase(order_id)["status"] == "blocked"
