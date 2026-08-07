# StarTrading ledger — cluster verdicts and durable findings

Status of the branch: **CLOSED**. See [`../CLOSURE.md`](../CLOSURE.md) for the two-minute
version.

Seven videos were extracted into per-video records under the standard schema. Those records
partitioned into three distinct models sharing one channel identity. This file records what
happened to each, and the two structural findings that outlived the test.

---

## Cluster verdicts

### Cluster α — **DEAD-ON-SIZING**

*Videos: `DvlS4m3qNV0` (masterclass, reference text), `O5NBF8Jg5vU`, `n6tdQXCM52Y`,
`UX-7OcxqdZw` (weak assignment).*

**Reason:** RR 0.2 against a level-based target forces a stop of 5× the entry-to-target
distance — a 424-point median stop on NQ. At MNQ, the smallest listed contract, the median
loss is 42% of a $2,000 trailing drawdown and the p95 loss is 200% of it. No position size
fits, because there is no smaller contract.

Independent of win rate, exit rule and bias rule. Full analysis and the retained
inconclusive-on-win-rate evidence trail:
[`../alpha-feasibility.md`](../alpha-feasibility.md).

**Scope:** this kills α *on NQ inside a trailing-drawdown account*. It does not kill α as
taught — forex and gold have fractional lot sizing, so the quantisation that disqualifies it
here does not arise there. Untested on its native instruments; no claim made.

### Cluster β — **UNTESTABLE**

*Video: `scwg7wUc55k`.*

**Reason:** the ruleset is never stated in any video held. β is defined only negatively —
broader window, explicitly not the 00:00 session, does not follow the daily bias, *"barely
anything to do with the previous one"* [87:33]. None of α's vocabulary (imbalance, BPR, FVG,
liquidity, confirmation) appears anywhere in the transcript. There is nothing to implement
and therefore nothing to test.

Not a verdict on merit. It would become testable if a video stating β's entry, stop and
target were obtained.

### Cluster γ — **NOT PURSUED**

*Video: `n5TBiz17eA4`.*

**Reason:** a single video, an incomplete ruleset, and an 08:30 anchor that sits outside the
session this project trades. Three reasons to deprioritise, none of them a finding about
whether it works.

γ is the only positive-RR model in the corpus (1:2) and the only one with trade management
(break-even stops on every trade plus re-entries), so the sizing verdict that killed α does
not transfer to it. **Explicitly not a verdict on its merit.**

---

## Model census — the durable analytical result

Anchor is the discriminating field; it partitions the corpus with no overlap.

| Record | Video | Instrument | Anchor | Formation filter | RR sign | Management | Cluster |
|---|---|---|---|---|---|---|---|
| 1 | vlKZEA0x2X4 | EUR/USD spot | 08:00 | central | 0.5 negative | none | **unresolved** |
| 2 | n5TBiz17eA4 | futures | 08:30 | absent | **1:2 positive** | BE + re-entry | γ |
| 3 | O5NBF8Jg5vU | GBPUSD, gold | 00:00 UTC | absent | 0.2 negative | refused | α |
| 4 | UX-7OcxqdZw | gold, GBPUSD | unknown | unknown | negative | unknown | α (weak) |
| 5 | scwg7wUc55k | unknown | broad, not 00:00 | unknown | not the OG 0.2 | unknown | β |
| 6 | DvlS4m3qNV0 | forex, gold | 00:00–01:00 UTC | absent | negative, 95% | not taught | α |
| 7 | n6tdQXCM52Y | unknown | 00:00 UTC | absent | negative, 95% | unknown | α |

**Record 1 is unassigned.** Its 08:00 anchor, EUR/USD instrument and central post-anchor
formation filter match nothing else; its 0.5 RR does not match α's stated 0.2. It
self-describes as *"my new model"*, which points at β — but β never states its rules, so the
match cannot be confirmed. Left open rather than forced.

**Authorial confirmation** of the split, from record 5 [87:21–87:43]: *"These are two separate
models... This is basically the OG model. This right now is the new model. It has barely
anything to do with the previous one."* The census was derived from the rule fields before
this quote was found; the two agree.

---

## Structural findings that outlived the test

These are the parts worth remembering. They are properties of the model class, not of the
particular backtest, and they generalise to any similar candidate.

### (a) The signal fires every session, so it carries no selection information

Across **all 1,544 legs**, the 00:00 UTC open sat inside the prior day's range. Not most —
all. This is structural rather than lucky: the 00:00 open is effectively the prior day's
closing price, which lies inside the prior day's high/low by definition.

Consequence: both the long and the short leg are *always* valid, so the model can never fail
to produce a signal. A signal that triggers every single session performs no selection, which
means **the undocumented discretionary bias rule was always doing 100% of the work.** The
mechanical part of α contributes nothing but geometry.

This is a general test worth reusing: if a candidate's entry condition is satisfied on every
observation, the entry condition is not the strategy.

### (b) α is not a specifiable strategy

α states no exit for a trade that reaches neither its target nor its stop within the session,
and **~32% of trades do not resolve same-session** (67.8% resolved same UTC day).

How those trades are treated swings expectancy from **+0.076R to −0.337R** (same-session
treatment: 89.70% win rate with unresolved excluded, versus 55.25% counting them as losses).
That range is **larger than the entire margin over breakeven**, and it straddles zero.

So the sign of α's expectancy is determined by a rule the source material does not contain.
This was discovered by testing an assumption the analyst had introduced rather than one the
model specified — without that check, the study would have reported a profitable system that
was an artefact of an arbitrary 20-day hold cap.

**The reusable lesson:** when a result depends on a parameter the source never states, the
finding is not the result. The finding is that the strategy is underspecified.

---

## Per-video records

The seven extraction records were produced under the standard schema (rules_stated with
timestamps, concepts_used, claimed_numbers, costs_included, breakeven_treatment,
contradictions, discretion_markers). The census table above carries the fields that decided
the outcome.

The single most decisive field across all seven was **`costs_included`**, which returned
**NO** on record 1 — *"we're not going to be including spread and commissions"* [00:19] —
and **UNKNOWN** on every other record. Commission is never mentioned in any of the seven
videos. That one field determined how much weight any claimed number could carry, and it is
why the cost gate was placed first in the feasibility test.
