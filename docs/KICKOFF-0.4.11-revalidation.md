# KICKOFF — 0.4.11 batch revalidation v2: `wr2` → `jr1` → STOP; `jl1` only on his green light

For the Mac session. The batch is his narration of 2026-08-18 turned into
contract text, plus the j49 post-mortem's plumbing. Stack for all runs:

| tier | contract | note |
|---|---|---|
| tv-macro-events | 0.2.0 | unchanged — T39 CONFIRMED by his ruling 2026-08-19 |
| tv-thesis | **0.4.5** | T40 struck; T71–T74; condition grammar; T18/19 reach enforced |
| tv-trigger | **0.4.16** | T75–T80 + chop v2 + all enforcement (see version header) |
| tv-manage | **0.3.4** | uniform 50/50; the runner's mandate is TP2 |

All agents on Sonnet, model recorded per row, as before. **The runbook has a
new §2e** — SIX orchestrator duties (level-truth guard, re-read counter,
fresh-eyes open, ladder bounce, reach bounce, 2-of-3 window-open vote). Read it before R1; the fresh-eyes step
changes how window-open thesis briefings are assembled (no prior thesis in
the first spawn; reconcile step after).

## RUN 1 — `wr2`: the fit week (2026-06-21…25)

`wr1` was pulled mid-run by him (2026-08-18): six trades went out
single-target and every LONDON close came in under w49 — the uniform 50/50
split had exposed a single-target habit the old conviction-keyed partials
were masking. The fix is **T78 (trigger 0.4.12): every plan is a LADDER —
TP1 by the unchanged preference order, TP2 the next structure at least ~1R
beyond it, typically 2.5–4R** — plus tv-manage 0.3.4 naming TP2 as the
runner's mandate. `wr1` is a burned prefix; this is `wr2`, from scratch.

Regression, same terms as before: the batch must not break the week he
approved. Pass = the book remains materially the approved one. Reviewer
checks per take: **two targets on every plan**, no fixed-R TP2. Structural
degradation is a STOP.

## RUN 2 — `jr1`: the j49 tape (2026-05-31…06-04) — mechanism check, not the test

Restored by his ruling 2026-08-18: *"lets not run jl1 until j49 and w49 are
done and we can look at them and be happy with them."* The epistemics stay
straight: his narration of these exact days is in the contracts verbatim,
so a good `jr1` book is NECESSARY, never SUFFICIENT — it verifies the batch
changes the behaviour it was built to change, on the tape where the
failures happened. The clean test is `jl1`, and it waits for his review.

Reviewer's receipts, from his narration — **for the reviewer AFTER the book
lands; none of this reaches any agent, briefing, or prompt:**

- **Mon 05-31, 03:12/03:18** — adjudicated on merits; no calendar
  stand-aside exists any more. Whatever the verdict, the reason must be
  structural.
- **Tue 06-01** — bias LONG by the open under T71–T74 (*"that was longs all
  day"*); the shapes he named: the VWAP+1-retest long after the
  multi-level reclaim near 09:48–09:51, the re-break re-entry near 10:33;
  VWAP+2 the first target, the prior-day high (30693) the full destination.
- **Thu 06-03, 03:22** — if taken, the stop sits per T75 beyond the
  rejected W/D VAH with breathing room, not tucked at the swing.
- Machinery in the rows: `thesis_fresh`/`thesis_reconciled` at every window
  open, level-truth bounces logged where they fire, the re-read counter
  forcing a thesis re-read on the second licence-only pass, the PRE hard
  cap enforcing.

## RUN 2c — `jr2`: the j49 tape under ENFORCED T78 (his call, 2026-08-19)

Status first: `wr2` DONE (+16.5304R, regression passed), `jr1` DONE
(+3.0837R). But jr1 ran with T78 violated on 8 of 12 takes (the schema-
example defect, fixed in 0.4.13), so the enforcement itself — and the
50/50 split, which only pays when TP2 exists — went untested. His call:
*"wouldnt it make sense to run jr1 with t78 enforced if it wasnt enforced
before."* Yes. `jr2`: same tape (2026-05-31…06-04 week), trigger 0.4.13,
the §2e duty-4 ladder bounce LIVE (re-spawn any take with <2 targets once,
tag `t78_single_target`), everything else identical to jr1. Fresh prefix
`jr2`, books to `output/books/jr2/`. Then STOP for his review.
Reviewer receipts: same three as jr1, PLUS: every take two-rung (bounces
counted), and the runner-vs-full-target decomposition re-cut with real
ladders.

## RUN 3 — `jl1`: the fresh July week, 2026-07-05…09 — **GATED ON HIS GREEN LIGHT**

**Do NOT start this run until he has reviewed the `wr2`/`jr1`/`jr2` books and
explicitly green-lit it.** His ruling: *"lets not run jl1 until j49 and w49
are done and we can look at them and be happy with them."*

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

## Windows — his 2026-08-19 ruling: NY_PRE IS CUT (jl1 onward)

Trading windows for `jl1` are **LONDON 03:00–04:59 and NY_AM 09:30–11:00
only**. NY_PRE is not traded: no candidate adjudication, no fills, and the
08:00 thesis read is skipped — NY_AM opens with its own fresh-eyes read at
09:30. (`docs/RULING-cut-ny-pre.md` carries his words and the receipt: PRE
negative on all three j49-tape runs; cutting it improves every current-era
book.) LONDON/NY_AM caps stay lifted-with-tags; the 09:10 rule is moot.

## Mechanics — unchanged

Fresh prefixes `wr2` / `jr1` (`wr1` is burned) (never reuse a prefix); books to
`output/books/<prefix>/`; day_summary rows authoritative; same capture
sequence, leak checks, §2d never-block, weekly-anchor hard gate; move books
to `output/agent_runs/` only when scored and sealed.

## After `jr1`: STOP AND PUSH

Both books land for his review; `jl1` runs only on his word. After `jl1`,
if it reads like him: paper days (HALT wiring first), Tradovate sync, the
execution agent. **2026-06-07…11** stays in reserve as a second OOS week if
anything needs a re-test; the j49 tape is teaching data and is never the
test.
