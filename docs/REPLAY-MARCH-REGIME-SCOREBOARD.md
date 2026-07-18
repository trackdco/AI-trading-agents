# March 2026 replay — regime-agent scoreboard (arm A vs arm B)

**Question.** Does the regime-context agent layer improve on the static champion
(Blend v1.1) when replayed walk-forward over a real month?

**Answer for March 2026: no.** Agent v0.2: **−$5,365**. After the two Pat-directed
revisions (v0.3.0, below): **−$1,715** — better, still negative, and the retest
surfaced a new failure mode. All numbers reported straight (anti-tuning discipline).

---

## v0.3.0 retest (2026-07-18)

Two revisions were made to `.claude/agents/regime-context.md` (Pat-directed,
pending Angus ratification) and the full month re-run from scratch (fresh emits,
22 fresh zero-context verdicts, new agent hash `6cbfd786de69`):

1. **Structure-exclusion rule** — a regime label (e.g. war) no longer removes a
   structure by itself; exclusion now requires briefing evidence against THAT
   structure. This fixes the 03-19 class of error (war ⇒ continuation-only vetoing
   the champion's winning fade).
2. **Hard length caps in the prompt** — rationale ≤600 / notes ≤1500 stated as
   verdict-voiding, with a target under each.

**Validity caveat: this retest is in-sample.** The revisions were designed by
looking at March's failures, so March can no longer certify the agent. The result
below measures whether the fixes *behave as intended*; certification needs a month
the v0.3 agent has never influenced (e.g. April–July).

### v0.3 result — 22/22 days ruled, 0 schema failures

| metric | v0.2 | v0.3 |
|---|--:|--:|
| arm A — static champion | +$4,276 (18d) | **+$3,356 (22d — full March, matches frozen baseline)** |
| arm B — champion + regime agent | −$1,089 | **+$1,641** |
| agents' effect | **−$5,365** | **−$1,715** |
| schema-failed verdicts | 3 of 21 | **0 of 22** |

Both fixes did what they were built to do:
- **No structure vetoes fired.** 03-19 went from −$132 (fade blocked, losers kept)
  to +$895 — exactly the half-sized champion trade. The wiring bug is gone.
- **No verdicts died on length.** 03-06 (NFP quintuple cluster) now stands down
  validly and saves its −$75.

### The new finding: the agent has collapsed into "always half-size"

Every one of the 22 days got `size_multiplier: 0.5` (or the one stand-down).
Arm B ≈ arm A × 0.5 almost line-for-line (+$1,641 ≈ half of +$3,356). The verdicts
justify it the same way each day: March's shock-bar counts and 300–1000pt ranges
read as "elevated volatility ⇒ 0.5x" every single morning. With the structure veto
removed, the agent's only remaining lever is size — and it never uses 1.0.

A de-risk layer that outputs a constant is not exercising judgment; it is a static
position-size cut, which needs no LLM. **For Angus:** the agent needs either
(a) calibration guidance for what "normal" volatility looks like (its briefing has
no baseline to compare shock counts against, so everything looks elevated), or
(b) an explicit instruction that 1.0 is the default and 0.5 must cite a
day-specific trigger, not the month's ambient volatility. Not tuned here.

### Bottom line after v0.3

On a green month the honest expectation for a pure de-risk layer is now
≈ −(half the month's profit), and that is exactly what we got. The two real
questions remaining are (1) does it save more than it costs in a **drawdown month**
(the fair test, still unrun), and (2) can it learn to size 1.0 on clean days
(the new finding above). 

---

## v0.2 run (original) — detail below

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
