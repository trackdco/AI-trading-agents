# Questions for Angus — decisions the build needs

Your lane: strategy authority + sign-offs. These are parked decisions the engine has
been running on PLACEHOLDER assumptions for. Answer inline (write after each **→**), and
they get folded into `config/strategy.yaml` / `strategy-definition-v1.0.md`. Nothing here
blocks the Step 4 gate (that's PASSED) — this clears the runway for Steps 5–8 and keeps the
Step 8 calibration honest.

Priority order is top-to-bottom.

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

3. **Hand-log point-value quirks.** Four rows in `feb2026_hand_log.csv` look mis-keyed;
   confirm the corrected value so the calibration MATCHED/MISSED comparison is right:
   - Feb 10 logged **+11** on a −$220 loss → should be **−11**? **→**
   - Feb 18 09:42 logged **0** on a −$400 stop → should be **−20**? **→**
   - Feb 19 logged **0** on a −$150 discretionary close (see #5) **→**
   - Feb 27 09:40 logged **0** on a −$324 stop → should be **−27**? **→**

4. **Feb 19 discretionary close.** A mechanical exit will never reproduce a discretionary
   close — so the engine will show this as a divergence at Step 8. Confirm that's expected
   (not a bug to chase).
   **→**

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
