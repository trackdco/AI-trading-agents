# PARITY COMPARISON — 2025-01-15 09:48 ET · **FAIL**

**2 of 8 fields match at 1.00-point tolerance. The parity gate FAILS.**

Angus's readings were committed in `7d98da5` **before** any detector value was computed. The
comparison is in the following commit. That ordering is on the record.

Per the runbook: *"A FAIL here is the valuable outcome. It means the detector does not implement
the strategy, and finding that before reading a result saves the run."* **It has done exactly
that** — and the pattern in the failures is more informative than a pass would have been.

---

## The table

| field | Angus | detector | diff | verdict |
|---|---|---|---|---|
| **BB basis 2m(20)** | 21263.50 | 21263.85 | **0.35** | ✅ **MATCH** |
| **session high so far** | 21329.25 *(08:48)* | 21329.00 *(08:48)* | **0.25** | ✅ **MATCH** |
| daily VWAP mid | 21153.50 | 21163.00 | **−9.50** | ❌ MISMATCH |
| daily VWAP +1σ | 21303.00 | 21308.13 | −5.13 | ❌ MISMATCH |
| daily VWAP −1σ | 21004.50 | 21017.87 | −13.37 | ❌ MISMATCH |
| NY VWAP mid | 21265.25 | 21262.18 | **+3.07** | ❌ MISMATCH |
| POC | 21285.00 | 21281.00 | +4.00 | ❌ MISMATCH |
| session low so far | 20957.75 *(said 08:30)* | 20909.00 *(03:02)* | **+48.75** | ❌ MISMATCH |

---

## The pattern, which is the actual finding

> **Every price-only indicator agrees. Every volume-weighted indicator disagrees.**

| | uses volume? | result |
|---|---|---|
| BB basis — mean of 2m closes | no | **agrees to 0.35** |
| Session high — max of highs | no | **agrees to 0.25, and to the minute (08:48)** |
| Daily VWAP, NY VWAP, POC | **yes** | all disagree |

The price series is not in dispute. Two independent price-only readings agree to within a tick,
and the session high agrees on both value *and* the minute it printed. **Whatever is wrong is on
the volume side, not the price side.**

### What was ruled out

Each of these was tested, not assumed:

| hypothesis | result |
|---|---|
| Wrong VWAP anchor | **Ruled out.** Every anchor from 18:00 through 18:04 was swept; the closest is +9.50. No plausible anchor produces 21153.50 |
| Wrong source price (HLC/3 vs close / OHLC4 / HL2) | **Ruled out.** All four sources tested at 1m and 2m; the closest of twelve combinations is still +6.34 |
| Wrong chart timeframe (1m vs 2m aggregation) | **Ruled out.** Moves the value 0.7 pt, not 9.5 |
| A simple time offset (wrong candle) | **Ruled out, and this is the sharp one.** The daily VWAP is rising ~3 pts/min, so his value corresponds to ~09:43. But the NY VWAP would then also read low — and his reads **high**. **The two VWAPs are off in opposite directions, which no single time shift can produce** |
| Back-adjusted / continuous contract | **Ruled out.** Prices would be shifted wholesale; the session high matches to a tick |

### What remains

**A difference in volume between TradingView's feed and the Databento MDP3 archive.** It is the
only candidate consistent with price agreeing, both VWAPs disagreeing in opposite directions,
and the POC being off.

**This is not yet established — it is the surviving hypothesis, and it has one decisive test.**

---

## The decisive test

From the archive, for **2025-01-15**:

| | |
|---|---|
| 09:46 two-minute candle | O 21299.50 · H 21327.75 · L 21295.00 · C 21324.25 |
| **its volume** | **4,279 contracts** |
| session volume 18:00 → 09:47 | **167,043** |
| session volume 09:30 → 09:47 | **62,343** |

If Angus's chart shows materially different volume, that is the answer and the fix is a data
question, not a code question. If the volume matches, the volume hypothesis dies and the cause
is still unidentified.

---

## Field-by-field: which side is more likely right

