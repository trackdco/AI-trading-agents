# NQ Backtesting Engine (Feb–Jul 2026)

A clean, config-toggled backtester for the NQ mechanical strategy. It tests the exact
strategy specified: session-anchored VWAP + SD bands, Bollinger(20,2), volume profile
(POC/VAH/VAL), fib, order blocks, rejection candles, Keltner volatility bands, liquidity
levels, mechanical HTF bias, and a true-aggressor **CVD** confirmation layer — across
Setups A / B / B2, four CVD modes, three confluence thresholds, and several target modes.

**Every number reported is in NQ points, with per-micro dollars (MNQ, $2/pt).** There is
**no RSI** anywhere. There is **no lookahead** anywhere.

## Layers

```
config.yaml   every rule the user set is a toggle here — nothing tunable is hard-coded
data.py       load 1m bars + true footprint; session-anchored 1-min CVD
indicators.py VWAP+bands, Bollinger, volume profile, ATR/Keltner, pivots, rejection  (proven math vendored)
signals.py    build no-lookahead context; detect Setups A/B/B2 with full confluence count
cvd.py        session CVD, per-candle delta%, absorption/exhaustion divergence, initiative, modes a–d
engine.py     execution & risk: entries, 70pt hard stop, sizing tiers, targets, one-at-a-time
report.py     all breakdowns, monthly split, CVD-mode table, equity curve
run.py        orchestrates the grid (TF × CVD-mode × min-confluence × target) + reports
```

Run: `python -m backtester.run` (full grid + reports) or `python -m backtester.run --smoke`.

## Data

* **1-min bars:** `nq_1m_feb_jul2026.parquet` — 161,525 rows, 2026-02-01 → 2026-07-15.
* **CVD:** true aggressor-side footprint `footprint_*2026.parquet` (12.6M rows,
  `side` B = aggressive **buy**, A = aggressive **sell**). **CVD is computed properly, not
  tick-rule approximated.**
* Paths are set in `config.yaml → data`. The raw parquet is gitignored (too big to commit)
  and lives in the sibling worktree; repoint `data.bars_1m` / `data.cvd_glob` to relocate.

### CVD sign (landmine — read this)
Per-minute delta = `vol(B) − vol(A)`, computed fresh from the raw footprint. This sign is
**correct** (a buy-dominated minute is positive). The repo's *legacy* `load_cvd_delta()`
returns the **negative** of this; that helper is **not** used here. If you ever swap in that
helper you must negate it, or every CVD gate selects the losing side.

## Assumptions & documented choices

**No lookahead.** 1-min bars are START-labeled (a bar stamped T closes at T+1min).
Resampled 3m/5m bars are CLOSE-labeled (`closed='left', label='right'`): a 5m bar stamped
09:35 aggregates 09:30–09:34 and is actionable at 09:35. Every "as-of ts" reader uses only
bars fully closed at ts. Signals fire only on **closed candles** — no anticipation entries.
Pivots/structure are treated as known only after their `swing_lookback` confirmation delay.

**Instrument.** NQ; tick 0.25; full contract $20/pt; **1 micro (MNQ) = $2/pt; 10 micros =
1 contract.** P/L is reported per-micro-sizing dollars and in points.

**Timeframes.** Signal TFs **3m and 5m are tested separately and reported per TF.** CVD is
1-min, session-anchored. HTF bias uses 15m structure + 1H VWAP.

