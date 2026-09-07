# PREREGISTRATION-3 — FIT half, C1a_C3b, 3,661 trades (2018-09-01 → 2024-12-31)


**F1 — session VWAP position** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 1–2σ | 1567 | 54.7 | +9.53 | +4.34 | 12.8 | 19.1 |
| beyond 2σ | 264 | 58.7 | +19.83 | +7.14 | 13.2 | 20.8 |
| inside ±1σ | 1830 | 53.5 | +8.13 | +3.26 | 12.8 | 19.9 |

gap best−worst: **beyond 2σ** (+19.83, n=264) minus **inside ±1σ** (+8.13, n=1830) = +11.70, LB95 -2.42 → not a candidate

**F2 — VWAP direction** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 2585 | 55.0 | +7.83 | +3.93 | 13.0 | 19.4 |
| toward | 1076 | 52.9 | +13.77 | +6.93 | 12.5 | 20.1 |

gap best−worst: **toward** (+13.77, n=1076) minus **away** (+7.83, n=2585) = +5.94, LB95 -1.84 → not a candidate

**F3 — prior-day value area** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| above VAH | 1123 | 55.8 | +11.24 | +5.47 | 12.6 | 18.2 |
| below VAL | 1355 | 54.9 | +10.50 | +4.44 | 13.2 | 20.6 |
| inside VA | 1183 | 52.4 | +6.93 | +0.89 | 12.8 | 19.6 |

gap best−worst: **above VAH** (+11.24, n=1123) minus **inside VA** (+6.93, n=1183) = +4.30, LB95 -3.77 → not a candidate

**F4 — VA edge** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| at edge | 167 | 50.3 | -0.07 | -14.31 | 12.7 | 19.7 |
| not | 3494 | 54.6 | +10.04 | +6.40 | 12.9 | 19.6 |

(fewer than two buckets with n ≥ 200 — no gap test)

**F5 — POC distance** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.5–1.5 | 323 | 53.3 | +6.48 | -4.87 | 12.8 | 20.5 |
| <0.5 | 145 | 57.2 | +7.34 | -10.42 | 13.2 | 21.5 |
| >1.5 | 3193 | 54.4 | +9.99 | +6.23 | 12.8 | 19.4 |

gap best−worst: **>1.5** (+9.99, n=3193) minus **0.5–1.5** (+6.48, n=323) = +3.51, LB95 -8.53 → not a candidate

**F6 — POC direction** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 2476 | 54.9 | +9.46 | +5.22 | 12.9 | 19.6 |
| toward | 1185 | 53.2 | +9.82 | +3.64 | 12.7 | 19.5 |

gap best−worst: **toward** (+9.82, n=1185) minus **away** (+9.46, n=2476) = +0.36, LB95 -7.24 → not a candidate

**F7 — prior-session Fibonacci** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 589 | 53.7 | +5.39 | -2.82 | 12.9 | 20.3 |
| >0.75 | 2722 | 54.6 | +9.78 | +5.80 | 12.8 | 19.3 |
| ≤0.25 | 350 | 53.7 | +15.03 | +3.55 | 12.9 | 20.7 |

gap best−worst: **≤0.25** (+15.03, n=350) minus **0.25–0.75** (+5.39, n=589) = +9.64, LB95 -4.78 → not a candidate

**F8 — overnight Fibonacci** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 834 | 53.2 | +6.00 | -1.47 | 12.9 | 20.1 |
| >0.75 | 2145 | 54.8 | +10.12 | +5.72 | 12.7 | 18.9 |
| ≤0.25 | 682 | 54.4 | +12.22 | +3.59 | 13.3 | 21.0 |

gap best−worst: **≤0.25** (+12.22, n=682) minus **0.25–0.75** (+6.00, n=834) = +6.22, LB95 -4.82 → not a candidate

**F9 — EMA200 trend** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 726 | 52.8 | +14.75 | +6.14 | 12.6 | 19.7 |
| flat | 419 | 56.1 | +14.05 | +4.31 | 12.8 | 20.5 |
| with | 2516 | 54.6 | +7.34 | +3.40 | 12.9 | 19.4 |

gap best−worst: **against** (+14.75, n=726) minus **with** (+7.34, n=2516) = +7.42, LB95 -1.89 → not a candidate

**F10 — EMA20 distance** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| < −0.5 | 1170 | 54.5 | +14.77 | +7.98 | 12.3 | 19.5 |
| > 0.5 | 1473 | 54.5 | +8.95 | +3.99 | 13.3 | 19.5 |
| −0.5–0.5 | 1018 | 54.0 | +4.51 | -1.59 | 12.9 | 19.8 |

gap best−worst: **< −0.5** (+14.77, n=1170) minus **−0.5–0.5** (+4.51, n=1018) = +10.27, LB95 +1.46 → **CANDIDATE**

**F11 — EMA50 side** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 1391 | 55.5 | +16.39 | +10.28 | 12.4 | 19.7 |
| with | 2270 | 53.7 | +5.40 | +1.33 | 13.1 | 19.5 |

gap best−worst: **against** (+16.39, n=1391) minus **with** (+5.40, n=2270) = +10.99, LB95 +3.83 → **CANDIDATE**

**F12 — opening range** (n=3,661)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| beyond against | 216 | 54.6 | +10.61 | -2.20 | 12.4 | 19.3 |
| beyond in direction | 1215 | 57.9 | +11.05 | +5.86 | 12.7 | 18.5 |
| forming | 1248 | 51.0 | +10.03 | +3.10 | 12.9 | 20.8 |
| inside OR | 982 | 54.2 | +6.95 | +0.96 | 13.0 | 19.5 |

gap best−worst: **beyond in direction** (+11.05, n=1215) minus **inside OR** (+6.95, n=982) = +4.09, LB95 -3.66 → not a candidate

## Summary

| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |
|---|---|---|---|---|---|
| F1 session VWAP position | beyond 2σ | inside ±1σ | +11.70 | -2.42 | no |
| F2 VWAP direction | toward | away | +5.94 | -1.84 | no |
| F3 prior-day value area | above VAH | inside VA | +4.30 | -3.77 | no |
| F5 POC distance | >1.5 | 0.5–1.5 | +3.51 | -8.53 | no |
| F6 POC direction | toward | away | +0.36 | -7.24 | no |
| F7 prior-session Fibonacci | ≤0.25 | 0.25–0.75 | +9.64 | -4.78 | no |
| F8 overnight Fibonacci | ≤0.25 | 0.25–0.75 | +6.22 | -4.82 | no |
| F9 EMA200 trend | against | with | +7.42 | -1.89 | no |
| F10 EMA20 distance | < −0.5 | −0.5–0.5 | +10.27 | +1.46 | YES |
| F11 EMA50 side | against | with | +10.99 | +3.83 | YES |
| F12 opening range | beyond in direction | inside OR | +4.09 | -3.66 | no |
