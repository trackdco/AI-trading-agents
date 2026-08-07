---
date: 2026-08-05
status: active
tags: [london, session-structure, pattern-taxonomy, research-sweep, youtube]
sources: ["https://www.youtube.com/watch?v=e6TIug9jQQs", "https://www.youtube.com/watch?v=60d85BdZ6_E", "https://www.youtube.com/watch?v=7jCUl1Bh89Q", "https://www.youtube.com/watch?v=SypN7HcXEpg", "https://www.youtube.com/watch?v=Ez_-e5D4uZs", "https://www.youtube.com/watch?v=ZrMW4xPMLOs", "https://www.youtube.com/watch?v=qdZA2tTwwDE", "https://www.youtube.com/watch?v=qJ4N1ZwPmds", "https://www.youtube.com/watch?v=NCLK9allGv8"]
---

# Tradesharpe — the method, from his own courses

Extracted from 51 cached transcripts (~1.1M chars), principally the four
full-length courses (2023, 2024, 2025, 2026 editions) plus the strategy
breakdowns. **The London-session-specific videos are still queued** — YouTube is
rate-limiting this IP to ~25 transcripts per cooldown window. So this is his
*general* method; the session-specific detail follows.

He is the most relevant of the four channels to this lane: he streams the
London session live, claims *"my public track record of every single trade I've
taken in London session over the past 3 years done on YouTube live from entry to
exit"* [`e6TIug9jQQs` @ 1:40:37], and 815 archived streams back that up.

---

## 1. The session window — and it is not what the title of every ORB video says

> *"How do we know what time to trade? So my rule of thumb is many people think
> London open is the best time to trade. **It's actually false. I like to trade 1
> hour before London open and during London open and only an hour after.** So
> trading a session doesn't mean you get to trade the whole session."*
> — [`7jCUl1Bh89Q` @ 16:00]

> *"my best time for London is going to be probably **just after Frankfurt
> Open**."* — [`e6TIug9jQQs` @ 1:23:56]

> *"you need to be trading in times of volume. London open, New York open, these
> times here. And recently **Asian Open has been great on gold**."*
> — [`e6TIug9jQQs` @ 1:08:46, repeated verbatim in `ZrMW4xPMLOs` @ 14:23]

**Why this matters to us specifically.** One hour before London open through one
hour after is roughly **02:00–05:00 ET**. Our London substrate window is
03:00–06:00 ET. **His window is shifted an hour earlier than ours and ends where
ours is still running.** If his edge is real and concentrated where he says it
is, our current window would capture its back half and miss its front.

That is a cheap, high-value thing to check against the substrate we already
have. **Measured — see `research/findings/london-window-LDN-WIN-01.md`.** He is
directionally right, and the correction is at the back end: the measured core is
03:00–05:00 ET, and our window's last hour (05:00–06:00) carries the worst
efficiency readings in the whole session.

Use `euro_open_clock` for the anchor, not `euro_open_det` — the latter turned
out to be noise (`docs/FINDING-euro-open-det-is-noise.md`).

---

## 2. 🔴 LTA — "Low Traffic Area", and what it is really describing

His central location concept, defined twice, near-identically, in both the 2025
and 2026 courses:

> *"**LTA stands for low traffic area**... It's basically **clean candle zones**.
> It's basically where we don't have support and resistance between one zone and
> another... this would be an LTA here — these are all bearish candles back to
> back, and the reason why this is an LTA is because we have all clean candles
> here. So if you look at this, you will see that **there's nothing stopping
> price in this zone**."* — [`e6TIug9jQQs` @ 22:05–23:15, `60d85BdZ6_E` @ 32:24]

With an explicit invalidation:

> *"that would create a resistance here and this would be an area where price
> could react. So essentially **that would invalidate the LTA**."*
> — [`e6TIug9jQQs` @ 23:47]

And the tradeable expectation:

> *"if we have clean candle zones, what we expect is that **a bearish LTA will
> allow us in the future to buy up to that zone**."* — [`e6TIug9jQQs` @ 23:52]

### This is the same object four traditions have each named separately

| Tradition | Name | Definition |
|---|---|---|
| Tradesharpe | **LTA** (low traffic area) | run of clean same-direction candles, no intervening S/R |
| Order-flow scalping (Fabio) | **zero prints** | footprint level where one side traded literally zero |
| Volume profile | **LVN** | price bucket with minimal traded volume |
| ICT | **FVG** | three-candle gap where price passed without overlap |

All four describe the same structural fact: **price traversed this region
without a two-sided auction, so it offers little resistance on the return, and
the market tends to come back to it.** Fabio's phrasing —
*"very inefficient because it didn't give a fair chance of one side of the
market"* [`xUyqIjCfZzg` @ 7:42] — and Tradesharpe's *"nothing stopping price in
this zone"* are the same sentence in different dialects.

**Why this is the most useful thing in this file.** Angus asked whether we can
find where one strategy's component pairs with another's. This is it, and it is
better than a pairing — it is a *single computable primitive* that four
independent sources all rely on, each with a different detection rule:

- **candle-based** (Tradesharpe's LTA / ICT's FVG) — computable from bars alone,
  available across our full 2023→2026 span including the sealed holdout
- **volume-based** (LVN) — computable from our volume profile
- **flow-based** (zero prints) — computable from `data/reference/cvd/footprint_*.parquet`

