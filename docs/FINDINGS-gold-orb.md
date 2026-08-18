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
---

# PHASE 2, REDO — the literal trade-for-trade diff, and what it costs the v3.1 result

The v1 116-trade export never arrived. A **v3.1 export did** (75 trades, COMEX:GC1!, 15m,
2026-03-03 → 2026-08-18), and it carries per-trade direction, both timestamps, fill prices,
exit signal, MFE/MAE and P&L. That is the gate this programme could not previously run.

Config was read off the export's own Properties sheet, not guessed: target **1.0R**, entry
cutoff 150 min after anchor, **force-flat 240 min after the ANCHOR** (13:30 ET, not 240 min
after entry — the engine gained a `flat_from_anchor` mode for this), 30-pt cap, ratchet
1.0→+0.25R, time stop 90 min @0.5R, VWAP gate ON, skipMon ON, breakers ON, 1 tick/side
slippage, $3/trade commission, qty floored at 1 contract throughout.

## The diff

Our data ends 2026-08-11, so 2 of the 75 TV trades are past it; 73 are comparable.

| | |
|---|---|
| day-level match | **65/73 = 89.0%** |
| **direction, on matched days** | **65/65 = 100%** |
| entry timestamp | 62/63 = 98.4% |
| entry price | **median &#124;diff&#124; 0.00 pt** (60/63 within 5 ticks) |
| exit reason | 63/65 = 96.9% |
| per-trade P&L | median &#124;diff&#124; **$10** |
| total | $23,729 vs TV $25,161 (5.7%) |
| days we traded that TV did not | **0** — strictly a subset |

Exit-reason confusion is one cell: a single target that the engine resolved as a stop.
Stops 14/14, targets 27/28, scratches 21/21.

**The whole residual is one gate, and it is identified.** Ablation recovers 10/10 of the
missed days by dropping the VWAP gate and nothing else — not the breakers (0/10), not the
cap (0/10). TV computes `ta.vwap` on 15-minute bars; the engine computed it on 1-minute
bars. Rebuilding VWAP at 15m moves the match 86.3% → 89.0% and confirms the mechanism; the
last handful are marginal days where the two VWAPs straddle the entry price, consistent with
the feed differences already documented in the opening range.

**Verdict: calibrated.** 100% directional agreement, zero median entry-price error, 96.9%
exit-reason agreement, one named and measured residual. 89.0% is a day short of the literal
90% bar (65 of 73 against 66 needed) and the shortfall is entirely inside the explained
class, so the gate is met in substance and missed in letter. Recorded that way rather than
rounded up.

## The finding that matters more: v3.1 does not survive its own window

The exported run looks strong — 75 trades, 62.7% win rate, PF 1.56, **+$25,161**. Run the
**identical config** on 2023-01-02 → 2025-08-31:

| | 2026 window | | train 2023–25 | |
|---|---|---|---|---|
| | PF | net | PF | net |
| **v3.1 full stack** | **1.67** | **+$26,501** | **0.98** | **−$2,177** |
| bare ORB 1.0R, all mechanisms off | 1.13 | +$12,404 | 0.97 | −$6,628 |

v3.1 on train: n=419, 48.4% WR, **EV −0.000R** [−0.076, +0.069], and −$10,560 at 2
ticks/side. Every ablation sits inside that interval. The ratchet and the risk cap are
**bit-identical** to leaving them off — on train they never fire.

This is in-sample by construction, and the briefing says so itself: the 30-pt cap exists
because of trade #2 *in that window*, the ratchet because of "the giveback seven" *in that
window*, the time stop because of the flats *in that window*, skipMon because of Monday *in
that window*. Five mechanisms fitted to 116 trades, then scored on the same 116 trades'
window.

**The decomposition splits the +$25k roughly in half.** The bare strategy already makes
+$12,404 there while losing −$6,628 on train, so about half the result is the 2026 regime
being favourable to ORB at all. The other half is the mechanism stack, which lifts PF by
**+0.54 in 2026 and +0.01 on train** — a fifty-fold difference in effect size between the
window it was designed on and every other year available.

