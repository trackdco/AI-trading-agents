# FINDINGS — the 2017–2019 holdout: **the grammar fails its own bar, and the tick screen says exactly why** (2026-09-03)

Protocol: `docs/PREREG-holdout-2017-2019.md`, committed `62e707b` before the
data existed; Amendment 1 (`cb973c3`) before decompression. Verdicts applied
mechanically by `scripts/score_holdout_2017_2019.py`; the printed verdict is
archived verbatim at `docs/holdout17_verdict.txt`. Scored window 2017-01-01 →
2019-12-31; 2016 Q4 warmup only.

## 0. The one-line result

**Tests A and B — the base grammar and the empire — FAIL on 2017–19.** Test C
(arming) passes mechanically but on a base too weak to mean much. And Gate 0,
measured before any trade result and predicted in P1, explains it: **NQ in
2017–19 did not have the room this grammar needs.**

| year | median active-session 1m candle | screening law |
|---|---:|---|
| 2017 | **4.0 ticks** | fails (≥20) |
| 2018 | 10.0 ticks | fails |
| 2019 | 9.0 ticks | fails |
| *2023–26, for scale* | *28 ticks* | *passes* |

## 1. Integrity gates — all passed before any result was read

| gate | measured |
|---|---|
| sha256 vs Databento manifest | match |
| price range (4,500–5,500 / 8,300–9,300) | 4,558.50 – 8,843.50 ✓ |
| session-days 2017+ (≥700) | 725 rail-pass / 863 total ✓ |
| join with the 2020–22 tape | 60 shared minutes, **0 differing bars** ✓ |
| rolls | 14, all Mar/Jun/Sep/Dec ✓ |
| EFP symbols | none ✓ |

## 2. The verdicts, as printed

**Test A — base grammar, value-area book, frozen constants: FAIL**

| year | n | WR | net EV | net R |
|---|---:|---:|---:|---:|
| 2017 | 153 | 58.2% | +0.0060 | +1 |
| 2018 | 751 | 64.3% | +0.0936 | +70 |
| 2019 | 481 | 61.8% | +0.0649 | +31 |
| pooled | **1,385** | 62.7% | **+0.0740** | +102 |

All years positive ✓ · WR ≥60% ✓ · **EV ≥+0.08: +0.0740, FAIL.** Missed by
0.006R. Note the trade count: 1,385 in three years, against 5,478 on 2020–22
and 7,307 on 2023–26. A 5pt floor on a 1-tick-median tape barely fires.

**Test B — the empire, flat: FAIL**

| book | n | WR | EV |
|---|---:|---:|---:|
| 8-level | 3,773 | 62.5% | +0.0765 |
| vwap-session | 5,473 | 60.2% | +0.0526 |
| vwap-ny | 4,303 | 61.9% | +0.0717 |
| railed | 12,785 | 61.6% | +0.0700 |

No book clears +0.08. 2017 net **−70R**, maxDD −88.5R against a worst day of
only −8.4R — a year-long grind, not a crash. 2018 +763R, 2019 +203R.

**Test C — arming, the primary verdict: PASS (mechanically)**

| half | flat R/day | armed R/day | dd-matched | lift |
|---|---:|---:|---:|---:|
| IS | +0.565 | +0.871 | +1.332 | +135.7% |
| OOS | +1.954 | +2.196 | +3.359 | +71.9% |

Raw EV +0.0700 → +0.1031 (+47.3%), maxDD −84.8 → −55.4. The bar was ≥+5% in
both halves; it clears it. **But read the denominator.** Flat R/day in the
first half is +0.565 — a twentieth of 2023–26's. A percentage lift on that
base is not comparable to +16–18% on +10.8/day, and P3 (lift inside +10% to
+40%) is **WRONG** for exactly that reason. What survives honestly: arming's
*direction* replicates for a third era — better per trade, shallower
drawdown — on a tape where the grammar itself is marginal.

**Test D — conviction sizing: PASS**, +54.7% / +23.2%, same caveat.

