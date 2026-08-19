# FINDING: jr2 06-01 A6 shows my jr1 L10 cap enforcement was probably wrong

**Raised from jr2, about jr1. Nothing in jr1 has been altered - it is committed and already
reported. This is for your ruling, and it is the same question jr1's L10 `harness_finding`
already flagged as `ruling_needed`.**

## What happened in jr2

`jr2 2026-06-01 A6` (NY_AM, 10:45) was re-adjudicated against a book where NY_AM's written cap
of 2 was fully used. Its briefing said, verbatim:

> the written NY_AM cap is 2 fill(s) and 2 are used. Caps are LIFTED-WITH-TAGS here: a fill
> past the written cap is taken and tagged beyond_written_cap, not refused.

The trigger returned `take_light` with `constraints_failed: ["beyond_written_cap"]` and said so
in its reason ("3rd concurrent long this window (caps lifted-with-tag)"). It filled at 10:45 @
30620.0. That is **exactly the documented shape**: the tag IS the mechanism.

## Why that indicts my jr1 handling

In jr1 I hit the same pattern at `2026-06-02 L10` (LONDON, cap 2, both slots live) and I
**enforced** it: retained the take flagged `SUPERSEDED_LONDON_CAP` and wrote a mechanical
window_cap pass over it. My stated reason was:

> "A verdict cannot both fail a mechanical constraint and be a take; nothing downstream was
> checking for that combination."

That reasoning is wrong for a lifted cap. Under LIFTED-WITH-TAGS, `beyond_written_cap` in
`constraints_failed` is not a self-contradiction - it is the required tag on a permitted fill.
LONDON's cap is lifted, exactly like NY_AM's. The only cap that is HARD is NY_PRE (his ruling
2026-08-18), and that is the one wr2 mechanically refuses.

So jr1 L10 should most likely have been **taken and tagged**, not superseded.

## What that costs

jr1 06-02 L10 was a `take_light` that I converted into a pass, so it never filled and never
scored. LONDON on jr1 06-02 shows 2 takes / 2 fills / -1.6848R; a third tagged fill would have
changed that day and the week total (jr1 finished +3.0837R blended). I have **not** recomputed
what L10 would have scored - doing so would mean re-running a book you have already reviewed,
and the decision to reopen jr1 is yours, not mine.

## Where the two runs now stand

| | cap | jr1 handling | jr2 handling |
|---|---|---|---|
| NY_PRE | **HARD** (2026-08-18) | mechanically refused | mechanically refused (06-01 P3/P4/P6) |
| LONDON | lifted-with-tags | **refused (L10)** | n/a so far |
| NY_AM | lifted-with-tags | n/a | **taken and tagged (A6)** |

jr2 follows the doctrine as written. jr1 does not, at exactly one row.

## The ruling I need

1. Confirm lifted-with-tags means what the briefing says - take and tag - so jr2 A6 stands and
   any later jr2 LONDON/NY_AM beyond-cap take is handled the same way. **I am proceeding on
   this reading**, per "decide and log, never block".
2. Say whether jr1 L10 should be reinstated and jr1 re-scored, or left as-is with this finding
   attached to it.
