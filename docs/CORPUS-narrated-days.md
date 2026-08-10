# CORPUS — narrated trading days

The teaching set. One narrated session-day per entry, captured verbatim in
intent and then **reconciled against our own bars and indicators** so the
agent can be scored on the same numbers he traded.

Structured source of truth: `data/narrated_days/<date>.json`.
This file is the human-readable roll-up.

| day | trader label | takes | passes | no-fills | status |
|---|---|---|---|---|---|
| 2026-06-21 | Monday 22 June 2026 | 3 | 2 | 0 | reconciled |
| 2026-06-22 | Tuesday 23 June 2026 | 3 | 1 | 1 | reconciled; profile anchor now known |
| 2026-06-23 | Wednesday 24 June 2026 | 3 | 3 | 1 | reconciled; limit-lifetime rule answered |
| 2026-06-24 | Thursday 25 June 2026 | 2 | 1 (whole window) | 0 | reconciled; weekly profile confirmed |

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

**3. Our Bollinger/VWAP stack is calibrated. The volume profile is close but
not exact.** Day 2 gave the anchor rule and exposed a genuine bug in our own
value-area code; the residual is now ~43pt. See day 2's calibration section.

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

> **Resolved on day 2:** he quotes the **full-target R**, so "3.6 RR" is the
> **3.80R** runner leg, not the 2.96R blended figure.

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

---

## 2026-06-22 — "Tuesday 23 June"

*(He said "Tuesday the 23rd" opening and "Tuesday the 24th" mid-narration.
23 June is the Tuesday and every price checks out on it. London narration is
London local — confirmed to the decimal: he read the 2m BB MA at his
displacement candle's close as **30,008.5**; ours is **30,008.58**.)*

### The read coming in

Asia sold off hard after stalling at all-time highs. A **~400pt New Week
Opening Gap** from last week's open is unfilled and he expects it to fill.
Shorts only — *"I'm not very interested in longs, we're too close to some key
levels."* And *"I want to get an entry as soon as I can."* He anchored the
weekly profile and dismissed it: *"the volume profile levels aren't going to
be too significant today."*

### L1 — LONDON short, 08:22 London / 03:22 NY · TAKEN · **+2.94R**

The build-up is a POC fight, narrated tick by tick: 08:06/08:08 broke the 2m
BB MA and the developing POC; 08:16 displaced back through; 08:18 rejected
the 2m MA; 08:20 touched POC again; 08:22 *"we rejected POC very hard."*

2m candle 03:22–03:23: **O 30,033.50 H 30,033.50 L 29,995.00 C 29,995.75** —
its open sits **on** the POC (30,032.50), and it closes through the 2m BB MA
(30,008.58). The 3m broke its own MA on the same move.

Mid-narration he caught himself and switched order type:

> *"Wait. We're teaching an agent how to trade. You know what? The damn agent
> is gonna be doing limit orders because that's how I fucking trade. Am I
> stupid? Oh sorry for the crash out Claude."*

- **Limit 30,005.5** — MA 30,008.5 less 3pt. He dictated "30,004 5.5"; his own
  arithmetic pins it, since only 30,005.5 gives the 28pt risk, 82pt target and
  2.9R he quotes. **Filled 03:25** — *"filled to the fucking tick."*
- **Stop 30,033.5** = the displacement candle's high, exactly. Never touched.
- **Target 29,923.25** (the 17 June lows) — **hit 03:54**. 82.25pt / 28pt =
  **2.94R** against his stated "2.9R" and "82 point target".

London ran on to 29,776. *"I could have held that basically to the new week
opening gap fill."* No further London entries.

### P1 — NY_PRE, 08:09 · LIMIT PLACED, **NEVER FILLED**

3m candle 08:09–08:11 closed through the 3m BB MA (29,851.86) and VWAP−1
(29,845.05). He limited the retest of VWAP−1 at **~29,839** — *"I had my
limits at about 8:39."*

**Highs after that candle topped out at 29,832.75. It never filled**, and
price ran straight down to fill the gap (pre-market low 29,675.75 against his
~29,685).

This is the first recorded no-fill, and it is the cost of the new grammar
stated plainly: the read was right, the direction was right, and he got
nothing.

### P2 — NY_AM short, 09:33 · PASSED

3m candle 09:33–09:35: **O 29,749.25 → C 29,718.75**, through the 3m MA
(29,729.91) and VWAP−1 (29,732.67). Valid.

> *"There was technically a valid trade there… Why didn't I? Market open, we
> filled the new week opening gap. I want a rebalance now."*

**The thesis completing is itself a reason to stop taking triggers in that
direction.** That is a different pass rule from Monday's (which was level
strength), and worth keeping separate.

