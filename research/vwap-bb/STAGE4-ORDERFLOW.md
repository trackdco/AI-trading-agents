# STAGE 4 — ORDERFLOW: CHARACTERISE AND PARK

## THE CONSTRAINT, before any result

> **MBP-10 coverage is 2025-06 → 2026-07. The workbench ends 2025-01-31.
> THERE IS ZERO OVERLAP.**
>
> Of the depth data: **287 files (2025-06 → 2026-01) fall inside the SEALED holdout and are
> unreadable.** **223 files (2026-02-01 → 2026-07-22) are readable** under the
> microstructure-only ruling.
>
> **Therefore orderflow-informed stop or target rules CANNOT be developed or validated on the
> workbench.** This stage produces measurements and parked hypotheses, **not a layer to add.**

Readable window: **2026-02-01 → 2026-07-22 only.** Sealed dates fail loud —
`stage4_orderflow.py` classifies every file by its first timestamp and **refuses 287 of 510**
before parsing a row. Nothing is skipped silently.

**Deferred capability, recorded so it is not forgotten:** when the holdout is opened, its depth
data becomes readable and can validate the cost model **against the actual trades being
judged**. That is a strictly better cost validation than the post-holdout window can provide,
because it covers the same sessions the verdict rests on. Noted in `STATE.md`.

---

## WHAT THE SCHEMA SUPPORTS

**One book snapshot per minute** — the minute's last update, `ts_event` at `:00`, flags 128.

| | |
|---|---|
| **No CVD** | 3 trade records in the entire dataset |
| **No OFI** | a sum over *events*; unrecoverable from snapshots at any frequency |
| **No footprint** | needs per-price trade aggregation, which does not exist here |
| **What exists** | static 10-level depth at minute boundaries |

Everything below is a property of a **static book sampled once a minute**. None of it is flow.

Sample: **29,635 snapshots, 123 sessions, 2026-02-02 → 2026-07-22**; 5,790 of those in RTH.

---

## 1. Resting size by distance from price

| distance (pts) | n bid | med bid | p90 bid | n ask | med ask | p90 ask |
|---|---|---|---|---|---|---|
| 0.25 | 770 | 1.0 | 3.0 | 770 | 1.0 | 3.0 |
| 0.50 | 7,690 | 2.0 | 5.0 | 7,688 | 2.0 | 5.0 |
| 1.00 | 8,712 | 3.0 | 5.0 | 8,700 | 3.0 | 6.0 |
| 1.50 | 8,760 | 3.0 | 6.0 | 8,766 | 4.0 | 6.0 |
| 2.00 | 8,722 | 4.0 | 6.0 | 8,699 | 4.0 | 6.0 |
| 2.50 | 8,655 | 4.0 | 6.0 | 8,679 | 4.0 | 6.0 |
| 3.00 | 1,975 | 2.0 | 5.0 | 1,902 | 2.0 | 4.0 |

Total visible book: **bid median 33, ask median 34 contracts**; per level, median 3.0 either
side. **Symmetric to within a contract at every distance.**

> **The single most consequential number in this stage: the ten visible levels span a median of
> 5.50 points.** The A5 stop sits at 10.00 and the A4 median target at 21.3. **The entire
> visible book fits inside the stop distance.**

---

## 2. Is there more resting size at the spec's level types?

**This is the measurement that would genuinely inform target placement, and it is mostly not
computable.** Stated rather than substituted:

| level type | status |
|---|---|
| **VWAP family** | needs volume — **NOT COMPUTABLE.** This is the spec's core level type |
| **POC / VAH / VAL** | needs volume — **NOT COMPUTABLE** |
| **prior-day H/L** | needs the prior *full* session; files cover 08:00–10:29 — **NOT COMPUTABLE** |
| BB basis | approximable as a 20-period SMA of the minute-mid series — computable, but a mid-series proxy, not the bar-close BB the spec uses |
| window extremes | running high/low of the observed window — computable, but not the session extreme the spec means |

**The two level types the strategy is actually built on — the VWAP family and the volume-profile
POC — are exactly the two this schema cannot test.**

