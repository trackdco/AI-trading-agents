# A briefing named a screenshot that did not exist — and the thesis flipped when it did

Found 2026-08-20, jl1 day 1, on the first live firing of runbook §2e duty 2.

## What happened

`mkth_jl1.sh` named every thesis screenshot `jl1_<sd>_<WINDOW>_<hhmm>.png`. That file exists for
a **window open** (03:00, 09:30) because the capture pass shoots one there. It does not exist for
any mid-window minute — an escalation or a duty-2 re-read — where the only frame captured at
that cursor is the **candidate** frame, `jl1_<sd>_<cid>_<hhmm>.png`.

The duty-2 re-read at 09:46 was therefore handed a path to a file that was never created.

## Why it matters more than it looks

The agent did the right thing: it said so, explicitly, and fell back to the parity-gated legend
in the briefing rather than pretending it had seen a chart. It emitted a coherent thesis.

Then the same re-read was re-run with the screenshot that actually exists:

| | bias | escalation_response |
|---|---|---|
| blind (legend only) | **short** | reaffirmed |
| sighted (chart read) | **long** | accommodated |

Same minute, same briefing, same legend numbers. The sighted read saw what the legend could not
convey — price sweeping the licensed VAL/VWAP-1 zone at 29,776.25 and displacing ~177pt back
through VWAP, the 15m MA and the 29,938-40 cluster that had rejected it twice, closing 0.93-body
at 29,953.75 — and flipped the primary bias. The blind read reaffirmed the short and would have
carried a stale side-lock into five more candidates.

**A missing screenshot does not fail loudly. It silently degrades a chart-reading tier to a
number-reading tier, and the numbers alone can support the opposite conclusion.**

## Fixed

`mkth_jl1.sh` now resolves the screenshot per minute: window-open frame if one exists, otherwise
the candidate frame captured at that same cursor (same tape, same cursor, same pixels — the
manage/candidate/thesis distinction lives in the filename and the briefing, never in the image).
The re-read was re-run sighted and the sighted verdict is the one in the book.

## The pattern worth keeping

This is the fourth defect in two runs found by an agent objecting to its INPUT rather than by
anyone checking its output: the 06-04 trigger that spotted a stop already traded through, the
manager about to double-bank a partial it had already taken, the macro spawn that refused to
fabricate a gate it could not read, and now this. The tiers that can say *"what you handed me
does not add up"* are doing more quality control than any downstream check.
