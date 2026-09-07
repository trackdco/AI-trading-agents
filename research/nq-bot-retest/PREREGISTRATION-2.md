# PRE-REGISTRATION 2 — NQ-bot: the 30-point stop cap removed

**Written 2026-09-07, before any new data exists in the session and before any run on it.** Second
pre-registered family on this bot; the first (`PREREGISTRATION.md`) was read once on 2026-09-06
and passed (`RESULT.md` §B). This document fixes one change, its readings, the data that will judge
it, the execution model, the pass mark, and what counts as a read.

## 1. The single change

**The 30-point maximum-stop cap (`HIGH_CONVICTION_MAX_STOP_PTS`) is removed.** In the driver this is
`--cap-lifted`. One reading. A raised cap (45, 60 …) was considered and is not run: no such number
has an argument; A5 and A22 never had a cap.

Applied to the three live cells of the pass-marked family, whose readings are inherited unchanged:

| cell | stop floor | R:R gate | RTH-only |
|---|---|---|---|
| V2-1 | C1a: 10.00 pt fixed | removed | yes |
| V2-2 | C1a: 10.00 pt fixed | kept | yes |
| V2-3 | C1b: 2 × ATR14 | removed | yes |

**Verdict = the minimum across the three.** All three are built and run; none is selected.

**Arguments that predate the data this will be tested on** (all before 2021-09, see §2):
- A5 / A22 (2026-08-08): the stop measures structure; a cap truncates exactly the stops the
  argument asks for. The 2×ATR reading was pre-registered on that basis and then collided with the
  cap on most signals (`PREREGISTRATION.md` §1-bis, `RESULT.md` §B.2).
- The one slice pattern stable across both seen windows is about stop width: floor-bound stops the
  weakest positive bucket, 20–30 pt stops the best (`RESULT.md` §B.11). Every entry-selection
  pattern flipped; this one did not.
- The cap-lifted sensitivity — pre-registered as a disclosure, never a candidate — was positive in
  every cell on the first holdout (§B.4). **That is a holdout read, and it is why this change needs
  data none of it has touched.**

**Not changed:** everything in `PREREGISTRATION.md` §2 (detector, score, HC 0.75, SWEEP_MIN 0.70,
HTF gate, C1/C2 exits, slippage 0.50/1.00, commission $1.29/side, daily loss $500, cumulative kill
switch $1,000, 30-bar warmup, 2-minute bars from 1-minute); the known defects left in place; the
level-type change withdrawn after `RESULT.md` §C.2 found nothing to exclude.

## 2. Data — new in the past

**Holdout-2: NQ front-month 1-minute bars, 2018-09-01 → 2021-08-31.** Every bar precedes every bar
this bot, its author's published results, this analysis, or this repository's tape has used (the
bot's own data starts 2021-09-01; the repository's tape 2023-01-02). It contains the 2020 crash —
a regime unlike 2021–2026, which is the point of a holdout, and is disclosed as a reason a failure
would read "not robust across regimes" rather than "the cap is right".

- Source: Databento GLBX.MDP3, schema `ohlcv-1m`, parent symbol `NQ.FUT` (every contract), pulled
  2018-08-01 → 2021-09-30 so that August 2018 warms the engine and September 2021 overlaps the
  bot's own series for an integrity check (volumes expected identical minute for minute, prices
  offset by the bot's roll adjustment, as in `RESULT.md` §0).
- Construction: unadjusted front month, rolling at the start of the Monday-of-expiry-week session —
  the repository tape's convention, which the first holdout used (`build_nq_series.py --roll
  monday_of_expiry_week`). Real round numbers.
- Integrity before any run: bar count per session, gaps beyond weekends and maintenance, the
  overlap check. A failure here is an abort, not a reason to patch.
- The engine starts cold on 2018-08-01, as the bot's own backtests do. The cumulative $1,000 kill
  switch is therefore armed from day one. If it trips, the cell is reported to the trip date and the
  n < 300 abort rule applies to it; a kill-switch-disabled run of that cell is reported alongside,
  never as the verdict.

## 3. Execution model — fixed

The bot's own: exits evaluated on 2-minute closes in software, hard stop filled at the breaching
close, trailing and breakeven exits at their level. Established as the bot's live behaviour in
`RESULT.md` §C.1. **Disclosed counterfactual, reported, never a candidate:** the same cells with
resting-order stops on 1-minute bars (`--intrabar-stops --no-kill-switch`).

## 4. Pass mark — fixed here, evaluated once

For each of the three cells on holdout-2:
- **mean net $/trade > 0**, and
- **session-block bootstrap one-sided lower bound > 0 at 97.5%** (α = 0.025: this is the second
  pre-registered family on the same bot, so the per-family level is halved; blocks = CME trading
  days of entry, 10,000 iterations, PCG64 seed 20260907; `analyze_retest.py --alpha 0.025 --seed
  20260907`).

**PASS only if all three cells clear both.** Otherwise NO EDGE DEMONSTRATED for the cap-free family;
the pass-marked family of `RESULT.md` §B stands as it is.

Abort (no verdict): fewer than 300 trades in any cell; sign of the mean flipping under 2× slippage
in any cell; a lookahead, slippage-direction, commission or PnL-sum check failing; a data-integrity
failure under §2.

Reported, not binding: profit factor, max drawdown (expected to rise — this change buys expectancy
with per-trade risk, and the reader must see the price), trade counts, monthly PnL, win rate, mean
stop; the same three cells **with the cap** and the **untouched bot** on holdout-2 as controls
(also the first test of the pass-marked family on data before its own history); the intrabar
counterfactual; the kill-switch-disabled variant where §2 requires it.

## 5. Procedure and reads

1. Commit this document; record its hash in `RESULT-2.md`.
2. Obtain the Databento key; fetch, build, integrity-check. No engine runs until the check passes.
3. Run: three cap-free cells; three capped controls; the untouched control; 2× slippage for the
   three cells; the intrabar counterfactual for the three cells. Seal each.
4. `analyze_retest.py` with §4's parameters. Write `RESULT-2.md`.

**Reads:** holdout-2, one read, covering everything in 3–4. Nothing in §1–§4 changes after step 2
begins. If the verdict is NO EDGE, the cap question is closed on this bot; a third family needs a
new document and data none of this has touched.
