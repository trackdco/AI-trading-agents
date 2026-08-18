# FINDINGS — ORB on gold: nothing clears the gate, and the reason is a regime shift

Programme run against the `gold-orb-models` skill. Declarations in
`docs/DECLARATIONS-gold-orb.md`; engine `src/research/orb/engine.py`; self-tests
`tests/test_orb_engine.py` (24, all pass).

**Phase 4 was not unlocked. No configuration met the promotion gate on train.**

---

## The answer in one paragraph

The plain 15-minute ORB on GC is flat-to-negative on 2023–2025 and every v3 mechanism
subtracts from it. Best cell on train is +0.046R against a required +0.10R, best profit
factor 1.11 against a required 1.30, and every 95% interval straddles zero — except London
03:00 at two ticks, which is the one cell significantly clear of zero and it is *negative*.
At two ticks per side the whole book goes negative. Underneath that sits the finding that
matters more than any cell: **gold's opening range roughly quadrupled between 2023 and
2026**, from a 4.5-point median to 18.5, and from 0.23% of price to 0.40%. Every v3 fix was
designed against the 2026 window and addresses a market that barely existed during the
measurement period — the 30-point risk cap binds on 0.6% of train trades and 18.5% of 2026
days.

---

## Phase 0 — data

| | |
|---|---|
| file | `data/gc_1m.parquet`, committed at `748df23` |
| span | 2023-01-02 → 2026-08-11, 1,276,717 bars, 936 session days |
| completeness | 931/936 days carry a 09:30 bar; 09:30–12:00 has all 150 bars on 929 |
| roll | 19 rolls, all at 00:00 or 18:00 ET, 2–4 days before contract month |
| back-adjusted | **no — raw front-month stitch** |
| 2021–2022 | **absent; Databento SDK installed but no API key, and the user has declined to buy one** |

The stitch is sound: every roll gap is positive and scales with price (+16 pts at $1,930 →
+60 pts at $4,080), which is gold's carry, and the four largest are Aug→Dec rolls carrying
four months of it. Raw rather than back-adjusted is immaterial here and arguably better —
ORB is intraday, no roll falls inside a session, and back-adjustment is a constant offset
within a contract era so it cannot move an intraday point distance.

**The programme therefore runs on 3.6 years, not the 5 the task asks for.**

**Seal.** Holdout 2025-09-01 → 2026-08-11 (235 days). Train 2023-01-02 → 2025-08-31 (701
days). The task's own calibration window sits inside the seal; that conflict and the
exposure taken are recorded in D2.

## Phase 1 — engine

`Config()` is v1-exact; every v3 mechanism is opt-in. 24 constructed-bar self-tests pass
before any data run, as mandated. Two of them pin behaviour the engine would otherwise get
quietly wrong:

- **The ratchet cannot fill on its own trigger bar.** 1m OHLC does not order its extremes,
  so a bar that touches +1.0R and the old stop is a stop, not a +0.25R scratch.
- **Slippage costs R while *adding* points.** With an R-multiple target and an
  opposite-side stop, worse entry widens the risk, which widens the 1.5R target by 1.5× as
  much. The trade banks more points and earns less R. This is precisely why the skill puts
  R first, and it is now a test rather than a footnote.

The consec-loss breaker resets **weekly**, and the test asserts the reset as hard as the
halt — the v2 Pine latch that reset only on a win is the named cautionary case.

## Phase 2 — calibration: passed on structure, and the gate is not computable as written

**The 116-trade export was not supplied.** Only the aggregates in `references/tv-findings.md`
are available — no timestamps, no directions, no per-trade points. The literal
trade-for-trade ≥90% gate cannot be evaluated. What follows is every aggregate that *was*
published, plus the landmarks and the weekday fingerprint.

**One real spec item was recovered from the diff.** With no entry cutoff the engine ran
entries to 16:00 against TV's 11:45. Setting the M3-base 12:00 ET cutoff reproduces TV's
envelope **exactly** — last entry 11:45. That is a genuine calibration find, not a fit.

| metric | TV | engine | gap |
|---|---|---|---|
| trades | 116 | 112 | 4 business days of data missing |
| **last entry** | **11:45** | **11:45** | **exact** |
| multi-trade days | 0 | 0 | exact |
| win % | 52.6 | 48.2 | 4.4 pp |
| profit factor | 1.14 | 1.09 | 0.05 |
| EV R/trade | 0.07 | 0.06 | 0.01 |
| median stop | 21 pts | 23.3 pts | 11% |
| stop exits | 31.0% | 33.9% | 2.9 pp |
| target exits | 20.7% | 25.9% | 5.2 pp |
| **Mon** | n=25, 32% WR | n=24, 33.3% WR | **near-exact** |
| Tue / Fri WR | 65% / 70% | 60.9% / 63.6% | 4–6 pp |
| **largest single loss** | **−$9,623** | **−$9,900** | **2.9%, same date** |

