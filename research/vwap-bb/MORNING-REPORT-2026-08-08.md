# MORNING REPORT — Amendment 04, overnight queue, items 2–11

**Read the headline. Everything else is detail on demand.** 13 commits, `88b2ae6` → `79bd2f3`,
all pushed. Spec `42d6f0f6` (A1–A13) → `cd20e532…` (A1–A15). N_trials 0 → **1 of 5**.

---

## 1. HEADLINE

**Everything ran except the one thing explicitly reserved for you.** A14 (tick rounding) and A15
(ladder de-duplication) are written and implemented; every test suite is re-run fresh and green
except two deliberately-unedited mis-built test bars; a sealed Stage 3 run exists under the
current spec and clears the sample floor; the P4–P9 batch is formally withdrawn; the pass marks
are drafted for your signature. **The one thing genuinely blocking you: sign or amend the four
items in `PASS-MARKS-FOR-SIGNING.md`.** The 2c differential diff is collected in full but **not
adjudicated** — you asked for the calls to happen in the morning, and this is that morning,
addressed to you, not decided by me overnight. Nothing else blocks. No bug was found in the
detector itself; two bugs were found and fixed in my own overnight verification tooling, both
disclosed below.

---

## 2. DECISIONS I DID NOT MAKE

All four live in **[`PASS-MARKS-FOR-SIGNING.md`](PASS-MARKS-FOR-SIGNING.md)**, restated briefly:

