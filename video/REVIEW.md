# REVIEW: SpendGuard demo, extended cut

159.5 s (2:39) · 1920 × 1080 · 30 fps · voiceover + burned-in captions, no music.
Render: `renders/spendguard-demo-extended.mp4`. The 40.5 s motion cut is kept as the opening.

## Structure

| Film | Section | Source |
|---|---|---|
| 0:00–0:04 | Opening card: SpendGuard name, tagline, "PayPal AI Hackathon" | motion graphics |
| 0:04–0:38.5 | Motion opening: poisoned listing → agent falls for it → guard blocks and voids → proof → 21/21 | motion graphics (HyperFrames) |
| 0:38.5–0:54 | Problem + setup | title, then a **real recording** of the settings page |
| 0:54–1:42.5 | Live web app | title, then **real recordings** on the **PayPal sandbox**: approve (captured), nudge (cheaper option accepted, captured), poisoned listing (PayPal approved, SpendGuard **blocked and voided**) |
| 1:42.5–2:13.5 | MCP client | title + **placeholder slot, 25.4 s** (`RECORDING-CHECKLIST.md` §1) |
| 2:13.5–2:33.5 | Proof | **placeholder slot, 10 s** (PayPal merchant activity, §2) + **real recording** of the ledger (Approved 2, Nudged 1, Blocked 1) |
| 2:33.5–2:39.5 | Closing | end card |

## What's real, and how it was recorded

- The settings, approve, nudge, block and ledger clips are Playwright recordings of the real app against the real
  **PayPal sandbox**. The person typed the sandbox buyer password on PayPal's own page; it was never automated. Real
  results (re-recorded on one fresh database): order `1CK872141B613954M` captured ($18.50, unscented moisturiser),
  `6F5236299F1160024` captured ($39.00 earbuds via the nudge), and `6RA44318S9907705V` authorized by PayPal then
  **voided** (Rose Petal, $19.99, blocked for its floral scent). The ledger shows those decisions with the guard's own reasons.
- They were recorded against **the local copy of the app** (`localhost:8000`, the same code and PayPal sandbox),
  not the hosted URL, because the hosted app needs `APP_PASSWORD` and the recorder can't enter it there. One fresh
  database with default settings was used for all takes, so the ledger matches the clips. It is separate from
  the hosted app's ledger. The web agent runs at temperature 0, replies in one short sentence, and asks before buying an alternative
  (`backend/app/agent.py`); checkout returns the real product name and price so the reply can't misstate it.
- Recording-only presentation: the page was zoomed (1.33×) and given its own narrow-window, single-column layout
  so the text records large. No content or behaviour was changed.
- Edits only remove waiting time (agent thinking, PayPal's page idling) and the PayPal sign-in screen (it shows the
  sandbox email). Every outcome is shown as it happened. Cut list: `recording/edit_live.sh`.
- The opening's "agent falls for it" is staged motion graphics. The MCP slot is where a real agent falls for it.

## Review-feedback round

Recorded a real block (the ledger now shows Blocked 1), trimmed the ledger's white loading frame and the landing-page
flash after PayPal's redirect, added voice lines over the silent stretches, shortened the agent's reply, and opened
the film with the project name.

## Part 1 fixes to the opening

The guard title lands as one line (no bare "SpendGuard" on black), "5 runs each", vo5 → "All twenty-one passed.",
the shorter vo4, and the end card moved to the end of the film.

## Measured vs only looked at

- `hyperframes check`: 0 errors. Warnings kept on purpose: `dead_stretch` over the two placeholder slots (they go
  away when the recordings are dropped in), `timeline_track_too_dense` on the captions track (49 caption groups),
  and `nested_media_start_basis_ambiguous` (scene-local timing is intended).
- Looked at: snapshots of every new section, the caption band, the tag band, and the PayPal frames (real PayPal
  checkout with its logo, then the Pay click).
- Audio: every voice line normalized to -16 LUFS; the render is measured below. **Measured, not heard.**
- Not checked: the final MP4 frame by frame.

## Weakest parts, and what I'd change with more time

- The live clips are upscaled 1.2× (recorded 1600×900 because the screen is 1536×864 at 125%), so the text is a
  little soft. Re-recording on a 1920×1080 at 100% screen would fix it.

## Changing things

- Narration and captions: `scripts/build_voice.py` (see `VOICEOVER.md`). A `|` in a line forces a caption break.
- Re-recording: `recording/` (`login.js`, `record_live.js approve|nudge|block|ledger`, `edit_live.sh`). It needs the app on
  `localhost:8000` with a fresh `DB_PATH`, and `npm i playwright` in `recording/`.
