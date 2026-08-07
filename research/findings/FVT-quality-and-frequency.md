---
date: 2026-08-06
status: RESULT — quality buys expectancy, not win rate. Frequency is the binding constraint.
tags: [fvt, quality, win-rate, green-days, frontier, prop]
scripts: scripts/fvt_quality.py, scripts/fvt_sessions.py, scripts/fvt_monthcv.py
---

# Setup quality buys expectancy, not win rate — and green days cap at 52.6%

ANGUS: *"We need to split the winners from losers. I guarantee you that's where his edge is…
he's consistent at 1.5r, guarantee his win rate is very high because he can see a bad trade
and not take it."* And: *"id be more than happy with some shit that cuts trades more but
boosts win rate."*

## Five quality dimensions are positive in all four years

Built from what a discretionary trader judges, including **JJ's own stated size rule** which
this project had previously dropped (*"ideally is larger than the candles before it"*).

| dimension | tier | n | gross | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|
| `dist_fv` | HIGH | 1,375 | +2.51 | +0.42 | +0.08 | +4.36 | +7.21 |
| `swing_age` | HIGH | 1,577 | +1.89 | +0.91 | +0.19 | +3.91 | +3.78 |
| `body_frac` | MID | 1,370 | +1.65 | +2.00 | +0.60 | +1.43 | +3.96 |
| `vol_ratio` | LOW | 1,375 | +1.56 | +1.10 | +0.28 | +2.89 | +2.15 |
| `break_depth` | HIGH | 1,375 | +0.92 | +0.26 | +1.58 | +0.82 | +1.15 |

## But stacking them does not raise the win rate

Alignment score = count of the five conditions met. At **JJ's 1.5R**:

| score | n | win rate | gross |
|---:|---:|---:|---:|
| 0 | 519 | 44.1% | +0.87 |
| 1 | 1,310 | 42.6% | +0.04 |
| 2 | 1,337 | 42.8% | +0.48 |
| 3 | 750 | 43.7% | +1.20 |
| 4 | 197 | **47.2%** | +2.47 |

`corr(score, win rate) = **+0.010**`. Even the strictest tier — 4 of 5 conditions, 5% of
setups, 0.18 trades/day — reaches only **47.2%**, not the 60–70% the hypothesis requires.

At RR 2.5 the same score separates cleanly (gross +0.04 → +3.92 across tiers). **Quality
predicts how FAR price runs, not WHETHER it goes the right way.** That is why it is worthless
at 1.5R and works at 2.5R.

This replicates the canon's alignment-score result almost exactly (+0.014 here vs +0.032
there), which suggests "stack quality conditions" is a dead end generally, not just here.

## Green days cap at 52.6%, and that cell loses money

| RR | filter | /day | win% | net | **green days** | pts/yr |
|---:|---|---:|---:|---:|---:|---:|
| 0.75 | score≥3 | 0.87 | 56.0% | **−0.29** | **52.6%** | −64 |
| 1.00 | score≥3 | 0.87 | 51.2% | +0.38 | 48.6% | 84 |
| 1.50 | none | 3.74 | 42.8% | +0.12 | 48.2% | 112 |
| 2.50 | none | 3.74 | 37.4% | +0.65 | 45.6% | **612** |
| 2.50 | score≥3 | 0.87 | 39.4% | **+2.31** | 41.5% | 505 |

Every route to a higher win rate costs more in payoff than it gains in hit rate — the same
win-rate/win-size frontier that killed the canon, now on the RR axis.

## The tension, and the spec it implies

- **Green days need FREQUENCY** — several trades a day average out within the day
- **Expectancy needs SELECTIVITY and high RR** — fewer trades, lower win rate

They oppose. Reaching **55% green days** at this win rate needs roughly **8–10 trades/day**.
FVT delivers 3.74 at most, 0.87 once filtered.

## Carry forward

1. **The quality score is a SIZING signal, not a filter.** +2.31 pt/trade at RR 2.5, positive
   in all four years (+0.84 / +1.27 / +2.29 / +7.95) — the best per-trade result of the
   session. Used to size up rather than to exclude, it keeps the frequency.
2. **Frequency is the binding constraint on everything.** The next trigger must fire 8–10
   times a day. That is now a design spec, not something to discover afterwards.

## Note on video evidence

Frame extraction from JJ's trade-by-trade videos was attempted to compare his actual entries
against the full candidate set. ffmpeg installs fine; YouTube returns 403 on media fetch and
bot-checks every player client (the one that passes is DRM protected). Metadata and channel
listings work, media does not. Screenshots supplied manually instead.
