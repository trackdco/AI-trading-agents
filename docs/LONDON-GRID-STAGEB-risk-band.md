# London grid audit — Stage B: the risk band

**Fit only. Sealed 2023/24 never loaded.**

**Grid declared upfront: 6 floors x 4 ceilings = 24 cells.** Shrinkage charged at this breadth: **+0.218 R**.

## Was 9.5 measured on London or inherited from NY?

**Measured on London, and it is not NY's number.** NY's Layer 0 is a 7-60pt BAND (`docs/` and the NY substrate carry both a floor and a ceiling). London's is `LON_RISK_MIN = 9.5` with **no upper cap**, and `src/canon/scorer.py:63` labels it "London Layer 0 ... London-native"; `scripts/london_canon.py` sources it as the "2025-London median". So the floor is London-derived — but it was fitted on 2025 only and never trialed against an honest population until this rebuild.

## By risk decile, both eras separately, 1 NQ lot

| decile | pts range | 2025 n/WR/R | 2026 n/WR/R | total $ |
|---|---|---|---|---|
| 1 | 0.2-0.8 | 506/4%/-1.11 | 183/1%/-1.17 | $-9,969 |
| 2 | 1.0-1.2 | 327/10%/-0.22 | 108/6%/-0.65 | $-5,288 |
| 3 | 1.5-2.0 | 400/16%/-0.23 | 157/8%/-0.53 | $-8,881 |
| 4 | 2.2-3.0 | 514/18%/-0.11 | 176/10%/+0.08 | $-5,238 |
| 5 | 3.2-4.0 | 421/26%/-0.04 | 152/11%/-0.45 | $-9,086 |
| 6 | 4.2-5.0 | 337/27%/-0.05 | 165/29%/+0.29 | $-128 |
| 7 | 5.2-6.2 | 303/29%/+0.02 | 185/24%/-0.08 | $-3,384 |
| 8 | 6.5-8.2 | 333/33%/-0.09 | 231/21%/-0.25 | $-15,702 |
| 9 | 8.5-11.5 | 288/41%/+0.04 | 260/36%/+0.08 | $+5,616 |
| 10 | 11.8-47.2 | 218/44%/-0.02 | 324/38%/+0.01 | $-5,171 |

## Floor x ceiling sweep — era-consistency bar: BOTH eras positive on adjusted R

| floor | ceiling | 2025 adj R | 2026 adj R | n | net | consistent |
|---|---|---|---|---|---|---|
| 0 | none | +0.406 | +0.009 | 391 | $+24,405 | YES |
| 0 | 60 | +0.406 | +0.009 | 391 | $+24,405 | YES |
| 0 | 40 | +0.406 | +0.009 | 391 | $+24,405 | YES |
| 0 | 25 | +0.404 | -0.003 | 392 | $+22,862 | no |
| 5 | none | +0.599 | +0.154 | 282 | $+28,276 | YES |
| 5 | 60 | +0.599 | +0.154 | 282 | $+28,276 | YES |
| 5 | 40 | +0.599 | +0.154 | 282 | $+28,276 | YES |
| 5 | 25 | +0.596 | +0.153 | 283 | $+27,054 | YES |
| 7 | none | +0.390 | +0.101 | 226 | $+21,600 | YES |
| 7 | 60 | +0.390 | +0.101 | 226 | $+21,600 | YES |
| 7 | 40 | +0.390 | +0.101 | 226 | $+21,600 | YES |
| 7 | 25 | +0.403 | +0.064 | 226 | $+20,646 | YES |
| 9.5 | none | +0.248 | +0.364 | 155 | $+18,848 | YES |
| 9.5 | 60 | +0.248 | +0.364 | 155 | $+18,848 | YES |
| 9.5 | 40 | +0.248 | +0.364 | 155 | $+18,848 | YES |
| 9.5 | 25 | +0.295 | +0.279 | 155 | $+17,512 | YES |
| 12 | none | +0.163 | +0.219 | 99 | $+11,470 | YES |
| 12 | 60 | +0.163 | +0.219 | 99 | $+11,470 | YES |
| 12 | 40 | +0.163 | +0.219 | 99 | $+11,470 | YES |
| 12 | 25 | +0.197 | +0.169 | 95 | $+9,728 | YES |
| 15 | none | +0.156 | +0.018 | 51 | $+4,664 | YES |
| 15 | 60 | +0.156 | +0.018 | 51 | $+4,664 | YES |
| 15 | 40 | +0.156 | +0.018 | 51 | $+4,664 | YES |
| 15 | 25 | +0.338 | -0.136 | 44 | $+3,211 | no |

## Verdict

**Best era-consistent band: floor 5pt, ceiling none** — net $+28,276, n=282, worse-era adjusted R +0.154.

This differs from the incumbent (9.5, no ceiling). Treat as a PROPOSAL requiring Angus sign-off and holdout confirmation, not a change to make here.