The weekday fingerprint and the largest loss landing within 3% on the same day
(2026-03-03) are the hardest things here to match by coincidence.

**Both nominated residual classes turn out to be null.** TV's same-bar both-hit optimism
cannot explain anything: an opposite-side stop and a 1.5R target are 2.5 opening ranges
apart, and **no bar — 1-minute or 15-minute — ever spanned both** in the whole window, so
the optimistic and pessimistic runs are byte-identical. A ±1-tick fill is 0.4% of a 23-point
stop. The residual is therefore *not* in the two places the briefing expects it.

**Where it actually is: the data feed, on extreme wicks in the opening range.** The two
landmark trades match on outcome and diverge on geometry — 2026-03-03 is −$9,900 against
−$9,623 (3%) while the recorded OR is 83.8 pts against ~101. Median stop runs the other way
(mine wider, 23.3 vs 21). So the feeds agree on the typical day and disagree on the extremes
— which is exactly where the pathology trades that motivated the 30-point cap live.

**One published figure is internally inconsistent and should not be used.** TV's MFE ladder
says 14% of trades reached ≥1.5R MFE while 20.7% of trades *hit a 1.5R target*. A trade
cannot hit the target without reaching it. Recomputing on flat-exits-only (44/18/2/0%) does
not reconcile it either. Flagged rather than matched against.

**Judgement:** calibrated enough to measure with; residual located and named. If the CSV is
supplied, run the literal diff before anything is promoted to demo.

## Phase 3 — train sweeps, and nothing clears the bar

2023-01-02 → 2025-08-31, one variable at a time, R leading. Costs are **per side**: "1 tick"
is a $20 round turn, "2 tick" is $40.

| config | n | win % | **EV (R)** | 95% CI | pts/trade | PF | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| **v1-exact baseline** | 656 | 47.3 | **+0.027** | [−0.049, +0.101] | +0.19 | 1.06 | +0.001 | +0.029 | +0.063 |
| skip Monday | 527 | 48.0 | **+0.046** | [−0.035, +0.130] | +0.21 | 1.06 | +0.039 | +0.055 | +0.043 |
| anchor 08:20 | 681 | 45.4 | +0.016 | [−0.066, +0.091] | **+0.41** | **1.11** | −0.012 | −0.030 | **+0.127** |
| target 1.25R | 656 | 48.5 | +0.013 | [−0.056, +0.083] | +0.11 | 1.03 | −0.029 | +0.017 | +0.071 |
| ratchet 1.0→+0.25R | 656 | 50.6 | +0.012 | [−0.053, +0.078] | +0.07 | 1.02 | −0.012 | +0.008 | +0.052 |
| VWAP gate | 526 | 46.8 | +0.011 | [−0.068, +0.092] | +0.16 | 1.05 | −0.039 | +0.009 | +0.100 |
| time stop 90m | 656 | 46.5 | +0.009 | [−0.052, +0.071] | −0.02 | 0.99 | −0.020 | +0.006 | +0.058 |
| prior-day-close gate | 455 | 45.9 | +0.002 | [−0.086, +0.087] | +0.15 | 1.04 | −0.074 | +0.016 | +0.109 |
| target 1.00R | 656 | 50.6 | −0.000 | [−0.068, +0.065] | +0.00 | 1.00 | −0.037 | +0.006 | +0.044 |
| **anchor 03:00 London** | 687 | 42.5 | **−0.045** | [−0.126, +0.037] | −0.21 | 0.92 | −0.039 | −0.080 | +0.002 |

Risk cap (25/30/40, cap and skip) and the two breakers are omitted from the table because
they are **inert** — every one reproduces the baseline to three decimals.

**At 2 ticks per side every cell goes negative** except skipMon (+0.008). Baseline −0.009.
London falls to −0.087 with a CI of [−0.164, −0.008] — the only interval in the entire study
clear of zero, and it is on the wrong side.

### Against the gate (D4: EV ≥ +0.10R, PF ≥ 1.3, n ≥ 200, neighbour-stable, survives 2 ticks)

| requirement | best achieved | verdict |
|---|---|---|
| EV ≥ +0.10R | +0.046 (skipMon) | **fail** |
| PF ≥ 1.30 | 1.11 (08:20) | **fail** |
| n ≥ 200 | 656 | pass |
| survives 2 ticks | baseline −0.009 | **fail** |

