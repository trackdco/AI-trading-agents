# TEACHING LOOP — his rulings on agent disagreements, in order

The refinement substrate. Every entry is a disagreement between a scored
agent run and his recorded or stated behavior, plus his ruling on it, dated.
Prompt versions cite entries here when they change. Doctrine that graduates
into a hard rule moves to `PLAYBOOK.md`; this file is where it lands first.

Entries are append-only. A ruling that later proves wrong gets a dated
correction entry, not an edit.

---

## T1 — 2026-08-11 · sequential pairs default toward PASS

**Run:** first scored London, session-day 2026-06-25. Predicted before the
trigger fired; confirmed by the run (agent passed his L1).

**His ruling, unprompted:** *"This is the one trade where I wouldn't be mad
about it not taking. I usually instate it has to break another level along
with the MA in the same candle. This was a heavily discretionary reading."*

**Consequence:** same-candle is the rule; sequential completion is discretion
ON TOP of the rule. An agent pass on a sequential pair is within doctrine and
scores as acceptable, never as a plain miss. Already folded into
`PLAYBOOK.md` §2 and the scorer's 2026-06-25 guard. Note the run's other
side: the agent's one take (L1-0318, −1.0R) was ALSO a sequential pair — the
permissiveness cost real R the same morning the ruling landed.

## T2 — 2026-08-11 · rebalance depth: the agent's `waiting_for` was too shallow

**Run:** same. The −1.0R long entered at 03:16-03:18 on "rebalance to the
2m/3m MA complete."

**The tape:** at entry, price sat ~180pt above the 15m MA (29,351) and the 1h
MA (~29,590) was never touched in the entire window (high 29,562.75 at
03:32). His own pre-session words named the depth: *"a rebalance to the
one-hour or around that VWAP+1 level would be good"* — and he took zero longs
that London because that condition never arrived.

**Consequence (pending his final phrasing):** after a large displacement the
rebalance that licenses entry is the one HE names on the higher timeframe
(15m by his displacement rule; 1h when the move is that extended) — a 2m/3m
MA touch alone is not "the rebalance." Open question to him: is 15m the
floor always, and when does it escalate to the 1h?

**ANSWERED, 2026-08-11:** *"The 15-minute is always the floor."* A 2m/3m MA
touch alone never licenses entry. Plus a target rule that was nowhere in the
corpus: when the 15m MA sits only ~1–1.5R from the entry, it is **TP1**, and
the real target is structure beyond it — the near MA is intermediate
structure, not the destination.

## T3 — 2026-08-11 · the missing fib layer, and location-shaped two-sidedness

**Run:** same. The agent passed his 2.45R short on direction: its thesis
licensed shorts only on "hard rejection at 29,655–29,710," which never
printed (high 29,562.75).

**His ruling:** *"We were trading around the 0.5 of the range of that day,
which is why I was convicted in us going down from there. If it were to
continue down it would've been from there or the weekly level. So it wasn't
too far off, just didn't look at fibonacci stuff."* Matches his narration at
the time: *"We're at around that 0.5 level right now… If we are to go back
down, we'd go back down now."*

**Two consequences:**
1. **Briefing gap, structural:** `agent_context` computes NY-range fibs only
   (undefined before 10:00 NY). His Friday fib was drawn on the DAY's range,
   pre-London. London/pre-market theses have been fib-blind by construction.
   Fix requires his marked-swing convention from him directly — the corpus
   warns fib swings are manual judgment (~70pt error from guessing the swing
   on 2026-06-23; within 2pt using his marked swing on 2026-06-26). Do not
   encode a guessed swing.
