# PARITY QUESTION SHEET — Rev 2 — for Angus to complete from his own charts

**Spec-1 Step 4, Stage A. Issued 2026-08-08. N_trials: 0. Holdout sealed. Sealed workbench
result unread.**

**No computed value appears anywhere below.** Not one. The point of the exercise is that your
readings are recorded *before* you see the detector's, so a disagreement cannot be rationalised
away afterwards. The comparison is Stage B and will not be run until this comes back.

**Fill it in, save it, send it back.**

---

## What changed since Rev 1, and what you can skip

Rev 1 asked for 8 values on **P1** and you answered them; those readings are recorded in
[`PARITY-ANGUS-READINGS.md`](PARITY-ANGUS-READINGS.md) and already compared.

**Rev 2 is wider.** It asks for the *whole* level menu, Bollinger bands on **each** entry
timeframe, the 4h range, cluster spans, the HTF classification, the §7 filter checks, and the
entry / stop / target that follow. Almost all of that has never been read.

| | what to do |
|---|---|
| **P1 fields you already gave** (daily VWAP mid / ±1σ, NY VWAP mid, BB basis, session H/L, POC) | **Copy them across.** Do not re-read them. They are already recorded and re-reading them now would not be blind |
| **Everything else on P1** | New. Read it fresh |
| **All of P2 (2025-01-22)** | New. Never read |

If you only have time for one page, **do P2** — it is the page with no prior readings at all.

---

## Setup

| | |
|---|---|
| Instrument | **NQ**, front month = **NQH5** (March 2025) on both dates |
| Timezone | **US Eastern (ET)**, every time on this sheet |
| Price units | **NQ index points**, quote to the tick (**0.25**) |
| Distance units | **NQ points**, one decimal is enough |

**Two readings, at two instants:**

| | date | instant |
|---|---|---|
| **P1** | **Wednesday 2025-01-15** | **09:48 ET** |
| **P2** | **Wednesday 2025-01-22** | **09:50 ET** |

### Bar convention — read this, it is the one thing that silently breaks the whole comparison

Two different conventions are in play in this project and they describe the **same instant**.
Spelling both out so neither of us has to guess:

- **The source bars are OPEN-labelled.** A bar labelled `09:47` covers **09:47:00–09:47:59**.
  This was verified against the order book, not assumed.
- **The detector shifts by +1 internally**, so its minute label is the bar's **close** time. In
  the detector's own terms, minute `09:48` is *"the bar covering 09:47:00–09:47:59, close-labelled"*.

**Both descriptions point at the same moment.** Stated once, plainly, in the form that cannot be
misread:

> ### "As at 09:48" means: the candle covering **09:47:00 → 09:47:59** has just closed, and
> ### **nothing** from 09:48:00 onward has happened yet.

TradingView labels intraday candles by **open** time, so on your chart that is the candle
labelled **09:47**, and it must be the **last completed** candle on screen. Tick which convention
your platform uses, because a one-bar offset shows up as a systematic disagreement on *every*
field and looks exactly like an indicator bug:

- [ ] my chart labels candles by **open** time (so I stepped to the **09:47** candle for P1)
- [ ] my chart labels candles by **close** time (so I stepped to the **09:48** candle for P1)

**Same for P2:** open-labelled → the **09:49** candle; close-labelled → the **09:50** candle.

### Session convention — RTH is the entry window, NOT the anchor

Also worth being explicit about, because "RTH" appears in the spec and means something narrower
than it sounds:

| | |
|---|---|
| **RTH 09:31–16:00 ET** | the **entry window** only (§1, Amendment A1). First tradeable signal bar 09:36. Both instants on this sheet sit inside it |
| **Globex 18:00 ET (previous day) → 16:59 ET** | the **session**, and therefore the anchor for the daily VWAP and the session volume profile (§2) |
| **09:30 ET cash open** | the anchor for the **NY session VWAP** only (§2). It does not exist before 09:30 |

So: read *inside* RTH, but anchor the daily VWAP and profile at **18:00 ET the evening before**.

### Indicator settings, so we are reading the same thing

- **Bollinger Bands** — length **20**, basis **SMA**, source **close**, **2σ**
- **Daily VWAP** — standard TradingView VWAP, anchored to the CME daily session open
  (**18:00 ET**), source **HLC/3**, bands ±1σ / ±2σ / ±3σ
- **NY session VWAP** — anchored **09:30 ET**, source HLC/3, bands ±1σ / ±2σ
- **Volume profile** — **session** profile, anchored to the same **18:00 ET** session open

