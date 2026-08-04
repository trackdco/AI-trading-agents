# FINDING — LDN-DRIVE-01 (euro-open-drive): **NOT TESTABLE** on this sample

**Drafted for Brake's signature.** Routes to Angus.
Reproduce: `python -m scripts.ldn_drive01_feasibility`.

**This is not a verdict and euro-open-drive has not been tested.** No outcome, return,
direction or P&L was computed. Nothing was selected on, so no statistical power was spent
and **this does not enter the DSR trial ledger** (§2.4). It is a determination that the
candidate *as specified* cannot be tested on the data we hold.

**Sealed 2023/24 untouched. No holdout look.**

---

## The finding

`london_feasibility_scan.py` cleared euro-open-drive at its first gate — **67 / 36** drive
opens, comfortably over the n ≥ 30 floor. That scan's own footer warns its numbers are
upper bounds. Applying the candidate's remaining declared gates:

| gate stack | 2025 | 2026 | |
|---|---|---|---|
| 1. open outside Asia range | 67 | 36 | OK |
| 1+2, strict one-time-framing | **0** | **0** | UNTESTABLE |
| 1+2, ≤ 2 violating 5-min bars | 7 | 1 | UNTESTABLE |
| 1+2, ≤ 3 violating 5-min bars | 12 | 4 | UNTESTABLE |
| 1+2, "IB never trades back through the open" | 0 | 0 | UNTESTABLE |
| 1+2+3, most permissive gate 2 + IB ≤ 1.5× Asia | 10 | 4 | UNTESTABLE |

The gates are the candidate's own, quoted from its mechanical skeleton: *"open prints
outside Asia range/value; one-time-framing on 5-min bars; skip if opening range already >
threshold (news spent)."*

## Why this is a definitional finding, not a threshold artifact

The thesis names one-time-framing without pinning a tolerance, so a single definition would
be my choice, not the candidate's. Both loose gates are therefore **laddered**, and the
answer does not move:

**Under Dalton's strict reading the gate fires on zero of the 103 drive-open days.** Not a
small count — zero. A 60-minute IB has ~11 five-minute transitions, and not one of those
103 days produced an IB in which price never took out the prior bar's extreme. The alternative phrasing in the thesis — the drive *"never trading back through
the open"* — also returns zero.

The decisive number is what it costs to make the count testable:

> Reaching n ≥ 30 in both eras requires tolerating **7 violations out of ~11 transitions**,
> which retains **92% of all drive opens**.

A gate that lets price take out the prior 5-min bar's extreme on 7 of 11 bars is not
one-time-framing; it is "any drive open" wearing the gate's name. **At the tolerance where
the sample becomes testable, the gate has stopped being the candidate's gate.** There is no
setting at which both the specification and the n-floor hold.

Gate 3 is irrelevant to the outcome — at any threshold from 1.5× to 3× it moves the count
by two days.

## What this says about the candidate — and what it does not

**It does not say the candidate is wrong.** Nothing here measures whether drive opens
extend. The claim is untouched.

What it says is that the trade **as specified is rare to the point of being unmeasurable on
three and a half years of data**. That has two readings and they are not the same:

1. **The gate is over-specified.** Strict one-time-framing across a full hour is a
   demanding filter, and NQ's 5-min noise may simply break it on days that are drives in
   every practical sense. If so, the gate needs re-specifying by someone who trades it —
   not by me, and not by picking the tolerance that makes the number work.
2. **London does not produce clean directional first hours.** This would be a real
   structural fact about the session, and it sits alongside the LDN-VWAP-01 acceptance
   finding (London relocates value on 37% of days it stretches to ±2σ). Those two point in
   opposite directions and both cannot be the whole story.

Distinguishing them requires re-specifying the gate, which is a **new candidate needing a
new prereg** — not a re-run of this one. I have not done it, because choosing a tolerance
after seeing which tolerances produce a testable n is exactly the search this process
exists to prevent.

## Recommendation to Angus

**Return to the author for re-specification, or shelve.** Do not authorise a census. Two
things must come back before it is worth a prereg:

- a one-time-framing definition committed to **in advance**, with its tolerance stated as
  a number, not "one-time-framing on 5-min bars";
- an expected event rate. If the author's own expectation is under ~30 days per era, the
  candidate is not testable at L0 regardless of the definition and should be shelved
  without further cost.

If it comes back re-specified, the prereg must record that the first specification was
found untestable — otherwise the second gate definition is an undeclared search.

## Process point worth carrying

This is the second time the feasibility discipline has paid, and the first time it has paid
*before* a prereg was written. LDN-INV-01 cost a diagnostic, a prereg and a census before
anyone noticed the validate era held 28 days per cell. Here the cost was one counting
script and no trials.

**Recommended amendment to `VALIDATION-PROCESS.md` §2.2:** the n-floor check must be run on
the candidate's **full gate stack**, not its trigger. A trigger-only count is an upper bound
and will clear candidates that cannot be tested. The one-line version: *count what you would
actually trade, before you write the prereg.*

## Programme state

| candidate | outcome | trials |
|---|---|---|
| london-inventory-fade | FAIL — fragility | 4 |
| london-asia-sweep-reversal | FAIL (one family) | 4 |
| london-asia-sweep-continuation | FAIL (same family) | — |
| london-level-trap-fade | FAIL — well-powered null | 4 |
| london-vwap-sigma-rotation | INCONCLUSIVE ON POWER, three findings against | 4 |
| **london-euro-open-drive** | **NOT TESTABLE — no trial** | **0** |
| london-level-defense-flow | blocked: NY veto conversation | — |
| london-value-traverse | blocked: volume-at-price map not built | — |
| london-eu-macro-windows | blocked: EU release calendar not built | — |

**6 of 9 resolved. London trial ledger: 16, unchanged.** No holdout looks spent.

The three remaining candidates are blocked on decisions or builds, not on testing capacity.
The testable set is exhausted.
