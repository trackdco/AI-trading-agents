# London holdout pre-registration

**Status: DRAFT — requires Angus sign-off before the sealed set is opened.**
Written 2026-07-30, before any holdout evidence was examined. The sealed 2023/24 days
(`data/reference/holdout_2023_24_days.csv`, 128 days) have been used ONLY to build the trigger
census and feature matrix; no outcome, check lift, or book figure has been read from them.

Purpose: fix what is being asked, and how many things, before the set is opened. Anything not
listed here is not a question the holdout answers — and adding one afterwards spends the
referendum retroactively.

---

## 1. The frozen configuration

| element | frozen value | why |
|---|---|---|
| **Arm** | `wall` = (W OR FAR) | L3 trial: only two of four checks survived, and they are one signal (r=0.834, agreeing on 94.2% of rows). Scored as one fact, not double-counted. |
| **Threshold** | score >= 1 | wall is binary |
| **Constraint level** | uncapped + $400 day stop | Grid Stage A: the level stops flipping under 14-month leave-one-out once lifetime is fixed. The earlier 4-of-14 instability was an artifact of unset lifetime. |
| **Order lifetime** | session-window-end, no distance cancel | ANGUS ruling: "the order lives while its session window lives" |
| **Risk floor** | `LON_RISK_MIN` = 9.5pt, **no ceiling** | London-native (`scorer.py:63`; 2025-London median), survived its own 24-cell floor x ceiling sweep |
| **Sizing** | flat 1 NQ lot | ANGUS: no sizing until the validated volume is visible |
| **Window** | 08:00-10:00 Europe/London, resolved per day | DST: 03:00-05:00 ET normally, 04:00-06:00 ET on ~20 fit / 21 holdout days |
| **Engine** | E3 limits, V8 management, `v8_be_at_open=False`, `rr_floor` 2.0, 7d lookback | v8_be_at_open off per ANGUS 29-Jul; 7d passed the L2 invariance gate |

**Rejected, and not to be relitigated on holdout evidence:**
- `old4` (W+FAR+ROOM+ASIA) — ROOM sits inside the permutation null in both eras (p=0.698/0.809); ASIA is significantly BACKWARDS in 2026 (lift -0.533, p=0.001).
- Risk floor 5 — better in 2025 (+0.599 vs +0.248) but worse in 2026 (+0.154 vs +0.364). Era crossing rejects it.
- 22pt distance cancel — better adjusted R in both eras but contradicts a standing ruling and lower net. A ruling, not a finding.

## 2. The exact numbers the single holdout run will report

Primary, on the frozen configuration, 128 sealed days, 1 NQ lot:

1. trades taken, trading days with a take
2. net P&L
3. win rate
4. mean R
5. maxDD (chronological equity curve)
6. months green / total
7. worst month
8. trades per week
9. W/FAR lift: mean R of `either` vs `neither`, with n on each side

Fit-span reference for comparison (NOT a target — stated so the holdout is read against a
declared prior rather than a remembered one):

| | fit |
|---|---|
| candidates (risk >= 9.5) | 884 |
| book trades | 187 on 107 days |
| net | +$22,795 |
| WR / mean R | 57% / +0.513 |
| maxDD | $1,720 (2025) / $2,550 (2026) |
| months green | 11/14 |
| W/FAR lift | +0.444 (2025) / +0.637 (2026) |

**Declared forward expectation: mean R ~ +0.48.** Selection-null calibration measured shrinkage
at the wall arm's OWN selection breadth (4 candidate checks) at **-0.014 R** — i.e. none — and
at zero breadth (rule held fixed) at -0.010 R. Exhaustive 29,161-combination search on the same
population shrinks +1.138 R, and the wall arm scores far BELOW what that search achieves
in-sample, which is why it does not read as an artifact. If the holdout comes in near +0.48,
that is the prediction met; materially below is the honest failure.

## 3. Secondary hypotheses — exactly ONE

**S1. Floor-5 / wall redundancy.** On the fit span, dropping the risk floor from 9.5 to 5 raised
net (+$28,276 on n=282 vs +$18,848 on n=155) because sub-9.5 candidates that PASS the wall check
are profitable — L2 measured sub-9.5 bleeding only on the UNSELECTED population. So the floor and
the wall check are partially redundant. **Holdout question:** on the sealed days, is the wall book
at floor 5 better or worse than at floor 9.5? Reported, not acted on.

Chosen as the only secondary because it is the **one** open question that would change the shipped
configuration. The others would not.

**Explicitly NOT asked of the holdout, and why:**
- `dep_resist>33 AND ASIA==0` (65.6%/65.5% WR, n=61) and `cvd_ASIA>737 AND dep_wall_above_sz>5`
  (65.9%/65.4%, n=67) — both failed only the pooled Wilson floor, which is a SAMPLE-SIZE
  objection. At n~61-67 a 95% lower bound of 60% needs n~150. The sealed set is 128 days and
  cannot supply it. Asking is spending the referendum on a question it cannot answer.
- Concurring-timeframes (H1) — monotone in both eras but the 3+ bucket held n=1 (2025) and n=5
  (2026). At n=1 a win rate is 0% or 100% by construction. Underpowered, not a hypothesis yet.

## 4. Multiplicity, declared before opening

**The sealed set is being asked 2 questions: 1 primary + 1 secondary.**

Šidák family-wise correction over 2 tests: per-test alpha = **0.0253**.

This is a deliberate reduction from the 5 questions that were on the table (primary + 4
secondaries). Each additional question dilutes the primary one, and the holdout opens once.

## 5. Known residuals, recorded not fixed

- **`london_matrix.py:125`** — `w.high.idxmax()` / `w.low.idxmin()` feeding `on_extreme_age`.
  DETERMINISTIC (pandas returns the first index label at the max; the index is sorted), so not a
  nondeterminism bug. But it encodes a semantic choice: on a tied extreme it measures the age of
  the EARLIEST touch, not the most recent. Measured: the session high is tied in 6 of 600 windows
  (1.0%), differing by a median of 8 minutes. Left unchanged because altering it is a
  trading-semantics decision, not an engineering one.
- **Jan 2026 is in the fit population** (629 triggers, 20 sessions). Excluded historically only as
  a trigger-cache seam artifact; bars are complete. Included because L0 does not select.
- **The 9.5 floor and the four checks were originally fitted on 2025** by the pre-rebuild canon.
  The 4-check selection null assumes they were specified independently of this data; they were
  not. The sealed set is the only evidence owing nothing to any choice made in the rebuild.
- **The fit span is 14 months (2025-06..2026-07).** All figures above are 1-lot and fit-only.

## 6. Sign-off

| | |
|---|---|
| Written by | engineering (Claude Code), 2026-07-30 |
| Requires | **Angus sign-off on §1 (frozen config), §3 (single secondary), §4 (multiplicity)** |
| Holdout may be opened | only after sign-off, once, frozen |