**Test E — autopsy claims:** E1 **FAIL** (prior-vol Q4 vs Q1: trades/day
+94%, but |ΔEV| 0.043 ≥ 0.02 — on this tape volatility *is* quality, which
is what the screen predicts: only the wild days reach the floor). E2 **PASS**
(worst-1% days' prior vol 1.23 vs 1.15 — still unmarked in advance).

**Predictions:** P1 CORRECT (all three years <20 ticks; 2017 weakest) ·
P2 CORRECT (frozen +0.074 beats era-scaled **−0.161** — a 1.25pt floor is eaten
whole by the one-tick fill plus 0.5pt cost, the 6E mechanism on NQ) ·
P3 WRONG · P4 CORRECT (losses chain) · P5 CORRECT (1R best at every depth,
fourth instrument-era running) · P6 WRONG (8-level > ny > session here).

## 3. Post-hoc, exploratory, NOT a verdict: the edge tracks the tick count

The tick screen was declared as a measurement, not a gate, so Tests A/B ran
on the whole period and failed. That stands. What follows is a look taken
*after* the verdicts, and it is the reason the failure is informative rather
than alarming. Value-area book, frozen constants, every month of all seven
years, bucketed by that month's own median active-session candle:

| ticks / candle | months | trades | EV/trade | months EV>0 | eras |
|---|---:|---:|---:|---:|---|
| 0–8 | 20 | 410 | **+0.012** | 45% | 2017–19 |
| 8–12 | 9 | 365 | +0.112 | 56% | 2017–19, 2020–22 |
| 12–16 | 10 | 886 | +0.091 | 80% | 2017–19, 2020–22 |
| 16–20 | 12 | 1,370 | +0.175 | **100%** | all three |
| 20–28 | 35 | 5,119 | +0.141 | 100% | 2020–22, 2023–26 |
| 28–40 | 18 | 3,523 | +0.153 | 100% | 2020–22, 2023–26 |
| 40+ | 13 | 2,497 | +0.143 | 100% | 2020–22, 2023–26 |

Under 8 ticks the grammar is a coin flip. From 16 ticks up it has never had
a losing month, in any era. The transition is 8–16. Inside 2017–19 itself:
2017 (3–5 ticks) is dead; **Q4 2018 (15–18 ticks) prints +0.18 / +0.25 /
+0.23** — as good as any quarter on the modern tape.

This is the fourth confirmation of the screening law and the first on NQ's
own history: ES (6–7 ticks) flat, 6E (3) dead, NQ 2017 (4) dead, NQ 2020+
(≥20) works. **The edge is a property of the tape's granularity, not of
the year or the instrument.**

## 4. What this means

1. **The grammar is not regime-free.** It needs roughly ≥16 ticks of median
   1-minute movement. NQ has had that since 2020 and has it now (28). If NQ
   volatility ever collapses to 2017 levels, expect the edge to go to zero —
   not negative, zero, with 1,385 trades a year instead of 20,000.
2. **A standing regime check belongs in the executor.** Trailing 20-day median
   active-session candle in ticks. This is day-level, causal, and — per the
   autopsy's structural argument — a bucket that *is* the rule effect. Its
   threshold should be pre-registered on forward data, not fitted here; the
   table above says the number is somewhere in 12–16.
3. **The frozen constants are right to stay frozen.** Scaling them down to
   the era (Run B) made it *worse*, −0.161 — the fill tax and cost do not
   scale with the floor. That is the same lesson as 6E and GC's 2023–24.
4. **Arming has now improved per-trade EV and cut drawdown in three separate
   eras**, including one where the base grammar fails. The magnitude on
   2017–19 is not meaningful; the direction is.
5. **2017–19 is spent**, and there is no earlier 1-minute NQ this program has
   budget for. Validation from here is forward time.

Scripts: `scripts/run_holdout_2017_2019.sh`, `scripts/score_holdout_2017_2019.py`,
`scripts/build_nq_2017_2019.py`. Data: `data/reference/nq_2017_2019_*`.
Verdict: `docs/holdout17_verdict.txt`. Constants: `docs/holdout17_constants.json`.
