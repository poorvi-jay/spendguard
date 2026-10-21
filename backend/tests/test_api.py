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
