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
