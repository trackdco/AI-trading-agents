# OPEN QUESTION for you — does T39 fire on FOMC *Meeting Minutes*?

**Decided conservatively and logged, not blocked. jl1 ran with 07-07 NY_AM CLOSED.**

## The facts

The July week carries exactly one FOMC-named calendar row:

```
2026-07-08T14:00, USD, FOMC Meeting Minutes, high
```

Calendar day 2026-07-08 is the tape-day of **session-day 2026-07-07**. Both traded windows that
session-day (LONDON 03:00-04:59, NY_AM 09:30-11:00) end hours before the 14:00 print.

## The tension

- **T39 is CONFIRMED doctrine**, your ruling 2026-08-19: *"fomc does close ny entirely. that is
  enforced."* The macro agent owns this gate; per hard constraint 10 its veto is absolute and
  not escalatable.
- **The jl1 kickoff says the opposite about this week**: *"no FOMC inside it."* Written with the
  calendar in hand.

Two independent macro spawns, given the row inline, both returned `fomc_day: true` and both
stated it closes NY_AM.

## What I did and why

I followed the contract: the macro agent's `fomc_day` veto is the designated authority, two
independent reads agreed, and T39 is confirmed. **Session-day 2026-07-07 NY_AM is closed** — its
five candidates (A1 09:33, A2 10:12, A3 10:24, A4 10:30, A5 10:36) are logged as mechanical
`fomc_closed` passes, not adjudicated. LONDON that day traded normally; T39 closes New York only.

I did not overrule the agent on the strength of a kickoff sentence, and I did not silently keep
the window open because closing it costs candidates on a five-day test.

## What I need from you

Does T39 mean **FOMC rate-decision days**, or **any FOMC-named calendar event including
Minutes**? The answer changes one window in jl1 and will recur — Minutes land eight times a year.

If Minutes should NOT close NY, 07-07 NY_AM can be adjudicated as a follow-up; the tape,
levelsets and legends for those five candidates are already captured, so it is a re-run of five
trigger spawns and nothing more.
