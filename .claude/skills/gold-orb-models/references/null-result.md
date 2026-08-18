# NULL RESULT — the 15-minute ORB family on GC is retired (19 Aug 2026)

**Read this before proposing, coding, or backtesting any opening-range breakout on gold.**
It is written to stand alone: no chat context is needed, and nothing below depends on a
conversation you cannot see.

**Verdict: the plain opening-range-breakout entry family on GC/MGC is retired.** Four
independent falsifications, listed with their provenance because two different kinds of
evidence are mixed here and a future reader must not treat them as equally verified.

---

## Provenance — which numbers were measured in this repo and which were supplied

| evidence | source | verified here? |
|---|---|---|
| (1) 26.5-year TradingView backtest | supplied by the user from a TV strategy-tester run | **no — never reproduced in this repo** |
| (2) engine measurement on train 2023-01 → 2025-08 | `src/research/orb/engine.py` | **yes** |
| (3) the four entry-axis sweeps | `scripts/orb_sweep2.py` | **yes** |
| (4) design-window decomposition | `scripts/orb_parity_v31.py` + engine | **yes** |
| risk-architecture stats (26 yr, worst trade −$5.3k, one gap-through) | supplied, same TV run as (1) | **no** |

Items (1) and the risk-architecture line are recorded because they are consistent with, and
far larger than, what was measured here. They are *not* independent confirmation produced by
this codebase. If they ever need to carry weight, reproduce them.

---

## The four falsifications

**(1) Long-history TradingView run — supplied.** 26.5 years, 4,531 trades, **PF 0.97**,
−$27k; **−$47k once the 2026 window is excluded**, that window being the one the v3
mechanism set was designed on. The exclusion making the result *worse* is the point: the
only stretch carrying the strategy is the stretch it was fitted to.

**(2) Engine measurement on train — measured here.** GC 1m, 2023-01-02 → 2025-08-31, the
exact v3.1 exported configuration: n=473, 47.6% win, **PF 0.947**, **EV −0.0118R**
[−0.082, +0.057], and **−$17,906 at 2 ticks/side** (PF 0.878, EV −0.0358R). The ratchet and
the 30-point risk cap are bit-identical to switching them off, because on train they never
fire.

**(3) Four single-axis entry sweeps — measured here.** Detailed below. No cell reached the
+0.10R gate.

**(4) Design-window decomposition — measured here.** The same configurations, two eras:

| | 2026 window | | train 2023–25 | |
|---|---|---|---|---|
| | PF | net | PF | net |
| v3.1 full stack | **1.62** | +$27,711 | **0.95** | **−$7,579** |
| bare ORB 1.0R, everything off | 1.13 | **+$12,404** | 0.97 | **−$6,628** |

Roughly half the 2026 profit is the regime — the *bare* strategy already makes +$12,404
there while losing $6,628 on train. The other half is the mechanism stack, which lifts PF
by **+0.49 in 2026 and −0.02 on train**: on the window it was designed for it is the
difference between marginal and good, and everywhere else it is **actively harmful**. This is in-sample by construction, and the
design document says so itself — the 30-pt cap exists because of one trade in that window,
the ratchet because of the "giveback seven" in that window, the time-stop because of the
flats in that window, skipMon because of Monday in that window.

---

## The sweeps, with the reasoning that settled each

Train 2023-01-02 → 2025-08-31, 656 baseline trades. Bare ORB (1.5R, no cap, no gates, no
management) re-run as the control inside every axis. Costs are per side **plus $3
round-turn commission**. Entry window held at 150 minutes after each anchor so the anchor
comparison is fair.

### ANCHOR — the gold-native-anchor thesis is dead

| anchor | avg R @1t | @2t | note |
|---|---|---|---|
| **09:30 ET** | **+0.023** | −0.013 | best in R |
| 08:20 ET (COMEX pit) | +0.008 | −0.019 | entirely 2025: −0.025 / −0.036 / **+0.123** |
| 03:00 ET (London) | −0.055 | **−0.094** | 2-tick CI **[−0.172, −0.012]** |

The thesis was that 09:30 is an equity convention gold has no native reason to respect, and
that 08:20 (deepest US metals liquidity) or 03:00 (London) should beat it. **The opposite
holds.** 09:30 is the best of the three in R. 08:20 wins dollars and profit factor while
losing R — the dual-currency split — and is a single-year artifact. **London is refuted**,
not merely weak: its 2-tick interval is clear of zero on the wrong side, one of only two
intervals in the entire programme to clear zero at all.

Do not re-propose an anchor sweep. It was the highest-prior variable in the original skill
and it is settled.

### CRABEL CONTRACTION — rejected, and rejected by its own dose-response

