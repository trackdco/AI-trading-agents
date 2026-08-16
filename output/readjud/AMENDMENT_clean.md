## CONTRACT AMENDMENT 0.4.8 — FRESHNESS CAPS THE GRADE

This amends the CONVICTION section of your contract. It is an addition to
rubric point 4, and it OVERRIDES anything in your contract that conflicts
with it.

**Rubric point 5 (new): FRESHNESS CAPS THE GRADE.** A level you have already
traded this session, or one the 15m has tested repeatedly, cannot carry its
full merit tier no matter how good the tier is.

### The principle

Your contract's rubric point 4 already lowers a grade for *"a level price
already sliced earlier in the session."* This extends the same logic from
*sliced* to *already faded*, and it is his doctrine in three places:

- rubric point 4 itself;
- THE RANGE FRAME — *"the middle is dead."* A level being revisited all
  session **is** the middle of a range, not an edge;
- his own review of a session where repeatedly fading one level was the thing
  he most disliked.

A level that has held four tests and is being faded for the third time may
still be a trade. **It is not an A.** Repetition at a level is not evidence
of the level's strength; it is evidence that the level is being worn down and
that price is rotating, not rejecting.

### The rule

- **Only a FRESH level may grade A.** A stale level tops out at **B**.
- **A third or later trade at the same level this session tops out at C.**
- **FRESH** = your briefing's `level_visits_this_session` block reports
  `level_visits_this_session: 1` for the level you name in `rejected_level`,
  AND that block reports `tests_15m_60min` of 2 or fewer.
- If the briefing carries no such block, grade as your contract otherwise
  directs and say so in `reason`.

### What this does NOT do

**It caps the GRADE. It never blocks a trade.** Your contract's rule on going
again at a level that already stopped you out stands untouched — a re-entry
is still licensed and you should still take it when it earns a take. What it
no longer does is come at A size.

Set `cited_freshness: true` in your structured output only if your reasoning
actually turned on this rule.
