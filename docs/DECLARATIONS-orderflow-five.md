# DECLARATION — THE FIVE ORDER-FLOW MEASURES AT ENTRY

2026-08-08, written and committed BEFORE the build and before any
outcome is read. Fit-only, no holdout, report-only, nothing adopted.

## WHY THIS IS A DIFFERENT KIND OF TEST

Everything tested on this family so far has been a SEARCH — up to 8,721
candidate combinations, where the best result is chosen for looking
best and therefore has to be judged against a permutation null. This is
not that. **The trader named these five measures in advance, from his
own trading, before seeing any result.** That makes it a pre-specified
hypothesis test: ordinary evidence applies, and a positive result means
what it appears to mean.

Test count is stated up front and is small: 5 singles + 10 pairs + 1
full stack = 16 constructs x 3 mechanisms = **48 tests** (sessions
reported alongside but the mechanism split is the declared primary, per
the trader: *"per setup type, as we have 3 different distinct types. it
makes no sense to generalise findings over all 3"*). At 95% that is
~2.4 expected false clears, so a lone isolated clear is still weak — a
coherent pattern across related constructs is the thing to look for.
A permutation null is reported as context, not as the gate.

## THE FIVE, taken from the old canon's own scorer

Source: `src/canon/scorer_ny.py::checks`. Reproduced faithfully, with
the ORIENTATION DEFECT corrected where it applies (see below).

| # | name | canon bit | definition at the entry minute |
|---|---|---|---|
| 1 | `WALL_AHEAD` | `D` | a depth wall exists AHEAD of entry — in the trade's path (`above` for a long, `below` for a short). **Note: this is the wall in front, NOT the support wall behind; earlier race-census work saved only the support side and could not express this.** |
| 2 | `WALLSZ` | `WALLSZ` | that ahead-wall's size >= **7.0** contracts (canon's `Q_WALLSZ_MIN`, taken as-is, not re-tuned) |
| 3 | `CVD_CONF` | `Tc` | `d15_conf == 1` — 15-minute cumulative delta agrees with the trade direction |
| 4 | `FILL_DELTA` | `T2a` | `thru_delta_conf == 1` — the entry candle's own delta agrees with the trade direction |
| 5 | `NO_OPP` | `T2b` | `bp5opp == 0` — no sustained opposing pressure in the prior 5 minutes |

**Canon bits deliberately NOT included, and why:** `AGE`
(`on_extreme_age`), `TRIG` (`trigdens_30`), `LONSLOPE` (`lon_slope_d`),
`G` (`ent_vs_vwap_sd_dir`), `W` (wall behind absent). These are canon
gates but are not "order flow at entry" as the trader framed this test;
including them would widen a declared hypothesis after the fact. They
remain available for a separate declared test.

## THE ORIENTATION CORRECTION, applied

Confirmed by independent audit (`docs/audit-deltaz-orientation.md`) and
by direct measurement: `delta_z` in `flow_features` is raw-signed
(longs mean +1.217, shorts −1.170) and the original CONCORD scored
`delta_z > 0` as agreement — **counting BUYING pressure as confirmation
on SHORT trades**, exactly as the trader put it. Every measure above is
expressed relative to the TRADE's direction. `d15_conf`,
`thru_delta_conf` and `bp5opp` are already direction-oriented in
`flow_features`; the ahead/behind wall split is oriented here by
construction.

## WHAT IS REPORTED, per mechanism (M1 / M2 / M3), never pooled

For each of the 5 singles, all 10 pairs, and the full 5-stack:
- **fire rate** — how often it fires at all, and how often ALONE vs
  alongside others (the trader's explicit ask: *"how often does that
  fire. how often does it go by itself"*)
- **n fights and n distinct days**
- **win rate AND EV together** (Law 3 — a high win rate with flat EV is
  a refutation, not a finding; BR-20 has caught this repeatedly)
- **P(reach 3R)** — the decision-relevant metric, because the trader's
  actual exit (75% at 3R + trail) needs **28.3%** to break even and the
  unselected population delivers **25.1%**
- day-clustered bootstrap 95% CI (seed 20260807, 2000 draws)
- the same figures under the real exit (`real_out`) as well as the
  structural target

## COVERAGE, stated before results

Depth exists on 229 of 290 days (~80% of fights); the wall features
specifically resolve on ~40% of fights. **Any WALL_AHEAD / WALLSZ
result is therefore a sub-population finding and will be labelled as
one.** The three flow measures have ~100% coverage. Pairs mixing a wall
measure with a flow measure inherit the wall coverage.

## THE BAR

A measure or pair is reported as WORKING only if, within a mechanism:
P(3R) exceeds 28.3% with the day-clustered CI clearing, AND EV and win
rate move together, AND the subset has >= 25 fights over >= 15 days.
Anything else is reported as it lands, including nulls.

Standing: fit-only, no holdout, report-only, nothing adopted.
