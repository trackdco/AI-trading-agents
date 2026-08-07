# HANDOFF — Rebuilding the London canon (for Brake)

**From:** the NY rebuild, 2026-07-28→31 · **Owner:** Brake · **Sponsor:** Angus
**Goal:** put London through the exact discipline that just rebuilt and validated NY, so the
three-session book (2 London / pre / gold) stands on honest foundations end to end.

Read this whole file before running anything. The method is the deliverable — the NY numbers
came from the *discipline*, not from cleverness, and every shortcut listed in §7 was tried by
us and burned us.

---

## 1. Why this rebuild exists (60 seconds of history)

The old NY canon was built on a population silently mangled by a trade cap living *inside*
`simulate()` (pre-market consumed gold's slots on 56% of day-books), a 22pt entry-cancel that
deleted the best fills, and a corrupted input column feeding one of its checks. Every
threshold fitted downstream inherited those defects. The fix was not patching — it was
rebuilding in **layers, each gated before the next consumes it**:

```
L0  census      every structural trigger, no selection        gate: parity vs cached stream
L1  fills       every limit walked, no cancels enforced       gate: engine fill reproduction to the tick
L2  outcomes    every fill through the REAL engine, V8        gate: lookback outcome-invariance
L3  features    order-flow features, as-of-clean              gate: reproduce cached matrices to 1e-6
    trial       every check tested, fit-era vs out-era        gate: permutation null bars
L4  policy      caps/sizing/risk as POST-HOC causal walks     gate: causal (no lookahead) unit tests
```

NY result for context (your benchmark for "it worked"): raw structure breaks even; two wall
checks carry the edge (gold: wall-AHEAD exists = D; pre: NO wall behind = W); book validated
on sealed 2023/24 data it never saw — 13/13 and 6/6 months green, funded-sim never busts.

**London was never broken the way NY was** (it always had its own 2-cap in its own simulate()
call) — but its checks were never honestly trialed either, and after watching half of NY's
checks die under scrutiny, nothing London ships untested.

---

## 2. London specifics you must respect

- **Window:** 08:00–10:00 Europe/London, converted to ET per-day (03:00–05:00 or 04:00–06:00
  ET depending on DST misalignment). Use `scripts/run_triggers_london.london_window_et(day)` —
  never hardcode the ET hours. `src/desk/canon_runtime.book_for_clock` shows the live mapping.
- **Risk gate:** London Layer-0 is `risk >= 9.5pt` with **no upper cap** (`src/canon/scorer.py`
  `LON_RISK_MIN`). Do not import NY's 7–60. But TEST the London gate on the honest population
  the way we tested NY's (L2 by risk band) before trusting it.
- **Escalation:** old London L2b demanded score ≥3 on the 2nd+ trade. That is policy → L4,
  not something to bake into lower layers.
- **Existing pipeline** (all already span-generalized `--span fit|holdout`):
  `scripts/london_substrate.py`, `london_matrix.py`, `london_depth.py`, `london_canon.py`,
  `scripts/holdout_london_triggers.py` (5,873 sealed-day triggers already built, verified
  lookback-invariant at 30d), `output/london_canon_book.parquet` (the OLD book — treat as
  history, not truth; its exit stamps/reasons are unusually complete and useful for gates).
- **Data inventory (verified during NY recon):**
  - depth: `data/reference/depth_london/` (fit, 294 files, condensed MBP-10) and
    `data/reference/depth_london_2023_24/` (128 sealed days)
  - tape: `output/fp_minutes.parquet` covers the full session day incl. London hours (fit);
    holdout tape = `data/reference/cvd/footprint_holdout_*.parquet` (contiguous, 6 months)
  - bars: `data/reference/nq_1m_master.parquet` (+ `nq_1m_feb_jul2026.parquet` for 2026)
  - sealed days: `data/reference/holdout_2023_24_days.csv` — **do not fit anything to these**
- **conf_LON warning:** NY's C-check input (`pm_sofar_conf`) turned out provenance-broken in
  the old cached matrices. London's session-CVD conf (`conf_LON`) computed by
  `scripts/score_canon_span.py` is the CLEAN truncated-at-fill form — use that path, never a
  cached column, and gate any cached comparison the way §4-L3 describes.

---

## 3. The eras — same discipline as NY

- **Fit span:** 2025-06 → 2026-07. **Discover on 2025 months ONLY. Validate on 2026.**
- **Holdout:** the sealed 2023/24 days. **Run ONCE, frozen, at the very end.** No peeking, no
  iterating. If you touch it twice, it is no longer a holdout and Angus should be told.
- A check/cut/threshold survives only if it points the same way in 2025, 2026, AND holdout.

---

## 4. The procedure, step by step

Mirror the NY scripts — they are your templates; most generalize with a session parameter.
Commit after every gated step. Run heavy compute with `nohup ... &` + a watcher; it costs
zero tokens.

**L0 — census.** Template `scripts/build_l0_triggers.py`. Regenerate London triggers from
bars via the production `detect_triggers` over the London window (07:45-style pre-band not
needed; use the DST-correct window with a sensible margin). The Trigger model already carries
`cluster_members` + `level_stack` (added for NY — you get them free).
*Gate:* parity vs the cached London trigger stream on ≥3 overlap days — identity columns
(ts/tf/direction/kind/entry_ref/stop_ref) IDENTICAL. Pattern labels may differ (the old
caches predate the current classifier — known, fine).
*Bonus gate if hand data exists:* Angus's Apr-2026 catalog has live London executions
(`data/reference/live_trades_catalog.md`, Melbourne-time conversion rules in the header) —
check the census contains them, like NY's 43/45.

**L1 — fills.** Template `scripts/build_l1_fills.py`. E3 limits only, ONE walk per trigger
recording events (max_away, struct interactions, mins_to_fill); cancel policies are derived
columns, never enforced in the walk. Orders die at the London window end (ANGUS ruling:
no distance cancel — "the order lives while its session window lives").
*Gate:* engine subset-reproduction — every fill `simulate()` produces (uncapped London cfg)
must match yours on fill minute + tick-rounded price. Remember the two bugs this gate caught
for NY: the engine tick-rounds the limit at placement and evaluates from the bar AFTER the
trigger bar.

**L2 — outcomes.** Template `scripts/build_l2_outcomes.py` (`--span` ready; add a London
window config). One trigger per simulate() call (kills serialization), V8 management, rr_floor
2.0 stays in (ANGUS: baked in). Record `target_level`/`working_target` (already added).
*Gate:* lookback invariance (7d vs 30d) on days with real fills — NY's 2d attempt FAILED this
gate honestly (target menu lost far levels); expect London to need ≥7d too.

**L3 — features + trial.** Template `scripts/build_l3_features.py` (add a `london` span/depth
mapping; London depth files are `glbx-*condensed.csv` format — see `london_depth.py` for the
loader). Then the trial (`scripts/l3_check_trial.py` pattern): every old London check with its
FROZEN threshold, lift tables per era.
*Gate:* matched same-trade fills must reproduce the old `london_matrix` feature values to
1e-6 — join on (day, fill-minute, direction, ENTRY) — entry included, or multi-trigger
sibling minutes give false FAILs (burned us for half a day).
*Then:* combination probes + adversarial verification + permutation guard (run these as
sonnet agents — Angus's standing instruction: sonnet for data grinding). Expect casualties:
NY killed C, PAQ, X, LONSLOPE and demoted five others to "unproven". Whatever survives for
London, survives on evidence you can show Angus.

**L4 — policy, all post-hoc causal walks.** Template `scripts/l4_select.py` +
`scripts/raw_validated_book.py`. Deliver at **standard 1-lot first** (ANGUS: no sizing until
the validated volume is visible). Test capped vs uncapped honestly — NY's cap turned out to
cost money and buy nothing once the junk was cut, but London's flow density is different;
measure, don't assume. Aikido pass (loser-trait autopsy) only after the gates are settled,
with the permutation guard, cuts must kill predominantly losers across all three eras.

**Funded fit.** Only after Angus reviews the 1-lot book: conviction ladder ($100/$200/$300 by
tier — tiers derived from London's own data), then the **daily risk budget** (realized losses
+ in-flight risk + new risk ≤ $700 against the $800 DLL) — this is a shared account-level
budget with NY, so coordinate with the NY book's encoding; do not give London its own $700.

---

## 5. Standing Angus rulings (do not re-litigate, do re-verify where marked)

| ruling | status |
|---|---|
| rr_floor 2.0, hard, every trade | baked into engine; keep |
| no distance cancel; orders die at session-window end | ships; verify on London L1 data |
| replace-with-freshest order interaction (both directions) | spec'd; L4 arm to measure |
| news blackout (red-folder list, `src/canon/news_gate`) | NY-scoped 8:30 events — check which events touch the London window before applying |
| V8 exits (exit study: nothing mechanical beat it; capture gap belongs to future agent layer) | re-verify cheaply on London (its old book has exit stamps — good gate) |
| 1-lot before sizing; sizing tiers from observed data | process ruling; follow |
| $800 DLL → $700 daily risk budget | account-level, shared with NY |

---

## 6. Verdict format Angus expects (send after EVERY gated step)

One message per step: what ran, PASS/FAIL with the numbers, anything killed and why, what
runs next. Failures are findings — report them with the diagnosis, never bury them. End-state
deliverable mirrors NY's: uncapped + capped 1-lot tables (n, /wk, WR, meanR, months green,
maxDD, worst month) for fit AND holdout, then the funded sim.

---

## 7. The burn list — every mistake we made, so you make none of them

1. **Mixed-DST timestamps.** Trigger ts strings flip −04:00/−05:00. Always
   `pd.to_datetime(..., utc=True).tz_convert("America/New_York")`. Bit us three times.
2. **`itertuples` mangles underscore-prefixed columns.** Name it `ts_et`, not `_ts`.
3. **Engine parity details:** limit tick-rounded at placement; first evaluated bar is the one
   AFTER the trigger bar; fill needs 1 tick through; gap fills at the open.
4. **Same-minute sibling triggers** share fill minutes with different limits — any join to
   cached artifacts must include entry price or you compare different trades.
5. **Serialization**: `simulate()` holds one order at a time and silently skips triggers while
   one rests — walk candidates independently at L1/L2; re-impose capacity only in L4.
6. **Cached columns lie.** The old conf_PM matched no clean definition of itself. Recompute
   everything from raw; gate against caches only where your own tape provably matches (d15 /
   fill_delta byte-exact was our proof).
7. **Realized-loss day-halts don't bound worst-day under overlapping positions** — losses
   aren't realized when the next entries fire. Budget = realized + in-flight + new.
8. **Causality in L4:** first-N-clearing, never best-of-day; prior-trade conditioning only on
   trades whose EXIT precedes the candidate's fill (the post-loss-cooldown finding collapsed
   when tested causally — looked great leaky, died honest).
