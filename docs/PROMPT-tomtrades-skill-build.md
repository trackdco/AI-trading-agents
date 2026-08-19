# PROMPT — deep research → skill → mechanical code for the tomtrades method

Paste the block below into a fresh Claude Code session **in this repo**. It is written to
run in phases with a human gate between each, because the failure mode here is an agent
that invents precision the source never had and hands you a backtest of its own
imagination.

Prerequisites: `docs/RESEARCH-tomtrades-audit.md` committed, and a Gemini API key in
`GEMINI_API_KEY` with billing enabled if you want the remaining videos ingested.

---

```
You are helping me turn a public day-trading method into a mechanical, backtestable
strategy I can falsify. Read docs/RESEARCH-tomtrades-audit.md first — it is a partial,
quote-grounded audit of the tomtrades method (@itstomtrades and @TomTradesJournal),
including a coverage ledger and a list of known contradictions. Treat it as evidence,
not as truth.

THE ONE RULE THAT OVERRIDES EVERYTHING ELSE
Never invent precision the source did not state. Where he is vague ("overextension",
"area of interest"), your job is to expose the ambiguity as an explicit, named,
sweepable parameter — not to pick a number and move on. Every rule you write must carry
a citation: video id + timestamp + verbatim quote. A rule you cannot cite is a rule you
delete. If you find yourself reaching for ICT/SMC vocabulary he never used, stop: use
his words for his concepts.

PHASE 1 — COMPLETE THE EVIDENCE BASE
The audit is partial; the free-tier Gemini quota (20 requests/day/model) cut it short.
Finish it:
- Re-run the extraction over every unprocessed video on both channels, and over the
  8h30m course in 40-minute segments. Rotate models when one is exhausted, and record
  which model produced each note.
- Prioritise @TomTradesJournal — it explains WHY each trade was taken, which is what a
  decision agent needs, rather than what a setup looks like in the abstract.
- Keep the same JSON schema and the same hard rule: every entry needs a verbatim quote
  and timestamp, or it does not get recorded.
- Output: a refreshed corpus plus an updated coverage ledger showing exactly which
  videos are still unread. Do not describe coverage as complete while anything is
  missing.
STOP. Show me the coverage ledger and the top 10 new findings before continuing.

PHASE 2 — RESOLVE EACH CONFLUENCE INTO A TESTABLE PREDICATE
For every confluence and filter in the audit — MTF range condition, hourly
overextension, minute-of-hour window, DXY/Yen correlation, AOI touch, Type 3 shift,
nested "shift within a shift", candle flip, volume behaviour — produce one entry with:
  - his definition, quoted
  - the ambiguity: precisely what he never specifies
  - 2-4 candidate formalisations, each computable from OHLCV (+ correlated series)
  - the parameter(s) each introduces, with a sensible sweep range and a default
  - how to measure whether the confluence adds edge ON ITS OWN, independent of the rest
  - a falsification test: what result would prove this confluence is noise
Where the audit flags a contradiction (the timing window especially — 22-52, 30-45,
20-30 and "37" all appear), do NOT reconcile it by picking one. Encode it as a
parameter and let the data choose.
STOP. Show me the confluence table before writing code.

PHASE 3 — BUILD THE SKILL
Use the skill-creator skill to build a project skill named `tomtrades-model` that
encodes the method as a reusable capability, with:
  - SKILL.md: the model, its vocabulary, its parameters and their defaults, and an
    explicit "what this method does NOT specify" section
  - a references/ file holding the full citation table (rule → quote → video → timestamp)
  - the confluence table from Phase 2
  - a loud statement of the evidence limits: self-reported statistics, a channel is a
    selected sample, and the extraction was model-mediated rather than human-verified
The skill must be honest enough that a future session cannot mistake this for a
validated edge.

PHASE 4 — MECHANICAL IMPLEMENTATION
Implement it to this repo's standards (context/code-standards.md), following the
existing engine layout and the "Python sees, Claude judges, Python acts" split:
  - a pure, deterministic detector: OHLCV (+ DXY/correlated series) in, timestamped
    candidate signals out, with every gating condition individually toggleable
  - config-driven parameters in the style of config/strategy.yaml, each commented with
    the quote it came from
  - NO LOOKAHEAD: signals compute on closed candles only, orders activate next bar.
    Minute-of-hour and session logic must be timezone-explicit — he is AU-based, so
    anchor to exchange time and state the assumption in the config.
  - unit tests with hand-computed fixtures, including one test per confluence proving
    it can be switched off independently
Then wire it into the existing backtester and produce a report with per-confluence
ablations — the whole point is finding out which parts, if any, carry the edge.

PHASE 5 — REPORT HONESTLY
Report what the data says, including and especially if the edge is absent. Divergences
from his claimed 81-88% winrates are findings to document, not problems to fix. Do not
tune parameters to make the result resemble his marketing. The repo's non-negotiable
applies: divergences are reported, not fixed.
Flag explicitly: he says he skips 30-40% of his own setups. A backtest takes every
signal, so it cannot reproduce his results even if the edge is real — quantify that gap
rather than papering over it.

CONSTRAINTS
- This is research. Do not touch the live/paper path, and do not modify
  strategy-definition-v1.2.md — that needs a written hypothesis and Angus's approval.
- Work in phases; stop at each STOP and wait for me.
- If evidence is thin for something, say so plainly instead of filling the gap.
```

---

## Follow-up prompts, once the above has run

**Refinement loop**
```
Run the ablation sweep over the parameters from Phase 2. For each confluence report
signal count, hit rate, expectancy and the delta from removing it. Rank by contribution.
Recommend the minimal subset that retains most of the edge, and tell me plainly if the
answer is "none of it survives".
```

**Comparison to the existing system**
```
Compare the tomtrades detector against the NQ engine in this repo: where do the concepts
overlap (session filters, structure shifts, fixed-R targets), where do they genuinely
conflict, and is there anything here worth proposing as a hypothesis against the
strategy document? Recommend against adoption if the evidence does not support it.
```

**Agent that reasons like him**
```
Using the journal-channel trade breakdowns as ground truth, build an evaluation set of
his actual decisions: context, what he saw, what he did, why. Then test whether the
mechanical detector agrees with his stated reasoning trade by trade. Where they diverge,
work out whether he applied an unstated filter — that gap is the discretionary layer,
and it is the only part that belongs in an agent rather than in Python.
```
