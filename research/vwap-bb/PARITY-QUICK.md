# PARITY — THE SHORT VERSION

**8 numbers per date. About 5 minutes each.** Do this one. The long sheet
(`PARITY-SHEET.md`) is better coverage but this is what actually unblocks the study.

Chart: **NQ, front month NQH5 (March 2025). Timezone: New York. 5-minute chart.**

---

## Before you read anything: turn on Bar Replay

TradingView → **⏵ Replay** in the top toolbar → click the candle you want → chart rebuilds as if
that moment were now.

**This is not optional.** Three of the numbers below (POC, session high, session low) are
completely different if the rest of the day is on screen — you'd be reading the *whole day's*
volume profile instead of the profile as it stood at that minute. That would look like a code
bug when it's just a chart-reading artefact.

TradingView labels candles by **open** time. So:

- For **09:48**, step Replay so the **09:45** 5-minute candle is the last completed one.
- For **09:50**, step Replay so the **09:45** 5-minute candle is the last completed one.

---

# DATE 1 — Wednesday 15 January 2025, at 09:48 ET

| # | what | your reading |
|---|---|---|
| 1 | **Daily VWAP — the middle line** | |
| 2 | Daily VWAP **+1σ** (upper band) | |
| 3 | Daily VWAP **−1σ** (lower band) | |
| 4 | **NY VWAP middle** (the one anchored 09:30) | |
| 5 | **Volume profile POC** *(needs Replay)* | |
| 6 | **Bollinger basis** — BB(20,2) middle line, 5m chart | |
| 7 | **Session high so far**, since 18:00 ET last night *(needs Replay)* | |
| 8 | **Session low so far**, since 18:00 ET last night *(needs Replay)* | |

**Then two judgement calls:**

| | |
|---|---|
| **A. Would you have taken a trade here?** yes / no — and if yes, long or short? | |
| **B. If yes — where exactly would your stop go?** Give me the price, or "X points below entry" | |

---

# DATE 2 — Wednesday 22 January 2025, at 09:50 ET

| # | what | your reading |
|---|---|---|
| 1 | **Daily VWAP — the middle line** | |
| 2 | Daily VWAP **+1σ** | |
| 3 | Daily VWAP **−1σ** | |
| 4 | **NY VWAP middle** | |
| 5 | **Volume profile POC** *(needs Replay)* | |
| 6 | **Bollinger basis** — BB(20,2) middle, 5m | |
| 7 | **Session high so far** *(needs Replay)* | |
| 8 | **Session low so far** *(needs Replay)* | |

| | |
|---|---|
| **A. Would you have taken a trade here?** yes / no — long or short? | |
| **B. If yes — where exactly would your stop go?** | |

---

## Rules

- **Can't find a number? Write "n/a".** Do not estimate. A blank is useful information; a guess
  quietly corrupts the comparison.
- **Anything odd, say so.** If your chart shows something the list doesn't ask about, or an
  indicator setting differs from what's assumed, that's often the most useful thing on the page.

## Why these eight

**#1 is the load-bearing one.** Every confluence cluster in the strategy is anchored to the VWAP
family. If the daily VWAP anchor or its source price differs from the code's, nothing downstream
can possibly agree — and everything else on this page becomes noise.

**#5, #7, #8 are the accumulating ones** — the values that are wrong if you read them off a
finished chart. They're the reason Replay matters.

**B is the single most valuable answer on the page.** It is not a parity check; it settles an
open question about the strategy itself. See `DECISIONS-FOR-ANGUS.md` decision 2.