### N1 — NY_AM long, 09:38 · TAKEN · **+3.69R**

2m candle 09:38–09:39: **O 29,713.25 → C 29,780.75**, closing through the
developing POC (29,740.50), the 2m MA (29,722.67) and VWAP−1 (29,719.12).
*(He said "VWAP plus one"; the data and his own stop reasoning both make it
minus. Recorded as a slip.)*

- **Limit at the developing POC, 29,741.5** — filled 09:42
- **Stop 29,671** — the bottom of the **09:36** candle, not the displacement
  candle, *"because this candle that displaced through the levels is
  basically exactly where VWAP minus one is — price can absolutely come down
  and reject VWAP minus one before it moves back up."* ~70pt.
- **TP1 29,901**, the pre-market 08:00 high (**ours: 29,900.75**), 75% out,
  hit 09:53 → **2.35R** against his "about a 2.3 to one"
- **TP2 the VWAP middle band**, hit 10:02 → **251 points**, exactly his
  figure → **3.69R**

### N2 — NY_AM short, 10:30 signal / 10:36 fill · TAKEN · **+3.13R**

Rejected the 0.382 of the day's range and touched the VWAP mid, having
displaced through the 15m MA. *"I don't think we're reclaiming much of this
sell-off today. If anything, I'm looking for a continuation."*

2m candle 10:30–10:31: **H 29,998.00** rejects both the VWAP mid (29,992.08)
and the POC (29,989.50), and it closes through the 2m MA (29,962.59).

- **Limit at the 2m MA retest, 29,969** — filled 10:36
- **Stop 30,046**, at the high that rejected the 0.382 — *"the high of this
  candle is around that POC / VWAP middle band level that it's been rejecting
  off of, so I don't feel safe putting that there."* 77pt.
- At 10:38 the 3m also closed through its MA — *"I feel pretty good about this
  trade."* Confirmation **after** entry.
- **Target VWAP−1, taken a couple of points early at 29,728** — hit **11:24**.
  241pt / 77 = **3.13R**

---

## WHAT DAY 2 SETTLES

**The R convention.** He quotes the **full-target R**, not the blended R. N1
is "3RR" (3.69R at the full target, 2.35R at TP1); N2 is "3RR" (3.13R). So
Monday's "3.6RR" was the 3.80R runner leg, not the 2.96R blended figure.
Day 1's open question is closed.

**The weekly profile anchor**, asked and answered:

> *"If I'm trading Monday, I'm gonna anchor it to the Asia Open at the
> beginning of last week. If I'm trading Tuesday, I'm gonna anchor it to the
> Asia Open of Monday night… the last five trading days should be exactly a
> week before, the same day. That's what I anchored it to, and it's
> developing."*

Anchor = **18:00 NY exactly seven days before the session-day's own 18:00
anchor, developing to now.** Now implemented as
`agent_context.anchored_weekly_profile`.

**And that exposed a real defect in our code, not his settings.** Our
`volume_profile` did two things wrong: it dumped each bar's whole volume at
its HLC3 instead of spreading it across the bar's range, and it built the
"value area" from the highest-volume bins *anywhere* in the profile and
returned their min and max. Over a week-long profile that returns something
close to the full range. Both are fixed — the value area now expands outward
from the POC in pairs, so it is contiguous.

