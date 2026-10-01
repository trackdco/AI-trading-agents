# FINDINGS — loser autopsy: the hypothesis is wrong, and usefully so (2026-09-03)

His hypothesis: *"it would highly depend on the previous day's volatility and
the gap or something like that. because if one day moves hella it could be
cos of news."*

**Verdict: wrong on both counts, and backwards on the first.** Prior-session
volatility does not mark the losing days — and where it does move day-R, it
moves it *upward*, purely by handing over more trades. The gap is null.

## 0. Why a DAY-level audit can be read as a rule (the G3b exception)

G3b died because an audit bucket is not a rule effect: the rail pass is
chronological, so refusing one trade changes which trades are open for the
rest of that day. **A day filter does not have that problem.** Nothing carries
between sessions here — levels come from the prior session's *bars* (which
exist whether or not we traded), the book is flat by EOD, and `rail_pass`
groups by day. Skipping day D leaves every other day bit-for-bit identical,
so for a day-level rule the bucket **is** the effect.

That makes this audit unusually trustworthy. It is also why the Part 4/5
early-session variants below are *not* in that class and stay flagged.

**Causality gate:** every predictor is computed from bars closed at or before
the session's own 18:00 open. Prior-session features use `[prev_t0, t0)`; the
gap uses the first bar *at* `t0` only. Nothing reads the session it predicts.

**Preregistered bar, written before any result:** SURVIVOR needs, in BOTH eras
independently, ≥3.0R spread between best and worst bucket, monotone or
single-peaked ordering, and ≥120 days per bucket. WATCH at ≥1.5R. Both eras
have been read, so a survivor is a hypothesis to preregister on 2017–19, never
an adopted rule.

Sample: 1,711 session-days — 764 (2020–22) + 947 (2023–26), flat railed empire.

## 1. The losing days are not marked in advance. At all.

| group | days | mean R | WR | trades/day | prior range | prior vol ratio | \|gap\|/range |
|---|---:|---:|---:|---:|---:|---:|---:|
| worst 1% | 17 | −14.0 | 47.3% | 75.2 | 313.6 | **1.12** | 0.033 |
| worst 5% | 85 | −7.3 | 51.6% | 63.0 | 278.5 | 1.03 | 0.060 |
| worst 10% | 171 | −4.7 | 53.4% | 59.3 | 268.7 | 1.02 | 0.056 |
| **all days** | 1,711 | +10.2 | 65.3% | 74.9 | **329.1** | **1.12** | 0.056 |
| best 10% | 171 | +28.7 | 71.2% | 116.7 | 448.7 | 1.26 | 0.047 |

The worst 1% of days follow a prior session whose volatility ratio is **1.12 —
the sample average to two decimals.** Their prior range is *below* average. The
gap is smaller than average. On every pre-open measure a catastrophic day is
indistinguishable from a Tuesday.

## 2. Prior volatility does pay — but it is opportunity count, not quality

Prior range, prior median 1m candle and prior/20-day ratio all cleared the
preregistered bar (spreads 9.8/6.5, 9.3/6.4, 5.0/3.3 R per day). They are one
feature wearing three hats, and the direction is the *opposite* of the
hypothesis: **more prior volatility, more money.** Then the decomposition:

| prior vol ratio | days | day R | trades/day | **EV/trade** | WR | red days |
|---|---:|---:|---:|---:|---:|---:|
| **2020–22** | | | | | | |
| < 0.75 | 186 | +7.3 | 56.0 | +0.1308 | 64.9% | 22% |
| 0.75–1.00 | 186 | +8.5 | 65.8 | +0.1300 | 64.9% | 15% |
| 1.00–1.34 | 186 | +9.8 | 70.1 | +0.1399 | 65.5% | 15% |
| > 1.34 | 186 | +12.3 | **89.0** | +0.1388 | 65.5% | 11% |
| **2023–26** | | | | | | |
| < 0.75 | 232 | +10.3 | 71.4 | **+0.1437** | 65.7% | 12% |
| 0.75–1.00 | 231 | +9.4 | 74.2 | +0.1267 | 64.8% | 13% |
| 1.00–1.32 | 232 | +11.3 | 79.9 | +0.1416 | 65.8% | 14% |
| > 1.32 | 232 | +12.7 | **94.9** | +0.1338 | 65.1% | 7% |

