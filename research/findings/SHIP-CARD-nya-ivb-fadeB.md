---
date: 2026-08-05
kind: pre-ship statistical breakdown (Angus's request)
status: SHIP DECISION PENDING — 2024 warning label attached; §3.2 autopsy COMPLETE (no spec change)
tags: [ny-am, ivb-fade, ship-card]
---

# SHIP CARD — IB range fade (NYA-IVB-01 branch B, default spec)

Spec (frozen): first 30 min of NY cash = the range. In 10:00-10:30, if price
touches either extreme while the range is intact, fade toward the range
midpoint. Stop 0.25x range beyond the extreme. No break-even, no partials.
One trade per day maximum. ~2 trades/week.

## Core economics (356 trades, 3.5 years, $160 fixed risk per trade)

| metric | base costs (1pt) | strict costs (2pt) |
|---|---|---|
| trades | 356 | 356 |
| win rate | 41.3% | 41.3% |
| net points | +2,539 | +2,183 |
| dollars | +$10,865 | +$8,296 |
| profit factor | 1.41 | 1.34 |
| expectancy/trade | +7.1 pts / +$30.5 | +6.1 pts / +$23.3 |
| avg R per trade | +0.19 | +0.15 |

- Payoff shape: avg win +59.8 pts ($+312) vs avg loss −29.9 pts ($−167) —
  2.0:1 payoff at 41% WR.
- Exits: 58% stops, 41% targets, <1% time. Median hold 10 MINUTES (p90 48)
  — this is a scalp. Touches cluster 10:00-10:02.
- Sides symmetric: long 41% WR (162), short 41% WR (194).
- Median IB 102 pts → median risk 25.6 pts.

## Yearly breakdown — READ THIS ROW FIRST

| year | trades | dollars | WR |
|---|---|---|---|
| 2023 | 98 | +$7,445 | 51% |
| **2024** | **100** | **−$1,538** | **32%** |
| 2025 | 101 | +$2,455 | 40% |
| 2026 | 57 | +$2,503 | 44% |

**WARNING LABEL: 2024 was a losing year.** The era rung passed on the
23-24 AGGREGATE (+$5,907) — the same calendar-masking failure mode the
pre-market program's H2-2025 hole taught us. 2023's monster year hid a
32%-WR 2024. The declared eras (2025, 2026, 23-24 pooled) all passed as
declared, so no rule was broken — but the year-level truth belongs on the
ship decision. Flow data does not exist for 2024, so the flow-conditioning
rescue path is unavailable for that year; the honest read is one losing
year in four, depth unknown.

## Risk profile

- Max losing streak: 15 trades (≈ 7 weeks at cadence; −$2,500ish at fixed
  $160 risk).
- Trade-sequence max drawdown: $3,370 — EXCEEDS a $2k trailing line
  standalone; standalone funded MC busts 20% of years. AS A BOOK COMPONENT
  (beside the canon): book P(bust) 0.5%, book maxDD median $1,460.
- Months: 43 total, 65% positive, best +$1,832, worst −$1,178.

## Validation record

- Tournament: 6 arms, all positive every era, PBO 0.10 (cleanest in
  program); default stands; 15-min-IB challenger (PF 1.64, $+21,313)
  banked for holdout adjudication.
- Sleeve grading: PSR(0) 0.994 vs 0.75 floor — PASS. Min certifying track
  390 days vs 911 held.
- Canon correlation: +0.02 union / +0.17 both-active (88 days) — clean.
- Book grading: passed (P(bust) 0.5%, corr matrix max 0.084).
- Ledger-DSR: 0.000 under the known-inflated denominator (Brake fix
  pending) — recorded, not decision-driving per §5.9.5.

## §3.2 loser autopsy + MFE/MAE (complete, run 2026-08-05 after Angus flagged)

- Winners' median adverse excursion 0.18R (they barely breathe); losers get
  0.84R favorable before dying (76% see >=0.5R). BE@0.5R and partial@0.75R
  declared as future arms for holdout adjudication — NOT applied (BE-family
  arms have twice failed adjudication in mean-reversion trades here).
- Winners and losers indistinguishable on IB size and side; flow-at-entry
  does NOT discriminate (both cohorts PF 1.6+) — the edge is structural; no
  flow gate supported, none added.
- 2024 autopsy: compressed-IB hypothesis FALSE (2024's small-IB trades were
  profitable); no declared feature explains the year. Verdict: environmental
  hole, PRICED not cut — same class as the inventory fade's H2-2025.

## Remaining before live (the ladder)

1. ANGUS DECISION on the 2024 warning label: ship as-is at book weight /
   hold for the banked 15-min-IB holdout adjudication (its 23-24 was
   +$1,480 but its 2024 split is UNKNOWN and checking it burns holdout
   information) / hold for more evidence.
2. Chained-agents-vs-mechanical rung (replay harness adapted from
   scripts/capture_desk_run.py; playbook = trial-11 signatures; agent must
   beat the mechanical book on the declared funded statistic).
3. Shadow period; two-party arming; §6 human sign-off.
