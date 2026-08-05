# NYA-IBC-01 — THE IB COMPLEX (A/B family) — ACTIVE FAMILY [ANGUS 2026-08-05]

RULING: "lets combine them as an A and B type setup, and find the raw
trade triggers for the in fit set. then, we can optimise."

One family, two legs of the same IB oscillation, one book, one process —
the canon A/B analog (overlap study: opposed 91% of both-days but
SEQUENTIAL, hinge at the midpoint, 23 simultaneous conflicts in 4 years).

- LEG A (reversal): the certified fade — 30-min IB (09:30-10:00), first
  touch of an intact extreme in 10:00-10:30, toward mid. Stop 0.25xIB.
  Lineage: research/candidates/nya-ivb.md (13 trials).
- LEG B (continuation): IB50 — 60-min IB (09:30-10:30), first mid touch
  from 10:23 (front-run on developing levels, lookahead-clean), toward
  the second-formed extreme. Stop = first-formed extreme AS TAUGHT
  (Angus: stops way too big — stop-cap class is a declared optimization
  arm, stage 2). Lineage: research/candidates/nya-ib50.md (6 trials).
- SPAN LAW (§5.11-9a): fit = 2025-06 -> 2026-07 (full coverage); OOF =
  the six sealed months (flow/depth unburned); full candle span = era
  context only.
- CONFLICT-RULE ARMS (declared now, adjudicated at combined-book stage):
  R-A leg-A precedence while open; R-B no leg-B entry while leg-A open;
  R-C net simultaneous signals; selector prereg R1-R4 applies.
- PROCESS (one-at-a-time, Angus operates each gate): stage 1 raw fit-span
  census (below) -> stage 2 optimization (his calls; stop caps, early-cut,
  conviction sizing, flow/depth arms per §5.11-9c) -> stage 3 OOF
  declaration + single look -> stage 4 combined-book grading + conflict
  rule -> stage 5 baseline sign-off (§5.11-8) -> stage 6 agent rung ->
  shadow -> ship decision.

### Stage 1 — raw fit-span trigger census (2026-08-05, scripts/nya_ibc_census.py)
Numbers on the funnel card; no optimization applied; base 1pt friction,
$160-risk; raw as-taught geometry both legs.

STAGE 1 RESULTS (291 fit sessions, base friction, $160-risk, RAW as-taught):
- LEG A (fade): 112 first-touch triggers (~1.9/wk). WR 42.0%, +24.5R,
  $+3,913, PF 1.37, mean +0.218R, median win +1.98R / loss -1.03R.
  2025: n=55 PF 1.26 (+$1,410) | 2026: n=57 PF 1.48 (+$2,503).
  Event universe: ~31 touch-minutes/day raw contact; all-touch tradeable
  expansion +34% (trial-10 full-span measurement) — stage-2 arm.
- LEG B (IB50): 138 mid-touch triggers (~2.4/wk); 153 sessions produced
  no trade (day-death + no touch). WR 52.2%, +1.7R, $+278, PF 1.03 —
  RAW IS FLAT, and the as-taught stop is the full opposite extreme
  (mean 93pts — Angus: "way too big"; caps are the first stage-2 arm).
  2025: n=78 PF 1.21 | 2026: n=60 PF 0.83.
- COMPLEX: 202 active days (A-only 64 / B-only 90 / both 48), day corr
  -0.056, combined $+4,191, maxDD $2,043.
READ FOR STAGE 2 (Angus's calls): leg A arrives healthy raw (the
certified geometry); leg B is the optimization project — declared arm
classes queued: stop caps (§5.11-3), early-cut t+15 dying-or-cvd
(trial 4: 5.7x on fit), conviction sizing (trial 3: monotone), front-run
window (trial 5: PF 1.15 vs 0.81), flow/depth per §5.11-9c. Nothing
frozen until the OOF look (stage 3).

### Stage 1b — UNCAPPED re-census (2026-08-05, ANGUS: no trade caps on raw)
scripts/nya_ibc_census_uncapped.py — every trigger, sequential re-entries.
- LEG A: the cap was never binding — 114 events vs 112 (2 re-entries in
  13 months). One-per-day is STRUCTURAL here (window expires / day dies
  before a second touch), not a YouTube-imposed cap. No distortion.
- LEG B: 152 events vs 138 — and the 14 RE-ENTRIES ARE TOXIC: WR 21%,
  mean -0.52R, PF 0.29 ($-1,156). Mechanism READ FROM THE RAW: re-entries
  can only occur after an extreme was WICK-touched without a close
  outside (my day-death used closes); the uncapped data shows a
  wick-touch of either extreme already exhausts the continuation.
  DISCOVERED ARM for stage 2: day-death = ANY extreme touch (wick), not
  close-outside — found from raw, not imposed. Uncapped ALL: PF 0.93
  (uglier than capped 1.03, as expected — and more to decipher, as
  ordered).

