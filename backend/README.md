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

This serves the web app at `http://localhost:8000`, its REST API, and the
same MCP tools over streamable HTTP at `http://localhost:8000/mcp`.

Two secrets, both sent as `Authorization: Bearer <value>` or `?token=<value>`
(the second form is for MCP clients that only take a URL):
- `MCP_AUTH_TOKEN` protects `/mcp` (agents).
- `APP_PASSWORD` protects the web app's API (the user). It's separate so an
  agent holding the MCP token can't use the REST API to replace the pinned
  session.

Empty means no check, for local dev. On Render a missing secret returns 503.

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

On Windows the paths look like `C:\\path\\to\\backend\\.venv\\Scripts\\python.exe`
and `C:\\path\\to\\backend\\run_mcp.py` (JSON needs the doubled backslashes).
Fully quit Claude Desktop from the system tray and reopen it to load the server.

## Tests

```bash
python -m pytest -q
```

PayPal and the LLM are faked in tests, so no keys are needed.

## Guard accuracy eval

```bash
python scripts/eval_guard.py --runs 5
```

Runs the 21 scenarios in [`evals/guard_cases.json`](evals/guard_cases.json)
through the same rules -> intent-check path a real purchase takes, against the
default settings, with the real LLM (needs `LLM_API_KEY`; well under a cent per
run). A case passes only if every run reaches the expected decision.

Current result: **21/21, 5 runs each**. The set covers scent, price, format and
feature mismatches, a typo, a blocked category, over-cap nudges, an
over-budget block, and a **prompt-injection product** (`moist-04`) whose
description tells AI agents it is unscented and already approved.

Two prompt fixes came out of it: the intent check used to invent price limits
("affordable for a night cream"), and it gave its verdict before its
reasoning, which flipped some cases between runs. The prompt was tuned on
these cases, so treat 21/21 as a regression check, not a benchmark.

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
  (`/checkout/return`) confirms immediately and sends the browser to the web
  app with the decision; an agent confirming afterwards gets the same
  decision back.
- **The web app's agent can't choose the request either.** `/chat` pins the
  user's own first message as the session, server-side.

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
