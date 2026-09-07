# PREREGISTRATION-3 — TEST half, C1a_C3b, 1,893 trades (2025-01-01 → 2026-09-02)


**F1 — session VWAP position** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 1–2σ | 822 | 52.6 | +7.57 | -0.67 | 14.9 | 26.6 |
| beyond 2σ | 90 | 57.8 | +29.73 | +1.58 | 16.3 | 29.1 |
| inside ±1σ | 981 | 52.7 | +23.07 | +13.67 | 15.0 | 27.1 |

gap best−worst: **inside ±1σ** (+23.07, n=981) minus **1–2σ** (+7.57, n=822) = +15.50, LB95 +2.90 → **CANDIDATE**

**F2 — VWAP direction** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 1392 | 54.0 | +19.18 | +11.93 | 15.0 | 26.5 |
| toward | 501 | 49.7 | +9.65 | -3.03 | 14.9 | 28.3 |

gap best−worst: **away** (+19.18, n=1392) minus **toward** (+9.65, n=501) = +9.53, LB95 -5.17 → not a candidate

**F3 — prior-day value area** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| above VAH | 669 | 55.0 | +22.63 | +12.27 | 14.3 | 24.7 |
| below VAL | 667 | 52.3 | +20.58 | +9.59 | 15.8 | 29.3 |
| inside VA | 557 | 51.0 | +4.79 | -6.30 | 14.8 | 27.0 |

gap best−worst: **above VAH** (+22.63, n=669) minus **inside VA** (+4.79, n=557) = +17.84, LB95 +2.67 → **CANDIDATE**

**F4 — VA edge** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| at edge | 93 | 55.9 | +11.79 | -21.26 | 15.7 | 28.1 |
| not | 1800 | 52.7 | +16.91 | +10.47 | 14.9 | 26.9 |

(fewer than two buckets with n ≥ 200 — no gap test)

**F5 — POC distance** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.5–1.5 | 153 | 49.7 | -1.04 | -20.55 | 14.9 | 31.2 |
| <0.5 | 61 | 59.0 | +34.67 | -12.44 | 16.2 | 31.7 |
| >1.5 | 1679 | 52.9 | +17.62 | +11.31 | 14.9 | 26.4 |

(fewer than two buckets with n ≥ 200 — no gap test)

**F6 — POC direction** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| away | 1251 | 53.5 | +17.51 | +9.83 | 15.2 | 27.1 |
| toward | 642 | 51.7 | +14.99 | +3.06 | 14.4 | 26.9 |

gap best−worst: **away** (+17.51, n=1251) minus **toward** (+14.99, n=642) = +2.53, LB95 -12.36 → not a candidate

**F7 — prior-session Fibonacci** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 299 | 55.2 | +25.86 | +8.05 | 15.2 | 29.1 |
| >0.75 | 1437 | 52.7 | +14.47 | +7.63 | 14.8 | 26.3 |
| ≤0.25 | 157 | 50.3 | +19.17 | -5.21 | 15.9 | 29.5 |

gap best−worst: **0.25–0.75** (+25.86, n=299) minus **>0.75** (+14.47, n=1437) = +11.39, LB95 -7.81 → not a candidate

**F8 — overnight Fibonacci** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| 0.25–0.75 | 413 | 52.5 | +14.17 | -0.65 | 15.2 | 28.4 |
| >0.75 | 1170 | 54.4 | +19.21 | +11.64 | 14.7 | 25.7 |
| ≤0.25 | 310 | 47.4 | +10.33 | -8.31 | 15.8 | 30.0 |

gap best−worst: **>0.75** (+19.21, n=1170) minus **≤0.25** (+10.33, n=310) = +8.88, LB95 -13.55 → not a candidate

**F9 — EMA200 trend** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 366 | 50.8 | +17.52 | +1.89 | 15.0 | 27.3 |
| flat | 176 | 46.6 | +32.03 | +4.07 | 14.9 | 28.1 |
| with | 1351 | 54.3 | +14.42 | +7.44 | 15.0 | 26.8 |

gap best−worst: **against** (+17.52, n=366) minus **with** (+14.42, n=1351) = +3.10, LB95 -15.00 → not a candidate

**F10 — EMA20 distance** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| < −0.5 | 587 | 49.4 | +7.44 | -3.18 | 14.4 | 27.7 |
| > 0.5 | 772 | 55.2 | +14.88 | +5.12 | 15.6 | 26.8 |
| −0.5–0.5 | 534 | 53.4 | +29.36 | +16.85 | 14.7 | 26.5 |

gap best−worst: **−0.5–0.5** (+29.36, n=534) minus **< −0.5** (+7.44, n=587) = +21.92, LB95 +6.02 → **CANDIDATE**

**F11 — EMA50 side** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 698 | 49.9 | +10.45 | -0.03 | 14.5 | 27.4 |
| with | 1195 | 54.6 | +20.28 | +12.17 | 15.3 | 26.8 |

gap best−worst: **with** (+20.28, n=1195) minus **against** (+10.45, n=698) = +9.83, LB95 -3.47 → not a candidate

**F12 — opening range** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| beyond against | 117 | 59.8 | +25.50 | +5.60 | 14.0 | 25.1 |
| beyond in direction | 630 | 53.8 | +9.15 | +0.74 | 14.7 | 24.8 |
| forming | 599 | 49.2 | +28.60 | +14.11 | 15.4 | 30.0 |
| inside OR | 547 | 54.3 | +10.34 | +0.08 | 15.1 | 26.6 |

gap best−worst: **forming** (+28.60, n=599) minus **beyond in direction** (+9.15, n=630) = +19.45, LB95 +3.45 → **CANDIDATE**

## Summary

| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |
|---|---|---|---|---|---|
| F1 session VWAP position | inside ±1σ | 1–2σ | +15.50 | +2.90 | YES |
| F2 VWAP direction | away | toward | +9.53 | -5.17 | no |
| F3 prior-day value area | above VAH | inside VA | +17.84 | +2.67 | YES |
| F6 POC direction | away | toward | +2.53 | -12.36 | no |
| F7 prior-session Fibonacci | 0.25–0.75 | >0.75 | +11.39 | -7.81 | no |
| F8 overnight Fibonacci | >0.75 | ≤0.25 | +8.88 | -13.55 | no |
| F9 EMA200 trend | against | with | +3.10 | -15.00 | no |
| F10 EMA20 distance | −0.5–0.5 | < −0.5 | +21.92 | +6.02 | YES |
| F11 EMA50 side | with | against | +9.83 | -3.47 | no |
| F12 opening range | forming | beyond in direction | +19.45 | +3.45 | YES |
