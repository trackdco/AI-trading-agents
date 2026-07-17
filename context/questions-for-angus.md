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

2. ~~**Session box times.**~~ ✅ ANSWERED (Angus): Asia 18:00–03:00, London 03:00–09:30,
   NY 09:30–16:00 (ET) all confirmed. Pre-market is "either/or" (NY-premarket vs late-London)
   — kept in the London box, not blocking.
   **+ NEW RULE — VWAP warm-up:** no entries in the **first hour after the 18:00 daily-VWAP
   anchor** (i.e. not before **19:00 ET**) — the daily VWAP needs time to form. Mainly affects
   the Asia/overnight (daily-model) backtests; the W1/NY window is unaffected.

## P2 — needed for the Step 8 calibration to be trustworthy (only you can answer)

3. ~~**Hand-log point-value quirks** (Feb 10, 18, 19, 27).~~ ✅ DONE — Brake corrected & pushed.

3b. ~~**Two more hand-log rows** (Feb 3 10:52, Feb 26 09:18).~~ ✅ RESOLVED (commit 6252074):
   Feb 3 → −61.5 pts (P&L −390→−369); Feb 26 → 73 pts kept, P&L 1120→1460 (the typo). All
   28 rows cross-check clean.

4. ~~**Feb 19 discretionary close** is an expected divergence.~~ ✅ CONFIRMED by Angus.

## P3 — ✅ ALL ANSWERED (Angus). Values for Brake to fold into config/strategy.yaml:

5. ~~**T_cancel**~~ → **20–25 pts, start ~22** (was 15 — too tight). Rationale: if a resting
   limit misses and price runs then returns, the trade usually fails — price rarely re-chases
   (same behaviour that motivates BE-at-1R). `entry.cancel_if_runs_points 15 → 22`.
6. ~~**Oversized stop**~~ → **40–45 pts, start ~42** → half size. Stop = bottom-of-wick of the
   rejection block, so size tracks block size; Feb median ~30, so 40–45 gives breathing room.
   The **hard 2R target minimum still applies** (a bigger stop must be justified by the target).
   NEW `sizing.oversized_stop_points = 42`.
   **+ Late-window (NEW):** 09:45–10:15 = peak AM-macro (prime). For strict-session tests,
   entries **after 10:30 → half size**. NEW `sizing.late_window_after = "10:30"`.
   **+ Confluence/sizing (clarified):** FULL = all three aligned (**BB + VWAP + POC**); HALF =
   exactly two **and they must include BB + VWAP**; **NO TRADE** if BB+VWAP aren't both present.
7. ~~**Value-area %**~~ → **70%** confirmed (standard session VP).
8. ~~**News ratings + rule**~~ → override fires on **high-impact days only**; **+ NEW RULE:** on a
   high-impact **pre-open** release (e.g. CPI 08:30), **no entries until 09:30** — let price play
   out post-news. NEW `news.no_premarket_entry_on_high_impact = true`.
   **+ Target floor (NEW):** hard **2R minimum on every trade** (not 1.5). "Thin target → half"
   is subsumed — below 2R is a no-trade, not a downsize. `targets.rr_floor 1.5 → 2.0`.

> ⚠️ **Strategy-doc reconciliation (Angus owns the v1.1 bump):** several of the above CHANGE or
> ADD to the LOCKED v1.0 doc — RR floor 1.5→2.0 (§6.5) + thin-target subsumed (§9); the
> "2 must be BB+VWAP" confluence minimum vs §7's trend-based 3-counter/2-with (reconcile); and
> three brand-new rules (VWAP warm-up, high-impact pre-open no-trade-till-09:30, oversized-stop
> & late-window half-size). Fold into strategy-definition and bump to v1.1.

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
