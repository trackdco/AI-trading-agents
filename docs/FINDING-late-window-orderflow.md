# FINDING — 10:15–10:30: same wall physics as golden, INVERTED flow physics

**2026-07-26, Angus's ask:** *"run the order flow variables that we did for the golden window
[on 10:15–10:30]. find that subset that produces the majority of the profit, cut the losers."*
Reproduce: `python -m scripts.late_a_orderflow` (matrix: `output/late_a_flow_matrix.parquet`,
292 trades, 2025-07→2026-07, canonical `src/canon/features.py` definitions, depth on 260/292).

## Survivors of the both-years rule (direction agrees 2025 AND 2026, ≥$60/t gap, n≥12/cell)

| check | on $/t | off $/t | gap | verdict |
|---|---|---|---|---|
| **W no-wall-behind** | +$155 (38% win) | −$132 (21%) | **+$288** | GOOD — same as golden |
| **D wall-ahead** | +$83 (34%) | −$167 (19%) | **+$249** | GOOD — same as golden |
| **WALLSZ ahead ≥7** | +$101 (37%) | −$114 (21%) | **+$214** | GOOD — same as golden |
| **d5_conf (flow-with, 5m)** | −$71 | +$47 | **−$118** | **BAD — INVERTED vs golden** |
| **C op_sofar_conf (open CVD with)** | −$98 | +$11 | **−$108** | **BAD — INVERTED** |
| **d30_conf (flow-with, 30m)** | −$74 | +$6 | **−$80** | **BAD — INVERTED** |

Non-survivors (fail both-years agreement): F fill_delta_conf, BIGFD, Tc d15, G vwapd, IMB,
pm_sofar_conf, PAQ, pathpos, kind. Baseline: 292t, −$11,748, 27% win, −51.8R.