**EV/trade is flat and win rate is flat.** In 2023–26 the *lowest*-volatility
quartile has the *highest* EV/trade. Trades per day runs 56→89 and 71→95: the
entire 6–10R day spread is the count. A wide prior session tells you how many
setups to expect, not how good they will be — so it is not a filter, and it
says nothing whatever about losing days.

**This is the day-level twin of the G3b lesson.** A bucket that clears the bar
on the aggregate can still be empty once decomposed. Day-R is trades × EV;
never read a day-level survivor without splitting it.

## 3. Nulls

| feature | spread (2020–22 / 2023–26) | verdict |
|---|---|---|
| \|session gap\| / prior range | 0.6R / 1.2R | **null** — flat across all four quartiles |
| day of week | 1.4R / 1.4R | null |
| prior close position in range | 3.2R / 1.5R | watch (fails 2023–26) |
| prior \|close−open\| / range | 1.7R / 1.7R | watch |

The gap is the cleanest null on the board. Quartile means in 2023–26:
+11.1, +10.0, +11.2, +11.0.

## 4. What a losing day actually is — diagnostic only

Same-session features. **Not knowable at the open, can never be a filter.**
Recorded because it explains the mechanism.

| | worst 5% | all | best 20% |
|---|---:|---:|---:|
| session range, 2020–22 | 295.6 | 293.9 | 350.8 |
| session range, 2023–26 | 311.6 | 357.3 | 398.4 |
| one-way push \|C−O\|/range, 2020–22 | 0.432 | 0.494 | 0.444 |
| one-way push, 2023–26 | 0.494 | 0.468 | **0.397** |
| trades, 2020–22 | 63.3 | 68.9 | 101.5 |
| trades, 2023–26 | 64.3 | 79.6 | 109.3 |

And by push quartile, EV/trade declines in both eras:

| push | 2020–22 day R / EV | 2023–26 day R / EV |
|---|---|---|
| lowest (choppy) | +10.0 / +0.1329 | +13.1 / +0.1447 |
| highest (one-way) | +7.5 / +0.1267 | +8.3 / +0.1239 |

Day-R spread 2.9R / 4.8R — just misses the bar in 2020–22, and is not causal
anyway. But the direction is consistent and it fits the physics: this grammar
fades an extension back to a level. **A losing day is a quiet, grinding,
one-way session with few setups** — the market never comes back, so every
resting limit fills into continuation. The *violent* days are the best days,
because violence with two-way range is round trips.

2022-11-29 (−24.6R, the worst day in either era) is the extreme case: NQ ran
11,520 → 12,077, closed on the high, 34% win rate, and **both directions
lost** (longs −13.2R, shorts −11.4R) on a day the market went straight up.

## 5. The early-session read — null once decontaminated

First 6 hours' P&L → **rest of day only** (no overlap; the first cut of this
reported whole-day R, so a good start scored itself):

| first 6h P&L | rest-of-day EV, 2020–22 | rest-of-day EV, 2023–26 |
|---|---:|---:|
| worst quartile | +0.1449 | **+0.1559** |
| best quartile | +0.1574 | **+0.1430** |
| spread | +0.0125 | **−0.0129** |

**The sign flips between eras.** Null. This reproduces the conviction audit's
finding that cumulative day P&L does not sort, and it is consistent with the
daily loss cutoff having been built and killed (it made max drawdown worse at
−20, −30 and −40pt alike).

## 6. What this means

**You cannot dodge the bad days.** Nothing available before the open marks
them, the gap is irrelevant, and volatility points the other way. The only
lever on a bad day is the one already in the spec: **size** — the dial in §32,
and arming, which cut the worst day from −24.6R to −21.0R without being aimed
at it.

Two things worth carrying forward:
1. **The count effect is real and unexploited.** Prior volatility forecasts
   *how many* setups arrive. That is not a filter but it is a capacity and
   sizing input — expect 56 trades after a quiet session and 95 after a wild
   one, at the same expectancy each.
2. **The strategy's true enemy is a narrow one-way grind**, not news. Anything
   that detects continuation *in flight* is the live research direction — and
   it changes occupancy within the day, so it needs an engine run, not a bucket.

Scripts: `scripts/loser_autopsy.py` (parts 1–2), `scripts/autopsy_p3.py`
(decomposition), `scripts/autopsy_p4.py`, `scripts/autopsy_p5.py`
(decontaminated early read).
