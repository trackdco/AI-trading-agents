# PREREG — LDN-PO3-01, geometry calibration + universe sensitivity

**Committed BEFORE the run. Nothing below is chosen after seeing a result.**

Date: 2026-08-05
Family: `LDN-PO3-01` (London pre-open range, break-fails-and-reverses branch)
Authorises: `scripts/london_po3_geometry.py`
Supersedes nothing. Reopens the kill recorded in `research/candidates/london-po3-ifvg.md`.

---

## 0. Why this exists (ANGUS 2026-08-05)

> *"look at all we tested to get the IB fade model shipped, look at all we did to
> get the canon shipped. if u arent testing jack shit and just sending it off, its
> obviously not gonna do well"*

The judgement is correct and the record proves it. Against the §5.11 pre-ship
checklist, this family cleared **2 of 9** items before it was killed:

| §5.11 item | LDN-PO3-01 | NYA-IVB-01 (shipped) |
|---|---|---|
| 1. loser autopsy + MFE/MAE | autopsy yes, **MFE/MAE never** | both, trial 9 |
| 2. event-universe sensitivity | **never run** | 356 → 478 (+34%), trial 10 |
| 3. stop/risk-normalisation arm class | **never run** | cap20 = best expression, rescued 2024 |
| 4. state-conditional re-tests | **never run** (pooled only) | trial 10, then refuted by permnull |
| 5. year/half-year reporting | yes | yes |
| 6. canon variable map | depth yes, in-trade flow **never** | full |
| 7. lookahead audit | yes (fills verified clean) | yes |
| 8. mechanical-baseline sign-off | n/a — never reached | yes |
| 9. deep-testing standard (9b/9c) | **never run** | tournament, PBO, PSR, MC |

Total arms tested: **LDN-PO3-01 = 2** (`F1` midpoint target, `F2` far-edge target,
both on a single stop rule). **NYA-IVB-01 = 28** across 13 trials, two vacated kills,
and a tournament.

The prior kill is therefore **VACATED** under §5.9.2 — an expectancy kill is legal
only after the complete declared search, and the geometry class was never searched.

## 0.1 Objective — corrected (ANGUS 2026-08-05)

> *"my objective is profit factor and optimisation to rinse prop firms"*

**Headline statistic = PROFIT FACTOR at strict cost (2 pt), reported per era and per
calendar year.** Reported alongside, never instead: R/trade, payoff ratio
(avg win / avg loss), win rate, and trade-sequence max drawdown in dollars at $160
fixed risk — because the funded shell's $2k EOD-trailing line is a hard constraint
and PF alone does not see it.

Win-rate-at-fixed-R is **not** the objective and is demoted to a reported column.

---

## 1. The two defects this run tests

Both were found by inspecting the ALREADY-RUN `F1`/`F2` arms in
`output/london_obk_l1.parquet` — i.e. **in-sample**. They are therefore hypotheses
requiring a null, not findings. Recorded here so the provenance cannot be
back-dated:

**D1 — the stop is uncontrolled.** Risk = distance to the sweep extreme, which
ranges p10 5.5 pts to p90 39.8 pts, a 7× spread, with no floor and no cap. Split by
risk quintile at base cost:

| risk quintile | n | median risk | WR | PF | R/trade |
|---|---:|---:|---:|---:|---:|
| q1 tightest | 77 | 5.5 | 19% | **0.52** | −0.481 |
| q2 | 69 | 9.2 | 35% | 1.30 | +0.215 |
| q3 | 72 | 14.0 | 28% | 0.83 | −0.143 |
| q4 | 69 | 21.2 | 35% | 0.72 | −0.202 |
| q5 widest | 72 | 39.8 | 51% | 1.27 | +0.033 |

**D2 — the payoff is uncontrolled.** Both declared targets are structural PRICE
LEVELS, so the R-multiple of the target is whatever the stop happens to be that day.
Measured on target exits: `F1` median 1.49R, p10 0.47R, p90 3.73R. `F2` median 4.22R,
p90 7.06R. **A fixed-R target was never tested on this branch, not once.**

