# VERDICT — LDN-SWP-01 (asia-sweep-reversal + asia-sweep-continuation)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_swp01_census`.

**Sealed 2023/24: untouched.** `fit_only()` drops them and asserts they are gone. **No
holdout look taken.**

**Bars caveat:** the §2 numbers are still `[PROPOSED]`. The conclusions below are
threshold-independent — they rest on effect sizes near zero and on a specification defect,
not on where a p-value bar sits.

---

## VERDICT

| candidate | verdict |
|---|---|
| **#3 asia-sweep-continuation** | **FAIL** — cleanly, under the declared specification |
| **#2 asia-sweep-reversal** | **FAIL** — declared test was invalid; causal re-measurement shows null |

**Neither candidate proceeds to L1.**

---

## 0. CORRECTION — the first run used the wrong session window

**Superseding the numbers in §1–§3 below.** The declared prereg hardcoded the outcome
window as 03:00–06:00 ET. That is not the London session:

- London is **08:00–10:00 Europe/London** = 03:00–05:00 ET normally, 04:00–06:00 ET in
  DST-mismatch weeks. The authority is `run_triggers_london.london_window_et(day)`.
- 03:00–06:00 ET is 08:00–**11:00** London — a three-hour window running an hour past the
  close.
- Hardcoding ET hours is item 1 on the burn list (`HANDOFF-london-rebuild.md` §7):
  *"the DST offsets between the two zones do not move together."*

Corrected re-run: `python -m scripts.ldn_swp01_london_only`. Same claim, same groups, same
decision rule, session boundary fixed and group P measured causally from the breach. The
converter also **recovers 30 DST-mismatch days** that the first run excluded (314 events,
up from 293). Windows actually used: 03:00–05:00 ET on 284 days, 04:00–06:00 ET on 30.

| era | n(D) | n(P) | mean D | mean P | Δ | p |
|---|---|---|---|---|---|---|
| 2025 | 134 | 71 | **+0.74** | **+4.89** | −4.15 | 0.583 |
| 2026 | 66 | 43 | **+4.39** | **+15.25** | −10.86 | 0.464 |

2026 95% CI on Δ: **[−39.91, +18.20]** — contains zero comfortably. Fragility gate
**fires** on 2025 (Δ −4.15 → +1.54 at drop-3), which is what a null looks like: noise
changes sign when you remove a few days.

**The verdict is unchanged, but the reason is now clean.** Both theses are refuted directly
by their own group means, on the correct window, with no artifact involved:

- **#3 continuation** needs `mean D` materially **positive**: it is **+0.74 and +4.39**
  points, against a session that moves tens of points. Nothing.
- **#2 reversal** needs `mean P` materially **negative**: it is **+4.89 and +15.25** —
  wrong sign and immaterial. Nothing.

Sections 1–3 are retained as the record of what was declared and what went wrong with it.
Their numbers should not be quoted.

## 1. What was declared, and what happened

The prereg (`PREREG-london-asia-sweep-pair.md`, committed 13:14:39Z) tested one question:
does the **timing** of an Asia-range sweep predict the direction of the London move?

- **Group D** — Asia extreme breached 00:00–03:00 ET (before deep liquidity).
- **Group P** — breached only after the 03:00 open.
- Outcome: 03:00→06:00 return, signed by sweep direction. Positive = continued.
- Primary: `Δ = mean signed_ret(D) − mean signed_ret(P)`; the claim was `Δ > 0`.

Population after declared exclusions (35 `dst_mismatch`, 6 post-open both-sides): **293
events** — 2025: 124 D / 72 P; 2026: 54 D / 43 P. All cells clear the n ≥ 30 floor.

## 2. The declared primary statistic is INVALID — a specification defect

`Δ` came back **−39.01 (2025)** and **−68.41 (2026)**, both p < 0.001, and it survived
every trim depth and winsorisation. A textbook-looking result.

It is an artifact of how I defined group P, and it should not be believed.

**Group P's breach lands a median of 47 minutes after 03:00** (mean 50.4, 44 of 115 after
60 minutes). The outcome window *starts* at 03:00. So the move that causes the breach is
inside the window being measured, and signing the return by "which side broke" makes the
outcome partly definitional — a day that rallies breaks the high and scores positive by
construction.

