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

### Stage 2c — in-trade diagnosis + management levers (DECLARED 2026-08-05 before run)
ANGUS: "we can see the diagnosis between trade setups themselves but then
also intra trade things that might help us capture more from winners and
cut losers shorter." Fit span, both legs (leg B diagnostic — parked as a
standalone, informs the complex's future and the agent playbook).
MEASUREMENTS: winners-vs-losers MFE/MAE profiles (medians/quartiles),
time-to-exit, checkpoint states t+3/5/10/15/30 with in-trade cvd,
POST-EXIT WALKOUT for winners (how far price ran beyond the target before
EOD — the capture-more question).
DECLARED LEVER ARMS (causal, evaluated on the shared minute path):
- Leg A (fast clock): A-cut3 (exit t+3 close if MAE>=0.5R); A-cut5-flow
  (exit t+5 if red AND cvd-against); A-partial (50% off at +1R, rest to
  mid); A-trail (after MFE>=1.5R stop to peak-0.75R); A-extend (at mid
  take 50%, let rest run with stop at entry to EOD — the walkout
  harvester).
- Leg B (B0 basis): B-cut15 (dying OR cvd-against — known); B-partial
  (50% at +0.5R full-risk basis); B-trail (after +1R stop to peak-0.5R).
BE remains a defeated null on both legs — no BE arm re-enters without new
prereg. All arms base friction, $160/unit-risk, ledger rows each.

STAGE 2C RESULTS (fit span; A n=112 / B n=138):
THE TWO LEGS HAVE OPPOSITE ANATOMIES:
- LEG A losers are FAILED WINNERS: 80% went >= +0.5R green before dying
  (median loser MFE 0.84R) — giveback deaths. Winners take little heat
  (median MAE 0.23R), pay in 12 min, and WALK OUT a median +2.69R BEYOND
  the mid target (p75 +4.37R) — the mid target leaves multiples on the
  table.
- LEG B losers DIE CLEAN: only 18% ever saw +0.5R (median MFE 0.32R).
  Winners walk out just +0.85R beyond target. Mirror image of A.
- BOTH legs: in-trade cvd decisive (A t+5: 56% with vs 22% against;
  B t+5: 68% vs 36%) — the canon class prior (flow decisive INSIDE the
  trade) now reproduced on every family tested.
LEVER ARMS (single-arm, fit-span, causal):
- A: cut5flow (exit t+5 if red AND cvd-against) +$990 -> $4,903 (best);
  partial 50%@+1R +$803; cut3-dying +$260; trail +$143; EXTEND (runner
  past mid, stop at entry) LOSES -$160 — the walkout is real but this
  harvester gives back more than it catches; a trail-from-target combo
  is the declared next arm.
- B: cut15 +$534 (confirmed); partial05 -$1,112 (hurts); trailB inert.
READ: A's management edge = flow-cut + profit protection (its losers are
givebacks); B's = early dying/flow cut (its losers are clean). The
walkout harvest on A is the open capture-more question — next declared
round: extend+trail combos, and the press/giveback state playbook is
agent-rung territory once the baseline is ruled. Ledger rows 244-246.

### Stage 2d — LEG-A TARGET STRUCTURE ARMS (DECLARED 2026-08-05 before run)
ANGUS: "what does this model actually target. could we try targeting
different structural levels such as vwap bands, session highs and lows...
the capture is selling a lot." Baseline target = IB mid (geometric, ~2R).
Declared target arms (stop unchanged 0.25xIB; fit span; if a structural
level sits less than 0.5R beyond entry in the profit direction at entry
time, the arm substitutes IB mid — substitutions counted):
- T0 IB mid (baseline)          - T1 opposite IB extreme (full traverse)
- T2 developing RTH session VWAP (09:30 anchor, chased as it moves)
- T3 far VWAP sigma band (VWAP -1sigma for shorts / +1sigma for longs)
- T4 session extreme-so-far at entry (day low for shorts / high for
  longs — the standing liquidity magnet, frozen at entry)
