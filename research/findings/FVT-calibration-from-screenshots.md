---
date: 2026-08-06
status: RESULT — ATR timeframe recalibrated from live screenshots. Base book now 4/4 years.
tags: [fvt, calibration, atr, bias, screenshots, nq]
---

# The ATR timeframe was wrong, and his screenshots proved it

ANGUS supplied six screenshots of JJ Simon's live trading (27 July 2026, NQU26/NQU6, Tradovate
+ TopstepX + a DOM platform). They settled several questions the written rules could not.

## What the screenshots verify

| written rule | what he actually does |
|---|---|
| market entry | limit and stop orders visible in the order feed |
| fixed 1.5R | **0.89R and 1.5R** both observed |
| ATR tiers 16.5/25/50 pt | stops of **25, 50, 56.25 and 83.5 pt** |
| 09:30–11:00 and 14:00–15:00 ET | **~08:47 ET pre-market** and **18:00–18:30 ET** |
| (not mentioned) | a moving average on the Tradovate chart |

Arithmetic confirmations, worked from the P&L tags:
- 5 contracts, target 27,829.25 from 27,905 = 75.75 pt × 5 × $20 = **$7,575** ✓ (tag matched)
- TP +$7,560 / SL −$5,010 on 3 contracts = 126 pt / 83.5 pt = **1.509R**
- Short 2: stop −$2,250, target +$2,000 = 56.25 pt / 50 pt = **0.89R**

Also visible: **at least five prop accounts** with different balances (copy-trading), ~$5,000
risk per trade on $100–160k accounts, and bracket orders placed at entry with no management.

## The calibration error

His stops are 50–83.5 pt, which under his own tiers means an ATR reading **above 20**. NQ's
**1-minute** ATR(14) has a median of **5.6** — it can never reach that band, so 61% of our
trades were being assigned the *bottom* 16.5pt tier while he sits in the top one.

| ATR timeframe | median | % in >20 band | dominant tier |
|---|---:|---:|---|
| 1m (was used) | 5.6 | 5.1% | 16.5pt |
| 5m | 13.3 | 30.0% | 25pt |
| 15m | 24.2 | 59.7% | 50pt |
| **30m** | **35.5** | **79.7%** | **50pt** |
| 60m | 51.2 | 96.8% | 50pt |

**The timeframe was not fitted — it was read off his screen.** That distinction matters: every
other parameter choice this session was an optimisation and failed out of sample.

## The corrected base book — ATR(30m), RR 1.5, friction 0.5pt

**4,122 trades, 3.74/day, 47.1% win, +1.12 pt/trade, 50.7% green days, 1,058 pts/yr/contract.**
Years: **+0.94 / +1.06 / +1.23 / +1.37** — the most evenly matched result of the session.

And it is not parameter-sensitive. **Every RR from 1.0 to 3.0 is positive in all four years:**

| RR | 1.00 | 1.25 | 1.50 | 1.75 | 2.00 | 2.50 | 3.00 |
|---|---:|---:|---:|---:|---:|---:|---:|
| net | +0.67 | +0.99 | +1.12 | +1.00 | +1.00 | +1.21 | +1.36 |
| green | 49.8% | **52.1%** | 50.7% | 50.4% | 48.6% | 47.3% | 46.8% |
| 4/4 | yes | yes | yes | yes | yes | yes | yes |

Three of five ATR timeframes (15/30/60m) are also 4/4, so neither axis is a knife-edge.

## Bias is a different lever from quality — and it works on win rate

Angus: *"he's always talking about his bias for the session… he doesn't trade every trigger."*

| filter | /day | win% | net | green | 4/4 |
|---|---:|---:|---:|---:|:---:|
| no bias | 3.74 | 47.1% | +1.12 | 50.7% | yes |
| **longs only** | 1.83 | **50.4%** | +1.85 | **52.0%** | yes |
| shorts only | 1.90 | 43.9% | +0.42 | 47.7% | |
| against 20d trend | 1.75 | 46.4% | +2.33 | 50.8% | yes |
| with 20d trend | 1.64 | 47.6% | −0.31 | 49.0% | |

Direction filters move the win rate (43.9% → 50.4%). **Setup-quality filters could not**
(42.6% → 47.2% at best, corr +0.010). He is not selecting better setups — he is selecting a
side and then taking setups that agree with it.

## Caveats kept on the record

- **Longs-only is probably beta.** NQ went ~11,000 → ~29,000 over the span. Intraday and flat
  by session close, which weakens the objection, but it needs a bear span to test and 2022 is
  outside our data.
- **~10 bias variants tested, two came back 4/4.** Selection risk.
- **0.5pt friction is load-bearing** and unverified against Angus's real commissions.
- The combined book still leans on **session diversification** — only NY PM is individually 4/4.
- **All four years are now used.** There is no clean holdout left; the only honest validation
  from here is forward testing.
