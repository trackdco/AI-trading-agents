# PREREG — LQV-01, the liquidity vacuum. Slot 1, clean slate.

**Committed before any number exists.**

Date: 2026-08-05
Family: `LQV-01`
Authorises: `scripts/lqv_census.py`

---

## 0. Why this is a clean slate and not a rework

ANGUS 2026-08-05: *"i keep telling u man we need to go clean slate and just build models.
why are we still trying to rework old models to make them profitable"*.

**Nothing here derives from the canon.** No BB, no VWAP band, no POC, no confluence
cluster, no rejection block, no displacement-through-a-level. The trigger does not read a
price level at all.

**And it is rare by MECHANISM, not by filtering.** Every model in this repo fires on a
common event and filters down — 33 triggers a session becomes 5 setups becomes 1 trade.
That hands all the work to the filter, which is exactly where overfitting lives, and it is
why every search collapses to a sample too small to survive its own null. Here the
population *is* the edge: if it fires ~1/day it is because book depletion happens ~1/day.

## 1. The mechanism

Resting liquidity is what stops price. When the resting size on one side of the book
**collapses relative to its own recent norm** while the other side holds, the market has
lost its brake in one direction. Price then travels into the thin side cheaply — not
because anyone is aggressive, but because there is nothing in the way.

This is a **liquidity** claim, not a directional-conviction claim. That distinction
matters: it does not require predicting intent, only measuring what is there.

**It is also invisible on a chart.** It cannot be inferred from OHLCV. That is the point —
an external falsification study on MNQ (14 signal families, 947 days) found every common
OHLCV intraday signal produced 0.07–1.50 gross points per trade against 2-point friction,
none deployable. **Bars cannot clear costs on this instrument.** Depth is the one input we
hold that most participants do not.

## 2. Data, and its hard limitation stated up front

`data/reference/depth_london` (295 days) and `depth_2025` / `depth_2026` (254 days) —
MBP-10, ten levels per side, **one snapshot per minute**.

**Minute resolution is a real constraint and it is declared here, not discovered later.**
True depletion happens in seconds. What we can measure is depletion *persisting across a
minute boundary*, which is a strictly weaker and slower signal. If `LQV-01` fails, that
failure does not close the concept — only this resolution of it.

## 3. The trigger — every threshold relative, nothing absolute

At each minute `t`, per side, within a band of the mid:

- `rest[side]` = total resting size within the band
- `norm[side]` = trailing median of `rest[side]` over the prior `W` minutes, **same session,
  strictly before t**

**VACUUM fires when, at minute t:**
1. `rest[thin] / norm[thin]` is in its bottom declared quantile — that side has emptied
2. `rest[thick] / norm[thick]` is at or above its median — the other side has *not*, so
   this is asymmetric depletion and not a general liquidity drought
3. the asymmetry is **new** — condition (1) was false at `t-1`, so each episode is counted
   once rather than every minute it persists

**Direction: into the thin side.** Nothing to stop price that way.

**No absolute constants anywhere.** Every threshold is a trailing quantile, so the model
adapts to volume regime by construction rather than needing recalibration. This is the
specific defect that made the canon un-adaptive — `Q_WALLSZ_MIN = 7.0`, `LON_FAR_MIN = 4.5`,
`LON_ASIA_MIN = -748.0` are all frozen 2025 numbers.

## 4. What L0 measures, and the declared kill line

**This rung is a census. It measures the EVENT, not a P&L, and it can only kill on the
premise** (§5.9.1).

Reported: events per session, per era, per session-hour; the depletion depth; and — the
mechanism test — **the forward path after the event, in the thin direction and against it,
at t+5 / t+15 / t+30, versus a same-session random-minute control.**

**KILL LINE, declared before the run:**

- **fewer than 0.5 events per session** — too rare to be a slot, even a selective one; or
- **the forward move into the thin side does not beat the random-minute control** at any
  horizon in **both** eras — the mechanism is absent and no entry rule can rescue it.

Anything else is carried forward. No expectancy claim is made at this rung in either
direction.

## 5. The bar this family must eventually clear (§ the prop scoreboard)

`src/validation/prop_score.py`, and it is not negotiable downstream:
**net ≥ 4 pt/trade after 2pt friction** (design target +10), **T ≥ 2**, **N ≥ 200**,
**green days ≥ 55%**, **max day ≤ 30%** of profit, every year green.

Slot 1 is expected to contribute **~1 trade/session**. Frequency for the book comes from
running several uncorrelated models, not from loosening this one — established today: 14
of 14 common signal families fail on MNQ because a small per-trade edge cannot pay 2-point
friction.

## 6. Sealed

The 2023/24 sealed days and `depth_london_2023_24` are **untouched** and stay that way
until a candidate has earned its one look.

---

## 7. AMENDMENT (2026-08-05, before any result was read)

**The first implementation did not match this prereg and produced zero events.**

§3 declares the thin side must sit in *"its bottom declared quantile"*. The code compared
the ratio to a fixed **0.25** — an **absolute threshold**, which is precisely the defect
§3 exists to prevent, written into the first script authorised by this document.

It was also unreachable. Measured over five sample days, the ratio of a side's resting
size to its own trailing median has **min 0.562 and 1st percentile 0.645** — aggregating
ten levels across ±10 points smooths out the collapse the trigger is trying to see. A
0.25 cut can never fire, and the census duly reported the premise dead.

**Corrected to what §3 actually declared:** `rt` is judged against **its own trailing
distribution** — bottom decile over a 60-minute window, shifted so the cut is computed
strictly before the minute being judged.

**This is implementing the prereg, not moving the goalposts.** The declared quantity was
always a quantile; the code was wrong. Recorded here rather than silently patched, and
the kill line in §4 is unchanged.

**Carried forward as a real limitation:** aggregate depth across ten levels is far more
stable than expected. If the corrected version also finds nothing, the honest reading is
that *depletion is not visible at this aggregation* — top-of-book would be sharper — and
that is a finding about the measurement, not about the market.
