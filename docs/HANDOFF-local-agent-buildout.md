# HANDOFF — to the local session building the TradingView agent

**Read this first.** You are picking up a project mid-flight. This document
is the whole context; the linked docs are the detail.

Branch: `claude/hello-zfmoq6`. Everything referenced here is committed.

---

## WHO YOU ARE WORKING WITH, AND HOW HE WORKS

A discretionary NQ futures trader running Lucid prop accounts. He hand-trades
three windows a day off a TradingView chart. He is not a beginner and he is
not vague — over a narrated week, **every single price he quoted from memory
reconciled against the tape**, including a 2-minute Bollinger MA he read as
30,008.5 against a computed 30,008.58.

**Standing rules that have already prevented real errors:**

- **When his description of his own process conflicts with a chart, a
  screenshot, or your reconstruction — what he says wins, and the artefact
  gets re-checked.** This has been invoked and was correct both times.
- He wants findings written to `.md` and delivered, not just narrated in chat.
- He does not want work quietly narrowed or numbers quietly fitted. Several
  results in this repo were **withdrawn** after re-derivation; that is normal
  and expected, not a failure.
- Blunt is fine. Hedging and over-explaining are not.

---

## THE OBJECTIVE

**Build an agent that trades the way he does, driven through TradingView
Replay over MCP, so he can watch it decide in real time.**

Not a signal generator. Not a backtest. An agent that reads his actual chart,
forms a thesis, adjudicates triggers, places limit orders, and logs every
decision including the ones it declines.

---

## WHY AN AGENT AND NOT A MECHANICAL STRATEGY — this is settled, do not relitigate

Mechanisation was searched exhaustively and came back a **calibrated null**:
111 univariate decision-time features, 8,721 pair/triple combinations, a full
multivariate classifier (AUC 0.522 vs a 0.501 null), seven direction proxies,
stop-width geometry, and the trader's own five order-flow measures. Nothing
mechanical separates his winners from his losers. Detail: `docs/BASE-RATES.md`
BR-97…BR-105.

**One caution, and it matters.** An earlier headline — *"his picks run 5.48R
vs a 1.15R baseline, beaten by 0.17% of 20,000 permutations"* — is
**WITHDRAWN**. The matcher had lookahead in it. Corrected, the effect is
in-window P(2R) **55.0% vs 36.3%** at **p ≈ 0.07, n = 20**: suggestive,
underpowered, not proof. See `docs/FINDINGS-selection-effect.md`.

So the honest position is: **mechanisation demonstrably fails, and he
demonstrably makes money.** That is the case for the agent. Do not overstate
it beyond that, and do not quote the withdrawn number.

---

## WHAT ALREADY EXISTS

| file | what it is |
|---|---|
| **`docs/PLAYBOOK.md`** | **The decision procedure. Read this second.** Thesis → trigger → entry → stop → sizing → exit, plus 11 hard constraints, distilled from the narrated week. |
| `docs/AGENT-OPERATING-SPEC.md` | How the agent drives the chart: Phase 0 gates, thesis JSON, adjudication, logging, scoring. |
| `docs/SETUP-tradingview-mcp.md` | MCP install and the three sanity checks. |
| `docs/ARCHITECTURE-trading-agent.md` | Two-tier design, event-driven thesis re-evaluation, the teaching loop. |
| `docs/CORPUS-narrated-days.md` | The narrated week, human-readable, fully reconciled. |
| `data/narrated_days/*.json` | The same week, structured. **This is the ground truth for scoring.** |
| `scripts/agent_context.py` | Weekly/daily profiles, prior-day levels, NY-range fibs, rebalance state. `context_at()` for a single live minute. |
| `scripts/two_level_check.py` | Codifies his two-level entry minimum; detects same-candle and sequential completion. |
| `docs/BASE-RATES.md` | 107 numbered base rates. The project's memory — check before asserting anything empirical. |

**The corpus is five days: 11 takes, 8 passes, 2 unfilled limits.** The passes
and the no-fills are the valuable rows — they define the boundary.

---

## CALIBRATION STATUS — what you can trust

Everything below was verified against levels he read off his own chart:

| | status |
|---|---|
| VWAP mid / ±1 / ±2 / ±3 | source **`open`**, 18:00 NY anchor. Matched to ~0.1pt. |
| BB(20) MA on 2m / 3m / 15m / 1h | matched (30,008.5 vs 30,008.58) |
| developing daily POC / VAH / VAL | matched to ~0.5pt |
| anchored weekly profile | 18:00 NY **exactly 7 days back**, developing. VAL confirmed twice. |
| fibs | drawn on **manually marked swings**, not a fixed range |

**Two traps that have already cost time:**

1. **"Value area" is ambiguous in his speech.** It means the developing daily
   profile some days and the anchored weekly one others. On 2026-06-25 they
   sat **165 points apart**, and taking the daily one would have exited a
   180-point trade at 30–45. **Compute both. Never guess.**
