# TASK FOR BRAKE — Order-book data pull (Angus directive, 18 Jul 2026)

**Why (Angus, pass 20):** MIG LiquidityEdge (absorption/exhaustion heat map, A–C graded
levels) turns out to be a CORE confluence in his real trading ("tapped a MIG A level +
closed through the VWAP band → market order"). The mechanical system excluded it (§2) and
1-minute OHLCV cannot reconstruct it — resting/absorbed volume needs book data. Angus has
committed to buying it: *"the only way we can really cross-check it is actually using
order book data… the payoff is there."*

**The structural anchor (Angus):** MIG levels form at ABSORPTION CANDLES — e.g. the
rejection block of a big bullish candle with a big bottom wick (sellers absorbed). The
engine already detects these candles as triggers; the book data lets us GRADE the zones
(how much volume was absorbed / rests there) and persist them as levels.

## UPDATE (18 Jul, pass 23) — Angus posted the MIG product listing; buy LESS, not more

The listing self-describes as **"MicroDOM-style liquidity & volume blocks for
TradingView"** (by Mohs Mayfair, $48.99/mo). TradingView Pine indicators have NO access
to real order-book depth — Pine sees price/volume (and lower-TF intrabar bars) only. So
MIG's boxes, B%/S% dominance tags, sweeps and "displacement confirmations" are all
RECONSTRUCTED from traded price/volume. Its "depth mapping / millisecond order flow"
copy is marketing, not a data capability the indicator can have.

**Therefore: buy the `trades` schema ONLY. Do NOT buy `mbp-10`.** True resting-depth
data cannot be needed to replicate an indicator that never saw resting depth. Trades
ticks (with aggressor-side flag) are strictly better raw material than MIG's own input.
If we ever want true depth as an UPGRADE beyond MIG, a ~2-week mbp-10 sample later is
the cheap way to test whether it adds anything.

## What to pull (Databento, GLBX.MDP3, same NQ outrights as the price pull)

**`trades` schema (tick-by-tick), 2026-02-01 → present.** Enables: volume-at-price
footprints per bar, delta (aggressor side via side flag), absorption detection
(heavy volume + no progress at a price), sweep detection, and exact wick-volume
grading — everything MIG approximates, from better inputs.

Practical notes:
- **Check the metered cost preview before confirming.** Databento shows the price of
  the exact query before you pay. If it looks way too high, the symbol filter is wrong
  (whole-CME pull instead of NQ outrights) — fix the filter, don't pay it.
- Same instrument filtering as before (outrights only, front-month by volume — reuse
  `to_continuous_front_month`'s roll logic for alignment with the 1m series).

## Size problem ("it's gigs, we can't upload it") — solved by never uploading raw

Raw ticks never touch GitHub. Committed output = a per-1m-bar FOOTPRINT parquet
(buy_vol/sell_vol per price level per bar): ~50–100× smaller than raw ticks, roughly
100–200 MB for Feb→present — commits fine next to the existing 1m dataset. The
level-memory layer, delta, absorption grading all compute from that file.

Two delivery paths, in order of preference:
1. **API key → engine session pulls directly.** Give the engine lane a Databento API
   key as an environment secret (NEVER committed). It downloads month-by-month inside
   the session: pull month → aggregate to footprint → delete raw → next month. Raw
   data exists only transiently on session disk.
2. **Brake pulls locally + runs the condenser script.** If the session's network
   policy blocks the Databento API, the engine lane writes the aggregation script;
   Brake runs it locally and uploads only the derived footprint parquet.

## What the engine lane will build on top (sequenced)

1. **Level-memory layer** (buildable NOW from OHLCV, upgraded by tick data): persist
   detected absorption candles (high-volume rejection blocks) as decaying levels; entry
   confluence = "price returns to a remembered zone" + the existing VWAP/BB machinery.
2. **Grading** (needs the data above): A–C by absorbed volume / resting size, calibrated
   against the MIG levels visible in Angus's live screenshots (pending upload).
3. Cross-check vs his live funded executions (no-hindsight; his trades = ground truth).

— Claude Code (engine lane), on Angus's direction. Ping the tracker when data lands.
