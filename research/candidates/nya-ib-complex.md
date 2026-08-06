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

STAGE 2G + GRADING CLOSE (2026-08-05):
- LOSER REPAIR: L1 (cut t+2 red+flow-against) makes losers prettier
  (avg -0.77, payoff 1.88) but costs ~$480 expectancy — cosmetic, not
  free. L3 (scratch t+10 if still red) is the one clean gain: WR holds
  72%, expct +0.737, $+13,205. Loss side declared MINED OUT; remaining
  money = walkout extension (offense) + conviction sizing.
- SHIP-SHAPE GRADING (band target + 0.5R stop + t10 scratch, TRUE-risk
  $160/trade, 291 fit sessions): PSR(0) 1.000 vs 0.75 floor — PASS;
  MTRL 19d vs 290 held; MC 12mo P(bust) 0.0%, median +$11,479/unit-yr;
  canon P&L correlation -0.078 (independent). Ledger row 253.
- THE 112-TRADE CONFIRMATION (Angus): yes — every headline number is the
  fit-span 112-trade set: 2.0/wk, WR 72%, avg win +1.41R true, avg loss
  -1.01R (with L3), expct +0.74R/trade.
AWAITING ANGUS (ship path): (1) operator ruling adopting the shape over
the certified default (or shadow-both); (2) loser rule pick (base+L3
recommended / base+L1 accepted-cost option); (3) then shadow -> two-party
arming with Pat. Agent rung = optional overlay AFTER mechanical ships
(his standing rule), offense-focused playbook.

### Stage 2h — AT-ENTRY CONVICTION DIAGNOSIS (DECLARED 2026-08-05)
ANGUS: "what variables are there at entry that increase and decrease win
rate... this in itself could ship higher risk cause the performance is
genuinely good regardless." Basis: final shape (band + 0.5R + t10
scratch), the 112 fit trades. Declared at-entry variable scan (all causal
at the touch minute): IB width (abs + vs trailing median), touch side,
entry clock, minutes-from-IB-completion, gap context (signed), band
distance at entry (the available RR), entry-vs-VWAP distance, VWAP slope,
entry delta / session cvd / dz, book imbalance + opposing/behind wall
ratios (coverage 10:00-10:29), weekday, trailing-5 strategy P&L,
approach velocity (pts/min over last 5m into touch), first-formed flag.
OUTPUT: per-variable WR splits + AUC table -> the conviction-ladder
candidates. This scan produces EVIDENCE for a pre-declared conviction
prereg (tiers monotonicity-tested per §5.12.1-14) — not gates; thin-cell
honesty at n=112 (terciles ~37).

STAGE 2H RESULTS (at-entry scan, final shape, n=112, base WR 72%):
UP-SHIFTERS (WR by tercile/half, mechanism-coherent):
- SESSION CVD AGAINST the fade (stretched flow): 86% vs 60% when flow
  already agrees (AUC 0.36 inverted) — the reversion pays when the
  session is stretched; the single most coherent conviction variable.
- EARLY TOUCH (entry <= ~10:10): 81% vs 60% late (AUC 0.36 inv) —
  immediate-rejection setups come early; late touches grind.
- ENTRY DELTA with the fade at the touch minute: 83% vs 66% (AUC 0.59).
- BAND DISTANCE hi (more available RR): 81% vs 71% (AUC 0.59) — wide-band
  (high-vol) sessions snap harder; conviction AND payoff rise together.
- VWAP SLOPE against the fade: 76% vs 65% — reversion-coherent.
- Wall-ahead hi: 86% but n=14 — thin, noted only.
DOWN-SHIFTERS: late entries (60%), session flow already agreeing (60%),
slope-with (65%). NOISE FLAGGED, NOT USED: weekday cells (Wed 50% / Thu
94% at n=17-24 — classic multiplicity bait), trailing-5 (dead, 74/70).
DISCIPLINE: 15 variables scanned on 112 trades — individual splits carry
multiplicity risk; the ladder is built as ONE pre-declared construct and
monotonicity-tested (§5.12.1-14), not cherry-picked cells.
PROPOSED CONVICTION LADDER (for Angus + next-round prereg): score 0-4 =
early-touch + session-cvd-stretched + entry-delta-with + band-dist-hi;
size tiers by score after monotonicity test; higher-risk shipping rides
the tiers (his call on unit scaling). Ledger row 254.

### FROZEN SPEC CANDIDATE v1 — "IB shelf fade" [ANGUS rulings 2026-08-05]
ENTRY: fade first touch of intact 30-min IB extreme, window 10:00-10:30
  (close-break veto). STOP: 0.5x legacy R = 0.125xIB beyond the extreme
  (true 1R). TARGET: near VWAP sigma band (developing), min 0.25xtrue-R
  away. SCRATCH: exit at t+10 close if still red. NO BE (defeated null).
CONVICTION LADDER (ANGUS: "2 tier... base then the confirmation at
entry"): CONFIRMED = score>=3 of {touch<=10:10, session-cvd against,
touch-minute delta with, band-dist >= median}; else BASE.
  BASE:      n=83 fit, 6.4/mo, WR 64%, +0.57R mean
  CONFIRMED: n=29 fit, 2.2/mo, WR 97%, +1.20R mean (two independent
  routes; permutation p=0.0003 raw)
