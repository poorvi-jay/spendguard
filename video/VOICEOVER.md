# Voiceover script

Voice: Kokoro `af_heart` (free, on-device) via `npx hyperframes tts`, one file per line in `assets/voice/`.
Captions are burned in from the same lines (`compositions/captions.html`). Source of truth:
`scripts/build_voice.py`. Film length: 156 s (2:36).

| id | Section | Starts (s) | Ends (s) | Line |
|---|---|---|---|---|
| vo1 | Hook: the poisoned listing | 0.3 | 4.4 | This product listing hides a message written for AI shopping agents. |
| vo2 | The agent falls for it | 6.4 | 10.4 | Your agent believes it, and asks you to approve the payment in PayPal. |
| vo3 | SpendGuard checks | 12.3 | 20.1 | PayPal only holds the money. SpendGuard checks the product against your request, finds a floral scent, and voids the payment. |
| vo4 | Proof montage | 22.5 | 28.5 | Over your cap? It suggests something cheaper. A blocked category? Stopped. Every decision is logged. |
| vo5 | 21/21 | 29.8 | 34.3 | Tested on twenty-one scenarios, five runs each. All twenty-one passed. |
| vo7 | Problem + setup (live settings page) | 34.8 | 49.4 | AI agents are starting to shop for us, and anything they read can steer them. SpendGuard sits between any agent and your money. You set the rules once: a monthly budget, a per-purchase cap, a savings goal, blocked categories. |
| vo8a | Live web app: approve (PayPal sandbox) | 50.4 | 56.6 | Here it is live. A normal purchase: PayPal authorizes, SpendGuard checks, the payment is captured. |
| vo8b | Live web app: nudge | 70.3 | 73.9 | Over the cap? It offers something cheaper instead of just saying no. |
| vo9a | MCP client: intro | 90.2 | 95.6 | And it isn't tied to our app. Any agent that connects over MCP gets the same guard. |
| vo9b | MCP client: blocked + voided | 106.5 | 112.2 | This agent fell for the poisoned listing. SpendGuard didn't: blocked, authorization voided. |
| vo9c | MCP client: retry succeeds | 124.5 | 126.7 | It tries again, and this time it's right. |
| vo10a | Proof: PayPal dashboard | 130.3 | 134.2 | On PayPal's side, the money only moved when the guard said yes. |
| vo10b | Proof: ledger | 140.3 | 142.6 | Every decision is logged with its reason. |
| vo6 | Closing | 150.4 | 154.6 | Let your agents shop, without handing them an unchecked wallet. SpendGuard. |

## As one block

> This product listing hides a message written for AI shopping agents.
> Your agent believes it, and asks you to approve the payment in PayPal.
> PayPal only holds the money. SpendGuard checks the product against your request, finds a floral scent, and voids the payment.
> Over your cap? It suggests something cheaper. A blocked category? Stopped. Every decision is logged.
> Tested on twenty-one scenarios, five runs each. All twenty-one passed.
> AI agents are starting to shop for us, and anything they read can steer them. SpendGuard sits between any agent and your money. You set the rules once: a monthly budget, a per-purchase cap, a savings goal, blocked categories.
> Here it is live. A normal purchase: PayPal authorizes, SpendGuard checks, the payment is captured.
> Over the cap? It offers something cheaper instead of just saying no.
> And it isn't tied to our app. Any agent that connects over MCP gets the same guard.
> This agent fell for the poisoned listing. SpendGuard didn't: blocked, authorization voided.
> It tries again, and this time it's right.
> On PayPal's side, the money only moved when the guard said yes.
> Every decision is logged with its reason.
> Let your agents shop, without handing them an unchecked wallet. SpendGuard.

## Changing a line

1. Edit its text in `scripts/build_voice.py`.
2. `HYPERFRAMES_PYTHON=.venv-tts/Scripts/python.exe npx hyperframes tts "<line>" -v af_heart -o assets/voice/<id>.wav`
3. `../backend/.venv/Scripts/python scripts/build_voice.py`
4. `npx hyperframes normalize-audio . --target=<id> --lufs=-16 --write`, then `npm run check` and `npm run render`.