- T5 prior-day RTH close (the unfinished-business level, static)
- T6 no-target trail control (after peak >= 1R, stop trails peak-0.75R;
  else EOD) — structure-free comparison
Report per arm: n, WR, sumR, $, per-year, mean capture (realized/MFE on
winners), substitution count. Ledger rows each.

STAGE 2D RESULTS (leg-A target arms; fit run + legal full-span era check —
candle-only arms, candles never sealed):
TWO CODE BUGS CAUGHT BY PROCESS, DISCLOSED: (1) profit-direction sign flip
made every arm skip its target (caught because T0 must reproduce the
$3,913 baseline — it didn't); (2) the sigma-band arm as coded targeted
the NEAR band while the declaration said FAR — an undeclared variant ran
by accident. Both bands now run and labeled honestly; arm count 8 (7
declared + 1 disclosed).
FULL-SPAN ERA CHECK (n=356):
- T0 mid (certified default): WR 41%, $+10,865 | 2024 -9.6R (the label)
- T2 developing VWAP: WR 47%, $+11,257 | 2024 +0.6R
- NEAR SIGMA BAND (vwap+sigma on the entry side — the first structural
  shelf): WR 75%, +101.7R, $+16,274 | years +28.6/+27.2/+26.2/+19.7R —
  POSITIVE AND NEARLY UNIFORM ALL FOUR YEARS; 2024 FULLY RESCUED. The
  strongest era signature measured on this family.
- far band (across VWAP): WR 37%, $+14,801 | 2024 +1.2R, 2023-heavy.
MECHANISM READ: the fade is not a "return to the middle" trade — it is a
"return to the first volatility shelf" trade. The rejection reliably
carries to the near band; travel beyond is regime-dependent (which is
exactly why the fixed mid printed a negative 2024).
STATUS: near-band target = proposed leg-A spec upgrade. §6.0: displacing
the certified default requires tournament discipline + holdout; candle
arms have no unopened holdout -> forward SHADOW adjudication (default vs
near-band run side by side) OR Angus operator ruling (§5.12-11). His
call. Ledger rows 247-249.

CORRECTION (ANGUS, re-affirmed): "we do not give a fuck about 2023 and
2024... those years have no order flow or depth data or anything to test
variables and optimise against." The stage-2d full-span framing violated
the §5.11-9a presentation standard. FIT-SPAN numbers are the decision
numbers, restated:
- T0 mid (default):    fit WR 42%, $+3,913 (25: +8.8R / 26: +15.6R)
- T2 developing VWAP:  fit WR 51%, $+4,861 (+10.9 / +19.5)
- NEAR SIGMA BAND:     fit WR 77%, $+5,491 (+14.6 / +19.7) — +40% over
  default, best in both fit years, no substitutions.
The 23/24 candle run stays in the file as background only and carries no
decision weight. All target-arm work from here presents fit-first.

### Stage 2e — near-band stop diagnosis (DECLARED 2026-08-05 before run)
ANGUS: "run a stop loss diagnosis properly and see if we can cut losses
earlier and hold that win rate." Basis: T3 near-band target, fit span,
n=112 paired. MEASURE: MFE and MAE-before-resolution distributions,
winners vs losers. STOP ARMS (distance stops at s x risk, s in 0.3 / 0.4
/ 0.5 / 0.6 / 0.75 / 1.0-baseline; intrabar first-crossing order decides;
plus time-cuts t+3 and t+5 if MAE>=0.5R as comparison) — the frontier:
WR vs payoff vs expectancy per stop. Ledger rows for the chosen frontier
points.

STAGE 2E RESULTS (near-band basis, n=112 paired, fit span):
THE MFE/MAE ANSWER: winners under this spec take almost NO heat —
MAE-before-win median 0.06R, p75 0.26R, p90 0.47R, max 0.91R; winner MFE
median 0.98R (runs ~0.3R past the band exit). Losers poke green first
(median MFE 0.55R) then die at -1R. MECHANISM: the rejection either
works immediately or it fails — heat IS the tell on this geometry.
STOP FRONTIER (intrabar stop-first, target = near band):
  0.30R: WR 59% payoff 2.13 expct +0.281 $+5,029
  0.40R: WR 65% payoff 1.63 expct +0.310 $+5,556
  0.50R: WR 71% payoff 1.35 expct +0.348 $+6,241
  0.60R: WR 73% payoff 1.13 expct +0.352 $+6,311  <- $ peak
  0.75R: WR 74% payoff 0.91 expct +0.324 $+5,807
  1.00R: WR 77% payoff 0.69 expct +0.306 $+5,491  (baseline)
READ: because 90% of winners never exceed 0.47R adverse, a 0.5R stop
clips ~10% of winners while halving every loss — WR holds 77->71%,
payoff DOUBLES 0.69->1.35, expectancy +14%. Angus's "cut losses earlier
and hold the win rate" is exactly what the geometry offers. Candidate
shape: NEAR-BAND TARGET + 0.5R STOP (= 0.125xIB): WR 71%, payoff 1.35,
$+6,241 fit (+60% over certified default).
DISCIPLINE NOTE: leg-A fit-span arm count this session ~16 (targets 8 +
stops 8). Before any freeze: PBO across the accumulated matrix, the
§5.11-9c deep round on THIS shape (flow/depth/conviction), and the
frontier stop choice is ANGUS's shape call (0.4/0.5/0.6 all defensible).
Displacement of the certified default still requires shadow adjudication
or his operator ruling. Ledger rows 250-251.

### Stage 2f — in-trade outcome prediction on the FINAL SHAPE (DECLARED 2026-08-05)
Basis: near-band target + 0.5R stop (Angus: "71% win rate is good, i want
to see what happens intra trade"). Fast clock — checkpoints t+2/3/5/8 min,
still-open conditioning. Per checkpoint: r_now / MFE / MAE / cvd-since-
entry / book imb (where covered); outcome AUC per variable; state x flow
prediction table (the "can we accurately predict outcomes" question).

STAGE 2 CLOSE-OUT — PBO over the accumulated leg-A arm matrix (8 arms x
112 days): PBO 0.16, P(OOS loss) 0.00 — selection is finding SIGNAL
(contrast leg B's 0.87). The band-target family's edge over mid is
consistent across time blocks, not cherry-picked. VERDICT CARD: the
complex = leg A alone; proposed frozen shape = NEAR-BAND TARGET + 0.5R
STOP (WR 71%, payoff 1.35, $+6,241 fit, +60% vs certified default);
in-trade largely self-managing (half resolve in 2 min); residual agent
value = press-state EXTENSION (winners' MFE 0.98R vs 0.70R captured).
AWAITING ANGUS: shape sign-off (rule now or shadow-both vs the certified
default) -> §5.11-8 baseline -> agent rung resumes. Ledger row 252.

### Stage 2g — LOSER REPAIR on the final shape (DECLARED 2026-08-05)
ANGUS: "i still think we can make the losers look better." Basis:
near-band target + 0.5R-legacy stop; ALL numbers in TRUE-R (risk = the
actual stop distance; $160 at the stop). Declared repair arms:
- L1 cut t+2 close if red AND cvd-against (the 38%-WR cohort)
- L2 cut t+3 close if red AND cvd-against
- L3 time-scratch t+10 if red (thesis = immediate rejection; lingering
  red = dead)
- L4 time-scratch t+15 if unresolved (flat exit regardless of sign)
- L5 pressed-add structure: enter half, add half only if +0.25R-true
  within 3 min (losers half-sized by construction — sizing-shape arm)
Report per arm: WR, avg loss, payoff, expectancy (true-R), $fit, and the
loser-distribution before/after. Thin-cell honesty applies.
