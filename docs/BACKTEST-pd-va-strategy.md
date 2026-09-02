# BACKTEST — PD VAH/VAL break-retest (his flight-note strategy)

His spec (2026-09-02): 3m close through prior-day VAH/VAL → limit the
retest, stop beyond the close-through candle (prior candle too if the
close-through candle's open is <5pt from the level), 5pt minimum stop,
fixed-R targets, Asia+London the strategy with full-day measured anyway.
His hand-test: one month in replay, ~800–1000pt at 1.5R, 50–75% WR day on
day, "0 trades or 5+" frequency, "probably won't work in NY."

Simulator: `scripts/pd_va_backtest.py` (interpretation decisions in its
docstring). Report: `scripts/pd_va_report.py`. Trades:
`output/analysis/pd_va_trades{,_through}.jsonl.gz`. 908 session-days,
2023-01-03 → 2026-07-14. No lookahead: prior-day levels, closed candles,
forward-only fills/exits, stop-before-target inside any single bar.

## 1. The strategy is REAL — and thin

Asia+London, touch fills, no costs (net R over 43 months):

| target | any-tick depth | ≥3pt depth |
|---|---|---|
| 1.0R | 56.0% WR, **+370R** | 59.0% WR, +389R |
| 1.5R | 43.1% WR, +207R | 44.5% WR, +224R |
| 2.0R | 35.6% WR, +168R | 36.3% WR, +168R |
| 2.5R | 30.2% WR, +133R | 31.1% WR, +163R |
| 3.0R | 26.3% WR, +120R | 27.0% WR, +147R |

Positive at every depth × target — the level genuinely means something.
Per-trade the edge is small: 56% at 1R against a 50% breakeven; 43% at
1.5R against 40%. Roughly +0.08–0.12R/trade before frictions, harvested
by volume (~3 trades/day). Median stop 8.8pt (20% of trades sit at the
5pt floor), median 2min from signal to fill, median 7min in the trade —
this is a scalping cadence, which is why frictions decide everything:

## 2. The two honesty haircuts

**Fill adverse-selection.** Touch fills credit every bounce-to-the-tick
winner a real resting limit might miss. Requiring price to trade one tick
THROUGH the level (guaranteed fill): 1R any-tick drops 56.0%→53.7% WR,
+370R→+222R. The classic limit-order tax is ~40% of the raw edge.

**Costs.** Per round-trip, subtracted in R against each trade's own stop:

| config (AL) | raw | fill-through | through + 0.5pt | through + 1.0pt |
|---|---:|---:|---:|---:|
| any-tick, 1.0R | +370R | +222R | **+36R** | −151R |
| any-tick, 1.5R | +207R | +102R | −59R | −219R |
| **≥3pt, 1.0R** | +389R | +277R | **+140R** | +2R |
| ≥3pt, 1.5R | +224R | +124R | −2R | −128R |

The only configuration that survives honest fills plus realistic costs is
**≥3pt close-through, 1R target**: ~+140R/43mo ≈ +3.3R/month, yearly
2023 ≈ 0 → 2024 +33R → 2025 +48R → 2026 +60R (improving, positive 3/4
years). Every 1.5R+ configuration is negative after the double haircut.

## 3. His hand-test month: found, and it was the best of 43

June 2026 (AL, any-tick): **1.5R → +661pt, 53.9% WR; 1R → +704pt, 67%
WR**. His claimed ~800pt / 50–75% WR is this month almost exactly — and
it is the **best month of 43** (next best +349pt; median month +59 to
+76pt; positive 30/43; worst −162pt). Under fill-through it still prints
+717pt at 1.5R — his eye-test was honest, the month was simply a 10× 
outlier, and it is also the tape he already knew (jl1/narration weeks
live in June 2026). One month of replay sampled the peak of 3.5 years.

## 4. Scoring the rest of the note's claims

- **"50–75% WR day on day" (1.5R):** median day-WR 44%; only 49% of days
  reach 50%. Not replicated at 1.5R. At 1R the aggregate is 54–59%.
- **"5 trades a day even on a bad day":** mean 3.0/day AL; 5+ on 27% of
  days; ZERO trades on 31% of days. Overstated.
- **"0 or 5+" bimodality:** half-true — zeros are common (282/908) but the
  1–4 middle is fatter than the note expects (385/908).
- **"Pump/dump prior day → 0 trades":** directionally right, weak — 
  zero-trade days 24% in the smallest PD-range quartile vs 35% in the
  largest.
- **"Won't work in NY":** WRONG in R-space. NY alone at 1R: 55.4% WR,
  +283R — the same edge. NY's close-through candles are huge (stops run
  30–80pt), so in POINTS it feels wild; in R, with size scaled down, it
  performs like Asia/London. Consistent with the substrate finding that
  R-quality is flat across vol regimes. (Asia is the best window:
  57.8% / +0.50R/day at 1R, vs London 54.5% / +0.32.)

## 5. Verdict against his own acceptance bar

His mechanical bar: **≥50% WR to target in the 1.5–2.5R band**. Measured:
41.5–44.5% at 1.5R (fills either way), ~35% at 2R. **The strategy fails
his bar in his band.** It holds ≥50% only at 1R, outside the band he
declared. Either the bar moves (accept a 1R strategy) or the strategy
needs a selection layer on top — which is exactly the agent-judgement
architecture already ruled.

## 6. Caveats and the one check only he can run

- The certified `volume_profile` carries a documented residual vs
  TradingView's own rows (worst case ~30pt on wide profiles). His
  hand-test used chart-marked levels; ours are computed. The June result
  (+661 vs his ~800) suggests the residual is not fatal, but the clean
  check is his: screenshot TV's PD VAH/VAL for any week, diff against
  `output/analysis/pd_va_days.json`.
- No order-expiry rule in the note: pendings here rest until the next
  signal replaces them or 16:00 (median fill comes in 2min; P90 44min).
- Same-bar stop+target ambiguity resolved AS LOSS throughout
  (~1–3% of trades), and fill-bar stop-outs are taken — both conservative.
- One month of hand-testing cannot distinguish 43-month regimes; this is
  not a criticism of the eye, it is why the corpus exists.

## OPEN (his word needed)

1. Which month was the hand-test? (If June 2026: confirmed found.)
2. Does a 1R-target, ≥3pt-depth version interest him despite sitting
   below his 1.5R band, or does this fold into the v2/Pat grading queue
   as a condition family (PD-VA break-retest) for the selection layer?