| prior day | n | avg R @1t | CI | PF |
|---|---|---|---|---|
| no gate | 656 | +0.023 | [−0.049, +0.096] | 1.046 |
| NR4 | 156 | +0.004 | [−0.148, +0.153] | 1.018 |
| **NR7** | 74 | **+0.116** | [−0.092, +0.334] | 1.324 |
| inside | 114 | −0.055 | [−0.214, +0.103] | 0.993 |
| **ID/NR4** | 76 | **−0.137** | [−0.326, +0.058] | **0.765** |

NR7 is **the only cell above +0.10R anywhere in the entire programme**, and it is rejected:
n=74, an interval 0.43R wide straddling zero, 2023 negative, and its three neighbours sit
at +0.004, −0.055 and −0.137. One spike among four variants of a single idea.

**The decisive argument is the dose-response, not the interval.** ID/NR4 is the *strictest*
form of contraction — an inside day that is also the narrowest of four — and it is **the
worst cell in the study**. A real precondition strengthens as you tighten it. This one
inverts. Crabel's volatility-contraction filter, the original ORB condition, does not
transfer to gold here.

### PARTICIPATION — one right shape, quantitatively irrelevant

| filter | avg R @1t | @2t |
|---|---|---|
| none | +0.023 | −0.013 |
| RVOL ≥ 1.2 × slot-matched 14d | +0.021 | −0.001 |
| **RVOL ≥ 1.5** | **+0.047** | +0.031 |
| RVOL ≥ 2.0 | +0.008 | −0.009 |
| breakout range ≥ 0.5 × ATR14 | +0.023 | −0.013 |
| breakout range ≥ 1.0 × ATR14 | +0.028 | −0.007 |
| **breakout range ≥ 1.5 × ATR14** | **+0.046** | +0.014 |

**Relative volume is a spike** — non-monotone, peaking at 1.5 with both neighbours far
below and 2023 negative. Not stable, not a finding.

**Breakout-bar range is the programme's only clean monotone dose-response**: +0.023 →
+0.028 → +0.046 as the threshold tightens. That is the shape a real effect makes. It is also
worth **+0.023R over control** and decays to **+0.014R at two ticks**. Directionally
vindicated and quantitatively irrelevant — it is a lead, not an edge.

### OR WINDOW — the equity 5-minute result does not transfer

| OR | n | avg R @1t | CI | @2t | PF@2t |
|---|---|---|---|---|---|
| **5m** | 686 | **−0.034** | — | **−0.083** | 0.889 |
| 10m | 671 | −0.020 | [−0.098, +0.059] | −0.051 | 0.922 |
| 15m | 656 | +0.023 | [−0.046, +0.095] | −0.013 | 0.978 |
| 20m | 609 | +0.013 | [−0.054, +0.086] | −0.013 | 0.992 |
| 25m | 569 | +0.012 | [−0.054, +0.075] | −0.008 | 0.978 |
| **30m** | 534 | **+0.053** | [−0.007, +0.115] | **+0.031** | **1.156** |
| **35m** | 467 | **+0.063** | **[+0.004, +0.122]** | **+0.044** | 1.101 |
| 40m | 390 | +0.032 | [−0.029, +0.095] | +0.016 | 1.004 |
| 45m | 391 | +0.024 | [−0.033, +0.081] | +0.006 | 0.976 |
| 60m | 254 | +0.002 | [−0.063, +0.065] | −0.013 | 0.900 |

**5m is the worst length tested.** The published equity-ORB result favouring a 5-minute
opening range does not transfer to GC — it inverts.

**30m and 35m form a real two-cell ridge**, not a lone spike: adjacent, both surviving two
ticks, both positive in all three years. 35m's one-tick interval is the only one on the
positive side of zero anywhere in this work.

**The cost-denominator control was run and the ridge survives it.** Fixed costs enter as
`cost/risk`, so a wider stop mechanically lifts EV, and every cell that helped also carried
a wider stop. Across the OR grid the cost term spans **0.020R** against an EV spread of
**0.083R**; pre-cost EV still peaks at 30–35m with intervals clear of zero; and 60m carries
the widest stop of all with the worst pre-cost EV in the upper half. The denominator
explains roughly **one fifth** of the ridge. The rest is real — and small.

**Still not promotable.** 35m reaches **63% of the +0.10R gate** and **PF 1.101 against the
1.30 gate**. Its 2025 is **+0.010** and fading. Nine OR lengths were tested, and one
interval clearing zero out of nine is about what 95% multiplicity buys on its own.

---

## The instrument finding — reusable, and independent of ORB

This is the most transferable thing the programme produced. **State risk parameters in ATR
units, never in points or percent of price.**