The mechanisms are not pure noise: they do move train from −$6,628 to −$2,177. They are
simply nowhere near large enough to matter once the regime that motivated them is gone.

## Consequences for the seal

The Mar–Aug 2026 window is now **irreversibly disclosed** — the user supplied a full trade
list for it. It cannot serve as holdout for anything in this programme again. What remains
sealed is **2025-09-01 → 2026-03-01 only**, roughly six months, and it is the last untouched
data on this branch. Spend it once, on a candidate that has already cleared train.

None has. Phase 4 remains unrun.


---

# PHASE 3B — four single-axis sweeps, scale-free parameters. **Nothing clears +0.10R.**

Train 2023-01-02 → 2025-08-31, 656 baseline trades over 656 days. 2010–2021 was requested
and is unavailable: the data begins 2023-01-02 and there is no Databento key. Costs now
include the **$3/round-turn commission** read off the v3.1 export, which earlier phases
omitted. Bare ORB (1.5R, no cap, no gates, no management) is re-run as the control inside
every axis. Entry window held at 150 min after each anchor so the anchor comparison is fair.

**Verdict, stated plainly as instructed: no cell reaches +0.10R on train, so nothing has
earned the holdout. Sep 2025 – Feb 2026 stays sealed.**

## Engine changes first

**The risk cap is now scale-free**, and the re-expression itself produced a finding:

| cap form | fires on train | fires in 2026 | comparable? |
|---|---|---|---|
| 30 points (v3) | 0.6% | 29.5% | **no** |
| **0.5 × prior-day ATR** | **8.8%** | **7.1%** | **yes** |
| 1.0 × prior-day ATR | 0.3% | 0.9% | yes |
| 0.5 % of price | 19.4% | 52.7% | **no** |
| 0.25 % of price | 78.4% | 93.8% | **no** |

Only the ATR form transfers. **Percent-of-price does not**, which says the 2023→2026 shift
is a change in *volatility*, not merely in price level — gold's daily range grew faster than
gold did. Eight new self-tests cover the ATR/pct caps, the four Crabel flags and the
participation features (32 total, all passing). VWAP stays on 1m.

## A. ANCHOR — the headline hypothesis is not supported

| anchor | n | win % | **avg R @1t** | 95% CI | @2t | PF@1t | $ @1t | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|
| **09:30 ET** | 656 | 47.1 | **+0.023** | [−0.050, +0.094] | −0.013 | 1.046 | +$10,472 | −0.004 | +0.025 | +0.060 |
| 08:20 ET (COMEX pit) | 670 | 45.1 | +0.008 | [−0.072, +0.088] | −0.019 | **1.099** | **+$25,705** | −0.025 | −0.036 | **+0.123** |
| 03:00 ET (London) | 660 | 42.0 | **−0.055** | [−0.139, +0.032] | **−0.094** | 0.914 | −$14,075 | −0.062 | −0.089 | +0.011 |

**09:30 is the best of the three in R.** The premise — that 09:30 is an equity convention
gold has no reason to respect — does not survive its own test. 08:20 wins on dollars and
profit factor while losing on R, the same dual-currency split as before, and it is entirely
a 2025 phenomenon (−0.025 / −0.036 / **+0.123**), so it fails stability outright.

**London 03:00 is refuted**, not merely weak: at 2 ticks its interval is [−0.172, −0.012],
one of only two cells in the whole programme clear of zero, and it is on the wrong side.

## B. CRABEL CONTRACTION — fails, and fails with the wrong dose-response

| prior day | n | win % | **avg R @1t** | 95% CI | @2t | PF | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| no gate | 656 | 47.1 | +0.023 | [−0.049, +0.096] | −0.013 | 1.046 | −0.004 | +0.025 | +0.060 |
| nr4 | 156 | 45.5 | +0.004 | [−0.148, +0.153] | −0.022 | 1.018 | −0.120 | +0.037 | +0.142 |
| **nr7** | 74 | 51.4 | **+0.116** | [−0.092, +0.334] | +0.083 | 1.324 | −0.058 | +0.175 | +0.307 |
| inside | 114 | 47.4 | −0.055 | [−0.214, +0.103] | −0.077 | 0.993 | −0.282 | +0.029 | +0.216 |
| **idnr4** | 76 | 42.1 | **−0.137** | [−0.326, +0.058] | −0.161 | **0.765** | −0.400 | −0.016 | +0.136 |

