# Loser autopsy — hold_C1a_C3a.json (entries ≥ 2025-09-01)

config: {'stop_floor': 'a5_10pt', 'rr_gate': 'removed', 'rth_only': True, 'cap_lifted': False, 'slippage_mult': 1.0, 'perf_patch': True, 'deterministic_ids': True, 'fast_features': True}

## 1. Geometry
- trades 1431: winners 800, losers 631, scratch 0; win rate 55.9%
- average win **$+118.78**, average loss **$-107.17**, payoff ratio 1.11; breakeven win rate 47.4% vs actual 55.9% → margin +8.5 points
- gross wins $+95,022, gross losses $-67,624, net $+27,398
- loss quantiles: p10 -190, p25 -139, median -94, p75 -68, p90 -6, worst -463
- worst 5% of losers (31 trades) carry 13% of all losses; worst 10 trades carry 5%

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
| 2026-04-08 14:10 | long | 15.2 | 11.7 | 0.80 | 0.33 | trending_up | stop | stop | 4 | -309 |

## 2. Exit anatomy

| exit pattern | losers | mean loss $ | winners | mean win $ |
|---|---|---|---|---|
| c1=stop / c2=stop | 567 | -119.0 | 0 | +0.0 |
| c1=c1_trail_from_profit / c2=breakeven | 59 | -2.2 | 454 | +33.3 |
| c1=c1_trail_from_profit / c2=trailing | 1 | -2.2 | 233 | +158.6 |
| c1=c1_trail_from_profit / c2=max_target | 0 | +0.0 | 74 | +495.2 |
| c1=c1_trail_from_profit / c2=time_stop | 0 | +0.0 | 39 | +162.0 |
| c1=time_12bars_fallback / c2=breakeven | 4 | -2.7 | 0 | +0.0 |

- both legs stopped: 567 of 631 losers (90%), mean -119.0
- losers' median holding 1 bars (2-min) vs winners' 8
- loss in stop units: median loss / (stop × $2 × 2 contracts) = 1.51 R

## 3. Where the losses cluster

**By entry hour (ET)**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 09:00 | 413 | 29% | 51 | +29.6 | +12,233 | 42% | -138.4 |
| 10:00 | 169 | 12% | 59 | +23.7 | +4,009 | 12% | -116.6 |
| 11:00 | 165 | 12% | 59 | +9.4 | +1,556 | 10% | -97.2 |
| 12:00 | 152 | 11% | 61 | +30.6 | +4,658 | 8% | -92.2 |
| 13:00 | 171 | 12% | 58 | +4.5 | +775 | 9% | -86.1 |
| 14:00 | 164 | 11% | 51 | -6.4 | -1,048 | 11% | -95.3 |
| 15:00 | 191 | 13% | 60 | +27.5 | +5,257 | 8% | -68.5 |
| 16:00 | 6 | 0% | 67 | -7.3 | -44 | 0% | -77.2 |

**First 30 minutes vs rest**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 09:30–10:00 | 413 | 29% | 51 | +29.6 | +12,233 | 42% | -138.4 |
| 10:00–15:30 | 896 | 63% | 58 | +13.3 | +11,915 | 54% | -95.8 |
| 15:30–16:00 | 122 | 9% | 61 | +26.6 | +3,250 | 5% | -64.3 |

**By weekday**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| Mon | 312 | 22% | 53 | +8.4 | +2,607 | 23% | -104.5 |
| Tue | 302 | 21% | 56 | +15.3 | +4,632 | 21% | -107.1 |
| Wed | 306 | 21% | 54 | +13.6 | +4,160 | 21% | -101.7 |
| Thu | 255 | 18% | 58 | +38.1 | +9,716 | 17% | -110.4 |
| Fri | 256 | 18% | 59 | +24.5 | +6,283 | 18% | -114.8 |

**By month**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 2025-09 | 99 | 7% | 55 | +0.5 | +47 | 6% | -86.3 |
| 2025-10 | 104 | 7% | 52 | -6.5 | -674 | 7% | -100.8 |
| 2025-11 | 94 | 7% | 53 | +39.5 | +3,712 | 7% | -109.0 |
| 2025-12 | 157 | 11% | 57 | +17.4 | +2,729 | 8% | -79.6 |
| 2026-01 | 128 | 9% | 54 | +7.6 | +967 | 8% | -96.1 |
| 2026-02 | 125 | 9% | 54 | +24.5 | +3,059 | 10% | -120.2 |
| 2026-03 | 149 | 10% | 63 | +39.6 | +5,899 | 9% | -111.2 |
| 2026-04 | 101 | 7% | 59 | +22.6 | +2,278 | 8% | -124.1 |
| 2026-05 | 75 | 5% | 60 | +36.1 | +2,710 | 5% | -110.7 |
| 2026-06 | 96 | 7% | 51 | +21.0 | +2,011 | 11% | -158.6 |
| 2026-07 | 137 | 10% | 52 | +5.4 | +739 | 11% | -117.1 |
| 2026-08 | 152 | 11% | 61 | +25.0 | +3,805 | 8% | -92.2 |
| 2026-09 | 14 | 1% | 29 | +8.3 | +117 | 1% | -82.1 |

