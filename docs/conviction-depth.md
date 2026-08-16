# Order-book depth as a conviction count — does it separate winners from losers, and does it add anything on top of flow?

*Generated 2026-08-08 from `output/htf_ma_census/race_wide.parquet` via `scripts/conviction_lib.py`. Report-only — nothing adopted, no parquet touched, no commit.*

---

## METHOD AND COVERAGE

**The object under test.** Not "does depth feature X split the book" — that question is settled at chance level (BR-94). This asks whether **book state stacked into a count of agreeing depth signals** separates winners from losers at the entry moment, and whether adding that count on top of the flow conviction count moves anything, on the *identical* rows where both are defined.

**Timing is causal here.** `conviction_lib.py`'s header states the construction evaluates every signal — flow and depth alike — at the minute the trigger candle closes and the market order is sent. The trader's earlier system read depth at a *limit fill* timestamped inside a later bar, which is hindsight; that defect cannot arise in this construction, so depth gets a fair, apples-to-apples test here for the first time.

**Population.** 3,153 fights across 290 session-days, 3 sessions (LONDON, NY_PRE, NY_AM) × 3 mechanisms (M1, M2, M3) = 9 cells, reported separately throughout — never pooled, per instruction.

**Coverage — the caveats that shape everything below:**

- Depth signals (`s_dep_imb`, `s_sup_res`, `s_thick`, and the two wall signals) exist on **229 of 290 days** (79.0%) → **2,521 of 3,153 fights (79.96%)**. All depth-conditioned results below are restricted to this subset and say so.
- The two **wall** signals (`s_wall_sz`, `s_wall_near`) are narrower still: **1,278 of 3,153 fights (40.53%)** on 224 days. Coverage is not uniform across mechanisms either — M1 sees walls on roughly a quarter of its fights, M2/M3 on roughly half (table below). Every wall number in this report is a **sub-population** finding and is labelled as such.
- `s_thick_up` (`dep_thickness_delta_5m > 0`) agrees **0.0%** of the time across all 2,521 rows where it is defined — the column is degenerate (`dep_thickness_delta_5m` is exactly 0.0 everywhere it is populated). It is **excluded** from every depth count built here. Because it always contributes 0 when present, `cc_depth` as returned by `add_counts` is numerically identical whether or not `s_thick_up` is included (verified: 100% row match) — the exclusion is enforced by construction, not by a workaround.
- A second redundancy, found in the course of this work and not previously flagged: **`s_dep_imb` and `s_sup_res` agree with each other on 100% of depth-available rows** — they are the same signal read twice on this population (`dep_imbalance` and `support_minus_resist` are near-collinear). So "6 depth signals" is really **4 independent reads of the book**: imbalance/support-resist (one axis), thickness-vs-day, wall size, wall distance — the last two confined to the 40.5% sub-population. This matters for how much "stacking" a depth count can honestly claim to do.

