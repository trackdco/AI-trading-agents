# March 2026 replay — regime-agent scoreboard (arm A vs arm B)

**Question.** Does the regime-context agent layer improve on the static champion
(Blend v1.1) when replayed walk-forward over a real month?

**Answer for March 2026: no — it hurt, by −$5,365.** This is a *reported finding*,
not a defect to tune away (anti-tuning discipline). See "Why" below — the cause is
diagnostic, and points at two concrete revisions for the agent-design owner (Angus).

## The number

Regime-only run (HTF agent not yet run; its layer left permissive). One 08:00-ET
cutoff, no-hindsight. 18 agent-ruled March days (the 3 fail-closed days are absent by
construction — see below):

| metric | dollars |
|---|---|
| arm A — static champion (Blend v1.1) | **+$4,276** |
| arm B — champion + regime agent | **−$1,089** |
| **regime agent's effect** | **−$5,365** |

Reproduce:
```
python -m scripts.run_regime_replay ingest
python -m scripts.build_regime_gate_schedule --start 2026-03-01 --end 2026-03-31
python -m scripts.score_replay_arms --start 2026-03-01 --end 2026-03-31
```

Per-day (book = E3 balance / E4 war, picked by the frozen pre-open imbal switch):

| day | book | arm A $ | arm B $ | Δ$ | what the agent did |
|---|---|--:|--:|--:|---|
| 03-02 | E3 | +1564 | 0 | **−1564** | trap → reversion-only blocked the continuation winner |
| 03-04 | E3 | −595 | −302 | +292 | half-size cut a loss |
| 03-05 | E3 | −285 | −128 | +158 | half-size cut a loss |
| 03-09 | E4 | −465 | −235 | +230 | half-size cut a loss |
| 03-10 | E4 | +742 | 0 | **−742** | CPI stand-down skipped a winner |
| 03-11 | E4 | +575 | 0 | **−575** | event stand-down skipped a winner |
| 03-12 | E4 | −805 | −202 | +602 | half-size cut a loss |
| 03-13 | E4 | −805 | −222 | +582 | half-size cut a loss |
| 03-17 | E4 | +3485 | +450 | **−3035** | reversion-only + half-size gutted the month's biggest winner |
| 03-18 | E4 | −600 | 0 | +600 | stand-down avoided a loss |
| 03-19 | E4 | +1800 | −132 | **−1932** | war→continuation-only **vetoed the +$2,060 fade, kept the losers** |
| 03-20 | E4 | +1310 | 0 | **−1310** | stand-down / block skipped a winner |
| 03-23 | E4 | 0 | 0 | 0 | shock stand-down (champion already flat) |
| 03-25 | E4 | −780 | 0 | +780 | stand-down avoided a loss |
| 03-26 | E4 | −700 | −168 | +532 | half-size cut a loss |
| 03-27 | E4 | 0 | 0 | 0 | — |
| 03-30 | E4 | 0 | 0 | 0 | — |
| 03-31 | E4 | −165 | −150 | +15 | half-size |

## Why it hurt — two distinct failure modes

**1. It was insurance in a green month.** The agent's half-sizing and stand-downs
*did* work as designed on losing days (03-04/05/09/12/13/18/25/26 all improved:
+$3,776 saved). But March was a **green** month for the champion, and the agent
clipped the winners far harder than it saved on losers. On a defensive tool, a green
month is the worst case: you pay the premium (clipped upside) and collect little
payout (few losses to avoid). The single biggest line, 03-17 (+$3,485 → +$450), is
half-size × reversion-only applied to the month's best day.

**2. Structure mismatch — the more serious one.** On war days the agent says
"ride continuation, block reversion." But the champion's E4 (war-book) edge is
*frequently a counter-trend fade* (pattern A = reversion). 03-19 is the clean proof:
the champion's entire +$2,060 came from a pattern-A fade at 09:49; the agent called
the day war/short and permitted **continuation only**, so it vetoed that fade and kept
the pattern-B2 continuation trades — which lost. The regime read was directionally
reasonable and still destroyed the day, because "war ⇒ continuation-only" contradicts
how the champion actually makes money in a war regime.

This second mode is not fixable by loosening size. It's a wiring question:
either the `_trigger_class` mapping (pattern A→reversion) is too coarse, or the
regime→permitted-structure logic ("war ⇒ continuation-only") is wrong for this
book. **Flagged for Angus**, not tuned here.

## Caveats on the number (all push arm B the same direction — down)

- **Regime-only.** The HTF agent was not run; its layer is permissive. Adding it can
  only *remove* more trades, so the combined gate would be ≤ this, not better.
- **3 days fail-closed.** 03-06, 03-16, 03-24 produced valid *judgments* but their
  rationale ran 627–665 chars over the 600-char schema cap, so the parser rejected
  them (fail-closed → those days trade as champion, unprotected). All three were
  de-risk calls (one stand-down, two half-size), so honoring them would have pushed
  arm B *further down*, not up. **This is a prompt/schema finding:** the agent needs a
  hard brevity instruction, or the cap needs raising — I did **not** hand-trim the
  rationales to force them through (that would be tampering with agent output).
- **No news (arm C).** Verdicts were built from price + ex-ante calendar only. The
  news archive (Brake's lane) could change some event-risk calls.

## What this does and doesn't tell us

It does **not** say the agent layer is worthless. It says: *tested on a month the
champion already won, a defensive de-risk agent loses, and the current war⇒continuation
rule actively fights the champion's fade edge.* The fair test of a defensive layer is a
**drawdown month** — where the stand-downs and half-sizes it applied to 03-04/12/13/25/26
would be the whole month, not the exception. The regime read (mode 2) must be fixed
regardless of month. Both are inputs for the next agent-design pass, not tuning targets.
