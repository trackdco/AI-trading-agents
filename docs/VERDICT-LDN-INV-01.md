# VERDICT — LDN-INV-01 (london-inventory-fade)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus
for ruling. Reproduce: `python -m scripts.ldn_inv01_continuous`.

**Sealed 2023/24: untouched.** `fit_only()` drops them and asserts they are gone. **No
holdout look was taken or spent.**

---

## VERDICT: **FAIL** — fragility. Both eras.

Killed by a pre-registered criterion, on the pre-declared primary window, in the discovery
era *and* the validation era. This is not a close call and it does not need more data.

---

## What ran

| trial | what | declared | result |
|---|---|---|---|
| 1 | L0 quintile census | `PREREG-london-inventory-fade.md` | 2025 asymmetric, 2026 not (criterion 2 armed) |
| — | power diagnostic | not a trial — no search, no tuning | criterion 2 unsound; 2026 underpowered |
| 2 | continuous hinged regression | `PREREG-london-inventory-fade-continuous.md`, commit `3627bc3` @ 12:55:42Z | **FAIL — fragility** |

Trial 2 was declared before it was run. The commit timestamp is the declaration.

## Why it fails

The pre-registered fragility clause (§2.5, carried into trial 2's prereg) says an edge
carried by ≤ 3 days is dead **regardless of every other test**. On the primary window
(03:00→04:00), the asymmetry `D = b_neg − b_pos` flips sign in both eras when the three
largest-magnitude days are removed:

| era | D (full sample) | D (drop-top-3) | |
|---|---|---|---|
| 2025 | **+1082** | **−201** | SIGN FLIPS |
| 2026 | **−402** | **+853** | SIGN FLIPS |

It is not a knife-edge at exactly three. The estimate is unstable at every trim depth:

| era | full | drop1 | drop3 | drop5 | drop10 | winsorised 1/99 |
|---|---|---|---|---|---|---|
| 2025 | +1082 | +1297 | **−201** | +576 | +705 | +801 |
| 2026 | −402 | −332 | **+853** | +1022 | +450 | −272 |

That is not an estimate with uncertainty around it. It is noise that changes sign
depending on which handful of days you include.

**A second, independent kill.** Even under the outlier-robust winsorised estimate — where
no days are dropped at all — 2025 gives **+801** and 2026 gives **−272**. Opposite signs
across eras. §2.1: *era-flips kill*.

## What the 2025 "textbook signature" actually was

The three days driving 2025 are **2025-04-07, 04-09, 04-10, 04-11** — the April 2025 tariff
week. Window moves of +343, −225, −199 and +155 points against a normal daily sd of 47.9,
including a prior-day return of **+11.8%**.

The signature was a macro-policy shock, not dealer inventory. That single fact explains the
whole arc of this candidate: why 2025 looked textbook, why 2026 looked like it had
"drifted up," and why the quintile means were so unstable. Quintile means are outlier-
sensitive by construction, and 2025 had extraordinary outliers pointing one way.

## The three-way test, for the record

Without the fragility override, trial 2 returns **INCONCLUSIVE ON POWER**:

| | 2025 | 2026 |
|---|---|---|
| n | 257 | 139 |
| b_neg (fade on the downside) | −206 (p₁ 0.385) | −555 (p₁ 0.220) |
| b_pos | −1288 | −153 |
| D = b_neg − b_pos | +1082 | −402, 95% CI [−2611, +1807] |
| power to detect D₂₅ | 34% | 25% |

2026's CI contains both zero and the 2025 estimate, so the sample cannot separate the
hypotheses — 932 days would be needed at 80% power against 139 available. **But fragility
overrides**, and it is decided on evidence already in hand. No waiting is required.

## Process findings — these outlive the candidate

1. **Kill criterion 2 is unsound as written and must be fixed before it is used again.**
   `docs/DIAGNOSIS-LDN-INV-01-power.md` §2: tested literally, *"top-quintile statistically
   indistinguishable from bottom-quintile"* **fires on the discovery era** (2025,
   02:00→06:00, p = 0.132). A criterion phrased as failure-to-reject fires whenever a cell
   is small. It tests the sample, not the strategy. Absence claims must be equivalence
   claims — the CI must exclude the discovery estimate, not merely contain zero. This
   affects all nine candidates. **Brake's knob; recommend fixing before candidate 2.**
2. **Quintile designs are outlier-fragile and use 40% of the data.** The whole arc of this
   candidate was an artifact of that choice. Recommend continuous specifications with a
   declared fragility check as the default L0 shape.
3. **Run drop-top-3 at L0, not at L4.** It cost one run here and would have killed this
   candidate on day one, before the refinement debate existed.

## Trial ledger impact

**4 trials** now sit in the LDN-INV-01 family: trial 1 (quintile census, 2 era directions)
and trial 2 (continuous, 2 era directions). The power diagnostic is **not** a trial — no
search, no tuning, no rule proposed. These four count in the DSR denominator for any future
candidate in the overnight-structure/inventory family per §2.4.

## Recommendation to Angus

**Tombstone LDN-INV-01.** No refinement, no re-test trigger, no shelf. The pre-committed
joint conditioning (`inv_skew_0255` × σ-location) should **not** be run: fragility is
decided, and conditioning further on a sample whose signal is three tariff-week days would
be fitting the shock, not the mechanism.

The mechanism itself is not disproven in general — the NY Fed work stands, and a real MOC-
imbalance feed remains the v2 upgrade path named in the original thesis. What is dead is
*this* proxy (`prior_rth_ret`) on *this* sample. If the candidate returns, it returns with
a real imbalance feed and a fresh prereg.

## What this does not establish

- Parity: the census reproduction in `DIAGNOSIS-LDN-INV-01-power.md` §1 differs from trial
  1's ledgered figures by 1.2–4.6 pts, unreconciled. Trial 2 computes D₂₅ **within its own
  run**, so the comparison is internally consistent regardless — but trial 1's exact
  figures should still be reconciled.
- The hinge at zero is a declared modelling choice, not a measured breakpoint.
- L0 structure only. No costs, stops or targets. Nothing here is tradeable evidence in
  either direction.
