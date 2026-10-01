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

## 6. NQ + gold combined, both armed, gold on its dial (his "what makes gold better")

Daily series added, 2023-01 → 2026-09; gold contributes 0 on dial-off days.

| | net R | R/day | maxDD | Sharpe | green | worst day |
|---|---:|---:|---:|---:|---:|---:|
| NQ alone | +10,863 | +11.45 | −14.0 | 1.206 | 91% | −14.0 |
| GC alone (0 on off-days) | +1,944 | +2.05 | −17.8 | 0.376 | 26% | −11.7 |
| **NQ + GC, full size each** | **+12,806** | **+13.49** | **−14.0** | 1.177 | 92% | −14.0 |
| NQ + GC at half size | +11,835 | +12.47 | −14.0 | **1.227** | 91% | −14.0 |
| half NQ + half GC | +6,403 | +6.75 | −7.0 | 1.177 | 92% | −7.0 |

- Correlation on the 299 days both traded: **+0.014**. On those days NQ is red
  6%, gold is red 19%, **both red 1%**.
- Gold adds +1,944R (+18%) at **zero added drawdown** — the empire's max
  drawdown is −14.0 with or without it. That is what zero correlation buys.
- On NQ's 20 worst days gold averaged **+4.4R** (on for 35% of them).
- **2026, gold fully on:** NQ +2,557 / GC +1,153; combined maxDD **−3.2 vs
  NQ alone −10.7**; Sharpe 1.66 vs 1.42.

What gold is *not*: better per trade, per day, or on drawdown alone. What it
*is*: a second, independent source of R that shows up when its own tape is
loud, and does not deepen the hole when NQ's is. In the one year both were
fully on, it cut the combined drawdown by two-thirds.

## 7. Do NQ and gold hold positions at the same time? (his ask)

Minute-resolved, NQ armed empire vs gold armed + dial, on the 299 days both traded.

| | share of minutes with anything open |
|---|---:|
| NQ only | 48.6% |
| gold only | 45.6% |
| **both at once** | **5.7%** |

- 13% of gold fills happen while NQ already holds a position.
- Of the both-open minutes, 60% are same-direction. That is not a doubled bet
  the way two NQ books are — different market, +0.014 correlation — so G3
  (first-in-wins) does not apply across instruments.
- Simultaneous open positions across both: 1 open 91% of in-market minutes,
  2 open 8.5%, 3 open 0.7%, 4+ open 0.1%. Max ever 6.
- Per-day peak: 2 on 27% of days, 3 on 62%, 4 on 10%, 5–6 on 1%.
- Overlap clusters in the NY morning: 09:00–12:00 ET carry 42% of the
  both-open minutes.

**Executor consequence:** the combined book needs a global open-risk cap
across instruments — G7's "open risk ≤ 4R" extended to the sum — and on
~11% of days it would bind at 4. Per-instrument G5/G6 stay as they are.

## 8. One position at a time, across everything (his rule: "no trades can ever overlap")

A global first-in-wins: a trade is kept only if nothing is open at its fill
minute — any book, any instrument. Post-hoc chronological rail, same standing
caveat as G3. Armed books, 2023–26, gold on its dial.

| | trades | /day | net R | R/day | maxDD | Sharpe | green |
|---|---:|---:|---:|---:|---:|---:|---:|
| NQ as it ships (up to 4 open) | 61,194 | 64.6 | +10,863 | +11.46 | −14.0 | 1.208 | 91% |
| NQ, one at a time | 59,352 | 62.6 | +10,382 | +10.95 | −14.0 | 1.179 | 90% |
| NQ + gold, as they ship (can overlap) | 79,436 | 83.8 | +12,807 | +13.51 | −14.0 | 1.179 | 92% |
| **NQ + gold, one at a time across all** | 74,911 | 79.0 | **+11,913** | **+12.57** | **−14.0** | 1.165 | 91% |

- The strict combined book drops 5,952 trades (7.5%) and 894R (7.0%). Max
  drawdown is **unchanged** at −14.0, so drawdown-matched it is a straight
  −7.0%.
- NQ alone, one at a time, costs 4.4%. Gold alone, 3.8%.
- The strict combined book (+11,913 / +12.57 per day) still beats NQ as it
  ships (+10,863 / +11.46) by **+9.7% R at the same drawdown**. Gold's seat
  survives the constraint.
- Slot split: NQ 57,858 trades, gold 17,053.

Net: the rule costs about 7% of the combined R and nothing on drawdown. It
also removes the need for the cross-instrument G7 extension in §7 — with one
position ever open, open risk is 1R by construction.
