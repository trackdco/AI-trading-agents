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