### Stage 2 — leg-B optimization arm matrix (DECLARED 2026-08-05 before the lab runs)
Universe: uncapped fit-span leg-B events under BOTH day-death definitions
(close-outside = census; wick-touch = the stage-1b discovery — reported
side by side; wick-death is the proposed universe correction).
Named arms (bounded, 10; day-level R matrix -> PBO CSCV; §6.0: default =
B0 as-taught; displacement needs PBO < 0.5 AND the stage-3 OOF look):
- B0  as-taught (full-extreme stop, target = predicted extreme)
- B1  stop cap 20pt   - B2  stop cap 30pt   - B3  stop cap 50pt
- B4  stop 0.25xIB (fractional, mirrors leg A geometry)
- B5  B2 + front-run-only entries (10:23-10:29)
- B6  B2 + mechanical early-cut t+15 (dying OR cvd-against)
- B7  B2 + front-run + early-cut
- B8  B7 + conviction sizing (declared score: weekday-floor >= 0.70 +
      entry-delta agreement + book lean; units = 1 + score)
- B9  as-taught + early-cut (isolates the cut without a cap)
Cap arms keep the taught target (predicted extreme) — the cap flips the
shape to ~3-4:1 RR at lower WR; that is the point (Angus: stops way too
big). All arms base 1pt friction, $160/unit-risk, ledger rows each.

STAGE 2 RESULTS (138 leg-B events, wick-death universe, fit span):
- ANGUS'S STOP CALL VINDICATED — every cap arm beats as-taught B0 ($+278):
  B1 cap20: +46.2R, $+7,398, BOTH years positive (+12.6/+33.6), WR 30%
  at ~4.7:1 avg RR — the cap converts the coin flip into a real trade.
  B4 quarter-IB: $+4,577. B2 cap30: $+3,731. B8 full stack (cap30 +
  front-run + early-cut + conviction sizing): $+9,144.
- THE GUARD: PBO = 0.87 (slope -1.16) — in-sample ranking across these
  10 arms is mostly noise; the displacement bar (PBO < 0.5) is decisively
  NOT met on fit data alone. §6.0: B0 remains default; B1/B4/B8 BANKED.
  This is not "cap20 is fake" — it is "the fit span cannot pick among
  these arms"; the STAGE-3 OOF look (six sealed months, flow+depth
  unburned) is the designed arbiter.
- RECOMMENDATION TO ANGUS (stage-3 declaration): pre-commit a THREE-SPEC
  OOF slate — B0 (as-taught control), B1 (pure cap20, simplest strong
  arm, matches the leg-A cap20 precedent), B8 (full stack) — one written
  look, decision rule declared BEFORE the look (ship-candidate = best
  OOF performer IF OOF-positive; else park leg B and the complex ships
  leg A alone). Ledger rows 238-240.

### Stage 3 — THE SEALED-MONTHS LOOK (2026-08-05, scripts/nya_ibc_oof_look.py) — ALL THREE NEGATIVE; LEG B PARKS
Executed once per docs/OOF-DECLARATION-ibc-legB.md. 71 leg-B events across
the six sealed months (~2.7/wk, consistent with fit cadence). Sealed flow
(130,288 min) + sealed depth (19,201 min) consumed for the first time —
logged as the program's first sealed-data spend.
- B0 as-taught: -0.3R, $-44 (flat — matches its fit character)
- B1 cap20:     -29.6R, $-4,735, WR 18% — THE FIT-SPAN STAR COLLAPSES
- B8 full stack: -27.2R, $-4,358
PER THE PRE-COMMITTED RULE (all three negative): LEG B PARKS. The complex
proceeds as LEG A ALONE. No discretion was available or exercised.
FRAMEWORK NOTE: PBO 0.87 warned that fit-span ranking was noise; the OOF
look confirmed it. Had cap20 shipped off its fit-span $+7,398, it would
have shipped noise worth -$4,735 on unseen data. The §6.0 + OOF
architecture did exactly what it was built to do.
FAMILY STATUS: NYA-IBC-01 = leg A (the certified fade) alone. Stage 4
combined-book question is moot; the remaining ladder is leg A's:
baseline ruling (§5.11-8, Angus: default/cap20-W120/dual — NOTE the
leg-A cap20 challenger now carries a caution flag from leg B's cap
collapse, though its own evidence is separate) -> agent rung (paused
run) -> shadow -> ship decision. Ledger rows 241-243.
