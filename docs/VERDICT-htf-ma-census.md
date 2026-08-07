# VERDICT — HTF BB MA mechanism census

**THE NUMBER THAT MATTERS (2026-08-08): the unselected reject book went from
−0.396R to −0.047R per trade** — the R-denominated exit sweep recovered ~0.35R
of the hold-arm bleed, reducing what selection must find from ~0.7R to ~0.05R:
a ~14-fold reduction in the difficulty of the only problem left. The adopted
exit (75% out at 3R, remainder trailed — the trader's own shape at the
trader's own size, plateau-interior, LODO 14/14) is the reason. H2 (obstacle
count, gate-passed, +0.21 money correlation at episode level) now needs to be
adequate, not miraculous.

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

## Census B — M2 REJECTION/CONTINUATION (run 2026-08-07, fit only, 15m reference)

```
CENSUS B — M2 REJECTION/CONTINUATION, fit only, 15m reference
reject events w/ target: 2,998 | break-retest w/ target: 1,297 | days 291

== HEADLINE: structural target before S past the trigger-candle extreme (cluster-collapsed, Wilson 95) ==
[REJECT]
  S=10t below   60.4% [55.8,64.7] n=464  |   57.9% [53.1,62.7] n=395
  S=10t above   59.6% [55.1,64.1] n=454  |   64.3% [59.8,68.8] n=427
  S=20t below   63.7% [59.3,68.0] n=464  |   59.7% [54.8,64.5] n=395
  S=20t above   63.3% [58.7,67.5] n=454  |   65.6% [60.9,69.9] n=427
  S=40t below   68.8% [64.4,72.8] n=464  |   62.8% [57.9,67.4] n=395
  S=40t above   67.4% [63.0,71.6] n=454  |   68.6% [64.1,72.8] n=427
[BREAK-RETEST (retest-referenced)]
  S=10t below   64.6% [59.5,69.3] n=364  |   69.0% [63.4,74.1] n=284
  S=10t above   69.4% [64.3,74.1] n=337  |   67.3% [61.9,72.3] n=312
  S=20t below   67.6% [62.6,72.2] n=364  |   70.1% [64.5,75.1] n=284
  S=20t above   73.3% [68.3,77.7] n=337  |   69.2% [63.9,74.1] n=312
  S=40t below   72.5% [67.7,76.9] n=364  |   75.0% [69.7,79.7] n=284
  S=40t above   77.2% [72.4,81.3] n=337  |   70.8% [65.6,75.6] n=312

== the skew (travel_max_W quantiles, reject) ==
  H2-2025 below  p50 1.28W p75 2.45 p90 3.90 p95 5.30 max 13.7
  H2-2025 above  p50 1.24W p75 1.96 p90 2.95 p95 4.10 max 8.8
  H1-2026 below  p50 1.08W p75 1.98 p90 3.14 p95 3.91 max 10.9
  H1-2026 above  p50 1.13W p75 1.85 p90 2.77 p95 3.73 max 7.9

== geometry (reject): target dist / stop dist, W units ==
  target p25/50/75: 0.04/0.10/0.20W | stop p25/50/75: 0.10/0.17/0.29W

== magnitude, read ONCE as declared (quartiles vs headline S=20) ==
  pen_bw         H2-2025: Q1..Q4 62% 66% 70% 72%
  pen_bw         H1-2026: Q1..Q4 62% 66% 67% 70%
  body_atr       H2-2025: Q1..Q4 64% 64% 64% 69%
  body_atr       H1-2026: Q1..Q4 64% 66% 64% 63%
  close_dist_bw  H2-2025: Q1..Q4 60% 62% 70% 78%
  close_dist_bw  H1-2026: Q1..Q4 54% 64% 73% 73%

== conditioning columns, REPORTED never filtered (headline S=20) ==
  confluence_count   H2-2025: 1:57%(n175) 2+:69%(n1379)
  confluence_count   H1-2026: 1:58%(n187) 2+:67%(n1231)
  mtf_reject_count   H2-2025: 1:68%(n1238) 2:64%(n272) 3+:64%(n58)
  mtf_reject_count   H1-2026: 1:65%(n1127) 2:69%(n239) 3+:69%(n64)
  admissible_snapshot H2-2025: ADMISSIBLE 70%(n1229) vs BLOCKED 58%(n339)
  admissible_snapshot H1-2026: ADMISSIBLE 70%(n1101) vs BLOCKED 52%(n329)

== sessions (reject, S=20, eras pooled; reported never filtered) ==
  asia       below   68.1% [62.6,73.2] n=298
  asia       above   70.9% [65.8,75.7] n=317
  london     below   60.3% [53.5,66.4] n=218
  london     above   65.4% [59.2,70.8] n=253
  ny_pre     below   61.9% [52.2,71.5] n=93
  ny_pre     above   65.2% [54.8,73.8] n=94
  ny_rth_am  below   71.3% [63.0,78.2] n=132
  ny_rth_am  above   70.8% [63.2,77.8] n=145
  ny_pm      below   55.3% [48.3,61.8] n=205
  ny_pm      above   56.6% [49.1,63.4] n=181

== placebos (headline: target before 20t past extreme) ==
  H2-2025: real 56.8% (events 474) | placebo mean 54.4% p95 59.6% | real at 80th pct
  H1-2026: real 55.4% (events 475) | placebo mean 49.8% p95 55.4% | real at 94th pct
```

