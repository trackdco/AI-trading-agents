---
date: 2026-08-06
status: RESEARCH — extracted rules, none tested yet
tags: [htf-bias, ict, premium-discount, po3, midnight-open, timing, research]
source: JadeCap "The Only ICT Daily Bias Video You'll Ever Need" (x4FJVEZUXhc, 137k views)
corpus: research/youtube/transcripts/ (110 cached)
---

# Higher-timeframe bias — the rules, stated mechanically

ANGUS 2026-08-06: *"i was very good at predicting how days would come out, and it obviously
is something the mechanical layer doesnt have… the big problem with raw data is its every
trigger, and that includes shorting when a trigger fires on heavy bullish days, and longing
when a trigger fires on heavy bearish days."*

`research/findings/the-geometry-frontier.md` established why this matters: 33 recorded
variables, 93 buckets, **1 above zero and that one is zero**, because every variable we hold
is a proxy for target distance. Escaping that needs information that is not a restatement of
where the levels are. **These rules are that kind of information.**

Source note: the $2.5M-in-four-months claim is marketing and is irrelevant. The rules are
testable whether or not the claim is true — that is the entire point of how we work.

---

## Step 1 — Premium / discount within a dealing range

- **Swing points** are a 3-candle pattern on the DAILY: a swing high has a lower high either
  side; a swing low has a higher low either side.
- Anchor the range from the swing high to the swing low. That is the **dealing range**.
- **Above 50% = premium → favour shorts. Below 50% = discount → favour longs.**
- He gives a simpler variant explicitly: use the **previous day's high to low** as the
  dealing range. That version needs no swing detection and is trivially mechanical.

> *"if we are in a premium and I'm expecting the market to go down now all of a sudden I have
> a bias… then your bias leads into trade setups on the low time frame."*

## Step 2 — Power of three, delineated at the MIDNIGHT open

Each daily candle is open → manipulation → distribution:

- bullish day: open → **low** → high → close
- bearish day: open → **high** → low → close

> *"I always use midnight as my delineation."*

- **Bearish bias → only look to short ABOVE the midnight open.**
- **Bullish bias → only look to buy BELOW the midnight open.**

> *"a lot of people get caught off guard by trying to short into weakness and buy into
> strength. And really, you have to flip your mindset to doing the opposite."*

## Step 3 — Timing, which he rates as important as the bias itself

**If the expected move has already happened, stand aside.** This is the part most people drop,
and it is the part closest to what Angus does by eye.

> *"If we're trading above a previous day's high, and this is 9:00 a.m. — if I have a bullish
> bias and we're trading up here at 9:00 a.m., that is not a good sign for me to go long."*

> *"Maybe the move's already occurred during that specific day and you should sit it out."*

- Bullish bias + previous day's high **already taken** before your session → no trade.
- Bearish bias + previous day's low **already taken** before your session → no trade.
- He also notes distrust when the intraday extreme prints in **London** while he expects the
  New York move — a session-timing mismatch.
- News: with CPI the next day, he trades **only post-release**.

---

## Three variables this gives us, none of which are in the scan

All are causally clean — knowable at order placement, from strictly prior or
already-completed information.

| variable | definition | why it is not geometry |
|---|---|---|
| `pd_position` | where the trigger price sits within the prior day's high–low range (0 = low, 1 = high) | a statement about **location in the auction**, not about distance to the next level |
| `vs_midnight_open` | trigger price above/below the 00:00 ET open, signed to trade direction | encodes whether you are **fading or chasing** the day's move so far |
| `already_moved` | has the prior day's high (for longs) / low (for shorts) already been taken today, before this trigger? | the direct test of *"the move already happened"* — pure timing, no level distance in it |

`already_moved` is the one I would bet on. It is the only variable in this project that
directly encodes **whether the day's expected move has been spent** — and it is exactly what
Angus means by predicting how a day comes out. Nothing in the current book knows it.

## What must NOT be assumed

- The daily bias direction itself (premium → short) is a **hypothesis to test, not a given**.
  Our own trend proxy separated nothing (win rate 22.4–22.8% in every bucket), and the 80%
  rule failed at ~20% on our data against a claimed 80%. Published bias rules have a poor
  record here.
- Test **each variable separately first**. `pd_position` and `vs_midnight_open` are partly
  redundant, and stacking them before either is proven is how the alignment score died
  (corr with net = +0.032, every bucket negative).
- Same two declared bars as the separator scan: **era-consistent 2025 and 2026 independently**,
  and **monotonic** across buckets. Then a family-wise permutation null before any of it is
  called a finding.

## Build order

1. `already_moved` — cheapest, most orthogonal, and the closest match to what Angus does.
2. `vs_midnight_open` — one join, needs the 00:00 ET price.
3. `pd_position` — needs prior-day H/L, already available in `daily_context`.
4. Only if one survives alone: the bias direction rule (premium → short).
