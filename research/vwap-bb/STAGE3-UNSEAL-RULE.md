# STAGE 3 — UNSEAL RULE

**Written 2026-08-08 under the Code-Path Verification Suite, Part 4.** This file did not
previously exist; "replace" is recorded as "created", and that is itself a finding — there was
no unseal rule in the repository before now.

Spec: `42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf` (A1–A13).

---

## 0. A precondition the brief assumes and the repository does not satisfy

> **There is no sealed Stage 3 run. Nothing named Stage 3 has ever been executed.**

The only sealed artefact is the **Stage 2 workbench smoke result**, at
`data/archive/workbench_results_SEALED_PRE-A8_UNOPENED.parquet`
(`a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0`, never opened). It was
produced under spec `8ead7259`, which **A9 and A10 have since superseded**, and STATE.md already
records its performance numbers as unusable for that reason.

**This rule therefore governs a run that does not yet exist.** It binds the first Stage 3 run
when one is produced. It also disposes of the Stage 2 artefact, in §4.

---

## 1. THE RULE

> **The sealed Stage 3 run is opened if and only if BOTH (a) and (b) hold.**

### (a) Verification

| | condition |
|---|---|
| **a.1** | **2a passes** — every spec-derived unit test, with no expected value edited after a failure |
| **a.2** | **2b reports zero violations across a full evaluated count**, with **no invariant left `NOT TESTABLE`** |
| **a.3** | **2c's diff is empty under enforced isolation**, or every disagreement is adjudicated to **spec ambiguity** rather than to a bug in either implementation |

### (b) Pass marks

| | condition |
|---|---|
| **b.1** | The Stage 3 pass marks are **signed and committed** — `PREREGISTRATION.md` §7, including the four OPEN items in §10 and the §7.3 drawdown carve-out |

**Both. Not either.**

---

## 2. IF A BUG IS FOUND ON THOSE PATHS

> **The sealed run is DISCARDED UNOPENED and repeated after the fix. It is not read "just to
> check", and it is not read "to see whether the bug mattered".**

Reading it to see whether the bug mattered is the whole failure this rule exists to prevent: it
converts a broken run into a data point, and a data point into a reason to keep the broken
version.

**If the detector is modified for ANY reason — bug fix, amendment, refactor, a rename — the
sealed run is stale by definition and must be discarded and re-run.** There is no such thing as
a modification that leaves a sealed result valid; if it changed nothing, re-running costs
minutes, and if it changed something, the seal was already void.

---

## 3. VERDICT AS AT 2026-08-08

> # DO NOT OPEN

Not a close call, and it does not turn on the verification result.

| clause | status | why |
|---|---|---|
| **precondition** | **FAILS** | There is no sealed Stage 3 run to open. |
| **a.1** | conditionally met | 64 tests, 61 pass. The 3 failures are two mis-constructed test bars and one expectation with no clause behind it — **no detector bug** — but the strict reading of a.1 is "passes", and three red lines are not a pass until the two bad cases are rebuilt. |
| **a.2** | **FAILS** | **Invariant 7, stop-first accounting, is `NOT TESTABLE`** and a.2 requires none remaining. Invariant 9 is `UNSPECIFIED IN SPEC`, which is a specification gap, not a pass. |
| **a.3** | see the suite report | Adjudicated there. |
| **b.1** | **FAILS** | The pass marks are **not signed**. `PREREGISTRATION.md` §10 still carries four OPEN items. |

**The operative clause is the precondition, and after it a.2 and b.1 independently.** Any one of
the three is sufficient for DO NOT OPEN.

---

## 4. DISPOSAL OF THE STAGE 2 ARTEFACT

The archived pre-A8 result is **not** the run this rule governs, and it must not be opened under
it either.

| | |
|---|---|
| Status | **superseded, never opened, retained** |
| May it be opened under §1? | **No.** §1 governs a Stage 3 run under the current spec. This is a Stage 2 run under `8ead7259` |
| May it be opened at all? | **Only by an explicit decision recorded as such**, which would be reading a result on a specification no longer in force. There is no purpose for which that is the right measurement |
| What it already delivered | The pipeline verification it existed to provide: `loc_gate_measure.py` reproduced its admitted count **exactly (1,423)** from an independent replication |
| Recommended | **Leave it closed permanently.** Its only remaining value is as evidence that the engine is deterministic and re-implementable, and that value is already realised |

---

## 5. WHAT MUST HAPPEN BEFORE THIS RULE CAN EVER RETURN "OPEN"

In order, because each depends on the one before:

1. **Close invariant 7.** Stop-first accounting is untestable on an admission list by
   construction — attributing an exit is outcome information. It becomes testable only against a
   Stage 3 engine, and it must be tested there **before** that engine's output is sealed, not
   after.
2. **Resolve invariant 9.** §5.3 says *"E1: limit at the BB MA"* and no clause anywhere rounds a
   price to the tick. **1,401 of 1,472 intended entries are off the 0.25 grid** and cannot be
   placed as written. The spec must say how prices are rounded, and in which direction, before
   any run claims to be executable.
3. **Rebuild the two mis-constructed 2a cases** so a.1 is met on its own terms.
4. **Build the Stage 3 engine.** `stage2_smoke.py` implements **none** of A8, A9, A10 or A13 and
   cannot be used.
5. **Sign the pass marks**, including the four OPEN items.
6. **Then run Stage 3, seal it, and apply §1.**

**N_trials: 0.** Nothing in this rule tested a hypothesis, and the trade list it governs does
not exist.
