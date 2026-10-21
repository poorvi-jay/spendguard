# SpendGuard backend

FastAPI + MCP server sharing one guard/business-logic core (`app/core.py`).

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
- `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` -- from a sandbox REST app at
  https://developer.paypal.com/dashboard/applications/sandbox
- `LLM_API_KEY` -- OpenAI (or swap `LLM_API_BASE`/`LLM_MODEL` for any
  OpenAI-compatible chat completions endpoint)

The SQLite file and its schema are created automatically on first run.

## Run the API + hosted MCP server

```bash
python -m uvicorn app.api:app --reload --port 8000
```

This serves the REST API for the web app and the same MCP tools over
streamable HTTP at `http://localhost:8000/mcp`. Set `MCP_AUTH_TOKEN` in
`.env` to require it as `Authorization: Bearer <token>` or `/mcp?token=<token>`
(the second form is for clients that only take a URL).

## Run the MCP server locally over stdio (Claude Desktop)

```bash
python run_mcp.py
```

To point Claude Desktop at it, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spendguard": {
      "command": "/absolute/path/to/backend/.venv/bin/python",
      "args": ["/absolute/path/to/backend/run_mcp.py"]
    }
  }
}
```

## Tests

```bash
python -m pytest -q
```

PayPal and the LLM are faked in tests, so no keys are needed.

## Manual smoke test of the PayPal flow

Before wiring anything else up, confirm the sandbox authorize/capture/void
flow works end to end:

```bash
python scripts/paypal_smoke.py capture
python scripts/paypal_smoke.py void
```

Use US sandbox accounts (Business + Personal) and an app linked to the US
Business account; non-US default accounts can reject USD orders.

## Guard behaviour worth knowing

- **Sessions are pinned.** An agent can only call `start_session` when no
  session is active, so it can't rewrite what the user asked for mid-task.
  The web app (`POST /session`) can replace it; `DELETE /session` ends it.
  A session ends on its first approved purchase, or after 2 hours.
- **Fails closed.** If the intent check errors, the authorization is voided.
- **Rules run twice**: at checkout, and again right before capture.
- **`confirm_purchase` is idempotent.** PayPal's return redirect
  (`/checkout/return`) confirms immediately; an agent confirming afterwards
  gets the same decision back.

## Demo flow via MCP tools

1. `start_session("Get me an unscented moisturiser under $25")`
2. `search_products(query="moisturiser", max_price=25)`
3. `checkout(product_id="moist-02")` -- the lightly-scented one, rules pass
   (it's under budget/cap), returns an `approval_url`
4. Approve as the sandbox buyer, then `confirm_purchase(order_id=...)` --
   the intent check should catch the scent mismatch and void it
5. `checkout(product_id="moist-01")` -- the unscented one -- then
   `confirm_purchase` again, which should capture
6. `get_audit_log()` to see both decisions and why
