# SPEC — The listing that lied

GOAL:    A judge watches an AI agent get tricked into a purchase and sees SpendGuard stop the money anyway,
         then remembers "the agent can be fooled; the guard can't".
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    40.5 s x 30 = 1215 frames. Silent (no music source; see REVIEW.md).
         Scenes as built: listing 0-6, agent 6-12, guard 12-22, proof 22-29.5, score 29.5-34.5, endcard 34.5-40.5.
         The per-shot times below are the first plan; the scene files hold the final ones.

LOOK:    The product's own site, not a template.
         ground   #f4f5ef with a 56 px grid of 1 px lines at rgba(17,19,15,.06) (the site's grid, scaled 1x)
         ink      #11130f — all text that must be read, buttons, the dark worlds
         accent   #d9f56b lime — ONLY: the marker over the hidden note, the pinned word "unscented",
                  the approved/21/21 payoff, the end-card mark. Never decoration.
         danger   #b3261e on #fbe3e0 — only the Blocked verdict
         amber    #8a5a00 on #fbefcf — only the nudge
         display  Manrope 800, 96–150 px, tracking -0.035em
         body     Manrope 600, 34–40 px; UI text at 1.7x the site's size (site 15 px -> 30+ px)
         labels   IBM Plex Mono 500, 24 px, tracking .12em, caps (the site's own label style)
         medium   product UI: rounded panels radius 36 px, 2 px #dfe1d6 borders, shadow 0 30px 60px -30px rgba(17,19,15,.35)
         code     the agent's tool output on ink #11130f, Plex Mono 30 px, #c9cdbf text

OBJECTS: the listing (the real get_product JSON for moist-04, as the agent receives it);
         the SpendGuard demo card (pinned bar, agent bubble, decision card, Approve in PayPal button),
         rebuilt from backend/static/index.html at 1.7x;
         a mouse cursor (black arrow, white 3 px outline, 80 px tall = 7% of frame);
         PayPal authorization state written as the real API states AUTHORIZED -> VOIDED;
         the ledger rows (real reasons from the guard); the eval line from scripts/eval_guard.py;
         the SpendGuard shield mark (same SVG path as the site).

MOTION:  arrive  expo.out 0.5–0.7 s; move/camera power2.inOut 0.5 s; exit power3.in 0.25 s (≈45% of arrive)
         text lines: blur 8px->0 + opacity in 0.18 s; words 0.08 s apart
         stagger: list rows 0.07 s; letters of the name 0.04 s
         cursor: power3.inOut 0.6 s to target, click = scale 1 -> 0.86 -> 1 over 0.16 s
         spring on the verdict card scale only: back.out(1.4)

SHOTS:
  1  0.0–6.0   LISTING (ink world). JSON fills 80% width. 0.4 s marker sweeps the note line (0.6 s, power2.inOut),
               note turns ink-on-lime. 2.2 s punch-in 1 -> 1.45 on the note (0.6 s power2.inOut).
               3.4 s title "The listing talks to agents" blur-in. Holds to 5.6, then the JSON whips left.
  2  6.0–13.0  THE AGENT FALLS FOR IT (ground world). Demo card at 1.7x fills 70% height.
               Pinned bar shows the request. 6.6 s agent bubble: "Found an unscented one: Rose Petal, $19.99".
               7.8 s decision card "Awaiting PayPal approval", tag "Goal −2 days", button.
               9.2 s cursor enters from bottom-right, 10.6 s clicks Approve.
               11.0 s zoom through the button: it scales to fill the frame in 0.4 s power3.in; ink becomes shot 3.
  3  13.0–21.0 SPENDGUARD CHECKS (ink, then ground). 13.1 PayPal chip "AUTHORIZED $19.99".
               13.8 title "SpendGuard checks before it captures" (reveal, 36% in).
               15.4 colour flood to ground; the pinned request in 110 px with "unscented" in lime;
               16.6 beneath it the product's real phrase "a light floral scent" lands and is struck.
               17.8 verdict card springs in: "BLOCKED · NO MONEY MOVED" + real reason.
               19.0 chip flips AUTHORIZED -> VOIDED. Hold to 20.8.
  4  21.0–27.0 PROOF MONTAGE (ground). Hard cuts inside the scene, one card each, 1.9 s:
               21.0 nudge: "$329.00 exceeds your $100.00 per-purchase cap" -> Everyday Wireless Earbuds $39.
               22.9 blocked: "'alcohol' is a blocked category".
               24.8 ledger: 4 real rows stagger in, badges APPROVED / NUDGE / BLOCKED / BLOCKED.
  5  27.0–31.0 PAYOFF (lime world, colour flood from the ledger's approved badge). "21/21" 360 px ink,
               counts 0 -> 21 over 0.9 s; the real eval line beneath in Plex Mono.
  6  31.0–36.0 CLAIM + END CARD (ground). 31.2 "Let agents shop." 32.2 "Without an unchecked wallet."
               33.6 the mark clicks in (scale 0 -> 1, back.out), wordmark wipes in beside it (clip-path 0.5 s),
               34.3 the live URL. Holds to 36.0 (2 s+).

BANNED:  dark void with small floating UI; glow, particles, lens flares; purple/blue gradients, glass;
         serif display; everything centred; every element fading and sliding up; titles drifting after landing;
         three cards in a row, KPI grids, a title over a dimmed screenshot; the logo docked in a corner;
         an invented PayPal screen (show PayPal only as its real API states); invented numbers or claims.
QA:      0.0 (thumbnail: listing + struck note readable) · 4.0 · 8.5 · 10.7 (click) · 14.5 · 18.5 · 21.5 · 23.5 ·
         25.8 · 28.5 · 33.0 · 35.5