UNIT RATIOS (fit-span $ at $160/unit-at-stop): 1:2 $+18,774 | 1:3
$+24,344 | 1:4 $+29,913 — ratio is Angus's sizing call.
STATUS: NOT SHIPPING (Angus). Spec frozen for SHADOW as one package;
shadow verdict must reproduce the tier separation before any size rides
it. All evidence fit-span in-fit; the shadow IS the holdout. Ledger 255.

SIZING RULING [ANGUS 2026-08-05]: $160 base / 2.5x = $400 confirmed.
Fit-span at ruled sizing: $+21,559 (base $+7,635 from 83 trades +
confirmed $+13,924 from 29 — the confirmed tier is 26% of trades and 65%
of P&L). Trade-day maxDD $412; worst day -$412. MC 12mo funded shell:
P(bust) 0.0%, median +$18,594/yr. SPEC v1 COMPLETE (entry/stop/target/
scratch/2-tier ladder/sizing) — status NOT SHIPPING; next rung = shadow
reproduction of the tier separation. Ledger row 256.

### OOF LOOK #2 RESULT (2026-08-05, per docs/OOF-DECLARATION-ibc-legA-v1.md) — PARTIAL: SPEC VALIDATED FLAT-SIZE, LADDER UNPROVEN
n=54 on the six sealed months (98% flow coverage), base 43 / confirmed 11.
- TOTAL at ruled sizing: $+6,897 — POSITIVE; 5 of 6 months green
  (2024-03: -$80 the only red).
- BASE TIER REPRODUCES ALMOST EXACTLY: WR 65% vs fit 64%; mean +0.65R vs
  fit +0.57R. THE CORE SPEC IS REAL OUT OF FIT.
- CONFIRMED TIER DOES NOT: WR 73% vs fit 97% (n=11); separation +8pp <
  the pre-committed +10pp bar. The 97% was fit-flattered, as suspected
  and warned; the sealed months did their job.
PRE-COMMITTED VERDICT: PARTIAL — the spec survives as FLAT-$160; the
2-tier conviction sizing is UNPROVEN and waits for shadow. No re-looks.
STATUS: NYA-IBC-01 leg A "IB shelf fade" = the program's first candidate
VALIDATED OUT-OF-FIT at flat size (~+0.65R/trade, ~2/wk, every-month-but-
one positive). Remaining ladder: shadow (flat-size spec live-paper +
ladder observation) -> §5.11-8 baseline -> Angus ship decision.
Ledger rows 257-258.

### RULINGS 2026-08-05 (post-OOF) + AGENT RUNG DECLARATION
- ANGUS: "im happy to ship this tbh" — ship-intent recorded; ladder still
  runs (agent rung -> shadow -> two-party arming).
- SIZING REVISED: $180 base / $360 confirmed (2.0x, replacing 160/400).
  §5.11-8 MECHANICAL BASELINE = frozen spec v1 at 180/360 — SIGNED by
  this ruling.
- AGENT RUNG (his order): full fit span, all 112 trades, chained desk run
  (canon run-1 architecture: one conversation per trade, tools disabled,
  event-driven turns, guardrails driver-enforced). Baseline = the frozen
  mechanical walk at 180/360. Graduation: agent total $ >= mechanical
  total $ AND non-negative defense delta AND zero guardrail violations.
  Defense/offense split reported per the canon journal convention.
  Spec: .claude/agents/trade-manager-shelf-v1.md (fast-clock terrain,
  honest fit + OOF numbers, walkout-extension briefing).

### AGENT RUNG RESULT (2026-08-05, runs/shelf_desk1, 111/112 trades)
HEADLINE: agent $+25,680 vs mechanical $+21,308 — +$4,373 (+21%) at
Angus's 180/360. Mech total independently reconciles the spec estimate.
ANATOMY (the honest read):
- ALL OFFENSE: +$4,459 on mech winners; defense a wash (-$87 on 30 mech
  losers) — the tight stop/scratch left nothing to save, as predicted.
- THE REFUSAL STRUCTURE IS A POSITIVE-SKEW LOTTERY: 81 band-exit
  refusals; only 22% beat the machine; median refusal delta $0 (trails
  recapture the band); typical cost -$151, worst -$411, bounded well.
  THE TOP 3 CATCHES (+$1,850/+$879/+$805) = ~79% OF THE ENTIRE EDGE.
- CONSISTENCY: only 8 of 14 months positive (range -$1,382..+$2,567) —
  the edge is lumpy, arriving in walkout bursts.
- Tier: confirmed trades carry +$3,493 of the delta (2x sizing amplifies
  refusal catches). Agent WR 72% = mech 73%; worst trades equal (-$374
  vs -$371) — downside control is genuinely clean.
INTERPRETATION: the agents are SELLING the band exit to BUY walkout
optionality at ~$100-150/ticket, paid off by a few +$800-1,850 runners.
Structurally safe per trade; the EDGE depends on big-walkout frequency
(~3-5/yr in fit), which fit cannot prove stable. In-fit, journal-fed.
RECOMMENDATION: ship the PROVEN core (mechanical flat-$180, OOF-validated)
live via the standard arming path; run BOTH overlays in SHADOW — the
2-tier ladder AND the single band-refusal agent decision (safe-default
design: agent timeout = mechanical exit). Each overlay graduates on its
own shadow receipts. Ledger row 259.

