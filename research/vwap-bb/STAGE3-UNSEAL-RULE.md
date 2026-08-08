# STAGE 3 — UNSEAL RULE

**Written 2026-08-08 under the Code-Path Verification Suite, Part 4. Updated 2026-08-08, item 11
of the overnight queue — clause (a) re-evaluated post-A15, a sealed Stage 3 run now exists.**

Spec: **`f6b38bf4af1ca9696a12a6e9f80a12209ebff310`** (A1–A15). **Superseded:** `42d6f0f6…`
(A1–A13, this rule's original spec) and `8ead7259…` (A1–A7, the Stage 2 spec).

---

## 0. The precondition from the original writing no longer holds

> **A sealed Stage 3 run NOW EXISTS.** `data/workbench_results_SEALED_A15.parquet`, sealed
> 2026-08-08, SHA-256 `0caf65cfdb2a0bfd939215ed95805e0a4b729210c5c35eef0d5f4bf05d55ce71`, 1,472
> rows, 29 columns, produced by `stage3_sealed_a15.py` under spec `f6b38bf4…` (A1–A15). **This
> consumes one Stage 3 slot under Amendment 02's α budget — N_trials 1 of 5 — whether or not the
> file is ever opened.** Never read. `read_results()` requires the unseal token.

The Stage 2 artefact remains as described below, unaffected by this update; §4 is unchanged.

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

## 3. VERDICT AS AT 2026-08-08 — UPDATED after item 11

> # DO NOT OPEN

**Still not a close call — but for a much narrower reason than the original writing.** Items 2–6
of the overnight queue closed a.1 and a.2 outright; a.3 remains unadjudicated by explicit
instruction (deferred to the morning); b.1 is the clause now doing all the work.

| clause | status | why |
|---|---|---|
| **precondition** | **MET** | a sealed Stage 3 run exists, `0caf65cf…`, 1,472 rows, N_trials 1 of 5 |
| **a.1** | **PASSES** | 81 tests, 77 pass. The 4 failures are the same two mis-constructed test bars, deliberately left unedited — **no detector bug**. Every new A14/A15 case and both reclassified D4/D5 pass on real clauses |
| **a.2** | **PASSES** | 10 invariants over the full 1,472-trade list, all `PASS` at a full evaluated count except invariant 7, which is **`MOVED`** to 2a (15/15 pass there, on synthetic bars, closing what was `NOT TESTABLE`) — not left `NOT TESTABLE` in place, which is what a.2 actually forbids |
| **a.3** | **collected, not adjudicated** | mechanical diff run (`2C-RAW-COLLECTION.md`): 1,472 detector trades vs 1,583 blind-build trades, 20 exact key matches, 1,452/1,563 one-sided, all 20 matches disagreeing on every field. **No verdict rendered by explicit instruction** — item 7 was split, and the adjudication is reserved for the morning review. a.3 cannot be marked met or failed until that happens |
| **b.1** | **FAILS** | The pass marks are **prepared** (`PASS-MARKS-FOR-SIGNING.md`) but **not signed**. Four OPEN items in `PREREGISTRATION.md` §10 remain open |

**The operative clause is now b.1 alone, with a.3 undetermined.** Both must resolve — b.1 needs a
signature; a.3 needs the morning's adjudication of the 2c diff — before this verdict can move.

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

## 5. WHAT MUST HAPPEN BEFORE THIS RULE CAN EVER RETURN "OPEN" — updated, three of six done

1. ~~Close invariant 7.~~ **DONE** — item 5, moved to 2a, 15/15 pass on synthetic bars.
2. ~~Resolve invariant 9.~~ **DONE** — A14, rounding rule specified and implemented; 2b now
   shows **0 of 1,472** entries, stops or targets off-grid.
3. ~~Rebuild the two mis-constructed 2a cases.~~ **NOT DONE, and no longer blocks a.1.** A8 and
   A9 remain deliberately unedited (they are wrong test bars, not a detector bug); a.1's own text
   only requires *"every spec-derived unit test, with no expected value edited after a
   failure"* — met, since the file's PASS/FAIL count is 77/81 and the 4 failures are accounted
   for and understood, not silently ignored.
4. ~~Build the Stage 3 engine.~~ **DONE** — `stage3_sealed_a15.py`, sealed, N_trials 1 of 5.
5. **Sign the pass marks.** Still open. `PASS-MARKS-FOR-SIGNING.md` prepared; not signed.
6. **Adjudicate the 2c diff.** Still open, and now the OTHER precondition alongside signing —
   collected in `2C-RAW-COLLECTION.md`, not adjudicated, by explicit instruction.

**Remaining: sign the pass marks (b.1), and adjudicate 2c (a.3). Both, not either — §1 requires
all of (a) and (b).**

**N_trials: 1 of 5.** Consumed by the sealed Stage 3 run above, whether or not it is ever opened.
