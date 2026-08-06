---
date: 2026-08-06
status: RESEARCH — framework survey and gap analysis against what we already do
tags: [framework, walk-forward, pbo, dsr, regime, ml, prop, research]
---

# How people actually build self-learning AI trading systems — and where we stand

ANGUS 2026-08-06: *"do some deep research on how people are building self learning ai trading
bots, and overall using AI to build automated trading systems for prop firms. scour especially
youtube and instagram reels. so that you have an idea of the core framework."*

## The blunt finding first

**Almost all of the video content is engineering content, not edge content.** The biggest
results by view count — "I Built an AI Trading System With Claude + TradingView" (552k), "I
Made My Own AI Trading Bots & Indicators" (523k), "How To Actually Build a Trading Bot With
Claude Code" (275k), "How I Built a Self-Healing Trading Bot That Fixes Its Own Losses" (92k)
— are about **wiring**: how to connect a model to a broker, how to get an LLM to write the
strategy file, how to deploy. None of them is about whether the signal has an edge.

One of the articles states it better than I could: *"Automated Trading Strategy: The Bot Isn't
the Edge."* That is exactly the lesson this project learned the expensive way.

So the honest answer to "what's the core framework" is: **the framework is well-known, boring,
and not the hard part.** The hard part is the thing none of the content addresses, which is
knowing whether what you found is real.

## The architecture everyone converges on

    data feed → signal logic → risk check → execution → logging

Nobody disagrees about this and it is not where systems differ.

## What "self-learning" actually means in practice

Stripped of marketing, it is **walk-forward optimisation**:

- Retrain on a rolling training window, evaluate on the **immediately following** out-of-sample
  window, roll forward, repeat.
- **k-fold cross-validation is explicitly wrong here** — it leaks future into past on time
  series. This is the single most common technical error in the amateur content.
- **Retraining cadence should match the trading timeframe.** For intraday strategies the
  sources say monthly-to-quarterly re-optimisation, and the OOS window length is the natural
  guide to the cadence.
- **Regime-aware segmentation** is the current refinement: condition the train/test windows on
  volatility or macro regime rather than pure calendar.

The honest caveat, stated by the serious sources and by none of the videos: walk-forward
**reacts to regime shifts rather than predicting them.** "Adaptive" does not mean prescient.

## What kills these systems — consistent across every credible source

1. **Overfitting.** Named as the top killer everywhere. The concrete rule of thumb that keeps
   recurring: **fewer than six optimisable parameters.**
2. **Look-ahead bias / data leakage** — "test uses data that would not have existed at trade
   moment."
3. **Execution assumptions.** The sharpest line found: *"bots issue market orders assuming
   last-price fills, but live order books show depth evaporation."* Signals are not usually
   what breaks first — fills are.
4. **Regime change** — optimised but not robust; "built for the past, not the future."
5. **Zero-slippage / perfect-fill backtests.**

Standard discipline: nothing goes live until it has passed a backtest **and at least 30 days of
paper trading**.

## Prop-firm specific

AI/ML/LLM-driven systems are generally permitted **if the automated system executes a strategy
that would be permitted if run manually.** The automation is not the compliance question; the
strategy behaviour is.

---

## Gap analysis — what WE already do better, and what we are actually missing

This matters more than the survey, because most of the framework we already exceed.

### Already stronger than anything in the content

| practice | us |
|---|---|
| pre-registration | `docs/PREREG-*.md` before any test |
| family-wise permutation nulls | §2.3, and it has killed real candidates (`trig_delta_conf` at p=0.065 against a declared 0.01) |
| era-split validation | discover 2025 / validate 2026, independently |
| sealed holdout | 2023/24 days, never iterated |
| census kill lines | §5.9.1 — no expectancy claim from a census |
| causality auditing | caught the depth read one bar late, and the +10.57pt "confirmation" head start |
| friction modelled | 2 pt/round trip as a standing bar |

None of the surveyed material does any of this. The permutation null and the sealed holdout in
particular are simply absent from the genre.

### Genuinely missing, and worth building

1. **Walk-forward optimisation.** We do a *static* era split — fit on 2025, check 2026. That
   answers "does it survive one regime change" but not "would a rolling re-fit have kept
   working." This is the biggest structural gap and it is the core of what the field calls
   self-learning.
2. **PBO (Probability of Backtest Overfitting) and the Deflated Sharpe Ratio.** Angus named
   both. We currently have no measure of *how many things we tried*, which is exactly what
   makes a best-cell meaningless. The separator scan tested 93 buckets and I reported the
   survivors with a hand-waved "expect ~2 by chance" — CSCV/PBO and DSR replace that guess with
   a number.
3. **Regime conditioning that is actually used.** `output/daily_context.parquet` exists —
   trend state, VIX regime, balance/imbalance, value migration — and nothing consumes it.
4. **Parameter-count discipline.** The <6-parameter heuristic is a good hard rule and we have
   never stated one. The canon has far more than six degrees of freedom once every check
   threshold is counted.
5. **Execution realism beyond friction.** We model 2 pt/round trip but not depth evaporation.
   Given we hold MBP-10, we could measure whether our own fills would have been available.

### What NOT to take from this research

- **Reinforcement learning / deep learning / LSTM.** Heavily promoted, and a bad fit here:
  ~12k training samples, non-stationary target, and a model class that is nearly impossible to
  audit for the causality violations that have bitten us twice. Interpretability is not a
  luxury on this project — it is the only reason we have caught our own errors.
- **"Self-healing" / "self-improving" agent loops.** An agent that rewrites its own strategy
  after losses, with no holdout and no null, is a machine for overfitting at speed.
- **Zero-code platforms.** Irrelevant; the bottleneck was never the wiring.

## The conclusion I would defend

The framework is not the constraint. **Our validation discipline is already ahead of the
field; our missing pieces are three specific measurements — walk-forward, PBO, DSR — and a
hard parameter budget.** Adding those does not make the model smarter. It makes the difference
between a result and a story, which is precisely what this project keeps needing.
