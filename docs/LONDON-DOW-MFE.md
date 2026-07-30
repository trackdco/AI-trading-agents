# London by weekday and half-hour + the near-miss losers (110 trades)

**Working stack, FIT ONLY, descriptive — weekday cells are 15-30 trades and are NOT statistically charged. For eyeballs and forward watching; a weekday rule would need its own prereg.**

## 1. Day of week

| day | n | WR | mean R | net | avg/day traded | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Mon | 30 | 73% | +0.880 | $+6,711 | $+305 | $+1,835 | $+4,876 |
| Tue | 23 | 43% | +0.506 | $+2,140 | $+126 | $+961 | $+1,179 |
| Wed | 18 | 67% | +0.498 | $+2,120 | $+163 | $+962 | $+1,158 |
| Thu | 23 | 61% | +0.566 | $+3,541 | $+208 | $+1,986 | $+1,555 |
| Fri | 16 | 75% | +0.847 | $+3,429 | $+312 | $+912 | $+2,516 |

## 2. Weekday x half-hour (net $, n in brackets)

| day | 08:00-08:30 | 08:30-09:00 | 09:00-09:30 | day total |
|---|---|---|---|---|
| Mon | $+1,121 (11) | $+2,766 (7) | $+2,824 (12) | $+6,711 |
| Tue | $-352 (7) | $+282 (8) | $+2,210 (8) | $+2,140 |
| Wed | $+805 (7) | $+1,188 (7) | $+128 (4) | $+2,120 |
| Thu | $+470 (6) | $+566 (10) | $+2,505 (7) | $+3,541 |
| Fri | $+1,132 (4) | $+1,750 (5) | $+546 (7) | $+3,429 |

## 3. Month by month

| month | n | WR | net |
|---|---|---|---|
| 2025-06 | 5 | 60% | $+769 |
| 2025-07 | 4 | 25% | $-422 |
| 2025-08 | 6 | 100% | $+1,610 |
| 2025-09 | 6 | 83% | $+790 |
| 2025-10 | 7 | 57% | $+2,236 |
| 2025-11 | 15 | 60% | $+1,470 |
| 2025-12 | 3 | 67% | $+205 |
| 2026-01 | 6 | 67% | $+1,470 |
| 2026-02 | 8 | 38% | $+28 |
| 2026-03 | 19 | 47% | $+3,870 |
| 2026-04 | 8 | 75% | $+1,215 |
| 2026-05 | 8 | 75% | $+1,960 |
| 2026-06 | 12 | 75% | $+2,091 |
| 2026-07 | 3 | 100% | $+650 |

## 4. Trades that went up, then came back to the stop (MFE on 1m bars)

Of 40 losers:

| reached before dying | count | share of losers | dollars lost in these |
|---|---|---|---|
| >= +0.25R unrealized | 35 | 88% | $-8,482 |
| >= +0.50R unrealized | 35 | 88% | $-8,482 |
| >= +0.75R unrealized | 28 | 70% | $-6,980 |
| >= +1.00R unrealized | 17 | 42% | $-4,325 |

Median loser MFE: +0.94R. Median WINNER MFE: +2.42R.

### BE-at-XR what-if (conservative conventions in the header)

| rule | losers saved -> 0R | winners killed -> 0R | net change | new book net |
|---|---|---|---|---|
| BE at +0.5R | 33 ($+8,002) | 29 ($-8,126) | $-124 | $+17,818 |
| BE at +1.0R | 16 ($+4,090) | 14 ($-2,896) | $+1,194 | $+19,135 |

V8 management already takes partials; this what-if layers a BE stop on top and is an APPROXIMATION on 1m bars (same-bar spikes excluded, BE slippage ignored). If the number is material it justifies running the real engine tournament (V-variants, strategy doc §8) — it does not justify adopting anything from a bar-walk.
