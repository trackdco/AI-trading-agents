# LONDON TASK #1 — the 2R floor vs the next structural level

London, EC displacement entries, deduped `vs_first`, engine-simulated. Scored on `src/validation/prop_score.py` — the prop objective, not profit factor.

Fit span **2025-06-02 → 2026-07-15**, **264 sessions**. Friction 2.0 pt round-trip charged inside the scoreboard.

### Funnel and veto census — displacement candidates

| stage / status | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| candidates | 2,657 | 2,657 |
| · cancelled_gap_through_stop | 42 | 39 |
| · cancelled_window_end | 6 | 6 |
| · outcome | 2,139 | 1,953 |
| · vetoed_bb_vwap | 348 | 348 |
| · vetoed_rr_floor | 95 | 284 |
| · vetoed_window | 27 | 27 |
| **outcomes** | **2,139** | **1,953** |
| **deduped setups (vs_first)** | **719** | **667** |
| working != target_level (front-run, both arms) | 100% | 100% |

### Full fit span

| metric | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| N (setups) | 719 | 667 |
| trades/day | 3.20 | 2.96 |
| net pt/trade | **-3.69** | **-3.64** |
| T | -6.06 | -6.01 |
| green days | **32%** | **35%** |
| median day | -12.1 pt | -8.1 pt |
| worst rolling 10d | -368 pt | -414 pt |
| max-day share | n/a (net loss) | n/a (net loss) |
| total pts | -2,656 | -2,427 |
| target-hit (pure) | **2.9%** | **29.2%** |
| target-hit (any) | 13.2% | 42.3% |
| mean R | -0.146 | -0.146 |
| median R | -0.406 | -0.231 |
| median risk | 11.8 pt | 11.5 pt |
| RR at order · min | 2.00 | -0.00 |
| RR at order · median | **3.07** | **1.52** |
| ordered under 2R | 0.0% | 58.9% |
| value of a target hit | +21.14 pt | +2.99 pt |
| green days · all-sessions | **27%** (264 sessions) | **30%** (264 sessions) |

### Era 2025 (2025-06-02 → 2025-12-31, 150 sessions)

| metric | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| N (setups) | 453 | 414 |
| trades/day | 3.41 | 3.14 |
| net pt/trade | **-2.44** | **-1.72** |
| T | -4.05 | -2.87 |
| green days | **31%** | **37%** |
| median day | -10.8 pt | -6.4 pt |
| worst rolling 10d | -315 pt | -254 pt |
| max-day share | n/a (net loss) | n/a (net loss) |
| total pts | -1,107 | -711 |
| target-hit (pure) | **3.8%** | **30.7%** |
| target-hit (any) | 13.9% | 44.7% |
| mean R | -0.105 | -0.070 |
| median R | -0.354 | -0.138 |
| median risk | 9.5 pt | 9.2 pt |
| RR at order · min | 2.00 | -0.00 |
| RR at order · median | **3.02** | **1.57** |
| ordered under 2R | 0.0% | 57.7% |
| value of a target hit | +16.44 pt | +3.21 pt |
| green days · all-sessions | **27%** (150 sessions) | **33%** (150 sessions) |

### Era 2026 (2026-02-02 → 2026-07-15, 114 sessions)

| metric | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| N (setups) | 266 | 253 |
| trades/day | 2.89 | 2.72 |
| net pt/trade | **-5.82** | **-6.78** |
| T | -4.55 | -5.48 |
| green days | **34%** | **32%** |
| median day | -12.3 pt | -11.0 pt |
| worst rolling 10d | -368 pt | -408 pt |
| max-day share | n/a (net loss) | n/a (net loss) |
| total pts | -1,549 | -1,716 |
| target-hit (pure) | **1.5%** | **26.9%** |
| target-hit (any) | 12.0% | 38.3% |
| mean R | -0.215 | -0.269 |
| median R | -0.878 | -1.004 |
| median risk | 16.5 pt | 16.8 pt |
| RR at order · min | 2.00 | -0.00 |
| RR at order · median | **3.10** | **1.45** |
| ordered under 2R | 0.0% | 60.9% |
| value of a target hit | +41.12 pt | +2.58 pt |
| green days · all-sessions | **27%** (114 sessions) | **26%** (114 sessions) |

### Exit mix

| exit reason | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| stop | 46.7% | 45.1% |
| partial+stop | 40.1% | 12.6% |
| partial+target | 10.3% | 13.0% |
| target | 2.9% | 29.2% |

### Net points/trade by the RR the engine ORDERED

Share of book in brackets. Friction charged.

| ordered RR | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| <0.5R | — | -4.83 (22%) |
| 0.5-1R | — | -2.36 (17%) |
| 1-1.5R | — | -2.29 (11%) |
| 1.5-2R | -7.22 (1%) | -3.29 (10%) |
| 2-3R | -4.29 (47%) | -5.78 (17%) |
| >3R | -3.05 (51%) | -2.70 (23%) |

### Paired: next structural (rr0) vs 2R floor (shipped) — 626 setups in common

Of 719 (2R floor (shipped)) and 667 (next structural (rr0)). 41 setups exist only in next structural (rr0); 93 only in 2R floor (shipped).

| | value |
|---|---:|
| per-trade delta (rr0 − 2R) | **+0.23 pt** |
| paired T | **+0.84** |
| outcome identical in both arms | **66.3%** |
| rr0 better / worse | 18.2% / 15.5% |