nr7 is the **only cell above +0.10R anywhere in this programme** and it fails every other
test at once: n=74, an interval 0.43R wide that straddles zero, 2023 negative, and three
neighbours at +0.004, −0.055 and −0.137. A lone spike among four variants of one idea.

The dose-response runs backwards, which is the decisive part. **ID/NR4 is the strictest
form of contraction and it is the worst cell in the entire study** (−0.137R, PF 0.765). A
real precondition gets *better* as you tighten it. Crabel's contraction filter does not
transfer to gold here.

## C. PARTICIPATION — one right shape, far too small

| filter | n | win % | **avg R @1t** | @2t | PF@2t | medRisk | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| none | 656 | 47.1 | +0.023 | −0.013 | 0.978 | 8.1 | −0.004 | +0.025 | +0.060 |
| relvol ≥ 1.2 | 413 | 47.7 | +0.021 | −0.001 | 1.012 | 11.0 | −0.012 | +0.089 | −0.034 |
| **relvol ≥ 1.5** | 306 | 49.0 | **+0.047** | +0.031 | 1.142 | 11.9 | −0.053 | +0.162 | +0.026 |
| relvol ≥ 2.0 | 195 | 47.2 | +0.008 | −0.009 | 0.890 | 14.7 | −0.017 | +0.017 | +0.027 |
| range ≥ 0.5×ATR | 655 | 47.2 | +0.023 | −0.013 | 0.978 | 8.1 | −0.004 | +0.022 | +0.066 |
| range ≥ 1.0×ATR | 631 | 47.2 | +0.028 | −0.007 | 0.997 | 8.1 | −0.010 | +0.025 | +0.097 |
| **range ≥ 1.5×ATR** | 529 | 48.2 | **+0.046** | +0.014 | 1.021 | 8.4 | −0.003 | +0.095 | +0.055 |

**Relative volume is a spike**: 1.2 → +0.021, 1.5 → +0.047, 2.0 → +0.008. Non-monotone, with
both neighbours far below the peak and 2023 negative. Not stable.

**Breakout-bar range is monotone** — +0.023 → +0.028 → +0.046 as the threshold tightens.
That is the shape a real effect makes, and it is the only clean dose-response in the whole
programme. It is also worth +0.023R over the control and dies to +0.014R at two ticks. The
billing as "best independent evidence of any filter" is directionally vindicated and
quantitatively irrelevant.

## D. OR WINDOW — the 5-minute hypothesis is refuted; the ridge is at 30–35m

| OR | n | win % | **avg R @1t** | 95% CI | @2t | PF@2t | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| 5m | 686 | 42.4 | **−0.034** | — | **−0.083** | 0.889 | −0.139 | +0.008 | +0.062 |
| 10m | 671 | 44.9 | −0.020 | [−0.098, +0.059] | −0.051 | 0.922 | −0.059 | −0.021 | +0.039 |
| 15m | 656 | 47.1 | +0.023 | [−0.046, +0.095] | −0.013 | 0.978 | −0.004 | +0.025 | +0.060 |
| 20m | 609 | 48.1 | +0.013 | [−0.054, +0.086] | −0.013 | 0.992 | −0.050 | +0.055 | +0.043 |
| 25m | 569 | 48.9 | +0.012 | [−0.054, +0.075] | −0.008 | 0.978 | +0.028 | −0.006 | +0.016 |
| **30m** | 534 | 49.4 | **+0.053** | [−0.007, +0.115] | **+0.031** | **1.156** | +0.076 | +0.015 | +0.079 |
| **35m** | 467 | 50.7 | **+0.063** | **[+0.004, +0.122]** | **+0.044** | 1.101 | +0.128 | +0.034 | +0.010 |
| 40m | 390 | 48.2 | +0.032 | [−0.029, +0.095] | +0.016 | 1.004 | +0.087 | −0.027 | +0.051 |
| 45m | 391 | 50.1 | +0.024 | [−0.033, +0.081] | +0.006 | 0.976 | +0.141 | −0.087 | +0.037 |
| 60m | 254 | 48.0 | +0.002 | [−0.063, +0.065] | −0.013 | 0.900 | +0.045 | −0.079 | +0.062 |

