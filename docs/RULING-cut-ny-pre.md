# RULING — NY_PRE IS CUT. London and New York AM only.

**His decision, 2026-08-17, stated twice:** *"im thinking of cutting ny pre
entirely im not gonna lie"* … *"id be happy to just cut ny pre and run london
an ny am."*

**Effective for runs AFTER `j49`.** Not mid-flight — `j49` was already
running with NY_PRE live when the ruling was made, and changing the window
set underneath it would produce a book whose days do not share a
configuration. It finishes as-is; its NY_PRE rows are simply excluded at
scoring, which also gives a second measurement of what the cut costs.

## What it costs, measured on the fit week before deciding

| | R | points | candidates adjudicated |
|---|---|---|---|
| w49 **with** NY_PRE | +16.279 | +1,320.9 | 81 |
| w49 **without** NY_PRE | +14.701 | +1,266.7 | 60 |
| **cost of the cut** | **−1.578R** | **−54.2pt** | **26% less work** |

## The case AGAINST cutting, recorded because it was real and was overruled

Put to him before the decision and reaffirmed against:

- Across **87 independent session-days**, NY_PRE has the **highest mechanical
  hit rate of the three windows** — 36.2% of its 207 triggers reach 2R and
  55.6% reach 1R, both better than LONDON and NY_AM. The raw opportunity in
  pre-market is real.
- In the agent books it is **net positive**, +1.46R across `jn1` and `w49`.
- The decision rests on **eight filled trades**. That is not a sample.

## His reasoning, which is a risk ruling and outranks the base rates

> *"staying in a trade on market open hoping it goes to tp is practically a
> gamble, it could stop you then run to tp in the same candle. id prefer to
> just leave it."*

He is describing the 09:30 candle, and he is right about the mechanism. It
also happens to be **the one case our own scoring cannot adjudicate**: every
book here uses a touch model, so a bar whose range spans both the stop and
the target produces an R we cannot verify, because bar data cannot say which
printed first. A position carried through the open is therefore both a real
gamble and an unmeasurable one.

NY_PRE's structural handicap follows from the same place. T51 force-flattens
every pre-market carry by 09:29:59, so the window with the best hit rate is
the one whose winners are cut off before they can run — one fill a day,
capped at ninety minutes, hard exit at the bell. Rather than relax T51 to
harvest it (which is the gamble he just refused), the window goes.

**This is a deliberate trade, not a leak:** ~1.6R a week and a quarter of the
adjudication load, exchanged for never holding risk through the cash open.

## What changes

- Windows become **LONDON 03:00–04:59** and **NY_AM 09:30–11:00**.
- **T52 (09:10 entry cutoff) and T51 (flatten by 09:29:59) become dead
  letters** — there is no pre-market position to cut off or flatten. Both
  stay written in the contracts against NY_PRE being restored; they simply
  never fire.
- Caps: LONDON 2, NY_AM 2.
- Candidate ids keep the `L`/`A` prefixes; `P` retires.

## Reversal

One line. `WINDOWS` in `scripts/offline_scan.py` and `scripts/offline_day.py`,
and the window list in the runbook. Restoring NY_PRE restores T51/T52 with
it, unchanged. If `j49` shows pre-market carrying days the other two windows
miss, that is the evidence that would justify revisiting.
