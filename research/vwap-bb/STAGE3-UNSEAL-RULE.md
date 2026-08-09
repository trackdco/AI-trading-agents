# STAGE 3 — UNSEAL RULE

**Written 2026-08-08 under the Code-Path Verification Suite, Part 4. Updated 2026-08-08, item 11
of the overnight queue — clause (a) re-evaluated post-A15, a sealed Stage 3 run now exists.
Updated again 2026-08-08, Amendment 05 round 2, item 1 — that sealed run has since been
DISCARDED UNOPENED under §2 below; see §0-bis and the revised §3 verdict.**

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

## 0-bis. That sealed run no longer exists at the path above — DISCARDED, per §2, unopened

**2026-08-08, Amendment 05 round 2, item 1.** The RR-floor admission gate (§6.5/A4) was found to
screen a price — the intended limit — that the accounting rule (`PREREGISTRATION.md` 4.2) does
not transact at (it fills at the next bar's open, unconditionally). Geometry-only measurement
(`fill_fork_report.py`, no outcome computed) found **65.2% of the sealed run's 1,472 trades**
realise below the very 1.5R the gate certified. This is exactly the condition §2 below describes
— a bug on a path a.1/a.2/a.3 were supposed to cover but didn't, because the mismatch is between
two documents (the spec's admission clause and the pre-registration's accounting clause), not
inside either one alone.

**Action taken, exactly per §2's text:** the sealed run was **discarded unopened**, not read "to
see whether the bug mattered." The file was moved, byte-identical, hash reverified before and
after the move (`0caf65cf…`), to
`data/archive/workbench_results_SEALED_A15_DISCARDED_UNOPENED.parquet`. **Its contents remain
unread to this moment.** Full reasoning, the exact 65.2% figure and its distributional detail:
`STAGE3-DISCARDED.md`, `FILL-ACCOUNTING-FORK.md`, `fill_fork_report.json`.

**N_trials: NOT refunded by the discard.** The slot this run consumed — 1 of 5 — stays spent, per
the standing rule that sealing consumes a trial "whether or not the file is ever opened."
Discarding for cause is not an exception to that rule; it is the exact scenario the rule is there
to prevent from becoming a free re-roll. **The next sealed Stage 3 run, whenever it happens,
consumes slot 2 of 5, not a re-use of slot 1.**

**Every clause below this point (§1 THE RULE, §3 VERDICT, §5 remaining steps) now governs a
*future* Stage 3 run — a re-seal that does not yet exist — not the discarded one.** §3's verdict
is rewritten accordingly; do not read the pre-discard verdict table as still describing a live
sealed file, because there is no longer a sealed file to describe.

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

## 3. VERDICT AS AT 2026-08-08 — UPDATED after the Amendment 05 round 2 discard

> # NO SEALED RUN EXISTS. THE QUESTION "OPEN OR NOT" DOES NOT CURRENTLY ARISE.

**Superseded verdict, kept for the record (this described the run that was discarded under §2 /
§0-bis, and no longer describes anything that exists):**

| clause | status at time of discard | why |
|---|---|---|
| **precondition** | ~~MET~~ **VOID** | the sealed run this row described no longer exists; discarded unopened, `STAGE3-DISCARDED.md` |
| **a.1** | PASSED | 81 tests, 77 pass, 4 accounted-for failures, no detector bug — unaffected by the discard, still true of the current code |
| **a.2** | PASSED | 10 invariants, full-count `PASS` or `MOVED` — unaffected by the discard, still true of the current code |
| **a.3** | MET | `2C-ADJUDICATION.md` — unaffected by the discard, still true of the current code |
| **b.1** | FAILED | pass marks prepared, not signed — **still unmet**, and now joined by a new, prior blocker (below) |

**a.1/a.2/a.3 pass or hold on the code as it stands — the discard was not caused by a detector
bug on any path those clauses check.** It was caused by a mismatch *between* the admission gate
(§6.5/A4, evaluated against the limit) and the accounting rule (`PREREGISTRATION.md` 4.2, fills
at the open) — a cross-document inconsistency neither a.1, a.2, nor a.3 was ever scoped to catch,
since each checks one implementation against one spec, not two spec documents against each other.

**New precondition for the NEXT seal, ranked before b.1, because b.1 is about signing marks on a
mechanism and there is currently no agreed mechanism to sign marks on:**

| | condition |
|---|---|
| **a.4 (new)** | The fill-accounting fork is resolved and pre-registered as a spec amendment — not a patch, per Angus's own closing instruction ("this is a change to the trader and it ships as a pre-registered spec version"). See `FILL-ACCOUNTING-FORK.md`, `FILL-MECHANICS-QUOTES.md`. |
| **a.5 (new)** | The fork set for the identity-churn pass-mark clause (`FORK-SET-ENUMERATION.md`, 5 forks / 32 combinations, fixed 2026-08-08) is built and run, and the minimum taken, per `PASS-MARKS-FOR-SIGNING.md`'s combining rule. |
| **b.1 (unchanged)** | Pass marks signed. |

**Operative clauses now: a.4, a.5, and b.1 — three, not one.** a.1–a.3 remain met on the current
code and do not need to be re-proven unless the detector changes again before the re-seal.

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

## 5. WHAT MUST HAPPEN BEFORE THIS RULE CAN EVER RETURN "OPEN" — updated after the discard

1. ~~Close invariant 7.~~ **DONE** — item 5, moved to 2a, 15/15 pass on synthetic bars.
2. ~~Resolve invariant 9.~~ **DONE** — A14, rounding rule specified and implemented; 2b now
   shows **0 of 1,472** entries, stops or targets off-grid.
3. ~~Rebuild the two mis-constructed 2a cases.~~ **NOT DONE, and no longer blocks a.1**, as before.
4. ~~Build the Stage 3 engine.~~ **DONE, then DISCARDED.** `stage3_sealed_a15.py`'s sealed output
   consumed N_trials 1 of 5 and was discarded unopened, `STAGE3-DISCARDED.md`. **The engine code
   itself is not known to be wrong** — the discard was about what the admission gate and the
   accounting rule jointly certify, not a bug in the engine's arithmetic.
5. ~~Sign the pass marks.~~ **STILL open**, and now sequenced behind items 7-8 below, not before
   them — signing marks on a mechanism that is about to change is signing marks on the wrong
   mechanism.
6. ~~Adjudicate the 2c diff.~~ **DONE** — `2C-ADJUDICATION.md`; a.3 is MET.
7. **NEW — resolve and pre-register the fill-accounting fork.** `FILL-ACCOUNTING-FORK.md` /
   `FILL-MECHANICS-QUOTES.md` lay out the choice; Angus's own words govern the form of the fix:
   *"this is a change to the trader and it ships as a pre-registered spec version, not a patch."*
   **Not started** — explicitly deferred this round ("do not amend the entry mechanism yet").
8. **NEW — build and run the 32-combination fork sweep**, `FORK-SET-ENUMERATION.md`, and take the
   minimum per `PASS-MARKS-FOR-SIGNING.md`'s combining rule. **Not started**, and sequenced
   *after* item 7 (sweeping combinations on a fill mechanism about to be replaced would measure
   identity churn on a population that already doesn't match its own admission criterion).

**Remaining, in order: fix the fill mechanism and re-pre-register (7) → build and run the fork
sweep, take the minimum (8) → sign the pass marks (5, i.e. b.1). §1 still requires all of (a) —
now including the new a.4/a.5 — and (b) together; neither substitutes for the other.**

**N_trials: 1 of 5, spent on the discarded run and not refunded.** The next sealed run consumes
slot **2 of 5**.