9. **Overfit guards are not optional.** Every mined cut/combination faces a permutation null
   (shuffle outcomes, re-run the search, record the max apparent lift on noise). NY's
   top-2025 combo pick failed 2026 below baseline — the discipline caught it in-house.
10. **Uncapped means concurrency.** Measure max concurrent positions and open risk before
    believing any uncapped table (NY peaks at 5–6 concurrent).
11. **Monitors:** check last-event *timestamps*, not event counts — a dead process's log looks
    "active" by line count. And user interrupts can kill in-flight background work; verify
    liveness after any interruption.
12. **Zero-trigger sanity:** compare census counts per month against the cached stream —
    NY matched to the row, exactly (that's what made everything downstream trustworthy).

---

## 8. Quick artifact map (NY, for reference and as templates)

```
scripts/build_l0_triggers.py   l0_handlog_check.py      output/l0_triggers_{span}.parquet
scripts/build_l1_fills.py                                output/l1_fills_{span}.parquet
scripts/build_l2_outcomes.py   l2_mfe_walk.py            output/l2_outcomes_{span}[_v5|_v6].parquet
scripts/build_l3_features.py   l3_check_trial.py         output/l3_features_{span}.parquet
scripts/l3_score_apply.py                                output/l3_scored_{span}.parquet
scripts/l4_select.py (+tests/test_l4_select.py)          output/aikido_{span}.parquet
scripts/raw_validated_book.py                            output/raw_validated_book_{span}.parquet
docs/… findings, config/live_thresholds.json (frozen thresholds), src/canon/features.py
(the as-of-clean builders — reuse, never reimplement)
```

Good hunting. Match the discipline and London will hold up the way NY did — and if it
doesn't, that's a real finding too, and Angus wants it straight.