**The 5-minute result from the equity literature inverts on gold.** 5m is the worst OR
length tested — −0.034R at one tick, −0.083R at two — and 10m is second worst. The grid is
monotone improving from 5m to 35m and then decays.

**30m and 35m are the only cells in the programme that survive two ticks with all three
years positive**, and they are adjacent, so this is a two-cell ridge rather than a lone
spike. 35m's one-tick interval [+0.004, +0.122] is the only one on the positive side of
zero anywhere in this work. Nobody proposed either length.

### And it is not the cost denominator

Everything that helped also carried a wider stop, which mechanically lifts EV because fixed
costs enter as `cost/risk`. Tested directly:

| | spread across the OR grid |
|---|---|
| EV **after** cost | 0.083R |
| EV **before** cost | 0.067R |
| the cost term itself | **0.020R** |
| corr(median stop, EV after cost) | +0.375 |
| corr(median stop, EV before cost) | **+0.137** |

Pre-cost EV still peaks at 30–35m (+0.077 and +0.084, intervals [+0.014, +0.139] and
[+0.024, +0.144], both clear of zero). The cleanest disproof is 60m: it carries the widest
stop of all and the *worst* pre-cost EV of the upper half. The ridge is small and real, not
arithmetic — but the denominator does account for roughly a fifth of its apparent size.

## Verdict

**Nothing clears +0.10R on train, so we stop.**

The best cell in the programme is **OR 35m at +0.063R** after one tick and commission —
63% of the required expectancy — with **PF 1.101** against a required 1.30. It survives two
ticks, it is neighbour-stable against 30m, its pre-cost interval clears zero, and all three
years are positive. It is still not promotable, and 35m's 2025 is +0.010, so what edge there
is looks to be decaying.

Nine OR lengths were tested. One interval clearing zero out of nine is roughly what
multiplicity buys at 95%, and that should be weighed against the ridge before anyone treats
35m as a finding rather than a lead.

**Holdout untouched: 2025-09-01 → 2026-03-01 remains sealed.** If it is ever spent, spend it
on OR 30–35m with the breakout-range filter — the only two things here with the right shape
— and only after they have been shown to clear +0.10R on data that is not this train set.


---

# CORRECTION (19 Aug 2026) — a bias-gate defect, and every affected number moved against the strategy

Found while parameterising the engine for handover. The VWAP and prior-day-close gates
`break`-ed out of the day on the first blocked candidate; the Pine reference re-evaluates
every bar. The engine silently under-traded every gated day.

| | before fix | after fix |
|---|---|---|
| parity, day-level match | 89.0% (65/73) | **100.0% (73/73)** |
| parity, exit reason | 96.9% | 98.6% |
| v3.1 on train, EV | −0.000R | **−0.0118R** |
| v3.1 on train, PF | 0.98 | **0.947** |
| v3.1 on train, net | −$2,177 | **−$7,579** |
| v3.1 on train @2 ticks | −$10,560 | **−$17,906** |
| stack effect on PF, 2026 vs train | +0.54 / +0.01 | **+0.49 / −0.02** |

**Two things this changes.**

First, the Phase 2 conclusion that the parity residual was VWAP *granularity* — 1-minute
against TradingView's 15-minute accumulation — **was wrong.** Granularity was worth under
three points of it; the defect was worth eleven. The corrected diff is a clean 100% on days
and direction. That earlier attribution is withdrawn.

Second, the mechanism stack now **subtracts on train** (bare PF 0.97 → full stack 0.95)
while still adding +0.49 in the window it was designed on. The in-sample reading is
sharper than before, not softer.

**Nothing in Phase 3B moves.** Those sweeps ran a bare ORB control with no VWAP or PDC
gate, so the defect could not touch them. The +0.10R gate result, the four axis verdicts and
the 30–35m ridge stand exactly as published above.
