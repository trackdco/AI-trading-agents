# Loser autopsy — hold_C1a_C3b.json (entries ≥ 2025-09-01)

config: {'stop_floor': 'a5_10pt', 'rr_gate': 'kept', 'rth_only': True, 'cap_lifted': False, 'slippage_mult': 1.0, 'perf_patch': True, 'deterministic_ids': True, 'fast_features': True}

## 1. Geometry
- trades 1123: winners 608, losers 515, scratch 0; win rate 54.1%
- average win **$+134.63**, average loss **$-109.39**, payoff ratio 1.23; breakeven win rate 44.8% vs actual 54.1% → margin +9.3 points
- gross wins $+81,854, gross losses $-56,337, net $+25,517
- loss quantiles: p10 -194, p25 -139, median -93, p75 -67, p90 -51, worst -463
- worst 5% of losers (25 trades) carry 13% of all losses; worst 10 trades carry 6%

**Ten largest losers**

| entry (ET) | dir | stop | ATR | score | HTF | regime | c1 exit | c2 exit | bars | $ |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-02-13 09:44 | short | 10.0 | 50.7 | 1.00 | 0.67 | high_volatility | stop | stop | 0 | -463 |
| 2026-07-31 09:38 | long | 18.2 | 32.7 | 0.85 | 0.33 | high_volatility | stop | stop | 0 | -403 |
| 2026-06-24 09:40 | long | 23.0 | 50.2 | 0.75 | 0.50 | high_volatility | stop | stop | 0 | -397 |
| 2026-06-30 09:34 | short | 17.8 | 31.5 | 0.90 | 0.50 | high_volatility | stop | stop | 0 | -360 |
| 2025-11-07 09:36 | long | 13.5 | 24.5 | 0.75 | 0.67 | trending_down | stop | stop | 0 | -336 |
| 2026-06-25 10:02 | short | 10.0 | 115.5 | 0.80 | 0.67 | high_volatility | stop | stop | 0 | -333 |
| 2026-08-13 09:34 | short | 13.5 | 15.2 | 0.75 | 0.83 | unknown | stop | stop | 0 | -325 |
| 2026-06-10 09:36 | short | 25.8 | 46.8 | 0.95 | 0.67 | ranging | stop | stop | 0 | -310 |
| 2026-07-09 09:34 | short | 22.2 | 25.2 | 0.85 | 0.67 | unknown | stop | stop | 0 | -310 |
| 2025-10-14 09:46 | short | 18.5 | 40.1 | 0.80 | 0.33 | high_volatility | stop | stop | 3 | -288 |

## 2. Exit anatomy

| exit pattern | losers | mean loss $ | winners | mean win $ |
|---|---|---|---|---|
| c1=stop / c2=stop | 479 | -117.4 | 0 | +0.0 |
| c1=c1_trail_from_profit / c2=breakeven | 35 | -2.3 | 342 | +38.7 |
| c1=c1_trail_from_profit / c2=trailing | 0 | +0.0 | 169 | +171.5 |
| c1=c1_trail_from_profit / c2=max_target | 0 | +0.0 | 71 | +498.0 |
| c1=c1_trail_from_profit / c2=time_stop | 0 | +0.0 | 26 | +165.1 |
| c1=time_12bars_fallback / c2=breakeven | 1 | -2.2 | 0 | +0.0 |

- both legs stopped: 479 of 515 losers (93%), mean -117.4
- losers' median holding 1 bars (2-min) vs winners' 7
- loss in stop units: median loss / (stop × $2 × 2 contracts) = 1.68 R

## 3. Where the losses cluster

**By entry hour (ET)**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 09:00 | 350 | 31% | 50 | +37.7 | +13,193 | 42% | -137.5 |
| 10:00 | 149 | 13% | 56 | +26.3 | +3,926 | 14% | -119.0 |
| 11:00 | 135 | 12% | 55 | +6.0 | +808 | 10% | -94.0 |
| 12:00 | 126 | 11% | 56 | +31.9 | +4,024 | 9% | -91.6 |
| 13:00 | 117 | 10% | 62 | +14.0 | +1,635 | 7% | -85.5 |
| 14:00 | 117 | 10% | 47 | -15.7 | -1,831 | 11% | -99.0 |
| 15:00 | 127 | 11% | 60 | +30.8 | +3,916 | 7% | -73.9 |
| 16:00 | 2 | 0% | 0 | -77.2 | -154 | 0% | -77.2 |

**First 30 minutes vs rest**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 09:30–10:00 | 350 | 31% | 50 | +37.7 | +13,193 | 42% | -137.5 |
| 10:00–15:30 | 702 | 63% | 56 | +15.2 | +10,679 | 53% | -97.4 |
| 15:30–16:00 | 71 | 6% | 54 | +23.2 | +1,645 | 4% | -72.8 |

**By weekday**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| Mon | 229 | 20% | 51 | +16.0 | +3,653 | 21% | -104.1 |
| Tue | 231 | 21% | 55 | +17.0 | +3,929 | 21% | -110.8 |
| Wed | 234 | 21% | 53 | +18.3 | +4,286 | 20% | -104.2 |
| Thu | 220 | 20% | 56 | +33.8 | +7,439 | 20% | -114.7 |
| Fri | 209 | 19% | 56 | +29.7 | +6,209 | 19% | -114.9 |

