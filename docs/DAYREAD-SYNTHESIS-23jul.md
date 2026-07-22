# Day-read synthesis: window-split rulebook + verified stand-down (23 Jul 2026)

Ultracode fan-out: 65 day features + 10 trade angles + window-split labels, screened OOF,
then **every survivor adversarially re-verified** (independent recompute + 3-of-4 half-period
stress). 26 findings confirmed. Scripts: `dayflow_v2.py`, `dayflow_screen.py`,
`trade_angles.py`, `standdown_eval.py`. Verdicts in scratchpad `verdicts_shard*.json`.

## The one structural truth: pre-market and golden are different animals

Pre-red and gold-red agree only **14% of days** — a red pre-market says almost nothing about
the golden window. They must be read, gated, and traded separately. This is the spine of
everything below.

## Verified TRADE rules (window-split) — these are the money

Each holds both years, 3-4/4 half-periods, on the 970-trade both-books universe.

**Pre-market window (fills before 09:30):**
- B (continuation): needs `conf_PM` (+$69/+$342 on-off) AND `conf_last15`; `div15` is a veto.
  Counter-intuitive but verified: overnight/London confirmation *hurts* early B fills.
- B2 (fade): `path_lo` (session CVD at day lows) is a veto (-$91/-$104).
- **B2 structurally lives here** — B2 pre −$34/+$20 vs gold −$94/−$63 per trade, both years.

**Golden window (fills 09:30-10:15):**
- B: `conf_last30` and `conf_LON` help (+$240/+$304); `conf_PM` and `div15` are vetoes.
  Session confirmation *helps* late fills — the exact inverse of the pre window.
- B2: `conf_last15`/`conf_last30` help strongly (+$186/+$249, off-trades bleed −$150 to −$200).

The headline: **the same signal flips sign across windows.** `conf_PM` is a keep for B in the
pre window and a veto for B in the golden window. `conf_LON` hurts pre-B, helps gold-B. You
cannot run one ruleset all morning — which is exactly how you described your own trading.

## Verified STAND-DOWN predictors (real, but weak in dollars)

**Pre-market red** is predictable from pre-08:00 flow (all verified 3-4/4):
- `abs_cvd_ASIA`, `absz_cvd_ON`, composite `comp_onflow_mag` → AUC ~0.58-0.61. Big one-sided
  overnight/Asia flow magnitude → pre-market chops out. Low overnight inventory also → pre-red.

**Golden red** is predictable from 09:40-known info (verified 4/4, the strongest cells):
- `pre_traded` (books already fired in the pre window) → P(gold red) 0.60→0.68 vs 0.36→0.52.
- Choppy pre-market / opening path (`pm_eff_path`, `op_eff_path` low; `pm_crosses` high) and
  **stalling CVD acceleration** (`abs_cvd_accel_PM` low) → gold red. AUC 0.59-0.67.

**Whole-day red**: `absz_cvd_ON`, `rel_range` above median (3/4); `yday_red` (2026-only).

### The honest dollar result

These predictors are statistically real but **do not convert to clean dollars as a hard gate**
on top of the already-filtered portfolio:

| | no-forecast portfolio | + full gates | + gold-gate only (≥3 flags) |
|---|---|---|---|
| 2025 | +$9,871 | +$6,221 (**worse**) | +$10,728 (+$858) |
| 2026 | +$15,684 | +$18,073 | +$15,684 (+$0) |

A perfect (oracle) window stand-down would add $17k/$19k — but AUC-0.6 predictors capture
almost none of it, because both-red days aren't cleanly separable. Hard-gating cuts winners
about as often as losers. **Verdict: these belong as conviction/sizing inputs (shade size down
when the chop/stall flags stack), NOT as binary skip rules.** The lone exception that helps both
years is the golden chop gate at a *strict* threshold (skip gold only when ≥3 of 4 flags fire) —
and even that is +$858/+$0.

## What to push

1. **Window-split trade rules** — verified, robust, the real edge. Pre and golden get their own
   CVD rulesets (opposite signs on conf_PM/conf_LON). This is new and directly actionable.
2. **B2 requires CVD** — already agreed; confirmed again per-window.
3. **Stand-down as soft conviction**, not a gate: stack the 4 golden chop/stall flags into a
   size multiplier; skip gold only at the strict ≥3 corner.
4. **Do NOT** hard-gate days on the overnight-flow composite — it cuts 2025 winners.

## Honest caveats
- Selected for 2-year consistency; next quarter is the true holdout.
- Chop features (`pm_eff_path`, `pm_crosses`) are non-stationary in level across years — use as
  within-day ranks, not fixed thresholds.
- Portfolio runs both books concurrently (~2x capital).

## ROUND 3 (24 Jul): the angles I had skipped — multivariate model + depth + sizing

