# LDN-PO3-01 / LDN-OBK-01 — mandatory loser autopsy (§3.2)

Authorised by `docs/PREREG-london-obk-L3-flow-and-autopsy.md`. Runs on the frame the raw-trigger flow pass
produced, so no feature could be added after seeing the split. Flow span
only (tape starts 2025-06-01), so **the 2025 column is H2 only**.
2023/24 untouched.

## F1

### F1 — winner vs loser on every declared feature

Medians. `gap` is winner minus loser, expressed in standard deviations of
the feature so the ten are comparable. A feature that separates outcomes
should show the SAME sign in both eras; sign flips are noise.

| feature | 2025 win | 2025 lose | 2025 gap σ | 2026 win | 2026 lose | 2026 gap σ | same sign |
|---|---:|---:|---:|---:|---:|---:|---|
| `delta_entry` | +0.00 | -2.00 | +0.05 | +15.00 | +4.00 | +0.22 | no |
| `delta_pre5` | +0.00 | -13.00 | +0.11 | -16.00 | +11.50 | -0.27 | no |
| `delta_sweep` | -11.00 | -8.00 | -0.02 | -9.00 | -14.00 | +0.03 | no |
| `absorb_extreme` | +1.95 | +1.84 | +0.06 | +1.43 | +1.54 | -0.09 | no |
| `wall_ratio_opp` | +1.67 | +1.75 | -0.14 | +2.00 | +2.00 | +0.00 | no |
| `book_imb` | +0.51 | +0.49 | +0.31 | +0.52 | +0.49 | +0.43 | **yes** |
| `width_rel` | +0.82 | +0.93 | -0.20 | +1.05 | +1.00 | +0.08 | no |
| `lon_hour` | +8.00 | +8.00 | +0.00 | +8.00 | +8.00 | +0.00 | no |
| `with_drift` | +1.00 | +1.00 | +0.00 | +1.00 | +1.00 | +0.00 | no |
| `disp_frac` | +0.08 | +0.07 | +0.17 | +0.08 | +0.08 | +0.10 | **yes** |

### F1 — half-year decomposition (§3.2 requires this, not year level)

| half | n | WR | net pts base | net pts strict | PF base | R/trade base |
|---|---:|---:|---:|---:|---:|---:|
| 2025H1 | 22 | 27% | +2 | -20 | 1.01 | -0.300 |
| 2025H2 | 130 | 32% | -405 | -535 | 0.63 | -0.281 |
| 2026H1 | 117 | 34% | +5 | -112 | 1.00 | +0.042 |
| 2026H2 | 8 | 12% | +3 | -5 | 1.02 | -0.588 |

### F1 — candidate cut-sets

Cuts are proposed from the **discover era only** (worst tercile), then tested
on every era. Per §3.2 a cut is legal ONLY if the cut cohort is bad in EVERY
era — a cut that only works where it was found is a declared negative.
De-risk (half size on the cohort instead of removing it) is tested alongside
every hard cut, because sometimes the answer is smaller, not none.

| cut | cohort bad in 2025 | in 2026 | legal | kept R base | kept R strict | de-risk R base |
|---|---|---|---|---:|---:|---:|
| cut absorb_extreme high | yes | yes | **LEGAL** | -0.132 | -0.238 | -0.125 |
| cut absorb_extreme low | yes | no | no | -0.274 | -0.360 | -0.161 |
| cut book_imb high | yes | no | no | -0.336 | -0.437 | -0.181 |
| cut book_imb low | yes | yes | **LEGAL** | -0.027 | -0.123 | -0.087 |
| cut delta_entry high | yes | no | no | -0.289 | -0.384 | -0.168 |
| cut delta_entry low | yes | yes | **LEGAL** | -0.133 | -0.240 | -0.120 |
| cut delta_pre5 high | yes | yes | **LEGAL** | -0.101 | -0.202 | -0.110 |
| cut delta_pre5 low | yes | yes | **LEGAL** | -0.135 | -0.232 | -0.126 |
| cut delta_sweep high | yes | no | no | -0.178 | -0.284 | -0.135 |
| cut delta_sweep low | yes | yes | **LEGAL** | -0.138 | -0.240 | -0.124 |
| cut disp_frac high | yes | yes | **LEGAL** | -0.087 | -0.193 | -0.107 |
| cut disp_frac low | yes | no | no | -0.190 | -0.278 | -0.144 |
| cut wall_ratio_opp high | yes | no | no | -0.202 | -0.312 | -0.129 |
| cut wall_ratio_opp low | yes | yes | **LEGAL** | -0.129 | -0.220 | -0.121 |
| cut width_rel high | yes | no | no | -0.214 | -0.321 | -0.144 |
| cut width_rel low | yes | yes | **LEGAL** | -0.092 | -0.178 | -0.111 |

**Unconditioned baseline for reference: R base -0.155, strict -0.250 (n=277).** A cut only matters if `kept` clears the baseline AND is legal.

**9 of 16 cuts are legal** (cohort bad in every era). **0 of them leave the arm positive at strict cost.**

