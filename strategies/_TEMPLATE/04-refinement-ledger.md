# <Strategy Name> — Refinement Ledger

**Stages 4–7. Append-only. Nothing is ever deleted from this file.**

This is the honesty mechanism of the whole pipeline. The number of things we
tried determines how impressed we're allowed to be by the thing that worked —
so failed experiments are not clutter, they are the denominator.

---

## Plain English

_What did we change, and did cutting the losers cost us the winners?_

---

## Baseline — the raw substrate (Stage 4)

Window: **2025-07-01 → 2026-06-30**. No filters. Every trigger taken.

| Metric | Value |
|---|---|
| Triggers | |
| Trading days with ≥1 trigger | |
| Win rate | |
| Expectancy (R) | |
| Profit factor | |
| Max drawdown (R) | |
| Gross win (R) / Gross loss (R) | |

> Sanity check: a raw, unfiltered trigger set that is *already* highly
> profitable usually means a lookahead bug. Verify before celebrating.

Gate A1 (≥60 triggers): **PASS / FAIL**

---

## Filter experiments (Stage 5)

**Every filter tested goes here, adopted or not.** One axis at a time; no grid
searches.

> **Filter efficiency** = (share of gross loss removed) ÷ (share of gross win removed).
> **Adopt only if efficiency ≥ 2.0 and ≥ 40 trades remain.**

| # | Filter tested | Trades left | Loss removed | Win removed | Efficiency | Expectancy | Adopted? | Note |
|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |

**Filters tested: _N_** → B1 expectancy threshold is **_____R**
(≤5 → 0.15R · 6–15 → 0.20R · 16–40 → 0.30R · >40 → automatic fail)

### Adopted stack

Maximum 3. More than that is three conditions of curve-fitting stacked up.

1. 
2. 
3. 

---

## Plateau check (Gate E1)

For each tuned parameter, expectancy one step either side of the chosen value.
We want a hill, not a needle.

| Parameter | −1 step | chosen | +1 step | Plateau? |
|---|---:|---:|---:|---|
| | | | | |

---

## Split-half check (Gate B5)

Cheap, and it catches regime artifacts before the OOS gets spent.

| Half | Trades | Expectancy | PF |
|---|---:|---:|---:|
| 2025-H2 | | | |
| 2026-H1 | | | |

Both positive? **YES / NO**

---

## Freeze (Stage 6)

- Spec version frozen at: **v____**
- Commit: `________`
- Date: ______
- Signed off by Angus: ______

**Nothing below this line may cause an edit above it.** A change after the
freeze means the OOS restarts on a different, unused window.

---

## Out-of-sample attempts (Stage 7)

Maximum 3. Each must use a different, previously untouched window. Every attempt
is recorded here whether or not we liked the answer.

| # | Window | Chosen how | Trades | Expectancy | PF | Degradation ratio | Result |
|---|---|---|---:|---:|---:|---:|---|
| 1 | | pre-registered per gate §D | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

**Attempts used: _N_ of 3.**

---

## Cost sensitivity (Gate C1)

| Scenario | Expectancy | PF | Passes? |
|---|---:|---:|---|
| Assumed costs | | | |
| **2× slippage** | | | |

---

## Regime slices (Gates E2–E4)

| Slice | Trades | Expectancy | Note |
|---|---:|---:|---|
| ATR low tercile | | | |
| ATR mid tercile | | | |
| ATR high tercile | | | |
| Best month's share of total R | | | ≤40% required |
| Best trade's share of total R | | | ≤15% required |
