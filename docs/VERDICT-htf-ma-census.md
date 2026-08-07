# VERDICT — HTF BB MA mechanism census

## Census A — M1 REBALANCE (run 2026-08-07, fit only, 15m reference)

```
CENSUS A — M1 REBALANCE, fit only (2025-06..2026-07), 15m reference
rows=1,806 clusters=1,394 days=291

== touch rate by D x side x era (cluster-collapsed, Wilson 95) ==
  D=0.5   above  H2-2025   87.2% [83.3,90.4] n=338
  D=0.5   above  H1-2026   89.4% [85.3,92.2] n=316
  D=0.5   below  H2-2025   91.1% [87.8,93.7] n=361
  D=0.5   below  H1-2026   89.4% [85.5,92.4] n=312
  D=0.75  above  H2-2025   95.8% [89.5,98.7] n=80
  D=0.75  above  H1-2026   85.0% [75.6,91.2] n=80
  D=0.75  below  H2-2025   90.4% [84.0,94.4] n=125
  D=0.75  below  H1-2026   94.3% [87.4,97.5] n=88
  D=1.0   above  H2-2025  100.0% [51.0,100.0] n=4 UNDERPOWERED
  D=1.0   above  H1-2026  100.0% [43.8,100.0] n=3 UNDERPOWERED
  D=1.0   below  H2-2025   75.0% [30.1,95.4] n=4 UNDERPOWERED
  D=1.0   below  H1-2026  100.0% [56.6,100.0] n=5 UNDERPOWERED

== ma_before_stop_S (LOAD-BEARING) — D=0.5, side x era ==
  S= 10t above    5.2% [ 3.4, 8.3] n=338  |    2.7% [ 1.5, 5.3] n=316
  S= 10t below    7.0% [ 4.7,10.0] n=361  |    3.4% [ 2.0, 6.2] n=312
  S= 20t above   11.0% [ 8.0,14.7] n=338  |    7.9% [ 5.4,11.4] n=316
  S= 20t below   11.4% [ 8.5,15.0] n=361  |    5.4% [ 3.4, 8.6] n=312
  S= 30t above   15.4% [11.9,19.6] n=338  |   11.1% [ 8.1,15.0] n=316
  S= 30t below   15.1% [11.6,19.0] n=361  |    8.0% [ 5.5,11.6] n=312
  S= 40t above   18.9% [15.1,23.5] n=338  |   14.4% [11.1,18.9] n=316
  S= 40t below   20.6% [16.7,25.0] n=361  |   12.5% [ 9.3,16.6] n=312
  S= 60t above   26.4% [21.9,31.3] n=338  |   19.2% [15.3,24.0] n=316
  S= 60t below   30.9% [26.2,35.7] n=361  |   18.0% [14.1,22.6] n=312
  S= 80t above   33.0% [28.3,38.3] n=338  |   25.7% [21.1,30.7] n=316
  S= 80t below   36.4% [31.5,41.4] n=361  |   23.5% [19.0,28.4] n=312

== ma_before_ext_E — D=0.5, pooled sides shown per era ==
  E=0.5 W above   42.3% [37.2,47.6] n=338  |   48.2% [42.6,53.6] n=316
  E=0.5 W below   50.7% [45.6,55.8] n=361  |   44.8% [39.4,50.4] n=312
  E=1.0 W above   62.5% [57.2,67.4] n=338  |   66.5% [61.1,71.4] n=316
  E=1.0 W below   66.3% [61.5,71.2] n=361  |   63.1% [57.7,68.3] n=312
  E=1.5 W above   72.4% [67.5,77.0] n=338  |   78.0% [73.0,82.1] n=316
  E=1.5 W below   74.7% [70.1,79.0] n=361  |   73.6% [68.6,78.3] n=312
  E=2.0 W above   79.6% [75.0,83.5] n=338  |   83.2% [78.7,86.9] n=316
  E=2.0 W below   79.4% [74.7,83.1] n=361  |   77.9% [73.0,82.1] n=312
  E=3.0 W above   85.3% [81.0,88.6] n=338  |   86.4% [82.2,89.7] n=316
  E=3.0 W below   86.7% [82.8,89.8] n=361  |   83.7% [79.1,87.3] n=312

== sessions (D=0.5, both eras pooled; reported never filtered) ==
  asia       above  touch 100.0% [97.9,100.0] n=177 | stop40  22.0% [16.6,28.7] n=177
  asia       below  touch 100.0% [98.0,100.0] n=190 | stop40  19.7% [14.9,26.3] n=190
  london     above  touch  99.4% [96.4,99.9] n=155 | stop40  20.3% [15.0,27.7] n=155
  london     below  touch 100.0% [97.6,100.0] n=154 | stop40  19.2% [14.0,26.4] n=154
  ny_pre     above  touch  97.4% [91.1,99.3] n=78 | stop40  16.7% [10.0,26.5] n=78
  ny_pre     below  touch  93.4% [85.5,97.2] n=76 | stop40  24.3% [15.5,34.4] n=76
  ny_rth_am  above  touch  89.7% [83.9,93.2] n=170 | stop40  10.0% [ 6.3,15.4] n=170
  ny_rth_am  below  touch  98.2% [94.9,99.4] n=167 | stop40  13.7% [ 9.4,19.8] n=167
  ny_pm      above  touch  26.8% [18.6,38.1] n=77 | stop40  13.0% [ 7.2,22.3] n=77
  ny_pm      below  touch  38.7% [29.4,48.9] n=93 | stop40   6.5% [ 3.0,13.4] n=93

== time-to-touch + adverse (D=0.5, touched rows) ==
  H2-2025: t_touch median 78m p75 176m | max_adverse median 28.6pt p75 73.2pt (in W: 0.43/1.08)
  H1-2026: t_touch median 83m p75 190m | max_adverse median 52.8pt p75 124.4pt (in W: 0.44/1.07)

== htf_agree_1h conditioning (D=0.5, touch rate) ==
  H2-2025 above: 1h-agree  86.7% [73.8,93.7] n=45 vs disagree  85.1% [79.8,89.0] n=233
  H2-2025 below: 1h-agree  92.0% [84.5,96.1] n=88 vs disagree  88.5% [83.5,92.1] n=217
  H1-2026 above: 1h-agree  85.5% [73.8,92.4] n=55 vs disagree  89.0% [83.7,92.4] n=205
  H1-2026 below: 1h-agree  88.0% [78.7,93.6] n=75 vs disagree  88.1% [82.8,92.0] n=194

== placebos (D=0.5 machine, sampled days, headline = touch-before-stop40 rate) ==
  real: events=307 touch=91.5% touch<stop40=16.0%
  shifted-MA placebo (100 draws): mean 14.7% p95 19.0% -> real at 72th percentile
  stale-MA placebo (5 sessions old): events=88 touch<stop40=5.7%
```

