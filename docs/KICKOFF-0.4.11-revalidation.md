# KICKOFF — 0.4.11 batch revalidation: `wr1`, then `jl1`, then stop

For the Mac session. The batch is his narration of 2026-08-18 turned into
contract text, plus the j49 post-mortem's plumbing. Stack for both runs:

| tier | contract | note |
|---|---|---|
| tv-macro-events | 0.2.0 | unchanged (T39 flagged in the register, not yet ruled) |
| tv-thesis | **0.4.4** | T40 struck; T71–T74 HTF-structure bias; condition grammar |
| tv-trigger | **0.4.11** | T75–T77 stops/retests; latched-condition default |
| tv-manage | **0.3.3** | uniform 50/50 partials; before-TP1 trail disambiguated |

All agents on Sonnet, model recorded per row, as before. **The runbook has a
new §2e** — three orchestrator duties (level-truth guard, mandatory re-read
counter, fresh-eyes window open). Read it before R1; the fresh-eyes step
changes how window-open thesis briefings are assembled (no prior thesis in
the first spawn; reconcile step after).

## RUN 1 — `wr1`: the fit week (2026-06-21…25)

Regression. The batch must not break the week he approved. Pass = the book
remains materially the approved one (small variance expected; structural
degradation — lost trades he praised, new losing shapes — is a STOP, and the
batch gets re-examined before anything else runs).

## RUN 2 — `jl1`: a fresh July week, 2026-07-05…09

**His call, 2026-08-18:** *"i reckon [run 2] should be a week from another
month. lets do july for good measure."* Right call — his narration of the
j49 days is now IN the contracts verbatim, so re-running that tape would
have been partly self-fulfilling. July is a clean test.

The week: session-days **2026-07-05 … 2026-07-09** (trading Mon Jul 6 –
Fri Jul 10). The only complete July week in the committed bars (the Jul 1
week has the holiday half-day; the dataset ends mid-Jul 15). No agent has
ever run it, no narration exists for it, no FOMC inside it.
`gate_offline_causality` run over all five days 2026-08-18: **ALL PASS**
(data coherent, every offline briefing field causal, scanner stable).

What the reviewer checks when the book lands (none of this reaches any
agent): the batch's machinery visible in the rows — `thesis_fresh` +
`thesis_reconciled` at every window open, any level-truth bounces logged,
the re-read counter firing on the second licence-only pass, the PRE hard
cap enforcing, stops placed per T75 (beyond the rejected level, not the
swing) — and then the only question that decides anything: **his
trade-by-trade read.**

## Windows — his 2026-08-18 ruling in force

All three windows run, with **NY_PRE HARD-capped at 1 fill per session-day**
(his ruling: *"we will allow a ny pre cap of 1 for now"* — it supersedes the
full cut; `docs/RULING-cut-ny-pre.md` carries the note). After a PRE fill,
later PRE candidates are passes with reason `window_cap`, never
tagged-and-taken. LONDON/NY_AM caps stay lifted-with-tags as before; the
09:10 entry cut stands. Scoring note: w49/jn1 books ran PRE uncapped, so
when comparing, apply the cap to their PRE rows arithmetically (first fill
only) for the like-for-like view.

## Mechanics — unchanged

Fresh prefixes `wr1` / `jr1` (never reuse a prefix); books to
`output/books/<prefix>/`; day_summary rows authoritative; same capture
sequence, leak checks, §2d never-block, weekly-anchor hard gate; move books
to `output/agent_runs/` only when scored and sealed.

## After `jl1`: STOP

He reviews both books. `jl1` IS the out-of-fit test of the batch — if it
reads like him, the path is paper days (HALT wiring first), Tradovate, the
execution agent. **2026-06-07…11** stays in reserve as a second OOS week if
anything needs a re-test; the j49 tape is teaching data and is never a test
again.
