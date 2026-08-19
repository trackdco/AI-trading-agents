# jr2 — the j49 tape under tv-trigger 0.4.13, with the T78 ladder bounce LIVE

Same tape as jr1 (session-days 2026-05-31 … 2026-06-04, three windows a day). The only
substantive change is that the schema example now shows two target rungs instead of one, plus
runbook §2e duty 4: any take emitted with fewer than two targets is re-spawned once with
"T78: name TP2 — the next structure at least ~1R beyond TP1", then proceeds per §2d tagged
`t78_single_target`.

## The question jr2 was run to answer

> "Count the bounces — I want to know how often the first emission still comes back
> single-target."

## The answer: never. Not once.

| | |
|---|---|
| take emissions by `tv-trigger` across the run | **37** |
| emitted with FEWER than two target rungs | **0** |
| bounces spent (`T78: name TP2`) | **0** |
| rows tagged `t78_single_target` | **0** |

Rung distribution: **26 takes with two rungs, 11 with three.** Not a single take needed the
bounce. The ladder  ledger is empty because nothing ever owed one.

This counts EVERY emission, including verdicts later superseded by a re-fired thesis or a
withdrawn gate — i.e. it counts first emissions, which is what the question asks about. The
live book alone carries 25 takes, also with zero shorts.

**Read against the change that produced it:** "schema beats prose" holds. Showing two rungs in
the schema example was sufficient on its own; the bounce that backs it up never had to fire.
The duty-4 machinery is therefore unexercised by this run — it is proven present, not proven
effective, because nothing tested it.

## Scored result

14 closed trades.

| | as-run (blended) | full-target |
|---|---|---|
| TOTAL | **−2.1792R** | +1.2667R |

Only 2 of the 14 ever banked a partial, so the 75/25 counterfactual can only bite on those two:
across that pair it is +0.2111R ahead of as-run. Two trades is not a ruling — that is the
mechanism, not the verdict.

Per-trade detail is in `output/books/jr2/` and reproduced by `score.py jr2`.

## What else this run turned up

Five defects, all found and fixed mid-run, all logged:

1. **jr2 adjudicated against a book with no exit rows** — the big one. The open-position gate is
   evaluated against exit state, and jr2 had none, so the gate was decided on stale state.
   jr1 interleaved manage and is clean. Full write-up, including the repair and the process
   lesson, in `docs/FINDING-jr2-adjudicated-on-a-book-with-no-exits.md`.
2. **`alive.py` hard-coded the NY_AM window end** — the same defect already fixed in `step.py`;
   it would have run every LONDON and NY_PRE chain against 11:00.
3. **The round driver never rebuilt manage state between rounds** — managers were briefed with
   the entry stop and an empty action history and could not see their own trails or partials.
   Caught when a manager was about to bank a second 50% partial. 14 rows rolled back and redone.
4. **The capture driver synced its pooled copy only at exit**, making frames invisible to
   anything running concurrently; and it gave up on long forward walks after one retry.
5. **A leak-guard false positive** — the bare phrase `"no further"` refused five briefings over
   ordinary thesis prose about a price ceiling. Narrowed to its scanner-scoped forms.

The gate repair changed real outcomes: 06-02 L8 and L10 were wrongly gated and are reinstated
(both filled), 06-01 A6 was wrongly filled and is voided, and 06-03's whole NY_AM window
re-adjudicated against a re-fired thesis, flipping three of four verdicts.

## Known limitation

**06-02 L10 has no manage chain.** TradingView's replay wedged and its four frames could not be
captured; the position is resolved mechanically at its written stop, which is the conservative
direction. Tagged in the book and documented in addendum 2 of the finding above. One position
of fourteen; the bounce count is unaffected.
