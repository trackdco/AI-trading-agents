# PARITY REPORT — first real capture, 2026-07-29 (R10b)

**Result: FAIL, 93.06% gate agreement (bar: 100%). DO NOT ARM stands.** This report is
the diagnosis of that failure and the experiment that decides what it means. For Angus's
ruling — see §4.

Inputs: `capture_2026-07-29.jsonl` (Pat's VPS, Sierra/Rithmic `.depth`, captured
2026-07-31 via `scripts/depth_capture.py`, scale 100× auto-detected) vs
`data/reference/depth_2026/nq_depth_2026-07-29_ny.csv` (Databento GLBX.MDP3 MBP-10,
condensed from Pat's raw pull). 180 archive minutes, 360 probes, 0 missing-from-live.

## 1. What the failure is NOT

Diagnosed 2026-07-31 (`diagnose` run over per-minute signed comparisons):

- **Not a scale/decode error.** The capture step auto-detected the box's 100× depth
  scaling; final book sanity (best bid/ask ≈ 28,026) correct.
- **Not systematic size inflation (implied-liquidity hypothesis rejected).** At matched
  price levels, **77.3% of sizes are byte-identical**; the live/archive size ratio has
  median **1.0000**; signed thickness delta has median **0** (mean +1.4, and live is
  thicker on only 43% of minutes — no directional bias).
- **Not a snapshot-convention bug.** Lag test: live-at-minute-M matches archive-at-M
  (median thickness gap 3.0) better than M±1 (6.5–7.0). Alignment is correct.
- **Not conflation loss.** Both books carry the full 10 levels per side every minute.

## 2. What it IS

Two honest views of the same book, photographed a split second apart, feeding a
knife's-edge feature:

- The books' visible top-10 price sets overlap at a median of 15/20 per minute — the
  book's *edges* differ at the sampling instant while the core is identical.
- The best bid/ask differ by exactly one tick on ~half the minutes (median −0.25) —
  sub-second skew between Sierra's write clock and the exchange event clock.
- The wall features are `argmax(size)` over the visible levels: a one-contract,
  one-instant difference can teleport "the wall." Worked example, 08:38: both books
  agree on the near book (4-lot @ 27873.25 max in the archive), but the live instant
  caught a far 7-lot @ 27800.00 inside its visible top-10 → wall_below jumps **73.25pt**
  on a single level. 4 of 180 minutes account for the large outliers.

## 3. The decisive experiment — vendor vs ITSELF

If sampling the SAME Databento raw file at each minute close vs 500ms earlier also
scores ≈93%, then the box's feed matches the vendor as well as the vendor matches
itself — the gap is the **noise floor of the gate's own sampling**, and the live feed is
clean. If vendor-vs-itself is ≈100%, the live feed genuinely differs beyond timing noise
and needs deeper diagnosis before anything arms.

Runbook (Pat's Mac, where the raw file lives; ~5 min):

    python3 scripts/parity_noise_floor.py ~/Downloads/glbx-mdp3-20260729.mbp-10.dbn --day 2026-07-29

The probe mechanics are self-checked (`--selfcheck` = 100.00% by construction).

## 4. Decision structure (ANGUS)

This is a ruling, not an engineering fix, and it waits for §3's number:

- **Floor ≈ capture's score** → the 100% bar is unachievable by construction against a
  different clock. Re-spec R10b with evidence (e.g. "gate agreement within X% of the
  measured same-vendor noise floor, no systematic size/alignment bias" — the bias checks
  in §1 stay hard requirements at 100%). The book's measured edge already contains this
  same sampling noise from the vendor side.
- **Floor ≈ 100%** → the live feed differs beyond timing noise. Candidates then: Rithmic
  conflation on bursts, stale-level ghosts (dropped deletes), clock skew beyond jitter.
  No arm until understood.

Nothing here relaxes any gate by itself. The DO NOT ARM verdict stands until the floor
number exists and Angus rules on it.