Three detectors for one claimed effect, on data we already hold. That makes the
honest first question a **measurement, not a strategy**: do these three
detectors actually mark the same prices? If they do, we have one robust
primitive and a cheap way to compute it on the bar-only years. If they disagree,
the disagreement itself tells us which one is picking up something real.

That is an event study, not a candidate, and per the S6/S8 precedent in the
prior sweep merge it should be run as one before anything gets a thesis.

---

## 3. The entry model

Stated near-verbatim in at least three separate videos [`e6TIug9jQQs` @ 40:34
and @ 1:18:46, `SypN7HcXEpg` @ 3:53, `ZrMW4xPMLOs` @ 11:26]:

1. Mark the zone (S/R levels and LTAs) — *the one discretionary joint*
2. Price trades into the zone and reacts
3. **Wait for a candle to CLOSE beyond the range** — no anticipation
4. **Entry: stop order at the break of that candle's high/low**
   — *"you can put buy stop break of this high"*
5. **Stop: below the candle that closed above.** If that candle is small,
   *"put it below the structure"* or *"below all the wicks — always safer"*
6. **Target: the next structural level.** 1:1 is frequently the stated objective

> *"We place stop loss below the candle that closes above. That's the way that we
> do it. This candle closed above here. I took it break of high."*
> — [`e6TIug9jQQs` @ 1:18:52]

### He has a geometry gate, and it is the one our failures lacked

> *"we only have like a 10 pip range and our stop loss below these lows here is
> about 36. **It makes no sense. So it's not something I would take.**"*
> — [`7jCUl1Bh89Q` @ 30:05]

He rejects a setup because the stop is large relative to the range — a
*pre-trade R filter*, not a post-hoc excuse. Worth flagging because this is
exactly the discipline whose absence killed `nypre-euro-handoff`: 78% win rate,
+0.02R, because the natural stop was the far side of a wide range. A published
strategy that already contains an R filter is a better starting point than one
that quotes only a hit rate.

Also, on waiting for the close rather than anticipating:

> *"if I took the trade and I put a stop loss below here and didn't wait for
> this, you can see now I'm not even at a one to one."* — [`e6TIug9jQQs` @ 50:32]

The wait is not caution — it is what makes the geometry work.

---

## 4. What is mechanical and what is not

| Component | Status | Our proxy |
|---|---|---|
| Session window | **mechanical** — clock rule, ±1h around the open | `euro_open_clock` in the substrate (**not** `euro_open_det`) |
| LTA / zone location | **discretionary** — "clean candles", eyeballed | candle-run detector; cross-check vs LVN and footprint zero prints |
| Trigger | **mechanical** — candle closes beyond range | 1-min/5-min bars |
| Entry | **mechanical** — stop order at break of trigger candle | trivially codable |
| Stop | **mechanical** — beyond trigger candle / structure / wicks | three declared variants, not free parameters |
| Target | **semi** — "next structural level", often 1:1 | prior-day H/L, POC, VA edges, session extremes |
| Geometry gate | **mechanical** — reject if stop large vs range | one threshold, needs a plateau check |

**One genuine discretionary joint** (zone location) and one semi (target
selection). That is a good ratio — the `01-research-dossier` heuristic says more
than about four discretionary points means a style rather than a strategy. This
is well inside that.

---

## What's usable

- The **±1h-around-the-open window**, which disagrees with our current substrate
  window by an hour and is cheap to test.
- **LTA as a candle-computable inefficiency primitive** — and the three-detector
  agreement study that follows from it. This is the highest-value item and it
  works on bar data, meaning it reaches the 2023/24 sealed holdout where our
  flow data does not.
- The **close-then-break entry with the stop at the trigger candle**, which is a
  naturally tight geometry rather than a wide-range one.
- The **pre-trade R filter** — a rule most published strategies do not have.
- The **live archive as ground truth**: 815 date-stamped streams, three years of
  London calls, alignable to our own substrate day by day.

## What's noise

- Win-rate claims (75%, 75–80%, 75–85%) quoted without R. His own geometry gate
  implies he knows this; the marketing does not reflect it.
- Prop-firm and course promotion, roughly a quarter of the education tab.
- The forex-era material. He built this on GBPJPY and gold; NQ tick value,
  spread and session structure differ, and nothing transfers for free.

## Contradictions between sources

- **His window vs ours.** He says 02:00–05:00 ET; the London substrate uses
  03:00–06:00 ET. Both cannot be the best three hours. Measurable, and worth
  measuring before any candidate is built on either.
- **His window vs the naive ORB framing.** Three channels converge on a
  session-open breakout (see `2026-08-05-channel-map-four-traders.md` §2) but
  Tradesharpe explicitly says trading *at* the open is the wrong read and the
  hour *before* matters. That is a real disagreement inside the convergence, and
  it is probably where the edge is or is not.

## Candidate leads

Still none filed, deliberately. Two measurements come first, both cheap, both on
data in hand:

1. **Window study** — does the 02:00–05:00 ET window outperform 03:00–06:00 on
   our own substrate, and is "just after Frankfurt open" separable?
2. **Inefficiency-primitive agreement study** — do candle-LTA, volume LVN and
   footprint zero prints mark the same prices, and do those prices get revisited
   more than matched controls?

Neither is a strategy. Both are the kind of thing that makes the eventual
strategy cost one arm instead of five.
