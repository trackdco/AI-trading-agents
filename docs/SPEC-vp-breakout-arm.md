# SPEC — Job 2: Breakout Arm (`accepted_K`)

**Prerequisite:** the Job 1 census on `claude/evening-chat-ipjsr6` (f9e1c53d, 4ab34b62).
**Scope:** analysis only. No new ingestion, no new profile construction, no new census pass over raw bars except the forward walk in §2.
**This is not a revival of the failed-auction arm.** That verdict stands. `accepted_K` is a different population with a different outcome, and the POC-rotation placebo said nothing about it.

---

## 0. Why this is a separate question

Job 1 measured rotation *to* POC. The breakout arm's claim is the opposite: price leaves the value area, does **not** come back, and continues. The outcome column is continuation, not rotation, so nothing in the Job 1 placebo result transfers — in either direction. It is neither supported nor condemned; it is unmeasured.

Prior is low. It shares the levels that just failed to attribute. Budget an afternoon, not a week.

---

## 1. Population

From `output/vp_census/excursions.parquet`:

- `accepted_K` = `NOT failed_K`, i.e. no 1-min close back inside `[val, vah]` within `K` minutes of `excursion_start`.
- Canonical `K = 15`, swept over the same `{5, 10, 15, 20, 30, 45, 60}`.
- Sides never pooled. Clustered and per-excursion figures both reported, clustered governs.
- Report `n` per cell up front. `accepted_15` is the complement of a population that ran 1,049 excursions, so some cells will be thin — anything under 30 clustered observations is UNDERPOWERED and is not ranked.

---

## 2. New outcome columns — scale-normalised

The rotation arm had a natural target (POC). The breakout arm has none, so targets must be expressed in units that survive a varying overnight range. **The unit is value-area width**, `W = vah - val`, per session.

For each excursion, walking forward from `excursion_start` to 16:00 ET:

| Column | Definition |
|---|---|
| `mfe_W` | Max favourable excursion beyond the breached level, in units of `W` |
| `reached_cont_T` | For each `T` in {0.25, 0.5, 0.75, 1.0, 1.5, 2.0} × `W` beyond the breached level: reached or not, and minutes to it |
| `returned_to_poc` | Did price touch POC at any point after `excursion_start` (the failure mode for a breakout) |
| `cont_before_reentry_T` | **Load-bearing.** For each `T`: did price reach `T` before a 1-min close back inside the value area |
| `cont_before_stop_S` | For each `S` in {10, 20, 30, 40, 60, 80} ticks back inside the value area from the breached level: did price reach `T = 1.0W` before hitting `S` |
| `t_first_reentry` | Minutes to first close back inside, `NaN` if never |

`cont_before_reentry_T` and `cont_before_stop_S` give the payoff shape across every plausible target and stop without building an entry model — same device as Job 1, same reason.

---

## 3. Required analysis

Wilson 95% intervals on every proportion. No point estimates.

- **Table A — unconditional.** Over *all* excursions: `P(cont_before_reentry_T)` for each `T`, `P(cont_before_stop_S)`.
- **Table B — conditional on `accepted_K`.** Same columns, one block per `K`.
- **Table C — lift**, with a CI on the difference. Intervals spanning zero are reported as null.
- **Table D — by side.** Never pooled.
- **Table E — by era.** 2025-H2 vs 2026-H1. Sign or rank disagreement → `UNRESOLVED`.
- **Table F — response surface** across `K`, bin width, VA%. Job 1's surface was featureless; state plainly whether this one is too.
- **Table G — power.** `n` per cell, clustered.

Additionally, and cheaply:

- **Table H — complementarity check.** For each excursion, the Job 1 rotation outcome and the Job 2 continuation outcome are mutually exclusive by construction at any given target. Report the joint distribution: rotated to POC / continued to `1.0W` / did neither by 16:00. The "neither" fraction is the honest measure of how often an excursion is simply not an event.

---

## 4. Placebos — build the proximity-matched harness here

Job 1's placebos were not proximity-matched, which is why "random levels beat real levels" overstated the case and why the reopening burden specifies the fix. **Build that fix now, in this job, as a reusable module.** It is the standard for everything downstream, not a one-off.

1. **Proximity-matched random levels.** Draw synthetic VAH/VAL/POC whose distances from the 09:30 price — and whose `W` — match the empirical distribution of the real profiles. 100 draws minimum. Report the real result's percentile.
2. **Stale-level placebo,** retained as a comparator so the two can be read side by side and the Job 1 confound is documented rather than repeated.

Emit as `src/research/placebo.py` with a stated interface, so the next model gets it for free.

---

## 5. Gates

G1–G6 from Job 1 apply unchanged, plus:

- **G7 Population reconciliation.** `n(failed_K) + n(accepted_K) == n(excursions)` for every `K`, every side. Any drift means the classification is not total.
- **G4 Determinism** specifically: all sorts `kind="mergesort"`.

Holdout stays sealed. Job 2 does not unseal; §6.4 of the Job 1 spec still governs and `report.py --unseal` must still exit 2.

---

## 6. Trial ledger and verdict

Append to `output/vp_census/trial_ledger.csv` — do not start a new one. The Job 1 configurations and these share an idea and the effective independent trial count is joint, not per-job.

`docs/VERDICT-vp-breakout-arm.md` in the §8 format. `NO LIFT` is a complete outcome.

If the verdict is `NO LIFT`, write one further paragraph: the combined statement that neither arm of the transcript's model attributes to the overnight value area, with the base rates that establish it. That paragraph is the durable artifact — it becomes a null in the base-rate library and saves the next person the same week.
