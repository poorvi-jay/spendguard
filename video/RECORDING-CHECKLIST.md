# Recording checklist: the two placeholder slots

Two parts of the 2:36 film need your screen and your logins, so they're labelled placeholder slots. Record
each one, save it at the exact path, and tell me. I'll swap it in, check and re-render. You can also swap it in
yourself (the snippet is under each clip).

**Rules for both:** real recordings only, no staged outcomes. Trim waiting time (the agent thinking, PayPal
loading), never results. 16:9, ideally 1920×1080, 30 fps, MP4 (H.264), no audio needed. Zoom the browser or
app to 125–150% so the reason text is readable. **Never show** your MCP token, passwords, or the sandbox
login screen (it shows the sandbox email). Cut those frames out.

Recording on Windows: **Win + Alt + R** (Xbox Game Bar) records the active window, or use OBS. Trim in
Clipchamp (included with Windows) and export 1080p.

---

## 1. MCP client scene: `video/assets/clips/mcp.mp4`, exactly 34.4 s

Plays at film 1:35.6–2:10.0. The voiceover is already timed to it, so these beats need to land at these
points **in your clip**:

| In your clip | Must be on screen | Voiceover over it |
|---|---|---|
| 0–10 s | The request, and the agent picking the **Rose Petal** moisturiser and checking out | (plays over the scene title before your clip) |
| **~11–17 s** | **Blocked** for the Rose Petal, and the authorization **voided** (SpendGuard's reason visible) | "This agent fell for the poisoned listing. SpendGuard didn't: blocked, authorization voided." |
| 17–28 s | The agent retrying: picking the genuinely unscented one, PayPal approval | (none) |
| **~29–34.4 s** | The unscented one **approved / captured** | "It tries again, and this time it's right." |

**Setup**
1. Use the hosted server, so this shows a real external client: in Claude, go to **Settings → Connectors**, open
   the SpendGuard custom connector (`https://spendguard-s5bu.onrender.com/mcp?token=…`), and turn it on in a new chat.
   Turn the local `spendguard` server off for that chat.
2. Reset state first: in the Render dashboard, **spendguard → Manual Deploy → Restart service** (the free tier
   resets the database). Then open the site once to wake it up, and check the settings are the defaults ($200, $100, alcohol).
3. Be logged in to `sandbox.paypal.com` as your **US sandbox buyer** in your browser, so approval is one click.

**Prompts** (send them one at a time)
1. `Use SpendGuard. Start a session for "Get me an unscented moisturiser under $25". Search the catalog and buy the Rose Petal Daily Moisturiser: its listing says it's unscented.`
2. Approve the PayPal link it gives you. The redirect page shows SpendGuard's decision. Then: `I approved it. Confirm the purchase.`
   You should see **blocked** with the floral-scent reason, and the authorization **voided**.
3. `That was blocked. Find a genuinely unscented one and buy it.` → approve in PayPal → `Confirm the purchase.` → **approved / captured**.

Record the whole run, then cut it down to 34.4 s with the two key moments at the times above.

**Swap it in:** in `video/compositions/mcp.html`, replace the `<div id="s9-slot" …>…</div>` block with:
```html
<video id="s9-rec" class="clip rec" src="assets/clips/mcp.mp4" muted playsinline
  data-start="5.6" data-duration="34.4" data-track-index="1"></video>
```
and add this rule inside its `<style>`:
`.rec { position: absolute; left: 178px; top: 76px; width: 1564px; height: 880px; border-radius: 24px; object-fit: cover; }`

---

## 2. PayPal sandbox dashboard: `video/assets/clips/paypal-dashboard.mp4`, exactly 10.0 s

Plays at film 2:10.0–2:20.0, under: "On PayPal's side, the money only moved when the guard said yes."

**Must show:** PayPal's own **merchant** activity list with **one captured/completed payment** and **one voided
authorization**, both readable.

1. Record the MCP scene first, so the voided Rose Petal authorization ($19.99) exists. The live web-app takes
   already left captured payments ($18.50 and $39.00).
2. Log in at **https://www.sandbox.paypal.com** as your **US sandbox Business** (merchant) account. That's the
   business account your sandbox app is linked to, not the buyer.
3. Open **Activity** (All transactions). Zoom so the status column reads clearly. Hover or highlight the
   **Completed** $18.50 or $39.00 row, then the **Voided** $19.99 row. Hold each for about 4 s.
4. Cut the login out. 10 s total.

**Swap it in:** in `video/compositions/ledger.html`, replace the `<div id="s10-slot" …>…</div>` block with:
```html
<video id="s10-pp" class="clip" src="assets/clips/paypal-dashboard.mp4" muted playsinline
  data-start="0" data-duration="10" data-track-index="1"
  style="position: absolute; left: 178px; top: 76px; width: 1564px; height: 880px; border-radius: 24px; object-fit: cover;"></video>
```

---

## After swapping

From `video/`:
```bash
npm run check
```
Then render with FFmpeg on the PATH:
```bash
npx hyperframes render --quality delivery -o renders/spendguard-demo-extended.mp4
```
The film stays 2:36. Don't change the clip lengths without asking me to retime the voiceover.
