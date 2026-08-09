# A22 — 2×ATR stop floor: fresh 2a/2b re-run and determinism check

**2026-08-08.** Angus's own decision on `PASS-MARKS-FOR-SIGNING.md` §10.2: switch the §5.4 stop
floor from a fixed 10.00 pt to 2×ATR(20, entry TF), structural. Spec after A22 (including the
tick-grid errata found during this re-run): git blob `a42f6ae3c6277e800991585ffacaa2cc47a9ea77` /
sha256 `12f2b822a0ee12aee32bcb06463e305e0a6e3e23ab4c98766b0c771116185daa`. **No outcome computed.**

## 1. What changed

`spec_a22.py`, layered on `spec_a16.py` (A16 limit entry + A17 bounded-span clustering; A18-A21
unchanged). `signal_candidates_a22` is identical to `signal_candidates_a16` except the R_int
floor: `max(structural stop, 2 × ATR(20, entry TF))` instead of `max(structural stop, 10.00 pt)`.
ATR matches the definition already computed as a one-off diagnostic in `vwapbb_geometry.py`,
never previously wired into the live pipeline: per-entry-TF (1/2/3/5 min), 20-bar lookback,
simple average of True Range on closed bars, warmup requires 20 closed bars on that TF or the
candidate is dropped.

## 2. A real bug found and fixed during this re-run, disclosed in the spec's Amendment Log

A5's fixed 10.00 pt floor was on-grid by construction; A22's 2×ATR floor is a simple average of
True Range values and is generally **not** a multiple of 0.25. First run of the fresh invariants
found **1,105 of 1,361 trades (81.2%) with an off-grid stop** — invariant 9 failing hard. Fixed
by extending A14's existing rounding rule (round away from entry) to cover this new case, and
recomputing R_int from the rounded stop. No trade was ever computed under the unfixed version;
the bug was caught between implementation and this re-run, before any admission list left the
module. Full account: `strategy-definition-v1.0.md`, A22's errata note.

## 3. 2a — spec-derived unit tests

101 tests (93 carried from A1-A21, +8 new: GROUP M for A22's `true_range`/`compute_atr`).
Committed unrun, then run, per the two-commit protocol.

**96 PASS, 5 FAIL.** Four of the five are the same pre-existing, already-disclosed failures from
before this round (A8, A9, H1b, H1c). The fifth, **M6, is a new but self-caught failure in the
test itself**, not the code: M6 wrongly assumed moving an outlier bar to the front of a series
would leave a simple-average ATR unchanged. It doesn't — the first bar in any such series never
contributes its own high/low to a True Range value, only its close feeds forward, so moving the
outlier there removes it from the sample rather than reordering it. Per this project's standing
rule, M6's expectation was **not edited** — it stays in the file, disclosed, and **M8** was added
with correctly-reasoned coverage of the same property (simple averaging vs. Wilder's smoothing),
which passes.

## 4. 2b — invariants over the whole trade list, fresh admission list under A1-A22

`invariants_a22.py`, built on `spec_a22.signal_candidates_a22` + `spec_a16.admit_a16` (fill
mechanics unchanged by A22). **1,360 trades**, same 539/501 session accounting and three
exclusion reasons as every prior run this round.

**10/10 invariants PASS** (after the fix in §2), including invariant 2, rewritten for A22 (checks
`stop_px` is exactly `entry ∓ R_int` and `R_int` never sits below `2×atr_tf` for that trade's own
recorded ATR), a new invariant 2-bis (every admitted trade carries a positive `atr_tf` — the
warmup gate holds), and invariants 1/3/4/5/6/9/10/11/12 carried over unchanged from
`invariants_a16.py` (A22 touches only the stop floor).

## 5. Determinism

`invariants_a22.py` run twice, independently:

```
run 1: TRADE-LIST SHA-256 (geometry only): 6cbd083c6ea097b9d5d37e3b79723d5a90dfff3f25c016cac23197fee582bff5
run 2: TRADE-LIST SHA-256 (geometry only): 6cbd083c6ea097b9d5d37e3b79723d5a90dfff3f25c016cac23197fee582bff5
```

**Identical.**

## 6. Population, in context

1,360 (A1-A22) vs 1,470 (A1-A21, fixed 10pt floor) vs 1,444 (A16 fill only, pre-A17 clustering).
The 1,470→1,360 drop (−7.5%) is A22's own isolated effect: a materially wider, session-varying
stop floor (median ≈25 pt vs a fixed 10 pt) changes both which candidates clear the RR floor and
the warmup-gate exclusion (candidates before 20 closed bars on their own entry TF are now
dropped, which A5's constant floor never required). This is a population-size measurement, not an
outcome — no trade's result was read to produce it.

## 7. What has NOT been run

No sensitivity comparison, no Stage 3 seal, no pass-mark evaluation. The 32-combination fork
sweep (`FORK-SET-ENUMERATION.md`) still needs to be built and run, now against the A22 floor
rather than the fixed one, before any Stage 3 seal.

**N_trials: 1 of 5, unchanged.** Unit-test pass/fail, invariant violation counts, and a
determinism hash are classification and measurement, not comparison of results — and the stop
floor itself was chosen by Angus directly among pre-existing figures, not selected by outcome.