### GRADUATION RULINGS [ANGUS 2026-08-05 evening]
- SIZING GRADUATES AT $200 BASE / $300 CONFIRMED (1.5x — his call,
  §5.12-11 on the record: compresses the unproven tier's weight instead
  of shadowing it). Economics: FIT $+19,987 | OOF (sealed six months)
  $+7,405. Agent layer: NOT shipping (his read confirmed by the rung:
  lottery-shaped offense; journal + harness archived for a future
  band-refusal shadow if wanted).
- CANON OVERLAY (measured): canon active on 51 of the 112 shelf days;
  SIMULTANEOUSLY in-market only 8 days in 13 months — and ALL 8 were
  OPPOSITE-direction (same instrument: netting/flatten risk on prop
  accounts). P&L correlation -0.065 — independent stream.
- OPEN INTEGRATION ITEM (the one thing before arming): book-level
  conflict rule for those ~8 days/yr — options per selector prereg:
  R1 net both (accept the hedge) / R-canon-precedence (shelf skips its
  entry while canon holds an opposite position; costs ~7% of shelf
  entries). RECOMMENDED: canon precedence (certified breadwinner keeps
  right of way; zero integration complexity). Angus to rule; then the
  ship package goes to the standard two-party arming with Pat (currently
  gated on his certification).

### BOOK-SELECTOR AGENT RUN (DECLARED 2026-08-05, per docs/PREREG-selector.md)
ANGUS: "an agent run where it now has this strategy and the canon encoded
... what trades it takes, how it manages them ... what happens when theres
an overlapping setup opposing eachother." THE SELECTION-DISCRETION
EXPERIMENT (his long-standing rule: selection discretion must be EARNED
vs mechanical arbitration baselines; conviction tie-breaks only as
pre-declared causal scores).
DESIGN (scoped to isolate SELECTION):
- One conversation per DAY (desk view), all 112 shelf fit days (canon
  active on 51, all 8 opposite-direction conflicts included; canon-only
  days excluded — they carry no interaction information).
- Events: canon fill (take/skip), shelf touch (take/skip; tier + $200/
  $300 sizing shown), CONFLICT event when an opposing signal arrives
  while a position is open (options: net both / skip new / cut old +
  take new).
- MANAGEMENT IS MECHANICAL BOTH ENGINES this run (canon = its shipped
  two-rule walk at 1-lot dollars; shelf = frozen spec walk at 200/300) —
  per-engine management was already tested; this run tests the BOOK.
- BASELINES: B0 = take everything (net conflicts); B1 = canon precedence
  (shelf skips opposite-entry). Agent must beat BOTH to claim selection
  alpha. Skips forfeit that trade's mechanical P&L — the only lever is
  judgment.
- Spec: .claude/agents/book-selector-v1.md; harness:
  scripts/nya_book_desk_run.py; journal = day rows with every decision.

### BOOK-SELECTOR RUN REJECTED MID-FLIGHT [ANGUS 2026-08-05]
"no, i want to run the agents from the beginning and simulate as if they
were trading live with the knowledge of the 2 strategies. they dont have
any hindsight, they are placed their and make their own decisions etc
etc." Background run killed after a handful of days; runs/book_desk1
archived as NOT EVIDENCE (design mismatch — a take/skip quiz, not a
desk). Superseded by the declaration below.

### LIVE-SIM DESK RUN (DECLARED 2026-08-05, supersedes book-selector)
THE EXPERIMENT: drop an agent desk at the START of the fit span
(2025-06-02) and walk it forward chronologically, day by day, as if
live. Its ONLY knowledge: the two shipped strategy specs. Its ONLY
memory: its own journal. No hindsight of any kind.
DESIGN:
- One conversation per session day, ALL 254 fit-span days with a canon
  or shelf signal (230 canon days, 112 shelf days, 88 overlap),
  chronological. 07:45 morning read, then live events.
- KNOWLEDGE = the specs only: canon rules (two sessions, engine stop,
  working structural target, close-and-reverse law, shipped two-rule
  management as the mechanical default) and IB Shelf Fade frozen v1
  (rules, tiers, $200/$300, OOF numbers 65%/+0.65R). EXPLICITLY
  EXCLUDED: every fit-span diagnostic briefing (fast-clock, heat,
  walkout terrain) — that material is the hindsight Angus is removing.
  The prior shelf rung HAD those briefings; this run does not.