What the proxies show, against a **distance-matched control** (same absolute distance from mid,
mirrored to the opposite side, so depth-versus-distance cannot explain the result):

| level proxy | n | median size | p75 | p90 |
|---|---|---|---|---|
| BB(20) proxy on mids | 268 | **5.5** | 8.0 | 11.0 |
| window running extreme | 94 | 8.0 | 12.0 | 15.4 |
| **distance-matched control** | 268 | **6.0** | 8.0 | 11.0 |

**BB proxy vs control: 0.92×.** Slightly *less* size at the level than at a matched arbitrary
price. **No detectable concentration.** On n=268 that is not a strong negative — but it is not
the positive the hypothesis needed, and it points the wrong way.

---

## 3. Book imbalance across 10 levels

| p10 | p25 | median | p75 | p90 | mean | stdev | fraction \|imb\| > 0.5 |
|---|---|---|---|---|---|---|---|
| −0.176 | −0.091 | **+0.000** | +0.080 | +0.158 | −0.0071 | 0.1414 | **0.6%** |

n = 5,790. **The book is almost perfectly balanced at minute boundaries.** Median exactly zero,
90% of observations inside ±0.18, and a persistent lean beyond ±0.5 on six snapshots in a
thousand. Any imbalance signal would have to live in the 0.6% tail, or at a frequency this
sampling cannot see.

---

## 4. Spread by time of day — and a correction

| ET bucket | n | median | p75 | p90 | p95 | in RTH? |
|---|---|---|---|---|---|---|
| 03:00 | 3,240 | 1.00 | 1.25 | 1.75 | 2.00 | |
| 03:30 | 3,240 | 1.00 | 1.25 | 1.75 | 2.00 | |
| 04:00 | 3,690 | 1.00 | 1.50 | 1.75 | 2.00 | |
| 04:30 | 3,690 | 1.00 | 1.50 | 1.75 | 2.00 | |
| 05:00 | 450 | 1.25 | 1.50 | 1.75 | 1.75 | |
| 08:00 | 3,000 | 1.00 | 1.25 | 2.00 | 2.50 | |
| 08:30 | 3,000 | 1.00 | 1.25 | 1.75 | 2.25 | |
| 09:00 | 2,986 | 0.75 | 1.00 | 1.50 | 1.75 | |
| 09:30 | 2,945 | **0.75** | 1.00 | 1.50 | 2.00 | **RTH** |
| 10:00 | 2,944 | **0.75** | 1.00 | 1.25 | 1.75 | **RTH** |

**UNMEASURED: 10:30 → 16:00 ET.** Every file ends at 10:29 or 04:59. **This stage did not extend
the cost basis into the missing hours. It cannot.** The 0.975 base still rests on a window
holding ~9.7% of the signal population.

### Correction to the cost-basis ruling's stated reason

The ruling recorded in `STATE.md` reads: *"CONSERVATIVE BY CONSTRUCTION — the widest hour applied
everywhere."*

**The measurement does not support "the widest hour."** Of the eleven 30-minute buckets with
data, **09:30–10:29 is the tightest**, at 0.75 median against 1.00–1.25 everywhere earlier. Nine
of those eleven buckets are outside RTH and carry no signals, so within RTH only this one hour is
measured and **nothing can be established about whether it is widest, narrowest or typical.**

**The ruling's conclusion may still hold; its stated justification does not.** The weak evidence
that survives is directional: p90 falls 1.50 → 1.25 across 09:30 → 10:29, so the trend at the
right edge of the measured window is still tightening. That is an argument from a trend inside a
10% slice, not a measurement.

**This does not change the cost figure or any verdict** — the 0.50–1.50 range moves breakeven by
4.0 points at the A5 floor, less than the width of the confidence interval on the win rate. It
changes only what may honestly be said about *why* 0.975 is defensible.

---

## 5. Depth at the A5 stop distance vs the A4 target distance

| | |
|---|---|
| Visible book reaches **below** mid | median **2.62 pts**, p90 3.25 |
| Visible book reaches **above** mid | median **2.62 pts**, p90 3.25 |
| Snapshots whose book reaches 10 pts down (**the A5 stop**) | **0.28%** |
| Snapshots whose book reaches 21.3 pts up (**the A4 median target**) | **0.14%** |

