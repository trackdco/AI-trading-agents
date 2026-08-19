# jr2 adjudicated on a book with no exits — parity break with jr1, caught mid-run

**Status: found and repaired inside jr2. No ruling needed; the fix is mechanical.**

## What happened

jr2's adjudication ran the three windows of five days *before* the manage phase, so at no point
during adjudication did the book contain a single `exit` row. `position_state` in every trigger
briefing is derived from the book. With no exits in it, a position that filled at 09:46 still
reads **OPEN** at 10:45, and in the next window, and the window after that.

To be precise about what is and is not the defect: carrying a position *across* a window
boundary is legitimate and written — T51, restated in every manage `window_note`, is explicit
that "a position open at the window close is NOT force-flattened; the window gates TAKING
trades, not holding them." The defect is not that positions cross windows. It is that in jr2
they never **close** — not at their stop, not at their target, not ever — because the phase
that closes them had not been run.

jr1, on the same tape, did not do this:

| run | 05-31 | 06-01 | 06-02 | 06-03 | 06-04 |
|---|---|---|---|---|---|
| jr1 fills / exits | 1 / 1 | 3 / 3 | 3 / 3 | 2 / 2 | 3 / 3 |
| jr2 fills / exits | 2 / **0** | 5 / **0** | 2 / **0** | 2 / **0** | 1 / **0** |

jr1 interleaved: on 06-01 its A2 exited at 09:55 and its A3 filled at 09:55. jr2 could not have
produced that sequence, because in jr2's book A2 never closes.

This is the `state-files-go-stale` trap in its purest form. The state was not hand-written this
time — it was *derived from the book*, which is the fix that trap normally calls for. But the
book was missing the rows that make the derivation correct.

## The smoking gun

06-04 L3 (04:22) was re-adjudicated against an "open" L2 short. The trigger agent noticed
unprompted:

> `position_state` shows an OPEN short (L2, 30,132.00, stop 30,172.00) that this candle's high
> (30,173.25) has traded through — that is a management-layer fact for `tv-manage`.

L2 was stopped out at 04:22 by the very candle being adjudicated, and the book still called it
open. The agent was right to hand it to the management layer; the orchestrator was wrong to have
never run one.

## Why it matters

The open-position gate (0.4.13 §2e duty 4) is absolute and is evaluated against exactly this
state. Over-reporting a position as open cuts in two directions:

- candidates **wrongly gated** — refused a trade that was legal, because the prior position had
  in fact already closed;
- candidates that **took anyway** on the agent's own judgement, reasoning explicitly about an
  open position that was not actually open.

It is *not* a uniformly conservative error, so it cannot be waved through as "errs safe".

## Blast radius as found — small and enumerable

- mechanically gated on an open position: 06-02 L6, L8, L10; 06-03 A4
- agent cited an open position in its reasoning: 06-02 L6, L8 (merit `take_full`, both
  superseded by the gate rows above)
- 06-01 A5 (10:34) and A6 (10:45) **filled** as same-direction longs stacking on an "open" A2
  (09:46). Whether that was legal depends entirely on whether A2 had exited — which the book
  could not say.

## The repair

The narrowest fix that restores parity, per `dont-over-correct-after-solid-run`:

1. Run the manage phase over the fills already in the book, so real `exit` rows land.
2. Re-derive `position_state` at each affected decision minute from the repaired book.
3. Re-adjudicate **only** those candidates whose disposition actually turns on the answer.
   Everything else stands untouched.
4. Finish the remaining windows against the repaired book, so the error stops propagating.

Restarting jr2 would discard ~90% of a completed adjudication to fix a defect touching six rows.
Not proportionate.

## What this does not change

The T78 bounce count — the thing jr2 was run to measure — is independent of this. It counts
target rungs on emitted takes, and no take's target ladder depends on the position state.

## The process lesson, which is the real finding

The manage phase is not a post-processing step. It is part of the state the *next* adjudication
reads. Deferring it does not delay work; it silently corrupts the input to everything downstream.
Any future run must interleave manage with adjudication exactly as jr1 did, or it is not
comparable to jr1.

---

## Addendum: a leak-guard false positive found while finishing the run

`runmanage.py`'s forward-reference blacklist contained the bare phrase `"no further"`. Its
purpose is to stop a briefing telling an agent what the SCANNER will do next ("there are no
further candidates"), because the scanner list is derived from the whole day's bars. But as a
bare substring it also fires on ordinary thesis prose about a price ceiling — the 2026-06-04
NY_AM in-force thesis contains "a long here targets **no further** than that 2m/3m MA", which
names no minute and leaks nothing. It refused all five NY_AM briefings for that day.

Fixed by scoping the phrase to its candidate/setup forms (`no further candidate`,
`no further setup`, `no further signal`, `no further trigger`, `no further scan`) and keeping
every other entry. `further candidate` already covered "no further candidates". Verified
against four probes: the three genuine leak wordings are still caught, the price-ceiling
sentence now passes.

The alternative — rewriting the thesis agent's own emitted text to dodge the checker — was
rejected. Editing an agent's output to satisfy a faulty guard corrupts the record of what the
agent actually said.

---

## Addendum 2: 06-02 L10 was resolved WITHOUT a manage phase — chart navigation failed

One position in jr2 does not have a manage chain, and its result must be read with that in mind.

`06-02 L10` (short, filled 04:48 @ 30724.0, stop 30737.0, R=13.0pt) was reinstated late in the
run, when the repaired book showed L3 had exited at 04:07 and L8 at 04:28 — so its gate was
withdrawn and it filled legitimately. Its four manage frames sit on tape-day 2026-06-03 and had
never been captured by any run.

They could not be captured. The TradingView replay wedged partway through: `replay start`
returns `success: true` with `is_replay_started: true`, and `replay step` returns success, but
the cursor stays pinned at 1780470359 and never advances. CDP is connected and the chart answers
`state`/`status` normally — only replay is stuck. A stop/start cycle, a resolution change, and a
start on a different date all failed to free it. This needs the TradingView app restarted by
hand, which is outside what this run can do.

**Disposition, per the never-block rule:** L10 is resolved MECHANICALLY at its written stop and
targets, with no discretionary management. That is the conservative direction — an unmanaged
position takes its full stop rather than benefiting from a trail or a banked partial, so this
cannot flatter the run. Its exit row is tagged `manage_phase: "NOT RUN - chart navigation
failure"` so it is never mistaken for a managed result.

**What this costs:** one position out of fourteen carries an unmanaged outcome. Every other
position in jr2 was managed call-by-call. The T78 bounce count — what jr2 exists to measure — is
untouched, since it counts target rungs at emission and does not depend on management at all.

**To finish it properly:** restart TradingView, then run
`capdrive.py capwork_l10c.json` (the corrected-cursor worklist), rebuild L10's state, and run its
chain through `mround.py`. The exit row should then be superseded rather than edited.
