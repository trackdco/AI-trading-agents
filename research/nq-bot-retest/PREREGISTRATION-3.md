# PRE-REGISTRATION 3 — NQ-bot: confluence features and conviction sizing

**Written 2026-09-07, before any feature below has been computed on any trade.** This is a
measurement study on the sealed trades of the pass-marked configuration, followed — only if the
measurement earns it — by one pre-registered sizing test. It changes no entry rule.

## 1. Subject and data

- Trades: the sealed trade lists of **C1a×C3a** (10pt floor, RTH-only, R:R gate removed, 30pt cap,
  `RESULT.md` §B) across every segment: 2018-09 → 2021-08 (`h2_ctl_C1a_C3a_capped`), 2021-09 →
  2024-12 (`dev_C1a_C3a`), 2025-01 → 2026-09 (`hold_C1a_C3a`). C1a×C3b is reported alongside as a
  robustness reading, never as the primary.
- Bars: the prepared 1-minute series each run was replayed on (`data/holdout2_input/prepared` for
  2018–2021; `data/holdout_input/prepared` for 2021–2026). Every feature uses only bars up to and
  including the trade's **signal bar**. Prices in the 2021-09 → 2025-08 segment are the bot's
  roll-adjusted series; every feature is a distance or a side relative to a level computed from the
  same series inside the same or previous session, so a constant offset within a session cannot
  affect it.
- **Fit half: entries 2018-09-01 → 2024-12-31. Test half: entries 2025-01-01 → 2026-09-02.** The
  test half's outcomes are known in aggregate (`RESULT.md` §B) but have never been cut by any
  feature below. It is read once, after the fit-half report is committed.

## 2. Features — one mechanical definition each, fixed now

Sessions are CME days (18:00 ET → 17:00 ET). ATR = the bot's own ATR14 recorded at the signal.
"Price" = the signal bar's close. Buckets are fixed here; none is chosen after looking.

| # | feature | definition | buckets |
|---|---|---|---|
| F1 | session VWAP position | (price − VWAP) / σ, VWAP and σ volume-weighted from the session start | inside ±1σ / 1–2σ / beyond 2σ |
| F2 | VWAP direction | trade direction is toward the VWAP (mean-reverting) or away | toward / away |
| F3 | prior-day value area | previous session's volume profile from 1-minute bars (each minute's volume spread uniformly over its range at 0.25); POC = modal price; VA = 70% of volume built outward from POC | inside VA / above VAH / below VAL |
| F4 | VA edge | price within 0.25 ATR of VAH or VAL | at edge / not |
| F5 | POC distance | \|price − POC\| / ATR | <0.5 / 0.5–1.5 / >1.5 |
| F6 | POC direction | trade direction is toward the prior-day POC or away | toward / away |
| F7 | prior-session Fibonacci | retracements 23.6/38.2/50/61.8/78.6% of the previous session's high–low; nearest-level distance / ATR | ≤0.25 / 0.25–0.75 / >0.75 |
| F8 | overnight Fibonacci | same levels on the overnight range (18:00 → 09:30 ET), RTH signals only | ≤0.25 / 0.25–0.75 / >0.75 |
| F9 | EMA200 trend | EMA200 on 2-minute closes (bot's bars); slope over the last 10 bars; direction with the slope, against it, or flat (\|slope\| < 0.05 ATR) | with / against / flat |
| F10 | EMA20 distance | (price − EMA20) / ATR, signed by trade direction (positive = extended against the trade) | < −0.5 / −0.5–0.5 / > 0.5 |
| F11 | EMA50 side | price above/below EMA50 relative to trade direction | with / against |
| F12 | opening range | first 30 minutes of RTH (09:30–10:00) high/low; signals after 10:00 | inside OR / beyond OR in trade direction / beyond against; signals before 10:00 = "forming" |
| C1–C6 | covariates, already recorded | stop width, ATR, level class, sweep depth, volume ratio, hour, HTF agreement | as in `RESULT.md` §B.10–11 |

Twelve features, 30 buckets. No other feature is added after this line.

## 3. What "holds" means — fixed now

Per feature, on the fit half: bucket n, win rate, mean net $/trade, session-block bootstrap 95% LB,
and the **gap** = mean of the best bucket minus mean of the worst bucket (buckets ranked on the fit
half), with its own block-bootstrap 95% LB. A feature is a **candidate** if the fit-half gap's LB
is > 0 and both buckets have n ≥ 200.

On the test half, read once for all candidates together: the same buckets with the ranking **fixed
from the fit half**. A candidate **holds** if the test-half gap (best-fit-bucket minus
worst-fit-bucket) is positive with its 95% LB > 0. Otherwise it is noise, reported as such. The
number of candidates is what it is; no correction is applied to the fit-half screen because the
test half is the arbiter, and the test half is read once.

Stop width and ATR are tabulated alongside every candidate: a "feature" that merely re-labels stop
width is disclosed as such and not counted.

## 4. Conviction sizing — fixed now, run only if ≥ 1 feature holds

- Score = number of held features on which the trade is in its best bucket minus the number on
  which it is in its worst bucket (held features only; equal weights; no fitting).
- Two multiplier readings, both run: **A** = {score ≤ −1: 0.5×, 0: 1×, ≥ +1: 1.5×};
  **B** = {0.75×, 1×, 1.25×}. Contracts are integers on two micros, so 0.5× = 1 contract with the
  same stop, 1.5× = 3; PnL scales linearly.
- Evaluated on the **test half only**, against flat 1× sizing: **PASS** if, under **both** readings,
  net $ per unit of risk taken (sum of PnL / sum of stop-distance × contracts) improves **and** max
  drawdown in dollars does not worsen by more than 10%. Otherwise conviction sizing is NOT
  DEMONSTRATED. Minimum across the two readings, as always.

## 5. Reads

Fit half: measured once, committed. Test half: one read covering §3 and §4 together. C1a×C3b
reported alongside with the same buckets. No re-cut of the test half under new features or new
buckets; a further study needs data none of this has touched.
