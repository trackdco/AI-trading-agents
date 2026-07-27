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

Counter-evidence already on record, so nobody sells this as a certainty: June's sequential
run found chained memory *hurt* reads (24%) while improving discipline, and the fresh-eyes
twin beat the incumbent 45% to 38%. Memory has been a net drag once already. Outcome
visibility is a new input, not a fix for that.

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
