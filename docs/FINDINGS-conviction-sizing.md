# FINDINGS — Conviction sizing, in-engine (2026-09-03)

His ask, after the conviction audit: "test the conviction sizing
in-engine."

**Verdict: ADOPT (first survivor after five consecutive kills).** At an
identical average position size, moving size from low-conviction to
high-conviction trades earns **+14.9% more R per day with a slightly
smaller max drawdown**. The simplest form is one rule with two sizes.

Receipts: `scripts/conviction_sizing.py` (report),
`--conviction` flag on `scripts/pd_va_backtest.py` and
`scripts/vwap_revolve.py` (tier tagging inside the sim).

## 0. Rule, written before any result was read

ADOPT if, after scaling the tiered book so its max drawdown equals the
flat book's, R/day improves by ≥5% in BOTH halves (IS < 2024-10-21 ≤
OOS). WATCH if it improves in both by less. KILL otherwise — including
any scheme that makes more R only by taking more risk.

Drawdown-matched is the bar because the sizing dial (S32) already sells
R/day for drawdown at any multiple; a conviction layer has to beat that
trade, not re-sell it. Six schemes fixed in the script, not tuned.
`sess` (size on session progress alone) is the negative control.

## 1. What "in-engine" means here, and what it does not

Sizing **cannot** change which trades are taken, when they fill, or when
they exit. A half-size position occupies the book exactly like a full
one, and every rail (G1 one-per-book, G3 first-in-wins, G5/G6 caps) keys
on position existence and direction, never on size. So the trade set is
identical **by construction**, and the only in-engine question is
whether the tier is computed correctly, from exact bars, with no
lookahead. That is what `--conviction` does: the tier is written at fill
time inside `simulate_day`/`simulate`, from the running session extremes
and the pre-fill excursion window, fill bar excluded. Applying a
multiplier afterwards is exact arithmetic, not an estimate.

**The patch changes nothing else, and this is receipted.** The level
book was re-run with `--conviction` and diffed against the pre-patch
dump: **22,187 trades, 0 differing on any pre-existing field.** The flag
adds three keys (`excur_r`, `sess_pct`, `tier`) and touches nothing.
Default off; the frozen spec runs exactly as before.

Rail-pass reproduction check: three books → **71,961 trades over 921
days, +9,896R, +10.74R/day, maxDD −18.1R** — S34's capped empire to the
trade. G5 and G6 bound 0 times, as in the receipts. G7 (open risk ≤4R)
binds strictly less under tiered sizing, since every non-A trade carries
less risk; measured peak open risk 4.00R flat, p99.8 3.00R.

## 2. Tier census on the railed empire

| tier | n | share | WR | net EV | IS | OOS | net R |
|---|---|---|---|---|---|---|---|
| A ran ≥1R past the level AND day moved ≥0.5× | 29,524 | 41.0% | 67.4% | **+0.2142** | +0.2323 | +0.2004 | +6,323 |
| B displaced only | 20,640 | 28.7% | 64.9% | +0.1491 | +0.1484 | +0.1495 | +3,077 |
| C moved-day only | 13,140 | 18.3% | 64.3% | +0.0441 | +0.0614 | +0.0310 | +580 |
| D neither | 8,657 | 12.0% | 60.4% | **−0.0097** | −0.0182 | −0.0041 | −84 |

Monotone in both halves. A+B is 70% of the trades and 95% of the R.

## 3. The result, with no normalisation games

All rows below deploy the **same average position size** as the frozen
spec — same average contracts, size merely redistributed:

| scheme | total R | R/day | maxDD | green | Sharpe | worst day | months + | worst mo | median mo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **flat (frozen spec)** | +9,896 | +10.74 | −18.1 | 89% | 1.158 | −18.1 | 45/45 | +8.1 | +210.3 |
| **2:1 on displacement** | **+11,370** | **+12.35** | **−17.7** | 90% | 1.197 | −17.7 | 45/45 | +10.5 | +258.3 |
| gentle (4 sizes, both features) | +11,429 | +12.41 | −18.1 | 90% | 1.209 | −18.1 | 45/45 | +8.4 | +257.4 |
| 3:2:1 on displacement | +11,361 | +12.34 | −19.3 | 90% | 1.201 | −19.3 | 45/45 | +10.7 | +256.3 |

**+1,474R over four years for the same average risk, and the worst day
gets smaller, not bigger.** Still 45/45 months positive; the worst month
improves from +8.1R to +10.5R.

Drawdown-matched (the pre-registered frame), split-half:

| scheme | scale | R/day | vs flat | IS | OOS | Sharpe | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| flat | 1.00 | 10.744 | — | — | — | 1.158 | — |
| audit (1/.5/.5/.25) | 1.34 | 11.825 | +10.1% | +12.0% | +8.5% | 1.188 | ADOPT |
| gentle (1/.75/.5/.5) | 1.28 | 12.386 | +15.3% | +15.7% | +15.0% | 1.209 | ADOPT |
| **excur (1/1/.5/.5)** | 1.20 | 12.587 | **+17.2%** | +16.3% | +17.8% | 1.197 | **ADOPT** |
| sess — negative control | 1.07 | 9.739 | −9.4% | −6.9% | −11.3% | 1.146 | **KILL** |

