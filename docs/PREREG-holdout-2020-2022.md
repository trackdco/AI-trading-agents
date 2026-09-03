# PRE-REGISTRATION — the 2020–2022 NQ holdout

**Written 2026-09-03, before the data exists.** Nothing in this file may
be changed after the pull lands. If it is changed, the change and its
reason are appended below with a timestamp, and the test is downgraded to
exploratory.

## 0. Why this is worth a protocol

Every parameter in the program was derived on 2023-01-03 → 2026-09-02:
the 1m timeframe, the ≥3pt depth, the 1R target, the 5pt floor, the 30pt
cap, the arming threshold, the conviction tiers. **There is no untouched
data anywhere in the programme.** PBO 0.000 and DSR 1.0 test for
selection overfit *within* that sample; neither can tell us whether the
edge exists in a period nobody has looked at.

2020–2022 is the only true holdout available. It also contains regimes
2023–26 does not: the March 2020 shock, the zero-rate melt-up, and a
sustained 2022 bear market. **A holdout can only be spent once.** This
document exists so that it is spent properly.

## 1. The data

    dataset   GLBX.MDP3
    schema    ohlcv-1m
    symbols   ["NQ.FUT"]        (parent — outrights AND calendar spreads)
    stype_in  parent
    start     2020-01-01
    end       2023-01-02        (one-day overlap with nq_1m_master)

Processed exactly as the ES and 6E ports were: calendar spreads dropped
(`-` in the mapped symbol), volume-rolled to a continuous front month by
session-day volume, roll day-pairs excluded, 18:00 ET session anchor.

**Integrity gates, checked before any result is read.** If any fails, the
run is void and the problem is fixed and reported before re-running:
- price range plausible for NQ 2020–22 (roughly 6,600 – 16,800)
- ≥ 700 session-days survive the engine's completeness filter
- the 2023-01-02 overlap day matches `nq_1m_master` bar for bar
- no `:` symbols (EFP/basis contamination — the 6E lesson)

## 2. The one configuration

The certified spec, unchanged:

> 1-minute close ≥ depth through prior-day VAH/VAL → limit at the retest →
> structural stop (floor, cap) → 1R full exit → SAR on an opposing
> crossing close → news gate 08:00–09:30 on high-impact days → honest
> fills (one tick through) → 0.5pt round-trip cost.

**Primary population: the PD value-area family alone**, certified cell.
Fewer moving parts than the 8-level book, and no weekly-profile warmup.
The 8-level book is a secondary report, not part of the verdict.

**No sweeping.** The full 20-cell depth × target grid may be *printed*
for information, but the verdict rests only on the declared cell. Nothing
in this protocol may be re-chosen after seeing results.

## 3. Two constant sets, both declared now, both reported

NQ's own 1-minute candle has nearly tripled inside the current sample —
full-session medians 3.50pt (2023), 4.50 (2024), 6.00 (2025), 9.00
(2026). The certified constants are anchored on the recent, larger tape.
On a 2020–22 NQ trading 6,600–16,800 they will very likely be oversized,
which is exactly the failure gold's 2023–24 era showed (§22: "partly
constants-era mismatch").

So both runs happen, and both are reported:

**Run A — frozen constants.** floor 5.0, depth 3.0, cap 30.0. The honest
"would this have worked exactly as specified" test.

**Run B — era-derived constants.** The ratio recipe, applied by scaling
rather than by absolute anchor so it is internally consistent:

    m_now  = median(high − low) over all 1m bars, full 23h session,
             2023-01-03 → 2026-09-02, roll days excluded
    m_era  = the same measurement over 2020-01-01 → 2022-12-30
    k      = m_era / m_now
    floor  = 5.0 × k,  depth = 3.0 × k,  cap = 30.0 × k
             (each rounded to the 0.25 tick)

Cost stays 0.5pt/RT — the contract's point value did not change.

