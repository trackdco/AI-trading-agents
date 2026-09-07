# CLOSED — NQ-bot re-test programme (2026-09-05 → 2026-09-07)

**Decision, Angus, 2026-09-07: not good enough to trade. Closed.**

## What was asked and answered

| question | document | answer |
|---|---|---|
| Can the third-party bot's tests be run, and what does it actually do? | `AI-TRADING-BOT-SETUP-AND-TEST-GUIDE.md`, `TRADE-AND-ENTRY-REVIEW.md` | Yes; its 4-year result is PF 1.13, near breakeven; its "MNQ" data is roll-adjusted NQ; four defects in its entry mechanism |
| Do three structurally argued fixes (10pt stop floor, RTH-only, phantom-target gate removed) hold on unseen data? | `PREREGISTRATION.md`, `RESULT.md` | **PASS** on 2025-09 → 2026-09, minimum across three live cells; the 2×ATR reading passed by $0.16/trade |
| Does removing the 30pt cap help? | `PREREGISTRATION-2.md`, `RESULT-2.md` | **ABORT** on 2018-09 → 2021-08: the 2×ATR cell tripped the bot's kill switch at cold start; doubled slippage turns the 10pt cells negative. The cap was never the lever |
| Is the stop model honest? | `RESULT.md` §C.1 | Yes — the bot evaluates every exit on 2-minute closes in software and holds no broker stops; with resting stops it loses $10/trade |
| Which levels or confluences select the winners? | `RESULT.md` §B.10–11, §C.2; `PREREGISTRATION-3.md`, `RESULT-3.md` | **None.** The bot's five score bonuses, the level types, the autopsy slices and twelve external confluences all flip between windows. Conviction sizing not demonstrated |

## The number to remember

Passed configuration, nine years of separate sealed runs, two micro contracts: 9,824 trades,
**+$10.65 per trade** after $9.25 of friction, PF 1.29, worst drawdown $3,572, one losing year
(2019). Untouched bot on the same span: +$4.92, double the drawdown, three losing years.

## Why it is closed

- The edge is the size of its own costs; a tick of slippage per fill removes a quarter of it, and a
  thin year (2018–2021) goes negative under doubled costs.
- It cannot be graded: no feature, internal or external, separates its winners from its losers
  across windows, so it cannot be sized and cannot be improved by selection.
- It depends on close-evaluated exits with a 2.5-point trail — implementable, but with an unshowable
  tail between closes.
- What survives every test is one observation, not a system: a 2–8 point overshoot of a 50-point
  level during regular hours, reclaimed within a bar, tends to revert, and pays only with a stop wide
  enough to survive the noise.

## What remains usable

`retest_backtest.py` (engine import, exact reproduction gate, checkpoints, continuation),
`fast_features.py` (verified-equivalent fast paths), `compare_trades.py`, `analyze_retest.py`
(session-block bootstrap, pass-mark as code), `prepare_holdout_data.py`, `build_nq_series.py`,
`features_study.py`, `loser_autopsy.py`, and the three pre-registration documents as templates.
The bot repository is unchanged; nothing here was pushed to it.

## Reads spent

Holdout-1 (2025-09 → 2026-09): one read. Holdout-2 (2018-09 → 2021-08): one read. Feature test
half (2025-01 → 2026-09): one read. No unseen NQ bar data remains in the repository for this bot.