| item | options | my recommendation |
|---|---|---|
| **10.1 parity** | (a) P2 alone satisfies it / **(b) the full verification suite supersedes the original hand-chart plan** / (c) not yet satisfied, want more hand readings | **(b)** |
| **10.2 stop anchor** | (a) floor as written / (b) structural anchor (prior swing or ATR) | **none — genuinely open**, unchanged by anything overnight |
| **10.3 axis structure** | any divisor in the table, or a different structure | **sign ÷4**, the working assumption everything else already cites |
| **10.4a primary criterion** | sign as drafted, or amend the cost basis/bound | **sign as drafted** |
| **10.4b abort condition 3** | abort, or annotate | **abort** |
| **10.4c trigger reading** | fix reading A, or promote it to a tournament axis (changes 10.3's divisor) | **fix reading A** — it's what everything to date has used, including last night's sealed run |

**Also reserved, not listed as a numbered pass mark but load-bearing:** whether the sealed Stage 3
run (§8 below) may ever be opened depends on **your signature** on the above **and** on your
adjudication of the 2c diff (§7). Both, not either.

---

## 3. SPEC HASHES

| point | git blob | sha256 |
|---|---|---|
| **start** (before item 2) | `4bad6a68…` | `42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf` |
| **after A14** | `3debc30d…` | `3a5ac2f70fda4b229b05ba86baefa6413f6a8682aeb6edb7efd45f67f8a1e780` |
| **after A15** (pre-errata) | `a74b1e46…` | `d460db91a0bbf3839788cf1251d8f84ed3c72fb619409efdab3ebca1fd4ac4ad` |
| **after A15 errata** = **end** | `f6b38bf4…` | `cd20e532fae0259854a25ee9261b408f21204563fc470afb7e3bdb28e33197ac` |

**One correction disclosed mid-sequence, not silently folded in:** A15 as first committed
contained a sentence contradicting its own stated rule and the code — it said the ≤1-tick rule
was operative and then, one sentence later, claimed levels exactly one tick apart stay separate
(the opposite). Caught while deriving item 6's boundary test cases, **before any test was written
against the wrong reading**. Fixed in a new commit (`367bc36`), not by rewriting history. Nothing
downstream was ever computed under the wrong reading — no code implemented the erroneous
sentence, only the prose stated it backwards for a few hours.

---

## 4. ITEM-BY-ITEM

| item | status |
|---|---|
| 2 — A14 tick rounding | **DONE.** Spec text, then code, then item 3's recheck, each its own commit |
| 3 — invariant 1 recheck | **DONE.** See §5 |
| 4 — A15 ladder de-dup | **DONE**, no code change (formalises existing behaviour) |
| 5 — invariant 7 into 2a | **DONE.** 15/15 pass on synthetic bars, closing what was `NOT TESTABLE` |
| 6 — new A14/A15 tests, full re-run | **DONE.** See §6 |
| 7 — finish 2c | **PARTIAL, by your own instruction.** Mechanical collection complete (`2C-RAW-COLLECTION.md`); **adjudication explicitly deferred to you**, not performed |
| 8 — predicate overlap audit | **DONE.** Clean answer: nothing double-counts (§9) |
| 9 — withdraw P4–P9 | **DONE.** Formal withdrawal notice, document retained in full |
| 10 — pass marks prepared | **DONE, not signed** (§2) |
| 11 — Stage 3, sealed | **DONE.** Gate passed, run sealed, N_trials 1 of 5 (§8) |

---

## 5. ADMITTED COUNT BEFORE / AFTER A14

Full workbench, 501 processed sessions, geometry only.

| | |
|---|---|
| Admitted, before A14 | **1,472** |
| Admitted, after A14 | **1,472** — same total, **different population** |
| Trades that lost the RR floor under the now-wider R | **8** |
| Trades gained under the rounded geometry | **8** |
| Trades holding their identity across the change | **1,464** |
| Invariant 1 on the after-list | **1,472 evaluated, 0 violations, PASS** |
| On-grid check on the after-list | **0 off-grid entries, stops, or targets** |
| **661 floor** | **CLEARS**, 1,472 ≈ 2.23× |

R_int median unchanged at 10.00 (the A5 floor still dominates 58.7% of trades); p75/p95/mean
moved by fractions of a point. Full detail: `data/item3_a14_recheck.json`.

---

## 6. 2a AND 2b — FRESH, IN FULL

### 2a — spec-derived unit tests

**81 tests, 77 PASS, 4 FAIL.** Determinism: `PYTHONHASHSEED=0`, two runs, **identical hash
`b38c1944…`** both times.

The 4 failures, unchanged from the original run and left deliberately unedited:

| id | clause | why it fails |
|---|---|---|
| A8 | §3 displacement B_min boundary | test bar has a lower wick, so §3's rejection predicate correctly co-fires — **the test bar was mis-built, not a detector bug** |
| A9 | same | same construction error |

(The B_min boundary itself is covered cleanly by the two replacement cases **A8b/A9b**, both
PASS.) **D4 and D5, previously `UNSPECIFIED IN SPEC`, now PASS on real A15 clauses.** New groups
**I** (A14 rounding, 11 cases) and **J** (A15 collapse, 6 cases) — **all 17 pass.**

### 2b — invariants over the full 1,472-trade admission list

| # | clause | evaluated | violations | status |
|---|---|---|---|---|
| 1 | §6.5/A4 RR floor | 1,472 | 0 | PASS |
| 2 | §5.4+A2+A5 stop anchor | 1,472 | 0 | PASS |
| 3 | §6.5/A4 nearest clearing rung | 1,472 | 0 | PASS |
| 4 | accounting 4.2 next-bar-open | 1,472 | 0 | PASS |
| 5 | A1 signal window | 1,472 | 0 | PASS |
| 6 | §5.6+§10.1(3) one-at-a-time / cap | 1,472 | 0 | PASS |
| 7 | 4.1 stop-first | — | — | **MOVED to 2a** (was `NOT TESTABLE`; now 15/15 PASS there) |
| 9 | A14 tick grid | 5,888 | **0** | **PASS** (was `UNSPECIFIED IN SPEC` before A14 existed) |
| 10 | §4.3 single contract | 1,472 | 0 | PASS |

Determinism: two runs, **identical hash `9bb1f055…`.**

**Two bugs caught and fixed in my own tooling before either result was accepted, both
disclosed:** a `sorted()` call over mixed int/string keys crashed on the first run (fixed with an
explicit sort key — not a logic change); invariant 9's status label was stale immediately after
A14 landed, still reading `UNSPECIFIED IN SPEC` against a clause that now existed (corrected to
`PASS` before accepting the run). **Neither bug is in the detector.**

---

## 7. 2c — COLLECTED, NOT ADJUDICATED

Per your mid-run instruction: *"Present the raw diff and the raw log; the calls happen in the
morning."* This is that morning. **I have not classified a single disagreement, and I have not
ruled on isolation.** Full mechanical collection: **[`2C-RAW-COLLECTION.md`](2C-RAW-COLLECTION.md)**.

**What's in it, unadjudicated:**

- Detector pinned to `bab2e03` (pre-A14/A15) via a detached worktree, so the diff reflects the
  blind build's actual target, not a moving one.
- **1,472 detector trades, 1,583 blind-build trades, 20 exact key matches, 1,452 detector-only,
  1,563 blind-only.** All 20 key matches disagree on entry, stop **and** target simultaneously.
- Widened identifier/magic-number grep: **no evidence of source copying** — none of the
  detector's distinctive names appear in the blind build, and where names coincide (`FRONT_RUN_F`,
  `POC_BIN`, `FRACTAL_N`) the surrounding logic diverges in ways a copy wouldn't (different POC
  bin-centre-vs-edge convention, different variable decomposition throughout).
