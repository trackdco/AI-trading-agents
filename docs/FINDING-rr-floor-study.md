# FINDING — the rr_floor study (2026-07-26): investigated, recommended, RETRACTED same day

**Verdict: `rr_floor` stays 2.0.** This standalone exists because the study ended up scattered
across four addenda of `FINDING-late-window-orderflow.md` — this is the index and the summary.

## The arc
1. Leak-hunt ablation flagged rr_floor (apparent −33R from enabling 2.0). Suspicious → deeper.
2. Engine read: rr_floor is a **target-picker** (`walk_menu` takes the first level clearing the
   floor), not a veto — so it sets exit geometry on every trade, not just admission.
3. Decomposition (floors 2.0/1.5/1.0): admission correct (−15.9R from sub-2R-only trades, both
   years); target geometry apparently **+37.8R** on shared fills → net +23.4R → recommended 1.5.
4. Angus: *"what's the MAE on these low-rr winners… lots to dissect here."* Dissection found one
   "save" at **29.21R** — impossible for a 1.5R-target trade.
5. **The freak:** 2026-02-19 09:46, 6.0pt stop (slipped the 7pt floor on fill improvement),
   sparse level menu. Floor 2.0 demanded 245pt/41R → stopped (−1.0R); floor 1.5 picked
   175pt/29R → hit (+29.2R). One coin-flip between two lottery tickets.
6. **Ex-freak: geometry +7.5R with years disagreeing (2025 +13.2 / 2026 −5.7); net book −6.9R.**
   Recommendation withdrawn. Angus's 2R floor survives its own audit.

## What survives (measured at the 2.0 floor, unaffected)
- 10-minute dead-trade cut (+6.7R both years; replaces the 3-min Layer-2d horizon — package item)
- Post-target extension (~half of winners run ≥1R past the exit) → the partial+trail study
- Admission finding: sub-2R-only setups lose → reinforces the 2.0 floor
- Early-golden d15∧wall subset (blind OOS 6/6 green — separate analysis)

## What ships instead: two mechanical guards
1. `walk_menu` target sanity clamp — reject targets demanding > K·R (the freak needed K ≤ 25)
2. Re-assert `min_stop_points` against the ACTUAL fill (the 7pt structural floor was slipped)

## Process lesson
The decomposition and the dissection ran on the SAME simulations — shared substrate, shared
freak, agreeing for the same wrong reason. "Independent confirmation" requires disjoint
substrates. What caught it: outlier quarantine + re-run-without + per-year signs. Third
plausible finding killed today (−2R halt, late-window fade subset, rr 1.5); the survivors ship.

## Files
`scripts/rr_floor_decomp.py` · `scripts/mgmt_dissect.py` · `scripts/loser_forensics.py` ·
`FINDING-late-window-orderflow.md` addenda b/c/d/f · `output/mgmt_rr*.parquet`, `rr_floor_*.csv`
Hosted walkthrough: the rr-floor-study artifact page (Angus's gallery).