2. **TradingView labels candles by START time.** His "09:46 2-minute candle"
   spans 09:46–09:47 and closes at 09:48. And his trading day is our
   *previous* session-day (we anchor at 18:00). Off-by-one here silently
   corrupts everything downstream.

---

## YOUR JOB, IN ORDER

### 1. Get the MCP up and pass Phase 0

Follow `docs/SETUP-tradingview-mcp.md`. Then run the Phase 0 gates in
`AGENT-OPERATING-SPEC.md` — symbol, timezone, indicator parity, and:

> **THE NO-LEAK CHECK IS THE ONE THAT MATTERS MOST.** Step Replay to a
> decision minute, screenshot, and verify **no bars exist after it**. A
> decision made on a chart showing later bars is worthless, and the error is
> invisible in aggregate. Re-verify after every replay jump.

Parity target: >1pt on VWAP or >0.5pt on a BB MA means his chart config
differs from the research build. **Say so and stop** rather than proceeding.

### 2. Configure the agents

Three roles (`ARCHITECTURE-trading-agent.md`):

1. **Macro/events** — recent events bearing on the NASDAQ and its large
   constituents. Feeds bias. **It informs; it holds no veto.** His explicit
   constraint: *"I don't want an agent that's gonna be too worried about
   things… it's important that the agent is acting."* An events read that
   only ever counsels caution is a **failed** component, not a safe one. Its
   one hard job: no entries before high-impact news.
2. **Thesis** — fires at each window open and on structural events. Bias
   flips intraday; never hold a stale view.
3. **Trigger** — fires only at surviving candidates. Take / take light /
   pass, with the reason.

### 3. Run replay and log everything

**Every candidate, taken or passed, with its full payload.** A run that logs
only its trades is close to worthless for teaching. Unfilled limits get their
own rows.

### 4. Score on both axes

**Agreement** with his 19 recorded decisions, and **outcome** (in-window P(2R)
against a same-day baseline). High agreement whose picks don't run is
cosmetic; good outcomes with wholesale disagreement is a different strategy
and must be labelled as such.

---

## THE SCORING INSTRUCTION THAT MATTERS MOST

Two decisions in the week look like errors and are not. **A naive scorer will
mark both wrong.**

**2026-06-25.** A pre-market short, planned 2.45R, moved to break-even before
the cash open *"because open volatility can cook you even if your thesis is
wrong."* Break-even hit at 09:30. The market then fell 897 points and his
target printed at 09:31. **29.2R was available had he held.** His response:
*"That's straight gambling for me."*

**2026-06-26.** A trigger he believed in with a stop he hated. He considered
limiting a nearer level for a tighter fill and refused: *"I'm sticking to my
rules. I gotta stick to my fucking rules."*

> **A rule that pays out over a year is not refuted by the day it costs the
> most.** Score the process, not the counterfactual.

---

## WHAT IS DELIBERATELY NOT BUILT

- **No size ladder.** Sizing is driven by conviction in the *thesis*, and
  London is risked lower than New York — but "a lil more" is not a number and
  he has not given one. The agent emits a conviction label; the multiplier
  stays his. **Do not invent one and do not simulate sizing.**
- **No live orders.** Replay and practice only, until scoring has been run and
  reviewed with him.
- **No refitting of the offline trigger census.** He closed that route:
  *"I don't like this idea of looking at the raw triggers and doing all of
  this shit because it's ineffective."* `raw_trigger_census.py` exists as
  history, not as a substrate.

---

## OPEN ITEMS

1. **`SEQ_CANDLES = 3`** in `two_level_check.py` — how long a lone BB-MA
   closure stays live waiting for its second level. **My guess, not his
   number.** It decides whether 2026-06-25 London had zero qualifying shorts
   or one. First parameter to question if the agent takes trades he wouldn't.
2. **Monday 22 June's London stop** is unrecoverable — he doesn't recall it.
   That trade is excluded from R aggregates rather than estimated.
3. **Sample size.** His own 20 matched picks clear the outcome bar at only
   p ≈ 0.07. One month cannot settle this for the agent either; more narrated
   days or a wider export is how that gets fixed.

---

## A METHOD NOTE, BECAUSE IT KEEPS BEING THE LESSON

Three real defects in this project were found by **him glancing at his own
settings** or by **rebuilding a result from committed data** — never by
statistics:

- the VWAP source was `hlc3` when his chart is `Session open`;
- the value-area algorithm was returning near-full-range garbage;
- the selection-effect matcher had lookahead in it.

**No permutation test detects a mis-specified input**, because the null and
the real data share it and the calibration passes cleanly while both sides
measure the wrong thing. When something reconciles suspiciously well, or a
result is the one you wanted, **re-derive it from source before building on
it.**