Angus called out that single-feature screens ≠ every angle. Correct. Three things I had not done:

**1. Multivariate model.** HistGradientBoosting over all 60 flow features, walk-forward
(TimeSeriesSplit, threshold/size decided on train only), target = sign of the portfolio's
realized P&L per (day, window). The nonlinear combination beats every single feature:
pre-window OOF-AUC **0.618** vs best single feature ~0.61 — and it climbs further with depth.

**2. Order-book depth (the modality I ignored).** Extracted L2 book-imbalance / thickness /
replenishment / thin-fraction per window from 174 days of 1-min snapshots
(`scripts/depth_daywin.py`). Adding depth to the pre-window model lifts OOF-AUC **0.618 → 0.660**
on the identical 106 days. Depth carries real, independent day-read signal — resting liquidity
matters, exactly as expected.

**3. The right eval (sizing, not a gate).** A binary skip@P≥0.5 still loses (overfits, too
aggressive) — consistent with round 2. But using the model's probability as a **size multiplier**
(full/0.6/0.25 by P(loss) tier, renormalized to avg 1 contract) beats ungated out-of-sample:

| pre-window model | OOF-AUC | ungated | hard-skip | **sized** |
|---|---|---|---|---|
| flow-only, all days (n=148) | 0.580 | +$24,308 | +$11,985 | **+$27,802** |
| flow-only, depth days (n=106) | 0.618 | +$10,426 | +$5,396 | +$15,908 |
| **flow + depth, depth days (n=106)** | **0.660** | +$10,426 | +$5,836 | **+$18,578** |

Depth-augmented sizing nearly **doubles** the pre-window P&L on its coverage (+$10.4k → +$18.6k),
walk-forward. The correct use of the day-read is confirmed: **conviction sizing, not a skip
switch** — and the richer the features (multivariate + depth), the more it pays.

### Still open / honest limits
- GOLD window is underpowered to model (only ~33-61 window-obs; the portfolio's B2 volume lives
  in the pre window). Needs per-trade modeling or more data.
- Depth covers 2025-H2 + Apr-2026 only; the 2026 depth folder for the rest of the year would let
  this run full-span.
- Small n (106-148 window-obs), walk-forward but not yet a true forward quarter.

## ROUND 4 (24 Jul): FULL 2026 depth + STRICT cross-year test — the round-3 gains were leakage

Angus pointed out the full 2026 depth was already on disk (`data/reference/depth_2026`,
Feb-Jul, 08:00-10:30). Rebuilt depth features on all **256 days** (152/104 per year) and ran the
decisive test I owed: **train one year, test the other** (not walk-forward, which mixes years).

Predicting the portfolio's window-level P&L sign — the decision-relevant stand-down target —
does **NOT generalize across years**:

| pre-window model | train2025→test2026 AUC | train2026→test2025 AUC | sized $ vs ungated |
|---|---|---|---|
| GBM flow-only | 0.576 | 0.476 | −$2,424 / +$2,253 |
| GBM flow+depth | 0.452 | 0.367 | −$3,391 / −$1,671 |
| logistic, 5 verified feats | 0.407 | 0.395 | −$3,052 / −$2,238 |
| logistic verified+depth | 0.362 | 0.379 | −$440 / −$2,636 |

Almost every cross-year AUC is **below 0.50** — the relationship *reverses* between years. Depth
makes it worse, not better. The round-3 "0.618 → 0.660 with depth" was **walk-forward optimism**:
TimeSeriesSplit's early folds test 2025-on-2025 (within-year), inflating the aggregate. Under a
clean year split it collapses. Sizing on these predictions loses money out-of-fit.

### Why (and what it means)
The verified single features (`abs_cvd_ASIA` etc.) predict **raw-book red** ~0.58 — but the
portfolio has *already* filtered trades with the CVD rules, and the residual "will the filtered
trades lose this window" is not predictable cross-year. The easy signal was captured by the
trade rules; what's left is noise-level.

**The honest conclusion:** the edge lives in the ENTRY rules (window-split CVD), which DO
generalize (verified 3-4/4 half-periods, portfolio +$9.9k/+$15.7k out-of-fit). The DAY-READ /
stand-down layer does **not** generalize as a predictive model on the filtered portfolio. The
oracle+stand-down ceiling is real but its gap is mostly **hindsight that can't be predicted
pre-decision** — not a model we haven't built yet. The golden window remains unmodelable
(only 61 portfolio window-obs).

This is a negative result, stated plainly rather than dressed up. The productive levers that
remain are: (1) the verified window-split entry rulebook, (2) modest conviction sizing from the
handful of features that survive within-year, held loosely, (3) a true forward quarter as the
real test — not more feature mining on these two years.
