# FINDING: the oracle is a hindsight ceiling — the books don't generalize (20 Jul 2026)

**TL;DR:** The SD-oracle (~$70k/yr 2023-25, ~$49k 2026-6mo) is a *perfect-foresight* ceiling, not
a capturable target. The two tradeable books LOSE money out-of-sample, and every book/stand-down
predictor tested (WAR, gap_open, inventory, CVD) is either noise or a 2026 curve-fit. Chasing
"60% of oracle" as a cross-year goal is chasing a ghost. Re-target to: **profitable every month
at 1 contract** (the champion already is, in 2026) and trade it live as a 2026-regime bet with a
kill-switch.

## The decisive evidence (per-year, book P&L, 1 NQ contract, cap 2)

| year | always-E3 | always-E4 | book-selector (gap/inv, tuned 2026) | oracle+SD (foresight) |
|---|---|---|---|---|
| 2026 (IS) | +$11,786 | +$10,435 | **+$16,264 (33%)** | $49,481 |
| 2023 (OOS) | −$16,354 | +$3,770 | **−$4,973 (−7%)** | $72,535 |
| 2024 (OOS) | −$2,476 | −$6,048 | +$1,486 (2%) | $74,627 |
| 2025 (OOS) | −$23,779 | −$18,805 | **−$24,018 (−39%)** | $61,769 |

Both books lose money in 3 of 4 years. The oracle is +$60-75k every year **only because it picks
the winning book per day and skips losers with hindsight.** Remove foresight and there is no
profitable substrate OOS.

## Predictors tested for book-choice / stand-down — all fail OOS or are noise
- **WAR / imbal_share** (current heuristic): picks better book 56% of days (~coin flip);
  imbal_share shows Δ≈0.01 separation between E3-win and E4-win days. Basically useless.
- **gap_open_pts + inventory_pts**: separate the books nicely *in 2026* (Δ −19, −12) → build a
  selector → **+$16k IS 2026, then −$5k/+$1.5k/−$24k OOS.** Pure 2026 fit.
- **CVD confirmation gate**: real *win-rate* lever (33%→38-40%), 2026-only data so un-OOS-able,
  and it's a selectivity lever not a P&L multiplier (dollars stay flat). See
  `FINDING-cvd-confirm-vs-fade-signcheck.md` (+ sign verified: side A = aggressive SELL,
  `scratchpad/sign_test.py`, corr(A-B, price) = -0.66).

## What this session confirmed does NOT move the backtest (stop re-chasing)
- E-2 fix: correct but inert (0/5,432 htf relabels; `unknown` never fires at a trigger point).
- Window/cap un-starve "+$4.5k/+36%": lean-engine mirage — real engine +$1.1k, and it fails OOS.
- 9:30 re-read: lean artifact, dead.
- Book-selector (gap/inventory): 2026 curve-fit, dies OOS (this doc).

## What IS real
- **Tier-2** (cash-open sit-out 09:30-09:40 + 10pt post-open stop): clean +$1,654 / +13% on 2026,
  same-cache apples-to-apples. Pending OOS but economically sound. Shipped, defaults-on in config.
- **CVD confirmation** as a win-rate lever (accuracy, not dollars). 2026-only.

## Recommendation
1. **Re-target.** Drop "60% of hindsight oracle." Target: profitable every month at 1 contract.
2. **Trade 2026 live now** with the champion (E-2 + Tier-2), tight monitoring, kill-switch when
   monthly P&L / win-rate breaks the 2026 profile.
3. **The real open problem** is a *durable cross-year edge*. The current entry logic is
   2026-calibrated; that's a strategy-design question (Angus), not a selection-layer tuning task.
   Do not spend more compute tuning selection on 2026 — it will keep dying OOS.