**By month**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 2025-09 | 55 | 5% | 51 | +5.7 | +312 | 4% | -80.6 |
| 2025-10 | 63 | 6% | 51 | +0.1 | +5 | 6% | -103.0 |
| 2025-11 | 82 | 7% | 51 | +40.0 | +3,282 | 8% | -116.8 |
| 2025-12 | 101 | 9% | 53 | +21.7 | +2,196 | 7% | -89.5 |
| 2026-01 | 86 | 8% | 52 | +4.6 | +393 | 7% | -92.5 |
| 2026-02 | 107 | 10% | 57 | +36.5 | +3,903 | 10% | -118.4 |
| 2026-03 | 141 | 13% | 61 | +36.7 | +5,178 | 10% | -106.6 |
| 2026-04 | 73 | 7% | 62 | +43.9 | +3,203 | 6% | -112.8 |
| 2026-05 | 67 | 6% | 52 | +16.1 | +1,082 | 6% | -112.4 |
| 2026-06 | 89 | 8% | 49 | +22.4 | +1,993 | 13% | -159.4 |
| 2026-07 | 122 | 11% | 48 | +1.6 | +194 | 14% | -121.2 |
| 2026-08 | 124 | 11% | 59 | +28.9 | +3,580 | 8% | -91.7 |
| 2026-09 | 13 | 1% | 31 | +15.0 | +195 | 1% | -82.5 |

**By stop distance**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 10.0 (floor bound) | 345 | 31% | 49 | +15.8 | +5,449 | 28% | -91.0 |
| 10–15 | 294 | 26% | 51 | +14.1 | +4,159 | 24% | -93.6 |
| 15–20 | 219 | 20% | 60 | +29.2 | +6,391 | 19% | -124.1 |
| 20–25 | 151 | 13% | 56 | +27.3 | +4,122 | 16% | -140.8 |
| 25–30 | 114 | 10% | 65 | +47.3 | +5,395 | 12% | -163.5 |

**By ATR14 at signal**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 10–15 | 125 | 11% | 52 | +4.0 | +495 | 7% | -65.8 |
| 15–20 | 182 | 16% | 55 | +18.3 | +3,331 | 11% | -74.6 |
| 20–30 | 389 | 35% | 55 | +13.3 | +5,156 | 33% | -106.4 |
| ≥30 | 427 | 38% | 54 | +38.7 | +16,534 | 49% | -139.7 |

**By stop / ATR**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| <0.7 | 731 | 65% | 52 | +24.0 | +17,535 | 71% | -112.6 |
| 0.7–1.0 | 392 | 35% | 59 | +20.4 | +7,982 | 29% | -102.4 |

**By HTF strength**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 0.2 | 8 | 1% | 50 | -22.4 | -179 | 1% | -109.2 |
| 0.3 | 114 | 10% | 56 | +39.6 | +4,517 | 10% | -108.1 |
| 0.5 | 392 | 35% | 52 | +25.2 | +9,878 | 36% | -106.2 |
| 0.7 | 342 | 30% | 55 | +9.8 | +3,363 | 31% | -113.6 |
| 0.8 | 210 | 19% | 56 | +33.1 | +6,961 | 18% | -110.4 |
| 1.0 | 57 | 5% | 56 | +17.1 | +977 | 5% | -106.5 |

**By signal score**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 0.75 | 590 | 53% | 55 | +29.6 | +17,469 | 46% | -98.5 |
| 0.80 | 320 | 28% | 56 | +12.2 | +3,917 | 29% | -116.0 |
| 0.85 | 116 | 10% | 48 | +23.2 | +2,693 | 12% | -115.6 |
| 0.90 | 59 | 5% | 51 | +21.9 | +1,293 | 7% | -127.3 |
| 0.95 | 24 | 2% | 42 | +2.2 | +53 | 4% | -144.9 |
| 1.00 | 14 | 1% | 50 | +6.5 | +91 | 2% | -185.9 |

**By regime label**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| high_volatility | 277 | 25% | 52 | +32.6 | +9,029 | 32% | -133.7 |
| ranging | 233 | 21% | 52 | +7.2 | +1,672 | 19% | -92.5 |
| trending_down | 183 | 16% | 52 | +9.7 | +1,776 | 17% | -108.0 |
| trending_up | 168 | 15% | 51 | +18.2 | +3,064 | 15% | -103.3 |
| unknown | 262 | 23% | 62 | +38.1 | +9,976 | 18% | -102.4 |

**By direction**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| long | 491 | 44% | 53 | +18.2 | +8,912 | 43% | -102.9 |
| short | 632 | 56% | 55 | +26.3 | +16,605 | 57% | -114.8 |

**Direction vs HTF bias**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| long with HTF bearish | 62 | 6% | 48 | +52.5 | +3,255 | 7% | -130.6 |
| long with HTF bullish | 410 | 37% | 53 | +13.4 | +5,490 | 33% | -96.6 |
| long with HTF neutral | 19 | 2% | 58 | +8.8 | +167 | 2% | -143.3 |
| short with HTF bearish | 494 | 44% | 56 | +21.1 | +10,446 | 44% | -113.5 |
| short with HTF bullish | 113 | 10% | 54 | +54.3 | +6,138 | 11% | -116.9 |
| short with HTF neutral | 25 | 2% | 44 | +0.8 | +21 | 3% | -127.1 |

## 4. Streaks, days, drawdown
- max consecutive losers 8; trading days 250, losing days 110 (44%)
- worst day $-645, worst 5 days -645, -635, -635, -614, -608; best day $+1,804
- max drawdown $2,285 from 2026-07-08 to 2026-07-23
- worst weeks: 2026-W29 -1,169, 2025-W42 -924, 2026-W17 -786; losing weeks 15 of 53

## 5. Friction
- commission $5,795, slippage $4,544 (entry 2,250 + exit 2,294); friction total $10,339 = 31% of pre-friction gross
- friction per trade $9.21; on losers it adds $9.19 to a mean loss of $-109.39 (8%)