---

## HOW TO READ THESE VALUES — read this before you start

**Budget: 25–30 minutes per page.** Most of it is §1.

### ⚠ The one thing that will ruin the exercise if you skip it

**Several values change depending on whether the rest of the day is on your screen.** Scroll to
2025-01-15 on a normal chart and you are looking at the *finished* day. Read the volume-profile
POC off that and you get the POC **for the whole session**, not the POC as it stood at 09:48 —
a completely different number.

The affected fields:

| value | what a finished chart shows | what we need |
|---|---|---|
| **Volume profile POC / VAH / VAL** | the whole session's profile | the profile built from 18:00 ET **up to the instant only** |
| **Session high / low so far** | the day's high and low | the extremes printed **before the instant** |
| **Week-to-date high / low** | the whole week's | **up to the instant only** |
| **Any "range" you eyeball** | shaped by bars that had not printed yet | as it looked at the instant |

**Use Bar Replay.** TradingView: the ⏵ **Replay** button in the top toolbar → click the candle
named above → the chart rebuilds as if that were now. Read everything off the replayed chart.

**Everything else is technically safe on a finished chart** — VWAP and its bands, Bollinger
Bands, prior-day levels and the candles themselves are plotted per-bar, so the value sitting
above the candle *is* that candle's value. But since you need Replay for the profile anyway, do
the whole sheet in Replay mode.

*Why this matters more than it sounds: the detector was audited specifically for this failure —
computing a whole-session value and reading it back at an earlier time. It came back clean. If
your sheet has the contaminated version and the detector has the clean one, the comparison shows
a mismatch that is nobody's bug, and we spend a day chasing it.*

### If you cannot get a value

**Write "n/a" and move on. Do not estimate.** A blank tells us the comparison cannot be run on
that field, which is useful information. A guess looks like data and quietly corrupts the
result.

If you are *eyeballing* a level rather than reading a number the platform gives you, write the
number and put **"(eye)"** next to it. That is not a failure — several of these fields have no
platform indicator and your eye is the only reference there is. But we need to know which is
which.

---
---

# P1 · Wednesday 2025-01-15 · 09:48 ET

*(the candle covering 09:47:00–09:47:59 has just closed)*

## 0. Chart provenance

| | |
|---|---|
| Platform | |
| Contract charted (NQH5 / continuous / other) | |
| Did you use Bar Replay? (yes / no) | |

## 1. Level menu — every level in the spec's menu, with its price

### 1a. Cluster-eligible levels (§3)

These are the only levels that can **form a cluster**. Read every one that exists at the
instant.

| level | price | units |
|---|---|---|
| BB MA (basis) — see §2 for the per-timeframe breakdown | | pts |
| Daily VWAP — mid | | pts |
| Daily VWAP — **+1σ** | | pts |
| Daily VWAP — **−1σ** | | pts |
| Daily VWAP — **+2σ** | | pts |
| Daily VWAP — **−2σ** | | pts |
| Daily VWAP — **+3σ** | | pts |
| Daily VWAP — **−3σ** | | pts |
| NY VWAP — mid | | pts |
| NY VWAP — **+1σ** | | pts |
| NY VWAP — **−1σ** | | pts |
| Daily POC | | pts |

### 1b. Over-extension reference (§3)

Not cluster-eligible; §3 defines over-extension as a touch of these.

| level | price | units |
|---|---|---|
| NY VWAP — **+2σ** | | pts |
| NY VWAP — **−2σ** | | pts |
| NY VWAP — +3σ (if plotted) | | pts |
| NY VWAP — −3σ (if plotted) | | pts |

### 1c. Structural / target-menu levels (§6)

| level | price | units | note |
|---|---|---|---|
| Session high so far (from 18:00 ET) | | pts | |
| Session low so far (from 18:00 ET) | | pts | |
| Prior-day high | | pts | RTH or Globex? state which → |
| Prior-day low | | pts | |
| Pre-market high (18:00 ET → 09:29) | | pts | |
| Pre-market low (18:00 ET → 09:29) | | pts | |
| Week-to-date high (as at the instant) | | pts | |
| Week-to-date low (as at the instant) | | pts | |
| Prior-week high | | pts | |
| Prior-week low | | pts | |
| Volume profile — VAH | | pts | state your value-area % → |
| Volume profile — VAL | | pts | |

### 1d. HTF range extremes (§1 context TFs, §6 menu, §7 location filter)

The spec says *"1h/4h for range extremes"* and never defines the range. **How you define it is
itself a finding** — please say.

