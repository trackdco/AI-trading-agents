# NYA-LVL-01 — depth pass

Authorised by `docs/PREREG-level-interaction-depth.md`. Five canon checks, each ALONE at frozen canon
thresholds. **Scored on win rate at fixed R, not profit factor.** NaN stands
down.

**Depth resolved on 1,254 of 4,548 events (28%)** — the
archive covers 08:00-10:29 ET, so this is a statement about the first ninety
minutes of RTH and nothing else.

Baseline on covered events: 1.0R **59.5%** (BE 50%) / 1.5R **47.9%** (BE 40%)

| check | arm | n | WR 1.0R | lift | WR 1.5R | lift | 25 lift | 26 lift | survives |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `W` | pass | 490 | 77.8% | +18.3% | 67.8% | +19.8% | +16.4% | +21.4% | **YES** |
| `W` | fail | 764 | 47.8% | -11.7% | 35.2% | -12.7% | -9.9% | -15.0% | no |
| `D` | pass | 768 | 75.1% | +15.6% | 62.9% | +15.0% | +12.5% | +20.9% | **YES** |
| `D` | fail | 486 | 34.8% | -24.7% | 24.3% | -23.6% | -21.0% | -29.9% | no |
| `WALLSZ` | pass | 450 | 76.7% | +17.2% | 63.3% | +15.4% | +14.0% | +23.0% | **YES** |
| `WALLSZ` | fail | 804 | 49.9% | -9.6% | 39.3% | -8.6% | -10.0% | -8.3% | no |
| `IMBWITH` | pass | 576 | 59.4% | -0.1% | 47.2% | -0.7% | -0.4% | -0.1% | no |
| `IMBWITH` | fail | 678 | 59.6% | +0.1% | 48.5% | +0.6% | +0.4% | +0.1% | no |
| `THICKHI` | pass | 422 | 62.1% | +2.6% | 46.4% | -1.5% | +2.2% | -10.3% | no |
| `THICKHI` | fail | 832 | 58.2% | -1.3% | 48.7% | +0.8% | -2.1% | +1.0% | no |

**3 of 5 checks survive** (positive win-rate lift in both eras at both objectives).

Best: `W` — 1.0R **77.8%** vs base 59.5%, n=490.