**Reading:** the DEPTH checks transfer intact — walls are alpha at 10:15–10:30 exactly as in
golden. The CVD-confirmation family flips sign: by this hour the open drive is spent, so
entering WITH recent flow is chasing a move about to mean-revert. The paying trade is the
**flow-exhaustion fade into book structure** — golden's wall checks plus the OPPOSITE of
golden's flow checks. Extending the golden checklist verbatim would keep the chasers and cut
the fades: exactly wrong. (Angus's "setup types are inherently different," as an hour effect.)

## The subset (exploratory — NOT adopted)

`op_sofar_conf=OFF AND wall-ahead=ON AND d30_conf=OFF`:

| | kept 41t | cut 251t |
|---|---|---|
| P&L (1-mini) | **+$10,505** | −$22,252 |
| win | 41% | 25% |
| @ canon floor | +12.4R = +$2,487 | |
| months green | 8/11 | |
| by year | 2025 +$4,716 (45%) · 2026 +$5,789 (38%) | |

## Caveats — read before believing
1. Each component survives both years independently, but the 3-rule CONJUNCTION was chosen
   greedily in-sample on n=292. Needs the freeze-and-OOS treatment the golden checks got.
2. **2026-06 is +$6,622 of the +$10,505 (63%).** Ex that month: +$3,883 over 10 months.
3. +12.4R/13mo is ~1R/month at floor — real but modest; the 1-mini figure rides wide stops.
4. Not wired into anything. Canon windows unchanged. Adoption = new signed-off book + A1/A2.

---

## ADDENDUM 2026-07-26 — the golden window is TWO regimes, and the clock gradient is real

Angus: *"break the golden window a bit... maybe we'll see specific order flow only aligns at
certain times."* Same harness, same both-years survival rule, three sub-windows
(`scripts/window_flow_split.py`, matrices in `output/golden_flow_matrix.parquet` + late-a).

### The regime gradient, one variable at a time (survivors only, $/t gap on vs off)

| check | 09:40–10:00 | 10:00–10:15 | 10:15–10:30 |
|---|---|---|---|
| W no-wall-behind | **+$532** | (flat, n.s.) | **+$288** |
| D wall-ahead | **+$557** | (−$210, n.s.) | **+$249** |
| WALLSZ ≥7 | **+$436** | (−$312, n.s.) | **+$214** |
| Tc d15_conf (flow-with 15m) | **+$318** | **+$380** | (+$21, n.s.) |
| d30_conf (flow-with 30m) | **+$263** | **−$223** | **−$80** |
| F fill_delta_conf | **−$327** | **+$294** | (−$3, n.s.) |
| C op_sofar_conf | (n.s.) | (−$369, n.s.) | **−$108** |
| G vwapd ≥ .107 | **+$74** | **+$162** | (n.s.) |

**Read as a clock:** 09:40–10:00 = *ride the drive* — 15/30-min flow WITH you is alpha and walls
define the path (the biggest gaps anywhere: +$532/+$557). 10:00–10:15 = *the drive ages* —
short flow still with you, 30-min flow now stale (d30 flips sign and survives), walls go
neutral. 10:15–10:30 = *the drive is dead* — every flow-confirmation inverts (fade regime),
walls return as fade structure. `d30_conf` alone tells the story: **+$263 → −$223 → −$80.**
The open drive has a measurable half-life of ~20 minutes past 09:40.

(The F inversion at 09:40–10:00 is coherent, not noise: limit retests fill ON the pullback
candle, whose delta opposes the trade — instantaneous delta against + medium flow with = a
retest in a drive. It flips positive at 10:00–10:15 where fills are breakout-style.)

### Per-sub-window subsets (greedy from survivors; same caveats as before)

| | 09:40–10:00 | 10:00–10:15 | 10:15–10:30 |
|---|---|---|---|
| rules | d15_conf ∧ d30_conf ∧ wall-ahead | fill_delta_conf | opCVD-off ∧ wall-ahead ∧ d30-off |
| kept | **93t** | 43t | 41t |
| P&L (1-mini / floor) | **+$40,745 / +$12,238** | +$11,224 / +$4,624 | +$10,505 / +$2,487 |
| win | 46% | 49% | 41% |
| **months green** | **11/12, worst −$368** | 7/11 | 8/11 |
| years | 25: +$26.3k · 26: +$14.4k | +$5.5k · +$5.8k | +$4.7k · +$5.8k |
| trades/month | **7.2** | 3.9 | 3.2 |
| biggest month share | 28% | — | 68% |

**The consistency ranking follows frequency exactly as the variance math predicts:** 7.2
trades/month → 11/12 green; ~3-4/month → 7-8/11. The early-golden subset is the only one with
the monthly profile Angus's objective demands, and it is not tail-driven (top month 28%).

### Notes for adoption (nothing adopted)
- These are champion-engine populations, NOT canon candidates. But the finding independently
  REVALIDATES two of the canon's gold checks (D wall-ahead, Tc d15) on a disjoint trade set —
  and shows the canon's single-checklist treatment of 09:40–10:15 blends two regimes: its
  flow checks are right for the first 20 minutes, partially inverted for the last 15.
- Adoption path: freeze the per-sub-window rules → OOS discipline (derive 2025 / test 2026 and
  the reverse) → re-derive the canon gold book with time-conditioned checks → new signed-off
  number → A1/A2 re-point. A canon change, same class as the news blackout.
- 2026-01 has no trades in any sub-window table (trigger-cache seam month).

---

## ADDENDUM 2026-07-26b — rr_floor deep-dive: the floor is right as a VETO, wrong as a TARGET-PICKER

Angus: *"rr floor should be looked at deeper."* He was right to distrust the ablation's −33R
headline — it conflated two mechanically different effects, because `rr_floor` is not a veto:
`walk_menu` picks the FIRST target level clearing the floor, so the floor also sets target
distance on every trade that trades anyway. `scripts/rr_floor_decomp.py` separates them
(golden 09:40–10:15, otherwise-canon, 13 months, per-fill diff):

| effect | rr 1.5 vs 2.0 | rr 1.0 vs 2.0 | verdict |
|---|---|---|---|
| **A. target geometry** (same fills, nearer first target) | **+37.8R** (2025 +13.2 / 2026 +24.5) | +36.3R | **the leak — robust both years** |
| **B. admission** (fills that only exist at the lower floor) | **−15.9R** (−8.7 / −7.2) | −18.7R (−8.2 / −10.5) | the veto is CORRECT both years |
| C. slot reshuffle | −1.5R | +12.9R | noise |
| **net book** | 377t +36.7R → **397t +60.1R** (win 31→36%, 8/13 green) | 411t +41.4R | **1.5 is the corner** |

Mechanism (asymmetric): of 68 shared fills whose target moved, only 40% improved — but the
improvements are round-trip saves (a winner that reached +1.5R but not +2R books the win instead
of stopping out: ~+2.5R per save) while the costs are small give-ups (−0.5R of extra reach).
Geometry gain PLATEAUS below 1.5 (+37.8 → +36.3) while admission losses grow — so 1.5 is a
mechanical corner, not a fitted sweep point.

**Interpretation:** the golden book's fixed-target exits overreach. This is the same story as
Angus's 3R+ winners (trailed, not fixed-target) vs the engine's 2.05R median winner — the exit
model, not entry admission, is where golden bleeds. NOTE: the live canon path is now MANAGED
exits (exit_manager, no fixed target), so this finding primarily indicts the BACKTEST substrate
that generated the canon universe and its dollars. Changing rr_floor there = full re-validation
(new signed-off book). Workflow adversarial verification still in flight as the independent check.

---

## ADDENDUM 2026-07-26c — management dissection: MAE, dead stop width, target optimism, and the 3-min cut at rr 1.5

Angus's three hypotheses (`scripts/mgmt_dissect.py`, corrected run — the first pass wrongly
applied the 3-min cut to trades already dead by minute 3; canon Layer-2d conditions on
alive-at-3, so does this).

