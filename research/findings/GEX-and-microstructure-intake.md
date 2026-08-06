---
date: 2026-08-05
status: RESEARCH INTAKE — two variable classes the programme has never encoded
tags: [gex, gamma, microstructure, ofi, micro-price, intake]
sources: ["research/transcripts/fabervaale/EXTRACTION-A-models.md", "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1712822", "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694"]
---

# Two classes this programme has never encoded

ANGUS 2026-08-05: *"you have uncapped network access now… you should be researching
yourself, finding things that could help and benefit. new theories and shit that we havent
tested before."*

Fair. Everything tested to date is the NY canon's inherited battery. Two classes below are
externally evidenced, and **one of them is already named by our own verified source.**

---

## 1. GEX — dealer gamma exposure

### The mechanism

Options dealers are, in aggregate, on one side of the index options book, and they
delta-hedge. Their hedging is **mechanical**, not discretionary, which is what makes it
predictable.

- **Dealers long gamma.** Price rises → their delta grows → they **sell into the rise**.
  Price falls → delta shrinks → they **buy the fall**. Hedging flow is *stabilising*.
  Volatility is suppressed and **price mean-reverts to levels**.
- **Dealers short gamma.** Everything inverts — they must **buy strength and sell
  weakness**, chasing the move. Hedging flow *amplifies*. Ordinary moves become trends and
  squeezes.

The price where aggregate dealer gamma crosses zero is the **gamma flip** (or zero-gamma
level). It is the boundary between those two regimes, and strikes with the largest gamma
concentration act as magnets or barriers (**call wall / put wall**).

### Why this is the single best-fitting idea for OUR problem, not just an interesting one

**Our surviving candidate is a FADE.** `A-FADE` — rejection blocks on a limit entry — is
the only positive cell in the entire London build (PF 1.08 raw, 1.37 with a 5pt risk floor,
positive in both eras).

**A fade is a bet on mean reversion. Long dealer gamma IS the mean-reversion regime.**

So GEX is not another feature to throw at a 70-variable search. It is a **regime switch
whose mechanism directly predicts when our strategy should and should not work.** That is a
mechanism-level match, and mechanism-level matches are the only kind §5.9.2 lets us treat
as high-prior.

The prediction is falsifiable and directional, and it should be declared before any data
is bought: **the fade's edge concentrates in positive-gamma sessions and degrades or
inverts in negative-gamma sessions.** If it does not, GEX is dead here and we stop.

### Our own source already said this

`research/transcripts/fabervaale/EXTRACTION-A-models.md` — the practitioner whose IB fade
is the healthiest candidate in the programme:

> *"the market maker are long gamma. So they will try to compress volatility. I expect a
> good explosion down"* [09:19]
>
> *"when you are positive gamma, they are going to compress every movement"*
>
> *"…you can also implement the short side okay that is more strong but you should be able
> to analyze the **gamma regime** because in this one **option flow comes really handy**."*

He also cites academic work by **Andrea Barbon, Carlo Zarattini and Andrew Aziz** on
profitable day-trading strategies. **That citation has never been chased** and is owed.

Note what this means for `NYA-IVB-01`: his own stated condition for the short side is a
gamma-regime read, and we shipped the fade **without it**. That is a documented gap in a
live-eligible candidate, not only a London question.

### The timing property that makes it cheap and causal

London runs 03:00–05:00 ET. US index options are not trading then — which is an
**advantage**, not an obstacle:

**The gamma profile is computed from the prior session's closing open interest, so it is
fully known before London opens.** It is a daily, strictly-prior conditioning variable.
No intraday options feed, no lookahead risk, no anchor-timing question of the kind that
consumed L3. It is causal by construction.

### What it needs

- **NDX (or QQQ) options open interest by strike and expiry, daily.** We hold none — a
  repo-wide search returns zero options files.
- Gamma per strike from OI × contract gamma, aggregated with the standard dealer-sign
  convention (dealers short calls / long puts as the base assumption), giving: total GEX,
  the zero-gamma flip price, and the largest call/put gamma strikes.
- **This is a purchase decision, not a research one.** Nothing can be tested until it
  exists.

---

## 2. Order-flow imbalance and micro-price — buildable TODAY, no new data

Well-evidenced in the microstructure literature and **absent from the canon**:

**Order Flow Imbalance (OFI)** — Cont, Kukanov & Stoikov. The key point is that OFI is a
**change** measure: the cumulative signed change in queue size at the best bid and ask over
an interval. Their finding is a **linear relation between OFI and price change, with slope
inversely proportional to market depth**, robust to intraday seasonality and stable across
time scales and stocks.

**We compute static book imbalance (`dep_imb`) — a level, not a change.** The literature's
predictive quantity is the thing we never built.

**Micro-price** — Stoikov. The mid adjusted by bid-ask imbalance and spread; a martingale
by construction and empirically *"a better predictor of short term prices than the mid-price
or the weighted mid-price."* Related: **queue imbalance at the best prices** is the
strongest single short-horizon predictor in this literature — *"the property of the best
bid and ask queues most useful for price prediction is not their lengths, but rather their
imbalance."*

**We use total book size across ten levels. We have never computed best-level queue
imbalance.**

Both are buildable from `data/reference/depth_london` (MBP-10, all ten levels, one snapshot
per minute) with no purchase. The one-snapshot-per-minute resolution limits OFI — it is
designed for event-level data — so what we can build is a **minute-resolution
approximation**, and that limitation goes on the record before it is tested, not after.

---

## The honest constraint that outranks both

**n = 655 on the fade. The measured noise floor is ~9pp.** Roughly 70 variables have now
been searched against that sample and the null median rises with every addition.

**Neither of these classes escapes that.** GEX helps *because it is a regime split with a
prior*, not because it is one more column — a declared, mechanism-driven binary split is a
fundamentally cheaper test than another sweep. That distinction is the whole reason it is
worth doing.

More variables against 655 trades makes things worse. A declared mechanism with a
directional prediction does not.
