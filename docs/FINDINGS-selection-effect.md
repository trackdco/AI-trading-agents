# FINDINGS — the selection effect, re-measured and downgraded

2026-08-10. `scripts/trader_selection_effect.py`,
`data/trader_fills/fxreplay_2026-01_full.csv` (both now committed —
previously this result had neither a script nor committed data).

## WHAT WAS CLAIMED

`ARCHITECTURE-trading-agent.md` opened with the justification for the whole
agent programme:

> **His picks are real.** Of the in-window 3m raw triggers he took, median
> run **5.48R** vs a same-day baseline of **1.15R**; P(2R) **71.4%** vs
> 38.5%. Binomial p = 0.013; permutation (20,000 draws of 14 from his own
> trading days) beaten by **0.17%** on median run and **0.55%** on P(2R).

## WHAT IT ACTUALLY IS

That reading contained two construction defects, both mine.

**1. The matcher had lookahead in it.** A fill was matched to the nearest
same-day same-direction trigger within ±5 minutes — *either side*. So a
candle that closed up to five minutes **after** he entered could be credited
as the trigger he selected. He cannot have selected a candle that had not
printed. Matching must be one-sided: the trigger closes at or before the
fill minute.

**2. The two halves of the headline came from different populations.** The
5.48R is the **all-hours** selected median; the 1.15R is the **in-window**
baseline. Neither pairing gives 5.48 vs 1.15 — all-hours is 5.48 vs 0.92,
in-window is 3.64 vs 1.15.

The in-window/all-hours distinction is not cosmetic. His session windows
(LONDON 03:00–04:59, NY_PRE 08:00–09:29, NY_AM 09:30–10:30) are already a
**hard mechanical constraint** in the design. Triggers inside them run
further than the all-day average as a matter of course — in-window baseline
1.20R vs all-hours 0.92R, P(2R) 36.3% vs 32.8%. An all-hours baseline
therefore credits *judgment* for a rule the machine enforces for free. The
comparison that isolates judgment is: same day, same window, which trigger.

## THE CORRECTED MEASUREMENT

His January export: 58 rows → 14 break-even dropped (*"I didn't actually
take those"*) → 2 duplicate misclicks collapsed → **42 real decisions over
14 days (3.00/day), +26,218 USD, 67% win rate, avg win +1,336 / avg loss
−800.**

Primary spec: 2m+3m triggers (his declared grammar is a race across
timeframes — 3m-only discards the entries he took on the 2m closure),
de-duplicated to one row per day/direction/3-min bucket, causal match within
3 minutes, VWAP source=open. Coverage **22 of 42 fills (52%)**.

| baseline | his n | median run | baseline | P(2R) his | P(2R) base | perm p (median) | perm p (P2R) |
|---|---|---|---|---|---|---|---|
| **IN-WINDOW** | 20 | **2.02R** | 1.20R | **55.0%** | 36.3% | 0.083 / 0.061 | 0.072 / 0.048 |
| ALL HOURS | 22 | 2.07R | 0.92R | 59.1% | 32.8% | 0.044 / 0.032 | 0.013 / 0.008 |

*(two p-values per cell: day-matched permutation, which holds his per-day
trade count fixed and randomises only the within-day choice; then the pooled
permutation, which is looser and also credits him for trading more on the
better days. 20,000 draws, seed 20260810.)*

**So: the direction and the size hold. The significance does not.**

- P(2R) **55.0% vs 36.3% in-window — a +18.7pp lift**, stable across every
  tolerance tried (+15pp to +25pp).
- Permutation p sits at **0.05–0.17** depending on tolerance and null design.
  Not 0.0017. At n=20 against a 102-trigger pool this is **suggestive and
  underpowered**, not established.

## SENSITIVITY — the full grid, so the reader can see the fragility

3m-only, causal:

| tol | matched | in-window his / base median | in-window P(2R) | perm p (day-matched) |
|---|---|---|---|---|
| ±1–2 | 8 (19%) | 2.32R / 1.15R | 50.0% vs 48.1% | 0.264 |
| ±3–8 | 10 (24%) | 3.64R / 1.15R | 55.6% vs 48.1% | 0.114 |

2m+3m union, causal:

| tol | matched | in-window his / base median | in-window P(2R) | perm p (day-matched) |
|---|---|---|---|---|
| 0 | 13 (31%) | 2.03R / 1.26R | 61.5% vs 36.1% | 0.142 |
| ±1 | 18 (43%) | 2.00R / 1.26R | 52.9% vs 37.1% | 0.170 |
| ±3 | 22 (52%) | 2.02R / 1.20R | 55.0% vs 36.3% | 0.083 |

Reproducing the withdrawn figure exactly: `--tf=3 --tol=5 --twosided`
returns all-hours median **5.48R** and in-window baseline **1.15R** — the
two numbers that were quoted as a pair.

**The VWAP source correction (BR-106) is not what moved this.** Run with
`--vwap=hlc3` and the in-window numbers are identical to the last decimal;
all-hours moves by <0.05R. The defects were in the matcher and the pairing.

## WHAT THIS DOES AND DOES NOT MEAN

**It does not mean he has no edge.** He made +26,218 USD on 42 decisions at
a 67% win rate. That is the evidence he can trade, and it is untouched.

**It does not mean his selection is absent.** 48% of his fills match no
trigger at all, so this measures roughly half his decisions; and n=20 has
almost no power against a spread this wide. A +18.7pp P(2R) lift that
recurs at every tolerance is the shape of a real effect that the sample
cannot resolve.

**It does mean the specific claim is withdrawn.** "Beaten by 0.17% of
20,000 permutations" is not a thing this data supports, and it should not be
cited — in the architecture doc, the operating spec, or as the benchmark the
agent is scored against. `ARCHITECTURE-trading-agent.md` and
`AGENT-OPERATING-SPEC.md` are corrected accordingly.

**The argument for the agent survives without it**, on the other leg it
always had: mechanisation was searched exhaustively and came back a
calibrated null (BR-97…BR-105 — 111 univariate features, 8,721 combinations,
a full multivariate classifier at AUC 0.522 vs 0.501, seven direction
proxies, stop-width geometry, the trader's own five order-flow measures).
Nothing mechanical reproduces what he does, and he demonstrably makes money.
That was always the stronger half of the case. What is gone is the claim
that we had *positively measured* his selection beating the baseline.

## THE SCORING BENCHMARK, RESTATED

The agent is still scored on agreement **and** outcome. But the outcome bar
is no longer "reproduce 5.48R vs 1.15R". It is:

- **In-window P(2R) ≥ ~55%** against the same-day in-window baseline of
  ~36%, measured the same way (causal match, 2m+3m, day-matched
  permutation).
- With the honest note that **his own 20 matched picks clear that bar at
  p ≈ 0.07** — so an agent matching him exactly would also fail to reach
  significance on one month. Scoring needs more months, and the narrated
  Feb/Mar/Apr week plus a wider export is how that sample gets built.

## METHOD NOTE

The lookahead in the matcher survived because the result was the one we
wanted and nothing was re-derived after it landed. It was found only when
the result was rebuilt from committed data as a script — which is the
argument for doing that at the time, not weeks later.
