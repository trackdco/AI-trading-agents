# THE CANON (Angus 25-Jul ruling: default system — do not divert unless explicitly asked)

`scripts/canon_mechanical.py` → `output/canon_book.parquet`. Both books, every day, no book
choosing, no day forecasting. Validated out-of-fit: **2025 +$14,349 / 2026 +$30,343**,
maxDD $5.6k/$3.0k, ~2 trades/day, WR 38%/43%.

| layer | rule |
|---|---|
| 0 hard gates | stop ≥ 7 pts (pre) / post-open floor 10 (golden, after 09:40) |
| 1 validation | 5 checks at fill: W wall-behind absent · F fill-bar delta confirms · T not fighting 15-min tape · G VWAP-side geometry aligned · C window-correct CVD (PM→pre, LON→gold) |
| 2 sizing | score ≤2 → 0 · 3 → 0.5 · 4 → 1.0 · 5 → 1.5 |
| 3 governor | trailing-15 confirmed-trade WR < 0.35 → all sizes ×0.5 (results-based, no forecast) |

## Bleed-day diagnosis (25 Jul, canon book: 63 bleed days −$37.5k vs 75 winner days +$87.2k)

**Composition is NOT the problem.** Bleed and winner days are near-identical in score mix
(mean 3.7 both), %score≥4 (54 vs 57), window/setup mix, trades/day. Two modest tilts: bleed
days have fewer wall-behind-absent fills (43% vs 56%) and lean short (44% long vs 54%).

**The edge is binary by day.** On winner days the checks separate hugely (F 76% vs 56%,
C 78 vs 57, G 74 vs 42). On bleed days ALL five checks stop separating (W 8 vs 12, F 8 vs 13)
— confirmed trades lose at the same ~90% rate as everything else. Bleed days are a regime
where the edge is wholly offline, not days where bad trades slipped through.

**What bleed days share ex ante (modest, directional):** half the pre-market conviction
(|cvd_PM| median 315 vs 538), fresher overnight extreme (122 vs 184 min), stalling CVD accel,
choppier pre-market path — the same verified gold-red family, still too weak to hard-gate.

**Jul-Sep 2025 specifically = dead tape:** overnight range −40% (median 107 vs 177 pts),
volume −19%. In that tape the CVD checks degrade to noise (C inverts: on 28% vs off 32%) but
the **heatmap check keeps working** (W: 42% vs 23% WR, +$11 vs −$135/t) — book structure
survives thin tape; flow signals don't.

**Circuit-breaker candidates (tested, NOT shipped — canon unchanged):** stop-after-2-consecutive
-losses hurts (−$2.1k/−$2.4k). Day-stop at −$400 helps mildly (+$1.1k 2025 / +$0.1k 2026,
Jul-Sep −$4.6k → −$4.1k) — candidate for the 2023/24 holdout, not canon.
