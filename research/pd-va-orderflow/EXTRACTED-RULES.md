# Extracted rules — "daily bias / key levels / order-flow execution" (video transcript, 2026-09-09)

Nothing here is tested. This is the video's method written as rules, with every gap marked
**UNDEFINED**. Claims of accuracy in the video (70–80% bias accuracy, "insane accuracy" with gamma,
a 1:8 example) are the presenter's and are not evidence.

## 1. Sessions and profiles

| object | definition | notes |
|---|---|---|
| Cash session | 09:30 → 16:00 ET | previous day's, on a 5-minute chart, as a fixed-range volume profile |
| PD cash VP | volume profile of yesterday's cash session → **VAH, VAL, POC** | value-area % not stated; standard 70% assumed |
| Overnight VP | 18:00 (prev day) → 09:29 ET of the trading day → ON-VAH, ON-POC, ON-VAL | used for targets; in neutral bias also as fade levels when PD levels are far |
| Entry timeframe | 1-minute | order-flow tools plotted there |

## 2. Daily bias — decided at the 09:30 open

| the 09:30 open is… | bias | plan |
|---|---|---|
| above PD cash **VAH** | bullish | wait for a pullback into PD VAH, go long there |
| below PD cash **VAL** | bearish | wait for a rally into PD VAL, go short there |
| inside [VAL, VAH] | neutral | fade the edges: short at VAH, long at VAL, target POC / the other edge |

**UNDEFINED:** what "open" is (the 09:30:00 print or the 09:30 bar's open/close); an open exactly
at VAH/VAL; how far above/below counts as "far" (which switches the plan to gamma levels); how long
after the open the bias remains valid; whether a bias flips intraday.

## 3. Key levels by bias

- Bullish: PD VAH first; PD POC and PD VAL as the next levels below. If the open is "far above"
  (UNDEFINED) so a retest is unlikely: gamma levels below price (put support, GEX levels).
- Bearish: mirror — PD VAL first; POC, VAH above; gamma levels above price if "far below".
- Neutral: PD VAH and PD VAL; if those are far, the **current** day's overnight VAH/VAL.
- With gamma available, in neutral bias: prefer the GEX level just beyond VAH/VAL over the VAH/VAL
  itself; skip the plain VAH tap if there is no gamma level near it.
- Presenter's ranking: opens outside value (bullish/bearish) give the best setups; neutral second.

## 4. Entry trigger — order-flow version (1-minute), in the direction of bias

Sequence at the key level:

1. **Tap** — price reaches the level (tolerance UNDEFINED).
2. **Absorption of the opposing side** — large aggressive prints of the wrong side (sellers for a
   long) located in the **wick** of the candle, with no follow-through ("effort, no reward").
   Definition given: aggressive volume in the wick = absorbed; aggressive volume in the body with
   the close beyond it = follow-through.
3. **Aggression of the trade side** — large same-side prints (buyers for a long) inside the body of a
   candle that closes in the trade direction, ideally leaving a same-side **imbalance** (buy
   imbalance) — that imbalance is the entry zone.
4. **Inversion** — a close beyond the price cluster of the absorbed opposing prints (long: close
   above the absorbed sellers). The absorbed side "lost the battle".

Entry: at the retest of the imbalance (preferred) or on the confirming close (aggressive).

Tool settings stated: "big trades" filter **45 contracts** (on MNQ), text plot, opacity 80;
imbalance tracker on. **UNDEFINED:** the imbalance ratio; whether 45 is a single print or a
per-level aggregate; how many candles absorption may span; a second attempt at the same level
(the first example takes the second tap after a breakeven exit); minimum distance of the close
beyond the cluster.

## 5. Entry trigger — ICT alternative (same level, same bias)

- 1-minute **inverse FVG**: a small opposing fair-value gap that price then closes through in the
  bias direction; enter on the inversion.
- "CISD" mentioned, not defined.

## 6. Stops

- Long: below the absorbed sellers' cluster (the absorption candle's low). Short: above the
  absorbed buyers. Neutral-fade short: above the absorbed buyers. **UNDEFINED:** tick offset.

## 7. Targets and management

- Bullish: overnight VP levels above, in order — ON-VAL (if coming from below), ON-POC, ON-VAH.
  Three contracts implied: **one off at the first ON level, then stop to breakeven, two held** for
  POC / VAH "if the bias is strong" (UNDEFINED).
- Bearish: mirror.
- Neutral: PD POC, then the opposite edge of the PD value area.
- Also used: relative equal highs/lows as a target; ON-VAH as the breakeven trigger (example 2).

## 8. Gamma overlay (MenthorQ end-of-day levels, SPX converted to NQ/MNQ)

- Regime: price **above HVL (0DTE)** → positive gamma → balanced, choppy, levels respected;
  **below HVL** → negative gamma → trending, levels break.
- Levels: call resistance, put support, HVL, GEX1–GEX5. Used as the preferred reaction points
  ("very strong confluence"), never as the trigger.
- **No historical data** for these levels; the presenter says so. Cannot be backtested; live-only.

## 9. What can be coded from what we have

| component | codable? | data in this repository |
|---|---|---|
| sessions, PD/ON volume profiles, VAH/VAL/POC, bias rule, key levels, targets | yes, once the value-area % and "open" are fixed | 1-minute NQ 2018-09 → 2026-09 |
| absorption / aggression / imbalance | yes only with aggressor-tagged per-price volume, and after fixing the 45-contract threshold and an imbalance ratio | footprint files 2025-06 → 2026-07 (`data/reference/cvd/`), 13 months; nothing before |
| inverse FVG | yes (1-minute FVG definition is mechanical) | 1-minute bars |
| gamma levels | no | none historical |

**Before building anything:** the newer branches already contain a prior-day value-area backtest
(`docs/BACKTEST-pd-va-strategy.md`, with a "champion config", a 5pt floor finding and a 7-session
forward test). The bias-and-levels half of this video is that strategy. Read it first.

## 10. Numbers the video actually gives

09:30–16:00; 18:00–09:29; 45-contract big-trade filter; opacity 80; "70 to 75%", "75 to even 80%"
bias accuracy (claimed); one example 1:8 (hindsight). Everything else is shape, not number.
