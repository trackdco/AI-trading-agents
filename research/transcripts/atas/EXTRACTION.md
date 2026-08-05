# ATAS_EN — extraction from 5 transcripts

Transcripts pulled and cleaned in this directory. Pipeline: transcript → mechanical spec →
dedupe against dead families → feasibility → prereg. **This document is stage 2–3.** No
trial has been spent and nothing has been tested.

**Result: 4 of 5 videos yield nothing testable. 1 yields a single falsifiable claim.**

---

## Video-by-video

### `jVomJTjmxL4` — SMC & Order Flow Strategy (83k views, the channel's biggest)

**Genuinely mechanical**, to its credit. Four declared entry conditions:

1. Candle closes positive (long) / negative (short)
2. **Delta direction** — "significant positive bias like +1355" long, "−1678" short
3. **VPOC** — candle must close *above* the volume point of control for longs, below for shorts
4. (fourth condition, later in the transcript)

**Verdict: ALREADY DEAD.** Condition 2 is `delta at the entry bar × direction` — that is
**LDN-FLOW-01's CONFIRM measure verbatim**. We measured it at **AUC 0.509 / 0.467** against
0.5 for a coin flip, and ρ was *negative in both eras*. Condition 3 is a volume-profile
level filter — **LDN-VT-01**, where naked POCs were touched 49.1% vs 50.9% for an arbitrary
equidistant level.

The channel's most popular strategy video is two of our measured nulls stacked.

### `ozgcDPrBxI4` — RAIN Footprint Strategies (78k views)

RAIN = **R**eversal, **A**bsorption, **I**mbalance, **N**on-belief.

- **Reversal** — "price returns to the POC of the signal candle" at a level (weekly high,
  monthly open, order block, volume profile level) → **LDN-TRAP-01**, well-powered null,
  n=161/89.
- **Absorption** → **LDN-DEF-01**, all three measures FAIL, n=99/89.
- **Imbalance** — footprint diagonal imbalance, same aggressive-flow family as LDN-FLOW-01.
- **Non-belief** — low participation at the extreme; closest to our EFFORT measure, null.

**Verdict: ALREADY DEAD**, three of four legs directly, the fourth by family.

### `DAImaXN51b0` — Stops Hunting, Icebergs and Sweeps

**Verdict: NOT A STRATEGY, AND NOT TESTABLE.**

This is a settings tour — filters, colours, alert configuration, display modes. There is no
entry rule, no direction, no stop, no target, no claimed edge anywhere in 1,571 words.

It is also **structurally out of reach**. The video's own opening explains why: *"MBO shows
every order inside that volume separately… This is where everything else comes from,
icebergs, stops, sweeps."* Iceberg and stop-run detection require **market-by-order** data —
individual order placement, partial fill and refill. **We hold none.** Our depth is MBP-10
aggregated, one snapshot per minute. This is exactly the limitation recorded in
`VERDICT-LDN-FLOW-01.md` §6 and `FINDING-depth-snapshot-lookahead.md`.

The one near-claim — *"spikes that likely represent seller stop losses… often appeared near
the end of corrections… good low-risk entry points in the direction of the trend"* — carries
"likely" and "often" and no specification.

### `WzV0PPsx3Xg` — Why is the HEATMAP so Good (34 min)

Product explainer. Same MBO/full-book dependency. Nothing extracted.

### `i50dCxemLko` — Use THIS Tool to Increase Your Win Rate (Heatmap)

The only video that yields a testable claim, and the most instructive one to read carefully.

**It disclaims itself up front:** *"A heat map isn't a strategy on its own. It's the
confirmation layer."*

**It is post-hoc narration.** Every example is retrospective — "look at this reaction, you
could have opened here." The presenter says outright: *"I don't know what was there, but it
doesn't matter. I can actually decode the situation at the chart."*

**And it is unfalsifiable as presented — its own examples contradict the thesis twice:**

> *"The price moved very aggressively… did not react to this waiting of 390 orders, actually
> 440 orders at the moment of approaching the area."*

> *"The price came to this level and broke through as if there was nothing at all."*

Both times, the framework absorbs the failure: the broken level is re-explained as
resistance-turned-support and the story continues. **A framework that explains both the
reaction and the non-reaction predicts nothing.** That is the single most important
observation in this extraction.

**Timeframe also rules it out as given:** 30-second charts, 3–4 tick stops, 2–5 minute
holds. We have 1-minute bars and 1-minute depth snapshots. Not testable at that resolution.

---

## The one survivor — a falsifiable claim worth extracting

Strip the narration and one real, testable proposition remains:

> **A price level carrying a large stack of resting limit orders is more likely to produce a
> reaction than a level without one.**

**Why this one is worth having:**

- **Falsifiable**, and directionally specific.
- **Computable on data we hold.** The MBP-10 files carry `bid_sz_00..09` / `ask_sz_00..09`
  **and `bid_ct_00..09` / `ask_ct_00..09`** — size *and order count* at ten levels, 295 days,
  covering exactly 08:00–10:00 London. The video's own "press control for 395 waiting
  orders" is the count field.
- **Genuinely untested by us.** Every previous null measured *aggressive* flow — traded
  volume, delta, absorption. This measures **passive resting intent**, a different
  information family. Nothing in LDN-FLOW-01 or LDN-DEF-01 speaks to it.
- **The source's own evidence is mixed**, which is a reason to measure rather than assume.

**Known limits before anyone gets excited:**

- One snapshot per minute. Resting size can be posted and pulled inside a minute and we
  would never see it — so this tests *persistent* resting liquidity only.
- **The depth look-ahead defect applies** (`FINDING-depth-snapshot-lookahead.md`): snapshots
  labelled `HH:MM:00` hold `HH:MM:59` state. **This claim cannot be honestly tested until
  that is fixed**, or it would read the book *after* the reaction it is supposed to predict.
  That is a hard blocker, not a caveat.

---

## Recommendation

**Do not prereg anything from this channel yet**, for one reason: the only survivable claim
depends on depth data that currently carries 59 seconds of look-ahead. Fix the condenser
first, then run a free feasibility count on the resting-liquidity claim.

**Hit rate to record: 5 transcripts → 4 dead or untestable → 1 claim, itself blocked on a
data fix.** That is a normal and healthy yield, and it cost zero trials. The channel is a
vendor teaching its own product; the two most-watched strategy videos are stacks of things
this desk has already measured at coin-flip separation.
