# STAGE 3 SEALED RUN — DISCARDED UNOPENED

**2026-08-08. Amendment 05 round 2, item 1. The sealed run is discarded per
`STAGE3-UNSEAL-RULE.md` §2: "The sealed run is DISCARDED UNOPENED and repeated after the fix."**

**File:** moved, byte-identical, hash re-verified before and after the move —
`0caf65cfdb2a0bfd939215ed95805e0a4b729210c5c35eef0d5f4bf05d55ce71` —
to `data/archive/workbench_results_SEALED_A15_DISCARDED_UNOPENED.parquet`. **Never opened.**
Not deleted, per this project's standing practice (the pre-A8 Stage 2 result was archived, not
deleted, for the same reason: a discarded result is still evidence that the pipeline runs and is
deterministic, even though its content must never be read).

---

## Why

**The admission gate screens on a price the system does not transact.** §6.5/A4's RR floor is
evaluated **"outward from entry"** — against the intended limit — and admits a candidate only if
some menu level's front-run-adjusted distance from that limit is **≥ 1.5R**. But the accounting
rule that actually fills the trade (`PREREGISTRATION.md` 4.2) fills at **the next bar's open,
unconditionally**, which is a different price from the limit on **99.3% of trades** (1,462 of
1,472). The population the gate believes it is screening — "trades whose *transacted* geometry
clears 1.5R" — is not the population that exists in the file. **Geometry-only, no outcomes**:
**65.2%** of the sealed run's 1,472 trades have a **realised** risk:reward (computed from the
actual fill to the fixed stop and target) that falls **below the very 1.5R the gate certified**.
Full distribution in `fill_fork_report.json` / the report below.

**This is not "the strategy might not work." It is "the file does not contain what its own
admission criterion claims it contains."** Reading it — even to check whether it happens to be
salvageable — would be exactly the failure `STAGE3-UNSEAL-RULE.md` §2 exists to prevent: turning
a broken run into a data point, and the data point into a reason to keep the broken version.

## N_trials — NOT refunded

**N_trials stays at 1 of 5.** The standing rule (`STATE.md`, `STAGE3-UNSEAL-RULE.md`) is explicit
that sealing consumes the slot **"whether or not the file is ever opened."** That rule exists
precisely to prevent "seal, discover a problem, discard, reseal" from becoming a free way to
iterate around the α budget. Discarding this run does not undo its cost. **The next sealed run,
whenever it happens, consumes slot 2 of 5.**

## What has to change before a re-run

1. **The order-type and fill-mechanics gap** — see `FILL-MECHANICS-QUOTES.md` for the four
   clauses quoted in full and the precise finding about what is and is not stated.
2. **The admission screen needs to evaluate a price the system will actually transact at**, or
   the accounting rule needs to change, or both need to be stated together so neither silently
   contradicts the other. This is a decision reserved for Angus, not made here.
3. **The fork-set enumeration** (`FORK-SET-ENUMERATION.md`) needs to be fixed and pre-registered
   before any run is sealed under the identity-churn clause in `PASS-MARKS-FOR-SIGNING.md`.
4. **This is a change to the trader, and ships as a pre-registered spec version, not a patch** —
   Angus's own words, recorded here so the sequencing isn't lost: quote → decide → amend →
   pre-register → run. Not: patch the code and reseal.

**N_trials: 1 of 5. Holdout untouched. The discarded file's contents remain unread.**
