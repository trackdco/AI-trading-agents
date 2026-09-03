# FINDINGS — Arm-after-displacement, and conditional targets (2026-09-03)

Two tests, both in-engine, both on the certified spec.

1. **Arm-after-displacement: ADOPT.** Holding the limit dark until price
   has run 1R past the level takes 19% fewer trades, raises expectancy
   per trade by 30%, and cuts max drawdown by 23%.
2. **Conditional targets by displacement: KILLED.** Kill #6. A higher
   target does not beat 1R in a single displacement bucket in both
   halves — not even on the trades that already ran 3R past the level.

Receipts: `--arm-after` and `--targets` on `scripts/pd_va_backtest.py`
and `scripts/vwap_revolve.py` (patch in `docs/patches/`),
`scripts/conviction_sizing.py --arm`.

## 1. The rule

The frozen spec rests a limit at the level the moment the signal candle
closes; it is live immediately and fills on the first touch. Arming adds
a wake-up condition: the order cannot fill until price has traded
`arm × risk` **beyond** the level. Only then does the retest count.

Conservative on intrabar order: the arming bar must be **strictly
before** the touch bar, because inside a single bar it is unknowable
whether the run past the level came before or after the pullback to it.
The signal candle's own last bar counts toward arming — its high and low
are known at the signal close, so that is legal information.

Unlike conviction sizing, this **changes the trade set**: a pending that
never displaces expires unfilled and frees the book for the next signal,
and one that displaces late fills later than it otherwise would. It is a
genuine engine run, not arithmetic on a tagged dump.

**Patch receipt:** re-run with `--arm-after` absent, diffed against the
pre-patch dump — **22,187 trades, 0 differing.** The frozen spec is
untouched; the flag is off by default.

## 2. Result — the railed empire

| arm at | trades | /day | EV/trade | total R | maxDD | Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| none (frozen spec) | 71,961 | 78.1 | +0.1375 | +9,896 | −18.1 | 1.158 |
| **1.0R** | 58,401 | 63.4 | **+0.1792** | **+10,467** | **−14.0** | 1.207 |
| 1.5R | 44,956 | 48.8 | +0.2027 | +9,112 | −11.9 | 1.217 |

All rows at the same average position size. Expectancy per trade rises
**+30%** at 1.0R and holds in both halves (IS +0.1484 → +0.1886, OOS
+0.1297 → +0.1725). Max drawdown falls 23%. Days worse than −5R: 26 →
19; worse than −10R: 7 → 5.

Drawdown-matched (the pre-registered frame): **+36.1%** R/day, IS +33.3%
/ OOS +38.5%, against a +5% bar. Volatility-matched — the conservative
floor — **+4.2%**. Every year +34% to +38%.

**A correction worth recording.** The level book alone shows a spike:
drawdown-matched +1.7% / **+37.2%** / +1.8% / +1.1% at arm 0.5 / 1.0 /
1.5 / 2.0. That looked like a fitted knob, and it was reported as one
before the empire ridge was run. It is not: one book's max drawdown is a
single worst day that jumps between episodes (2023-10-02 at 1.0R,
2026-05-28 at 1.5R). Across three books the statistic settles and the
ridge is **monotone** — +0.0% / +36.1% / +40.2%, with EV/trade rising
0.1375 → 0.1792 → 0.2027 the whole way. Total R peaks at 1.0R, so the
knob is a volume-versus-smoothness preference, not a fitted spike.
Single-book drawdown is too noisy to sweep a parameter on; the empire is
the unit of test.

## 3. Arming and conviction sizing are substitutes, not a stack

The armed book contains **only tiers A and B**, by construction: arming
at 1R *is* the ≥1R displacement test. So the adopted 2:1 sizing rule is
a literal no-op on it (measured: +0.0%), and no other sizing scheme adds
anything (A full / B three-quarter: −0.2%; A full / B half: −0.3%).

Pick one:

| | trades | total R | maxDD | Sharpe | live requirement |
|---|---:|---:|---:|---:|---|
| conviction 2:1 | 71,961 | +11,370 | −17.7 | 1.197 | amend a resting order's size mid-flight |
| armed 1R | 58,401 | +10,467 | −14.0 | 1.207 | place the order later — no order-modify path |

Sizing keeps more R; arming cuts more drawdown, trades 19% less often,
and is the easier of the two to wire, since it needs no order
modification — the limit simply is not placed until the run happens.

## 4. Conditional targets by displacement: KILLED

Pre-registered before the sweep: a conditional target is worth building
only if a higher target beats 1.0R **in both halves** in some
displacement bucket. Level book, targets 1.0 / 1.5 / 2.0, net of cost.

Armed book, EV difference vs the 1.0R target in the same bucket:

| displacement | target | IS vs 1R | OOS vs 1R | both halves? |
|---|---:|---:|---:|---|
| 1–2R | 1.5 | −0.1272 | −0.1214 | no |
| 1–2R | 2.0 | −0.1742 | −0.1915 | no |
| 2–3R | 1.5 | −0.0472 | −0.0463 | no |
| 2–3R | 2.0 | −0.1287 | −0.1775 | no |
| 3R+ | 1.5 | −0.0233 | **+0.0189** | no (sign flips) |
| 3R+ | 2.0 | −0.1252 | −0.0086 | no |

**Zero cells survive.** The only bucket that even flirts with it is 3R+
at 1.5R, and it flips sign between halves — 1.0R wins in-sample by
0.023R, 1.5R wins out-of-sample by 0.019R, and the two average to a
+0.0025R difference over 6,700 trades. That is noise, and by the rule
used since round 1 it is NULL.

The post-hoc best case, with the winning target picked per bucket *after*
seeing the answer, still loses:

| rule (armed book) | trades | net R | R/day | maxDD |
|---|---:|---:|---:|---:|
| plain 1R | 18,582 | +3,327 | +3.81 | −12.1 |
| 1.5R when displacement ≥3R | 18,328 | +3,295 | +3.77 | −16.0 |
| 1.5R when displacement ≥2R | 18,192 | +3,100 | +3.55 | −18.0 |

Less R **and** a third more drawdown, from the cherry-picked version.

**Mechanism, and why it was worth asking.** Displacement predicts
whether the trade *works*, not how far it *runs*. The hypothesis was
that ground already covered makes a further target cheap; the measurement
says the opposite — a trade that has already run 3R past the level is
more likely to reach 1R, and no more likely to reach 1.5R than any other
trade. This is the third independent confirmation that the 1R full exit
is right: runners died (S16), fixed higher targets died after honest
fills and costs (S2), and now conditional targets die too.

An honest note on process: the screen script's own verdict line printed
"BUILD", because it checked whether the best-EV target was non-decreasing
*across buckets* rather than whether a higher target won *within* a
bucket in both halves. The second is the standard this program has used
since round 1. Applied correctly, nothing survives. The buggy check is
recorded here rather than quietly fixed.

## 5. Caveats

- The arming threshold was not swept to find a maximum; 1.0R is the
  audit's own bucket edge, fixed before results were read, and 0.5 /
  1.5 / 2.0 were run to show the shape, not to select.
- Same sample that produced the displacement hypothesis. Both halves and
  all four years hold, and OOS is not degraded, but there is no untouched
  holdout — expect winner's-curse shaving.
- Arming reduces frequency 78 → 63 trades/day. That is still
  automation-only, but it changes the funded-account arithmetic; the S33
  Monte Carlo artifact needs re-running before it describes an armed book.
- Standing caveats unchanged: no queue or latency model, post-hoc
  chronological rail pass, computed rather than chart-read levels.
