# TASK FOR BRAKE — Order-book data pull (Angus directive, 18 Jul 2026)

## UPDATE 3 (18 Jul, pass 24) — ANGUS: pull APRIL first, one month only (~$80/mo economics)

April is the chosen validation month: it's the worst performer of the Feb–Apr test window
AND the month with Angus's documented live executions — so the heatmap's benefit gets
cross-checked directly against his real trades where the system hurts most. Scope the pull
to April 2026 (trades schema per Update 2; mbp-10 stays phase-2). Feb–Mar can follow later
if April validates.

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

## UPDATE 2 (18 Jul, pass 23) — ANGUS RULING: mbp-10 is IN, as its own later phase

Angus used the live heatmap himself pre-break and rates it highly as ORDER CONFIRMATION
and EXIT TARGETS — that's real resting-depth value beyond anything MIG reconstructs, so
depth data is confirmed, sequenced AFTER current calibration proves out on price data:
1. **NOW — `trades` historical** (this task): powers level-memory + absorption grading.
2. **DEPTH PHASE (after performance delivers): `mbp-10` historical, Feb→May first** —
   calibrate the depth layer against Angus's live screenshots and his
   confirmation/exit-target usage. Historical data doesn't expire; no need to buy
   before the phase starts.
3. **LIVE LAUNCH: Databento live mbp-10 stream** — same schema, same code path,
   agents read the book in real time. NOTE: live CME data adds exchange license fees
   on top of Databento's rate (production cost, not calibration cost).

**MIG subscription ≠ agent data source.** It's an invite-only TradingView Pine
indicator: the sub buys chart pixels, there is no API, Pine boxes can't export their
coordinates, and an invite-only script can't be edited to add alerts. Agents can never
consume it. Our graded-zones/level-memory layer pointed at mbp-10 IS the heatmap —
machine-readable and backtestable, which MIG can't be even in principle.

## Context (superseded recommendation, kept for the reasoning)

The MIG listing self-describes as **"MicroDOM-style liquidity & volume blocks for
TradingView"** (by Mohs Mayfair, $48.99/mo). Pine indicators see price/volume only —
no order-book access — so MIG's boxes/B%/S% tags are reconstructed from traded
price/volume, and `trades` ticks are strictly better raw material than MIG's own input.
That argued for skipping mbp-10; Angus's live experience (depth as confirmation/exits,
a use BEYOND replicating MIG) overrules — hence the phased plan above.

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

## UPDATE 4 (pass 28) — Brake: STOP compressing the 18 GB export for GitHub

GitHub hard-caps files at 100 MB; no compression gets 18 GB under that, and we don't need
the raw ticks in git AT ALL. Run **`scripts/condense_trades.py`** (committed, instructions
in its docstring) locally next to your export — it turns the raw file into the per-minute
footprint parquet (~50–100x smaller). Commit ONLY that parquet. If the output still tops
~95 MB, run it once per month (one output file per month).

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
