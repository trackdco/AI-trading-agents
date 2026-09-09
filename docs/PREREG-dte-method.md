# PRE-REGISTRATION — the DTE method (delivery / target / execution)

Written 2026-09-09, BEFORE the run. Source: a YouTube transcript. Claimed 70-80% win rate.
NQ, entry on 1-3 min. Three gates, all mandatory — "if just one letter is missing, do not
take the trade."

## The three gates, as stated
**D — Delivery.** Price must be inside an unmitigated higher-timeframe fair value gap
(4h, 1h or 15m). Inside a BEARISH HTF FVG -> shorts only. Inside a BULLISH one -> longs
only. Inside both at once (conflicting) -> NO TRADE. A close beyond an HTF FVG inverts it
and flips the bias.

**T — Target.** An obvious draw on liquidity, PLUS low-resistance liquidity leading to it:
at least 3 clustered UNTAPPED swing highs (for an up-target) or lows (for a down-target).
If that liquidity has already been swept, no trade. Stated as the single most important
element: "if I do not have lower resistance liquidity, I do not take a trade."

**E — Execution.** A V-spike inversion fair value gap. An FVG forms, then price trades
back into it and CLOSES through it within 6 candles, in a V shape. The candle that does the
inverting must show displacement — a full-bodied close, "not a weak little candle with a
bullish wick at the bottom". Enter on the highest-timeframe inversion available in the leg.

## Mechanical translation (frozen)
Data: NQ 1-minute, three tapes kept separate (2017-19 / 2020-22 / 2023-26). ET throughout.

- **FVG at bar i**: bullish if `low[i] > high[i-2]`, zone `[high[i-2], low[i]]`.
  Bearish if `high[i] < low[i-2]`, zone `[high[i], low[i-2]]`.
- **Inversion**: a bullish FVG is inverted when a later bar CLOSES below its zone low
  (now resistance -> SHORT). A bearish FVG is inverted when a bar CLOSES above its zone
  high (now support -> LONG).
- **V-spike**: `inversion_bar - fvg_bar <= W` bars. W = 6 (his number).
- **Displacement**: on the inversion bar, `|close-open| / (high-low) >= B` and the close is
  in the trade direction.
- **HTF delivery**: FVGs computed on 15m / 1h / 4h. At the entry bar the entry price must
  sit inside at least one un-inverted HTF FVG whose direction matches the trade. Inside
  both a bullish and a bearish HTF FVG -> skipped as conflicting.
- **LRLQ**: count untapped fractal swing lows below entry (shorts) / highs above (longs)
  within a 240-bar lookback. Untapped = never exceeded since it formed. Need >= L.
- **Entry** at the close of the inversion bar.
- **Stop** at the V's apex: the extreme of bars `fvg_bar .. inversion_bar` against the trade.
- **Target** entry +/- `T x risk`. He takes full TP at 1:2.

Exits scanned from the bar AFTER entry. A bar touching both stop and target counts STOP.
Cost 0.75 pt round turn. One position at a time. Session 09:30-11:00 ET (he trades the open).

## Swept settings — declared now, all reported
- HTF set ......... {15m} / {15m,1h} / {15m,1h,4h}
- V window W ..... 3 / 6 / 10
- displacement B .. 0.5 / 0.6 / 0.7
- LRLQ count L .... 0 (off, control) / 3 / 4
- entry timeframe . 1 / 2 / 3 min
- target T ........ 1.0 / 2.0

## The bar — alive only if ALL hold
1. Positive net R/trade after cost on ALL THREE tapes at the same settings.
2. Win rate above the break-even rate for its target size by > 5 points.
3. Pooled t > 2.5 (large sweep).
4. Survives dropping its 3 best trades.
5. Beats a matched RANDOM entry (same session, risk, target) by > 0.10 R.
6. The winning settings form a ridge, not a spike.

## Predictions, scored after the run
- **P1** The win rate will land nowhere near 70-80%. At 1:2, break-even is 33.3%; a 70%
  win rate there is +1.10 R/trade, which no rule in this repo has approached.
- **P2** The LRLQ gate — called the most important element — will move R/trade by less
  than 0.05 versus L=0.
- **P3** The HTF delivery gate will cut trade count hard without improving R/trade.
- **P4** It will fail the random-entry control, like the pin bar did.
- **P5** The 1:1 target will beat 1:2 on win rate but not on R, as in every prior test.

---

## ADDENDUM 2026-09-09 — cross-market port of DTE + D(1h/4h)

Declared BEFORE the run. The rule that survived on NQ 1-minute is now ported to other
instruments. Only the market changes; the rule is frozen exactly as it stands in
docs/FINDINGS-dte-delivery-isolated.txt.

**Data.** `data/reference/algotrader_3min/{NQ,ES,RTY,YM,GC}_3min.parquet` — 3-minute bars,
2021-04 to 2026-06, ~1,590 sessions each, verified 99.4% against our Databento NQ.

**Timeframe change, and why NQ must be re-run.** The finding is on 1-minute bars. These
reference files are 3-minute. 3-minute is inside the source's stated 1-3 minute entry
range, so it is a fair venue — but a positive ES or GC result means nothing unless NQ is
ALSO positive on 3-minute. NQ-3min is therefore the control, run on the same file, and the
port is judged against it, not against the 1-minute number.

**Cost normalisation.** 3 ticks round turn per market, matching NQ's 0.75pt = 3 ticks:
NQ 0.75 / ES 0.75 / RTY 0.30 / YM 3.0 / GC 0.30. Max risk 320 ticks.

**The bar.** The port succeeds on a market only if: R/trade > 0 after cost, positive on
both halves of that market's sample, and the win rate clears the 33.3% break-even for the
1:2 target. The PORT AS A WHOLE succeeds only if NQ-3min is positive (else the venue is
invalid) and at least 3 of 5 markets are positive.

**Predictions, scored after the run**
- **P1** NQ-3min will be positive but weaker than NQ-1min, with far fewer trades.
- **P2** ES will be positive and weaker than NQ — it is the more efficient contract and
  the prior ES port of the empire came out "dead flat".
- **P3** GC will be the weakest or negative. Different participant structure, and gold has
  already failed two ports in this repo (gold empire, trend-band rejection).
- **P4** At least one market will fail. The 6E finding was "the grammar transfers, the
  instrument does not"; a rule built on NQ order-flow-shaped behaviour should not travel
  cleanly to every contract.
- **P5** Trade frequency will scale with each market's tick-to-range ratio, not uniformly.
