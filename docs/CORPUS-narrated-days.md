# CORPUS — narrated trading days

The teaching set. One narrated session-day per entry, captured verbatim in
intent and then **reconciled against our own bars and indicators** so the
agent can be scored on the same numbers he traded.

Structured source of truth: `data/narrated_days/<date>.json`.
This file is the human-readable roll-up.

| day | trader label | takes | passes | status |
|---|---|---|---|---|
| 2026-06-21 | Monday 22 June 2026 | 3 | 2 | reconciled; profile levels unresolved |

---

## THREE CONVENTIONS ESTABLISHED ON DAY 1

These bite every future day, so they are stated once here.

**1. TradingView labels candles by START time.** His *"9:46 two-minute
candle"* spans 09:46–09:47 and closes at 09:48. Our census right-labels by
close time. Every narrated time needs **+TF minutes** to reach our label.
Verified three independent ways on this day (03:39/3m, 09:46/2m, and his own
explicit *"open at 10:15 with a close at 10:18"*).

**2. His trading day is our previous session-day.** Our session-day is the
18:00 NY anchor date, so his *"Monday 22 June"* cash session lives in
**session-day 2026-06-21**. Getting this wrong makes `prev_day_levels`
return the current day's own extremes — it looks like lookahead and isn't.

**3. Our Bollinger/VWAP stack is calibrated. Our volume profile is not.**
See the calibration section at the end.

---

## 2026-06-21 — "Monday 22 June"

### The read coming in

Asia opened up, sold off, has trended up since. Previous day's high already
swept. **Thursday 18 June stalled at this level and it has not been broken**
(verified: Thu-18 session high 30,783.25; price at the London open 30,765).
Trading heavy into **VWAP +2**, and on the anchored volume profile *"at the
very top of the weekly range — we're topping out this range."*

Bias: **not inclined to longs** unless a rebalance to the 15m or 1h presents
itself; **more inclined to shorts**. Waiting on the reaction at the 18 June
highs.

Macro frame, in his words: April–May was a bullish pump on the ceasefire and
strong earnings (he names NVDA), and into late June *"it was just a given
that we were gonna keep going up"* — so he is trend-following, not fading.
He is not fading here either; the shorts are rebalance trades inside an
uptrend, taken at the top of a range.

### L1 — LONDON short, 08:42 London / 03:42 NY · TAKEN

3m candle starting 03:39 NY: **O 30,772.00 H 30,772.00 L 30,752.50
C 30,752.50**. It closed through its own 3m BB MA (30,756.58) **and through
VWAP +2** (30,765.03) — and the 2m closed through its MA (30,768.01) on the
same move, exactly as he described.

- **Entry** 30,753 market (our 03:42 bar opens 30,754.00)
- **Stop** at the Thursday-18 high, **not the candle high** — *"the candle's
  very close to the weekly high, and we might retest it"*
- **TP1** weekly VAH 30,713, 75% out — hit on the 3m candle starting 04:09
  (its low ran to 30,698.00)
- **Runner** targeted VWAP +1 (30,678.33). London low after entry was
  **30,687.25** — missed by ~9 points, remainder taken out at break-even.
  His call: *"It got very close to VWAP +1, but I wouldn't have hit."* ✓

> **Open:** he said *"stops at 30"* and the sentence cut off. 30,783 (the
> Thu-18 high) fits his rationale and his *"bit of a big stop"* remark, but
> it is inferred. R for this trade is provisional until confirmed.

### P1 — NY_PRE, whole window · PASSED

*"I did not like anything in pre-market. Nothing was really piecing together
for me."* The 07:00 NY rally put a big wick through the 15m Bollinger band
and dumped straight back; still stalling at the top of the range.

### P2 — NY_AM short, 09:42 NY · PASSED ← the boundary row

3m candle from 09:42: **O 30,842.75 → C 30,790.00**, closing through the 3m
BB MA (30,837.15) **and** VWAP +1 (30,832.75). **Mechanically valid, correct
direction for his standing bias, and he declined it.**

Why: the developing **daily value area high** was sitting right there and
price had stalled around the value area highs all day — it wicked around them
at the open before pumping back. Plus the 07:45 15m was a good rejection
candle, so it could keep going up. *"I'd be okay with taking shorts with some
extra confirmation here."*

This is the single most valuable row on the day: a valid trigger in his own
direction, passed on a discretionary read of level strength.

### N1 — NY_AM long, 09:46 NY · TAKEN, and self-criticised

2m candle from 09:46: **O 30,822.50 → C 30,873.75**, closing through the 2m
BB MA (30,846.58) and **VWAP +1** (30,836.20), off a rejection of the
developing daily VAH.