**Not assuming the detector is correct**, per the brief.

### Session low — 48.75 points apart. Two readings, and one of them is a spec question

- **20909.00 printed at 03:02 ET** and is genuinely in the archive.
- **20957.75 is also a real low** in this session — it prints at 18:04, 20:11 and 05:36 — but
  **not at 08:30**, where Angus placed it. From an 08:30 start the low is 20994.25; from 06:00
  it is 20963.50.

Two readings, and they are not equivalent:

1. **Reading-scope error.** Angus read the low of what was on screen rather than scrolling back
   through the full overnight to 03:02. On a 2-minute chart, 18:00 → 09:47 is ~475 candles.
   **Most likely.**
2. **A genuine difference in what "session low" means.** If, trading live, Angus thinks of the
   session low as the overnight low from around the European open rather than from the 18:00
   Globex open, then **the spec's definition does not match how he trades**, and that is a spec
   finding requiring an amendment — not a reading error to be corrected.

**This needs Angus to say which. It is not resolvable from the data.** The distinction matters
because session extremes are in the target menu, so a different definition moves targets.

### Daily VWAP — 9.50 points, and this one is material

At the strategy's ~10-point cluster tolerance, **a 9.5-point VWAP error is nearly a whole
cluster width**. Clusters that should form would not, and clusters that should not would.
Confluence detection is the first stage of everything downstream.

Cause **unidentified**. Anchor, source and timeframe are ruled out; volume is the surviving
suspect. **Neither side is presumed correct.** My VWAP was verified in Stage 1 against an
independent naive reference and matches the spec's stated definition — but that verifies I
compute what I intended from *my* bars, which is a different claim from computing the same thing
a chart does.

### NY VWAP — 3.07 points

Same cause, smaller because the window is 17 minutes rather than 16 hours. Note the **direction
is opposite** to the daily VWAP's — the fact that broke the time-shift hypothesis.

### POC — 4.00 points

Two contributions, both plausible, not separated:

