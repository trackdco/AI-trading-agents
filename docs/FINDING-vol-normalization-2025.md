# FINDING: vol-normalization recovers ~$5.6k on 2025, but isn't a standalone fix (22 Jul 2026)

**Context.** With full 2025 H2 CVD + heatmap now in hand, we confirmed the 2026 order-flow
edges (CVD gate, book-support absorption) do NOT generalize to 2025 — the base setups run
~25% win in the tight/choppy regime and no selection filter rescues them. Angus's read:
this is a *favorable-regime* strategy; the fix is (1) vol-adaptive point tools and (2) a
regime stand-down gate. This finding tests part (1).

## The mechanism (already built — `year_suite.py --norm vol`)

Per-month scale factor = trailing-20d median morning-range (08:00–10:15) ÷ the Feb–Jul 2026
calibration-era median. Zero-lookahead. It scales `min_stop_points`, `t_cancel`, `front_run`,
and the `oversized_stop` threshold by that factor — so in a low-vol month the stops shrink
with the range ("a 15pt stop is a 30pt-equivalent in a tight tape"). Neutral on 2026 by
construction (factor ≈ 1.0 in the reference era) → safe to ship, only acts off-era.

## Result — champion v1.1 arm, 2025 full year

| | full year | Oct (worst) | Oct maxDD |
|---|---|---|---|
| fixed point tools | **−$14,508** | −$4,621 | $4,621 |
| vol-normalized | **−$8,916** | −$1,426 | $1,486 |

- **Recovery: +$5,592** (~38% of the loss), matching the pre-registered $4–7k/arm estimate.
- **Worst-month drawdowns roughly halve** — material for a funded-eval trailing DD.
- Nov even flips green (+$1,545).

## Verdict

Vol-normalization is a **real, zero-lookahead bleed-reducer**, not an edge. 2025 is still
−$8.9k after it — right-sizing the tools shrinks the losses but the base setups still lose in
the chop. Confirms the two-part plan: **ship vol-norm AND build the volatility stand-down
gate** (sit out the days the tape won't support a 2R move). Vol-norm closes ~38% of the gap;
the stand-down gate must close the rest.

## Reproduce

```bash
# regenerate per-day triggers (year_suite reads output/triggers_hist2326_days/)
python -c "import pandas as pd; d=pd.read_csv('output/triggers_hist2326_ob.csv'); d['day']=d.ts.str[:10]; [g.drop(columns=['day']).to_csv(f'output/triggers_hist2326_days/{k}.csv',index=False) for k,g in d.groupby('day')]"
python -m scripts.year_suite --year 2025 --norm none   # -$14,508
python -m scripts.year_suite --year 2025 --norm vol    # -$8,916
```
