# DIAGNOSIS — LDN-INV-01, trial 1: can the sample decide kill criterion 2?

**For Brake's verdict. Diagnostic, not a trial** — no threshold tuned, no rule proposed,
nothing searched. Reproduce with `python -m scripts.ldn_inv01_power`.

**Sealed-span guard:** 2023/24 dropped by `fit_only()` and asserted gone. No holdout look.

---

## 1. Parity — read this before quoting any number below

Reproducing the trial-1 census from raw (substrate + master candles, prereg windows):

| cell | ledger | this run | Δ |
|---|---|---|---|
| 2025 q0 02:00→06:00 | +20.7 | +19.5 | −1.2 |
| 2025 q0 03:00→04:00 | +17.6 | +13.0 | −4.6 |
| 2025 q4 02:00→06:00 | −3.8 | −5.5 | −1.7 |
| 2025 q4 03:00→04:00 | −13.0 | −10.6 | +2.4 |
| 2026 q0 02:00→06:00 | +17.9 | +15.7 | −2.2 |
| 2026 q4 02:00→06:00 | +42.0 | +40.6 | −1.4 |

Same signs, same structure, same story — but **not to the decimal**. Likely causes:
boundary-minute selection (this run takes the first/last available close within a 6-minute
tolerance of each boundary) or DST-mismatch-day handling, which the prereg's known-limits
section flags as analysed separately. **This is a parity gap, not a pass.** Every
conclusion below is robust to a ±5pt shift, but the exact figures should be reconciled
against the census code before either version is quoted as authoritative.

## 2. The finding that matters: criterion 2 is unsound as written

Criterion 2 reads: *"Asymmetry absent: top-quintile drift statistically indistinguishable
from bottom-quintile."* Tested literally, **within** each era:

| era | window | spread | p | criterion 2 |
|---|---|---|---|---|
| 2025 | 03:00→04:00 | +23.6 | 0.038 | distinguishable |
| **2025** | **02:00→06:00** | **+25.0** | **0.132** | **FIRES** |
| 2026 | 03:00→04:00 | −5.9 | 0.650 | FIRES |
| 2026 | 02:00→06:00 | −24.9 | 0.415 | FIRES |

**Criterion 2 fires on the discovery era.** On the headline window, in the year the ledger
calls a "textbook inventory signature," the criterion that is supposed to kill the
candidate is satisfied. It is not discriminating between eras — it is discriminating
between sample sizes and window variance.

A criterion phrased as "statistically indistinguishable" fires automatically whenever a
cell is small, because failing to reject is the default at low power. As written it tests
the sample, not the strategy.

**Fix (Brake's knob):** absence-of-effect must be an *equivalence* claim, not a failure to
reject. Criterion 2 should require the confidence interval on the era's spread to **exclude
the discovery-era effect**, not merely to include zero.

## 3. Power — what this sample can and cannot see

| window | 2025 asymmetry | 2026 within-cell sd | n/cell | power to see the 2025 effect | min detectable @80% |
|---|---|---|---|---|---|
| 03:00→04:00 | +23.6 | 48.5 | 28 | **44%** | +36.3 (1.5×) |
| 02:00→06:00 | +25.0 | 114.2 | 28 | **13%** | +85.5 (3.4×) |

Both cells sit below the §2.2 floor of n ≥ 30. On the headline window the test is
effectively blind — it would miss the 2025 effect six times out of seven.

**But the concentrated window says something real.** Comparing 2026's observed spread
against the 2025 effect: **z = −2.28, p = 0.023 — distinguishable.** So on 03:00→04:00 the
2025 asymmetry did *not* persist at its 2025 magnitude. That is not a pure power artifact,
and it is the strongest evidence against the candidate. (On 02:00→06:00 the same comparison
gives p = 0.102 — not distinguishable, consistent with the 13% power.)

Two distinct questions, two different answers:
- *Is 2026's q0 different from its q4?* No (p = 0.65) — **underpowered**.
- *Is 2026's spread different from 2025's?* Yes on the thesis window (p = 0.023) — **something changed**.

## 4. What would settle it

| | 03:00→04:00 |
|---|---|
| validate-era days needed @80% power | ~331 |
| validate-era days available | 139 |
| shortfall | ~192 days (**~9 trading months**) |

**The practical consequence: running the pre-committed refinement now cannot produce a
PASS.** Whatever joint conditioning on `inv_skew_0255` × σ-location discovers, the 2026
era has 28 days per cell and cannot confirm it. The refinement would spend ledger trials —
and, via the inverse pass, double them — to reach a result that is unconfirmable by
construction, while inflating the DSR denominator for every later candidate in this family.

**A cheaper power upgrade exists.** The quintile design uses 2/5 of the sample (56 of 139
days in 2026). A continuous test — regressing window return on `prior_rth_ret` across all
days, with the asymmetry as an interaction term — uses every day and would materially raise
power on the same data. The prereg already calls the quintile split "descriptive" and
specifies trailing-252-day quantiles for the tradeable L1 rule, so this is within the
thesis. It changes the test, so it needs declaring first.

## 5. Recommended verdict (Brake's call)

**INCONCLUSIVE ON POWER** — blocks like FAIL per VALIDATION-PROCESS §5, with a different
follow-up: this is a data problem, not a design problem.

1. **Do not fire criterion 2 as written.** It fires on the discovery era; applying it now
   would tombstone the candidate on a defect in the criterion.
2. **Re-specify criterion 2** as an equivalence test before it adjudicates anything —
   this is a §2 knob and it affects every candidate, not just this one.
3. **Do not run the refinement yet.** It cannot produce a confirmable result at n=28/cell,
   and it costs ledger trials that raise the deflation bar for the whole family.
4. **Shelve with a re-test trigger** rather than a tombstone: revisit when the post-2025
   era reaches ~331 census days (~9 trading months), or immediately if the continuous-test
   redesign in §4 is declared and passes prereg.
5. **Record honestly** that on the thesis window the 2025 asymmetry did not persist at
   magnitude (p = 0.023). That is real evidence against, and it should sit in the ledger
   whatever the eventual verdict — it is the fact that will decide this candidate when the
   sample can finally speak.

## 6. What this does not establish

- The parity gap in §1 is unreconciled; figures are directionally sound, not authoritative.
- Nothing here says the mechanism is false. It says this sample cannot adjudicate it, and
  that the one comparison with enough power points the wrong way.
- The four windows overlap and are not independent; the consistent negative 2026 spread
  across all four is suggestive, not four confirmations.