| weekly VAH | old | fixed | his |
|---|---|---|---|
| Mon 03:42 | 30,898.75 | 30,756 | 30,713 |
| Mon 10:20 | 30,956.75 | 30,798 | 30,755 |

Error falls from **~+186pt to a consistent +43pt**. The consistency across
two different times of day says we have the right construct with a systematic
offset — most likely row size or tick-level volume distribution. **Not
tuned:** two observations is not enough to fit a parameter, and fitting it
would be the exact mistake this project keeps catching.

### Four new rules, in his words

- **Two levels, always.** *"My entry always needs to be closure through two
  levels. That's usually what I stick by."* Holds on every candidate today.
  N2 closed through the 2m MA while *rejecting* the VWAP mid and POC — so
  **rejection counts toward the pair**, not just closure.
- **Which level to limit at:** *"the closest structural level — what was
  closest to price at that candle close… the last thing it would have broken
  through."*
- **The offset is forward-looking.** *"This candle is closed through, this
  Bollinger Band is probably going to move down. I'm going to give it three
  points of leeway."* He offsets in the direction the MA is travelling,
  because the MA moves before the retest arrives.
- **Stops avoid live levels.** Both NY stops were moved off the displacement
  candle's extreme because that extreme sat **on** a level price was actively
  rejecting. Monday's London stop moved for the same reason. This is one rule,
  not three exceptions.

### Two things that need changing

**The NY_AM window is too tight.** He entered N2 at **10:36** and exited at
**11:24** — his best trade of the day, entirely outside 09:30–10:30. Combined
with January's 10:51 entry, the window needs to run to at least 11:00.

**A no-fill is now a real, logged outcome.** P1 had the right read and the
right direction and produced nothing. Every unfilled limit gets its own row.

---

## 2026-06-23 — "Wednesday 24 June"

Chop. Range-bound all session, failing to break either side. **Two losses
and one win, net ≈ +2.1R** — and by far the most valuable day so far for
*pass* reasoning: three declined candidates in London alone, each for a
different stated reason.

> *"Wow, this shit is fucking horrible price action."*

The fork he set at the open: *"It's either gonna break this range and keep
pushing to the upside, which will be a good thesis for New York… or we're
gonna break and just keep going lower."* And the gate: **"I'm not going to
take anything until I see some higher time frame alignment."**

### The three London passes — three different rules

**LP1, London open (03:00 NY).** 3m closed through the VWAP+1 band and its
BB MA. Passed: *"we're right at developing POC, I don't really wanna take a
short here."* Then — *"Haha, maybe I should have taken a short. We fuckin'
dumped the next candle."* **A pass he immediately regretted.** Kept as-is:
the agent learns the rule, not the outcome.

**LP2, 08:36 London / 03:36 NY.** Touched the 15m MA, the 1h MA and the VWAP
mid; closed through the MA on both 2m and 3m. Passed — chop, and:

> *"We're right at POC now. I'd rather POC be aligned with my trades rather
> than rely on my trade to break through it."*

**LP3, 09:03 London / 04:03 NY** — the important one. The 3m closed through
its MA **and** through POC, so it clears the two-level minimum. Still passed:

> *"Except VWAP+1 is right here. I don't really like taking trades where it
> has to break through something in order for my trade to work. I like a
> couple things to be broken through with some **headroom**."*

**Two levels broken is necessary, not sufficient.** The next level beyond
the entry must not be sitting immediately in the way. That is a genuinely
new constraint and it is not derivable from anything in the previous two
days.

### L1 — LONDON short, 09:49 London / 04:49 NY · **−0.46R**, and a good loss

Rejected VWAP+1, then closed through the BB MA and the developing POC after
rejecting the VAH.

