# jr1 — exact state and how to resume

`wr2` is COMPLETE and pushed (see `docs/FINDINGS-wr2-T78.md`). This file covers `jr1` only.

## Where it stands

Adjudication, by `output/analysis/complete.py jr1`:

| day | LONDON | NY_PRE | NY_AM |
|---|---|---|---|
| 2026-05-31 | done | done (P2 filled 08:26 @30455.00 long) | done (A2 took 09:57, limit EXPIRED unfilled 10:07) |
| 2026-06-01 | done | done (P2 filled 08:35 @30538.00 short) | A2 filled 09:46 @30505.00 long; A3-A6 rebuilt, re-adjudication in flight |
| 2026-06-02 | done (L3 filled 03:37, L8 filled 04:25, cap reached) | done | A1/A2/A3 adjudicated; **escalation open at 09:36** |
| 2026-06-03 | done | P1/P2/P3 done, **both escalations spent**; P4/P5 rebuilt, not yet adjudicated | not started (briefings building) |
| 2026-06-04 | done | done (P2 filled 08:44 @30118.00 long) | not started |

## What is NOT done

1. **Trigger adjudication** — the days marked above. Run `complete.py jr1` for the live list.
2. **Manage chains and exits** — NO jr1 position has been managed or scored yet. Three fills
   from before this session (06-02 L3, 06-03 L1, 06-04 L1) are still unmanaged, plus every
   fill listed above.
3. **Window closes and day summaries** — none written.
4. **Scoring** — `score.py` has no DAYS entry for jr1; add one before running it.

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
