from fastapi.testclient import TestClient

from app import api

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
}
HEADERS = {"Accept": "application/json, text/event-stream"}


def test_mcp_requires_token(monkeypatch):
    monkeypatch.setattr(api, "MCP_AUTH_TOKEN", "s3cret")
    with TestClient(api.app) as client:
        assert client.post("/mcp", json=INIT, headers=HEADERS).status_code == 401
        assert client.post("/mcp?token=wrong", json=INIT, headers=HEADERS).status_code == 401

        ok = client.post("/mcp", json=INIT, headers={**HEADERS, "Authorization": "Bearer s3cret"})
        assert ok.status_code == 200
        assert ok.json()["result"]["serverInfo"]["name"] == "SpendGuard"
        assert client.post("/mcp?token=s3cret", json=INIT, headers=HEADERS).status_code == 200

        # REST routes aren't behind the MCP token.
        assert client.get("/health").json() == {"status": "ok"}


# REST tests skip the lifespan (no `with`): the MCP session manager can only start once per process.


def test_rest_requires_app_password_not_mcp_token(monkeypatch):
    monkeypatch.setattr(api, "MCP_AUTH_TOKEN", "mcp-token")
    monkeypatch.setattr(api, "APP_PASSWORD", "app-pass")
    client = TestClient(api.app)

    assert client.get("/settings").status_code == 401
    assert client.get("/settings", headers={"Authorization": "Bearer mcp-token"}).status_code == 401
    assert client.get("/settings", headers={"Authorization": "Bearer app-pass"}).status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_missing_secret_fails_closed_on_render(monkeypatch):
    monkeypatch.setattr(api, "APP_PASSWORD", "")
    monkeypatch.setattr(api, "ON_RENDER", True)
    assert TestClient(api.app).get("/settings").status_code == 503


def test_paypal_return_redirects_to_app_with_decision(paypal, intent):
    from app import core

    core.start_session("Get me an unscented moisturiser under $25")
    order_id = core.checkout("moist-01")["order_id"]

    response = TestClient(api.app).get(f"/checkout/return?token={order_id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/?order={order_id}&status=approved")