Every legal cut still leaves a losing arm. Removing the worst cohorts
raises the number without crossing zero, and half-sizing them does the
same thing more slowly — which is what it looks like when the losses are
spread through the sample rather than concentrated in a removable
subset. There is no cut here, and there is no de-risk here.

## A/S1

### A/S1 — winner vs loser on every declared feature

Medians. `gap` is winner minus loser, expressed in standard deviations of
the feature so the ten are comparable. A feature that separates outcomes
should show the SAME sign in both eras; sign flips are noise.

| feature | 2025 win | 2025 lose | 2025 gap σ | 2026 win | 2026 lose | 2026 gap σ | same sign |
|---|---:|---:|---:|---:|---:|---:|---|
| `delta_entry` | +3.00 | -4.50 | +0.10 | -14.00 | +5.50 | -0.19 | no |
| `delta_pre5` | +14.00 | -18.00 | +0.17 | -56.00 | -14.00 | -0.25 | no |
| `delta_sweep` | +12.50 | -34.00 | +0.26 | -58.00 | -19.00 | -0.27 | no |
| `absorb_extreme` | +1.67 | +1.97 | -0.12 | +1.81 | +1.71 | +0.11 | no |
| `wall_ratio_opp` | +2.00 | +2.00 | +0.00 | +2.00 | +2.00 | +0.00 | no |
| `book_imb` | +0.49 | +0.48 | +0.21 | +0.53 | +0.49 | +0.45 | **yes** |
| `width_rel` | +0.95 | +0.86 | +0.16 | +1.07 | +1.00 | +0.11 | **yes** |
| `lon_hour` | +8.00 | +8.00 | +0.00 | +8.00 | +8.00 | +0.00 | no |
| `with_drift` | +0.00 | +1.00 | -2.00 | +1.00 | +1.00 | +0.00 | no |
| `disp_frac` | +0.08 | +0.08 | +0.05 | +0.08 | +0.08 | -0.11 | no |

### A/S1 — half-year decomposition (§3.2 requires this, not year level)

| half | n | WR | net pts base | net pts strict | PF base | R/trade base |
|---|---:|---:|---:|---:|---:|---:|
| 2025H1 | 24 | 33% | -107 | -131 | 0.54 | -0.210 |
| 2025H2 | 138 | 30% | -332 | -470 | 0.69 | -0.265 |
| 2026H1 | 129 | 38% | +26 | -103 | 1.02 | +0.019 |
| 2026H2 | 9 | 33% | +62 | +54 | 1.62 | -0.067 |

### A/S1 — candidate cut-sets

Cuts are proposed from the **discover era only** (worst tercile), then tested
on every era. Per §3.2 a cut is legal ONLY if the cut cohort is bad in EVERY
era — a cut that only works where it was found is a declared negative.
De-risk (half size on the cohort instead of removing it) is tested alongside
every hard cut, because sometimes the answer is smaller, not none.

| cut | cohort bad in 2025 | in 2026 | legal | kept R base | kept R strict | de-risk R base |
|---|---|---|---|---:|---:|---:|
| cut absorb_extreme high | yes | no | no | -0.116 | -0.227 | -0.106 |
| cut absorb_extreme low | yes | yes | **LEGAL** | -0.172 | -0.264 | -0.120 |
| cut book_imb high | yes | no | no | -0.300 | -0.402 | -0.162 |
| cut book_imb low | yes | yes | **LEGAL** | -0.010 | -0.109 | -0.070 |
| cut delta_entry high | yes | yes | **LEGAL** | -0.128 | -0.232 | -0.108 |
| cut delta_entry low | yes | no | no | -0.155 | -0.255 | -0.118 |
| cut delta_pre5 high | yes | no | no | -0.192 | -0.297 | -0.133 |
| cut delta_pre5 low | yes | no | no | -0.209 | -0.310 | -0.136 |
| cut delta_sweep high | yes | no | no | -0.201 | -0.307 | -0.134 |
| cut delta_sweep low | yes | no | no | -0.178 | -0.281 | -0.125 |
| cut disp_frac high | yes | yes | **LEGAL** | -0.108 | -0.217 | -0.103 |
| cut disp_frac low | yes | no | no | -0.112 | -0.205 | -0.106 |
| cut wall_ratio_opp high | yes | no | no | -0.172 | -0.275 | -0.125 |
| cut wall_ratio_opp low | yes | yes | **LEGAL** | -0.143 | -0.244 | -0.111 |
| cut width_rel high | yes | no | no | -0.216 | -0.329 | -0.133 |
| cut width_rel low | yes | no | no | -0.088 | -0.182 | -0.098 |

**Unconditioned baseline for reference: R base -0.133, strict -0.233 (n=300).** A cut only matters if `kept` clears the baseline AND is legal.

**5 of 16 cuts are legal** (cohort bad in every era). **0 of them leave the arm positive at strict cost.**

Every legal cut still leaves a losing arm. Removing the worst cohorts
raises the number without crossing zero, and half-sizing them does the
same thing more slowly — which is what it looks like when the losses are
spread through the sample rather than concentrated in a removable
subset. There is no cut here, and there is no de-risk here.