- **Entry** 30,873 market (= the trigger candle's close)
- **Stop** 30,818 — the **bottom of the body**, not the wick (body bottom
  30,822.50, so ~4.5pt clearance). 55pt risk. *"I don't like how big the
  stop is."*
- **Target** 1:1 at 30,928, which is also the 09:40 high (30,926.75). Hit at
  09:58. **+1.0R**

**His own critique, and it checks out:** he should have limit-ordered the
**retest at 30,851**. That fills around 09:54 (lows 30,843.75 / 30,842.50),
keeps the same 30,818 stop for **33pt of risk** against the same target —
**2.33R instead of 1.0R**. His *"that would have been an easy 2:1"* is
arithmetically right.

### N2 — NY_AM short, 10:15 NY · TAKEN — the model trade

3m candle from 10:15: **O 30,909.75 H 30,911.75 L 30,848.00 C 30,855.25**,
closing through the 3m BB MA (30,878.96) **and** VWAP +1 (30,887.06).

> *"For my trade to invalidate, it has to break through this 3-minute
> Bollinger Band and VWAP +1, and that's a double anchor right there."*

- **Entry: LIMIT 30,878 on the retest of the 3m BB MA** — the MA was at
  30,878.96, and *"I usually like to give it a couple points from where it
  actually is."* Filled on the 10:18 bar (high 30,888.00).
- **Stop** 30,913.5, just above the displacement candle high (30,911.75).
  **35.5pt risk** — against 55pt on the market-entry trade an hour earlier.
- **TP1** the 15m BB MA at ~30,783 (ours: **30,786.94** — his *"around
  30,787"*), 75% out, hit 10:27 → **2.68R**
- **TP2** the VWAP middle band at 30,743, hit 10:30 → **3.80R**

**Target selection is explicit reasoning about level clustering:** the weekly
VAH sat ~30,759 and the VWAP mid ~30,743, fifteen points apart. *"Price never
touches a value area high and then just runs straight from it. It usually
wicks around, and with VWAP right there, I'm inclined to believe it would
touch VWAP."* So he took the further of the two.

> **Open:** he calls this **3.6 RR**. Blended, 0.75 × 2.68 + 0.25 × 3.80 =
> **2.96R**; the runner leg alone is **3.80R**. Which convention gives 3.6?
> It matters for scoring.

Price ran to 30,540 by noon. Recorded as fact, not as a criticism of the exit.

---

## WHAT DAY 1 CHANGES IN THE DESIGN

**C1 — entry grammar becomes limit-on-retest.** *"If we're teaching an agent
to trade a trade like me, we're going to start taking fucking limit orders."*
The trigger candle stops being the entry bar and becomes the **signal** bar;
the level it displaced through (the BB MA) becomes the **entry price**. Same
day, same setup, the difference is 1.0R vs 2.33R.

This introduces a failure mode the market-entry grammar didn't have: **no
retest, no fill, no trade.** Needs a declared rule — how long the limit rests,
and whether it is ever chased. Unanswered.

**C2 — passes get narrated too.** Already delivering: P2 is a valid trigger
in his own direction that he declined, which is exactly the discrimination
the agent has to learn.

**C3 — a macro/events agent joins the stack.** Reads recent events affecting
the NASDAQ and its big constituents. Constraint, in his words: *"I don't want
an agent that's gonna be too worried about things… it's important that the
agent is acting."* It informs bias; it does not hold a veto.

---

## CALIBRATION STATUS AFTER DAY 1

**Matched — trust these:**

| level | ours | his |
|---|---|---|
| 3m BB MA | 30,878.96 | 30,878 limit |
| 15m BB MA | 30,786.94 | "around 30,787" |
| 2m BB MA | confirmed at both 2m triggers | — |
| VWAP mid / +1 / +2 | confirmed at every trigger candle | — |
| prev-day VAH | 30,755.25 | ~30,755 NY target |
| bar OHLC | every quoted price within ~1pt | — |

After the BR-106 source fix, the Bollinger/VWAP stack reproduces his chart
well inside a tick on the 15m MA. That materially de-risks the MCP parity
gate.

**NOT matched — the volume profile.** His *"weekly value area high"* is
**30,713 in London** and **~30,755 in New York** — 42 points apart on the
same day. Our candidates: 5-day-rolling wVAH **30,898.75**, wPOC
**30,718.75**, prev-day VAH **30,755.25**. A developing-from-Monday anchor
and a 5-day rolling anchor were both tested; neither reproduces the pair.
Anchor, value-area %, bin width and volume-vs-TPO are all unknown.

**Until that is settled, our profile levels must not be substituted for his** —
and two of his three trades took TP1 at a profile level, so this is
load-bearing, not cosmetic.
