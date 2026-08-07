# VERDICT — vp-excursion-census (Job 1) — 2026-08-07

```
VERDICT      NO LIFT (attributable to the level). The failed-auction
             conditional lift exists arithmetically, is era-stable in
             sign, and FAILS BOTH PRE-REGISTERED PLACEBOS: week-old
             levels produce ~5x the lift, and 19 of 20 random level
             placements produce more lift than the real value area.
             The volume-profile level is not doing the work.

MECHANISM    Conditioning on "close beyond a line, quick close back"
             selects moments of local mean reversion at ANY line. POC
             sits inside the value area — in the direction of the
             snap-back — so P(touch | quick rejection) exceeds P(touch)
             for any interior target. Nobody pays for the level; the
             conditioning event pays for itself. Stale and random
             levels show MORE lift because the real profile's
             unconditional rotation rate (56-60%) is already near its
             ceiling — exactly the confound section 0 of the spec
             warned the absolute hit rate would be.

EVIDENCE     n = 1,049 excursions / 747 clusters / 290 sessions
             (FIT 2025-06-02 -> 2026-07-15, tape end; spec end
             2026-07-31 unreachable). Sides never pooled.
             Unconditional P(touched_poc), clustered:
               above 0.603 [0.553, 0.651]   below 0.561 [0.510, 0.611]
             Median t_touched_poc: 21 min above / 20 min below.
             Lift at canonical K=15 (cluster-bootstrap 95% CI):
               above +0.097 [+0.069, +0.127]  (clustered headline +0.079)
               below +0.060 [+0.035, +0.086]  (clustered headline +0.062)
             poc_before_stop_S lifts rise monotonically S=10..80 from
             +0.047 to ~+0.11 (above); all CIs exclude zero. Asymmetry:
             above-side lift consistently exceeds below-side (Table D
             result in its own right).
             All artifacts: output/vp_census/ (tables_rates.csv,
             tables_lift.csv, table_e/f/g, placebos.csv,
             construction_gate.csv, gate_report.md, trial_ledger.csv).

NULLS        Stale-level placebo (levels from 5 sessions earlier):
               above +0.391 vs real +0.079 — FIVE TIMES the real lift.
               below +0.336 vs real +0.062.
             Shuffled-level placebo (20 draws, relative position in the
             overnight range drawn from a donor session):
               above: median +0.110, range [+0.076, +0.136];
                      real +0.079 sits at draw-rank 1/20 from the BOTTOM.
               below: median +0.094, range [+0.061, +0.159]; rank 1/20.
             With 20 draws the p-floor is 1/21 = 0.048; the design
             cannot distinguish "worst" from "typical-low" more finely,
             and does not need to — the real level UNDERPERFORMS its
             own placebo distribution.

SURFACE      Flat plateau everywhere. K in {5..60}: above 0.081-0.097,
             below 0.039-0.065, no interior peak — K is not a real dial
             ("instant" carries no information at 1m resolution beyond
             K>=5). Bin width {0.25, 1.0, 2.0}, VA% {68, 70, 75},
             expansion {paired, single}: headline moves by <0.03 with
             overlapping CIs; canonical settings sit interior. POC
             bin-instability: 17/290 sessions (5.9%, under the 20%
             flag threshold); excluding them moves the headline by
             <0.002 (sensitivity in this doc's build log).

ERA          Sign agreement 7/7 K values on both sides (2025H2 vs
             2026H1; above +0.110 vs +0.082 at K=15, below +0.061 vs
             +0.058). K-RANKING disagrees across eras (Spearman -0.72
             above, -0.07 below) — expected ordering noise on a flat
             plateau, but by the letter of section 5.5 the K-structure
             claim alone would be UNRESOLVED. Immaterial: the placebo
             failure governs regardless of K.

GAPS         (1) Tape ends 2026-07-15; spec FIT end was 2026-07-31.
             (2) Construction gate: matched flip rate 3.7% PASSES the
                 5% bar, but 22.3% of excursions exist under only one
                 construction and level deltas have a violent tail
                 (p90 |dPOC| 92 pts — bimodal overnight profiles put
                 POC on different modes). Bar-approx is a valid
                 substitute for CLASSIFICATION, not for level
                 placement on bimodal nights.
             (3) ~10 early-close holiday sessions have truncated
                 census windows (outcomes measured to the last bar).
             (4) G3 raw-contract cross-check covers through 2026-01-31
                 (raw pull end); later sessions inherit the master
                 file's volume-roll construction per
                 docs/CONTRACT-ROLL-DATES.md.
             (5) poc_before_stop_S same-bar (POC touch + stop-extension
                 in one bar) scored against the hypothesis.
             (6) Trial ledger holds 148 rows; the 126 construction
                 configurations are highly correlated variants of one
                 idea — effective independent trial count is ~2-3
                 (two sides, one family), not 126.

NEXT         None inside this family — a NO LIFT verdict is a complete
             outcome (spec section 8). No Job 2 prereg will be written
             on this evidence. REOPENING BURDEN, stated now: any
             revival must show real levels beating PROXIMITY-MATCHED
             random levels (placebo levels forced to the same
             distance-from-price distribution as the real ones), with
             acceptance bar: real lift above the 95th percentile of
             >=100 matched draws, pre-registered, on data this census
             has not consumed. The sealed 2023/24 census exists
             (output/sealed/, write-only, never read) and stays sealed;
             it answers a different question and this verdict spends
             no look on it.
```

Every figure above traces to a named artifact under `output/vp_census/`.
The sealed holdout was computed and written by
`scripts/vp_census/build_holdout.py` with no statistic printed or read;
`scripts/vp_census/report.py` refuses `--unseal` without
`docs/PREREG-vp-excursion-census.md` (verified: exit 2).

Gates: G1-G6 ALL PASS (`output/vp_census/gate_report.md`). Section 2.4
construction gate: PASS at 3.7% matched flip rate (bar under 5%), with
the tail caveat recorded in GAPS item 2.
