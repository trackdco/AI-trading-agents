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
   rather than proceeding quietly. *(Bollinger and VWAP already
   reconcile to ~1pt or better against his narrated 2026-06-22 levels.)*
   **The volume profile does NOT reconcile** — his "weekly value area
   high" landed 42pt apart at two points of the same day and matches
   none of our anchors. Read profile levels off the chart only; never
   substitute ours. Settle anchor / value-area % / bin width / TPO-vs-
   volume before relying on any of them.
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

**The trigger candle is the SIGNAL bar, not the entry bar.** Entry is a
**limit order on the retest** of the level the candle displaced through
— normally its own BB MA — placed a couple of points inside it. Declared
2026-08-10: *"If we're teaching an agent to trade a trade like me, we're
going to start taking fucking limit orders."* On 2026-06-22 the same NY
setup was worth 1.0R entered at market on the close and **2.33R** entered
on the retest, identical stop and target. See
`docs/CORPUS-narrated-days.md`.

Consequence the market grammar did not have: **no retest means no fill
means no trade.** How long the limit rests, and whether it is ever
chased, is not yet declared — log every unfilled limit as its own row.

**Candle times are START times on his chart.** A "09:46 2m candle" spans
09:46–09:47 and closes at 09:48. Our census right-labels by close time.
Off-by-one here silently mismatches every decision.

**Hard constraints — a candidate failing any of these is passed with
the reason logged, no judgment required:**
1. Direction must match the standing thesis. (He declined a valid 10:12
   long outright: *"I don't even like this long."*)
2. Inside a window: LONDON 03:00–04:59, NY_PRE 08:00–09:29, NY_AM
   09:30–10:30 NY. *(11:00 was his older cut-off; treat as configurable
   and log any candidate that only fails on this.)*
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

**Targets** are pre-identified structure from the thesis, not fixed R
multiples. His realised distribution sits at **1.5–2.5R**; beyond ~3R
the raw population's fixed-target EV decays.

**When two levels cluster, take the further one.** *"Price never touches
a value area high and then just runs straight from it. It usually wicks
around, and with VWAP right there, I'm inclined to believe it would
touch VWAP."* On 2026-06-22 the weekly VAH and the VWAP mid sat 15pt
apart and he targeted the VWAP — worth 3.80R on the runner instead of
~3.4R.

**Management:** partial at intermediate structure; move to break-even
after TP1.

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
