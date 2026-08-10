# OPERATING SPEC — the local TradingView replay agent

For the Claude Code session running **on the trader's desktop** with the
`tradingview` MCP attached. Setup: `docs/SETUP-tradingview-mcp.md`.
Architecture and rationale: `docs/ARCHITECTURE-trading-agent.md`.

## THE CHART IS THE SOURCE OF TRUTH

Read every level, band and MA **off the chart via the MCP**. Do not
reconstruct them and do not substitute the research values. This is the
whole point of the MCP route: it removes the calibration debt that
scuppered the offline approach.

Calibration already known, for cross-checking only — never as a
substitute:
- VWAP: source **open**, anchored at the **18:00 session start**;
  bands are VWAP ± k·σ. Known because the trader read it off his own
  TradingView config — not fitted. The reconstruction sits 0.10pt from
  the chart on the one bar available to check, but so do hlc3/ohlc4/
  close on that bar (whole spread 0.08pt), so **that check confirms
  nothing about the source**. Across the windows the sources diverge by
  a median 0.72pt (~3 ticks) and a p95 of 1.5pt — enough to flip a
  borderline "closed through" call, which is why the chart wins.
  Details and the population measurement: `docs/FINDINGS-vwap-calibration.md`.
- BB: **20, 2, SMA on close**, per timeframe. Reconstruction matched the
  chart to 0.01pt on three checks.
- Session-day runs 18:00 → 17:00 NY.

## PHASE 0 — GATES, BEFORE A SINGLE DECISION IS RECORDED

Run these every session. If any fails, stop and report; do not trade
through a failed gate.

1. **Symbol and timeframe.** Confirm the chart is on the intended
   contract and TF. Log it.
2. **Timezone.** Read the chart's displayed time for a known bar and
   reconcile to NY. The trader's exports were UTC while his charts were
   per-session local — assume nothing.
3. **Indicator parity.** Read VWAP, VWAP±1, and the BB MA at one known
   minute; compare against `scripts/agent_context.py` values for the
   same minute. Report the deltas. >1pt on VWAP or >0.5pt on the BB MA
   means the chart config differs from the research build — say so
   rather than proceeding quietly. *(Bollinger and VWAP reconcile to
   ~1pt or better against his narrated levels on both 2026-06-22 and
   2026-06-23 — including a 2m BB MA he read as 30,008.5 against our
   30,008.58.)*

   **Volume profile — partially calibrated.** The **developing daily
   POC** matches exactly (29,740.50 vs his 29,741.5 limit). His
   **anchored weekly** profile is anchored to 18:00 NY exactly seven
   days back and develops from there — implemented as
   `agent_context.anchored_weekly_profile`. Its VAH still sits a
   consistent **+43pt** from his reading, so read weekly profile levels
   off the chart; ours are for orientation only.
4. **NO-LEAK CHECK — the one that matters most.** Step replay to a
   decision minute, screenshot, and verify no bars exist after it. A
   decision made on a chart showing later bars is worthless and the
   error is invisible in aggregate. Re-verify after every replay jump.

## PHASE 1 — THESIS (per session-day, and on events)

