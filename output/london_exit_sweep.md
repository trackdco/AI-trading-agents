# LONDON EXIT LAB — target RR, break-even and runner policies

12 arms, displacement-only, deduped per arm, engine-simulated over **264 sessions**. Friction 2.0 pt charged. Control = **min 2R** (the shipped book).

> Every arm changes what happens AFTER entry, so none changes how many trades London produces. The session ceiling (~26 pt/day even if every setup behaved like the best population, against a 50 pt/day objective) is untouched by anything here. What these can fix is per-trade edge.

**Bar: net ≥ +4 pt, T ≥ 2, N ≥ 200, green ≥ 55%, positive in BOTH eras.**

### Target RR — what to aim at

| arm | N | /day | net pt | vs 2R | T | green | med day | worst10d | flat stop | 2025 net | 2026 net |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nearest | 852 | 3.23 | -3.47 | +0.20 | -6.64 | 28% | -5.3 | -472 | 45% | -2.10 | -5.71 |
| min 1R | 927 | 3.51 | -3.13 | +0.54 | -5.97 | 27% | -5.7 | -460 | 46% | -2.35 | -4.51 |
| min 1.5R | 920 | 3.48 | -3.48 | +0.19 | -6.53 | 27% | -8.3 | -446 | 47% | -2.75 | -4.75 |
| min 2R | 913 | 3.46 | -3.67 | +0.00 | -6.87 | 27% | -7.9 | -446 | 47% | -2.78 | -5.23 |
| min 2.5R | 903 | 3.42 | -3.72 | -0.05 | -6.86 | 27% | -8.3 | -434 | 47% | -2.66 | -5.55 |
| min 3R | 896 | 3.39 | -3.73 | -0.06 | -6.81 | 27% | -7.9 | -456 | 48% | -2.63 | -5.65 |

### Management — what to do on the way (all on the 2R target)

| arm | N | /day | net pt | vs 2R | T | green | med day | worst10d | flat stop | 2025 net | 2026 net |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2R + BE@1R (no partial) | 912 | 3.45 | -4.06 | -0.39 | -5.25 | 25% | -12.5 | -432 | 53% | -3.05 | -5.83 |
| 2R + partial@1R | 913 | 3.46 | -3.45 | +0.22 | -5.45 | 33% | -5.4 | -340 | 54% | -2.95 | -4.32 |
| 2R + partial@1R + BE | 913 | 3.46 | -3.42 | +0.25 | -5.42 | 34% | -4.9 | -341 | 54% | -2.96 | -4.22 |
| 2R + partial 1st + BE | 913 | 3.46 | -3.66 | +0.01 | -7.13 | 26% | -8.4 | -396 | 47% | -2.71 | -5.33 |
| 2R + runner holds | 911 | 3.45 | -3.88 | -0.21 | -6.07 | 26% | -10.1 | -427 | 47% | -3.18 | -5.09 |
| 2R + runner to EOD | 911 | 3.45 | -0.52 | +3.15 | -0.36 | 19% | -19.1 | -551 | 47% | -2.71 | +3.27 |

### Split by population

`RAN` = price never retraced to the trigger level (the population that pays); `RETRACED` = it did. An arm that only helps RETRACED is buying the wrong thing.

### Per-trade net and total by population

| arm | RAN n | RAN net | RAN total | RETRACED n | RETRACED net | RETRACED total |
|---|---|---|---|---|---|---|
| nearest | 128 | +3.62 | +464 | 724 | -4.72 | -3419 |
| min 1R | 132 | +7.37 | +973 | 795 | -4.88 | -3877 |
| min 1.5R | 129 | +6.98 | +901 | 791 | -5.19 | -4103 |
| min 2R | 129 | +7.02 | +906 | 784 | -5.43 | -4258 |
| min 2.5R | 128 | +7.27 | +930 | 775 | -5.53 | -4287 |
| min 3R | 127 | +7.62 | +968 | 769 | -5.61 | -4311 |
| 2R + BE@1R (no partial) | 129 | +12.58 | +1622 | 783 | -6.81 | -5329 |
| 2R + partial@1R | 129 | +13.80 | +1780 | 784 | -6.29 | -4931 |
| 2R + partial@1R + BE | 129 | +13.49 | +1740 | 784 | -6.20 | -4861 |
| 2R + partial 1st + BE | 129 | +5.12 | +661 | 784 | -5.11 | -4007 |
| 2R + runner holds | 128 | +11.00 | +1408 | 783 | -6.31 | -4944 |
| 2R + runner to EOD | 128 | +19.10 | +2445 | 783 | -3.73 | -2922 |

### Verdict

**No arm is net-positive in both eras.** Every one fails the burn-list bar (§8.1) before the prop bar is even reached.

Best full-span net: **`2R + runner to EOD` at -0.52 pt/trade** (-2.71 in 2025, +3.27 in 2026) — still short of the +4 bar.

