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

## What to pull (Databento, GLBX.MDP3, same NQ outrights as the price pull)

Priority order — get (1); add (2) if budget allows:

1. **`trades` schema (tick-by-tick), 2026-02-01 → present.** Enables: volume-at-price
   footprints per bar, delta (aggressor side via side flag), absorption detection
   (heavy volume + no progress at a price), and exact wick-volume grading. This is the
   80% solution and much smaller than depth data.
2. **`mbp-10` (market-by-price, 10 levels), same range** — true RESTING liquidity
   (the heat-map dimension: where size sits before it trades). Biggest files; if cost
   or size is a concern, a Feb–Mar sample first is enough to validate against Angus's
   screenshots before committing to the full range.

Practical notes:
- Same instrument filtering as before (outrights only, front-month by volume — reuse
  `to_continuous_front_month`'s roll logic for alignment with the 1m series).
- Sizes are large: keep raw files OUT of git (data/raw/, gitignored); we'll commit only
  derived per-level aggregates (like the committed 1m slices).
- If pulling `trades` for Feb–Mar first to validate cheaply: that's the pair of months
  where we have Angus's hand logs, so validation density is highest there.

## What the engine lane will build on top (sequenced)

1. **Level-memory layer** (buildable NOW from OHLCV, upgraded by tick data): persist
   detected absorption candles (high-volume rejection blocks) as decaying levels; entry
   confluence = "price returns to a remembered zone" + the existing VWAP/BB machinery.
2. **Grading** (needs the data above): A–C by absorbed volume / resting size, calibrated
   against the MIG levels visible in Angus's live screenshots (pending upload).
3. Cross-check vs his live funded executions (no-hindsight; his trades = ground truth).

— Claude Code (engine lane), on Angus's direction. Ping the tracker when data lands.
