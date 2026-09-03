# FINDINGS — the full empire on gold (2026-09-03)

First time GC has seen the two VWAP books, the three-book rail pass, and
arming. Gold constants at the certification ratios (floor 1.5 / depth 0.9 /
bin 0.3 / cap 9.0), cost 0.15pt/RT, news gate on, 2023-01 → 2026-09.
**In-sample, not sealed**: the VA book and the vol dial (S22, S24) were derived
on this tape; the VWAP books and arming are first-look but the same tape.

## 0. The tick screen decides gold, exactly as it decided NQ 2017–19

| year | median 1m candle | vs 20-tick law | vol dial on |
|---|---:|---|---:|
| 2023 | 5.0 ticks | dead zone | 0% of days |
| 2024 | 7.0 ticks | dead zone | 0% |
| 2025 | 11.0 ticks | flicker | 52% |
| 2026 | 20.5 ticks | **on** | 100% |

Gold 2023–24 is NQ 2017–19: a tape that cannot reach a 1.5pt floor. The S24
dial (trade only when the trailing-20-day median 1m candle ≥ 1.0pt) is the
same regime gate the NQ holdout produced, derived independently a day earlier
on gold's own numbers. Two instruments, one law.

## 1. Per book — no book clears the seat bar over the whole tape

| book | n | WR | EV | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 8-level | 10,273 | 62.3% | +0.062 | +0.019 | −0.017 | **+0.082** | +0.075 |
| vwap-session | 14,969 | 60.9% | +0.050 | −0.039 | −0.013 | +0.079 | +0.053 |
| vwap-ny | 7,679 | 61.1% | +0.056 | −0.042 | +0.028 | +0.080 | +0.064 |

Pooled EV is +0.05–0.06 because 2023–24 drags. In 2025–26 all three books
run +0.05–0.08 — roughly half NQ's per-trade edge, the same ratio S22 found.

## 2. The empire

| | days | trades | /day | WR | EV | net R | R/day | maxDD | Sharpe | green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat, undialed | 918 | 31,621 | 34.4 | 61.3% | +0.055 | +1,742 | +1.90 | **−84.1** | 0.30 | 57% |
| flat + dial | 300 | 22,413 | 74.7 | 62.8% | +0.074 | +1,656 | +5.52 | −20.0 | 0.65 | 73% |
| armed, undialed | 914 | 26,081 | 28.5 | 61.7% | +0.083 | +2,153 | +2.36 | −63.1 | 0.38 | 60% |
| **armed + dial** | 300 | 18,242 | 60.8 | 63.1% | **+0.107** | +1,944 | **+6.48** | **−17.8** | **0.80** | **81%** |

By year, net R — flat: 2023 −29 / 2024 −12 / 2025 +882 / 2026 +901.
Armed: −10 / +23 / +987 / +1,153.

The dial keeps **95% of the R on 33% of the days** and cuts the drawdown from
−84 to −20. Undialed gold is untradeable on risk; dialed gold is a real second
stream.

## 3. Arming on gold — the same rule as NQ

| | IS lift | OOS lift | raw EV | maxDD | verdict |
|---|---:|---:|---|---|---|
| undialed | −147% | +49.0% | +0.055 → +0.083 | −78.6 → −63.1 | FAIL |
| **dialed** | **+23.1%** | **+42.9%** | +0.074 → +0.107 (+44%) | −20.0 → −17.8 | **PASS** |

The undialed FAIL is arithmetic, not evidence: the IS half is 2023–24 where
flat gold is *negative*, so the ratio is meaningless. On the days gold is
tradeable, arming lifts it +23% / +43% drawdown-matched — inside the +10–40%
band NQ showed, at the top of it. **Arming has now replicated on a third
tape.** Caveat: the dialed sample is 300 days and the IS half is small.

## 4. Gold vs NQ, armed, on their own tradeable days

| | R/day | maxDD | Sharpe | green | days on |
|---|---:|---:|---:|---:|---:|
| NQ armed 2023–26 | +11.46 | −14.0 | 1.21 | 91% | 100% |
| GC armed + dial | +6.48 | −17.8 | 0.80 | 81% | 33% |

Gold is half of NQ per day, at worse risk, one day in three. The same read as
S22: additive as a second stream, the lesser tape alone. S24 measured the two
books' daily correlation at −0.018 — the diversification is real. **A combined
NQ + dialed-GC armed book is the natural next number and has not been run.**

## 5. Engine fix found on the way

`vwap_revolve.py` hard-coded `DEPTHS = (0.0, 3.0)` — NQ's certified depth,
2× gold's stop floor. Now derived from the instrument table; NQ output
byte-identical, gold gets (0.0, 0.9). Caught before the gold VWAP jobs ran.

Scripts: `scripts/run_gold_empire.sh`, `scripts/gold_empire.py`.