- DECISIONS (all the agent's): take/pass every signal at fill;
  management of every taken position within the standing guardrails
  (stops tighten only; canon target >=2.0R until a partial then >=0.1R;
  shelf target >=0.3R or null=ride; partials 0-1; EOD/pre-session
  flattens absolute); cross-engine conflicts entirely its call — pass,
  net the hedge, or cut the open position (close_other). Canon-vs-canon
  close-and-reverse stays ENGINE LAW (part of the spec itself).
- DEFAULTS ARE THE MACHINE: malformed/silent replies, turn-cap
  overflow (16/day), and unrefused mechanical-exit events all execute
  the mechanical book. A fully passive agent reproduces B0.
- SIZING FIXED per shipped spec (canon engine size; shelf $200/$300 by
  tier, computed causally at fill). Participation, management, and
  conflict resolution are the discretion under test — not sizing.
- BASELINES: B0 = both books fully mechanical, net conflicts (canon
  two-rule dollars; shelf frozen walk at 200/300). B1 = canon
  precedence (shelf skips entry while an opposite canon position is
  open). Passed signals logged with forfeited mechanical P&L (pass
  audit — shown in the journal digest AFTER resolution; causal).
- CAVEAT ON THE RECORD: the shelf spec was BUILT on this span, so "no
  hindsight" here means no outcome/future leakage and no diagnostic
  briefings — it cannot make the span out-of-sample. This is a
  simulation exercise for desk behaviour (selection, conflicts,
  management style), not a validation gate. Nothing ships off it
  without the standard OOF path.
- Spec: .claude/agents/live-desk-v1.md; harness:
  scripts/nya_live_desk_run.py; RUNS=runs/live_desk1; journal = day
  rows with embedded per-trade rows, every decision stamped.
- HARNESS VALIDATION (pre-launch): fully passive agent reproduces B0
  TO THE CENT on 8 test days incl. conflict days (anchoring law:
  untouched positions settle at the engine's own dollars; only agent
  deviations are simulated — capture_replay principle). Live demo day
  2025-06-04: agent took all canon fills, held mechanical exits ("day
  one baseline" in its own notes), and PASSED the 10:00 conflicting
  shelf long citing open canon short + down-flow — landing exactly on
  B1's number for the day. Demo state wiped; the real run starts
  clean at 2025-06-02. Scale: 254 days, 875 signals, 16-turn/day cap.
- CADENCE AMENDMENT [ANGUS, pre-launch]: "on a live trading desk, it
  should be making llm calls every minute. intraday adaptation etc...
  as if i were to sit infront a chart with knowledge of these 2
  strategies and trading them out myself in the given window." The
  16-turn event budget is DEAD. New rhythm: one call EVERY MINUTE the
  desk is at the chart = all of 08:00-10:30 (the only entry window
  either engine has) + every minute a position is open after 10:30;
  flat after 10:30 ends the day. Signal and mechanical-exit turns
  count as that minute's call. Reply contract gains "pos" (target
  position when >1 open). MAX_TURNS_DAY=600 is a runaway ceiling, not
  a budget. Passive-agent==B0 re-validated at minute cadence before
  relaunch.
- FINAL LAUNCH CALIBRATION [ANGUS, three rulings pre-launch]:
  (1) HYBRID CADENCE — full minute-by-minute WHILE HOLDING (the part
  the live desk will query); 5-minute pulse + every signal minute
  while flat in 08:00-10:30 ("that shit will take way too long"
  otherwise; in-trade record stays complete).
  (2) MONTH-PARALLEL — days within a calendar month run concurrently
  (6 workers), journal chains month-to-month. His words: "might not be
  exactly what a live agent moving on day to day might look like, but
  its the closest we can get while still being quick."
  (3) MODEL — desk turns run on Sonnet (his usage call). Recorded for
  basis-stamping: any future comparison of this archive against a
  different-model desk must note the model changed.
  KNOWLEDGE BASE confirmed with him: both rulebooks in full + holdout
  performance (shelf OOF 65%/+0.65R; canon = certified live core), NO
  fit-span diagnostics, no outcome hindsight. Full discretion on
  participation, management, conflicts. Mirrors the live seat: rulebooks
  + holdout record + (this archive, once it exists).
- CHARTER v1.1 MID-RUN [ANGUS, 6 days in]: "just to be sure it can take
  whatever trade it wants... can also manage the trades as in cut them
  earlier, hold them longer, take partials... 7 days in a row being
  identical is sus and points towards discretion not really being
  there." First 6 days (2025-06-02..06-10, all June batch) ran on
  charter v1.0: 2 deviated days (+$300 mgmt touch, -$385 conflict
  pass), 4 identical — transcripts show "trust engine management / no
  override on day one" rubber-stamping. v1.0's framing over-anchored
  passivity ("machine never punishes passivity"; canon "dies by a
  thousand management mistakes"); v1.1 removes both and states the
  default-vs-recommendation distinction explicitly. BASIS STAMP: any
  v1.0-vs-v1.1 behavioral comparison must split on this boundary.
  KNOWN ARTIFACT: month-parallel means every June day trades on an
  EMPTY journal ("day one" x21) — June conservatism is structural;
  July onward carries a month of record.
- CHARTER v1.2 + ARCHIVE DEPTH [ANGUS, mid-June batch]: "make sure the
  agent is taking deep notes on every trade it takes. all variables you
  know." (a) DEBRIEF TURN: one journal entry per closed agent-taken
  trade (entry read / in-trade / resolution / lesson, <=500 chars),
  written knowing the machine counterfactual (causal — post-close);
  stored on the trade row, last 2 fed back through the monthly digest.
  (b) FULL TRADE RECORD mechanically on every taken trade — his spec:
  "not just entry variables but intra trade variables where the trade
  turned against it... where it could have captured more, market
  conditions." ENTRY: delta1m/cvd5m/cvd15m/opposed5/volx, book
  imbalance + nearest wall, vwap & near-band distance in R, vwap
  slope, RTH range so far, tier score. IN-TRADE PATH: MFE/MAE in R
  with minutes-to-each, first-red minute + cvd5 there, held minutes,
  capture (realized/peak), flow at exit (cvd5/opposed). POST-EXIT:
  run after exit on the original stop (left_peak_R), would-have-
  stopped flag, session settle R. MARKET CONDITIONS: gap, overnight
  range, prior-day range per day. The debrief prompt hands the agent
  its own path (MFE/MAE/turn/after) so the lesson is written against
  facts; the monthly digest adds canon run-1 conditioned gauges (early
  cuts by flow state: would-have-died rate + median run-after; capture
  median). BASIS STAMP: days completed before the mid-June restart
  carry none of these fields; Angus also confirmed B0 semantics = both
  engines stacked at shipped spec, P&Ls summed, opposite-direction
  overlaps net.

### JUNE AUDIT — TWO HARNESS BUGS FOUND, JUNE VOIDED [ANGUS 2026-08-05]
His call before spending more: "i dont think we calibrated it properly
... see if theres any early signs of bugs or errors we might have
calibrated agents around ... before i waste more usage doing a broken
test." Run stopped at 19 days; full audit of journal + 912 transcript
turns. Deficit at stop: agent $+6,045 vs B0 $+7,062 (-$1,017).
BUG 1 (DOMINANT, material) — THE AGENT INHERITED CANON POSITIONS
STRIPPED OF THE SHIPPED PARTIAL. 43.8% of canon trades bank a 50%
partial in their shipped management (partial+target 351, partial+stop
467, partial+be_stop 3). The harness handed the agent only {stop,
working target}, so ANY management touch silently converted the trade
into a naked position — biasing the entire experiment against
discretion. Evidence: both big June losses were shipped partial+target
trades where the agent trailed and lost the whole position
(2025-06-20 C4 agent $1,055 vs mech $1,701 = -$646; 2025-06-23 C2
$180 vs $715 = -$535). FIX: recover the partial price via
capture_replay.implied_partial (the engine's own inverted arithmetic),
carry it as a standing order the agent inherits and can override,
disclose it on the signal line and in the book state, and warn about
it in the charter. POST-FIX PROOF: the same 06-20 C4 under a
trail-to-BE stub now settles $+1,701 = mech exactly (was -$646).
BUG 2 (real, pervasive) — R UNITS WRONG ON 31% OF CANON POSITIONS +
HINDSIGHT LEAK. The book's `stop` column is not reliably the initial
stop: 28% disagree with `risk`, and 51 trades sit ~BE yet exit 'stop'
for ~$15 (a MOVED stop = post-hoc information). The agent was told
"engine stop (-1R, INVIOLATE)" while its state line showed -0.12R to
-0.94R, and its stop_r requests were converted through `risk` rather
than the real stop distance — the same TRUE-R class of error Angus
caught on the shelf $-sizing. FIX: reconstruct the initial stop as
entry - s*risk (the engine's own -1R, no post-hoc content).
POST-FIX: 100% of canon signals now open at exactly -1.00R (was 72%).
CLEARED (audited, no defect): sizing/dollar convention (dollars_1lot
is at-size; settle matches; half-size rows reconcile to 0.00);
anchoring law (untouched-trade drift exactly $0.00 across 19 days);
full P&L decomposition reconciles to the cent; 0 CLI errors in 912
turns; 0 silently-dropped decisions (the agent always named `pos`);
the agent was genuinely trading (25 revises with coherent trailing
logic, 6 passes with stated reasons, 3 of them money-saving).
RULING: the 19 June days are VOID as evidence — archived to
runs/_archive/live_desk1_prebugfix/. Run restarts clean from
2025-06-02 on the corrected harness.

### CHAINING AMENDMENT — FORTNIGHTLY [ANGUS 2026-08-05]
"what if we did every 2 trading weeks for higher frequency, re run it
with that calibration. the closer we can get to a day the better, just
dont want to wait a million years." RULED: journal now chains every 10
TRADING DAYS (2 trading weeks), 26 blocks across the span, replacing
calendar-month chaining. THE ECONOMICS (why finer is also faster):
wall clock = 254/min(BATCH, WORKERS) waves, so batch granularity is
free until it drops below the worker count. Raising WORKERS 6->10
alongside BATCH=10 gives fortnightly learning in 26 waves (~8h) vs the
old 21-day/6-worker setup at 43 waves (~14h) — finer AND ~6h quicker.
Measured alternatives on the record: 10-day/6w = 43 waves (~14h, no
gain); 5-day = parallelism capped at 5, 51 waves (~16h); daily
chaining = fully sequential, 254 waves (~80h) — the "million years"
case, and the honest reason daily is out of reach. Charter v1.3 tells
the desk its book rolls fortnightly; dashboard deviation-rate now
buckets per journal block instead of per calendar month. Passive==B0
re-validated at the new settings.

### DIGEST GAUGE FIX — THE TRAIL LEAK WAS INVISIBLE [2026-08-05, day 29]
Angus, on the block-2 giveback: "id like to think the agents will learn
from that give back." CHECKED RATHER THAN ASSUMED — and the feedback
loop was aimed at the wrong behaviour. The digest carried the canon
run-1 gauge for EARLY CUTS (exit_reason 'agent_exit'): n=2 in 29 days,
i.e. noise. The desk's actual dominant behaviour is TIGHTENING A STOP
UNTIL IT CATCHES THE TRADE — those die as exit_reason 'stop' above
-0.95R and were counted nowhere: n=32, net -$378 vs letting the engine
run them. The single biggest leak was absent from the desk's own
feedback; it could only see it through the last-2 rotating debrief
quotes. FIX: added a TRAIL GAUGE to the digest, split by the flow state
the desk tightened into (same conditioning convention as run-1), so the
lesson reads "when it looked like THIS" rather than a blanket "stop
trailing" — important because trailing is NOT uniformly bad here
(several trails beat the machine: +$300 saving a loser, +$332, +$258).
First reading, day 29: trailed with flow still WITH you n12 -$150,
median +2.36R ran on after the stop hit; with flow AGAINST you n20
-$227, median +2.10R ran on. BASIS STAMP: days 1-29 ran without the
trail gauge; run restarted from day 30 so the desk reads it. Completed
days are preserved (resume by state.json) — no re-simulation.

### ENGINE-BLAME FEEDBACK LOOP [ANGUS asked "is it taking IB trades as
well" — day 29]. IT IS, BUT LOPSIDEDLY: canon 85/87 taken (passed 2%),
shelf 8/13 taken (PASSED 38%) — declining the IB model ~20x more often.
ROOT CAUSE, in the desk's own pass notes: "shelf mgmt has
underperformed us (-297 delta), avoid adding conflict." It was reading
the digest line "SHELF taken n8: you $+1,268 vs mech $+1,885
(management delta -$617)" as EVIDENCE AGAINST THE ENGINE — but the IB
model earned +$1,885 mechanically on those trades; the -$617 measures
the DESK'S OWN handling. It was blaming the strategy for its own
management error and then starving the strategy of trades, a
self-reinforcing loop (fewer shelf trades -> thinner record -> more
reason to skip) that would have quietly hollowed out leg A over 254
days. FIX: digest now separates "the ENGINE earned $X — the strategy's
own record, not in question" from "YOUR HANDLING: $Y — this number is
about YOU", plus an explicit rule that a negative handling number means
manage differently, NOT stop taking that engine. Also note 8/8 shelf
trades taken were BASE tier (no CONFIRMED yet — sample, ~26% base rate).
BASIS STAMP: days 1-29 ran on the old engine-split wording; resumed
from day 30 (completed days preserved). Watch: does shelf pass-rate
fall toward canon's after day 30?

### SAMPLE DISCIPLINE — CHARTER v1.4 [ANGUS, the deeper diagnosis]
He reframed the engine-blame finding as the general disease: "it takes
what a dozen trades and draws the conclusion, thats way too
inconclusive to draw conclusions around... it should be trading like
that for the first couple months minimum and using the journal as
DOCUMENTATION rather than RULING, just like i wouldnt take 5 trades,
see one part underperform and just burn it." RULED INTO THE CHARTER:
(a) new section "Your journal is a logbook, not a verdict" — both
engines were certified on hundreds of trades; the desk's own record is
a handful and cannot rule on a strategy or even on its own handling at
that size; trade the book and document in the early months. (b) A pass
must be justified by what is IN FRONT OF IT (flow against, conflicting
position, session read) — NEVER by a thin or red logbook on that
engine. (c) Digest now stamps every per-engine handling number with its
n and marks it "LOGBOOK ONLY" under SAMPLE_FLOOR=40 of the desk's own
trades on that engine. He also settled the entry-origination question:
self-originated trades outside both rulebooks are NOT wanted ("outside
of our criteria it probably wont find any other trades... more so i
think about cutting losers entirely if it can spot them out early") —
participation discretion stays pass/take only, and he is satisfied the
early-cut behaviour already covers his real interest. BASIS STAMP:
days 1-29 pre-v1.4; resumed day 30. SUPERSEDED: full clean restart from
day 1 on v1.4 (those 29 days archived as live_desk1_v13_29days — their
journal fed forward into every later block, so mixing calibrations
would have made the learning curve unreadable).

### FADE-MECHANICS GAP — CHARTER v1.5 [overnight, day 26 of the v1.4 run]
v1.4 fixed the REASONING (zero engine-blame language left in the pass
notes) but the BEHAVIOUR persisted: canon passed 1%, SHELF passed 50%
(6 of 12), and those shelf passes cost $977 net (4 forfeited winners
+$1,416, 2 dodged losers -$439). Root cause is deeper and is a genuine
briefing gap, not agent error: EVERY shelf pass cites one-sided flow
against the fade — "cvd15m -1119, opposed 4/5, against new long entry",
"opposed 5/5, heavy sustained sell momentum into entry — looks like
breakout not fade". But the IB Shelf Fade is MEAN REVERSION: it only
fires when price has driven into the range extreme, so flow is ALWAYS
one-sided against it at entry. The certified conviction score proves
the point — ecvd < 0 (session CVD signed AGAINST the trade) is a
CONFIRMING flag worth a point toward CONFIRMED tier, i.e. the spec
treats stretched flow as evidence FOR the fade while the desk was
reading it as a veto. A heuristic calibrated for continuation applied
to a reversion setup; left alone it would have declined ~half of leg A
across the span and produced the false conclusion "the desk doesn't
like the IB model". FIX (charter v1.5): brief the fade mechanics
explicitly — one-sided flow into the extreme IS the setup, the spec's
own score counts it as confirmation, and if it were a veto the setup
could not carry a 65% OOF win rate; what separates a fade from a failed
fade is the TURN at the touch (touch-minute delta flipping toward the
trade — the other confirming flag), absorption, the extreme holding.
Judge the turn, not the drift. NO RESTART NEEDED: the charter is passed
as --system-prompt-file on every CLI call, so it takes effect on the
next turn. BASIS STAMP: days 1-26 of this run were traded on v1.4;
day 27+ on v1.5. Watch the shelf pass rate from here.

### SHELF-TEMPO GAP — CHARTER v1.6 [ANGUS, day 80: "its just a bit
confused on how to manage the IB setups rather than canon"]
HIS READ CONFIRMED EXACTLY, and the mechanism is now pinned. Engine
split at day 80: CANON management +$1,682 over 261 trades (genuinely
additive); SHELF management -$1,313 over 26. DECOMPOSITION: the 20
untouched shelf trades are EXACTLY $0 (anchored) — 100% of the drag
comes from the 7 it touched. Exit-reason split: band exits n15 $0,
agent stops n9 -$765, agent exits n3 -$548.
THE MECHANISM — TEMPO MISMATCH: shelf median hold 2 min, 81% resolve
within 3 min, median minute-of-MFE t+0 (it peaks INSTANTLY); canon
median hold 4 min, 48% within 3 min, MFE t+1. Five of the seven touched
shelf trades peaked at t+0/t+1 and were stopped or exited by t+2-3,
each costing $217-345. The desk's own debriefs name it: "MFE +2.03R at
t+0, never went red (MAE -0.22R). I trailed the stop tight and got
stopped at +0.40R instead of letting the band target"; "MFE +1.62R
instantly then hard reversal... I tightened stop to -0.5R fearing
further bleed, got stopped -0.62R". It is applying CANON-TEMPO
management (trail, react to flow wobble, protect) to a trade that is
already at its best price by the time the first management turn fires.
FIX (charter v1.6): brief the STRUCTURAL tempo, derived from the spec
itself and NOT from fit statistics (no outcome leakage) — a near
developing-band target plus a t+10 scratch both say the position
resolves in minutes and the plan is built to complete inside that
window; therefore the burden of proof for touching a shelf position in
its first minutes is HIGH, an early flow wobble is the ordinary texture
of a fade rather than new information, and doing nothing is an active
correct decision on this engine far more often than on the canon.
NO RESTART (charter is read per CLI call). BASIS STAMP: days 1-80 on
v1.5; day 81+ on v1.6. Watch: does shelf management delta stop
deteriorating, and does the touched-shelf rate fall from 26%?

### CANON CONVICTION SIZING WAS NOT APPLIED [ANGUS caught it, day 94]
"you're not doing the conviction based sizing shit we built for the
canon? please tell me u are." WE WERE NOT. The canon book carries TWO
size-ish columns and the harness used the wrong one: `size_engine`
(1.0/0.5 — the de-risk half-size flag) instead of `tier` (0.5x / 1.0x /
1.5x — the shipped CONVICTION multiplier, spread 138/267/358 across the
fit-span signals). `tier` is not inside dollars_1lot; it is applied
downstream by the funded shell, so the live-sim ran the canon FLAT —
a high-conviction trade weighted identically to a reduced one. The
shelf's own conviction tiers ($200 BASE / $300 CONFIRMED) WERE wired,
which is what made the omission easy to miss.
MATERIALITY: re-grading the 94 completed days with tier weighting FLIPS
THE HEADLINE — flat: agent $+47,301 vs machine $+47,921 (-$619);
tier-weighted: agent $+55,825 vs machine $+55,480 (+$345). (Approximate:
92 of 337 canon trades did not rejoin cleanly and defaulted to 1.0x.)
FIX: tier_mult carried on every canon signal; mech_dollars and the
agent's settle both scale by it; tier stored on the trade row; and per
§5.11-10(c) the desk is now TOLD the conviction on each signal ("HIGH
conviction 1.5x size" / "standard 1.0x" / "REDUCED 0.5x") so it can
weight its care accordingly. Passive==B0 re-validated to the cent.
NOTE THIS IS §5.11-10 FAILING ON ITS OWN AUTHOR: the law requires
briefing the agent on the strategy's DEFAULT MANAGEMENT IN FULL, and
sizing is part of that. The audit hook in the law is amended: the
spec-vs-strategy diff must explicitly include SIZING, not just entry,
exit and management rules.

### CONVICTION SIZING CORRECTED TO SPEC — RESTART #4 [ANGUS, day 94]
His spec, stated: "$160 base for the canon, with multiples of 0.5, 1,
1.5 and 2." The harness had NONE of it — it used `size_engine` (the
1.0/0.5 de-risk flag), so every canon trade carried identical weight
and the desk was never told which setups the book was leaning on.
FULL RULE RECOVERED from funded_book.py:176 — multiplier = the book's
`tier` column (0.5 / 1.0 / 1.5, gold-score derived) EXCEPT the FIRST
elite signal of each day, which takes 2.0 (subsequent elites fall back
to their base tier). Risk $ = 160 x multiplier -> $80 / $160 / $240 /
$320. Fit-span spread: 137 / 255 / 318 / 53 signals.
IMPLEMENTATION: canon dollars re-based from engine 1-lot realised
dollars to R x (160 x multiplier), putting it on the same footing as
the shelf (R x tier dollars). Both baselines and the agent settlement
scale identically; passive==B0 re-validated to the cent. Per
§5.11-10(c) the desk is now TOLD the conviction on every canon signal
("ELITE conviction 2x — $320 risk" etc). EXCLUDED deliberately, and on
the record: the funded shell's drawdown-state effects (ramp, soft
de-risk at -35%, daily budget) — this sim is constant-risk by design so
the measurement isolates decisions from account state; running the
final decision stream back through the funded shell is a separate
downstream exercise.
MATERIALITY: full-span B0 at correct conviction sizing = $+105,547.
The 94 completed days were on a different dollar basis entirely and
are VOID — archived runs/_archive/live_desk1_flatsizing_94days. This
also changes DECISIONS going forward, not just accounting: the desk can
now see that a signal is a 2x elite versus a 0.5x reduced trade.
RESTART #4, clean from 2025-06-02.

### IB MANAGEMENT POST-MORTEM + CHARTER v1.7 [ANGUS asked for the
diagnosis before the rerun; ruled NO HINDSIGHT in the fix]
EVIDENCE: 41 shelf trades pooled across the two archived runs (36
unique). Shelf sizing was ALWAYS correct at $200/$300, so this evidence
is untainted by the canon sizing bug. Untouched 28 -> exactly $0
(perfect machine replication). Touched 13 -> -$1,930. Only 2 of 13
interventions helped. Machine WR 78% vs desk 71%.
THE REFLEX, in the desk's own words: "S4 short reversed hard from
+1.85R peak to -0.22R... cutting before full -1R stop, setup looks
[failed]" (machine +1.41R); "Gave back peak +1.62 to -0.32... tighten
stop to cap further round-trip risk" (machine +1.02R). It reads THE
GIVE-BACK FROM AN INSTANT SPIKE AS PROOF THE SETUP FAILED. Note the
same day's ENTRY note was textbook v1.5 — "delta/cvd flipping negative
at entry = confirming turn signal, not a reason to fade the fade" — so
v1.5 fixed entry reasoning while the MANAGEMENT reflex survived intact.
WHY THE REFLEX IS WRONG (measured, FOR OUR RECORD ONLY — deliberately
NOT given to the desk): base rate 75% win / +1.17R median. Heat taken
by t+2: >=0.25R -> 83% win; >=0.35R -> 75%; >=0.50R -> 69%; >=0.75R ->
50% (n8, median -0.07R). So early heat carries essentially no signal
until ~0.75R, by which point the -1R stop is already handling it. And
the spike it kept protecting is if anything a mild NEGATIVE: MFE >=1.5R
by t+1 wins 65% vs the 75% base rate, and machine LOSERS have a HIGHER
median MFE (+1.70R) than winners (+1.25R) — they spike hardest then
fail. Median-split on heat separates almost nothing (72% vs 78%).
FIX (charter v1.7) — SPEC-DERIVED ONLY, per his ruling "this is
hindsight so we cant do that, its unfair": the stop is an eighth of the
IB, deliberately tight against the volatility of a range extreme, so
the position is BUILT to take heat inside its own plan; a round-trip
off an early high-water mark is what a fade looks like while the level
is fought over, not the setup breaking; the -1R stop and the t+10
scratch ARE the protection, and stacking a third tighter layer does not
reduce risk, it converts band-reaching trades into scratches — and does
so precisely on the trades that moved fastest in your favour. No
statistics, no outcome data, nothing the desk could not derive from its
own rulebook.

### MONTHLY CHAINING [ANGUS: "go month on month... i want it to be done
quicker"]. RULED. But the batch size was never the bottleneck — the
WORKER POOL was. Wall clock = waves, and a wave is min(batch, WORKERS)
days. Monthly on the old 10-worker pool would have been SLOWER (39
ragged waves ~12h vs the fortnight's 26 ~8h). Largest month on the span
is 22 trading days, so WORKERS 10 -> 22: every calendar month now runs
in ONE wave, 14 waves total (~4h) — half the fortnightly setup and the
outcome he actually wanted. Charter v1.7 tells the desk its book rolls
MONTHLY; dashboard deviation-rate now buckets by calendar month.