- **Limit 29,821** at the developing POC — ours is **29,821.50**. Filled 04:52.
- **Stop ~29,850**, *not* above the candle that closed through, *"just
  because VWAP+1 is right above it — I want to give it a bit of headroom."*
  Placed at the top wick of the 3m candle before it. 29pt.
- **Trailed hard.** At 10:00 London a big 3m candle wicked the 3m MA and
  traded down; he trailed above that wick to **29,834.25** — 13.25pt.
- Stopped 05:12 for **13.25pt instead of 29**.

His read: *"it looks as though if I didn't trail my stops I might have lost
anyways."* **Verified — the untrailed 29pt stop would also have been hit.**
The trail cost nothing and saved 16 points.

### PRE1 — NY_PRE 08:33 · LIMIT PLACED, **NEVER FILLED** — and it would have won

3m candle 08:33–08:35 closed through its BB MA (29,839.44) and the developing
POC (29,821.50), with its high at 29,844.25 sitting **on** VWAP+1 (29,844.27)
— a rejection, not a closure, which is exactly the case day 2 established
counts toward the pair.

- **Limit 29,821** at the POC retest. **Pre-market high afterwards: 29,814.25.
  Never reached.**
- **Stop 29,860** = the daily VAH (ours **29,860.50**), not the candle high,
  *"purely because that candle is basically at the same level as the
  three-minute moving average and VWAP+1."*
- Target the daily VAL. That is **1.99R** — his *"would have been a 2:1"*.

> *"I could care less. This wasn't a great trade anyway in the first place,
> so I'm not going to be mad about it."*

### N1 — NY_AM long, 09:50 · **−1.0R**

Asia low swept; *"we're probably going to come to the top of this range now."*
The 2m candle 09:50–09:51 closed through **four** levels at once: the
developing VAL (29,695.50), VWAP−1 (29,679.35), the 2m MA (29,718.14) and the
VWAP mid (29,751.97).

His own confidence, stated before the outcome: *"this is technically a valid
trade, but I'm not too confident in it."*

- **Limit at the 2m MA, 29,719.25.** *(He dictated "29,619.25" — a digit slip.
  29,719.25 is the MA, and it is the only value consistent with his stop, his
  target and his stated 1.6R.)* Filled 09:55.
- **Stop 29,657.25** — exactly the displacement candle's low. 62pt.
- **Target 29,820.25**, the POC overlapping VWAP+1 → planned **1.63R**, his
  *"roughly a 1.6 to 1"*.
- **Stopped 10:00.**

### N2 — NY_AM long, 10:24 · **+3.58R**

Same thesis, second attempt. At 10:22 the 2m touched VWAP−1 and left a big
top wick; he waited. *"The 3-minute low-key left a massive top wick. I'd want
to wait for closure through."* — he checked the higher of his two timeframes
before committing.

The 10:24–10:25 2m closed through the developing VAL (29,675.50), VWAP−1
(29,657.62) and the 2m MA (29,667.81).

- **Limit 29,676** at the VAL — *"that's the closest thing to my level."*
  Filled 10:26. *(He calls it the "value area high"; every number he quotes is
  the value area **low**. Naming slip, not a different level.)*
- **Stop 29,639**, just below the 10:24 low (29,639.50). 37pt.
- Touched the VWAP mid → **moved to break-even.**
- **Target 29,808.5**, a point inside VWAP+1 (ours 29,809.49) — **hit 10:45**
  (his "10:44 candle", start-labelled). **3.58R** against his "3.6R".

---

## WHAT DAY 3 SETTLES

**The limit-lifetime question, answered outright:**

> *"A limit will rest for maybe 10 minutes max. If it runs to a structural
> level and then fills me, I'm not very confident in that anymore… I would
> want it to get filled within a couple minutes. If it hits some structural
> levels and then fills me, I'm more likely to lose."*

