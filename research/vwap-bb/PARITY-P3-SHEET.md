# PARITY SHEET — P3

**Wednesday 2025-01-29 · 10:20 ET.** The candle covering 10:18:00–10:19:59 has just closed.
Nothing from 10:20:00 onward has happened.

**Do not open `research/vwap-bb/P3-SELECTION-SEALED.md` until this sheet is submitted.**
It contains the reason this instant was chosen and the values the detector produced. Opening it
first destroys the gate.

**Bar Replay to 10:20:00 ET, then read.** Do not scroll forward. If you see anything past 10:20,
stop, reset, and start again — a contaminated reading is worse than no reading, because it looks
like a pass.

---

## Which bar you are on

Chart labels by **open** time, so step to these:

| entry TF | last completed bar | covers |
|---|---|---|
| 1m | 10:19 | n/a — not readable on this platform for Jan 2025 |
| **2m** | **10:18** | 10:18:00 – 10:19:59 |
| **3m** | **10:15** | 10:15:00 – 10:17:59 |
| **5m** | **10:15** | 10:15:00 – 10:19:59 |

At 10:20 the NY VWAP has 50 minutes behind it, so its σ bands are eligible under A8. At P2 they
would not have been. This instant exercises them properly.

---

## §0 — Provenance

| field | answer |
|---|---|
| Platform | |
| Contract charted | |
| Bar Replay used | |
| Chart labels candles by | |
| **Which chart timeframe did you read the VWAP values off?** | |
| Any scheduled macro event on this date you'd normally account for? | |

**The VWAP timeframe question is new and it matters.** A8 now specifies VWAP computed from
1-minute bars. You cannot render that for January 2025, so the NY band comparison is a known
limitation, not a fresh failure — but recording which timeframe you read lets the comparison be run
against a same-timeframe recomputation as well as the canonical one. Without it, seven fields
mismatch for a reason already diagnosed and the result reads as a second FAIL.

On the macro-event line: answer from what you'd normally know sitting down to trade. Don't go and
look it up.

---

## §1a — Cluster-eligible levels

Every value, at 10:20:

| level | price |
|---|---|
| Daily VWAP — mid | |
| Daily VWAP — +1σ | |
| Daily VWAP — −1σ | |
| Daily VWAP — +2σ | |
| Daily VWAP — −2σ | |
| Daily VWAP — +3σ | |
| Daily VWAP — −3σ | |
| NY VWAP — mid | |
| NY VWAP — +1σ | |
| NY VWAP — −1σ | |
| Daily POC (4 ticks per row) | |

## §1b — Over-extension reference

| level | price |
|---|---|
| NY VWAP — +2σ | |
| NY VWAP — −2σ | |
| NY VWAP — +3σ | |
| NY VWAP — −3σ | |

## §1c — Structural levels

Prior-day and prior-week values on a **Globex** basis — that was set as the operative definition
by your P2 reading and the implementation already agrees.

| level | price |
|---|---|
| Session high so far (from 18:00 ET) | |
| Session low so far | |
| Prior-day high (Globex) | |
| Prior-day low (Globex) | |
| Pre-market high (18:00 → 09:29) | |
| Pre-market low | |
| Week-to-date high | |
| Week-to-date low | |
| Prior-week high | |
| Prior-week low | |
| VAH | |
| VAL | |

## §1d — HTF ranges

| field | value |
|---|---|
| 4h range — high | |
| 4h range — low | |
| 1h range — high | |
| 1h range — low | |
| Method used | |

Same method as P2 (swing highs and lows) unless you'd naturally do it differently — if so, say
which and why.

## §2 — Bollinger Bands, per entry timeframe

20-period, 2σ. **Check the column headings before you write** — upper above, lower below. The 3m
row came in transposed at P2.

| TF | lower 2σ | basis (20 SMA) | upper 2σ |
|---|---|---|---|
| 1m | n/a | n/a | n/a |
| 2m | | | |
| 3m | | | |
| 5m | | | |

## §3 — Last completed candle per entry timeframe

| TF | label | open | high | low | close |
|---|---|---|---|---|---|
| 1m | n/a | n/a | n/a | n/a | n/a |
| 2m | 10:18 | | | | |
| 3m | 10:15 | | | | |
| 5m | 10:15 | | | | |

## §4 — Clusters

Leave this blank. I'll compute it from §1a, §1c and §2 the way I did at P2, so the cluster logic is
derived from your raw readings rather than done twice by hand.

## §5 — HTF classification

15-minute chart, N=2 fractal. At 10:20 the completed 15m bars run through 10:00, so **the latest
confirmable swing is 09:30 or earlier** — a swing at bar *i* needs bars *i+1* and *i+2* completed.
Anything later than 09:30 cannot be confirmed yet.

