# TASK FOR BRAKE — Order-book data pull (Angus directive, 18 Jul 2026)

## UPDATE 8 (20 Jul, Angus directive) — HEATMAP RE-SCOPE: this is an EXIT/STOP tool, not just an entry filter

**Read this before continuing any mbp-10 work.** Everything below (Updates 1-5) framed
the depth heatmap as order confirmation / entry timing. Angus's correction: the bigger
prize is on the OTHER side of the trade — **exits and stop placement.**

The mechanical oracle ceiling we've been measuring against all week (the $260k/4yr
figure quoted everywhere in the repo) is built ENTIRELY from price-based entries and
EXITS. It has no concept of resting liquidity ahead of price. Angus's hypothesis,
stated directly: *"if we're cutting our trades too early because there's a strong
indication on heatmap that we're going to go far higher, I want to implement that."*
That means: **the oracle ceiling itself may be too low** — it's the ceiling of a
strategy that exits blind to the book. A heatmap-aware exit (trail behind absorbed
levels, hold through a thin patch, take profit into a wall) could raise the actual
achievable ceiling above what we've been chasing all week.

So when the April mbp-10 data is condensed, the FIRST study on it (before any entry
work) should be: **for each of our historical winning AND losing trades that hit its
mechanical stop or target, what did the book look like in the 30-60s before that exit?**
Specifically:
- Trades that hit a fixed target/trail-stop and exited — was there a large resting
  wall just beyond the exit price that the mechanical exit left on the table?
- Losing trades that got stopped — was the stop placed inside a thin/absorbed zone
  that a book-aware stop would have avoided, or did depth actually predict the reversal?
- This produces a concrete, denominated number: "book-aware exits would have added
  $X / recovered Y% of the trades that exited too early" — the heatmap's OWN oracle
  delta, on top of the price-only ceiling.

Practical note: this needs the same Apr 1-11 mbp-10 window already sampled (Update 5)
— no new purchase, just a new study angle on data already in hand. Full-April pull
(Update 3, ~$80/mo) still stands for when this angle validates.

## UPDATE 7 (20 Jul, Angus directive) — NEW TASK: pull VIX (+ VXN) historical data

**Brake: pull historical VIX data — this is a parallel, independent task to the
heatmap work above, doesn't block on it.** Angus's reasoning: VIX moves inversely to
equities/Nasdaq and is the highest-signal EXTERNAL regime feature we don't have yet —
elevated/rising VIX historically favors trend/momentum days, low/calm VIX favors
chop/rotation days. This is the next feature-discovery round after tonight's Tier-A
free features (which already flipped the 4-year book-selection P&L from -8% to +1% —
see docs/SPEC-v07-regime-dial.md — so there's real reason to expect VIX adds more).

**What to pull:** daily VIX (CBOE), and ideally VXN (the Nasdaq-100 equivalent —
more relevant to NQ specifically) for the full backtest span, 2023-01 through today.
Free sources, no paid data needed:
- CBOE historical data page (VIX and VXN both have free downloadable CSVs going
  back years) — first choice, most authoritative.
- Yahoo Finance `^VIX` and `^VXN` daily history as a fallback/cross-check.
- FRED (`VIXCLS` series) as a third cross-check if the above have gaps.

**Format:** date, close (and ideally open/high/low if the source has it — term-structure
day-over-day change matters more than level, so we want daily deltas computable).
Drop it as `data/reference/vix_history.csv` (and `vxn_history.csv` if pulled separately),
commit + push on its own branch, ping the tracker.

**Angus wants it CROSS-CHECKED, not just added** — same discipline as tonight's feature
round (several candidates were tested and REJECTED for adding noise, not just accepted
because they sounded right). Once the data lands, engine lane will:
1. Compute VIX level + day-over-day change as of each session's pre-open.
2. Measure its book-lean discrimination against the floored oracle books exactly like
   the Tier-A features (scripts/measure_candidate_features.py) — keep it ONLY if it
   moves the needle beyond what's already wired.
3. Report back with numbers either way — this could come back "didn't help," and
   that's a valid, useful result, not a failure.

## UPDATE 6 (18 Jul, Angus directive) — NEW TASK, JUMPS THE QUEUE: historical news calendar

**This is now the single blocking item for the next agent exam — do it before any more
depth condensing.** The regime agent's event awareness (`red_folder_today`) prints 0 for
every day before 2026 because our Forex Factory calendar only covers Feb 2026 onward.
The March replays proved event-read is central, so testing the agent on 2025 without a
calendar handicaps it on exactly the feature that matters most. My server is
Cloudflare-blocked from forexfactory.com; a home connection isn't. Ten-minute job:

```
git pull
pip install cloudscraper beautifulsoup4 pandas
python scripts/scrape_ff_calendar.py
```

- Fetches the 37 FF calendar month pages (Jan 2023 → Jan 2026, ~3s apart, a few
  minutes), USD events only, and writes **`config/news_calendar_hist.csv`** (a few
  hundred KB — commits fine as-is, no condensing).
- It prints per-year counts + a sanity line at the end; roughly **60–100 high-impact
  days/year** means it worked.
- Commit + push the CSV on its own branch (e.g. `news-data`) and ping the tracker.
- If Cloudflare blocks the scrape: open each month URL in a browser
  (forexfactory.com/calendar?month=jan.2023 … dec.2025), save the pages as HTML into
  one folder, then `python scripts/scrape_ff_calendar.py --html-dir that_folder`.
  If parsing comes back empty, push one saved month page and I'll adapt the parser.

Everything downstream is pre-wired (the loader auto-merges the file): once it lands I
rebuild the regime vector + analog table and rerun the 2023–25 baselines. Full run
instructions are in the script's docstring.

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

## UPDATE 5 (pass 28) — Apr 1 sample received ✓; next condensing requests (same raw files)

The Apr 1 mbp-10 sample landed and already produced a finding (the session's biggest wall —
92 lots offered at 24,063.50 — sat under the engine's losing 09:46 long; a depth check at
the trigger would have vetoed it). To turn anecdote into statistics, from the SAME Apr 1–11
raw files (no new purchase):
1. Condense the remaining clean sessions with the same recipe: **Apr 2, 3, 6, 7, 8, 9**
   (skip Apr 10 — Databento flagged it degraded).
2. ALSO cut **02:00–05:30 ET** windows per session (Angus: London's first two hours were
   his best sessions) — same one-snapshot-per-minute, 10+10 levels format.
Scope note for expectations: 10 levels ≈ ±2.4 pts around price — this is the AT-THE-TOUCH
confirmation layer (Angus's live usage), not the zone map; the zone map comes from the
`trades` footprint (`scripts/condense_trades.py`) when that pull lands.

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