- **Row size.** TradingView's Session Volume Profile divides the range into a fixed *number of
  rows*; the detector uses fixed **1.00-point** bins (frozen at gate 4, A2 #2, tagged `[FIAT]`).
  Over a ~420-point range a 24-row profile gives ~17.5-point rows, and quantisation alone could
  produce 4 points.
- The same volume difference as above.

**Angus's value is not the no-Replay artefact** — the full-session POC is 21387 and the RTH-only
POC 21355, both far from his 21285. **He read a genuine point-in-time profile.** Good.

---

## Verdict and what it blocks

**PARITY FAILS.** The detector does not reproduce a chart on the volume-weighted half of the
level menu — the half the whole strategy is anchored to.

**Nothing has been adjusted to match.** No parameter was changed, no code touched. This pass
diagnoses; it does not fix.

| | |
|---|---|
| Blocks | spec-1 Step 4 sign-off; pre-registration §10.1 |
| Does **not** block | the sealed workbench result, which stays sealed and unread either way |
| N_trials | **0** |

**Next, in order:**

1. **Volume for the 09:46 candle** from Angus's chart — decides the volume hypothesis outright.
2. **Angus's ruling on "session low"** — reading-scope error, or a real difference in what a
   session is.
3. If volume differs: this becomes a data-source question, and the honest options are to accept
   a known offset with its size recorded, or to reconcile the feeds.

**Still outstanding from the sheet and unrelated to any of the above:** the two judgement calls —
would you have taken this trade, and **where exactly does the stop go**. The second settles open
item 10.2 and no amount of data can substitute for it.

---

# ADDENDUM — the candle OHLC, and a behavioural finding bigger than the parity gap

## 1. Price data: confirmed matching

| | Angus | detector | diff |
|---|---|---|---|
| O | 21299.00 | 21299.50 | 0.50 |
| H | 21327.75 | 21327.75 | **0.00** |
| L | 21295.00 | 21295.00 | **0.00** |
| C | 21324.50 | 21324.25 | 0.25 |

**4 of 4 within half a point, two exact.** Combined with the BB basis (0.35) and the session
high (0.25, same minute), **the price series is settled: it agrees.** Volume remains the only
live suspect for the VWAP gap, and it is still untested — Angus has not supplied a volume figure.

## 2. At 09:48 the detector agrees with Angus: NO TRADE

Angus: *"Way too high for a long, definitely no reason to short either… it had just gone up 141
pts in last 8 minutes."*

The detector fires **nothing** at 09:48 — no trigger on any timeframe, any reading. Checked
explicitly. **The two agree.**

That is a real behavioural match, and it is worth more than the numeric parity would have been
on this minute.

## 3. But the detector's first trade of the day is 12:03 — and Angus sees a setup at ~09:41

On 2025-01-15 the detector produces **19 candidates**, the first at **12:03** (a long). Under A7
first-come, that is the one taken. **Nothing at all between 09:36 and 12:03.**

Angus's chart annotation marks a setup earlier and lower: *"Broke through bollinger band and
displacement candle back inside of it"* — a §4 pattern-B reclaim. That is a setup he says he
would have taken, and the detector took nothing.

**The detector did see it.** Cascade over 09:36 → 10:10, reading A, all timeframes:

| drop reason | candidates |
|---|---|
| **§7 invalidation-at-entry** | **30** (23 long, 7 short) |
| confluence below minimum | 21 |
| no trigger fired | 8 |
| **survived all filters** | **0** |

The long triggers at **09:41, 09:42, 09:44, 09:45** — exactly Angus's window — all fire, and all
die to **§7 invalidation-at-entry**.

## 4. What that filter is actually doing

§7: *"Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand
down. **[Hypothesis — test]**"*

Implemented as: for a long, if the trigger candle's high ≥ NY VWAP +1σ, stand down.

On this session, how often that condition is true, by 30-minute bucket:

| 09:30 | 10:00 | 10:30 | 11:00–12:59 | 13:00 | 13:30 | 14:00–15:59 |
|---|---|---|---|---|---|---|
| 79% | **100%** | 40% | 0% | 33% | 97% | **100%** |

**On a trending day this filter blocks with-trend longs almost entirely.** It only stops firing
during the 11:00–13:00 lull when price returns to VWAP — which is precisely why the detector's
only long is at 12:03, and why everything after 13:00 is a **short on a session that rallied
from 21180 to 21430.**

Stated plainly: **on this day the frozen spec fades a trend.** That is a consequence of a rule
the spec itself marks as an untested hypothesis, and nobody has yet checked it against intent.

## 5. This is a gate-4b finding, not a parity finding

Gate 4b (LITERALISM, added to the runbook this week): *a stated rule frozen to its most literal
reading can produce behaviour the author never intended.* This is the fourth instance, and the
first found by putting the author's own judgement next to the detector's on the same chart.

**Two readings of "opposing ±1σ", and the spec does not disambiguate:**

- **(a) As implemented** — for a long, the +1σ *above*, the band you are moving toward. Rationale:
  if the candle already reaches it, the move is spent. Consistent with Angus's own "way too high
  for a long" at 09:48.
- **(b) The other reading** — for a long, the −1σ *below*, the band that would invalidate the
  setup if price fell back through it.

Reading (a) blocks 30 candidates in a 34-minute window. Reading (b) would block almost none.
**The rule's meaning is worth more than any parameter in the spec, and it has never been
settled.**

**Nothing has been changed.** No filter altered, no parameter touched. This is diagnosis.

## 6. Open questions for Angus, in priority order

1. **Is (a) or (b) what you mean by invalidation-at-entry?** This single answer changes the
   traded population more than anything else outstanding.
2. **The 09:41–09:45 setup you'd have taken — should the strategy take it?** If yes, the
   invalidation rule as implemented is wrong. If no, it is right and 12:03 is correct behaviour.
3. **Volume of the 09:46 candle** — still the decisive test for the VWAP gap. Archive: 4,279.
4. **"Session low"** — reading-scope error, or a genuinely different session definition?