**Tools used as supplied, unmodified:** `load`, `signals`, `add_counts`, `monotone_table` (dual-currency table with day-clustered bootstrap CI per level, `min_n=15`), `spearman_trend` (rank correlation of level vs metric, thin levels dropped), `permute` (outcome shuffle within session×mech, BR-97's null), `dboot_mean`. No statistics were reimplemented.

---

## 1. DEPTH-ALONE CONVICTION TABLES (per session × mech, never pooled)

`cc_depth` = count of {`s_dep_imb`, `s_sup_res`, `s_wall_sz`, `s_wall_near`, `s_thick`} agreeing with trade direction, 0–5 (`s_thick_up` excluded as above). Built only on rows where at least one depth signal is available — i.e. the depth-available subset. Win% and EV together (Law 3), day-clustered 95% CI, Spearman trend of level vs EV and vs win% (thin levels, n<15, dropped from the trend).

### LONDON M1  (n_total=617, depth-available=478, 77%, days_total=257)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 75 | 46 | 30.7% | +0.105 | [-0.364, +0.609] |  |
| 1 | 104 | 55 | 28.8% | +0.209 | [-0.299, +0.827] |  |
| 2 | 117 | 51 | 29.1% | -0.219 | [-0.462, +0.031] |  |
| 3 | 154 | 62 | 25.3% | -0.221 | [-0.486, +0.077] |  |
| 4 | 12 | 8 | 50.0% | +0.217 | — | yes |
| 5 | 16 | 10 | 37.5% | +0.026 | [-0.613, +1.133] |  |

Spearman(level, EV) = **-0.600**  ·  Spearman(level, win%) = **+0.100**

### LONDON M2  (n_total=280, depth-available=217, 78%, days_total=137)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 33 | 20 | 54.5% | +0.142 | [-0.359, +0.595] |  |
| 1 | 40 | 23 | 37.5% | -0.135 | [-0.562, +0.340] |  |
| 2 | 33 | 22 | 24.2% | -0.494 | [-0.868, -0.002] |  |
| 3 | 75 | 39 | 45.3% | -0.180 | [-0.439, +0.066] |  |
| 4 | 21 | 10 | 28.6% | -0.060 | [-0.735, +0.824] |  |
| 5 | 15 | 9 | 33.3% | -0.047 | [-0.655, +0.555] |  |

Spearman(level, EV) = **-0.029**  ·  Spearman(level, win%) = **-0.486**

### LONDON M3  (n_total=334, depth-available=272, 81%, days_total=168)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 32 | 26 | 40.6% | +0.020 | [-0.513, +0.626] |  |
| 1 | 43 | 24 | 37.2% | -0.054 | [-0.459, +0.451] |  |
| 2 | 95 | 44 | 43.2% | -0.138 | [-0.389, +0.094] |  |
| 3 | 71 | 42 | 36.6% | -0.342 | [-0.601, -0.086] |  |
| 4 | 15 | 10 | 53.3% | -0.021 | [-0.568, +0.454] |  |
| 5 | 16 | 14 | 62.5% | -0.196 | [-0.495, +0.098] |  |

Spearman(level, EV) = **-0.543**  ·  Spearman(level, win%) = **+0.600**

### NY_PRE M1  (n_total=438, depth-available=356, 81%, days_total=233)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 72 | 47 | 25.0% | -0.225 | [-0.565, +0.150] |  |
| 1 | 94 | 54 | 22.3% | -0.053 | [-0.572, +0.623] |  |
| 2 | 83 | 46 | 34.9% | +0.130 | [-0.357, +0.725] |  |
| 3 | 78 | 42 | 39.7% | +0.166 | [-0.233, +0.596] |  |
| 4 | 21 | 10 | 33.3% | -0.026 | [-0.765, +1.261] |  |
| 5 | 8 | 6 | 37.5% | +0.762 | — | yes |

Spearman(level, EV) = **+0.700**  ·  Spearman(level, win%) = **+0.600**

### NY_PRE M2  (n_total=243, depth-available=199, 82%, days_total=143)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 39 | 27 | 51.3% | +0.265 | [-0.301, +0.798] |  |
| 1 | 26 | 20 | 42.3% | -0.022 | [-0.459, +0.465] |  |
| 2 | 59 | 36 | 20.3% | -0.206 | [-0.803, +0.628] |  |
| 3 | 39 | 27 | 30.8% | -0.402 | [-0.816, +0.069] |  |
| 4 | 18 | 10 | 33.3% | +0.545 | [-0.699, +2.568] |  |
| 5 | 18 | 9 | 38.9% | -0.215 | [-0.768, +0.294] |  |

Spearman(level, EV) = **-0.314**  ·  Spearman(level, win%) = **-0.429**

### NY_PRE M3  (n_total=244, depth-available=194, 80%, days_total=137)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 23 | 17 | 34.8% | -0.333 | [-0.761, +0.185] |  |
| 1 | 28 | 16 | 35.7% | -0.049 | [-0.559, +0.588] |  |
| 2 | 57 | 33 | 40.4% | +0.198 | [-0.264, +0.709] |  |
| 3 | 50 | 36 | 34.0% | -0.327 | [-0.640, +0.039] |  |
| 4 | 22 | 12 | 45.5% | +1.209 | [-0.010, +2.139] |  |
| 5 | 14 | 9 | 35.7% | -0.258 | — | yes |

Spearman(level, EV) = **+0.700**  ·  Spearman(level, win%) = **+0.400**

### NY_AM M1  (n_total=486, depth-available=391, 80%, days_total=226)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 84 | 40 | 40.5% | +0.047 | [-0.317, +0.458] |  |
| 1 | 91 | 47 | 41.8% | +0.027 | [-0.286, +0.404] |  |
| 2 | 109 | 51 | 38.5% | +0.012 | [-0.302, +0.369] |  |
| 3 | 70 | 37 | 40.0% | -0.059 | [-0.430, +0.429] |  |
| 4 | 20 | 10 | 35.0% | -0.200 | [-0.603, +0.315] |  |
| 5 | 17 | 8 | 52.9% | -0.110 | [-0.607, +0.411] |  |

Spearman(level, EV) = **-0.943**  ·  Spearman(level, win%) = **-0.029**

### NY_AM M2  (n_total=263, depth-available=215, 82%, days_total=116)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 39 | 15 | 71.8% | +0.054 | [-0.302, +0.310] |  |
| 1 | 27 | 17 | 37.0% | -0.469 | [-0.778, -0.179] |  |
| 2 | 62 | 26 | 56.5% | -0.122 | [-0.364, +0.125] |  |
| 3 | 46 | 25 | 71.7% | +0.055 | [-0.198, +0.294] |  |
| 4 | 18 | 11 | 55.6% | +0.124 | [-0.501, +0.775] |  |
| 5 | 23 | 9 | 56.5% | -0.129 | [-0.363, +0.056] |  |

Spearman(level, EV) = **+0.200**  ·  Spearman(level, win%) = **-0.143**

### NY_AM M3  (n_total=248, depth-available=199, 80%, days_total=128)

| level | n | days | win% | EV | 95% CI | thin |
|---:|---:|---:|---:|---:|---|:---:|
| 0 | 27 | 16 | 59.3% | -0.075 | [-0.393, +0.308] |  |
| 1 | 29 | 18 | 55.2% | -0.169 | [-0.390, +0.125] |  |
| 2 | 62 | 29 | 38.7% | -0.360 | [-0.651, +0.053] |  |
| 3 | 44 | 25 | 50.0% | -0.166 | [-0.468, +0.145] |  |
| 4 | 17 | 8 | 70.6% | +0.129 | [-0.275, +0.458] |  |
| 5 | 20 | 11 | 60.0% | -0.056 | [-0.410, +0.268] |  |

Spearman(level, EV) = **+0.543**  ·  Spearman(level, win%) = **+0.429**

**Reading across the 9 cells:** the trend sign is not stable — 5 of 9 cells trend down (more depth agreement → lower EV), 4 trend up, and magnitudes swing from near 0 to ±0.94 on tables with only 5–6 usable levels. There is no session or mechanism where depth-alone conviction climbs monotonically with EV *and* the sign replicates elsewhere. Section 4 calibrates every one of these trend numbers against the permutation null — treat the numbers in this section as descriptive until you have read that section.

---

## 2. DOES DEPTH ADD TO FLOW? (like-for-like, identical rows)

The key question. Restrict to the depth-available subset per cell (same rows for both counts — the classic error this report is built to avoid is comparing `cc_flow_clean` on its full-coverage population against `cc_all_clean` on the depth-restricted one). On that identical subset, compute `cc_flow_clean` (flow only, Law-2 features dropped) and `cc_all_clean` (flow+depth, same exclusions) and compare their monotone tables directly.

### LONDON M1  (depth-available n=478, days=203)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 0–10 | +0.143 | +0.036 | -0.271 (2→8) | +0.0pp |
| flow+depth `cc_all_clean` | 0–13 | +0.117 | +0.450 | +0.079 (3→11) | +11.3pp |

### LONDON M2  (depth-available n=217, days=111)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 0–9 | +0.257 | -0.029 | +0.080 (3→8) | -6.5pp |
| flow+depth `cc_all_clean` | 2–14 | +0.000 | -0.143 | -0.356 (5→11) | -15.0pp |

### LONDON M3  (depth-available n=272, days=136)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 0–10 | -0.943 | -0.886 | -0.533 (3→8) | -26.9pp |
| flow+depth `cc_all_clean` | 2–14 | -0.714 | -0.714 | -0.804 (4→10) | -20.0pp |

### NY_PRE M1  (depth-available n=356, days=186)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 0–10 | +0.000 | +0.607 | -0.188 (3→9) | +20.5pp |
| flow+depth `cc_all_clean` | 1–14 | +0.214 | +0.679 | +0.952 (4→10) | +42.5pp |

### NY_PRE M2  (depth-available n=199, days=116)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 1–10 | -0.357 | -0.631 | -0.380 (3→9) | -18.3pp |
| flow+depth `cc_all_clean` | 2–14 | -0.607 | -0.821 | -1.036 (6→12) | -17.9pp |

### NY_PRE M3  (depth-available n=194, days=105)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 1–10 | -1.000 | -0.900 | -0.446 (4→8) | -17.2pp |
| flow+depth `cc_all_clean` | 1–13 | +0.400 | +0.400 | +0.516 (7→10) | +20.3pp |

### NY_AM M1  (depth-available n=391, days=176)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 0–10 | +0.036 | +0.500 | +0.203 (3→9) | +18.8pp |
| flow+depth `cc_all_clean` | 1–15 | +0.033 | +0.767 | +0.335 (4→12) | +35.3pp |

### NY_AM M2  (depth-available n=215, days=94)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 1–10 | +0.029 | +0.029 | -0.242 (3→8) | -15.2pp |
| flow+depth `cc_all_clean` | 1–14 | +0.321 | +0.144 | +0.154 (5→11) | +14.2pp |

### NY_AM M3  (depth-available n=199, days=100)

| construct | level range | trend(EV) | trend(win%) | bottom→top EV | bottom→top win% |
|---|---|---:|---:|---:|---:|
| flow-only `cc_flow_clean` | 1–10 | -0.500 | -0.500 | -0.366 (4→8) | -9.0pp |
| flow+depth `cc_all_clean` | 2–14 | +0.086 | +0.600 | +0.041 (6→11) | +29.2pp |

**Scorecard:** flow+depth trend beats flow-only trend in **5 of 9** cells, loses in **4 of 9**, on identical rows. No consistent direction — see Section 4 for whether even the largest of these deltas clears the permutation null (it does not, once given enough draws).

**Plain statement:** depth does not reliably widen the top-vs-bottom conviction spread beyond what flow alone already gives, on the rows where both are measurable. Where flow+depth looks better than flow-only in a given cell, a different cell shows the opposite by a similar margin — the pattern is consistent with cell-to-cell noise, not with depth adding information.

---

## 3. WALL SUB-POPULATION (40.5% coverage — labelled, not generalised)

`cc_wall` = `s_wall_sz` + `s_wall_near`, 0–2, defined only on the **1,278-fight (40.5%) wall sub-population**. Coverage is mechanism-dependent (M1 ≈ 25–32%, M2/M3 ≈ 51–54% per cell, table below) — this is not a uniform 40.5% slice, it concentrates in M2/M3.

| session | mech | wall-avail n | % of cell | days |
|---|---|---:|---:|---:|
| LONDON | M1 | 157 | 25.4% | 84 |
| LONDON | M2 | 150 | 53.6% | 79 |
| LONDON | M3 | 180 | 53.9% | 97 |
| NY_PRE | M1 | 118 | 26.9% | 71 |
| NY_PRE | M2 | 128 | 52.7% | 74 |
| NY_PRE | M3 | 125 | 51.2% | 78 |
| NY_AM | M1 | 155 | 31.9% | 72 |
| NY_AM | M2 | 139 | 52.9% | 62 |
| NY_AM | M3 | 126 | 50.8% | 70 |

### 3a. Combined wall count (`cc_wall`, 0–2), dual currency

**LONDON M1** (n=157)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 42 | 25 | 35.7% | +0.234 | [-0.319, +0.956] |
| 1 | 53 | 28 | 32.1% | -0.103 | [-0.461, +0.244] |
| 2 | 62 | 36 | 37.1% | -0.091 | [-0.438, +0.327] |

Spearman(level, EV) = **-0.500**

**LONDON M2** (n=150)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 28 | 17 | 32.1% | -0.132 | [-0.720, +0.527] |
| 1 | 67 | 38 | 32.8% | -0.379 | [-0.617, -0.127] |
| 2 | 55 | 29 | 47.3% | -0.069 | [-0.324, +0.197] |

Spearman(level, EV) = **+0.500**

**LONDON M3** (n=180)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 45 | 25 | 44.4% | -0.111 | [-0.418, +0.216] |
| 1 | 76 | 35 | 36.8% | -0.299 | [-0.543, -0.041] |
| 2 | 59 | 39 | 45.8% | -0.173 | [-0.448, +0.128] |

Spearman(level, EV) = **-0.500**

**NY_PRE M1** (n=118)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 31 | 20 | 32.3% | +0.059 | [-0.638, +0.843] |
| 1 | 43 | 25 | 27.9% | -0.157 | [-0.616, +0.422] |
| 2 | 44 | 28 | 45.5% | +0.279 | [-0.288, +0.901] |

Spearman(level, EV) = **+0.500**

**NY_PRE M2** (n=128)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 36 | 23 | 41.7% | -0.070 | [-0.508, +0.283] |
| 1 | 55 | 30 | 23.6% | -0.241 | [-0.723, +0.399] |
| 2 | 37 | 25 | 32.4% | -0.284 | [-0.763, +0.204] |

Spearman(level, EV) = **-1.000**

**NY_PRE M3** (n=125)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 25 | 17 | 40.0% | +0.190 | [-0.450, +0.833] |
| 1 | 57 | 36 | 36.8% | +0.383 | [-0.218, +1.014] |
| 2 | 43 | 29 | 32.6% | -0.283 | [-0.688, +0.154] |

Spearman(level, EV) = **-0.500**

**NY_AM M1** (n=155)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 42 | 18 | 45.2% | +0.111 | [-0.386, +0.597] |
| 1 | 64 | 32 | 40.6% | -0.120 | [-0.425, +0.234] |
| 2 | 49 | 23 | 49.0% | +0.137 | [-0.359, +0.662] |

Spearman(level, EV) = **+0.500**

**NY_AM M2** (n=139)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 43 | 18 | 55.8% | -0.112 | [-0.423, +0.138] |
| 1 | 42 | 24 | 52.4% | -0.101 | [-0.484, +0.342] |
| 2 | 54 | 24 | 53.7% | -0.246 | [-0.409, -0.101] |

Spearman(level, EV) = **-0.500**

**NY_AM M3** (n=126)

| level | n | days | win% | EV | 95% CI |
|---:|---:|---:|---:|---:|---|
| 0 | 27 | 17 | 55.6% | -0.184 | [-0.450, +0.127] |
| 1 | 63 | 32 | 54.0% | -0.096 | [-0.409, +0.338] |
| 2 | 36 | 21 | 52.8% | -0.220 | [-0.514, +0.061] |

Spearman(level, EV) = **-0.500**

With only 3 discrete levels per cell, these trends are coarse (spearman ∈ {-1, -0.5, 0, +0.5, +1}) and noisy by construction. 6 of 9 cells trend negative (more wall agreement → lower EV), the rest positive — again no stable direction. Calibration in Section 4 shows every one of these sits inside its own permutation range.

### 3b. Wall size and wall distance, individually (median split, same sub-population)

| session | mech | size: n0/win0/EV0 | n1/win1/EV1 | Δ EV | dist: n0/win0/EV0 | n1/win1/EV1 | Δ EV |
|---|---|---|---|---:|---|---|---:|
| LONDON | M1 | 80/35.0%/+0.148 | 77/35.1%/-0.170 | -0.318 | 57/33.3%/+0.041 | 100/36.0%/-0.036 | -0.078 |
| LONDON | M2 | 53/30.2%/-0.353 | 97/42.3%/-0.139 | +0.214 | 70/34.3%/-0.199 | 80/41.2%/-0.229 | -0.030 |
| LONDON | M3 | 65/43.1%/-0.160 | 115/40.9%/-0.234 | -0.074 | 101/39.6%/-0.218 | 79/44.3%/-0.195 | +0.023 |
| NY_PRE | M1 | 48/31.2%/+0.021 | 70/38.6%/+0.091 | +0.070 | 57/29.8%/-0.072 | 61/41.0%/+0.188 | +0.260 |
| NY_PRE | M2 | 51/37.3%/-0.218 | 77/27.3%/-0.199 | +0.019 | 76/31.6%/-0.084 | 52/30.8%/-0.357 | -0.273 |
| NY_PRE | M3 | 43/41.9%/+0.399 | 82/32.9%/-0.042 | -0.442 | 64/35.9%/+0.216 | 61/36.1%/+0.003 | -0.213 |
| NY_AM | M1 | 71/47.9%/+0.159 | 84/41.7%/-0.090 | -0.250 | 77/39.0%/-0.125 | 78/50.0%/+0.171 | +0.297 |
| NY_AM | M2 | 56/53.6%/-0.125 | 83/54.2%/-0.187 | -0.063 | 72/55.6%/-0.096 | 67/52.2%/-0.230 | -0.134 |
| NY_AM | M3 | 52/51.9%/-0.200 | 74/55.4%/-0.116 | +0.085 | 65/56.9%/-0.086 | 61/50.8%/-0.219 | -0.133 |

(size: 0 = below-median support-wall size, 1 = at/above median, i.e. agrees; dist: 0 = far, 1 = at/below median distance, i.e. near/agrees.) Sign flips cell to cell for both size and distance — no session or mechanism shows a consistent "bigger/closer wall → better EV" reading. This is the sub-population BR-20 already flagged as prone to a dual-currency inversion; nothing here overturns that caution.

---

## 4. PERMUTATION CALIBRATION — the centrepiece

Every headline trend above is run through `calibrate(fn, B, n_perm=10)`: `fn` reproduces the exact statistic (spearman trend, or flow-vs-flow+depth delta) on the real frame, then on 10 permutations that shuffle `out`/`win` **within each session×mech cell only**, preserving every signal, every count, and cell size exactly (`permute()` from `conviction_lib.py`). BR-97 already established this exact machinery passes ~5% of pure noise at scale — a result that sits inside its own null range here is exactly that: noise, not a finding.

### 4a. Depth-alone trend (Section 1), real vs null

| session | mech | real | null mean | null sd | null range | frac(&#124;null&#124;≥&#124;real&#124;) |
|---|---|---:|---:|---:|---|---:|
| LONDON | M1 | -0.600 | +0.010 | 0.545 | [-0.800, +0.700] | 0.50 |
| LONDON | M2 | -0.029 | -0.040 | 0.514 | [-0.543, +0.829] | 1.00 |
| LONDON | M3 | -0.543 | -0.257 | 0.439 | [-0.943, +0.486] | 0.40 |
| NY_PRE | M1 | +0.700 | +0.050 | 0.512 | [-0.700, +0.800] | 0.40 |
| NY_PRE | M2 | -0.314 | -0.023 | 0.462 | [-0.714, +0.714] | 0.50 |
| NY_PRE | M3 | +0.700 | +0.000 | 0.420 | [-0.600, +0.700] | 0.10 |
| NY_AM | M1 | -0.943 | -0.177 | 0.355 | [-0.657, +0.486] | 0.00 |
| NY_AM | M2 | +0.200 | -0.114 | 0.174 | [-0.371, +0.200] | 0.50 |
| NY_AM | M3 | +0.543 | +0.086 | 0.481 | [-0.771, +0.771] | 0.30 |

### 4b. Marginal question (Section 2): flow+depth trend alone, and flow+depth minus flow-only, on the depth-available subset

| session | mech | stat | real | null mean | null sd | null range | frac |
|---|---|---|---:|---:|---:|---|---:|
| LONDON | M1 | flow+depth trend | +0.117 | -0.030 | 0.458 | [-0.700, +0.567] | 0.80 |
| LONDON | M1 | Δ(flow+depth − flow) | -0.026 | -0.077 | 0.207 | [-0.390, +0.329] | 0.90 |
| LONDON | M2 | flow+depth trend | +0.000 | +0.139 | 0.386 | [-0.429, +0.714] | 1.00 |
| LONDON | M2 | Δ(flow+depth − flow) | -0.257 | +0.046 | 0.519 | [-0.650, +0.886] | 0.80 |
| LONDON | M3 | flow+depth trend | -0.714 | -0.093 | 0.223 | [-0.393, +0.286] | 0.00 |
| LONDON | M3 | Δ(flow+depth − flow) | +0.229 | +0.204 | 0.501 | [-0.614, +1.029] | 0.90 |
| NY_PRE | M1 | flow+depth trend | +0.214 | -0.236 | 0.208 | [-0.607, +0.179] | 0.60 |
| NY_PRE | M1 | Δ(flow+depth − flow) | +0.214 | +0.282 | 0.482 | [-0.500, +1.107] | 0.60 |
| NY_PRE | M2 | flow+depth trend | -0.607 | +0.125 | 0.283 | [-0.464, +0.464] | 0.00 |
| NY_PRE | M2 | Δ(flow+depth − flow) | -0.250 | -0.018 | 0.332 | [-0.643, +0.393] | 0.60 |
| NY_PRE | M3 | flow+depth trend | +0.400 | -0.020 | 0.477 | [-0.800, +0.600] | 0.60 |
| NY_PRE | M3 | Δ(flow+depth − flow) | +1.400 | +0.220 | 0.642 | [-1.200, +1.200] | 0.00 |
| NY_AM | M1 | flow+depth trend | +0.033 | +0.093 | 0.321 | [-0.450, +0.617] | 1.00 |
| NY_AM | M1 | Δ(flow+depth − flow) | -0.002 | +0.106 | 0.384 | [-0.750, +0.648] | 1.00 |
| NY_AM | M2 | flow+depth trend | +0.321 | +0.036 | 0.469 | [-0.571, +0.821] | 0.70 |
| NY_AM | M2 | Δ(flow+depth − flow) | +0.293 | -0.031 | 0.450 | [-0.764, +0.786] | 0.60 |
| NY_AM | M3 | flow+depth trend | +0.086 | -0.080 | 0.564 | [-0.829, +0.771] | 0.90 |
| NY_AM | M3 | Δ(flow+depth − flow) | +0.586 | +0.004 | 0.450 | [-0.629, +1.071] | 0.20 |

### 4c. Wall trend (Section 3a), real vs null

| session | mech | real | null mean | null sd | null range | frac |
|---|---|---:|---:|---:|---|---:|
| LONDON | M1 | -0.500 | -0.150 | 0.776 | [-1.000, +1.000] | 1.00 |
| LONDON | M2 | +0.500 | -0.350 | 0.808 | [-1.000, +1.000] | 1.00 |
| LONDON | M3 | -0.500 | +0.350 | 0.594 | [-1.000, +1.000] | 1.00 |
| NY_PRE | M1 | +0.500 | -0.400 | 0.735 | [-1.000, +1.000] | 1.00 |
| NY_PRE | M2 | -1.000 | +0.250 | 0.750 | [-1.000, +1.000] | 0.50 |
| NY_PRE | M3 | -0.500 | +0.350 | 0.594 | [-1.000, +1.000] | 1.00 |
| NY_AM | M1 | +0.500 | +0.000 | 0.742 | [-1.000, +1.000] | 1.00 |
| NY_AM | M2 | -0.500 | +0.000 | 0.742 | [-1.000, +1.000] | 1.00 |
| NY_AM | M3 | -0.500 | -0.050 | 0.789 | [-1.000, +1.000] | 1.00 |

### 4d. Robustness re-check at n_perm=50

`n_perm=10` has a resolution floor: "0 of 10 null draws as extreme" (`frac=0.00`) only means p < ~0.09, not p < 0.05 — the exact under-count BR-97 warned about. Every cell that hit `frac=0.00` at n_perm=10 above was re-run at n_perm=50 to see whether the read holds:

| session | mech | statistic | real | frac at n=10 | frac at n=50 |
|---|---|---|---:|---:|---:|
| NY_AM | M1 | depth-alone trend (4a) | -0.943 | 0.00 | 0.02 |
| LONDON | M3 | flow+depth trend (4b) | -0.714 | 0.00 | 0.14 |
| NY_PRE | M2 | flow+depth trend (4b) | -0.607 | 0.00 | 0.12 |
| NY_PRE | M3 | Δ(flow+depth-flow) (4b) | +1.400 | 0.00 | 0.08 |

Every `frac=0.00` at n_perm=10 rises to 0.02–0.14 at n_perm=50 — i.e. well inside a noise band once the null is actually resolved, with one partial exception (NY_AM M1 depth-alone trend, `frac=0.02` even at n=50: 0 of 50 permutations reached −0.943). That single cell is the closest thing to a real effect this report finds — and it runs **backward**: at NY_AM M1, *more* depth signals agreeing with the trade goes with *lower* EV (table in Section 1), which argues against using depth as bullish confirmation, not for it. Across the 36 calibrated headline statistics in 4a–4c (9 cells × 4 statistics: depth-alone, flow+depth-alone, delta, wall), this is the **only** one that does not comfortably fold into its own null — 1 in 36 is inside the false-positive budget BR-97 established, not evidence of a population-level effect.

---

## WHAT THE BOOK SAYS

**Depth-alone (Section 1):** no session×mech cell shows a stable, monotone win%-and-EV climb with `cc_depth`. Trend direction flips cell to cell (5 negative, 4 positive), and the one cell with the starkest reading — NY_AM M1, spearman −0.943 — survives calibration but points the *wrong way*: more depth agreement, worse expectancy. That is not a gate to build.

**Does depth add to flow (Section 2), on identical rows:** no. Flow+depth beats flow-only on trend in 5 of 9 cells and loses in 4, and the largest apparent "win" for depth (NY_PRE M3, delta +1.400 at n_perm=10) collapses to inside-noise (frac 0.08) the moment the permutation count is large enough to resolve it. Depth does not widen the top-vs-bottom conviction spread beyond what the flow count already achieves on the same rows.

**Wall sub-population (Section 3, 40.5% and mechanism-skewed toward M2/M3):** no consistent direction on the combined wall count, on wall size alone, or on wall distance alone. Every trend calibrates to inside its null.

**Calibration (Section 4), the load-bearing result:** of 36 headline statistics calibrated against BR-97's cell-preserving permutation null, 35 sit comfortably inside their own null range and 1 sits just outside it — in the direction that argues against, not for, depth as conviction. At a nominal ~5% false-positive rate across 36 tests, roughly 1–2 false positives are expected by chance alone; finding exactly one, running backward, is precisely what pure noise looks like. **This is a clean, expected null, and it is publishable as one.**

**Consistent with, and extending, BR-94:** the earlier depth feature-by-feature sweep found chance-level selection both at the trader's original (hindsight) evaluation timestamp and re-run at the causal entry timestamp — "identical clear set, cell for cell." This report asked the different, harder question — does *stacking* depth into a count help, alone or on top of flow, at the causal entry moment — and the answer is the same: no. Depth earns a fair test here for the first time (causal timing, not limit-fill hindsight) and the verdict does not change.

**Practical read:** do not add a depth-based conviction gate on top of the existing flow-based selection. The 40.5%-coverage wall signals in particular should not be promoted to a filter — any apparent win-rate effect there is exactly the shape of the BR-20 dual-currency trap (check EV before trusting a hit-rate-looking split), and none of the splits examined here clear that bar in the first place.

