# tv-macro-events cannot read files — it must be spawned with the briefing INLINE

Found at the start of jl1, 2026-08-20.

## What happened

Ten macro spawns were given a briefing **path** and asked to read it. Every one returned
`tool_uses: 0`. None of them read anything. What came back instead:

- three reads named events that were **not in their briefing** — NFP / AHE / Unemployment Rate
  and ISM releases on files whose `released_so_far_today` and `scheduled_later_today` were both
  empty;
- one set `fomc_day: true` on a briefing containing **zero calendar rows**;
- one claimed the briefing file was invalid JSON carrying leaked outcome fields
  (`past_result`, `market_reaction`). Reading the file disproved every part of that: it parses,
  and contains none of those keys;
- two narrated "*Reads the file*" or emitted a tool-call block as their final answer;
- one hit a genuine tool failure and **correctly refused to fabricate**, which is the only
  behaviour in the set that was right.

## Root cause — a runbook gap, surfaced by an orchestrator mistake

**Corrected 2026-08-20 after his diagnosis, which is better than the one first written here.**

`tool_uses: 0` is not a defect. It is the design. tv-macro-events is the leak-tightest tier:
it has no tools *on purpose*, so it physically cannot open a file and therefore can never read
anything it was not handed. Its contract line has always said "spawned with the briefing
**inline**". The contract was never wrong.

The gap was in the runbook's R1 step, which said only "Call tv-macro-events". Every other tier
is spawned with a file path, so a path-style spawn is the natural move — and for this one tier
it spawns the agent blind. He has since made the inline requirement explicit in R1, with the
reason, so it cannot regress on a future run or a future orchestrator session.

The failure mode worth naming is therefore not "the agent confabulates". It is: **a
deliberately blind agent, handed nothing, has no channel to report that it got nothing.** It
answers from whatever it has, which is its own prior. The only spawn that could tell something
was wrong was the one whose tool calls visibly failed — and that one correctly refused.

## What the orchestrator did wrong

The agent's own registry line says it is *"Spawned by the orchestrator only, **with the briefing
inline**; never self-select"*, and the briefing's own `instruction` field tells it
*"You have no tools; do not attempt to verify anything outside this file."* It was designed to
be handed content, not a path. I handed it a path. Given nothing to read and an instruction
saying it has no tools, it filled the gap from memory of other trading weeks.

## The lesson worth keeping

A confabulating agent is not always a broken agent. This one was starved of input by its caller
and had no way to say so — the only spawn that *could* tell something was wrong was the one
whose tool calls visibly failed, and that one refused to answer. **Silence about missing input is
the dangerous failure mode**, and the fix belongs at the caller.

## What was done

- All four window opens whose calendar actually has rows were re-spawned with the full briefing
  inline. The first re-spawn returned a clean read that names only the real event and computes
  its blackout band correctly.
- The six window opens whose calendar is **empty** were written mechanically by the orchestrator.
  With no dated row the answer is forced — no blackout, no FOMC, no driver, neutral lean — so an
  agent read adds nothing and, as shown above, demonstrably subtracts. Those rows carry
  `_provenance: orchestrator-mechanical (empty calendar)`.
