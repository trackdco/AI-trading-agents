# PREREGISTRATION-3 — TEST half, C1a_C3a, 2,460 trades (2025-01-01 → 2026-09-02)


**F1 — session VWAP position** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 1–2σ | 1063 | 54.8 | +11.41 | +4.06 | 16.8 | 23.5 |
| beyond 2σ | 113 | 57.5 | +26.56 | +0.48 | 19.2 | 25.7 |
| inside ±1σ | 1284 | 56.0 | +19.82 | +11.99 | 16.8 | 24.2 |

gap best−worst: **inside ±1σ** (+19.82, n=1284) minus **1–2σ** (+11.41, n=1063) = +8.41, LB95 -2.52 → not a candidate

**F2 — VWAP direction** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 1845 | 56.7 | +18.57 | +12.31 | 17.0 | 23.4 |
| toward | 615 | 52.0 | +10.26 | -0.43 | 16.6 | 25.7 |

gap best−worst: **away** (+18.57, n=1845) minus **toward** (+10.26, n=615) = +8.31, LB95 -4.08 → not a candidate

**F3 — prior-day value area** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| above VAH | 948 | 55.9 | +15.23 | +6.93 | 16.5 | 21.2 |
| below VAL | 801 | 55.3 | +20.95 | +11.20 | 17.5 | 27.0 |
| inside VA | 711 | 55.3 | +13.17 | +3.57 | 16.8 | 24.3 |

gap best−worst: **below VAL** (+20.95, n=801) minus **inside VA** (+13.17, n=711) = +7.79, LB95 -6.39 → not a candidate

**F4 — VA edge** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| at edge | 101 | 52.5 | +1.63 | -28.61 | 17.2 | 27.6 |
| not | 2359 | 55.7 | +17.13 | +11.67 | 16.9 | 23.8 |

(fewer than two buckets with n ≥ 200 — no gap test)

**F5 — POC distance** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.5–1.5 | 188 | 55.9 | +20.02 | +0.38 | 16.7 | 28.1 |
| <0.5 | 89 | 59.6 | +21.33 | -12.57 | 17.7 | 27.1 |
| >1.5 | 2183 | 55.3 | +16.00 | +10.63 | 16.9 | 23.5 |

(fewer than two buckets with n ≥ 200 — no gap test)

**F6 — POC direction** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 1652 | 55.3 | +15.57 | +9.20 | 17.1 | 23.8 |
| toward | 808 | 56.1 | +18.38 | +8.46 | 16.5 | 24.3 |

gap best−worst: **toward** (+18.38, n=808) minus **away** (+15.57, n=1652) = +2.81, LB95 -9.44 → not a candidate

**F7 — prior-session Fibonacci** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 376 | 58.5 | +28.75 | +13.38 | 17.0 | 26.9 |
| >0.75 | 1886 | 55.1 | +13.29 | +7.37 | 16.8 | 23.2 |
| ≤0.25 | 198 | 54.0 | +23.79 | +3.15 | 17.6 | 26.1 |

gap best−worst: **0.25–0.75** (+28.75, n=376) minus **>0.75** (+13.29, n=1886) = +15.46, LB95 -1.16 → not a candidate

**F8 — overnight Fibonacci** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 513 | 52.8 | +9.01 | -3.48 | 16.9 | 25.5 |
| >0.75 | 1558 | 57.3 | +18.75 | +12.61 | 16.8 | 22.7 |
| ≤0.25 | 389 | 51.9 | +17.35 | +1.06 | 17.3 | 26.9 |

gap best−worst: **>0.75** (+18.75, n=1558) minus **0.25–0.75** (+9.01, n=513) = +9.74, LB95 -4.87 → not a candidate

**F9 — EMA200 trend** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 466 | 52.8 | +19.97 | +7.20 | 17.0 | 24.0 |
| flat | 243 | 52.7 | +24.41 | +2.83 | 16.6 | 24.5 |
| with | 1751 | 56.7 | +14.47 | +8.48 | 16.9 | 23.9 |

gap best−worst: **flat** (+24.41, n=243) minus **with** (+14.47, n=1751) = +9.94, LB95 -12.99 → not a candidate

**F10 — EMA20 distance** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| < −0.5 | 687 | 52.7 | +8.71 | -1.27 | 15.9 | 25.9 |
| > 0.5 | 1114 | 56.6 | +16.19 | +8.20 | 17.9 | 22.7 |
| −0.5–0.5 | 659 | 56.6 | +25.13 | +14.68 | 16.3 | 24.1 |

gap best−worst: **−0.5–0.5** (+25.13, n=659) minus **< −0.5** (+8.71, n=687) = +16.42, LB95 +2.14 → **CANDIDATE**

**F11 — EMA50 side** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 845 | 53.0 | +11.23 | +2.18 | 16.2 | 25.3 |
| with | 1615 | 56.8 | +19.25 | +12.68 | 17.3 | 23.3 |

gap best−worst: **with** (+19.25, n=1615) minus **against** (+11.23, n=845) = +8.03, LB95 -3.17 → not a candidate

**F12 — opening range** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| beyond against | 141 | 58.9 | +19.20 | +2.01 | 15.9 | 22.7 |
| beyond in direction | 882 | 57.0 | +9.03 | +2.21 | 16.9 | 21.7 |
| forming | 713 | 52.6 | +30.13 | +16.98 | 17.5 | 27.3 |
| inside OR | 724 | 55.9 | +11.64 | +2.82 | 16.5 | 23.7 |

gap best−worst: **forming** (+30.13, n=713) minus **beyond in direction** (+9.03, n=882) = +21.10, LB95 +6.82 → **CANDIDATE**

## Summary

| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |
|---|---|---|---|---|---|
| F1 session VWAP position | inside ±1σ | 1–2σ | +8.41 | -2.52 | no |
| F2 VWAP direction | away | toward | +8.31 | -4.08 | no |
| F3 prior-day value area | below VAL | inside VA | +7.79 | -6.39 | no |
| F6 POC direction | toward | away | +2.81 | -9.44 | no |
| F7 prior-session Fibonacci | 0.25–0.75 | >0.75 | +15.46 | -1.16 | no |
| F8 overnight Fibonacci | >0.75 | 0.25–0.75 | +9.74 | -4.87 | no |
| F9 EMA200 trend | flat | with | +9.94 | -12.99 | no |
| F10 EMA20 distance | −0.5–0.5 | < −0.5 | +16.42 | +2.14 | YES |
| F11 EMA50 side | with | against | +8.03 | -3.17 | no |
| F12 opening range | forming | beyond in direction | +21.10 | +6.82 | YES |
