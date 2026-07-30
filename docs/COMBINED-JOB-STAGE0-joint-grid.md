# Combined job — Stage 0: joint risk floor x order lifetime x cap

**Fit only. Sealed 2023/24 never loaded.**

**Grid declared upfront: 3 floors x 3 lifetimes x 3 caps = 27 cells.**

**Effective independent tests: 6** (components for 95% of variance in the cell-outcome correlation matrix; top eigenvalue 17.8 of 27). The cells are nested filters of one population, so they are near-duplicates — the nominal count badly overstates how many independent questions were asked.

| charge | nominal N=27 | effective N=6 |
|---|---|---|
| shrinkage | +0.233 R | **+0.039 R** |

Both are reported; the effective charge is the defensible one.

## The grid — per era, 1 NQ lot, adjusted at the EFFECTIVE charge

| floor | lifetime | cap | 2025 n/net/adjR | 2026 n/net/adjR | both adj>0 |
|---|---|---|---|---|---|
| 7 | 15pt | 1/session | 73/$+10,266/+0.752 | 58/$+556/+0.056 | YES |
| 7 | 15pt | 2/session | 103/$+13,039/+0.665 | 90/$+5,382/+0.198 | YES |
| 7 | 15pt | uncapped | 116/$+12,509/+0.580 | 106/$+5,480/+0.178 | YES |
| 7 | 22pt | 1/session | 79/$+10,839/+0.730 | 60/$+3,068/+0.222 | YES |
| 7 | 22pt | 2/session | 111/$+13,574/+0.660 | 97/$+8,709/+0.338 | YES |
| 7 | 22pt | uncapped | 135/$+14,594/+0.588 | 122/$+10,964/+0.329 | YES |
| 7 | window-end | 1/session | 80/$+9,844/+0.606 | 66/$+1,914/+0.137 | YES |
| 7 | window-end | 2/session | 116/$+13,274/+0.570 | 110/$+8,326/+0.280 | YES |
| 7 | window-end | uncapped | 148/$+15,836/+0.565 | 160/$+14,831/+0.357 | YES |
| 9.5 | 15pt | 1/session | 45/$+6,162/+0.551 | 43/$+2,665/+0.285 | YES |
| 9.5 | 15pt | 2/session | 58/$+6,485/+0.464 | 62/$+5,844/+0.372 | YES |
| 9.5 | 15pt | uncapped | 60/$+6,080/+0.418 | 72/$+6,408/+0.358 | YES |
| 9.5 | 22pt | 1/session | 50/$+5,500/+0.467 | 47/$+6,100/+0.556 | YES |
| 9.5 | 22pt | 2/session | 66/$+7,585/+0.478 | 71/$+10,520/+0.604 | YES |
| 9.5 | 22pt | uncapped | 71/$+6,829/+0.398 | 85/$+12,591/+0.589 | YES |
| 9.5 | window-end | 1/session | 53/$+5,821/+0.457 | 54/$+5,062/+0.409 | YES |
| 9.5 | window-end | 2/session | 71/$+7,579/+0.428 | 84/$+11,269/+0.543 | YES |
| 9.5 | window-end | uncapped | 78/$+8,178/+0.395 | 109/$+14,618/+0.531 | YES |
| 12 | 15pt | 1/session | 28/$+3,986/+0.506 | 30/$+812/+0.064 | YES |
| 12 | 15pt | 2/session | 32/$+3,391/+0.396 | 43/$+3,000/+0.221 | YES |
| 12 | 15pt | uncapped | 32/$+3,391/+0.396 | 47/$+2,570/+0.190 | YES |
| 12 | 22pt | 1/session | 29/$+3,701/+0.460 | 35/$+3,732/+0.345 | YES |
| 12 | 22pt | 2/session | 36/$+3,348/+0.341 | 49/$+5,921/+0.407 | YES |
| 12 | 22pt | uncapped | 37/$+3,142/+0.310 | 54/$+6,009/+0.383 | YES |
| 12 | window-end | 1/session | 32/$+2,910/+0.330 | 39/$+3,252/+0.261 | YES |
| 12 | window-end | 2/session | 42/$+4,578/+0.342 | 57/$+6,892/+0.399 | YES |
| 12 | window-end | uncapped | 43/$+4,372/+0.316 | 66/$+6,518/+0.329 | YES |

## Q1 — does window-end x uncapped hold at floor 9.5?

Incumbent cell: n=187, net $+22,795, adjusted R +0.395/+0.531.

Best cell at floor 9.5: lifetime `window-end` x cap `uncapped` at $+22,795.

**HOLDS** — window-end x uncapped is the best cell at the incumbent floor.

## Q2 — does the floor era-crossing persist across cap/lifetime settings?

Floor 5 was rejected on an era crossing (better 2025, worse 2026) measured against a CAPPED comparator. If the crossing appears at every cap/lifetime it is a property of the floor; if only under capping it was a comparator artifact.

| lifetime | cap | floor 7 vs 12: sign(2025 delta) | sign(2026 delta) | crossing |
|---|---|---|---|---|
| 15pt | 1/session | +1 | -1 | YES |
| 15pt | 2/session | +1 | -1 | YES |
| 15pt | uncapped | +1 | -1 | YES |
| 22pt | 1/session | +1 | -1 | YES |
| 22pt | 2/session | +1 | -1 | YES |
| 22pt | uncapped | +1 | -1 | YES |
| window-end | 1/session | +1 | -1 | YES |
| window-end | 2/session | +1 | -1 | YES |
| window-end | uncapped | +1 | +1 | no |

**Crossing present in 8 of 9 cap/lifetime settings.** It is a property of the floor, not the capped comparator — the floor-5 rejection stands on general grounds.
