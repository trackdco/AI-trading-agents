---
date: 2026-08-05
status: reference
tags: [ny-pre, order-flow, depth-walls, structural-events, research-sweep, youtube]
sources: ["https://www.youtube.com/watch?v=xUyqIjCfZzg", "https://www.youtube.com/watch?v=tvERE-Beu2U", "https://www.youtube.com/watch?v=DyS79Eb92Ug", "https://www.youtube.com/watch?v=nn0Dx_OL24o", "https://www.youtube.com/watch?v=_mAy6q3OBZw"]
---

# Footprint scalpers, live on NQ/ES — the confirmation layer `thin-break-trap` was missing

Five sources supplied by Angus, not found by search. **677,503 characters of
transcript**, all committed under `research/youtube/transcripts/`. Three are
multi-hour live-trading sessions with running commentary, which is the highest
signal-to-noise format available — the trader narrates the read *before* the
outcome is known.

| Video | Channel | Date | Length | Views | Rule hits |
|---|---|---|---|---|---:|
| [Two World Class Order Flow Scalpers (Fabio Valentini & Carmine Rosato)](https://www.youtube.com/watch?v=xUyqIjCfZzg) | Chart Fanatics | 2026-05-17 | 3:49:37 | 233,828 | 537 |
| [#1 Scalper in the WORLD](https://www.youtube.com/watch?v=tvERE-Beu2U) | Chart Fanatics | 2025-09-21 | 3:34:10 | 3,784,281 | 422 |
| [BEST Scalper in the World](https://www.youtube.com/watch?v=DyS79Eb92Ug) | Words of Rizdom | 2025-12-18 | 2:21:40 | 1,583,686 | 302 |
| [He Became a Top Ranked Scalper with This Tool](https://www.youtube.com/watch?v=nn0Dx_OL24o) | Andrea Cimi | 2025-05-02 | 1:02:21 | 330,005 | 53 |
| [600 Trades In 3 Months Using This One Setup](https://www.youtube.com/watch?v=_mAy6q3OBZw) | Titans Of Tomorrow | 2025-11-21 | 10:36 | 33,170 | 34 |

**Who this is.** Fabio Valentini — ranked three times in the Robbins World Cup
scalping division, quarterly returns of *"68% in the first cup, 88 or 89% in the
second one, and 218% in the third"* [_mAy6q3OBZw @ 1:30]. Footprint scalper.
Carmine Rosato appears alongside him in the 2026 session and separately in our
earlier corpus. This is not retail content — it is two ranked practitioners
narrating live NQ/ES order flow for nine hours.

---

## What's usable

### U1 — 🔴 The A+ setup they name is our `thin-break-trap`, with the two confirmations it was missing

Unprompted, when asked what the best trade of the session was
[xUyqIjCfZzg @ 45:09]:

> **"The best setup that I saw, which I hesitated to execute on, was when the
> pre-market lows broke. We had the zero prints that formed and the massive
> absorption at the low."**
> — *"Massive absorption. That's an A+ perfect setup"*
> — *"and really low risk."* — *"Very low risk."*

Three components, all mechanical: **(a)** the pre-market low breaks, **(b)** zero
prints form below it, **(c)** absorption at the low. Plus the property the whole
program keeps failing on — *"really low risk"*, i.e. a naturally tight stop.

Our `nypre-thin-break-trap` thesis proposed (a) and asked what discriminates trap
from real break. **They answer it: absorption, plus the one-sided print
signature.** That is not a coincidence of framing — it is the same trade, arrived
at independently, by someone who trades it for a living.

### U2 — "Zero prints", defined precisely enough to code

[xUyqIjCfZzg @ 6:48–7:41]:

> *"there's unfilled levels 6917 on ES and 6914 — they're what I call **zero
> prints where there's zero volume on one side of the market**... the market
> aggressively sold off and trades were aggressively hitting the bid. And at
> these prices, **no trades hit the offer**. And the market likes to revisit
> them... they're usually **very strong magnetic forces**... as soon as they form
> I mark them because **the chances of them being revisited are very very high**.
> Some days in the same session, some days it takes a week or maybe even a month."*
> — *"The real inefficiency"* — *"very inefficient because it didn't give a fair
> chance of one side of the market."*

A zero print is a price level in the footprint where one side traded **zero** —
an auction that never gave the other side a chance to transact. The claim is a
revisit base rate.

**This is directly computable from `data/reference/cvd/footprint_*.parquet`** and
it is a *falsifiable base rate*, not a vibe: what share of zero prints formed in
08:00–09:30 are revisited by 10:00 / by the close / at all, and how does that
compare to a matched non-zero-print level? That is a one-census question.

Note what it is *for*: **a target and a magnet, not an entry.** That matters more
than it sounds. Our sleeves keep dying on R-economics rather than direction —
`euro-handoff` reached 78% WR and still paid +0.02R because the natural target
was too far. A validated magnet level is a *target-selection* upgrade available
to every existing sleeve, and it costs no new entry arm.

### U3 — Absorption is the single recurring trigger across nine hours

45 absorption references across the three live sessions. The read is consistent:
aggressive orders hit a level, fail to move price because passive size is filling
them, and the failure — not the aggression — is the signal.

> *"Sellers are getting annihilated on this level. Absorbed. These are aggressive
> buyers."* [DyS79Eb92Ug @ 20:22]
> *"if the market gets heavily absorbed here I want to be cover below this low"*
> [DyS79Eb92Ug @ 7:32]
> *"not willing to have a reaction like pushing but limit orders are absorbing
> them"* [tvERE-Beu2U @ 2:50:02]

And the inverse as a stand-down rule, stated explicitly [DyS79Eb92Ug @ 44:35]:

> *"this is a trade we can do. But **not when we are getting absorbed** because
> when we are getting absorbed **we are betting on the losing side**."*

That last line is the cleanest statement of the trapped-counterparty test we
have from any source: absorption tells you which side is about to be trapped.

### U4 — The edge is in the thin part of the book, said plainly

[xUyqIjCfZzg @ 24:20]:

> *"this range right here is... **too much liquidity for me. I like trading where
> there's not a lot of liquidity because that is where in my opinion a lot of the
> edge comes from**."* — *"This is like fair value for them. So they transact
> really efficiently there and you have a choppy face. You're looking for
> **inefficiencies** in the market, not efficiencies."*

Independent practitioner confirmation of the session-mechanics claim that the
pre-market's thin book is the *reason* to be there, not a reason to avoid it —
subject to costs (U6).

### U5 — A ranked scalper avoids the pre-market open, and says why

[tvERE-Beu2U @ 1:23:30 — auto-caption is fragmented here, segments interleave]:

> *"...pre-market opening. **This is the reason why [I never trade pre-market
> opening]** ... you see the battle but you don't know who will win it."*

Read conservatively — the caption is damaged and the bracketed clause is inferred
from the surrounding fragments. But the reason given is coherent and matters:
at the pre-market open, aggression is two-sided and **unresolved**. He waits for
resolution.

That is not a contradiction of U1 — it is the same logic. He does not trade the
*battle*; he trades the *verdict*. Our session-mechanics finding reaches the same
place from the structure: the pre-market supplies the setup, 09:30 supplies the
adjudication.

### U6 — 🔴 An explicit slippage warning about NQ specifically

[xUyqIjCfZzg @ 45:40]:

> *"The only fear I have on this setup is being slipped. If you have a huge
> aggression, maybe they steal some ticks because you get filled lower than your
> original stop-loss."* — *"Well, **in the NASDAQ, that's very possible**."* —
> *"there's **more slippage in the NASDAQ**, especially with larger size."* —
> *"right now with the volatility on ES, the **book thickness is between like
> 40-50 contracts**... But NASDAQ, I don't know how thick the book is."*

The one named risk on the A+ setup, from the person who trades it, is **stop
slippage on NQ**. This is the C1 cost question from the earlier sweep, confirmed
by a practitioner rather than inferred by us. It argues the 2× slippage arm is
not a formality for this candidate — it is the actual kill test. We hold MBP-10
for the window and can measure book thickness at trigger time directly rather
than assuming it.

### U7 — Their frequency argument is our certification argument

[_mAy6q3OBZw @ 0:40]:

> *"there is an average of 500 trades every three months... I think **it's the
> only way to keep the drawdown low and get a big performance because you need a
> big data sample and a lot of execution**. Otherwise, you can just go hard on
> risk, but it's like gambling because you need five lucky trades."*

Independent arrival at the point in `findings/nypre-session-mechanics-2026-08-05.md`
§8: at ~2 trades/month our sleeves need 380–1,345 days to certify. He solves the
same problem the same way — frequency, not size. Risk discipline stated: 0.25%
per trade, 1:3 to 1:5 RR, **max three stops per day then flat for the day**.

---

## What's noise

- **N1 — The performance numbers are unauditable here.** 68/88/218% quarterly are
  self-reported in an interview. Robbins World Cup placings are externally
  verifiable in principle; the returns as stated are not, and nothing in this
  file should be cited as a performance claim. We take the *mechanism*, not the
  track record.
- **N2 — Discretionary pattern-reading dominates the live commentary.** Most of
  the nine hours is real-time judgement — "I like this", "not confident here" —
  that does not reduce to rules. The extractable material is U1–U4; the rest is
  context.
- **N3 — Tooling talk.** Substantial time on footprint/DOM platform mechanics.
  Not transferable; we compute from Databento.

## Contradictions between sources

- **C1 — Their clock is not our clock.** These traders work the 09:30 open and
  the afternoon; Fabio describes scalping *"every afternoon from the starting of
  New York session to late night"* [_mAy6q3OBZw @ 1:50], and U5 has him avoiding
  the pre-market open outright. **So none of this is direct evidence that
  08:00–09:30 is tradeable.** What transfers is the *mechanism* (U1–U4), not the
  session. Stated plainly so nobody later cites this file as pre-market evidence
  it is not.
- **C2 — Against our own `nypre-quiet-hours-reversion` tombstone.** They fade
  failed pushes constantly. We measured that at 43–53% and killed it. The
  difference is the confirmation: they require *absorption at the level*, we
  tested a bare price-reversion trigger. That is a real, specific reason our
  version failed and theirs does not — and it is testable rather than a
  face-saving story: add the absorption gate to the killed trigger and see if the
  rate moves. **Not a reopening of that candidate** (its reopening burden stands);
  a note that its failure has a candidate explanation.

## Out of scope for ny-pre, flagged for the other lanes

**A stated base rate on first-hour expansion** [DyS79Eb92Ug @ 1:15:10]:

> *"it means that the market expanded in the first hour of the session"* —
> ***"90% of the session that expand they rebalance till the power hour. This is
> the structure of the New York: if you expand immediately, and Trump is not
> tweeting, you rebalance."***

He puts *"90% of my execution of model B, testing of the value area after their
expansion"* in the run-up to the power hour. **This is an RTH-afternoon claim,
not a pre-market one** — it belongs to the NY AM / afternoon lane, not here. It
is a clean, censusable base rate (does an expanded first hour predict a value-area
retest before 15:00?) and it should be handed over rather than tested in this lane.

## Candidate leads

- **`nypre-thin-break-trap` — upgraded, and my ranking of it changes.** U1 supplies
  the exact trigger stack (break → zero prints → absorption) and U3 supplies the
  stand-down rule. It was third of three on the grounds that it was
  under-specified; it is now the best-specified of the three. Redundancy against
  the canon and the parked `open-sweep-fade` is still the thing to check first
  and cheaply.
- **Zero prints as a target/magnet layer — measurement first, not a candidate.**
  Per the S6/S8 precedent in the prior sweep merge: run the event study (revisit
  rate vs matched control) before promoting anything. If it holds it is a
  target-selection upgrade for sleeves we already have, which is worth more than
  another entry.
- **First-hour expansion → power-hour rebalance** — hand to the NY AM lane.
