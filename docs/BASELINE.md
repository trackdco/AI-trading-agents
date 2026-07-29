# ✅ CURRENT BASELINE — 2+2 caps + CVD absorption gate + pre-market stop cap (2026-07-21)

**This is the baseline we build from now.** Angus's call. It replaces the single-cap champion
shape. For Bar: this is the "new dataset" — the CVD-absorption gate that cut 154 trades to 89
and lifted the win rate to 43%, now with the pre-market actual-stop cap that takes it to +$17,346.

## The shape

- **Per-window 2+2 caps:** pre-market (08:00–09:30) gets its own 2 trades; the golden window
  (09:40–10:15) gets its own 2. (Un-starves the golden window — it was sharing one cap before.)
- **CVD-absorption selection gate** (the shipped `filters` in `config/strategy.yaml`):
  - cut **below-value opens** (`open_vs_value == below_value`)
  - require **CVD absorption** (`cvd ≤ 0` = flow into the level; skip hollow rejections)
- **Pre-market actual-stop cap = 20pt** (Angus 21 Jul): skip a pre-market trade when the
  **real fill** would put the stop beyond 20pt ("stop too big → more likely to lose than win").
  Evaluated at fill time on the fill bar's open only — causal, no lookahead. Pre-market runs
  ~1/2.4× the post-open volatility, so wide stops there don't belong. **Golden is NOT capped** —
  its money is in the 30–40pt structural stops; the two sessions want opposite stop regimes.

## The numbers (Feb–Jul 2026)

| | trades | P&L | win | months green |
|---|---|---|---|---|
| raw 2+2 (no gate) | 154 | +$15,119 | 34% | 5/6 |
| + CVD absorption gate | 89 | +$15,381 | 43% | 5/6 |
| **+ pre-market 20pt stop cap** | **82** | **+$17,346** | **44%** | **5/6** |

**Cut 65 trades to the CVD gate, then 7 wide-stop pre-market losers to the cap — kept growing
the money, lifted win rate 34% → 43% → 44%, no green month lost, every green month stronger.**

The cap removes 7 pre-market trades (−$1,965, 29% win) whose actual stop exceeded 20pt — all
E4 displacement entries that gapped through on the fill. Verified two ways (slot consumed vs.
freed for the next setup): **identical result** — on the passed days there was no 2nd qualifying
setup, so it's moot. Control run (cap off) reproduces +$15,381 exactly.

## Reproduce / inspect

```bash
python -m scripts.window22_cvd            # canon: 2+2 + CVD gate + 20pt pre cap -> +$17,346
PRE_MAX_STOP=0 python -m scripts.window22_cvd   # cap OFF -> reproduces the +$15,381 control
python -m scripts.premarket_actualcap_run       # side-by-side: control / cap / cap+backfill
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