| field | price | time (ET) |
|---|---|---|
| Most recent confirmed 15m swing high | | |
| The one before it | | |
| Most recent confirmed 15m swing low | | |
| The one before it | | |
| **Your call: uptrend / downtrend / range** | | |

A8–A12 added the plateau tie-break: if two bars print the identical high, the **earlier** one is
the swing. Apply that if you hit a tie.

## §6 — Filters

| filter | reading |
|---|---|
| Location — is price extended, or is there room? | |
| Confluence — how many distinct types at the cluster you'd trade, and is it with-trend or counter-trend? | |
| Invalidation — is the last candle touching a ±1σ? **Say which VWAP: daily, NY, or both.** | |
| Over-extension — has NY VWAP ±2σ been touched this session? At what time? | |

## §7 — Trigger

| field | answer |
|---|---|
| Is there a valid trigger at 10:20? | |
| Which timeframes did you check? | |
| If yes — TF, direction, and what the trigger was | |
| If no — why not, in your own words | |

Your own words matter more than a tidy answer. The two unwritten entry conditions found at P2 both
came out of this box.

## §8 — Resulting trade

Only if §7 fired.

| field | value |
|---|---|
| Entry price | |
| Stop price | |
| Target price | |
| Resulting R:R | |
| What anchored the stop | |
| What the target was measured to | |

## §9 — Anything the sheet did not ask for

Anything you noticed that no box above captures. "Nothing" is a real answer — it was the answer at
P2 — but this box has produced two spec gaps in this project, so give it thirty seconds.

---
---

# STAGE-B NOTE — not part of the sheet, added when it was filed

**Nothing below asks a question or changes an answer.** It records what was checked before the
sheet was accepted, and three things the Stage B comparison must not get wrong. **No detector
value for 2025-01-29 appears here.**

## Every timing claim in the sheet was verified by arithmetic

Detector close-minute label at the instant is `cm = 620`.

| claim | check | verdict |
|---|---|---|
| 2m last completed bar = 10:18, covers 10:18:00–10:19:59 | 620 % 2 = 0 → closes at the instant | **correct** |
| 3m last completed bar = 10:15, covers 10:15:00–10:17:59 | 620 % 3 = 2 → **3m does not evaluate at the instant**; its last close was `cm 618` = 10:18 | **correct** |
| 5m last completed bar = 10:15, covers 10:15:00–10:19:59 | 620 % 5 = 0 → closes at the instant | **correct** |
| completed 15m bars run through the bar labelled 10:00 | last 15m close is 10:15, labelling that bar 10:00 | **correct** |
| latest N=2-confirmable swing is 09:30 | 10:00 − 2 × 15 min | **correct** |
| NY VWAP has 50 minutes behind it; σ bands eligible under A8 | 620 − 570 = 50 ≥ 30 | **correct** |
| at P2 they would not have been | 590 − 570 = 20 < 30 | **correct** |
| plateau tie-break gives the swing to the earlier bar | A10, as written | **correct** |

## Three things Stage B must handle, flagged now rather than argued later

**1. The blind is PARTIAL, by construction, and the verdict must be weighted for it.**
Amendment 03 §7 required P3 to be an instant where a trigger survives past the confluence gate,
and that requirement is Angus's own text. **He therefore already knows a trigger exists and that
it is on 2m, 3m or 5m.** §7's yes/no question is effectively pre-answered and **carries no
evidential weight**. What remains genuinely blind, and what the gate actually tests:

- **which** timeframe it fires on, and whether more than one fires
- the **direction**
- the **trigger kind** — rejection block or displacement
- every level in §1a–§1d, §2 and §3
- the **entry, stop and target** in §8, and what anchors them

Stage B must state this and must not count a §7 agreement as a match.

**2. `research/vwap-bb/P3-SELECTION-SEALED.md` stays shut.** It is in the repository and
readable. It holds the timeframe, the direction, the geometry and the selection reasoning. It is
opened only after the completed sheet is recorded, exactly as `PARITY-ANGUS-READINGS.md` was at
P2.

**3. Two claims in the sheet body are slightly wider than the record supports.** Neither changes
a question, so neither was edited:

- §1c says prior-day *and prior-week* are Globex "and the implementation already agrees."
  **Prior-DAY: correct**, verified at P2 (21783.50 / 21377.75 against the reading's 21783.75 /
  21378.25). **Prior-WEEK: the detector does not compute it at all** — it is not in the level
  menu and was NOT COMPARABLE at P2. Read the boxes; expect no verdict on those two.
- §4 says clusters will be derived "from §1a, §1c and §2". Including §1c produces the
  **structural-eligible** reading of ambiguity (a). The implementation takes structural levels as
  **not** cluster-eligible. Stage B must compute **both** readings, as it did at P2, and label
  which is which.

**Detector unmodified. Sealed workbench parquet unopened. Holdout sealed. N_trials 0.**
