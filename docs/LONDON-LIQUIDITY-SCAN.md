# London liquidity / session-pool / bias scan — Brake's three hypotheses

**Working stack (110 trades, 40 losers). FIT ONLY. User-declared mechanisms, tested once as declared. Three bars: era-bad, profit-trap (net <= 0 both eras), worst-of-6 charge. This is the last fit-side loss scan this dataset supports.**

| cell | n | WR | mean R | net | 2025 n/R/$ | 2026 n/R/$ | p(worst-of-6) | era-bad? | net<=0 both? | VERDICT |
|---|---|---|---|---|---|---|---|---|---|---|
| LQ1 wall behind within 2x stop (magnet) | 4 | 100% | +1.106 | $+1,426 | 3/+1.10/$+980 | 1/+1.13/$+446 | 0.914 | n | n | fails |
| LQ2 any wall behind (W==0) | 4 | 100% | +1.106 | $+1,426 | 3/+1.10/$+980 | 1/+1.13/$+446 | 0.914 | n | n | fails |
| SE1 stop in front of ON-extreme pool | 14 | 57% | +0.243 | $+772 | 5/+0.46/$+581 | 9/+0.12/$+191 | 0.918 | Y | n | fails |
| SE2 stop beyond the pool (control) | 1 | 0% | -1.007 | $-735 | 1/-1.01/$-735 | 0/+nan/$+0 | 0.275 | Y | Y | fails |
| DB1 counter overnight drift | 57 | 58% | +0.630 | $+7,672 | 25/+0.21/$+928 | 32/+0.96/$+6,745 | 1.000 | n | n | fails |
| DB2 htf counter_trend | 37 | 54% | +0.522 | $+5,024 | 11/+0.55/$+1,570 | 26/+0.51/$+3,454 | 0.999 | Y | n | fails |

## No survivor

None of the three mechanisms produces a cell that is bad in both eras AND removes negative money AND has n >= 10. Whatever pattern is in the losers, these three lenses either do not see it or see it only as the profit-trap shape (weak cells that still net positive). All three go to the declared-priors table for forward data as stated hypotheses with their fit numbers attached.

## Read it

- Thresholds (2.0x stop, ON midpoint, 1.0x pool) are round declared numbers, untuned — moving them after seeing this table would convert a declared test into a mined one.
- SE2 is the mechanical control: if SE1 (stop in front of the pool) is bad, SE2 (stop beyond it) should not be — a sign both are noise is both landing the same side.
- n=40 losers total: only large effects can register; absence of a verdict is absence of PROOF, not absence of the mechanism.