**Session-anchored VWAP.** = the canon daily VWAP, anchored at the **CME session open 18:00
ET**, TradingView volume-weighted SD bands (1/2/3σ). (This is the "same VWAP as the canon
strategy". Configurable via `indicators.vwap.anchor`.)

**Bollinger Bands (20, 2σ), incl. midline** — a core confirmation, kept. Population stdev
(ddof=0), TradingView parity.

**Volume profile.** POC/VAH/VAL, 0.25-pt bins, each bar's volume spread uniformly across the
bins its range touches; value area expands greedily from POC to 70%. Developing, snapshotted
from bars closed at ts.

**Fib.** 50% of the most recent *significant* swing on the entry TF (a swing must span
≥ `fib.swing_min_points`), from confirmed pivots only.

**Order blocks.** Last opposing candle before an impulse ≥ `order_block.impulse_min_points`;
we track the **50%** of the block (`ob_mid`). The far edge is the structural stop reference.

**Rejection candles.** Wick pierces a level and the candle closes back on the trade side,
wick ≥ `rejection.wick_frac` of range. A "large" rejection (range ≥ `large_range_points`)
also contributes its **50%** as a level.

**Volatility bands (documented choice).** **Keltner Channels** = EMA(20) ± 2·ATR(10) — a
volatility envelope distinct from Bollinger (which is stdev-based). Config
`indicators.volatility_bands`.

**Liquidity levels.** Prior-session High/Low as draw-of-liquidity targets and sweep context
(equal-highs/lows tolerance and untested-swing scaffolding are in config for extension).

**HTF bias (mechanical, exact).**
`bias = LONG  if close > 1H session-VWAP AND 15m structure is HH & HL`;
`bias = SHORT if close < 1H session-VWAP AND 15m structure is LH & LL`;
`NEUTRAL otherwise`. Structure = last two **confirmed** 15m swing highs and lows
(HH = higher high, HL = higher low, etc.). **Bias is mandatory** — a neutral bias means
**no trade**.

**CVD confirmation layer (short-term, at the level — never session-wide).**
* *Initiative trigger*: entry-candle `delta% = Σdelta / Σtotal × 100`; long needs
  ≥ +10%, short ≤ −10% (`cvd.initiative_delta_pct`).
* *Absorption / lack-of-participation divergence*: over the last ~2×`swing_lookback_min`
  minutes, price makes a new extreme against the trade while session-CVD fails to confirm it
  (CVD holds/reverses). Captures both absorption (CVD pushes, price holds) and exhaustion
  (price extends, CVD doesn't).
* **Modes tested:** `a` none · `b` divergence required · `c` initiative required · `d` both.

**Setups.**
* **A — Reversal:** rejection of a strong level (VWAP band / VAH / VAL / POC), wick + close
  back; entry off the rejection close. Alt path: closed outside a Bollinger band then
  reclaimed inside (`bb_reclaim`). Counter-impulse but only **with** HTF bias.
* **B — Continuation:** rejection off a midline (BB basis / VWAP / POC) in the HTF-bias
  direction. **Setup-B shorts require an extra confirm** (5m agreement OR CVD divergence) and
  are reported separately.
* **B2 — POC limit:** resting limit at POC in the HTF-bias direction, taken only where a
  prior reaction at POC exists; fills on touch.

**Confluence.** Factors tracked & counted: htf_bias, rejection_candle, bb_midline, vwap, poc,
ob_mid_50, fib_50, bb_reclaim, liquidity, rejection_50, volatility_band, cvd_divergence,
initiative_delta. Two levels are "confluent" within `confluence.proximity_points` (8pt).
**Minimum confluence is tested at 3 vs 4 vs 5.** Hard rules enforced: HTF bias mandatory;
closed candles only; Setup-B-short extra confirm.

**Risk (never violated).**
* **Hard max stop 70pt** — if the logical stop (beyond the rejection wick / OB extreme) is
  wider than 70pt, the trade is **skipped**. No exceptions.
* **Sizing:** 0–40pt stop → 1 contract (10 micros); 41–70pt → 0.5 contract (5 micros).
* One trade at a time; no re-entry at the same level after a stop-out in the same session.

**Targets (tested).** `fixed80 / fixed100 / fixed120 / dynamic / trail80`. Default band
80–120pt; dynamic targets the nearest opposing structural level clamped to [80,120];
**liquidity override** retargets to a liquidity draw if one is within reach (even < 80pt);
trail80 starts trailing 30pt behind the extreme after +80pt.

**Costs (realistic).** 1 tick slippage per side (adverse) + commission per micro per side
(`costs.commission_per_micro`, round-turn applied in code).

**Intrabar assumption.** Within a 1-min bar, **stop is checked before target** (conservative
worst-case ordering) — realised win rates are therefore not optimistic.

## Reporting

`report.py` / `run.py` produce: overall + by setup / direction / TF / CVD-mode / entry-time
bucket; per breakdown — trades, win rate, avg win/loss (pts + $), profit factor, expectancy,
max drawdown, max consecutive losses, planned-vs-realised RR, stop-size distribution + which
sizing tier fired, liquidity-override frequency; a monthly split; a CVD-mode a–d comparison
table; and an equity-curve chart (`out/equity_headline.png`). The full config grid is written
to `out/summary_grid.csv`, headline trades to `out/headline_trades.csv`.

## Caveat on in-sample

2026 Feb–Jul is **in-sample by design** (that's the data we have). July is partial
(→ 2026-07-15) and thin — treat July separately. Confluence thresholds / target modes are
presented as a grid, not cherry-picked; prefer configs that hold up across months, not the
single highest-PF cell.
