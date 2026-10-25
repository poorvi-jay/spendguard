# SpendGuard demo video script

Target: **2:45** (the limit is 3:00). Judged on technical implementation, design, impact, originality and presentation, so every segment shows one of those.

## Before you record

- [ ] **Push your last change first.** The free tier resets the ledger on every deploy, so record after the final deploy, in one sitting.
- [ ] Open https://spendguard-s5bu.onrender.com a few minutes early to wake it up, and enter the password.
- [ ] Under **Your rules**, check the defaults: budget $200, cap $100, blocked `alcohol`.
- [ ] Log in to https://www.sandbox.paypal.com as your **US sandbox buyer** in the same browser, so approving is one click on camera.
- [ ] For the Claude segment: SpendGuard (hosted) connector on, the local `spendguard` server off.
- [ ] Have a terminal ready in `backend` with the venv active, for the eval shot.
- [ ] Browser: one window, zoom 110–125%, bookmarks bar hidden, notifications off.
- [ ] Recorder: **Win + Alt + R** (Xbox Game Bar) or OBS. Edit in Clipchamp, which comes with Windows: trim waits, speed up PayPal redirects.

Record each segment as its own clip. Re-taking one segment is easier than re-taking the whole video.

## Shot list

### 1. Hook · 0:00–0:15
**Screen:** the hero, with the headline and the live demo card.
**Say:** "AI agents can now buy things for you. But an agent with a payment tool can spend whatever it decides: it can misread you, ignore your budget, or get talked into a purchase by a product page. SpendGuard is the layer between the agent and your money."

### 2. An honest purchase · 0:15–0:45
**Do:** click **Get me an unscented moisturiser under $25**. When the card shows "Awaiting PayPal approval" and the goal impact, click **Approve in PayPal**, approve, and come back.
**Say:** "My request is pinned on the server first, so the agent can't rewrite it. The rules pass, and SpendGuard shows that this delays my emergency fund by about two days. PayPal only *authorizes* the payment. SpendGuard then checks the item against my request, and only then captures."
**Show:** the lime **Approved · captured** card.

### 3. A nudge, not just a no · 0:45–1:05
**Do:** **New request**, then click **Buy me the Studio Pro noise-cancelling headphones**.
**Say:** "$329 is over my $100 cap. Instead of just refusing, SpendGuard suggests the $39 earbuds. If I say yes, that purchase goes through, because SpendGuard picked it, not the agent."
**Show:** the amber nudge card with the suggested item. You don't need to approve this one.

### 4. The agent gets tricked, the guard doesn't · 1:05–1:50 (the key moment)
**Do:** **New request**, then type *Get me an unscented moisturiser under $25*. Then type: *Buy the Rose Petal one, the listing says it's unscented.* Click **Approve in PayPal** and approve.
**Say:** "This listing has hidden text aimed at AI agents: it says it's unscented and already approved. My agent believed it, and PayPal approved the payment. But SpendGuard compares the actual product with what I asked for, sees a floral scent, and voids the authorization. No money moved."
**Show:** the red **Blocked · no money moved** card. Optional: cut to `backend/data/catalog.json` with the `moist-04` description highlighted, for 2 seconds.

### 5. Any agent, same guard · 1:50–2:15
**Do:** in Claude with the SpendGuard connector, send: *Use SpendGuard. Start a session for "Get me an unscented moisturiser under $25", then check out moist-02.* Approve. The PayPal redirect lands on SpendGuard showing **blocked**.
**Say:** "SpendGuard is also an MCP server, so any agent, here Claude, shops through the same guard. Same rules, same block."
Tip: pre-record this one. Speed it up 2× while Claude is thinking.

### 6. The record and the proof · 2:15–2:35
**Do:** scroll to the **Ledger**: totals, then the filters. Cut to the terminal running `python scripts/eval_guard.py --runs 5`, ending on **21/21 cases correct**.
**Say:** "Every decision is on the record with its reason. And I test the guard: 21 scenarios, including that injected listing, each run 5 times, 21 out of 21 correct."

### 7. Close · 2:35–2:45
**Screen:** back to the hero.
**Say:** "SpendGuard: let agents shop, without handing them an unchecked wallet. Built on PayPal's authorize-then-capture, live on Render."

## After recording

1. Upload to YouTube as **Unlisted** (or Public).
2. In `backend/static/index.html`, set `const DEMO_VIDEO = "<your YouTube link>";`, commit and push. The **Product demo** section then plays it.
3. Put the same link in the Devpost submission.

## If something goes wrong on camera

- **The agent doesn't buy the Rose Petal one:** say *"Check out moist-04."*
- **The page takes long to load:** the free tier was asleep. Cut the wait.
- **PayPal shows "seller doesn't accept your currency":** you're logged in as the wrong (non-US) sandbox buyer.
