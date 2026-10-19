import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, guard, paypal_client  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Every test gets its own empty SQLite file instead of backend/spendguard.db."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(db, "_initialized", False)
    db._local.conn = None
    yield
    if db._local.conn is not None:
        db._local.conn.close()
        db._local.conn = None


class FakePayPal:
    """Stands in for the PayPal sandbox and records what the guard did."""

    def __init__(self):
        self.calls = []
        self.approved = True
        self._next = 0

    def create_order(self, amount, currency="USD"):
        self._next += 1
        order_id = f"ORDER{self._next}"
        self.calls.append(("create", order_id))
        return {"order_id": order_id, "approval_url": f"https://paypal.test/{order_id}", "status": "CREATED"}

    def authorize_order(self, order_id):
        if not self.approved:
            request = paypal_client.httpx.Request("POST", "https://paypal.test")
            response = paypal_client.httpx.Response(422, request=request)
            raise paypal_client.httpx.HTTPStatusError("not approved", request=request, response=response)
        self.calls.append(("authorize", order_id))
        return f"AUTH-{order_id}"

    def capture_authorization(self, authorization_id):
        self.calls.append(("capture", authorization_id))
        return {"status": "COMPLETED"}

    def void_authorization(self, authorization_id):
        self.calls.append(("void", authorization_id))

    def actions(self):
        return [name for name, _ in self.calls]


@pytest.fixture
def paypal(monkeypatch):
    fake = FakePayPal()
    for name in ("create_order", "authorize_order", "capture_authorization", "void_authorization"):
        monkeypatch.setattr(paypal_client, name, getattr(fake, name))
    return fake


@pytest.fixture
def intent(monkeypatch):
    """Controls the LLM intent check: set .matches, or .error to make it fail."""

    class Intent:
        matches = True
        error = None

        def __call__(self, product, original_request):
            if self.error:
                raise self.error
            return guard.IntentCheckResult(self.matches, "matches" if self.matches else "contradicts the request")

    fake = Intent()
    monkeypatch.setattr(guard, "check_intent", fake)
    return fake
