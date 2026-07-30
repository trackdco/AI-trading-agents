# London 09:30-10:00 — the weak bucket, diagnosed and priced

**Fit only. Sealed 2023/24 never loaded. London standalone (no NY interaction measured here, by request).**

Book: **187 trades, $+22,795, 57% win, mean R +0.513, maxDD $2,440** at flat 1 NQ lot.

## 1. The edge is not flat across the window

| London fill time | n | share of trades | win rate | mean R | net $ | share of net | 2025 R | 2026 R |
|---|---|---|---|---|---|---|---|---|
| 08:00-08:30 | 45 | 24% | 60% | +0.371 | $+4,722 | 20.7% | +0.159 | +0.488 |
| 08:30-09:00 | 55 | 29% | 67% | +0.759 | $+10,215 | 44.8% | +0.977 | +0.625 |
| 09:00-09:30 | 44 | 24% | 57% | +0.734 | $+6,864 | 30.1% | +0.477 | +0.970 |
| **09:30-10:00** | 43 | 23% | 40% | +0.119 | $+994 | 4.4% | +0.038 | +0.190 |

**09:30-10:00 takes 23% of the trades for 4.4% of the profit**, and it is weak in BOTH eras (+0.038 / +0.190) — structural, not a regime artifact.

## 2. Why — a hit-rate problem, not a payoff problem

| bucket | avg WIN R | avg LOSS R | winners / losers | win rate |
|---|---|---|---|---|
| 08:00-08:30 | +0.99 | -0.56 | 27 / 18 | 60% |
| 08:30-09:00 | +1.58 | -0.92 | 37 / 18 | 67% |
| 09:00-09:30 | +1.93 | -0.84 | 25 / 19 | 57% |
| 09:30-10:00 | +1.64 | -0.88 | 17 / 26 | 40% |

When a late trade works it pays **+1.64R** — competitive with the best bucket — and its losses are normal. The setups are not junk; the strike rate is. So the mechanism has to explain FREQUENCY of failure, not size.

### It is not the window close truncating them

First hypothesis, and it is wrong.

| bucket | median min to 10:00 | median hold | % exiting at/after 10:00 |
|---|---|---|---|
| 08:00-08:30 | 107 | 12.0 | 0% |
| 08:30-09:00 | 77 | 9.0 | 0% |
| 09:00-09:30 | 48 | 14.5 | 7% |
| 09:30-10:00 | 18 | 9.0 | 37% |

**37% of late-bucket trades exit AFTER 10:00**, so positions are not force-closed at the window edge and survivors get their full run. Median hold is 9 minutes against 18 available — they die early, they do not run out of clock.

### The two mechanisms that do explain it

| bucket | room ahead | session range | **stop / range** | stop (pts) | pure stop % | reached partial+target % |
|---|---|---|---|---|---|---|
| 08:00-08:30 | 0.44 | 184.8 | **7.44%** | 14.00 | 33% | 18% |
| 08:30-09:00 | 0.47 | 186.0 | **5.87%** | 12.75 | 33% | 31% |
| 09:00-09:30 | 0.54 | 185.5 | **7.55%** | 11.88 | 41% | 11% |
| 09:30-10:00 | 0.63 | 199.8 | **5.45%** | 11.75 | 56% | 9% |

**Both of the project's known pathologies stack in this one bucket.**

1. **Room ahead is highest here.** That is the loser signature isolated in `docs/LONDON-LOSS-ANATOMY.md` (AUC 0.382, losers higher): entries far from value, at the extremes of an already-extended range, fighting mean reversion. By 09:30 the continuation entries are gone; what still triggers is the fades.
2. **Stop/range is lowest here, against the largest realized range.** By 09:30 the session has printed its widest range, but the structural stop is the smallest fraction of it. Same mechanism as `docs/LONDON-ERA-DIAGNOSIS.md` — a stop that is not wide enough for the volatility already realized — except intraday, every day, rather than across regimes.

Consistent with the exit mix: the pure-stop rate is highest and the reached-partial+target rate lowest in exactly this bucket. Three independent measurements agreeing is why this reads as a mechanism rather than as n=43 noise.

## 3. Guard — is the time-of-day structure real?

Permuting the fill-time label across trades (5,000 shuffles, seeded 20260730) and taking the **worst bucket in each shuffle**. Taking the min is deliberate: it makes the statistic pay for the fact that four buckets were looked at and the worst one chosen, so no separate multiplicity correction is owed.

| | mean R gap, book minus worst bucket |
|---|---|
| observed (09:30-10:00) | **+0.393** |
| permuted median | +0.217 |
| permuted p95 | +0.426 |

**p = 0.0760.** A random time-labelling produces a worst-bucket this weak about 8% of the time, so the profile is NOT distinguishable from chance clustering. The mechanism in section 2 may still be real, but the bucket's weakness on its own does not clear a null that accounts for having picked the worst of four.

## 4. What cutting it would do

Applied at the POPULATION level and then re-selected, so a skipped trade never consumes a day-stop budget — the honest form of the counterfactual.

| book | trades | net $ | win rate | mean R | maxDD | net/maxDD | risk deployed | 2025 / 2026 net |
|---|---|---|---|---|---|---|---|---|
| full window 08:00-10:00 | 187 | $+22,795 | 57% | +0.513 | $2,440 | 9.3 | $52,295 | $+8,178 / $+14,618 |
| **cut from 09:30** | 144 | $+21,801 | 62% | +0.630 | $1,325 | 16.5 | $41,170 | $+8,252 / $+13,549 |
| cut from 09:15 | 127 | $+16,730 | 61% | +0.541 | $1,325 | 12.6 | $37,010 | $+6,985 / $+9,745 |
| cut from 09:00 | 100 | $+14,938 | 64% | +0.585 | $1,740 | 8.6 | $29,530 | $+5,942 / $+8,995 |

**The 09:30 cut, stated plainly.** Net goes $+22,795 -> $+21,801 (**$-994**) on 43 fewer trades. Win rate 57% -> 62%, mean R +0.513 -> +0.630, maxDD $2,440 -> $1,325, and return-on-drawdown 9.3 -> 16.5. Total dollar risk deployed falls $11,125 (21% less capital at risk over the span).

Shrinkage charged at the declared breadth of 3 boundaries: **-0.014 R** per trade off whichever cut is chosen — negligible, which is the benefit of declaring three candidates rather than sweeping every minute.

## 5. Verdict

**Cutting it costs money: $-994.** The bucket is WEAK, not LOSING — it contributed $+994 — so removing it removes profit. Exactly the trap the VWAP filter fell into: a poor win rate is not a negative expectancy.

The case, if there is one, is risk-adjusted: maxDD falls $1,115 and 21% less capital is put at risk, for 4.4% of the net. Return-on-drawdown goes 9.3 -> 16.5.

**Recommendation: do NOT cut it for this holdout.** Three reasons, in order of weight. (1) The time-permutation guard returns p=0.076 — the profile does not clear a null that pays for picking the worst of four buckets.
(2) The window is FROZEN in §1 of the pre-registration; narrowing it is a config change that would invalidate the era-crossing, grid and determinism work already done against 08:00-10:00. (3) The holdout is already at 2 gated questions on ~84 projected trades and cannot price a fourth.

**What to do instead.** Record the profile as a declared prior and check it on the holdout as part of the primary's descriptive output — if 09:30-10:00 is the weakest bucket there too, on data owing nothing to this analysis, it becomes a properly evidenced candidate for a later window change. That costs no alpha, because it gates no decision.
