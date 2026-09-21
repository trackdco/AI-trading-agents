# Why 0.3.5 got worse — the arithmetic, and what actually caused it

Clean week, audit-clean, 20 fills: **35% win rate, +1.51R average winner,
−0.05R expectancy blended.** Previous run: 9 fills, 57% WR, 1.90R winners,
+0.57R. So: **more than twice the trades, at half the win rate.**

## The break-even maths, which settles what matters

| win rate | avg winner needed to break even |
|---|---|
| **35%** (this run) | **1.86R** |
| 50% (his floor) | 1.00R |
| 57% (previous run) | 0.75R |

This run averaged **1.51R** winners at 35% — structurally unprofitable. At his
own 50–57%, even 1.2R winners print money. **The win rate is the whole game;
everything else is second order.**

## Three hypotheses tested against the log. Two died.

**DEAD — "the escalation rule made it take junk."** The opposite. Splitting the
20 fills by whether an escalation was involved:

| | n | WR | sum |
|---|---|---|---|
| escalated takes | 6 | **50%** | **+3.54R** |
| plain takes | 14 | **28%** | **−2.97R** |

The escalation rule produced the *better* half. It is exonerated, and the
safeguards (2/window budget, ratchet, qualification bar) held — 20 escalations
across five days, 15 accommodated, 5 re-affirmed.

**DEAD — "management gave the winners back."** 11 of 12 losses are a clean
−1.00R full stop-out. Nothing was managed away; these trades went from entry to
stop without ever offering anything. **This is entry selection, not management.**

**ALIVE, and partly my error — the T17 band widening leaked into ENTRY
QUALIFICATION.** He asked for a *targeting* change: *"the closest structural
level was 1R but I like around 1.2, 1.3R… it was searching for levels within
that range."* He was complaining that the agent **skipped near levels and
reached for far ones**. He never asked it to take more trades.

I implemented it as a band on `targets[0]`, which also silently relaxed the
entry test: a setup whose only structure sits at 1.0R now **qualifies**, where
under 1.5R it would have failed the band and been passed. Splitting on it:

| first target | n | WR | sum |
|---|---|---|---|
| under 1.5R | 9 | 33% | **−2.26R** |
| 1.5R and over | 11 | 36% | **+2.83R** |

Note the win rates are nearly identical — **the band did not make the reads
worse, it capped what a correct read could pay.** At 35% accuracy a 1.0–1.3R
first target cannot cover the losers. Both halves are equally accurate; only
one can pay for itself.

## The thing nobody has ruled on, and it is now the biggest single defect

**Stop widths across these 20 trades ran 10.0pt to 116.5pt from the same rule** —
an 11× spread. The sub-20pt stops (10, 14, 16) are inside NQ noise and got
tagged; the 90–117pt stops make even a correct read pay ~1R. This was raised as
open question #3 in `ANALYSIS-friday-three-runs.md` and never answered, and it
is the most likely remaining cause of a 35% win rate — a stop that does not
match the structure it is protecting produces a loss on a read that was right.

## What to change, in order of expected effect

1. **Restore the entry qualification bar to 1.5R while keeping T17's targeting
   freedom.** Two different rules, conflated by me: a candidate must have
   structure at **≥1.5R** to be worth taking at all; once taken, `targets[0]`
   may sit as near as **1.0R** if that is the structure price will actually
   reach. This preserves exactly what he asked for and removes what he didn't.
2. **Rule on stop-width bounds** (his call, still open). A floor around
   0.3×W15 and a ceiling around 1.5×W15 as scrutiny flags, not vetoes.
3. **Leave the escalation rule alone.** It is carrying the run.