**Phase 4 is not unlocked.** The 2025-09-01 → 2026-03-01 stretch of the seal remains
untouched.

### Predictions, marked against D6

1. *Plain ORB on gold is flat or negative* — **confirmed.** +0.027R at 1 tick, −0.009 at 2,
   interval straddling zero throughout.
2. *08:20 beats 09:30* — **split, and the split is the point.** 08:20 is the best cell in
   dollars (+$28,175 vs +$12,440) and the only PF above 1.10, while being **worse in R**
   (+0.016 vs +0.027). Skill rule 1 says R leads, so 08:20 does not win. It is also
   concentrated in 2025 (−0.012 / −0.030 / **+0.127**), which fails neighbour-stability on
   its own.
3. *1.5R is too far; 1.0–1.25R should score better* — **refuted.** Both shorter targets are
   *worse* on train (1.25R +0.013, 1.00R −0.000, against 1.5R's +0.027). The MFE ladder that
   motivated the change came from the 2026 window and does not generalise.
4. *The cap helps dollars, not R* — **confirmed, and it does neither here**, because it
   never fires. See below.
5. *skipMon will look good and is not evidence* — **confirmed, and worse than predicted.**

### The placebo that kills skipMon

| | EV (R) | 95% CI |
|---|---|---|
| skip nothing | +0.027 | [−0.043, +0.097] |
| **skip Wednesday** | **+0.063** | [−0.018, +0.147] |
| skip Monday | +0.046 | [−0.037, +0.125] |
| skip Tuesday | +0.029 | [−0.047, +0.110] |
| skip Friday | +0.003 | [−0.080, +0.084] |
| skip Thursday | −0.005 | [−0.089, +0.077] |

**Skipping Wednesday beats skipping Monday.** On train the worst day is Wednesday
(−0.115R) and the best is Thursday (+0.150R, the only weekday interval clear of zero). The
2026 window says Monday is worst and Friday best. **The weekday effect does not replicate
across eras** — it inverts. Three different days "help" when removed, all with intervals
spanning zero, which is what multiplicity looks like.

This also disposes of the D2 contamination worry: what the seal leaked does not hold on
train anyway.

## The finding underneath all of it — gold's opening range quadrupled

| year | days | median OR | p90 | median as % of price | median OR in $ | days whose OR alone > the 30-pt cap |
|---|---|---|---|---|---|---|
| 2023 | 257 | 4.5 pts | 8.4 | 0.23% | $450 | **0.0%** |
| 2024 | 259 | 6.3 pts | 10.4 | 0.26% | $630 | **0.0%** |
| 2025 | 258 | 10.2 pts | 18.9 | 0.30% | $1,015 | 3.1% |
| 2026 | 157 | 18.5 pts | 37.6 | 0.40% | $1,850 | **18.5%** |

A 4.1× rise in points and a 1.7× rise as a share of price, so it is not merely gold going
from $1,900 to $4,600 — the opening fifteen minutes got genuinely more violent.

**This is why the v3 mechanisms measure as inert or harmful.** They were designed against
Mar–Aug 2026, where the median stop is 23 points and 18.5% of days blow through a 30-point
cap. On train the median stop is 8.1 points and **4 trades out of 656 (0.6%)** risk more
than 30. A cap that never fires cannot help; a ratchet calibrated to 2026's excursions
scratches 2023's winners early.

It also reframes the calibration residual. The two eras are different enough that a
mechanism tuned on one should not be expected to transfer, and the honest reading of the
whole v3 package is that **it is a fix for the 2026 regime, validated on the 2026 regime,
and untested anywhere else.**

## What to do next, in order

1. **Get the 116-trade CSV** and run the literal trade-for-trade diff. It is the one gate in
   this programme that was specified and could not be executed.
2. **Re-cut train and holdout on volatility, not the calendar.** A 2023–2025 train and a
   2026 holdout are not the same market. Either normalise the stop by ATR or ban
   cross-regime promotion outright.
3. **Do not spend more on the v3 mechanism grid** until (2) is settled — on train they are
   measuring nothing, and on 2026 they cannot be measured without breaking the seal.
4. Commission is still **not modelled** ($0). Every number above needs a further ~$2–4 per
   round turn before it is real, which moves the 1-tick baseline to roughly break-even and
   the 2-tick book further under.

Per the repo's non-negotiables and the skill's rules: no parameter was tuned to improve a
number, every swept value is published including the ones that lose, the UNDEFINED
parameters were enumerated rather than silently defaulted, and the two figures that could
not be reproduced (TV's MFE ladder, the landmark OR widths) are reported as unreconciled
rather than quietly dropped.
