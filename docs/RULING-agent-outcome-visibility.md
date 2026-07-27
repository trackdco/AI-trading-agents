# RULING — agents SEE outcomes and P&L. They do not ACT on them. Yet.

**Angus, 2026-07-27 (verbatim):** *"agents should see outcomes and pnl data, id want to have
access to that for now so it can build a learning curve, not act on it. once it trades live
for a bit and we can see that it has room to actually trade better than our mechanical
strategy, i will unlock the door for them. for now, they are executing off our mechanical
books, but that is not the end goal. they should be proficient at trading regardless at one
point, and at that exeedingly more profitable than the mechanical baseline. take me, as an
example. ive been trading for 3 years, and someone trading the same strategy for 3 months
would get murked if it was a contest. the same applies for ai, except ai can adopt my 3 years
experience in a few hours realistically."*

This CLOSES the C1/C2 desk-contract question, open since pass 31 and flagged again in
`docs/SPEC-adaptive-journal.md` §5.1. The frozen v0.3 desk contract forbade showing an agent
outcome/P&L data about its own verdicts; the feedback wiring was deliberately built to a
ledger only and never connected. **It may now be connected — for learning, not for acting.**

## The two halves, and why they are separable

**SEE — now permitted, and the point.** Agents may be shown realized outcomes, P&L,
counterfactuals for trades not taken, their own past verdicts and how those graded. This is
the substrate the whole adaptive journal exists to build (`SPEC-adaptive-journal.md`).

**ACT — still forbidden.** `docs/RULING-mechanical-only.md` is untouched. Nothing an agent
thinks reaches an order. The books execute mechanically; the agent is a reader.

The separation is **structural, not procedural**: the trade path does not consult an agent at
all. There is no code route from a model's opinion to the broker. Visibility of P&L therefore
cannot leak into execution — not because we trust the agent to restrain itself, but because
the wire does not exist.

## The invariant that DOES need enforcing

Seeing outcomes is safe. Seeing *the future* is not. The engineering line is an **as-of
boundary**, and it is the thing to test rather than trust:

> An agent reasoning about day D may see outcomes only from days strictly before D, and
> within D only from decisions already resolved at the moment it reasons.

Same discipline the repo already applies to features (no-lookahead tests, the single
structural 08:00-ET briefing cutoff, the pass-15 hindsight decontamination of
`regime-context.md`). Outcome data is simply another feature with a timestamp, and the walk-
forward replay is exactly where a violation would otherwise hide — the agent would appear to
learn brilliantly and be reading its own answers.

Concretely, before any outcome feed goes live:
- every outcome record carries a `resolved_ts`; the briefing builder filters on it
- a test asserts no briefing for day D contains a `resolved_ts >= D`'s decision time
- the fresh-eyes twin remains the control — a memory-quarantined agent seeing the same facts

## Why the compression argument is already measured

Angus's three-years-versus-three-months point is the thesis behind
`docs/LONG-WALK-2023-2026.md`, and part of it is already on the board. The walk-forward
analog table's read accuracy improves every year as the library deepens, with no agent
judgment layered on at all:

**2023: 37% → 2024: 41% → 2025: 44% → 2026: 52%** (3-way, random = 33%)

That curve is experience compressing into retrieval. What this ruling unlocks is the
next input — not just "what did similar days do" but "what did I decide, and what did it
cost me". Whether the agent amplifies that curve or wastes it is the open question, and it
is measurable rather than arguable.

### What the old agent evidence does NOT bear on (Angus, 27 Jul — correcting this doc)

A first draft cited June's sequential run — chained memory "hurt reads" (24%), fresh-eyes
beat the incumbent 45–38 — as caution. **That citation was wrong twice and is withdrawn.**

1. **It measures a task that no longer exists.** That agent picked ONE book per day, or stood
   down. The canon trades *both books, every day, no book choosing, no day forecasting*
   (`CANON-MECHANICAL.md`). There is no stand-down. An agent's future job is not "which book
   today" but per-trade judgment inside a book that is always live.
2. **It scores on a metric this repo has since retired.** `FINDING-standdown-is-capture-
   negative.md` concluded that read accuracy and dollar capture are ANTI-correlated —
   "reads is the wrong target" — and that every agent version captured LESS than simply
   always-trading the champion (21%), with capture falling as the FLAT rate rose (v0.6, 35%
   flat → 19%; v0.6.1, 78% flat → 11%). Quoting a read score as evidence about money
   contradicts the finding that killed the stand-down layer.

Angus's framing, which the data supports: the agent *should not be scared to trade* —
opportunities exist most sessions, and the measured cost of caution was the entire leak
(wrong-FLATs = 78% of $38,137 regret). None of that era's evidence was gathered with depth
or CVD available, which is now central to every canon check.

### The honest bar, restated against the CURRENT system

The useful caution is not historical, it is arithmetic. The canon's ladder is already good at
skipping: across the fit window its rejects run **19% WR / −$73,806** against **46% / +$49,277**
on what it takes, and `scripts/canon_attribution.py` shows every layer is dollar-negative on
what it discarded bar one 5-trade cell. So the margin an agent has to beat is a layer that is
demonstrably competent, on a task where the flow data it would reason from is the same data
the checks already consume.

That is the measurement to run — not a re-litigation of the book-selection era.

## The bar for unlocking ACT

Angus sets it and holds it: the agent must demonstrate, on live-adjacent evidence, room to
trade **better than the mechanical baseline** — not equal to it. Until then agents execute
the mechanical books unchanged. Consistency (months green) remains the objective function,
so "better" means better on that, not on totals.

## What this changes today

| | |
|---|---|
| Trade path | **nothing** |
| `RULING-mechanical-only.md` | **unchanged** — still in force |
| `SPEC-adaptive-journal.md` §5.1 | **CLOSED** — Tier 2 counterfactuals are authorized |
| Desk contract (v0.3 C1/C2) | outcome/regret feedback may now be wired into briefings, subject to the as-of boundary |
| Live journaling | still waits for arming (PROMOTION-GATE §E) |
