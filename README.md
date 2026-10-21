# SpendGuard

**Guardrails for AI agents that spend money.**

An MCP server that lets any AI agent shop and pay through PayPal, but checks every payment against the user's budget, goals, and original request before any money moves.

Built for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/).

## Problem

AI agents are starting to buy things for people. Today, an agent connected to a payment tool can spend whatever it decides to — it might misread a request, ignore a budget, or be tricked by a malicious product page into buying something never asked for. Nothing sits between the agent's decision and your money.

## Solution

SpendGuard sits between the agent and PayPal. The agent can still search, compare, and check out, but every checkout passes through the guard first:

- **Rules check** — monthly budget, per-purchase cap, blocked categories
- **Goal impact** — how much this purchase delays the user's savings goal
- **Intent match** — an LLM compares the item against what the user originally asked for, catching both agent mistakes and prompt-injection tricks

PayPal is the enforcement point: checkout creates an order with authorize-then-capture. The user approves in PayPal, the guard makes its final decision, and SpendGuard either captures the payment (approve) or voids it (nudge/block). The agent never has direct control over capture.

## Architecture

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| MCP server | Official MCP Python SDK, served over HTTP on Render |
| Payments | PayPal Orders API (authorize, capture, void) |
| LLM | OpenAI `gpt-4o-mini` (any OpenAI-compatible API works): intent check for guard decisions, agent for the web app |
| Storage | SQLite for settings, sessions, and audit log |
| Frontend | One static page served by the same FastAPI app on Render |

## MCP Tools

PayPal requires the buyer to approve an order in its own UI before anything
can be authorized, so checkout is necessarily two calls: `checkout()` starts
it, `confirm_purchase()` finishes it once approval has happened.

| Tool | What it does |
|---|---|
| `start_session(original_request)` | Pins what the user actually asked for, once, before any shopping |
| `search_products(query, max_price)` | Finds products from the catalog |
| `get_product(id)` | Full details for one product |
| `checkout(product_id)` | Runs budget/cap/category rules; if they pass, creates a PayPal order and returns an approval link |
| `confirm_purchase(order_id)` | After buyer approval: runs the intent check, then captures or voids |
| `get_spending_summary()` | Budget used, goal progress |
| `get_audit_log()` | Past decisions and their reasons |

## Status

Live at https://spendguard-s5bu.onrender.com: the web app, its API, and the
MCP server at `/mcp`, all one FastAPI service sharing one guard core. See
[`backend/README.md`](backend/README.md) for setup and run instructions.

## License

MIT — see [LICENSE](LICENSE).