## Census B verdict (per SPEC §8)

```
VERDICT      M2 REJECTION/CONTINUATION: BASE RATE ESTABLISHED — both arms,
             era-consistent, cluster-collapsed; same placebo rider as M1.
HEADLINE     Structural target before 20t past the trigger-candle extreme:
             REJECT 59.7-65.6% (all four era-side cells agree within Wilson
             intervals). BREAK-RETEST (retest-referenced, the fairness fix)
             67.6-73.3% — HIGHER than reject in every matched cell, both eras.
             The census's strongest branch is break-and-retest: ~70-77% to
             first target at S=40t, with a defined entry 80% of the time.
             Corroborated independently by ANGUS's setup-4 pair (Wednesday):
             the winner was break-and-retest; the loser was immediate entry.
SKEW         travel_max_W p50 1.1-1.3W, p90 2.8-3.9W, p95 3.7-5.3W, max 8-14W,
             both eras. The economics are in the tail, as claimed; the first
             level (median 0.10W) is a toll booth, not the trade.
MAGNITUDE    Read once, as declared: close_dist_bw is the carrier — Q1->Q4
             monotone +18pp/+19pp in BOTH eras (60->78, 54->73). pen_bw
             +8-10pp both eras. body_atr flat. The "hard rejection" ANGUS
             verbalised as persistence (null, BR-5) lives in HOW FAR THE
             CLOSE SETTLES from the MA — an unhunted variable, both eras.
CONDITIONING (reported, never filtered) admissible_snapshot separates
             era-consistently: ADMISSIBLE 70%/70% vs BLOCKED 58%/52% — the
             Census C rule showing its teeth for free in the B columns.
             confluence 2+ vs 1: +11/+9pp. mtf_reject_count: flat (consistent
             with the persistence null).
SESSION      asia + ny_rth_am strongest (68-71%); ny_pm weakest (55-57%,
             truncation-confounded). Reported, never filtered.
NULLS        Proximity-shifted line, headline metric: real at 80th pct
             (H2-2025) / 94th pct (H1-2026); beats the placebo MEAN in both
             eras (+2.4pp/+5.6pp) but clears p95 in neither. Under the same
             standard M1 was held to: line-specialness NOT proven. The base
             rates, not the line, are the durable artifact.
ERA          Every headline cell agrees across eras within intervals; skew,
             magnitude, and admissibility findings replicate in both.
GAPS         5m/60m comparators unrun; ny_pm truncation unquantified; break
             placebo not run (reject-headline only); Census C full sweep
             (ceiling_broken_K) pending.
NEXT         Census C — the admissibility rule sweep — now carrying an
             era-consistent +12/+18pp preview from unfiltered columns, the
             strongest selection lead either mechanism has produced.
```