**The question cannot be answered.** MBP-10 shows ten levels; ten levels span a median of 5.5
points; the stop sits at 10 and the target at 21.3. **Both are outside the visible book on
99.7% of snapshots.** Asking whether one side is systematically thinner *at those distances*
requires MBP-50 or full depth. It is not a matter of more careful analysis of this data.

---

## PARKED HYPOTHESES

Each falsifiable, each with the data it would need. **None is proposed for the spec.**

### The horizon problem, stated first because it governs all of them

The order-book literature's exploitable window is **10 ms – 10 s**. This strategy's median hold
is **5–7 minutes** — three to four orders of magnitude longer. The one peer-reviewed forward
test at 1-minute resolution reports **negative out-of-sample R²**: worse than predicting the
mean.

**Expect little.** Measuring it cheaply is still worth doing before dismissing it, which is what
this stage did. Nothing here changes that prior, and one measurement (§2, 0.92×) moves against
it.

| # | hypothesis | falsifiable as | data required | status from this stage |
|---|---|---|---|---|
| **H-OF-1** | Resting size concentrates at the spec's structural levels, so a target placed at one has a higher fill probability than a target the same distance away at an arbitrary price | Median resting size within 1 tick of a VWAP band / POC / prior-day extreme exceeds the distance-matched control by ≥25% | **MBP-10 plus 1-minute bars for the same sessions** — bars supply the levels, depth supplies the size. Neither the workbench nor the post-holdout window has both | **UNTESTABLE HERE.** BB proxy 0.92×, i.e. slightly against, n=268 |
| **H-OF-2** | Book imbalance at the signal minute predicts the direction of the next 5–7 minutes | Sign agreement > 55% between imbalance at T and price change T→T+6 | MBP-10 plus bars, same sessions | **UNPROMISING.** Imbalance median 0.000, stdev 0.141, only 0.6% beyond ±0.5 — the predictor has almost no variance to work with |
| **H-OF-3** | Thin depth on the stop side at entry predicts a higher stop-hit rate | Stop-hit rate in the thinnest depth quintile exceeds the thickest by ≥10 pts | **MBP-50 or full depth**, plus outcomes | **UNTESTABLE, STRUCTURALLY.** The stop is outside the visible book on 99.7% of snapshots. Not a sampling problem — a schema problem |
| **H-OF-4** | Spread widens materially in the afternoon, so the 0.975 base understates cost for the 90% of signals firing after 10:29 | Median RTH spread 10:30–16:00 exceeds 0.975 − 0.225 = 0.75 pt | **MBP-10 with an afternoon window.** Every held file ends at 10:29 or 04:59 | **UNMEASURED.** The single cheapest data purchase that would improve the cost model — and the holdout's own depth data would answer it for the exact sessions being judged |
| **H-OF-5** | Top-of-book size predicts slippage on a market stop exit | Realised slippage correlates with inside size at exit, ρ > 0.2 | Trade prints, which do not exist here — 3 records total | **UNTESTABLE.** Requires a trades or TBBO product |

### What the measurements did establish, independent of any hypothesis

1. **The book is thin and symmetric.** 33/34 contracts across ten levels, ~3 per level, matched
   to within a contract at every distance. There is no visible asymmetry to exploit.
2. **The book is narrower than the strategy's risk.** Ten levels span 5.5 points; the stop is
   10. **The strategy operates entirely outside the depth this data can see.** That single fact
   retires H-OF-1 and H-OF-3 on this schema, regardless of effort.
3. **Minute-boundary imbalance is near-degenerate** as a signal — median exactly zero, 0.6%
   beyond ±0.5.

---

## Accounting

| | |
|---|---|
| Files inventoried | **510** |
| **Refused as holdout-dated** | **287** — by date, before any row was parsed |
| Readable and read | **223** |
| Snapshots | 29,635 (5,790 RTH), 123 sessions |
| Holdout | **never read** |
| Strategy performance computed | **none** |
| Spec changes proposed | **none** |
| **N_trials** | **0** |

Reproduce: `python3 research/star-trading/tools/stage4_orderflow.py`
