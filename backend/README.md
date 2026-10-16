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
- `LLM_API_KEY` -- DeepSeek (or swap `LLM_API_BASE`/`LLM_MODEL` for any
  OpenAI-compatible chat completions endpoint)

The SQLite file and its schema are created automatically on first run.

## Run the REST API (for the web frontend)

```bash
uvicorn app.api:app --reload --port 8000
```

## Run the MCP server (for Claude Desktop / any MCP client)

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

## Manual smoke test of the PayPal flow

Before wiring anything else up, confirm the sandbox authorize/capture/void
flow works end to end:

```bash
python -c "
from app import paypal_client
order = paypal_client.create_order(18.50)
print('Approve at:', order['approval_url'])
input('Press enter after approving as the sandbox buyer...')
auth_id = paypal_client.authorize_order(order['order_id'])
print('authorization_id:', auth_id)
paypal_client.capture_authorization(auth_id)
print('captured')
"
```

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