## Census C — admissibility sweep (run 2026-08-07)

```
CENSUS C — admissibility sweep (prereg §C), fit only
events: 4,295 | NO-CEILING 75.9% | with ceiling 24.1% (5m 19.5%, 60m 4.6%)

== ANGUS asymmetry: remaining favorable travel FROM ENTRY (W) ==
  reject  H2-2025: p50 1.28 p75 2.68 p90 4.63 p95 6.23
  reject  H1-2026: p50 1.01 p75 2.27 p90 4.37 p95 5.53
  break   H2-2025: p50 1.22 p75 2.79 p90 4.69 p95 5.71
  break   H1-2026: p50 1.17 p75 2.40 p90 4.20 p95 6.10

== strata by K (metric: target before 20t past extreme) ==
[K=1]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  65.6%[57.0,73.3]n=128  | UNBROKEN  57.0%[51.5,62.3]n=321 
          ADMISSIBLE(K)  68.8%[65.6,71.7]n=886   [sizes: 1743/131/395]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  68.1%[59.2,75.9]n=116  | UNBROKEN  51.7%[46.2,57.2]n=315 
          ADMISSIBLE(K)  69.4%[66.2,72.6]n=786   [sizes: 1519/120/387]
[K=2]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  59.8%[53.0,66.3]n=204  | UNBROKEN  59.8%[53.8,65.6]n=264 
          ADMISSIBLE(K)  67.8%[64.7,70.8]n=901   [sizes: 1743/218/308]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  61.6%[54.6,68.6]n=181  | UNBROKEN  52.3%[46.2,58.3]n=260 
          ADMISSIBLE(K)  68.6%[65.2,71.7]n=792   [sizes: 1519/192/315]
[K=3]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  59.8%[53.3,65.5]n=245  | UNBROKEN  60.1%[53.8,66.6]n=222 
          ADMISSIBLE(K)  67.4%[64.3,70.4]n=906   [sizes: 1743/271/255]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  61.3%[54.9,67.4]n=230  | UNBROKEN  51.2%[44.6,57.7]n=219 
          ADMISSIBLE(K)  68.1%[64.8,71.2]n=799   [sizes: 1519/253/254]
[K=5]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  57.8%[52.2,63.2]n=308  | UNBROKEN  64.5%[56.9,72.1]n=148 
          ADMISSIBLE(K)  66.5%[63.4,69.5]n=916   [sizes: 1743/363/163]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  57.4%[51.6,62.7]n=302  | UNBROKEN  53.6%[45.3,61.6]n=140 
          ADMISSIBLE(K)  67.0%[63.6,70.1]n=810   [sizes: 1519/355/152]
[K=10]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  57.8%[52.6,62.7]n=362  | UNBROKEN  69.2%[57.2,79.1]n=65 
          ADMISSIBLE(K)  66.0%[62.9,69.0]n=923   [sizes: 1743/455/71]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  56.0%[50.8,61.1]n=357  | UNBROKEN  54.2%[40.9,65.4]n=60 
          ADMISSIBLE(K)  65.6%[62.2,68.7]n=818   [sizes: 1519/444/63]
[K=inf]
  H2-2025: NOCEIL  68.6%[65.4,71.6]n=865  | BROKEN  58.5%[53.5,63.1]n=399  | UNBROKEN  77.3%[43.4,90.3]n=11*
          ADMISSIBLE(K)  66.1%[63.0,69.1]n=926   [sizes: 1743/513/13]
  H1-2026: NOCEIL  68.7%[65.3,71.8]n=769  | BROKEN  55.8%[50.8,60.7]n=387  | UNBROKEN  53.8%[29.1,76.8]n=13*
          ADMISSIBLE(K)  65.3%[62.0,68.5]n=822   [sizes: 1519/494/13]

Per-arm x side splits + the prereg plateau reading follow in the verdict append. Sides/arms pooled cells above are for the K surface shape only; the bar is read on the full split table.

== full split at each K: ADMISSIBLE vs UNBROKEN, era x arm ==
  K=1    reject  +11.3pp!(n269) | +18.5pp!(n267)   ('!' = CIs non-overlapping)
  K=1    break    +9.5pp (n68) | +15.8pp!(n70)   ('!' = CIs non-overlapping)
  K=2    reject   +7.4pp (n227) | +14.3pp!(n231)   ('!' = CIs non-overlapping)
  K=2    break    +3.9pp (n45) | +23.6pp!(n46)   ('!' = CIs non-overlapping)
  K=3    reject   +6.4pp (n192) | +15.3pp!(n194)   ('!' = CIs non-overlapping)
  K=3    break    +5.9pp (n34) | +22.4pp!(n37)   ('!' = CIs non-overlapping)
  K=5    reject   -0.9pp (n125) | +14.0pp!(n117)   ('!' = CIs non-overlapping)
  K=5    break    +9.8pp (n23) | +13.1pp (n28)   ('!' = CIs non-overlapping)
  K=10   reject   -9.3pp (n48) |  +5.3pp (n45)   ('!' = CIs non-overlapping)
  K=10   break   +11.8pp (n17) | +26.6pp (n16)   ('!' = CIs non-overlapping)
  K=inf  reject  UNDERPOWERED | UNDERPOWERED   ('!' = CIs non-overlapping)
  K=inf  break   UNDERPOWERED | UNDERPOWERED   ('!' = CIs non-overlapping)
```