Fire at each window open, **and** whenever a material structural event
occurs — a session/prior-day/weekly extreme is taken out, a 15m close
through the BB MA, a displacement beyond ~0.5·W15, an awaited rebalance
completing, or TP1 filling. Bias flips intraday; do not hold a stale
view. (The trader: *"London I was inclined to sells, then New York I'm
more inclined to longs, then this happened and I'd rather shorts now."*)

Read before deciding: daily and 1h structure; prior-day VAL/VAH/POC and
high/low; the **weekly (5-day anchored) profile** — weekly VAL and
weekly lows are live targets for him; Asia's character; where price sits
in the multi-day range; the NY-range fibs once 10:00 NY has passed.

Emit, as structured JSON, and log it:
```
{ "bias": "long|short|stand_aside",
  "targets": [ {"level": "...", "price": 0.0} ],
  "invalidation": {"level": "...", "price": 0.0},
  "waiting_for": "e.g. rebalance to the 15m MA | nothing",
  "reasoning": "2-4 sentences" }
```

## PHASE 2 — TRIGGER ADJUDICATION

A candidate exists when a **2m or 3m candle closes through its own
BB(20) MA and through a VWAP band**. Watch for it on the chart; do not
rely on the precomputed census — it is a research artifact built on
slightly different indicator values and it is known to miss real
entries.

**TWO LEVELS, ALWAYS.** *"My entry always needs to be closure through two
levels. That's usually what I stick by."* A single closure is not a
candidate. The pair can be any two of: its own BB MA, a VWAP band, the
developing POC, a profile edge — and **a rejection counts toward the
pair**, not only a closure (2026-06-23 N2 closed through the 2m MA while
rejecting the VWAP mid and the POC).

**The trigger candle is the SIGNAL bar, not the entry bar.** Entry is a
**limit order on the retest**, placed a couple of points inside the
level. Declared 2026-08-10: *"the damn agent is gonna be doing limit
orders because that's how I fucking trade."* On 2026-06-22 the same NY
setup was worth 1.0R at market and **2.33R** on the retest, identical
stop and target.

- **Which level?** *"The closest structural level — what was closest to
  price at that candle close… the last thing it would have broken
  through."* Not always the BB MA: on 2026-06-23 it was the developing
  POC once and VWAP−1 once.
- **The offset is forward-looking.** Offset in the direction the MA is
  **travelling**, because it keeps moving while the retest is pending:
  *"this candle is closed through, this Bollinger Band is probably going
  to move down, I'm going to give it three points of leeway."*

Consequence the market grammar did not have: **no retest means no fill
means no trade.** It is a real outcome, not an edge case — 2026-06-23's
pre-market limit had the right read and the right direction and produced
nothing. **Log every unfilled limit as its own row.** How long the limit
rests, and whether it is ever chased, is still not declared.

**Candle times are START times on his chart.** A "09:46 2m candle" spans
09:46–09:47 and closes at 09:48. Our census right-labels by close time.
Off-by-one here silently mismatches every decision.

**Hard constraints — a candidate failing any of these is passed with
the reason logged, no judgment required:**
1. Direction must match the standing thesis. (He declined a valid 10:12
   long outright: *"I don't even like this long."*)
2. Inside a window: LONDON 03:00–04:59, NY_PRE 08:00–09:29, **NY_AM
   09:30–11:00** NY. The old 10:30 cut-off is wrong: on 2026-06-23 his
   best trade of the day entered at **10:36** and exited 11:24, and
   January's best was 10:51. 11:00 is his own stated historical cut-off.
3. Not in the first few minutes of the cash open.
4. If a displacement is awaiting a rebalance to the 15m MA, stand aside
   until it happens.
5. A thesis alone is never enough — the trigger must exist. *"I know
   it's going down, but there's no entry to back that up."*

**Conviction inputs, recorded and weighed, NOT hard filters:**
- 2m and 3m closing through their MAs **in the same minute** — named
  twice, unprompted, as a thing he actively looks for
- POC + BB MA + a VWAP band in the **same candle**
- proximity to weekly VAL/VAH, prior-day levels, or a NY-range fib
  (0.618 set up his 10:28 short)

**Stop placement — do not reach for the trigger candle's extreme by
default.** He is
explicit that it stops him out on trades that work; on 2026-01-14 the
candle stop would have killed both London entries. Place it beyond the
structure the thesis rests on, with clearance. On an oversized
displacement candle use the **body**, not the wick: *"if it came for
that wick area I'd be getting stopped out anyway, so I may as well save
my stops."* Note: mechanically widening stops is EV-neutral in R — the
gain comes from placing them where invalidation actually lives.

The rule is **place it where the thesis dies, then add a couple of
points of clearance** — which cuts both ways. On 2026-06-22 the London
short went *wider* than the candle (out to the Thursday high, because the
candle high sat too close to the weekly high to survive a retest), while
the 10:15 NY short went **just above the signal candle's high**, because
there the candle high *was* the invalidation: it is where price would
have to reclaim both the 3m BB MA and VWAP +1. *"That's a double anchor
right there."* Read the level, not the candle.

**The specific test: does the candle's extreme sit ON a live level?** If
it does, the stop goes beyond that level instead, because price can go
touch it and come back. Three instances, one rule: 2026-06-22 London
(candle high near the weekly high); 2026-06-23 N1 (candle low sat exactly
at VWAP−1 — *"price can absolutely come down and reject VWAP minus one
before it moves back up"*); 2026-06-23 N2 (candle high sat at the
POC/VWAP-mid it had been rejecting off — *"I don't feel safe putting that
there"*). When the extreme is clean, use it.

**Targets** are pre-identified structure from the thesis, not fixed R
multiples. His realised distribution sits at **1.5–2.5R**; beyond ~3R
the raw population's fixed-target EV decays.

**When two levels cluster, take the further one.** *"Price never touches
a value area high and then just runs straight from it. It usually wicks
around, and with VWAP right there, I'm inclined to believe it would
touch VWAP."* On 2026-06-22 the weekly VAH and the VWAP mid sat 15pt
apart and he targeted the VWAP — worth 3.80R on the runner instead of
~3.4R.

**Take profit sits a couple of points SHORT of the target band** —
*"I usually keep my take profit a couple points away from the VWAP
band."* On 2026-06-23 that was 29,728 against a VWAP−1 of 29,721.

**Management:** partial at intermediate structure; move to break-even
after TP1.

**R is quoted at the FULL target, not blended across the partials.** His
"3RR" on 2026-06-23 N1 means 3.69R at the final target, with TP1 at
2.35R. Score both, but report his convention when comparing to him.

Emit per candidate:
```
{ "decision": "take|pass", "reason": "...",
  "entry_type": "limit_retest|market", "entry": 0.0,
  "retest_level": "bb_ma_3m", "filled": true,
  "stop": 0.0, "stop_rationale": "...",
  "targets": [0.0], "conviction": "A|B|C",
  "constraints_failed": [] }
```

## THE AGENT STACK

Three roles, not one. Separating them is what lets a disagreement be
attributed rather than just observed.

1. **Macro/events agent.** Recent events bearing on the NASDAQ and its
   large constituents — earnings, policy, geopolitics. Feeds Phase 1
   bias. **It informs; it does not hold a veto.** Declared constraint:
   *"I don't want an agent that's gonna be too worried about things…
   it's important that the agent is acting."* An events read that only
   ever counsels caution is a failed component, not a safe one.
2. **Thesis agent** — Phase 1 above.
3. **Trigger agent** — Phase 2 above.

## PHASE 3 — LOGGING (non-negotiable)

Every candidate, taken or passed, with its full payload, to
`output/agent_runs/<date>.jsonl`. **The passes are the valuable rows** —
they define the boundary, and boundary is where the discrimination
lives. A run that logs only its trades is close to worthless for
teaching.

## PHASE 4 — SCORING

- **Agreement** with the trader's own fills: take/pass confusion matrix
  per window and per day.
- **Outcome**: do its picks reproduce the effect his do — median run and
  P(2R) against a same-day baseline of all candidates that day,
  permutation-calibrated.
- **Both are required.** High agreement whose picks do not run means the
  agreement is cosmetic. Good outcomes with wholesale disagreement is a
  different strategy, and must be labelled as such, not as "trades like
  him".

Benchmarks measured on his real January fills: 42 decisions over 14 days
(**3.00/day**), **67% win rate**, avg win +1,336 vs avg loss −800 USD,
net **+26,218**.

On the outcome axis, the bar is **in-window P(2R) ≈ 55%** against a
same-day in-window baseline of **≈36%** (median run 2.02R vs 1.20R),
measured with a *causal* match — the trigger must have closed at or
before the entry minute — over 2m+3m triggers. **His own 20 matched
picks clear that bar only at p ≈ 0.07**, so one month cannot settle it
for the agent either; the sample has to be widened first.

*(The previously quoted "5.48R vs 1.15R, beaten by 0.17% of 20,000
permutations" is withdrawn — the matcher had lookahead and the two halves
came from different populations. `docs/FINDINGS-selection-effect.md`.)*

## DISCIPLINE

Replay and practice orders only. No live orders under any
circumstances until scoring has been run and reviewed with the trader.
