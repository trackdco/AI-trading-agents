# FORK SET — fixed before anything runs under the identity-churn clause

**2026-08-08. Amendment 05 round 2, item 4.** Per the pass-mark clause in
`PASS-MARKS-FOR-SIGNING.md`: *"the pass mark is evaluated as the minimum across every documented
resolution combination."* This document IS that enumeration. **Nothing in this document has been
run.** No outcome, no P&L, no comparison of results — this is a specification of which
combinations exist, fixed before any of them is computed, exactly as the clause requires.

---

## 1. The five forks, each defined precisely enough to implement without further judgement calls

| # | fork | reading A | reading B | governing text |
|---|---|---|---|---|
| **1** | **Cluster formation** | **Mutual proximity** — every level in a cluster within tolerance of every other (current) | **Single-linkage chaining** — consecutive sorted gap ≤ tolerance, span may exceed it | §3: *"within proximity tolerance"* — undefined which |
| **2** | **§7 invalidation band** | **Same-side band** — the NY ±1σ band the trade is heading *into* (+1σ long, −1σ short) (current) | **Opposite-side band** — the NY ±1σ band the trade is heading *away from* (−1σ long, +1σ short) | §7: *"the opposing ±1σ"*, `[Hypothesis — test]` |
| **3** | **`range` confluence minimum** | **2** — `range` is not counter-trend, so it takes the base requirement (current) | **3** — `range` is treated as requiring the raised (counter-trend) minimum | §7 names only 2 of §4's 3 HTF flags |
| **4** | **Front-run F** | **2.0** — low end of the stated range (current, `vwapbb_a7_selector.FRONT_RUN_F`) | **2.5** — the midpoint (blind build's reading) | §6.4: *"F: CALIBRATE (start 2–3 NQ pts)"* — a range, not a value |
| **5** | **Weekly H/L in the target menu** | **Absent** — never computed, `OUT-OF-SCOPE-BRANCHES.md` branch 9 (current) | **Present** — prior-week high/low added as target-menu entries | §6 menu: *"... weekly H/L ..."*, listed but never built |

**Combinations: 2⁵ = 32.** Every combination yields an admission list somewhere near the
1,450–1,600 range the sweep already measured (±3% on count, per Amendment 05's original finding),
each one a population that could plausibly be mistaken for "the" result.

## 2. A third reading exists on fork 4 and is deliberately excluded, with the reason stated

§6.4's stated range is "2–3 NQ pts," and **3.0** (the other boundary) is a third defensible
reading, distinct from both the detector's 2.0 and the blind build's 2.5 midpoint. **Excluded
from the enumerated set for now**, not because it's less valid, but because widening fork 4 to
three values makes it asymmetric with the other four binary forks and changes the combination
count from a clean 32 to 48 (2⁴×3). **Flagged as a decision, not silently resolved**: if 3.0 is
wanted in the set, say so and the count becomes 48, not 32.

## 3. Candidates NOT in this set, surfaced by the standing audit (item 5) — flagged, not added

`STRUCTURAL-LEVELS-AUDIT.md` found gaps beyond the five forks above that were never part of the
original sweep and are **not** included here without an explicit decision:

- **Pre-market H/L, absent from the target menu** despite §6 naming it (*"session extremes
  (Asia/London/pre-market)"*) — a parallel case to fork 5's weekly H/L, same shape, different
  level.
- **NY VWAP ±3σ, absent from both the cluster set and the target menu** despite §2/§3 naming it
  as part of the NY VWAP indicator.
- **The "structural" confluence TYPE, never emitted** — §3 counts it as a fourth type
  (*"structural ×1"*) but no code path ever tags a level "structural" for cluster-formation
  purposes, capping the real attainable confluence count at 3, not 4.

**None of these three is enumerated as a fork above.** They are structurally similar to fork 5
(a named-but-unbuilt menu item) and could each become one. **Whether they belong in the
combination set is exactly the kind of decision this document exists to force before a run, not
after** — recorded here so it is asked, not silently decided either way.

## 4. What "the minimum across every documented resolution combination" requires, operationally

For the pass-mark clause to be executable as written, each of the (at minimum) 32 combinations
needs its own admission list built and its own Stage 3 outcome computed **before** the minimum is
taken — the combining rule (minimum) is fixed now; running all 32 is a substantially larger job
than the single run just discarded, and has not been attempted. **This document fixes the list.
Building and sealing 32 runs is separate, unstarted work**, and — per the same reasoning that
governs a single Stage 3 seal — **each full sweep-and-minimum, taken together, still only
consumes the ONE Stage 3 slot** it replaces (N_trials 2 of 5 when it is run, not 32 of 5),
because no selection happens among the 32; all 32 are computed and the minimum is taken
deterministically.

## 5. Sequencing, restated from the instruction that closes this round

**Do not amend the entry mechanism yet.** This fork set exists to bound what "one resolution" of
Amendment 05's identity-churn clause means. **The fill-accounting question
(`FILL-ACCOUNTING-FORK.md`, `FILL-MECHANICS-QUOTES.md`) is a separate, prior decision** — it
determines what a "trade" even IS (which price it transacts at), and has to be settled, amended,
and re-pre-registered **before** any of these 32 combinations is built, or the sweep would be
measuring identity churn on top of a population that also doesn't match its own admission
criterion. **Sequence: fix the fill mechanism → re-pre-register → then build and run the 32 (or
however many, once §3's open items are resolved) → then take the minimum.**

**N_trials: 1 of 5, unaffected.** This document computed nothing.
