# PRE-REGISTRATION — ES false-breakdown reclaim (long only)

Written 2026-09-05, BEFORE the run. Source: a Reddit post describing a discretionary
strategy. Claims: ~60% win rate, ~1:1.3 realised RR, 3-5 trades/week, "pays the bills".

## The claim, as posted
> Wait for price to take out a multi hour level, or overnight low or previous day low.
> Wait for it to dip down, and then pop up above that level and hang for a few minutes.
> Get long, stop below low, target 10-15pts above. Leave a little runner to fly.

## Mechanical translation (frozen)
Data: `data/reference/algotrader_3min/ES_3min.parquet`, 3-minute ES, ET, 2021-04-27 to
2026-06-04. Quarterly roll days (2nd Thu of Mar/Jun/Sep/Dec) and the day after excluded.

Three fixed levels per RTH session, all set before 09:30 ET:
- `PDL`  previous RTH session low (09:30-16:00)
- `ONL`  overnight low, 18:00 ET prior evening to 09:29 ET
- `MHL`  multi-hour low, 05:30-09:29 ET (4 hours before the open)

Per level, scanning RTH bars 09:30-15:00 ET:
1. **Breakdown** — a bar's low trades below the level.
2. **Dip** — track the running minimum low from the breakdown bar onward.
3. **Reclaim** — a later bar CLOSES above the level.
4. **Hang** — the NEXT bar also closes above the level (~6 minutes on 3-min bars).
5. **Entry** long at the close of the hang bar.
6. **Stop** = running minimum low minus one tick (0.25).
7. **Target** = entry + T points. T tested at 10, 12, 15.
8. Flat at 16:00 ET if neither is hit.

One trade per level per session (first occurrence only). Exits are scanned from the bar
AFTER entry. A bar that touches both stop and target counts as a STOP.

Costs: headline at 0.50 pt round turn (2 ticks: commission + slippage). Also reported at
0.25 and 0.75.

No runner in the headline. The runner can only add to a fixed-target result, so if the
fixed target fails, the runner is not the reason.

## Control (the one we have owed ourselves)
For every real trade, one matched RANDOM trade: same session, same risk in points, same
target, entry at the close of a uniformly random RTH bar. This isolates whether the
entry rule carries information or the geometry does all the work.

## The bar — the strategy is alive only if ALL of these hold
1. Net R/trade > 0 after 0.50 pt cost on BOTH halves of the sample.
2. Win rate >= 50% (posted claim: 60%; break-even at the realised RR must be cleared).
3. Median reward:risk >= 1.0 (posted claim: 1.3).
4. Trade frequency between 1 and 10 per week (posted claim: 3-5).
5. Expectancy >= +0.15 R/trade after cost.
6. Pooled t > 2.0.
7. Beats the matched random control by more than 0.10 R/trade.

## Predictions, scored after the run
- **P1** The mechanical stop will average well above the ~10 pts the claimed 1:1.3 implies,
  because the dip low can be far from the reclaim. Realised RR will come in below 1.3.
- **P2** Win rate will land below 60% — the mechanical "hang" cannot tell a real reclaim
  from chop, which is exactly the judgement the poster says takes years of reps.
- **P3** MHL will be the weakest of the three levels (most recent, most noise-like).
- **P4** The random control will not be far behind. If the gap is under 0.10 R, the entry
  rule carries little information and the result is geometry.
