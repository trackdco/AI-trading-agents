# NYA-FA-01 grading pack — frozen fail-branch spec

Book: n=28 trades, 2025-06-02..2026-07-15 (270 sessions), $+984 at $160-risk.

## DSR (denominator from the merged machine ledger, §6.0)
  ledger: 18 trials, effect var 0.2964
  daily SR +0.0442 | SR0 +1.0093 | PSR(0) 0.786 | DSR 0.000 (below .95)
  min track vs zero: 1155 days (have 270)

## PBO (CSCV over the 9 searched gate x stop cells)
  PBO 0.85 over 12870 splits (9 cells, 256 days) — OVERFIT >= .50; IS->OOS slope -0.64, P(OOS loss) 0.62

## Funded-shell MC (comparative)
  spec alone                 12mo P(bust) 2.6%  median $+855
  canon alone (same days)    12mo P(bust) 0.2%  median $+76,449
  canon + spec (paired)      12mo P(bust) 0.1%  median $+78,124

## Correlation battery vs canon
  active 28/230 days, both-active 21
  union Pearson -0.049 Spearman -0.026
  both-active Pearson -0.086 (n=21 — below T3's 60-day trust bar: structural rules govern)
  T5 shared families 1/3 (order-flow): no veto