## Census A verdict (per SPEC §8)

```
VERDICT      M1 REBALANCE: BASE RATE ESTABLISHED — with the placebo rider below
M1 REBALANCE 89% touch at D=0.5W (era-consistent: 87.2/89.4 above, 91.1/89.4
             below; tight Wilson intervals; n=312-361 clusters per cell).
             D=0.75: 85-96%, eras agree within intervals. D>=1.0W: n<=5,
             UNDERPOWERED — price rarely gets a full W from the 15m MA.
SCALE LAW    The durable finding: adverse-before-touch is CONSTANT IN W UNITS
             (median 0.43W / 0.44W across eras) while drifting badly in points
             (28.6pt -> 52.8pt). Tick-denominated stop cells era-drift
             (S=60t below: 30.9% -> 18.0%); W-denominated cells are era-stable
             (E=1.0W: 62-66% all four cells; E=1.5W: 72-78%). The mechanism is
             scale-invariant; ANY fixed-tick stop rule will regime-break.
PAYOFF       Fairly priced naive: collect ~0.5W with p~.64 against 1.0W
             tolerated adverse (EV ~ -0.04W); p~.75 against 1.5W (EV ~ -0.01W).
             The base rate is real; the naive trade on it is not free money.
NULLS        Proximity-shifted MA (100 draws, headline touch<stop40): real
             16.0% vs placebo mean 14.7%, real at the 72nd percentile — NOT
             distinguishable. A random nearby line performs almost as well on
             the fixed-stop payoff metric. Stale 5-session MA: 5.7% — the
             CURRENT band position carries real information; the specific MA
             line vs its neighbors does not, at this metric.
SURFACE      Touch rate rises smoothly D=0.5 -> 0.75 (interior, no spike);
             stop-S and ext-E columns monotone in S/E as they must be.
ERA          H2-2025 vs H1-2026 agree on every W-normalized cell; disagree on
             tick-normalized cells (the scale law, not a mechanism failure).
SESSION      Asia/London touch ~100% (slow, overnight); ny_rth_am 90-98%;
             ny_pm 27-39% — largely 17:00-close truncation, not mechanism
             failure. Reported, never filtered.
CONDITIONING htf_agree_1h: no effect at D=0.5 (agree~disagree in all four
             cells) — killed as a conditioning variable at this displacement.
GAPS         Placebo run on the stop40 headline only (not on the unconditional
             touch rate or W-cells); 5m/60m comparator references not yet run;
             D>=1.0 underpowered; ny_pm confounded with truncation; Census B/C
             pending.
NEXT         ONE test: proximity placebo on the W-NORMALIZED payoff cell
             (touch before 1.0W further extension, D=0.5). Acceptance bar,
             stated now: real >= 95th percentile of 100 matched draws in BOTH
             eras. Pass -> the MA is special and M1 graduates to entry-timing
             research. Fail -> M1's 89% base rate enters the base-rate library
             as the NULL that every future level idea must beat, and entry
             research pivots to what selects WHICH rebalances (Angus's eye).
```

## NEXT test result + convergence decomposition (run 2026-08-07)

```
DECOMPOSITION (all fit days, 1,490 events at D=0.5, wins only):
  price-led (share>=.75): 50-72% by cell | ma-led (<=.25): 7-21%
  profit<=0 at touch: 4.5-14.2% (below-side cleanest: 4.5/7.1%)
  pooled median price_share 0.86; mean profit at touch +0.381W vs mean gap
  0.549W -> TRUE COLLECTABLE = 69% of the naive gap.
  The touch is real: price does most of the walking. The rebalance pays
  ~0.38W mean per touched event; refine every payoff calc accordingly.

DECLARED W-CELL PLACEBO BAR (real >= p95 both eras):
  H2-2025: real 65.8% | placebo mean 62.9%, p95 67.3% -> 89th pct  FAIL
  H1-2026: real 63.9% | placebo mean 59.8%, p95 63.7% -> 96th pct  PASS
  RESULT: FAIL. No re-litigation: the bar was declared before the run.
  Honest residue on the record: real beats the placebo MEAN in both eras
  (+2.9pp / +4.1pp) and crushes the stale control — the MA carries a small
  real signal that does not clear significance in the discovery era.

RULING (as pre-registered): M1's 89% touch rate enters the base-rate library
as the NULL for level-based ideas. The 15m MA is not proven special vs
proximity-matched neighbors at the payoff level. Research pivots to
rebalance SELECTION — what distinguishes the rebalances worth taking —
and to Census B (M2 rejection/continuation).
```