## Census C verdict (read against the prereg §C bar)

```
VERDICT      NOT ESTABLISHED. The bar demanded ADMISSIBLE-vs-UNBROKEN
             separation positive in BOTH eras with non-overlapping intervals
             at >=2 ADJACENT K values. Both-era non-overlap occurs at exactly
             one cell: K=1, reject (+11.3pp!/+18.5pp!). No plateau. The
             E1-CONDITIONAL therefore EXPIRES UNUSED, as declared.
WHAT IS REAL Separation is SIGN-consistent at K in {1,2,3}, both arms, both
             eras (8/8 powered cells positive), magnitudes larger in H1-2026;
             it decays and flips by K=10 (reject -9.3pp). The lead survives
             as a lead, not as an established rule.
DISCOVERY    Permission EXPIRES, fast: BROKEN within K=1 own-TF bar performs
             like NO-CEILING (~66-68%); by K>=5 BROKEN degrades to 56-58%.
             The spec's open question is answered: a ceiling break grants
             passage for roughly ONE bar of its own timeframe. Fresh
             permission only.
STRATA       NO-CEILING 75.9% of events (68.6%/68.7% era-stable baseline);
             with-ceiling 24.1% (5m 19.5%, 60m 4.6%). UNBROKEN-ceiling is the
             consistently worst stratum (52-60%).
ASYMMETRY    ANGUS's spent-travel hypothesis NOT supported: remaining
             favorable travel from entry is equal across branches (reject p50
             1.01-1.28W vs break 1.17-1.22W; p95 5.5-6.2 vs 5.7-6.1). The
             fixed-target-vs-tail exit difference between branches is not
             mechanical scarcity; it is path shape, cause unmeasured.
GAPS         Break-arm UNBROKEN cells thin (n17-70 clusters, several
             UNDERPOWERED); K=inf unpowered both arms; canon-L0 comparator
             population deferred; no placebo run on C (lead-level, not
             mechanism-level).
NEXT         Nothing auto-runs. The surviving selection leads, ranked by
             trial status: close_dist_bw (passed its constant-target trial),
             K<=1 fresh-permission admissibility (sign-consistent, plateau
             failed), confluence/Census D (motivated by the twice-failed
             placebo pattern). Sequencing is the human's call.
```