**H1 — the 1.5R wins are NOT scrapes.** Winner MAE is identical at both floors (median
0.39–0.40R, ~12% ≥0.8R). The geometry saves specifically: median MAE 0.41R, 11% scrape rate —
same quality as the general winner population. 17 clean saves averaging ~1.5R, plus ONE 29.2R
outlier (6.0pt stop that slipped under the 7pt floor at fill × a sparse level menu whose first
qualifying target sat 175pt away — quarantined from all headlines).

**H3 — stops carry real dead width, but the counterfactual is hindsight.** The median winner
uses 40% of its stop; p90 ≈ 0.82. Re-measuring the same winning moves against stops at
1.25×realized-MAE gives median 1.55R → 4.62R — but realized MAE is unknowable at entry, so
this BOUNDS the prize; it is not a rule. The implementable version is a forward stop-placement
study (structure + k ticks) inside the re-derivation. Note: engine stop WIDTH ≈ Angus's
hand-log width (34pt vs ~32pt median) — his 3–6R came from FURTHER TARGETS (90–180pt vs the
engine's ~50–70pt picks), which feeds H2, not from thinner stops.

**H2 — targets leave money at BOTH floors.** Of target-hit wins, ~half run ≥1R beyond the
exit (median +0.94R post-exit extension). Combined with the round-trip saves (the 2.0 reach
turning winners into stops), fixed targets are wrong in both directions: too far to get hit
reliably, too near to capture the run. Both errors point at the exit FAMILY — partial+trail
(Angus's actual style; V8; the live exit_manager direction) — not at the floor constant.

**3-min cut (r_3≤−0.1106 & fw_3≤−13), alive-at-3 only:** the SEPARATION survives at both
floors and both years (flagged lose 85/88% at rr2.0, 79/76% at rr1.5) — but ACTING on it
flips sign: **+1.1R at rr2.0 → −7.9R at rr1.5** (it sacrifices 13 flagged winners worth
+24.5R — largely the very trades the nearer target rescues). Angus's suspicion confirmed: the
rule does not transfer across floors; Layer-2d thresholds must be RE-DERIVED jointly with any
floor change. (Caveat: champion-path population and an approximated r_3 convention — the
canon's own intrade_matrix conventions must be used for the real re-calibration.)

**Consolidated:** rr 1.5's geometry gain is now supported by two independent measurements
(per-fill decomposition +37.8R; MAE-clean saves), the admission veto at 2R stays (sub-2R-only
trades lose both years), and the correct adoption is ONE mechanical package — floor + cut
re-calibration + stop/target-family study — two-way OOS, new signed-off number, all frozen
constants per docs/RULING-mechanical-only.md. Pending: the workflow's adversarial rr verdict.

---

## ADDENDUM 2026-07-26d — the cut frontier: dead-trade detection evens out at TEN minutes

Angus: *"id like to see where the flagged loss evens out... i still think we can prevent a
lot of losers from fully losing."* Full sweep (`scripts/loser_forensics.py`): horizon
{3,5,10}min × mark {−0.05..−0.45R} × flow {off,−13,−60,−150}, both books, alive-at-h only.

**The horizon is the whole answer — the grid is monotone:**

| horizon | verdict | why |
|---|---|---|
| 3 min | NO cell survives both years (incl. the canon's own −0.11/−13) | 21–27% of underwater trades still recover; the cut kills 1-in-4 recoverers worth ~1.5R each |
| 5 min | worst of all — every cell negative | same, plus the marks are deeper |
| **10 min** | **EVERY cell positive with both-years agreement, both books** | recover rate has fallen to 15%, and flow-qualified to ~5% |

Best cells (13-month dR, exit at the +10min mark):

| book | rule | flagged | lose% | winners sacrificed | dR | 25/26 |
|---|---|---|---|---|---|---|
| rr1.5 | r_10 ≤ −0.05 & fw_10 ≤ −13 | 19 | **95%** | **1** | **+8.2R** | +4.4/+3.9 |
| rr2.0 | r_10 ≤ −0.11 & fw_10 ≤ −13 | 17 | 94% | 1 | +6.7R | +3.0/+3.6 |

**Candidate mechanical rule for the adoption package: still ≤ −0.05..−0.11R at 10 minutes
AND 10-min flow against (fw_10 ≤ −13) → exit.** ~+7–8R/13mo per book (~+$1.5k @floor),
one winner sacrificed, precision 94–95%. This REPLACES Layer-2d's 3-minute horizon, which
on this population costs money even at its home floor (+1.1R with years disagreeing at
rr2.0; −7.9R at rr1.5). Angus's instinct is confirmed with a twist: losers can be
prevented from fully losing — but the tape needs ten minutes to prove death, and acting
at three kills the quarter of underwater trades that were coming back.

Caveats: n=12–19 per cell (small; the credible part is the monotone horizon structure,
not any single cell); exit-at-mark approximation; exploratory — re-derive under
intrade_matrix's own conventions, jointly with the floor, inside the one-package ritual.

**Part B (flow while underwater)** is underpowered at per-year granularity (few cells reach
n≥10/year) but the medians agree with Part A's mechanism: at 10min, recoverers show flow
FLIPPED BACK positive (fw_10 median +271 vs −83/−103 for the dead) and heavy adverse
pressing that price ABSORBED (−356 pressing yet alive = defense), while the dead drift down
under modest pressing (no defense required). To power Part B properly, run the same
forensics on the full canon both-books universe (~970+ trades) where intrade_matrix already
has the conventions.

---

## ADDENDUM 2026-07-26e — two-way OOS: early-golden CONFIRMED, transition weak, late-a RETRACTED

`scripts/golden_deep_oos.py` — derive greedily on one year, freeze, test blind on the other:

| sub-window | derive 2025 → blind 2026 | derive 2026 → blind 2025 | verdict |
|---|---|---|---|
| **09:40–10:00** | d15∧wall-ahead → **+21.4R, 44% win, 6/6 green** | REJ-off∧d15∧d30 → +13.0R, 4/6 | **CONFIRMED** (d15 core in both) |
| 10:00–10:15 | d15 → +0.8R, 5/6 | d5∧F → +14.0R | weak-positive, thin (n=79) |
| **10:15–10:30** | → **−4.1R** | → **−16.1R** | **DEAD. The +$10.5k fade subset was in-sample fit — RETRACTED** |

The late-a retraction closes the window-extension question: no tradeable rule set transfers
across years there. (The individual wall-check survival stats stand as description; nothing
tradeable.) The 10-minute dead-trade cut is unaffected — it is an exit rule on existing
windows, not a window extension.

Splits (per-year checked): **displacement carries golden** — +13.3R (2025) / +34.2R (2026),
both years, while the engine's rejection_blocks net ~0 both years (+1.1/−4.6). This does not
contradict Angus's live retest success: his A-grade retests score 0–2 on the engine checklist,
i.e. the engine's "rejection_block" population is not his retest population. Calm-vs-war-day
split is suggestive (calm-day golden −14.5R in 2025) but YEARS DISAGREE (+3.5R on n=16 in
2026) → parked, unconfirmed.

---

## ADDENDUM 2026-07-26f — rr_floor 1.5 RETRACTED: 80% of the gain was one degenerate fill

The adversarial pass the workflow owed us, run by hand. The 2026-02-19 09:46 fill (6.0pt stop
that slipped the 7pt floor on fill improvement; sparse level menu) is the SAME entry at both
floors — at 2.0 the walk demanded a 245pt/41R target and stopped out (−1.0R); at 1.5 it picked
175pt/29R and hit (+29.2R). A coin-flip between two lottery tickets, carrying the finding:

| | with freak | ex-freak |
|---|---|---|
| shared-fill geometry gain | +37.8R | **+7.5R** (2025 +13.2 / 2026 **−5.7** — years disagree) |
| net book 1.5 vs 2.0 | +23.4R | **−6.9R** |

**rr_floor stays 2.0.** Angus's own floor rule survives its audit. Process note: the "two
independent confirmations" (decomp + dissection) shared the same sims and therefore the same
freak — measurement independence was overstated; true independence requires disjoint substrates.

SURVIVES (measured at the 2.0 floor, unaffected): the 10-minute dead-trade cut (+6.7R both
years), the post-target-extension case for the partial+trail study, the early-golden d15+wall
OOS result, and the admission finding (sub-2R-only trades lose — reinforcing the 2.0 floor).

NEW MECHANICAL GUARDS from the freak (for the package): (1) walk_menu sanity clamp — reject
targets demanding more than K·R (a 41R demand on a 6pt stop is a malfunction); (2) re-check
min_stop_points at FILL (structural 7pt floor can be slipped by fill improvement).
