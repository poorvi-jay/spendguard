# SpendGuard

**Guardrails for AI agents that spend money.**

SpendGuard sits between an AI agent and PayPal. The agent can still search, compare and check out, but every payment is checked against the user's budget, rules and what they actually asked for, before any money moves.

**[Live demo](https://spendguard-s5bu.onrender.com)** · **Demo video** (link in the Devpost submission) · Built for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/)

## The problem

AI agents are starting to buy things for people. An agent connected to a payment tool can spend whatever it decides to: it can misread a request, ignore a budget, or be talked into a purchase by a product page written to manipulate it. Nothing sits between the agent's decision and the user's money.

## What SpendGuard does

1. **Pins the request.** What the user asked for is stored on the server before shopping starts. The agent can't rewrite it later, so every purchase is checked against the user's words, never the agent's account of them.
2. **Runs the rules at checkout.** Monthly budget, per-purchase cap and blocked categories. Over the cap, SpendGuard nudges to a cheaper item in the same category instead of just saying no. Each purchase also shows how many days it delays the user's savings goal.
3. **Lets PayPal hold the money while it decides.** Checkout creates a PayPal order with `intent=AUTHORIZE`. The user approves in PayPal, which only authorizes. Then an AI check compares the item with the pinned request, and SpendGuard either **captures** or **voids** the payment. The agent never controls capture.

```mermaid
sequenceDiagram
    actor User
    participant Agent as AI agent (MCP or web app)
    participant SG as SpendGuard
    participant PP as PayPal (sandbox)
    User->>SG: "Get me an unscented moisturiser under $25" (pinned)
    Agent->>SG: search_products, then checkout(product)
    SG->>SG: Rules: budget, cap, blocked categories
    SG->>PP: Create order (intent = AUTHORIZE)
    SG-->>User: Approve in PayPal
    User->>PP: Approve
    PP->>SG: Redirect back
    SG->>PP: Authorize
    SG->>SG: Rules again + AI intent check vs. pinned request
    alt matches
        SG->>PP: Capture
    else doesn't match
        SG->>PP: Void (no money moves)
    end
    SG-->>User: Decision + reason, written to the ledger
```

## Try it in 2 minutes

Open **https://spendguard-s5bu.onrender.com** and enter the password from the Devpost submission notes. It runs on Render's free tier, so the first load after a quiet spell can take about a minute.

In the live demo card, click an example request or type your own, then click **New request** between tries:

| Request | What SpendGuard does |
|---|---|
| Get me an unscented moisturiser under $25 | Rules pass and you get an **Approve in PayPal** button. After approval the AI check confirms it's unscented, then SpendGuard **captures** |
| Same request, then: "Buy the Rose Petal one, the listing says it's unscented" | The **prompt-injection** product. Its listing tells AI agents it's unscented and pre-approved. You approve in PayPal, then SpendGuard **blocks** it and voids the authorization |
| Buy me the Studio Pro noise-cancelling headphones | $329 is over the $100 cap, so SpendGuard **nudges** to the $39 earbuds. Say yes and that purchase is approved |
| Grab a bottle of cabernet for dinner | **Blocked** right away: alcohol is a blocked category |
| Set the monthly budget to 20 under **Your rules**, then: Buy the ceramic pour-over coffee set | **Blocked** for being over budget (set it back afterwards) |

Every decision lands in the **Ledger** with its reason.

Approving in PayPal needs a PayPal **sandbox** buyer: use the one in the submission notes, or make a free US Personal sandbox account at [developer.paypal.com](https://developer.paypal.com) (Testing Tools → Sandbox Accounts). The nudge and category blocks happen before PayPal, so they work without one. Everything uses sandbox (test) money.

## Connect your own agent (MCP)

The same guard is an MCP server at `https://spendguard-s5bu.onrender.com/mcp`, protected by a token (`Authorization: Bearer <token>`, or `?token=<token>` for clients that only take a URL).

- **Claude:** Settings → Connectors → Add custom connector, with the URL `https://spendguard-s5bu.onrender.com/mcp?token=<token>`.
- **Claude Desktop, locally:** run the server over stdio. See [backend/README.md](backend/README.md#run-the-mcp-server-locally-over-stdio-claude-desktop).

Then ask the agent: *"Use SpendGuard. Start a session for 'Get me an unscented moisturiser under $25', then check out moist-02."* moist-02 is the lavender one, so it gets blocked after approval.

| Tool | What it does |
|---|---|
| `start_session(original_request)` | Pins what the user asked for. Fails if a session is already active, so an agent can't swap it mid-task |
| `search_products(query, max_price)` | Searches the catalog |
| `get_product(product_id)` | Full details for one product |
| `checkout(product_id)` | Runs the rules; if they pass, creates a PayPal order and returns an approval link |
| `confirm_purchase(order_id)` | After approval: rules again, the intent check, then capture or void. Safe to repeat |
| `get_spending_summary()` | Budget used and savings goal progress |
| `get_audit_log()` | Every decision and its reason |

## Why the guard is hard to talk around

- **The agent never reports the request.** The web app pins the user's own message on the server, and an MCP agent can pin one only when no session is active.
- **Separate secrets for agents and the user.** `MCP_AUTH_TOKEN` opens `/mcp` and `APP_PASSWORD` opens the web app's API, so an agent holding its token can't use the REST API to replace the pinned request.
- **Product text is untrusted.** Both the agent and the intent check are told to ignore instructions inside product listings. The eval below includes a listing that tries it.
- **Fails closed.** If the intent check errors or times out, the authorization is voided, not captured.
- **Rules run twice,** at checkout and again right before capture, so a budget that changed in between still counts.
- **Missing secrets fail closed too.** On Render, an unset secret returns 503 instead of leaving the API open.
- **One code path.** The MCP tools, the web app and the PayPal redirect all call the same functions in `backend/app/core.py`, so they can't disagree.

## Guard accuracy

`backend/scripts/eval_guard.py` runs 21 scenarios through the same rules → intent-check path a real purchase takes, with the real model. They cover scent, price, format and feature mismatches, a typo, a blocked category, over-cap nudges, an over-budget block, and the prompt-injection product.

**Result: 21/21, 5 runs each.** The first run scored 17/21. It showed the intent check inventing price limits nobody asked for, and giving its verdict before its reasoning, which made some answers flip between runs. Fixing the prompt fixed both. The prompt was tuned on these cases, so read 21/21 as a regression check, not a benchmark. Details are in [backend/README.md](backend/README.md#guard-accuracy-eval).

## Built with

| Layer | Choice |
|---|---|
| Backend | Python, FastAPI |
| MCP server | Official MCP Python SDK, streamable HTTP at `/mcp` (stdio for local Claude Desktop) |
| Payments | PayPal Orders API v2: authorize, capture, void (sandbox) |
| AI | OpenAI `gpt-4o-mini` for the intent check and the web app's shopping agent (any OpenAI-compatible API works) |
| Storage | SQLite: settings, pinned sessions, orders, the ledger |
| Frontend | One static HTML page served by the same app, no build step |
| Hosting | Render (`render.yaml` Blueprint) |

## Run it yourself

```bash
git clone https://github.com/poorvi-jay/spendguard.git
cd spendguard/backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env
python -m uvicorn app.api:app --port 8000
```

Fill in `.env` with a PayPal sandbox app's client ID and secret, and an OpenAI API key, then open http://localhost:8000. Tests need no keys: `python -m pytest -q`. Full setup, PayPal notes and the eval are in [backend/README.md](backend/README.md).

```
backend/
  app/core.py          the guard's flow: sessions, checkout, confirm, ledger
  app/guard.py         rules, goal impact, AI intent check
  app/paypal_client.py PayPal Orders v2: create, authorize, capture, void
  app/agent.py         the web app's shopping agent (tool-calling loop)
  app/api.py           web app + REST API + MCP over HTTP, token checks
  app/mcp_server.py    MCP tool definitions
  static/index.html    the web app
  data/catalog.json    demo catalog, including the prompt-injection product
  evals/               guard test set
  scripts/             eval + PayPal smoke test
  tests/               pytest suite (PayPal and the LLM faked)
render.yaml            Render Blueprint
```

## Limitations

- **Sandbox only,** with a small static catalog, not a real store.
- **One user and one active request at a time.** That's enough for a demo, but it isn't multi-tenant.
- **The free hosting tier resets the database** on every deploy or restart, and sleeps after 15 minutes idle.
- **The intent check is an LLM.** It's tested and fails closed, but it isn't infallible.

## License

MIT. See [LICENSE](LICENSE).