With a worked example on N2: *"If we were to come to the VWAP middle band
before filling my limit order, I would close that limit order."*

So the rule has two clauses, and the second is the interesting one: **cancel
if price reaches the next structure before the fill arrives.** A late fill is
not the same trade at a better price — it is a different, worse trade. He
never chases.

**Window semantics.** *"You don't flatten trades when the window closes. My
window would be realistically around 10:45. That doesn't mean I flatten
trades. I just can't enter any trades after that."* The window governs
**entries only**. *(Note: January's 10:51 entry sits outside even this.
Flagged, not resolved.)*

**Three new judgment rules**, in his words:

- **Headroom** (LP3) — the next level must not be in the way.
- **POC alignment** (LP2) — POC should be with the trade, not an obstacle.
- **HTF alignment gate** — in chop, stand down until the higher timeframes
  point one way.

**And a management rule with evidence**: trail to beyond the wick of a candle
that rejects your level against you. It cost nothing on L1 and saved 16
points.

### Calibration

**The developing daily profile is now fully calibrated.** Every level he named
today reproduces: POC 29,821.50 vs his 29,821 (quoted twice), VAH 29,860.50 vs
his 29,860 stop, VAL 29,675.50 vs his 29,676 limit, VWAP+1 29,809.49 vs his
29,808.5 take-profit, and both stops sitting exactly on displacement-candle
lows. The only outstanding item remains the **anchored weekly** profile's
+43pt VAH offset.

---

## 2026-06-24 — "Thursday 25 June"

> *"I didn't take any trades in London. I was actually looking for a
> rebalance since it pushed all day. Once I realised it was just straight
> going up there was no good entries anyways — no closure through 2 levels at
> once. Closed through the BB MA multiple times but no other opportunities…
> was just straight pumping."*

A whole-window pass with a **falsifiable mechanical claim** attached, which
makes it the cleanest negative control in the corpus. Built
`scripts/two_level_check.py` to test it rather than take it on trust.

**Was it one-way?** Price held above **both** the 15m and the 1h BB MA for
**100% of the London window**. The deepest approach to the 15m MA came within
**1.09pt and never touched it** — the rebalance he was waiting on genuinely
never arrived.

**Were there two-level closures?**

| | count |
|---|---|
| candles closing through exactly one level | **30** |
| … almost all of them the own BB MA or VWAP+2 alone | — |
| candles closing through 2+ levels, any pair | **3** |
| candles closing through 2+ levels **including their own BB MA** | **1** |

The one is **03:03 3m UP**, through its own MA and the developing VAH — a
**long**, three minutes into the open, in the direction he had already
dismissed. The other two (04:48 3m and 04:50 2m, both down) closed through
VWAP+1 and the VAH but **not their own BB MA**.

**His recollection is mechanically correct under his own grammar.** And the
30-vs-3 split is exactly his *"closed through the BB MA multiple times but no
other opportunities."*

### R13 — the own BB MA looks mandatory, not optional

Checking every take in the corpus:

**9 of 9 takes close through the candle's own BB MA.** The second leg varies
freely — VWAP band, developing POC, VAH, VAL — but the own MA is always
there.

It has real discriminating power here: it is the difference between 3
qualifying candles and 1. Without it, the 04:48/04:50 shorts look like missed
entries and his account looks loose; with it, they are correctly excluded and
his account is exact.

**Caveat, and it matters:** nine takes is a small sample, and this rule is
**inferred from his behaviour, not stated by him**. It is now the default in
`two_level_check.py` (`--any-pair` relaxes it), but it should be put to him
directly rather than assumed. If it is right it is a hard constraint the
agent can lean on; if it is an artefact of three days, leaning on it would
quietly discard valid setups.

### The New York side — an 897-point collapse

**Macro frame, and it checks out.** *"The previous day before market close it
just pumped for the last hour — rallied up fucking 700 points."* The prior
cash session's final hour ran **+581pt net, +608.5pt low-to-close**; from the
15:13 low to the close is **+830.5pt**, and the last three hours net exactly
**+706pt**. His number is right.

