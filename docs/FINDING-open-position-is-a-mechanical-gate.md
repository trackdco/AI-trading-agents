# RESOLVED FROM THE CONTRACT: an already-open position is an absolute mechanical gate

This settles the question jr1 raised twice as `ruling_needed`, and it settles it from the
contract text rather than from precedent. **No ruling from you is required for this one.**

## The question

Across three windows now, triggers briefed with an OPEN same-direction position have split on
whether that position bars a second entry:

| run | window | candidate | read |
|---|---|---|---|
| jr1 | 06-02 LONDON | L6 | gate - passed |
| jr1 | 06-03 NY_AM | A6 (10:21) | gate - "an absolute mechanical gate, not a thesis opinion" |
| jr1 | 06-03 NY_AM | A8 (10:54) | **sizing input** - took light on byte-identical state |
| jr2 | 06-02 LONDON | L5 (03:42) | gate - passed, citing open L3 |
| jr2 | 06-02 LONDON | L6 (04:03) | **not a gate** - take_full alongside open L3 |
| jr2 | 06-02 LONDON | L8 (04:24) | **not a gate** - "adds alongside open L3 ... within LONDON cap" |

## The contract already answers it

`tv-trigger` 0.4.13, section 2e duty 4:

> **NO ESCALATION ON MECHANICAL GATES.** Window bounds, the window cap, the news blackout, the
> 09:35 open buffer, and **an already-open position** are not thesis opinions. They are absolute
> and an escalation cannot reopen them.

An already-open position is named in the same breath as window bounds and the news blackout.
It is absolute.

## Why the flip clause does not rescue the takes

The contract also carries a flip clause (his ruling 2026-08-16):

> Any candidate firing **opposite** an open position is now a flip candidate ... If you take it,
> the orchestrator flattens the old position for you.

That is scoped to candidates firing *opposite* an open position. jr2's L6 and L8 are
**same-direction** shorts stacking onto an open short - the flip clause does not reach them, and
the mechanical gate does. The cap is a separate constraint: L8's "within LONDON cap" is true and
irrelevant, because the gate binds independently of the cap.

## What was done

- jr2 06-02 L6 and L8: merit `take_full`s **retained in full**, flagged
  `SUPERSEDED_POSITION_OPEN`, with mechanical `position_open` passes written after them.
- jr1's enforcement of 06-03 A8 (and 06-02 L6) was **correct**, and its `ruling_needed` flag can
  be closed on this basis rather than left open.

## What is still open, and is genuinely yours

This is a different question from the *cap* one in
`docs/FINDING-jr2-lifted-cap-contradicts-jr1-L10.md`, which remains open:

- **Gate (this doc):** already-open position - RESOLVED by contract text, no ruling needed.
- **Cap (other doc):** LONDON/NY_AM caps are LIFTED-WITH-TAGS, so jr1's L10 was probably wrong
  to refuse - still needs your ruling.

The two were entangled in jr1 because L10 tripped the cap while others tripped the gate. They
are separate rules with opposite dispositions: the gate refuses, the lifted cap tags and takes.