| cap form | fires on train 2023–25 | fires in 2026 | transfers? |
|---|---|---|---|
| 30 points | 0.6% | 29.5% | **no** |
| **0.5 × prior-day ATR14** | **8.8%** | **7.1%** | **yes** |
| 1.0 × prior-day ATR14 | 0.3% | 0.9% | yes |
| 0.5 % of price | 19.4% | 52.7% | **no** |
| 0.25 % of price | 78.4% | 93.8% | **no** |

Gold's 09:30 15-minute opening range by year: **4.5 pts (2023) → 6.3 → 10.2 → 18.5 (2026)**,
and as a share of price **0.23% → 0.26% → 0.30% → 0.40%**.

A 4.1× rise in points and a 1.7× rise as a share of price. **Percent-of-price does not
transfer either**, and that is what localises the cause: the 2023→2026 shift is a
**volatility regime change, not a price-level change**. Gold's range grew faster than gold
did. Any parameter expressed in points, or in percent of price, is silently a different
parameter in each era.

**Any future gold work in this repo expresses risk parameters in ATR units.**

---

## Seal status

| span | status |
|---|---|
| 2023-01-02 → 2025-08-31 | train, fully used |
| **2025-09-01 → 2026-03-01** | **SEALED AND UNSPENT** |
| 2026-03-02 → 2026-08-11 | **permanently disclosed** — a full v3.1 trade list was supplied for it |

**The sealed six months are available to the next gold hypothesis.** They must **not** be
spent re-testing the ORB family. Nothing in this programme earned them, and re-running a
retired hypothesis against the last clean data would destroy the only out-of-sample
resource on this branch in exchange for a result already known on train.

Mar–Aug 2026 can never serve as holdout again for anything. Treat it as in-sample.

---

## Two leads, recorded as leads

Neither is a result. Both fell short of the gate on train.

1. **OR window 30–35 minutes.** A real two-cell ridge that survives two ticks and the
   cost-denominator control. Nobody proposed it; it emerged from the grid.
2. **Breakout-bar range ≥ 1.5 × ATR14.** The only clean monotone dose-response found.

**Reopening either requires clearing +0.10R on data that is not this train set.** In
practice that means more history — the programme ran on 3.6 years because the data begins
2023-01-02 and no Databento key was available. It does **not** mean the sealed six months.

---

## What carried over regardless — do not rebuild these

The entry family is retired. The infrastructure around it is validated and reusable.

- **A calibrated engine.** Diffed trade-for-trade against a real TradingView v3.1 export
  (75 trades, 73 inside our data): **100.0% day match (73/73), 100% direction agreement,
  98.6% exit-reason agreement, median entry-price difference 0.00 pt, median per-trade P&L
  difference $10.** Totals $27,711 against TV's $25,161.

  Getting there required fixing a defect worth recording, because it is the kind a parity
  diff exists to catch. The directional bias gates (VWAP, prior-day close) originally
  `break`-ed the day on the first blocked candidate, where the Pine reference re-evaluates
  every bar. The engine therefore silently under-traded every gated day. Parity was 89.0%
  before the fix and 100.0% after, and the earlier attribution of that residual to VWAP
  granularity (1-minute vs TradingView's 15-minute accumulation) **was wrong** — granularity
  accounted for under three points of it. `test_a_failed_bias_gate_does_not_kill_the_rest_of_the_day`
  pins the corrected behaviour.
- **35 constructed-bar self-tests**, covering every mechanism before it touches data. Two
  pin behaviour that is easy to get silently wrong: a ratchet must not fill on its own
  trigger bar, and slippage costs R while *adding* points because an R-multiple target
  widens with the risk it is measured against.
- **The risk architecture** — hard cap, profit ratchet, time-stop, daily/weekly/consecutive
  breakers with a weekly consec reset. Reported over 26 years (supplied, not verified here)
  as worst trade −$5.3k with one gap-through. It is the exit and risk layer, not the entry,
  and it is not implicated in this null.
- **ATR normalisation**, per the instrument finding above.

The **candidate generator is the only piece being retired**, and the engine is now
parameterised so a different one drops in: `run(bars, cfg, ctx, signal_fn=...)` takes any
callable returning `Candidate(signal_tmin, fill_tmin, direction, stop_ref, meta)`. See
`src/research/orb/README.md` in the AI-trading-agents repo for the full interface.

**Note on the numbers above.** Falsification (2) and the decomposition were first reported
at PF 0.98 / EV −0.000R / −$2,177 and a +0.54-vs-+0.01 stack effect. Those figures predate
the bias-gate fix and are superseded by the ones in this document. The correction moved
every one of them **against** the strategy, so the retirement verdict is stronger than when
it was first taken, not weaker.
