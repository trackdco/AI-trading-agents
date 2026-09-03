# FINDINGS — the 2020–2022 holdout: **PASS on frozen constants** (2026-09-03)

Protocol: `docs/PREREG-holdout-2020-2022.md`, committed `80c3f23` before
the data was pulled. Amendment 1 (boundary-continuity gate) committed
before the file was decompressed. Verdict applied mechanically.

**Result: PASS on Run A — the certified spec, constants untouched.**
The strategy generalises to three years nobody had looked at, containing
the March 2020 crash, a zero-rate melt-up, and the 2022 bear market.

## 1. Integrity gates (all four passed, checked before any result)

| gate | required | measured |
|---|---|---|
| price range | ~6,600 – 16,800 | 6,628.75 – 16,756.00 ✓ |
| session-days | ≥ 700 | 779 ✓ |
| no EFP/basis symbols | none | none ✓ |
| boundary continuity (amended) | clean join | 0 duplicated minutes, 80.75pt session gap, 12 rolls all in Mar/Jun/Sep/Dec ✓ |

1,519,338 raw rows → 1,057,201 continuous bars after dropping calendar
spreads and volume-rolling. 2020-01-01 → 2022-12-30.

## 2. Constants

Per §3, scaled by the ratio of like-for-like median 1m candles (full
session, roll days excluded):

    m_now  (2023-01-03 → 2026-09-02)  5.2500pt
    m_era  (2020-01-01 → 2022-12-30)  4.5000pt
    k = 0.8571

| | floor | depth | cap | bin |
|---|---|---|---|---|
| Run A — frozen | 5.00 | 3.00 | 30.00 | 1.00 |
| Run B — era | 4.25 | 2.50 | 25.75 | 0.75 |

**k = 0.857 is the surprise.** NQ's 2020–22 minute was only 14% smaller
than the 2023–26 average, so the constants-era mismatch that killed
gold's 2023–24 era never really arose here.

## 3. The result

**RUN A — frozen constants**

| year | n | WR | net EV | net R | R/day | cond 1 |
|---|---:|---:|---:|---:|---:|---|
| 2020 | 1,737 | 66.8% | **+0.1588** | +276 | +1.32 | PASS |
| 2021 | 1,505 | 64.3% | +0.1229 | +185 | +0.88 | PASS |
| 2022 | 2,236 | 65.2% | +0.1257 | +281 | +1.33 | PASS |
| **pooled** | **5,478** | **65.4%** | **+0.1354** | **+742** | **+1.17** | |

Conditions: (1) all years positive ✓ (2) WR ≥60% ✓ 65.4% (3) EV ≥+0.08 ✓
+0.1354. **PASS.**

**RUN B — era constants**: 6,381 trades, 65.5% WR, +0.1206 net EV, +769R,
all three years positive. **Also PASS**, but worse per trade than frozen.

## 4. How much was shaved

| | WR | net EV | R/day |
|---|---:|---:|---:|
| in-sample 2023–26 | 67.2% | +0.1559 | +1.49 |
| holdout 2020–22 | 65.4% | +0.1354 | +1.17 |
| **retained** | **97.3%** | **86.9%** | **78.8%** |

A ~13% haircut on expectancy is precisely the winner's-curse magnitude
the standing caveat predicted, and it lands well inside the deliberately
generous +0.08 bar. R/day falls further (79%) because the era traded
fewer signals per day, not because the trades were worse.

**2020 — the COVID year — was the best of the three** (+0.1588). The
strategy did *better* in the most violent regime available, and 2022's
sustained bear market still printed +0.1257. That is the single most
reassuring line in this file.

## 5. Prediction scoring (§5, declared before the run)

| | prediction | outcome |
|---|---|---|
| **P1** | era constants beat frozen | **WRONG** — frozen +0.1354 beats era +0.1206 |
| **P2** | era WR between 60% and 68% | **CORRECT** — 65.5% |
| **P3** | 2020 most extreme: widest stops, most cap refusals, biggest one-day loss | **MOSTLY WRONG** — 2020 had the largest single-day loss (−8.1R vs −6.7R), but **2022** had the widest stops (8.2pt median vs 7.2pt). Cap refusals were only 2.4% of signals across the whole run |
| **P4** | 1R dominates every higher target | **CORRECT** — 1R best at all four depths; the whole grid replicates the NQ/GC/ES shape |

Two of four clean. P1 being wrong is the interesting miss: I expected the
2026-anchored constants to be mis-scaled on an older, smaller tape, and
they were not. The tighter era floor simply admitted more marginal trades
(6,381 vs 5,478) at lower average quality.

## 6. What this does and does not establish

**Does:** the *base grammar* — 1m close ≥3pt through prior-day VAH/VAL,
limit at the retest, structural stop, 1R exit, SAR, news gate, honest
fills, cost — holds on unseen data across a crash, a melt-up and a bear
market, with no re-tuning. Combined with PBO 0.000 and the GC and ES
replications, the case that this is auction physics rather than a fitted
artefact is now much stronger than it was this morning. The standing
winner's-curse caveat can be quantified at roughly 13% rather than left
open-ended.

**Does not — and this is a real limitation of my own protocol design.**
§2 declared *one* configuration: PD value area, certified cell. So the
8-level book, both VWAP books, **arming, and conviction sizing remain
validated on 2023–26 only.** They were all derived in-sample and this
holdout says nothing about them. I should have pre-registered arming
alongside the base spec; I did not, and §7.5 says the holdout is spent.
Running it now would be a second look at data I have already seen.

The honest options are: treat the layers as in-sample-only and let
paper-trading validate them, or obtain a *further* untouched period
(2017–2019) and pre-register the layers against that before looking.

## 7. Caveats

- 779 session-days, 5,478 trades in the certified cell — solid, but a
  third the size of the in-sample run.
- 2020–22 microstructure is not 2026's. Fills in March 2020 were far
  worse than the one-tick-through rule assumes, so the 2020 figure is
  probably the most optimistic of the three.
- The 30pt cap was applied unchanged to Run A even though the era's tape
  was smaller; it refused only 2.4% of signals, so it barely bound.
- Per §7.5 this holdout is now **spent**. Any further use of 2020–22 is
  in-sample and must be described that way.