| | value | units |
|---|---|---|
| **4h range — high** | | pts |
| **4h range — low** | | pts |
| How did you determine the 4h range? (lookback, swing method, eyeball) | | |
| 1h range — high | | pts |
| 1h range — low | | pts |

### 1e. Session boxes (§2) — boundaries not stated in the spec

The spec names Asia / London / NY session boxes but never gives their hours. **Please write the
boundaries you actually use.** This is a genuine gap and your answer closes it.

| box | your start (ET) | your end (ET) | high | low |
|---|---|---|---|---|
| Asia | | | | |
| London | | | | |
| NY | | | | |

### 1f. Data extremes (§2, §6 rule 3)

We hold no economic calendar, so this is likely "n/a" — but if you know of one, say so.

| | |
|---|---|
| Any high-impact release in this session? (what, and at what time ET) | |
| High printed within 15 min of it | |
| Low printed within 15 min of it | |

## 2. Bollinger basis and bands, per entry timeframe (§1, §2)

All four entry timeframes are evaluated independently (§1 MTF arbitration), so all four are
needed.

| entry TF | BB basis (20 SMA) | upper 2σ | lower 2σ |
|---|---|---|---|
| **1m** | | | |
| **2m** | | | |
| **3m** | | | |
| **5m** | | | |

## 3. Last completed candle on each entry timeframe

The candle in force at the instant defined at the top — i.e. the last one **fully closed**.

| entry TF | its label on your chart | open | high | low | close |
|---|---|---|---|---|---|
| **1m** | | | | | |
| **2m** | | | | | |
| **3m** | | | | | |
| **5m** | | | | | |

## 4. Confluence clusters (§3)

**A cluster is ≥2 of the §1a levels within ~10 NQ points of each other.**

Two things that are easy to conflate, kept separate on purpose:

- **Membership** — which of the §1a levels are inside the ~10 pt band. That is what defines the
  cluster and its span.
- **Confluence count** — distinct level **types** touched, where the whole VWAP family counts
  **once**, BB counts **once**, POC counts **once**, structural counts **once**. That is the
  number §7's confluence minimum is tested against.

So daily VWAP mid + daily VWAP +1σ within 10 pts is a cluster of **two levels** but a confluence
count of **one type**.

| # | levels in it (name them) | lowest price | highest price | **span (pts)** | **distinct types** |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