2. **Thesis shape:** `condition_for_other_side` must be able to license the
   other side by LOCATION (at the marked retrace / at a named level, "it
   would've been from there") — not only by rejection at an overhead cluster.

**CONVENTION SUPPLIED, 2026-08-11 — the London fib layer is now buildable:**
- **When:** London continuation days — Asia moved predominantly one way and
  he is reading London as continuation of that move.
- **Swing:** *"I'll always mark out the fib from the high of the day to the
  low of the day"* — the developing session-day range. Objective inputs; no
  hand-marking needed for this case.
- **Acting levels:** 0.382, **0.5 (the equilibrium)**, 0.618, **0.705** (his
  "OT" level, favored especially in New York; deep retrace that
  statistically holds). Matches the FIBS constant already in
  `agent_context`.
- **The meta-rule:** *"What matters more than the fib itself are what levels
  are in alignment with the fib levels… You can't just take the levels at
  face value."* A fib acts only in CONFLUENCE with other structure plus
  price behavior at it.
- **Behavior flips the read:** a sustained stall at the 0.5 licenses the
  fade; the same 0.5 BREAKING after that long a stall flips him the other
  way (*"I'd be expecting a break to the upside"*).
- **Verified on the tape (2026-06-25):** pre-London H 29,892.75 / L 29,160.5
  → 0.5 = 29,526.6; VWAP mid 29,490.8; his entry 29,492.75; the London
  stall 29,44x–29,562.75 straddled exactly that band. It is a ZONE read,
  not a point read — encode tolerance, not equality.

## T4 — 2026-08-11 · headroom scope — OPEN, awaiting his answer

**Run:** same. The agent's pass on his short also cited headroom: prior-day
VAL in the entry path. He took the trade and price sliced the level.

**The question as put to him:** do all computed levels count as "in the way"
(constraint 7), or only levels this day's tape is actively respecting — that
Friday being the weekly profile, by his own read? Unanswered; do not refine
headroom until he rules.

**ANSWERED, 2026-08-11 — the dichotomy was the wrong shape; his rule is
distance, role, and behavior:**
1. A level sitting AT the entry that price has just broken counts toward the
   trigger, not as obstruction — *"it was kind of sitting right there where
   the entry was… it broke through two levels."*
2. Once IN the trade, a nearby level ahead is a **tripwire**: price slicing
   through it → continue to target; price STALLING at it → *"I'd probably
   close the trade early."* This is a new management clause for the exit
   logic, not only an entry filter — nothing in the corpus carried it.

## T5 — 2026-08-11 · the entry grammar, dumbed down by him — REJECTION IS THE CAUSE

**Context:** volunteered unprompted while the first NY replay leg ran.

**His words:** *"If we can dumb down an entry, what does an entry actually
look like? It's a rejection off of a key level, and then a breakout through
the moving average and something else stacked on top of it, and then an
entry at the retest… We've rejected this key level, whatever it is. Great,
it's 0.5 of the daily range. What am I going to look for then? If price
breaks through the moving average or breaks through VWAP as well, I'm
inclined to take shorts because that rejection is constituting me to go for
shorts. That's really all it is."*

**Consequence — a causality inversion for the trigger prompt.** The doctrine
as first written treated the two-level closure as THE trigger, with
rejection merely "counting toward the pair." His grammar is ordered:
**(1) rejection at a key level → (2) the two-level break as the rejection
proving itself → (3) entry at the retest.** A two-level break with no
rejection story behind it is movement, not an entry. This cleanly separates
his Friday short (rejection at the 0.5-zone/VWAP-mid confluence) from the
agent's −1.0R long the same morning (identical mechanical shape, nothing
being rejected). 0.3.0 trigger frame: *name the level that was rejected, or
lean pass.*

**Two riders, same monologue:**
- **Origin-proximity stop clause:** when the displacement candle's origin
  sits close to the VWAP band, limit at the closest structure (the BB MA)
  but give the stop breathing room beyond the band cluster — *"I'm not
  going to put it past the fact that we might come up and retest the
  Bollinger Band and the VWAP band."* The origin-side variant of the
  existing extreme-on-a-live-level stop rule.
- **Style anchor, for every prompt:** *"I'm never trying to catch these
  gigantic moves. You have to take your piece of the pie and get out… I
  like having a higher win rate."* Guards the agents against drifting
  toward home-run targeting; consistent with the realized 1.5–2.5R
  distribution and the §7 break-even guard.
