# DECLARATION — LONDON COMBINATION BOOK (incumbent + room-gated reject)

## PROCESS NOTE, first, because it changes how these numbers may be read

**This specification was written AFTER the run, not before it.** The
overnight queue said "combination declaration and run"; the run went first.
That is a process error and it is recorded rather than hidden.

What it costs: **the combination numbers in FINDINGS-phase0.md are
fit-side descriptive, not a declared test.** They cannot confirm anything
and are not treated as if they could.

What limits the damage: the combination has **no free parameters left to
choose**. Both streams were fully fixed by earlier declarations — the
incumbent by BR-16/BR-23, the room-gated stream by
DECLARATIONS-room-to-run §1 (as-traded construction, 2pt floor, 3R
threshold) — and the account-layer bars were declared in
DECLARATIONS-room-to-run §4 Bar 2 before any of tonight's numbers existed.
The only genuinely new decision was the union rule, and that was
data-driven by the declared redundancy check (§2 below), not chosen.

This document is therefore a **specification of record**. Nothing ships
from it.

---

## §1 — THE UNION RULE, and the check that chose it

**Declared before the overlap numbers were read** (the criterion was set in
the overnight queue): *if redundancy comes back under ~50%, proceed to a
simple union with the number stated; if it is high, stop and do not invent
a dedup rule overnight.*

**Redundancy** — a room-gated trade is redundant if an incumbent trade
exists at the **same locus, same direction, entry within 5 minutes**:

| stream | n | redundant | concurrent | genuinely new |
|---|---|---|---|---|
| LONDON reject 3m | 334 | **6.6%** | 22.2% | 93.4% |
| LONDON reject 5m | 308 | **8.1%** | 25.3% | 91.9% |

Well under the 50% line, so: **simple union, no dedup rule.** The 6.6% /
8.1% double-count is stated and left in.

**Concurrency is reported separately and is NOT a dedup question.** 22–25%
of room-gated trades are open at the same time as an incumbent trade. That
is a *risk-spine* fact — it raises simultaneous R-at-risk — and it is
carried into the account lab through the daily-total-R metric, which is the
binding constraint (BR-25), not through position counting.

**Cross-timeframe union is still NOT done.** 41.9% of the 5m stream is
redundant with the 3m stream — far above the line. So the 3m and 5m streams
are combined with the incumbent **separately, never with each other**. The
cross-TF dedup rule remains undeclared and unbuilt.

## §2 — SCOPE

- **LONDON only.** NY_PRE and NY_AM are excluded regardless of what the
  12-cell table shows for them. They need their own declaration.
- **Reject arm only** from the room-gated stream.
- Streams: incumbent LONDON (composite + sweep_b) ∪ room-gated LONDON
  reject at 3m; and separately ∪ 5m.

## §3 — KNOWN DEFECT IN THE COMBINED OBJECT

**The two books use different entry conventions on the break arm.** The
incumbent's break arm enters on a **retest** of the level; the room-gated
LTF stream enters at the **next 1m open**. The reject arms match (both
next-1m-open), and the room-gated stream contributes rejects only — so the
combined book contains one retest-entry population (the incumbent's
union_break component) alongside next-open populations.

This is not fatal — each stream was measured under its own consistent
convention — but a combined book is not a single-convention object, and any
future claim about it must say so.

## §4 — SCORING, on the bars already declared

Full account lab, not EV and frequency: **P(graduate), worst-day R, and max
non-breaching size against the $2,000 EOD trailing drawdown**, at each
book's own carryable size and under the cushion policy (k=.05, $150–$300).
Reported at both the **sim stage** (5-payout cap, 250-day clock) and a
**live-stage proxy** (same mechanics, no cap, no clock — LucidLive terms
are not public, so this is explicitly a proxy).

## §5 — STANDING

No holdout contact. Nothing adopted, armed, or treated as shipped. Review
in the morning.