**By stop distance**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 10.0 (floor bound) | 351 | 25% | 48 | +11.0 | +3,847 | 25% | -91.0 |
| 10–15 | 303 | 21% | 51 | +13.1 | +3,964 | 19% | -88.9 |
| 15–20 | 312 | 22% | 64 | +22.1 | +6,906 | 19% | -115.7 |
| 20–25 | 231 | 16% | 60 | +30.7 | +7,082 | 16% | -118.4 |
| 25–30 | 234 | 16% | 60 | +23.9 | +5,599 | 20% | -146.6 |

**By ATR14 at signal**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| <10 | 76 | 5% | 51 | -7.4 | -560 | 3% | -51.9 |
| 10–15 | 248 | 17% | 54 | +0.3 | +67 | 14% | -81.1 |
| 15–20 | 247 | 17% | 64 | +21.6 | +5,338 | 11% | -79.8 |
| 20–30 | 431 | 30% | 55 | +13.3 | +5,742 | 32% | -113.1 |
| ≥30 | 429 | 30% | 54 | +39.2 | +16,810 | 41% | -139.2 |

**By stop / ATR**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| <0.7 | 690 | 48% | 53 | +26.2 | +18,083 | 56% | -116.4 |
| 0.7–1.0 | 350 | 24% | 60 | +20.8 | +7,297 | 22% | -105.6 |
| 1.0–1.5 | 255 | 18% | 58 | +4.4 | +1,130 | 14% | -90.5 |
| ≥1.5 | 136 | 10% | 58 | +6.5 | +887 | 8% | -89.4 |

**By HTF strength**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 0.2 | 13 | 1% | 54 | -11.5 | -149 | 1% | -102.0 |
| 0.3 | 168 | 12% | 55 | +22.7 | +3,819 | 11% | -102.7 |
| 0.5 | 474 | 33% | 54 | +23.2 | +10,977 | 34% | -105.9 |
| 0.7 | 446 | 31% | 57 | +6.9 | +3,069 | 32% | -112.9 |
| 0.8 | 258 | 18% | 57 | +35.1 | +9,060 | 17% | -102.8 |
| 1.0 | 72 | 5% | 57 | +8.6 | +623 | 5% | -108.0 |

**By signal score**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| 0.75 | 736 | 51% | 58 | +28.0 | +20,602 | 43% | -92.9 |
| 0.80 | 428 | 30% | 56 | +6.9 | +2,934 | 32% | -114.2 |
| 0.85 | 143 | 10% | 56 | +30.5 | +4,363 | 11% | -118.8 |
| 0.90 | 71 | 5% | 46 | +2.4 | +167 | 7% | -130.5 |
| 0.95 | 34 | 2% | 38 | -18.6 | -631 | 5% | -148.0 |
| 1.00 | 19 | 1% | 47 | -2.0 | -37 | 3% | -170.1 |

**By regime label**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| high_volatility | 312 | 22% | 52 | +25.7 | +8,024 | 30% | -135.5 |
| ranging | 306 | 21% | 58 | +10.5 | +3,204 | 17% | -90.5 |
| trending_down | 230 | 16% | 54 | +6.6 | +1,523 | 17% | -108.9 |
| trending_up | 238 | 17% | 54 | +14.9 | +3,549 | 16% | -99.3 |
| unknown | 345 | 24% | 60 | +32.2 | +11,098 | 20% | -96.8 |

**By direction**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| long | 679 | 47% | 54 | +14.0 | +9,520 | 48% | -104.0 |
| short | 752 | 53% | 57 | +23.8 | +17,878 | 52% | -110.3 |

**Direction vs HTF bias**

| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |
|---|---|---|---|---|---|---|---|
| long with HTF bearish | 77 | 5% | 52 | +39.3 | +3,025 | 7% | -133.0 |
| long with HTF bullish | 575 | 40% | 55 | +12.3 | +7,087 | 38% | -97.8 |
| long with HTF neutral | 27 | 2% | 52 | -21.9 | -592 | 3% | -143.9 |
| short with HTF bearish | 580 | 41% | 58 | +17.4 | +10,118 | 40% | -110.2 |
| short with HTF bullish | 138 | 10% | 58 | +51.1 | +7,056 | 9% | -108.6 |
| short with HTF neutral | 34 | 2% | 50 | +20.7 | +703 | 3% | -117.0 |

## 4. Streaks, days, drawdown
- max consecutive losers 8; trading days 259, losing days 119 (46%)
- worst day $-675, worst 5 days -675, -645, -635, -623, -608; best day $+1,804
- max drawdown $2,198 from 2026-07-10 to 2026-07-23
- worst weeks: 2026-W29 -1,393, 2025-W42 -908, 2025-W40 -814; losing weeks 14 of 53

## 5. Friction
- commission $7,384, slippage $5,853 (entry 2,874 + exit 2,979); friction total $13,237 = 35% of pre-friction gross
- friction per trade $9.25; on losers it adds $9.22 to a mean loss of $-107.17 (9%)
