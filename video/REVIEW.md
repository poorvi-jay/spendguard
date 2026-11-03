# REVIEW: SpendGuard demo, extended cut

156 s (2:36) · 1920 × 1080 · 30 fps · voiceover + burned-in captions, no music.
Render: `renders/spendguard-demo-extended.mp4`. The 40.5 s motion cut is kept as the opening.

## Structure

| Film | Section | Source |
|---|---|---|
| 0:00–0:34.5 | Motion opening: poisoned listing → agent falls for it → guard blocks and voids → proof → 21/21 | motion graphics (HyperFrames) |
| 0:34.5–0:50 | Problem + setup | title, then a **real recording** of the settings page |
| 0:50–1:30 | Live web app | title, then **real recordings**: an approve (captured) and a nudge (cheaper option accepted, captured) on the **PayPal sandbox** |
| 1:30–2:10 | MCP client | title + **placeholder slot, 34.4 s** (`RECORDING-CHECKLIST.md` §1) |
| 2:10–2:30 | Proof | **placeholder slot, 10 s** (PayPal merchant activity, §2) + **real recording** of the ledger |
| 2:30–2:36 | Closing | existing end card |

## What's real, and how it was recorded

- The settings, approve, nudge and ledger clips are Playwright recordings of the real app against the real
  **PayPal sandbox**. The person typed the sandbox buyer password on PayPal's own page; it was never automated. Real
  results: order `25S17209CA4662904` captured ($18.50, unscented moisturiser) and `3D890101J20079413` captured
  ($39.00 earbuds via the nudge). The ledger shows those decisions with the guard's own reasons.
- They were recorded against **the local copy of the app** (`localhost:8000`, the same code and PayPal sandbox),
  not the hosted URL, because the hosted app needs `APP_PASSWORD` and the recorder can't enter it there. A fresh
  database with default settings was used for each take. The web agent now runs at temperature 0 (`backend/app/agent.py`).
- Recording-only presentation: the page was zoomed (1.33×) and given its own narrow-window, single-column layout
  so the text records large. No content or behaviour was changed.
- Edits only remove waiting time (agent thinking, PayPal's page idling) and the PayPal sign-in screen (it shows the
  sandbox email). Every outcome is shown as it happened. Cut list: `recording/edit_live.sh`.
- The opening's "agent falls for it" is staged motion graphics. The MCP slot is where a real agent falls for it.

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
- The nudge take's first second still shows the example chips before the request is typed.

## Changing things

- Narration and captions: `scripts/build_voice.py` (see `VOICEOVER.md`). A `|` in a line forces a caption break.
- Re-recording: `recording/` (`login.js`, `record_live.js approve|nudge|ledger`, `edit_live.sh`). It needs the app on
  `localhost:8000` with a fresh `DB_PATH`, and `npm i playwright` in `recording/`.
