# ARCHITECTURE — the trading agent

2026-08-08. Design agreed with the trader after two full narrated days
(2026-01-14 London and New York) and a month of his real backtest fills.

## WHY AN AGENT AT ALL — the evidence, not a preference

Mechanization was tried exhaustively and failed on **selection**, and he
demonstrably makes money doing it by hand:

- **He makes money.** 42 real January decisions over 14 days (3.00/day),
  **+26,218 USD, 67% win rate**, avg win +1,336 vs avg loss −800.
- **His trigger selection is suggestive but NOT established.** Corrected
  2026-08-10: of the in-window 2m/3m triggers he took (22 of 42 fills
  match, causal), median run **2.02R vs a same-day in-window baseline of
  1.20R**, P(2R) **55.0% vs 36.3%** — a +18.7pp lift stable across every
  matching tolerance, at **permutation p ≈ 0.07**, n = 20. Suggestive,
  underpowered, not proof. **The earlier "5.48R vs 1.15R, beaten by 0.17%
  of 20,000 permutations" is WITHDRAWN** — the matcher allowed a candle
  closing *after* his entry to count as his selection, and the two halves
  of the ratio came from different populations. See
  `FINDINGS-selection-effect.md`; reproduce either reading with
  `scripts/trader_selection_effect.py`.
- **No mechanical proxy reproduces it.** Rejected individually: 111
  decision-time features (univariate, calibrated null), 8,721
  pair/triple combinations (best beaten by 9 of 10 shuffled searches),
  a full multivariate classifier (AUC 0.522 vs 0.501 null), stop width
  (a blanket structural stop is neutral-to-worse in R), seven direction
  proxies (all flat or negative), previous-day level proximity (null).

The conclusion is not "there is no signal" — it is that whatever he is
doing has no mechanical proxy, and the working hypothesis is that it is a
**conjunction reasoned as a narrative**, which is LLM-shaped work. That is
a hypothesis the agent is built to test, not a finding. His
own Jan-14 read chained: Asia choppy → 04:00 displacement through the
15m BB MA → prev-day VAL rejected hard yesterday → can't close back
above it on the 2m → at VWAP−1 → 15m prints a rejection wick. No
component is predictive alone; the story is.

## THE SPLIT: mechanize constraints, delegate judgment

**Mechanical (hard, coded, cheap).** These shrink ~9 in-window
triggers/day to a small adjudication set before any token is spent:

1. Trigger exists: a 2m or 3m candle closes through its own BB(20) MA
   **and** a VWAP band. (2m and 3m are deduplicated so the same move is
   not counted twice.)
2. Inside a window: LONDON 03:00–04:59, NY_PRE 08:00–09:29, NY_AM
   09:30–10:30 NY. *(Under review — his best January trade was 10:51,
   and the raw hour histogram is flat into 11h–12h.)*
3. Direction must match the standing thesis. He declined a valid 10:12
   long outright: *"I don't even like this long."*
4. Not in the first few minutes of the cash open (*"I don't like the
   heavy volatility from the first few minutes"*).
5. After a displacement, no entry until the 15m rebalance has occurred
   (*"I'm not taking anything until price reaches the 15m MA"*).
6. Trigger required even with a strong thesis (*"I know it's going
   down, but there's no entry to back that up"*).

**Recorded as conviction inputs, not filters:** simultaneous closure
across 2m and 3m, and closure through POC + BB MA + VWAP band in the
same candle — he named this twice as what he actively looks for.

**Judgment (agent).** Directional bias, whether *this* rejection
matters, whether the confluence is meaningful here, which target,
where the stop belongs, when to move to break-even.

## TWO TIERS, WITH EVENT-DRIVEN RE-EVALUATION

**Tier 1 — thesis agent.** Not set-and-hold. The trader is explicit
that bias can flip within a day ("London I was inclined to sells, then
New York I'm more inclined to longs, then this happened and I'd rather
shorts now"). So it fires:

- at each window open, and
- on **material structural events**, which are mechanically detectable:
  a session or prior-day/weekly extreme is taken out; a 15m close
  through the BB MA; a displacement beyond a set size; the completion
  of an awaited rebalance; TP1 filling.

Output (structured): direction bias (long / short / stand aside),
primary and secondary targets, the level that invalidates the view,
and **what it is waiting for**.

**Tier 2 — trigger agent.** Fires only at surviving mechanical
triggers. Sees the chart screenshot truncated at the decision minute,
the numeric state, and the standing thesis. Outputs take/pass, stop,
target, and a one-line reason. May flag `thesis_stale` to force a
Tier-1 re-read before adjudicating.

Separating them is what makes the teaching loop converge: a
disagreement can be attributed to a bad thesis or to bad adjudication
of a good thesis.

## WHAT THE AGENT MUST SEE

The MCP screenshots his **actual chart**, which removes the need to
rebuild his view from bars — strictly better, since it carries his own
indicator settings and drawings. Required on the chart or in the
numeric payload:

- 2m/3m/15m/1h panes; BB(20) MA on each; VWAP + deviation bands
- developing POC / VAH / VAL; **previous-day** VAL/VAH/POC/high/low
- **weekly (5-day anchored) volume profile** — he trades off weekly VAL
  and weekly lows; absent from the research build
- **NY-range fibs** (session high→low, the 0.618 in particular) — set
  up his 10:28 short; absent from the research build
- rebalance state (has price returned to the 15m MA since displacing)

## VALIDATION — the part that stops self-deception

1. **Agreement** with his 42 January decisions: take/pass confusion
   matrix, per window and per session-day.
2. **Outcome**: in-window P(2R) against the same-day in-window baseline
   (~36%), permutation-calibrated. His own matched picks sit at 55.0%,
   p ≈ 0.07 — so **one month cannot resolve this for the agent either**,
   and the sample has to be widened before the outcome axis can rule.
3. **Both are required.** 80% agreement whose picks do not run means the
   agreement is cosmetic. Outcomes that beat baseline while disagreeing
   with him wholesale is a different (possibly better) strategy, and
   must be labelled as such rather than as "trades like him".
4. **No-leak gate**: replay screenshots must contain no bars after the
   decision minute. Verify before trusting a single decision.

## THE TEACHING LOOP

Every disagreement is surfaced: trades it took that he passed, and his
trades it passed. He gives the reason; the reason becomes prompt
refinement. **Passes are worth more than winners** — they define the
boundary, and the boundary is where all the discrimination lives.

Known risk: an agent prompted on his reasoning inherits his blind spots
and will confabulate plausible reasons when guessing. The guard is
scoring against outcomes, not agreement alone.

## REALISTIC CEILING

An imitator cannot out-judge its teacher on the same information. It can
beat him on execution: no misclicks (his January export contains 14),
never missing a window while watching another, and never deviating from
his own rules through boredom or impatience. "Same judgment, perfectly
executed" is the honest target; anything beyond that has to come from
information he isn't using.