*Note on reproducibility:* §34 quotes the 2026 median candle as 7.1pt;
the measurement defined above gives 9.00pt for 2026, so the two are not
the same statistic. Scaling by a ratio of like-for-like measurements
avoids depending on reproducing that absolute number.

## 4. The bar

In-sample anchor — PD value area, certified cell, 2023–26:

| year | n | WR | net EV | R/day |
|---|---:|---:|---:|---:|
| 2023 | 1,630 | 67.2% | +0.1448 | +1.12 |
| 2024 | 1,914 | 68.8% | +0.1887 | +1.72 |
| 2025 | 2,189 | 66.9% | +0.1484 | +1.49 |
| 2026 | 1,574 | 65.8% | +0.1380 | +1.74 |
| **all** | **7,307** | **67.2%** | **+0.1559** | **+1.49** |

**PASS** requires all three, on the better of Run A / Run B:
1. net expectancy **> 0 in each of 2020, 2021 and 2022 separately**
2. pooled win rate **≥ 60%** (break-even at 1R is ~50% before cost)
3. pooled net expectancy **≥ +0.08R** — roughly half the in-sample
   +0.1559, a deliberately generous allowance for winner's-curse shaving

**PARTIAL** — pooled net expectancy > 0 but one calendar year negative,
or pooled win rate between 55% and 60%.

**FAIL** — pooled net expectancy ≤ 0, or pooled win rate < 55%.

## 5. Predictions, declared now so they can be scored

Recording these makes the exercise honest: a prediction that survives is
evidence, and one that fails is a correction I cannot quietly drop.

- **P1.** Run B (era constants) beats Run A (frozen) on pooled net
  expectancy. *Reason: NQ was much smaller then, so a 5pt floor and 30pt
  cap are oversized for the tape.*
- **P2.** Run B's pooled win rate lands between 60% and 68% — below the
  in-sample 67.2% but clearly above the 50% break-even.
- **P3.** 2020 is the most extreme year: the widest stops, the highest
  share of signals refused by the cap, and the largest single-day loss of
  the three.
- **P4.** The 1R target still dominates every higher target, as it has on
  NQ, GC and ES.

## 6. What each outcome means, decided in advance

- **PASS on Run A** — the strongest possible result. The frozen spec,
  untouched, generalises to an unseen three-year period containing a
  crash and a bear market. The four-year numbers can be trusted as
  stated, and the standing winner's-curse caveat can be materially
  relaxed.
- **PASS on Run B only** — the *grammar* generalises but the constants
  must track volatility. This is a real finding and it changes the live
  spec: the floor, depth and cap become volatility ratios rather than
  fixed points, which is the audit's untested recommendation #4. It also
  implies the current constants will drift out of calibration as NQ's
  volatility changes, and need a review cadence.
- **PARTIAL** — logged as-is. No re-tuning to convert it into a pass.
- **FAIL on both** — the edge is specific to 2023–26. That is the single
  most important thing this programme could learn, and it must be
  reported as loudly as any survivor. It does not mean the backtest was
  wrong; it means the live case rests on the assumption that the current
  regime persists, which would have to be stated explicitly to anyone
  putting money behind it.

## 7. Rules of engagement

1. **One look.** Both runs execute, everything is reported, and no
   parameter is changed afterwards to improve the result.
2. **A bug is the only licence to re-run**, it must be documented in the
   findings alongside the result, and the pre-bug output is reported too.
   (Precedent from today: the trade-dump price rounding that zeroed every
   6E risk; the `abs()` window that made level-SMT read the future.)
3. **Everything is reported** — the failing cells, the ugly years, the
   grid. No selective presentation.
4. **The verdict is mechanical.** §4's three conditions are applied as
   written. Any judgement beyond them is labelled as commentary, not
   verdict.
5. This holdout is **spent after this run.** Any further use of 2020–22
   is in-sample and must be described that way.

---

*Committed before the data was pulled. Baseline figures in §4 come from
`output/analysis/pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz`, the PD
value-area run on the current sample.*
