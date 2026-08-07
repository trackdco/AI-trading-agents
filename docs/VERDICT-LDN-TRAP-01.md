# VERDICT — LDN-TRAP-01 (level-trap-fade)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_trap01_census`.

Declared `PREREG-london-level-trap-fade.md` at **15:21:38Z**, run unchanged.
**Sealed 2023/24 untouched. No holdout look.**

---

## VERDICT: **FAIL** — fragility gate fires, and the primary is a clean, well-powered null.

**This is the first candidate whose null means something.** The two before it were killed by
an outlier cluster and by a specification defect; this one had real statistical power and
simply found nothing.

---

## The result

| era | n | mean signed_ret | p (one-sided) | |
|---|---|---|---|---|
| 2025 (discover) | 161 | **−2.30 pts** | 0.721 | wrong sign |
| 2026 (validate) | 89 | **−2.64 pts** | 0.621 | wrong sign |

The claim was that price continues **away** from a reclaimed level — `mean > 0`. It is
negative in both eras, immaterial in both, and nowhere near significance.

**The distribution says it plainly:** median −0.88 pts, **48% of events positive**, sd 62.5.
A coin flip with a rounding error.

**Fragility gate fires** in both eras — sign flips at drop-3 (2025: −2.30 → +0.70; 2026:
−2.64 → +0.36). That is the signature of noise, not of an edge with outliers.

## Why this null is worth more than the last two

| | events | min detectable mean @80% power |
|---|---|---|
| 2025 | 161 | **+9.75 pts** |
| 2026 | 89 | +21.33 pts |

The discovery era could have detected a ~10-point edge and did not. For a trade whose
targets are overnight VWAP and mid-range — moves of tens of points — a real signature would
have shown. This is a **null on evidence**, not a null on power.

Contrast LDN-INV-01, where the validate era needed 331 days and had 139: there we could not
tell absence from invisibility. Here we can.

## The refinement does not rescue it

Declared secondary — first revisit vs second-or-later. The thesis predicts the fade works on
the **first** revisit (trapped defenders help) and inverts later (defenders spent):

| era | first revisit | later |
|---|---|---|
| 2025 | **−4.72** (n=102) | +1.89 (n=59) |
| 2026 | −2.36 (n=61) | −3.24 (n=28) |

The first-revisit cell — the one the thesis says should be strongest — is the **worst** cell
in 2025, and 2026 shows no split at all. The refinement points the wrong way where it was
supposed to be strongest.

## Per-level breakdown (descriptive, not verdict-eligible)

| level | n | mean |
|---|---|---|
| ONH | 129 | +2.91 |
| ONL | 77 | −12.99 |
| PDH | 24 | −4.90 |
| PDL | 20 | +6.89 |

Signs disagree across levels with no pattern the thesis predicts, on an sd of 62.5. **Do not
mine this table** — four cells, none pre-registered, is precisely the search that DSR exists
to deflate. It is reported for completeness only.

## Clean-run confirmation

Both defects found earlier in this program were checked for and absent:

- **Session window:** derived per day from `london_window_et()` — 08:00–10:00 Europe/London.
  No hardcoded ET hours. DST-mismatch days handled by the converter, not excluded.
- **Causality (prereg §3):** every variable — the four levels frozen at the open, the break,
  the reclaim minute `t`, the direction — is determined at or before `t`, and the outcome is
  measured over (`t`, window close]. Nothing defining the event is drawn from the interval
  being measured.
- **Levels frozen at the open**, deliberately: a rolling ONH/ONL would be partly defined by
  the move being measured.

So the failure is the candidate's, not the test's.

## Trial accounting

**4 trials** into LDN-TRAP-01 (primary × 2 era directions, secondary × 2). London program
running total: **12** (4 LDN-INV-01, 4 LDN-SWP-01, 4 here). These count in the DSR
denominator per §2.4.

## Recommendation to Angus

**Tombstone.** No refinement, no re-test trigger. The signature is absent at structure level
with adequate power, and the thesis's own refinement points the wrong way. Nothing about
entry mechanics, stops or targets recovers a directional edge that is not there — and the
candidate file itself rates crowding on this pattern as decades-old and heavily traded.

**4 of 9 candidates now closed**, at a cost of three censuses and no holdout looks.

## What this does not establish

- L0 structure only. No costs, stops or targets; the §2.5 cost stack applies from L1.
  Nothing here is tradeable evidence in either direction.
- Holding to the window close is a measurement convention, not the candidate's exit (VWAP /
  mid-range targets, 30–45 min stagnation kill). L0 asks only whether price drifts the right
  way; it does not.
- The break threshold (4 ticks) and reclaim window (15 min) were declared, not optimised. A
  signature living only at other values would be missed — the deliberate cost of not
  searching.
- The profile-structure level-quality variant (poor/flat extremes, equal touches, no
  rejection tail) was explicitly out of scope and remains untested. It needs a builder and
  a fresh prereg. Given the primary null and the inverted refinement, it is a weak
  candidate for that investment.
