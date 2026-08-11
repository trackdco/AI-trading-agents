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

## T4 — 2026-08-11 · headroom scope — OPEN, awaiting his answer

**Run:** same. The agent's pass on his short also cited headroom: prior-day
VAL in the entry path. He took the trade and price sliced the level.

**The question as put to him:** do all computed levels count as "in the way"
(constraint 7), or only levels this day's tape is actively respecting — that
Friday being the weekly profile, by his own read? Unanswered; do not refine
headroom until he rules.