This violates the standing causality rule (§2.5: *"decision at minute t uses only ≤ t
information"*). **The defect is mine, introduced in the prereg, and it was not caught
before the run.**

**Causal re-measurement** (diagnostic, not a trial — breaches within the first 30 minutes
only, return measured *from* the breach forward):

| group | 2025 | 2026 |
|---|---|---|
| D — dead-hour sweep (clean as specified) | **+3.43** | **+1.16** |
| P — post-open, as declared (contaminated) | +42.44 | +69.57 |
| P — post-open, measured causally | **+2.84** | **+1.57** |

The effect vanishes entirely. Both groups are flat in both eras.

## 3. Why both candidates fail

**#3 continuation — FAIL, cleanly.** Group D needs no correction: the sweep is determined
00:00–03:00, wholly before the 03:00–06:00 outcome window. No circularity. Its thesis
predicts that dead-hour sweeps *extend* — that `signed_ret(D)` is materially positive.
Measured: **+3.43 and +1.16 points**, against a session that moves tens of points. That is
nothing, consistently, in both eras, on 124 and 54 events. This is a clean refutation under
the declared specification.

**#2 reversal — FAIL.** Its thesis predicts post-open sweeps *revert* — `signed_ret(P) < 0`.
The declared test cannot adjudicate that (§2 above). The causal re-measurement gives **+2.84
and +1.57** — not negative, not positive, nothing. That measurement is a diagnostic rather
than a declared trial, so the formally correct status is *declared test invalid*; but the
direction is unambiguous and there is no version of this data in which post-open sweeps
revert. Re-running it under a corrected prereg would spend trials to confirm a null already
visible.

**The narrow-Asia secondary** adds nothing: 2025 Δ −40.30 (p<0.001), 2026 Δ −48.28 (p 0.069,
n 11/6 — under the floor). It inherits the same contamination and is not evidence.

## 4. The finding that outlives the candidates

**The fragility gate cannot catch a specification defect.**

LDN-INV-01 taught us to run drop-top-3 first, and that check works — it killed a candidate
whose signal was three tariff-week days. Here it passed cleanly at every trim depth, on a
result that was *entirely* artifact.

The reason is structural: **circularity is robust.** Dropping outliers does not remove a
definitional relationship; if anything it sharpens it. A specification defect produces a
result that is large, significant, stable and completely meaningless — and it will clear
every robustness check we currently run first.

**Recommendation (a §2 knob):** add a **causality audit** to the L0 gate, beside the
fragility ladder. One question, asked before any result is read:

> *Is every variable used to define the event, the direction, or the grouping determined
> strictly before the outcome window opens?*

For this census the answer was no, and it takes thirty seconds to ask. It would have caught
this before the run rather than after.

## 5. Trial accounting

**4 trials** into LDN-SWP-01 (primary × 2 era directions, narrow-Asia secondary × 2), as
declared. The causal re-measurement is **not** a trial — no search, no tuning, no rule
proposed; it is a validity check on the declared test.

Running family total: **8 trials** (4 LDN-INV-01 + 4 here). These count in the DSR
denominator for future session-structure candidates per §2.4.

## 6. Recommendation to Angus

**Tombstone both.** Candidates 2 and 3 close together, as one family, as they were opened.

Two of the nine are now dead on structure measurement alone, at a cost of two censuses and
no holdout looks. That is the pipeline working as designed.

The mechanisms are not disproven in general — the stop-pool logic is sound and widely
documented. What is dead is the claim that **sweep timing predicts London direction** on
this sample. If either returns it needs a genuinely different trigger definition (acceptance
tests, flow confirmation at the extreme), a causal specification, and a fresh prereg.

## 7. What this does not establish

- L0 structure only. No costs, stops, or targets; nothing here is tradeable evidence in
  either direction.
- The causal re-measurement uses a 30-minute breach cutoff chosen *after* the defect was
  found. It is diagnostic, not confirmatory, and is reported as such.
- 35 `dst_mismatch` days were excluded by design and are unanalysed.
- `sweep_side_dead` counts a wick through the extreme as a breach — deliberate (the stop
  pool is reached by the wick), but it is not an acceptance test, and both candidates'
  L1 skeletons call for acceptance logic this census does not implement.
