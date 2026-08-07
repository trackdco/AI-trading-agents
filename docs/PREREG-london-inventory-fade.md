# PRE-REGISTRATION — london-inventory-fade

Filed per docs/VALIDATION-PROCESS.md §1, BEFORE any census run. The git timestamp
of this commit is the declaration. Thesis: research/candidates/london-inventory-fade.md
(greenlit ANGUS 2026-08-04). Trial family: LDN-INV-01.

## Claim (falsifiable)

After a bottom-quintile prior US RTH day, NQ earns positive drift in the
European-open window (02:00–06:00 ET), concentrated in 02:00–04:00 — the market
reversing part of the prior close's loss when the first deep liquidity arrives.
The effect is ASYMMETRIC: materially weaker or absent after top-quintile days.
(Conditional leg of the documented overnight-drift mechanism; the unconditional
form is publicly dead post-2021 — research/findings/strategy-classes-evidence.md.)

## Mechanism family / inputs / session

- Family: overnight-structure (inventory). NY-canon overlap: MEDIUM.
- Inputs: `prior_rth_ret` (conditioning quantile), `inv_skew_0255`,
  `settle_prev` (distance to settlement), `on_vwap_0255`/`on_sigma_0255`
  (σ-location), position vs prior RTH range. All from
  output/london_day_features.parquet (built scripts/london_day_features.py).
- Session: london, window extended 02:00–06:00 ET for this candidate — the
  mechanism lives AT the European open, before the standard 03:00 window.
- Entry type at L0: time-window returns (no stops/targets/costs — structure
  measurement). L1+ adds execution semantics and the §2.5 cost stack (taker).

## Eras

- Discover: 2025 (calendar year). Validate: 2026-01..2026-07. **Inverse pass
  required** (§2.1): discover-2026 / validate-2025 must agree in direction.
- 2023/24 is NOT touched in any form. The holdout is the six sealed months, one
  declared look, Angus's go required (§4).

## L0 census spec (this document authorizes exactly this computation)

Per day: NQ point returns over 02:00→03:00, 03:00→04:00, 04:00→06:00,
02:00→06:00 ET (close-to-close of boundary minutes, master candle store).
Reported by prior_rth_ret quintile (era-local quintiles, descriptive; the
tradeable rule at L1 uses trailing-252-day quantiles — causal), by era.
Windows × quintiles are ONE ledgered trial family, not independent discoveries.

## Acceptance bars (defaults, §2 — Brake to review knobs)

n ≥ 30 days per era cell for direction claims; era-flip kills; family-wise
permutation p ≤ 0.01 at the L3 trial stage; DSR/PBO at grade; cost stack per
§2.5 from L1 on; effective-N per §2.2 (day-level, non-overlapping — n honest).

## Kill criteria (die if ANY)

1. No conditional window with positive bottom-quintile drift agreeing in sign
   across 2025 AND 2026.
2. Asymmetry absent: top-quintile drift statistically indistinguishable from
   bottom-quintile (then it is generic overnight drift, which is dead — not an
   inventory effect).
3. Fragility: conditional edge concentrated in ≤ 3 days (§2.5 drop-top-3).
4. Post-conditioning L1 expectancy below the §2.5 cost stack.

## Known limits

- No closing-imbalance feed: `prior_rth_ret` + `inv_skew_0255` are proxies for
  dealer inventory; a real MOC-imbalance feed is a v2 upgrade path.
- Bottom-quintile conditioning ≈ 50 days/era — direction claims only per era
  cell (§2.2); pooled for magnitude.
- The 02:00–03:00 leg sits partly before the detected European open on
  DST-mismatch days (04:00 ET open, measured); mismatch days analyzed separately.
