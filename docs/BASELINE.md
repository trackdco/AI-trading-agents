# ✅ CURRENT BASELINE — Golden-window 2+2 caps + CVD absorption gate (2026-07-21)

**This is the baseline we build from now.** Angus's call. It replaces the single-cap champion
shape. For Bar: this is the "new dataset" — the CVD-absorption gate that cut 154 trades to 89
and lifted the win rate to 43%.

## The shape

- **Per-window 2+2 caps:** pre-market (08:00–09:30) gets its own 2 trades; the golden window
  (09:40–10:15) gets its own 2. (Un-starves the golden window — it was sharing one cap before.)
- **CVD-absorption selection gate** (the shipped `filters` in `config/strategy.yaml`):
  - cut **below-value opens** (`open_vs_value == below_value`)
  - require **CVD absorption** (`cvd ≤ 0` = flow into the level; skip hollow rejections)

## The numbers (Feb–Jul 2026)

| | trades | P&L | win | months green |
|---|---|---|---|---|
| raw 2+2 (no gate) | 154 | +$15,119 | 34% | 5/6 |
| **+ CVD absorption gate** | **89** | **+$15,381** | **43%** | **5/6** |

**Cut 65 trades, kept (grew) the money, lifted win rate 34% → 43%, no green month lost.**

## Reproduce / inspect

```bash
python -m scripts.window22_cvd     # regenerates the shape + monthly + day-of-week
```
- Trade frame: `output/window22_trades.csv` (per-trade, slice freely; `gated_kept` = passed the gate)
- Rendered dashboard: `docs/golden-window-dashboard.html` (open in a browser)
- Full analysis (day-of-week inversion, golden-window breakdown, caveats):
  `docs/FINDING-golden-window-2plus2-cvd.md`

## Notes for anyone building on this

- **2026 in-sample by design** — we trade 2026 forward, not 2023–25. OOS in prior years is
  explicitly not a veto.
- **CVD sign landmine:** the repo's `conviction()` / `load_cvd_delta()` produce the *negative*
  of the committed journal's CVD. Any fresh CVD computation must **negate** it, or `cvd ≤ 0`
  selects the hollow (losing) trades. Verified fix reproduces 89t/+$14,351-class numbers.
- **Open thread:** the golden window is the highest-quality zone per trade (54% win / $243) but
  under-traded; work in progress is a heatmap/CVD *selector* to add golden volume at quality.