Per year, drawdown-matched R/day vs flat: excur **+16 / +17 / +18 / +17%**
(2023–26); gentle +17 / +15 / +16 / +14%. Every year, both halves.

**The negative control failed, which is the point.** Sizing on session
progress alone is *worse* than flat (−9.4%). It is not "any tiering
helps" — it is displacement specifically.

## 4. How big is the effect, honestly

The improvement is real under every risk normalisation, but its size
depends on which one:

| risk normalisation | audit | gentle | excur |
|---|---:|---:|---:|
| maxDD (1 observation) | +10.1% | +15.3% | +17.1% |
| mean of 5 worst days | +7.7% | +9.5% | +11.0% |
| mean of 20 worst days | +10.2% | +13.9% | +13.8% |
| 5th-percentile day | +33.2% | +26.8% | +5.5% |
| **daily stdev (the conservative floor)** | **+2.5%** | **+4.4%** | **+3.4%** |
| downside stdev | +4.0% | +8.8% | +13.1% |

Read it this way: **+3–4% is the floor** (pure Sharpe: 1.158 → 1.197 for
excur, 1.209 for gentle), **+15% is the prop-relevant number**, because
tiered sizing shrinks the bad tail more than it shrinks the mean — it
downsizes exactly the trades that cluster into bad days — and a funded
account's binding constraint is literally a trailing drawdown, not a
variance.

Block bootstrap, 5-day blocks, 2,000 draws, drawdown-matched:

| scheme | median | 5th pct | 95th pct | P(>0) | P(≥+5%) |
|---|---:|---:|---:|---:|---:|
| audit | +11.1% | +3.3% | +32.9% | 97.4% | 93.0% |
| gentle | +15.2% | +8.3% | +30.4% | 99.1% | 97.4% |
| excur | +17.0% | +8.3% | +31.0% | 98.9% | 97.4% |
| sess | −8.4% | −11.2% | +11.6% | 25.4% | 13.5% |

## 5. The rule to adopt

**Full size when price ran ≥1R past the level before the retest; half
size when it did not.** One feature, two sizes, ~70% of trades take the
bigger size. `gentle` (four sizes off both features) is statistically
indistinguishable (+15.3% vs +17.2%, well inside the bootstrap spread)
and carries more knobs, so the two-size rule is preferred on parsimony.

**Executor requirement — this is not free plumbing.** Displacement is
known at fill time, not signal time, so the live form is: rest the limit
at the base size, and **increase the working order's size once price has
traded ≥1R past the level**. Equivalently, work it as two clips and add
the second only after the displacement prints. If the executor cannot
amend a resting order's quantity, this rule cannot be implemented as
measured, and the fallback (size at signal time on session progress
alone) is the scheme that FAILED. Confirm the Rithmic/Sierra order-modify
path before counting on it.

## 6. What was NOT tested here

`steep*` (A 1.0 / B 0.5 / C 0.25 / **D 0.0**) showed +22% drawdown-matched
but is **excluded from the verdict**: a zero multiplier is a skip, not a
size, and a skipped trade frees the book for a later signal — S34
measured +41R from exactly that effect on the stop cap. Its honest
version is the audit's recommendation 3 (arm-after-displacement: pull
the resting limit rather than never place it), which changes occupancy
and needs its own engine run.

## 7. Caveats

- **Same sample that produced the hypothesis.** The two features were
  selected from these four years. The bucket edges (1R, 0.5×) were fixed
  before results were read, and the effect holds in both halves and all
  four years — but there is no untouched holdout, so expect
  winner's-curse shaving on the effect size. The OOS half is not
  degraded (+17.8% vs +16.3% IS), which is the reassuring shape.
- **maxDD is one observation** out of 921 days. Hence §4's six metrics
  and the bootstrap rather than a single headline.
- **The funded-account artifact is now stale for this variant**: at the
  drawdown-matched scale the big tier carries ~1.2× the flat per-trade
  risk, so the $/micro tables in S33 need re-running before they describe
  a tiered book.
- Everything else in the standing caveat stack is unchanged: no queue or
  latency model, post-hoc chronological rail pass, ~80 trades/day is
  automation-only.

## 8. Where the code lives

The engines (`scripts/pd_va_backtest.py`, `scripts/vwap_revolve.py`) live
on branch `claude/tradingview-mcp-agent-setup-ql18v8`, not on this one.
The `--conviction` tagging change is committed here as a reviewable
patch — `docs/patches/conviction-tagging.patch` — to be applied on that
branch:

    git checkout claude/tradingview-mcp-agent-setup-ql18v8
    git apply docs/patches/conviction-tagging.patch

It is additive and gated behind an off-by-default flag; with the flag
absent the engines are byte-identical in behaviour (§1's 0-diff receipt).

Reproduce end to end:

    python -m scripts.pd_va_backtest --levels all --tf 1 --sar \
        --fill-through --news-gate --max-risk 30 --conviction
    python -m scripts.vwap_revolve --tf 1 --style retest \
        --max-risk 30 --dedupe --conviction
    python -m scripts.vwap_revolve --tf 1 --style retest --anchor ny \
        --max-risk 30 --dedupe --conviction
    python -m scripts.conviction_sizing