---

## 2. Span, data, and what stays sealed

- Span: **2025-01-01 → 2026-07-15**, 1-minute NQ candles only. Unchanged from L1.
- **2023/24 candles: UNTOUCHED. The six sealed months: UNTOUCHED. Depth and flow:
  not used in this run at all.** This stage spends no holdout look of any kind.
- Costs 1 pt base / 2 pt strict, both always reported. $160 fixed risk sizing.
- Conservative intrabar: stop is checked before target within a bar.

## 3. Event universes (§5.11.2) — 4 arms, at the DEFAULT geometry only

Reported as sensitivity. **The universe is NOT selected from these results**; U1
remains the default universe for §4 regardless of which scores best.

- **U1 — as-is (DEFAULT).** First break of the pre-open range per side, first close
  back inside. One trade per side per day. This is the L1 universe.
- **U2 — re-entry.** Every break→fail cycle inside the trigger window, not just the
  first.
- **U3 — window widened.** Trigger window 08:00–11:00 London (from 08:00–10:00).
- **U4 — U2 + U3.**

## 4. The geometry grid — 6 stops × 7 targets = 42 arms, on U1

Every cell listed here runs. No cell is added afterwards.

**Stops** (all measured from the entry, which is unchanged: the fail-bar close):

| id | rule |
|---|---|
| `E` | beyond the sweep extreme — **DECLARED DEFAULT, as taught** |
| `E+F8` | sweep extreme, floored at 8 pts (stop pushed out if the extreme is nearer) |
| `E+F12` | sweep extreme, floored at 12 pts |
| `E~C20` | sweep extreme, capped at 20 pts (stop pulled in if the extreme is further) |
| `E+F8~C20` | floored at 8 and capped at 20 |
| `FIX15` | fixed 15 pts, ignores the extreme |

**Targets:**

| id | rule |
|---|---|
| `MID` | pre-open range midpoint — **DECLARED DEFAULT** |
| `FAR` | far edge of the pre-open range (as taught) |
| `R1` / `R1.5` / `R2` / `R3` | fixed multiples of the arm's own risk |
| `TRAIL` | no fixed target; trail the stop by the initial risk once 1R favourable |

Flat at the end of the trigger window on every arm (time exit), as in L1.

## 5. Promotion rule — DECLARED BEFORE THE RUN (§6.0.1)

**The default spec is `U1 / E / MID` (= L1's `F1`). It stands unless displaced.**

An alternative cell may displace it only if **ALL FOUR** hold:

1. **Positive PF at strict cost in BOTH eras AND in every calendar year present**
   (2025, 2026) — §5.11.5, no era-aggregate masking;
2. **Family-wise permutation null p ≤ 0.01** on the *whole 42-cell selection
   procedure*, not on the winner alone (§2.3) — declared here, run before any
   promotion claim is made;
3. **PBO < 0.5** on the arm matrix (§6.0.1);
4. **Holdout adjudication** under the single corrective iteration (§5.9.4).

**In-sample rank promotes nothing.** A cell that tops the grid and fails (2) is
reported as a failed cell, not as a result.

## 6. Kill condition — DECLARED BEFORE THE RUN

**If no cell in the 42 is PF-positive at strict cost in both eras, the expectancy
kill becomes legal** and this family dies with the geometry class finally searched.
That is a clean outcome and it is the outcome I expect to be more likely than not.

**If a cell survives §5.5(1), it is not a result yet** — it is a candidate for the
null in §5.5(2), which runs next and can kill it.

## 7. Ledger

All 46 arms (42 geometry + 4 universe) recorded to `output/trial_ledger.parquet` at
trial time, winners and losers alike, per §6.0.2. The DSR denominator takes every
one of them. This run deliberately and knowingly increases the denominator — that is
the price of the search being complete, and it is cheaper than a kill that isn't.