### PRE1 — NY_PRE short, 09:03 · **BREAK-EVEN**, and the most instructive row in the corpus

3m candle 09:03–09:05: **O 30,198.00 → C 30,171.50**, through its own 3m BB
MA (30,176.96) and VWAP+1 (30,172.23).

- **Limit 30,172.5 at VWAP+1** — ours reads 30,172.23–30,172.45 across the
  next three minutes. Filled 09:06.
- **Stop 30,202.5**, above the displacement candle's high of 30,201.75 —
  0.75pt of clearance. His *"30-point stop"*, exactly.
- **Target the VWAP middle band** (30,098.71) → a planned **2.45R**.
- **Moved to break-even for the cash open:** *"open volatility can cook you
  even if ur thesis is wrong."*

**Break-even hit at 09:30** (first-30-min high 30,193.00). Then the market
fell to **29,295.75** by 09:59. His target was hit at **09:31**.

**Had he held: 29.2R was available.**

> *"Wow, it would've obliterated take profit on open — but that's straight
> gambling for me."*

A disciplined de-risk immediately before a volatility event cost a 2.45R
planned trade that ran to twenty-nine, and he does not flinch. **The rule is
the rule; the outcome is not the teacher.** Any scoring that penalises this
decision is scoring the wrong thing.

### N1 — NY_AM long, 10:18 · **WIN**, ~180pt

After the collapse, price traded down near VWAP−3. *"We're clearly bearish"* —
so this is a **counter-trend rebalance**, not a reversal, and it is sized
accordingly: *"it's not going for a big target or anything."*

2m candle 10:18–10:19: **O 29,535.25 → C 29,612.25**, through VWAP−1
(29,584.63) and the 2m BB MA (29,563.94).

- **Limit at VWAP−1** — *"that's obviously the closest structural level."*
  Filled on his 10:22 candle (our 10:23).
- **Near-stop by two points**: the lowest low after the fill is **29,524.00**
  at 10:24, putting his stop around 29,522. Worth noting this is **not** the
  displacement candle's low (29,488.00), which was never approached within
  36pt — so the stop is inferred, not stated.
- **Target "the value area low" — taken at ~29,774 at 10:52.**

### That target confirmed the weekly profile

The **daily** VAL at 10:52 was 29,609.50, and price had already crossed it at
10:26 — exiting there would have been 30–45 points, not 180. The level he
actually used was the **anchored weekly** VAL:

| | ours | his |
|---|---|---|
| awVAL at 10:18 | **29,778** | — |
| awVAL at 10:52 | **29,768** | exit ~**29,774** |

**Second independent confirmation of the weekly profile, and the first on the
VAL edge.** Combined with the anchor rule he gave on day 2, the construct now
looks right. It also suggests the earlier **+43pt VAH residual** may be partly
his habit of placing take-profit a few points *inside* a level rather than at
it — a candidate explanation, not an established one.

**Operationally:** when he says "value area", check **both** the developing
daily profile and the anchored weekly one. They were 165 points apart here.

### Three more rules

- **R14 — no entries before high-impact news.** *"Obviously we're not trading
  before high-impact news. That is stupid."* A hard constraint, and the first
  concrete job for the macro/events agent.
- **R15 — move to break-even before the cash open** when carrying a pre-market
  position. Applied here at a cost of ~29R and endorsed afterwards.
- **R16 — target size scales to direction.** A counter-trend rebalance gets a
  modest target by design.

**R13 update:** now **11 of 11 takes** close through the candle's own BB MA.
Still inferred rather than stated, and still needs putting to him.

> *"Some days the price action is not good. You're not taking as many trades
> when you know how to trade."*

Which is what the day shows: a whole-window London pass and a pre-market
break-even, both correct process, on a session that offered one clean trade.
