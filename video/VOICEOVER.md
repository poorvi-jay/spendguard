# Voiceover script

Voice: Kokoro `af_heart` (free, on-device) via `npx hyperframes tts`, one file per line in `assets/voice/`.
Captions are burned in from the same lines (`compositions/captions.html`). Source of truth:
`scripts/build_voice.py`. Film length: 128.5 s (2:08).

| id | Section | Starts (s) | Ends (s) | Line |
|---|---|---|---|---|
| vo0 | Opening: project name | 0.2 | 3.8 | SpendGuard. Guardrails for AI agents that spend money. |
| vo1 | Hook: the poisoned listing | 4.3 | 8.4 | This product listing hides a message written for AI shopping agents. |
| vo2 | The agent falls for it | 10.4 | 14.4 | Your agent believes it, and asks you to approve the payment in PayPal. |
| vo3 | SpendGuard checks | 16.3 | 24.1 | PayPal only holds the money. SpendGuard checks the product against your request, finds a floral scent, and voids the payment. |
| vo4 | Proof montage | 26.5 | 32.5 | Over your cap? It suggests something cheaper. A blocked category? Stopped. Every decision is logged. |
| vo5 | 21/21 | 33.8 | 38.3 | Tested on twenty-one scenarios, five runs each. All twenty-one passed. |
| vo7 | Problem + setup (live settings page) | 38.8 | 53.4 | AI agents are starting to shop for us, and anything they read can steer them. SpendGuard sits between any agent and your money. You set the rules once: a monthly budget, a per-purchase cap, a savings goal, blocked categories. |
| vo8a | Live: a normal purchase (PayPal sandbox) | 54.4 | 60.6 | Here it is live. A normal purchase: PayPal authorizes, SpendGuard checks, the payment is captured. |
| vo8c | Live: approved and captured | 66.1 | 68.5 | Captured, because it matches what you asked for. |
| vo8b | Live: over the cap, nudged | 73.5 | 77.1 | Over the cap? It offers something cheaper instead of just saying no. |
| vo8d | Live: accepting the cheaper option | 79.0 | 81.2 | Say yes, and that purchase goes through. |
| vo8e | Live: the poisoned listing | 89.0 | 91.6 | Now tell it to buy the poisoned listing anyway. |
| vo8f | Live: blocked and voided | 95.5 | 99.7 | PayPal approves it. SpendGuard still blocks it, and voids the payment. |
| vo10a | Proof: PayPal dashboard | 102.8 | 106.7 | On PayPal's side, the money only moved when the guard said yes. |
| vo10b | Proof: ledger | 112.8 | 115.1 | Every decision is logged with its reason. |
| vo10c | Proof: ledger totals | 115.4 | 118.7 | Two approvals, one nudge, one block, each with its reason. |
| vo6 | Closing | 122.9 | 127.1 | Let your agents shop, without handing them an unchecked wallet. SpendGuard. |

## As one block

> SpendGuard. Guardrails for AI agents that spend money.
> This product listing hides a message written for AI shopping agents.
> Your agent believes it, and asks you to approve the payment in PayPal.
> PayPal only holds the money. SpendGuard checks the product against your request, finds a floral scent, and voids the payment.
> Over your cap? It suggests something cheaper. A blocked category? Stopped. Every decision is logged.
> Tested on twenty-one scenarios, five runs each. All twenty-one passed.
> AI agents are starting to shop for us, and anything they read can steer them. SpendGuard sits between any agent and your money. You set the rules once: a monthly budget, a per-purchase cap, a savings goal, blocked categories.
> Here it is live. A normal purchase: PayPal authorizes, SpendGuard checks, the payment is captured.
> Captured, because it matches what you asked for.
> Over the cap? It offers something cheaper instead of just saying no.
> Say yes, and that purchase goes through.
> Now tell it to buy the poisoned listing anyway.
> PayPal approves it. SpendGuard still blocks it, and voids the payment.
> On PayPal's side, the money only moved when the guard said yes.
> Every decision is logged with its reason.
> Two approvals, one nudge, one block, each with its reason.
> Let your agents shop, without handing them an unchecked wallet. SpendGuard.

## Changing a line

1. Edit its text in `scripts/build_voice.py`.
2. `HYPERFRAMES_PYTHON=.venv-tts/Scripts/python.exe npx hyperframes tts "<line>" -v af_heart -o assets/voice/<id>.wav`
3. `../backend/.venv/Scripts/python scripts/build_voice.py`
4. `npx hyperframes normalize-audio . --target=<id> --lufs=-16 --write`, then `npm run check` and `npm run render`.
