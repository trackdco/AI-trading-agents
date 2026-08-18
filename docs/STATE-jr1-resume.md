# jr1 — exact state and how to resume

`wr2` is COMPLETE and pushed (see `docs/FINDINGS-wr2-T78.md`). This file covers `jr1` only.

## Where it stands

Adjudication has gone 61 outstanding -> 16. Run `output/analysis/complete.py jr1` for the
live list; the count moves UP when a take or a thesis re-fire supersedes downstream verdicts,
which is correct, not a regression.

| day | LONDON | NY_PRE | NY_AM |
|---|---|---|---|
| 2026-05-31 | done | done | done |
| 2026-06-01 | done | done | done |
| 2026-06-02 | done | done | A1 done; A2-A6 rebuilt after the bias flip, not yet re-adjudicated |
| 2026-06-03 | done | done | A1/A2/A3 done; A4-A9 rebuilt after A3's fill, not yet adjudicated |
| 2026-06-04 | done | done | A1 done; A2-A6 briefings building |

### The ten live fills, none of them managed or scored yet

    2026-05-31 P2 NY_PRE 08:26 long  30455.00  stop 30434.00
    2026-06-01 P2 NY_PRE 08:35 short 30538.00  stop 30558.00
    2026-06-01 A2 NY_AM  09:46 long  30505.00  stop 30460.00
    2026-06-01 A3 NY_AM  09:55 long  30545.00  stop 30493.00
    2026-06-02 L3 LONDON 03:37 short 30705.50  stop 30730.00
    2026-06-02 L8 LONDON 04:25 short 30712.00  stop 30735.00
    2026-06-03 L1 LONDON 03:22 short 30498.00  stop 30549.00
    2026-06-03 A3 NY_AM  09:52 short 30299.00  stop 30357.00
    2026-06-04 L1 LONDON 03:44 long  30122.50  stop 30099.00
    2026-06-04 P2 NY_PRE 08:44 long  30118.00  stop 30083.00

Two takes did NOT fill and must not be counted against a cap: 05-31 A2 (limit expired 10:07)
and 06-03 P4 (limit ran 08:48).

## What is NOT done

1. **16 trigger adjudications** - the days marked above.
2. **Every manage chain and every exit.** No jr1 position has been managed or scored. This is
   the larger half of the remaining work and it needs frames: run `mkmng2.py` per fill to see
   what `legendpool` already serves and what needs a live capture pass on the j49 tape
   (2026-06-01..05). wr2's 47-frame pass is committed and pools by cursor, so some j49 minutes
   may already be served.
3. **Window closes and day summaries** - none written. `closeday.py` refuses to write if the
   day-summary total and the scorer disagree, so run it last.
4. **Scoring** - `score.py` has no DAYS entry for jr1; add one before running it.

## The loop, in order

    zsh $T/bwj.sh <sd> <dn> <WINDOW>            # build briefings; thesis must be in force first
    # spawn tv-trigger per candidate (10d: parallel only while every prior one PASSES)
    $PY $T/trow.py jr1 <sd> <cid> <HH:MM> <WINDOW> <verdict.json> [tool_uses]
    $PY $T/fillrow.py jr1 <sd> <dn> <cid> <win_end>      # resolves the limit off the bars
    $PY $T/capday.py jr1 <sd> <WINDOW> <cap> <hard> <after_cid> <cid:HH:MM> ...
    $PY $T/mkmng2.py / mng1.py / step.py / xrow.py       # manage chain, exactly as wr2

Caps: LONDON 2, NY_PRE 1 (HARD), NY_AM 2.

## Rules this run has already had to apply, with precedent in the book

- **A take that follows a cap-reaching fill is superseded, not honoured.** Four times in jr1
  (05-31 P3, 06-01 P3-P7, 06-02 L10, 06-04 P3). Two of them removed a fill the agent wanted.
  Use `capday.py`; it refuses if the named candidate has no live fill row.
- **10d speculative parallel adjudication is licensed only while every prior candidate
  PASSES.** When one takes, flag the downstream verdicts `SUPERSEDED_STATE_MOVED`, rebuild
  their briefings `--force`, re-adjudicate.
- **An escalation re-fires Tier 1 and the result is in force FROM THAT MINUTE**, so it
  supersedes every later verdict built against the thesis it replaced. The escalating
  candidate keeps its pass - that is what "pass and raise rather than override" means.
  Budget is 2 per window. 06-03 NY_PRE has spent both; 06-02 NY_AM has one open.
- **Never assert state that has not happened.** 05-31 A3 was flagged on the grounds that A2
  had filled; A2's limit expired unfilled. The flag was rewritten to say what actually
  changed and to name the error. Check `fillrow` output before writing a supersede reason.

## Open questions logged for his ruling

- `harness_finding` on 2026-06-02 L10: a trigger returned `take_light` while listing
  `beyond_written_cap` in its own `constraints_failed`. Cap enforced. Should the LONDON cap
  be HARD in the same sense NY_PRE is - later candidates never adjudicated at all?
- (wr2) `harness_finding` on 2026-06-23 A4: T55 measures trail clearance off the LEVEL with
  no regard for where that level sits in the range actually trading. Cost 1.2287R there.
