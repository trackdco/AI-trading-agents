# Phase 0 — Data validity gate (restored after container loss; findings unchanged)

**Scope:** NY pre-market 08:00–09:29 ET only. n=216, +$18,376.00, WR 40.74% [34.4, 47.4].
Buckets 08:00 n=138 / 08:30 n=47 / 09:00 n=31. London excluded; NY 09:30–10:29 (n=52) labelled control.
**Baseline:** `output/baseline_book_clean.parquet` — 404 trades, +$52,522.81, regenerated from the
committed script and reproducing to the cent. The leaky +$56,065.18 appears nowhere.

## VERDICT: the gate does NOT cleanly pass.

| Item | Status | Evidence |
|---|---|---|
| 0a order-flow source | NO DATA | 0 `.scid` files in this environment; no proxy substituted |
| 0b depth coverage | PASS | 252 days · 150 min/day · full 10-level DOM on every record |
| 0c lookahead audit | FAIL | **40 of 161** columns fail; 9 are canon check letters that move sizing |
| 0d clock / DST | PASS | 1-hour slip arithmetically excluded (strawman misbuckets 1,380/2,400 bars) |
| 0d contract | FAIL | **23 of 216** trades (10.6%) = **46.5% of pre-market P&L** on wrong-contract days |
| 0e census | BINDING | OOS halves 69/24/16 — only 08:00–08:29 can reach 30 OOS trades |

### 0c highlights
* **`W` (depth) is leaky and the finding doc says it is clean.** `condense_depth.py` keeps the LAST
  book state in the minute; measured on 3,600 snapshots over 24 days, the record stamped T matches
  the bar CLOSE of minute T (median error 0.25 pt, inside one spread; 24/24 days closer to close
  than open). Up to 59 s post-fill. `W` flips on **41.6% [35.2, 48.4]** of taken trades re-read
  from the last provably-pre-fill snapshot. Propagates D → WALLSZ → score → Q → struct → **size**.
* **`cvd_conf` is an undocumented sibling of `conf_PM`** — same still-open 08:00–09:30 window,
  equal on 98.2% of rows. The window accrues a median **67 min** after a pre-window fill.
* **Inclusive slicing** in `trade_angles.py` (`div15` 9.7% affected, `fade_last15` 7.4%) and the
  entry-tick family (`stacked_imb` **24.2%**, `delta_div` 15.9%).
* **Clean, proven exactly (0/970 mismatches):** `pm_sofar_*`, `op_sofar_*`, `d5/d15/d30(+_conf)`,
  `pathpos`, `fill_delta*`, `fill_vol_rel`; `conf_ON/LON`, `cvd_ON/LON/ASIA` close pre-08:00.
* **14 UNVERIFIABLE** (sources absent): `entry, stop, risk, tf, pattern, TRIG, trigdens_30`, and
  7 regime-vector fields. Not asserted clean.
* Positive control: a deliberately-leaky column differs on 456/970 and aborts the run if not.

### 0d highlights
* **Three sources, three roll dates**: bars roll 2 sessions early; NQ.v.0 on the volume roll;
  NY depth holds the expiring contract through expiry Friday. Series NOT back-adjusted
  (2025-09-15 same-day +237.25 pt jump vs median 7.75). Symptoms: `dep_wall_above_d` NaN 98.5%
  vs 32.4%; `gap_open_pts` median 408.75 vs 20.00 on roll days.
* P&L itself is internally consistent (entry/stop/exit from one series); the FEATURES that
  selected the trades were computed against the wrong instrument on those days.
* DST-misalignment weeks: 24/268 NY trades; every NY bucket contains aligned trades → no NY
  bucket contaminated. (London grid issues N/A to this scope.)

### 2025 tape contamination (affects values, not lookahead)
Two 2025 footprint files never price-cleaned: 126,861 rows at price <1000 (1.90%/1.47% of
volume; 2026 files: zero). `fp_minutes.vwp` off-band >25 pt on 12.69% of 2025 minutes vs 0.56%
in 2026 → `on_eff_path`, `on_extreme_age` (canon **AGE**), `pm_sofar_patheff/crosses`, `div15`
untrustworthy in 2025.

## Rulings required (restated)
1. The 40 FAIL columns — drop-don't-patch is a rulebook call (9 move sizing). **→ now H0.**
2. The 23 contract-exposed trades — `contract_clean` stratum on every headline. **→ H5 runs it.**
3. Order-flow source — does the Databento aggressor tape stand in for `.scid`?
4. Baseline — clean book is marked superseded by `baseline_book_news.parquet` (+$55,989.81/383).
