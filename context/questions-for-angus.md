# Questions for Angus — decisions the build needs

Your lane: strategy authority + sign-offs. These are parked decisions the engine has
been running on PLACEHOLDER assumptions for. Answer inline (write after each **→**), and
they get folded into `config/strategy.yaml` / `strategy-definition-v1.2.md`. Nothing here
blocks the Step 4 gate (that's PASSED) — this clears the runway for Steps 5–8 and keeps the
Step 8 calibration honest.

Priority order is top-to-bottom. (Brake's chat calls #2 "session hours", #5 "cancel
distance", and #6 "oversized stop" — the "what did you mean" numbers he needs before he
tunes. Same items; answering here covers his nudge.)

---

## P1 — cheap, unblocks Steps 5–6 (do first)

1. **Strategy doc final read-through.** Now targets **v1.2** (17 Jul 2026 — v1.1 instated your
   nine rules; v1.2 instated your calibration rulings, see both changelogs in the header). Read it once end-to-end; confirm it's final
   (or list edits). The v1.1 amendments themselves are already Angus-approved; this is the
   whole-document once-over.
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

> ✅ **Strategy-doc v1.1 bump DONE** (Angus directed, 17 Jul 2026): all of the above folded into
> `strategy-definition-v1.2.md` (§2/§3/§5.5/§6.5/§7/§9 + header changelog). Reconciliation of
> "2 must be BB+VWAP" with the trend rule: counter-trend requires the full 3-type alignment;
> with-trend may trade 2-type (BB+VWAP) at half. Repo references updated; `config/strategy.yaml`
> left for Brake to update together with the new values (his lane, he's mid-build).

## P5 — NEW (surfaced by the v1.1 adversarial audit, 17 Jul) — needed before/at Step 7-8

10. ~~**Counter-trend full-confluence sizing.**~~ ⚠️ SUPERSEDED by v1.2 (same day): the
    calibration review reversed this — counter-trend now trades **FULL** size (Angus: "I
    wasn't doing 50%"). See §9 v1.2.
11. ~~**Late-window in W2.**~~ ✅ ANSWERED (Angus, 17 Jul): after-10:30 half-sizing applies
    ONLY to session-scoped (NY-only) windows; **W2 full-day has no time-based sizing at all.**
    (W2's exact span — working read 18:00→15:55 CME session — still riding on the config
    placeholder; low priority, confirm whenever.)
12. ~~**"Entry time" definition.**~~ ✅ ANSWERED (Angus, 17 Jul): **FILL time** governs every
    time cutoff (10:30 half-sizing, 11:00 window end, 09:30 news stand-down). Signal 10:28 /
    fill 10:36 = after-10:30 trade = half. Brake's Step 7 already implements the fill clock —
    no change needed.

14. ~~**The PCE edge case.**~~ ✅ ANSWERED (Angus, 17 Jul pass 9): **(b) named list only** —
    CPI / PPI / NFP-payrolls family / JOLTS / rate decisions; **PCE excluded**. Implemented
    as `filters.named_high_impact` (regex list) gating the pre-open stand-down + §6.3
    override. Feb 20 08:06 admitted. NOTE (overnight suite): the ruling costs Feb ~−12R on
    the engine (unblocked mornings added losers) — it stands on doctrine, revisit only with
    out-of-sample evidence.
13. ~~**2R measured to what.**~~ ✅ ANSWERED (Angus, 17 Jul): measured to the ACTUAL level —
    stop 40 ⇒ target level ≥ 80 pts away, and the target must be a real level, not an
    arbitrary 2R price. Front-run F is execution mechanics, excluded from the R math.

15. ~~**Does the §9 v1.1 type-ladder STACK with or SUPERSEDE the §7 count-minimum?**~~
    ✅ RULED (Angus, 17 Jul, calibration review): **SUPERSEDE — and further.** Confluence
    minimum is 2 everywhere (must be BB+VWAP; POC bonus); the 3-counter-trend minimum is
    deleted; sizing is FULL by default (half only oversized-stop/late-window). Instated in
    v1.2 + engine + config; validated on the committed slice (Feb 11 09:48 now trades, +3.92R).
    Original question preserved below for the record:
    **(superseded)**
    (Surfaced by the Step-8 calibration report — it is the single biggest driver of MISSED.)
    Your v1.1 sizing ladder says a **2-type BB+VWAP** cluster is *tradeable at half size*.
    But §7 still requires **3 confluences counter-trend / 2 with-trend**. For a 2-type
    counter-trend setup these collide: the ladder permits it (half), §7 vetoes it (2 < 3).
    The engine currently enforces BOTH (a trade must clear the §7 count AND the BB+VWAP gate),
    so many of your actual trades are vetoed for confluence 2 < 3 even when the engine detected
    the *identical* trigger you took (e.g. Feb 11 09:48 3M A, your +5.98R). The decision-log
    says the ladder "refines §7/§9" — which did you mean:
    (a) **STACK** — keep §7's 3-counter-trend minimum on top of the BB+VWAP gate (engine is
        already correct; the MISSED trades are "detector rightly stricter than me"); or
    (b) **SUPERSEDE** — the type-ladder replaces the raw count for sizing, so 2-type BB+VWAP
        is a valid HALF-size trade regardless of trend (drop min_conf_counter to 2 / gate on
        types only)? This is a rule ruling + doc bump, NOT something Brake tunes to February. **→**

16. ~~**Target selection vs the 2R floor.**~~ ✅ ANSWERED (Angus, 17 Jul pass 9): **YES —
    walk the distance-ordered menu outward to the first level clearing the floor** (veto only
    if nothing does). Implemented as `targets.walkout_under_floor: true` (resolver walk-out,
    `walkout_` name prefix for observability). Suite: MATCHED 6→8, win% 20.5→23.1.

17. ~~**V5 runner-target definition.**~~ ✅ ANSWERED (Angus, 17 Jul pass 6): V5 runner → the
    **next structural level**; V6 runner → the **one beyond it** (75% booked at first
    structure; first-PT floor 1.5). Built + measured (pass 8): both lose to V0 on Feb's
    distribution (partials cap the tail) — V0 stays active; V5/V6/V7 remain testable variants.

18. ~~**Keep vs cut pre-market.**~~ ✅ ANSWERED (Angus, 17 Jul pass 6): **KEEP — trade from
    08:00** ("that's clearly not the leak"). W1 stays 08:00–11:00.

## P4 — scope decision (with Brake)

9. ~~**Data range.**~~ ✅ ANSWERED (Angus, 17 Jul): full backtest runs **Jan 1 → present**.
   **→ Brake action:** re-pull Databento from 2026-01-01 (current dataset starts Feb 1).
   Feb calibration can run on current data meanwhile.

---

## Your next GATE (after the build): Step 8 calibration classification

Once Steps 5–8 are built and Brake runs February, you get a report bucketing the engine's
trades vs your 28 hand trades into **MATCHED / MISSED / EXTRA**. Your job: rule every MISSED
and EXTRA as *"my setup, I missed it"* vs *"not my setup — detector too loose."* That's the
call that decides whether we tighten rules or accept divergence. Nothing to prep now beyond
P1–P3 above; just know it's coming.