*(Add rows if you see more. Write **"none"** in row 1 if nothing qualifies. If a cluster only
exists on one entry timeframe because of that timeframe's BB MA, say which.)*

## 5. HTF classification at this minute (§1, §4)

**15-minute chart. Swing highs and lows confirmed with 2 bars either side (fractal, N=2).** A
swing is only confirmed once 2 bars have printed after it — so at 09:48 the most recent
*confirmable* swing is necessarily some bars back.

- [ ] **uptrend** — higher high **and** higher low
- [ ] **downtrend** — lower high **and** lower low
- [ ] **range** — anything else

| | price | time (ET) |
|---|---|---|
| Most recent confirmed 15m swing **high** | | |
| The one before it | | |
| Most recent confirmed 15m swing **low** | | |
| The one before it | | |

## 6. The §7 filters, checked at this minute

Answer these even if no trigger fires — a filter that would have blocked something is as
informative as one that did not.

| filter | spec text | your reading |
|---|---|---|
| **Location** | *"no longs at HTF range top / shorts at range bottom"* | Is price at the **top** of the HTF range? ☐ yes ☐ no · at the **bottom**? ☐ yes ☐ no |
| **Confluence minimum** | *"3 counter-trend; 2 with-trend"* | Distinct types available (from §4): ______ · Is the setup with-trend or counter-trend? ______ |
| **Invalidation-at-entry** | *"trigger candle simultaneously touching the opposing ±1σ → stand down"* | Does the last completed candle touch the **opposing ±1σ**? ☐ yes ☐ no ☐ no trigger. **Which ±1σ did you check — daily VWAP's or NY VWAP's?** ______ |
| **Over-extension** | *"touch of NY VWAP ±2σ"* | Has price touched NY VWAP ±2σ this session? ☐ yes ☐ no. If yes, at what time? ______ |

## 7. Does a trigger fire at this minute? (§3, §5)

- [ ] **No trigger.** → say briefly why not, then go to §9.

  ```

  ```

- [ ] **Yes** — complete the rest.

| | |
|---|---|
| Entry timeframe it fires on | |
| If more than one TF fires, list all of them | |
| **Direction** — long / short | |
| **Type** — rejection block (§3) / displacement (§3) | |
| Which cluster (row # from §4) | |
| Pattern per §4 — **A** reversal / **B** reclaim / **B2** continuation | |

**Reminders of the two definitions, verbatim from §3:**

> **Rejection block:** entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the
> trade side of all cluster levels, (c) leaves a wick through/into them.
>
> **Displacement:** entry-TF candle whose **body closes through ≥2 cluster levels**, with
> **body/range ≥ 0.6** and **close within the extreme quartile of the candle's range**.

## 8. The resulting trade

| | value | units | note |
|---|---|---|---|
| **Entry** — E1, limit at the BB MA (§5.3) | | pts | which timeframe's BB MA? ______ |
| **Stop** — beyond the wick extreme of the trigger candle (§5.4) | | pts | |
| Stop distance | | pts | |
| Was the **10.00 pt minimum** (A5) binding? | ☐ yes ☐ no | | i.e. was your structural stop under 10 pts |
| **Target** — first opposing menu level whose front-run-adjusted distance is ≥ **1.5R** (§6.5) | | pts | |
| **Which level is the target** | | | name it from §1 |
| Target distance | | pts | after the **2.0 pt** front-run (§6.4) |
| Resulting **R** multiple | | | |

**If you would not take this trade** even though it is mechanically valid, say so and say why.
**That answer is worth more than the numbers.** It is how the two missing entry criteria
(unfilled range, liquidity swept) were found.

```


```

## 9. Anything the sheet did not ask for

A level not in the menu, a session boundary you treat differently, an indicator setting that
differs, something on the chart that changes the read. **This box is the most useful one on the
page.**

```



```

---
---

# P2 · Wednesday 2025-01-22 · 09:50 ET

*(the candle covering 09:49:00–09:49:59 has just closed)*

**Nothing on this page has ever been read.** It is fully blind on both sides.

## 0. Chart provenance

| | |
|---|---|
| Platform | |
| Contract charted (NQH5 / continuous / other) | |
| Did you use Bar Replay? (yes / no) | |

## 1. Level menu

### 1a. Cluster-eligible levels (§3)

| level | price | units |
|---|---|---|
| BB MA (basis) — see §2 for per-timeframe | | pts |
| Daily VWAP — mid | | pts |
| Daily VWAP — **+1σ** | | pts |
| Daily VWAP — **−1σ** | | pts |
| Daily VWAP — **+2σ** | | pts |
| Daily VWAP — **−2σ** | | pts |
| Daily VWAP — **+3σ** | | pts |
| Daily VWAP — **−3σ** | | pts |
| NY VWAP — mid | | pts |
| NY VWAP — **+1σ** | | pts |
| NY VWAP — **−1σ** | | pts |
| Daily POC | | pts |

### 1b. Over-extension reference (§3)

| level | price | units |
|---|---|---|
| NY VWAP — **+2σ** | | pts |
| NY VWAP — **−2σ** | | pts |
| NY VWAP — +3σ (if plotted) | | pts |
| NY VWAP — −3σ (if plotted) | | pts |

### 1c. Structural / target-menu levels (§6)

| level | price | units | note |
|---|---|---|---|
| Session high so far (from 18:00 ET) | | pts | |
| Session low so far (from 18:00 ET) | | pts | |
| Prior-day high | | pts | RTH or Globex? state which → |
| Prior-day low | | pts | |
| Pre-market high (18:00 ET → 09:29) | | pts | |
| Pre-market low (18:00 ET → 09:29) | | pts | |
| Week-to-date high (as at the instant) | | pts | |
| Week-to-date low (as at the instant) | | pts | |
| Prior-week high | | pts | |
| Prior-week low | | pts | |
| Volume profile — VAH | | pts | value-area % → |
| Volume profile — VAL | | pts | |

### 1d. HTF range extremes

| | value | units |
|---|---|---|
| **4h range — high** | | pts |
| **4h range — low** | | pts |
| How did you determine the 4h range? | | |
| 1h range — high | | pts |
| 1h range — low | | pts |

### 1e. Session boxes — boundaries not stated in the spec

| box | your start (ET) | your end (ET) | high | low |
|---|---|---|---|---|
| Asia | | | | |
| London | | | | |
| NY | | | | |

### 1f. Data extremes

| | |
|---|---|
| Any high-impact release in this session? (what, and at what time ET) | |
| High printed within 15 min of it | |
| Low printed within 15 min of it | |

## 2. Bollinger basis and bands, per entry timeframe

| entry TF | BB basis (20 SMA) | upper 2σ | lower 2σ |
|---|---|---|---|
| **1m** | | | |
| **2m** | | | |
| **3m** | | | |
| **5m** | | | |

## 3. Last completed candle on each entry timeframe

| entry TF | its label on your chart | open | high | low | close |
|---|---|---|---|---|---|
| **1m** | | | | | |
| **2m** | | | | | |
| **3m** | | | | | |
| **5m** | | | | | |

## 4. Confluence clusters

≥2 of the §1a levels within ~10 NQ points. Span = highest minus lowest. Distinct types: VWAP
family ×1, BB ×1, POC ×1, structural ×1.

| # | levels in it (name them) | lowest price | highest price | **span (pts)** | **distinct types** |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

## 5. HTF classification at this minute

15-minute chart, fractal swings confirmed with 2 bars either side.

- [ ] **uptrend**   - [ ] **downtrend**   - [ ] **range**

| | price | time (ET) |
|---|---|---|
| Most recent confirmed 15m swing **high** | | |
| The one before it | | |
| Most recent confirmed 15m swing **low** | | |
| The one before it | | |

## 6. The §7 filters, checked at this minute

| filter | your reading |
|---|---|
| **Location** — at HTF range top? ☐ yes ☐ no · at range bottom? ☐ yes ☐ no | |
| **Confluence** — distinct types available: ______ · with-trend or counter-trend: ______ | |
| **Invalidation** — last completed candle touches the opposing ±1σ? ☐ yes ☐ no ☐ no trigger · which ±1σ: ______ | |
| **Over-extension** — NY VWAP ±2σ touched this session? ☐ yes ☐ no · time: ______ | |

## 7. Does a trigger fire at this minute?

- [ ] **No trigger.** → why not:

  ```

  ```

- [ ] **Yes** — complete below.

| | |
|---|---|
| Entry timeframe it fires on | |
| All timeframes firing, if more than one | |
| **Direction** — long / short | |
| **Type** — rejection block / displacement | |
| Which cluster (row #) | |
| Pattern — **A** / **B** / **B2** | |

## 8. The resulting trade

| | value | units | note |
|---|---|---|---|
| **Entry** — E1, limit at the BB MA | | pts | which timeframe's BB MA? ______ |
| **Stop** — beyond the trigger candle's wick extreme | | pts | |
| Stop distance | | pts | |
| Was the **10.00 pt minimum** binding? | ☐ yes ☐ no | | |
| **Target** — first opposing menu level ≥ **1.5R** after front-run | | pts | |
| **Which level is the target** | | | name it |
| Target distance | | pts | after the **2.0 pt** front-run |
| Resulting **R** multiple | | | |

**Would you actually take this trade?** If not, why not:

```


```

## 9. Anything the sheet did not ask for

```



```

---
---

## What happens next — Stage B

When this comes back, **every field is compared at 1.00 point tolerance** and marked
**MATCH** or **MISMATCH**, with **both** values shown. Every mismatch is diagnosed as exactly
one of:

| | |
|---|---|
| **spec ambiguity** | the document permits both readings — the spec is the thing that needs fixing |
| **implementation bug** | the code does not do what the spec says — the code needs fixing |
| **charting difference** | platform convention, e.g. profile row count or session boundary — neither side is wrong, but it must be recorded |
| **reading error** | either side misread — including me |

Then a single verdict: **PARITY PASS** or **PARITY FAIL**.

**The detector is not assumed to be correct.** It has been wrong three times out of three on
literalism checks in this project, and your chart is the reference the specification was written
from. **The detector will NOT be adjusted to match your readings in that pass** — Stage B
diagnoses, it does not patch. And no mismatch will be softened into "close enough."

**A FAIL here is the valuable outcome.** It means the detector does not implement the strategy,
and finding that before a result is read saves the run rather than wasting it. A sheet that
disagrees with the code is worth more than one that agrees.

### Three fields matter more than the rest

- **§1a daily VWAP mid.** Every cluster is anchored to the VWAP family. If the anchor or the
  source price differs, nothing downstream can agree and every other mismatch is a consequence
  of this one.
- **§8 stop.** The detector places it one tick beyond the trigger wick, floored at 10.00 points
  (A5). If you place it somewhere structurally different, **that is the answer to an open
  question**, not a mismatch to be reconciled — and it is the single most valuable thing this
  sheet can produce.
- **§1d the 4h range.** The spec never defines it, and the §7 location filter depends on it.
  Whatever you write becomes the definition.