- **`AMBIGUITIES.md` (386 lines) and `READ_MANIFEST.md` (61 lines) are reproduced verbatim, in
  full**, inside the collection file. Neither has been checked against its cited clause.
- **One thing worth your attention before you adjudicate:** the blind build's own manifest is
  honest that it read the amendment log, which by now contains several *detector-derived
  measurements* (A5's 29.6%, A13's σ̂ census, A9's 46.9). Its own `NOTES.md` shows it checking
  fork choices against those published numbers, and — separately — flags the one place it
  *declined* to fit a reading to a published count (the `range` confluence minimum), which is
  some evidence the discipline was real elsewhere. Per your own item-7 instruction: **any
  resolution justified by an output figure is contaminated and every trade touched by it comes
  out of the diff — per-ambiguity, not all-or-nothing.**

---

## 8. STAGE 3 — RAN. COUNT AND HASH ONLY.

| | |
|---|---|
| Ran | YES |
| Realised trade count | **1,472** |
| SHA-256 | **`0caf65cfdb2a0bfd939215ed95805e0a4b729210c5c35eef0d5f4bf05d55ce71`** |
| 661 floor | **CLEARS** |

Gate: items 2–6 introduced no behaviour contradicting an existing clause (A14/A15 are additions,
exempted by the item's own text; the two bugs found were in my tooling, not the detector) — gate
**passed**, run executed and sealed. **Nothing else about it appears anywhere in this report, in
`STATE.md`, or in any commit message — checked directly with a token scan before accepting the
script's own output, not assumed.** `STAGE3-UNSEAL-RULE.md` updated: precondition now met, a.1
and a.2 now pass, a.3 awaits your 2c adjudication, b.1 awaits your signature. **Verdict:
DO NOT OPEN**, resting on those two alone.

---

## 9. ITEM 8 — PREDICATE OVERLAP AUDIT

**Clean answer.** A bar at exactly `B_MIN` with a top-quartile close does necessarily fire both
rejection and displacement (confirmed directly, A8b/A9b) — but traced `kind` through
`stage2_smoke.py`, `spec_current.py`, `invariants_2b.py` and `vwapbb_a7_selector.py`: it is
**stored on every candidate and read by nothing** — not the confluence count (`types`/`nlev`,
both derived from the cluster's level composition before `trig()` is ever called), not the
conviction score, not `tie_break()`. Every admission builder's de-dup key excludes `kind`
entirely, so a bar satisfying both predicates on one cluster collapses to **one** admitted trade.
Nothing double-counts.

---

## 10. DETERMINISM HASHES

| artefact | run 1 | run 2 | match |
|---|---|---|---|
| 2a result | `b38c1944…` | `b38c1944…` | ✓ |
| 2b trade list | `9bb1f055…` | `9bb1f055…` | ✓ |
| 2c diff (pinned worktree vs. earlier unpinned run same commit) | identical summary stats both times | | ✓ |

---

## 11. NEW WORK PROPOSED

- **10.2's stop-anchor question could be narrowed, not resolved, with data already held**: a
  distribution of *hand-log stop distances relative to the nearest computable structural level*
  (prior swing, session extreme) might show whether your 35-pt stops track one of them more than
  the other, even without confirmed prices. Not done — it's new scope, flagged rather than run.
- **The 2c blind build's `sensitivity.py` fork sweep is itself informative independent of
  adjudication** — it found trade *identity* far more sensitive to ambiguity resolution than
  trade *count* (55% survival under a single flipped fork, ±3% on count). Worth reading even
  before the diff is adjudicated; it's a general caution about this project's whole verification
  approach, not specific to the blind build.

---

## 12. WHAT I COULD NOT DO

- **2c's adjudication.** Not a failure — explicitly reserved for you. Collection is complete;
  the classification (detector bug / second-build bug / spec ambiguity) and the isolation verdict
  are not made.
- **10.2, the stop anchor.** Genuinely undecidable by me — the hand log records distances, never
  prices, and no amount of overnight computation changes that.
- **Confirming the TradingView splice date** (Amendment 03 §8's item 3, carried over, still
  open) — requires your chart, not the archive.
- **A8/A9's mis-built test bars.** Left deliberately unedited per rule 5's own logic (an
  expectation may not be edited after a failure); replaced by A8b/A9b rather than fixed in place.
  If you want them corrected in place rather than superseded, say so.

Nothing else was skipped, capped, sampled, or approximated. Every commit that could be verified
for determinism was run twice with matching hashes. The holdout was never touched, the archived
Stage 2 parquet was never opened, and the newly sealed Stage 3 parquet was never opened.
