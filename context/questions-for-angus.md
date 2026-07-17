# Questions for Angus — decisions the build needs

Your lane: strategy authority + sign-offs. These are parked decisions the engine has
been running on PLACEHOLDER assumptions for. Answer inline (write after each **→**), and
they get folded into `config/strategy.yaml` / `strategy-definition-v1.0.md`. Nothing here
blocks the Step 4 gate (that's PASSED) — this clears the runway for Steps 5–8 and keeps the
Step 8 calibration honest.

Priority order is top-to-bottom. (Brake's chat calls #2 "session hours", #5 "cancel
distance", and #6 "oversized stop" — the "what did you mean" numbers he needs before he
tunes. Same items; answering here covers his nudge.)

---

## P1 — cheap, unblocks Steps 5–6 (do first)

1. **Strategy doc final read-through.** `strategy-definition-v1.0.md` still says
   *"LOCKED pending final Angus read-through."* Read it once end-to-end; confirm it's final
   (or list edits).
   **→**

2. **Session box times.** Currently PLACEHOLDER: Asia 18:00–03:00, London 03:00–09:30,
   NY 09:30–16:00 (ET). Steps 5–6 use these for session context + session-extreme targets.
   Confirm or correct.
   **→**

## P2 — needed for the Step 8 calibration to be trustworthy (only you can answer)

3. ~~**Hand-log point-value quirks** (Feb 10, 18, 19, 27).~~ ✅ DONE — Brake corrected & pushed.

3b. **Two more hand-log rows Brake couldn't safely auto-fix** (primary columns disagree with
   each other, so which is the typo is YOUR call):
   - **Feb 3 10:52** — P&L −$390 implies −65 pts, but the 61.5-pt stop implies −61.5 (you
     logged −61). Which is right: the P&L or the stop? **→**
   - **Feb 26 09:18** — P&L $1120 implies 56 pts, but Stop×R (17.25 × 4.22) implies 73 pts
     (what you logged). Is the P&L the typo, or the points? **→**

4. ~~**Feb 19 discretionary close** is an expected divergence.~~ ✅ CONFIRMED by Angus.

## P3 — config calls that are strategy, not engineering (have working placeholders)

5. **T_cancel** — cancel an unfilled entry if price runs this many points past it. Doc gives
   no start value; currently **15 pts**. OK, or set it. **→**
6. **"Oversized stop"** — one of the half-size triggers (§9). Needs a number: stop >
   ___ pts → half unit? **→**
7. **Value-area %** for VAH/VAL — currently **70%** (industry standard; POC itself is
   unaffected). Confirm. **→**
8. **News-impact ratings** — the Feb calendar's high/medium tags were best-effort; confirm
   they match how you want news days classified for the news-day target override. **→**

## P4 — scope decision (with Brake)

9. **Data range.** Loaded dataset starts **Feb 1, 2026**, not Jan 1 — fine for Feb
   calibration, but the full Jan→present run needs Brake to re-pull from Jan 1. Do you want
   the Jan-onward run, and when? **→**

---

## Your next GATE (after the build): Step 8 calibration classification

Once Steps 5–8 are built and Brake runs February, you get a report bucketing the engine's
trades vs your 28 hand trades into **MATCHED / MISSED / EXTRA**. Your job: rule every MISSED
and EXTRA as *"my setup, I missed it"* vs *"not my setup — detector too loose."* That's the
call that decides whether we tighten rules or accept divergence. Nothing to prep now beyond
P1–P3 above; just know it's coming.
