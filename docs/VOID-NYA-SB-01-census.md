# VOID — NYA-SB-01 census, 2026-08-06. No verdict. No trials recorded.

The census declared in `PREREG-nya-silver-bullet.md` (08:03:40Z) **ran and is being
discarded as invalid**. Recording it rather than deleting it, because the failure mode is
the useful part.

---

## What happened, in order

1. Feasibility on the full gate stack: **73 / 72 entries** across 2025H2 / 2026H1. Clear.
2. Census ran. Result: **WR 2.7% / 13.9%** against a 33.3% break-even bar, **−91.2R** over
   145 trades.
3. **I did not report that.** A 2.7% win rate at 2R is below what a random entry produces
   (~33%), which is a signature of an implementation fault, not a weak edge.
4. Checked my stop sizes against his stated ones. **Mine: median 58 pts, mean 93, max 543.
   His, across three videos: 27, 28, 51, 53 pts.** My stop was 2–10× too wide, so a 2R
   target sat 116+ points away inside a 30-minute window — unreachable by construction.
5. Corrected the stop to the FVG's far edge (structural invalidation of the displacement).
   **Median risk 3.75 pts** — now 10× too *tight*.

## Why this is now a specification problem, not a coding one

Two defensible readings of *"I'd run my stop at the most recent short-term low"*
`[qngA8aIfV0M @ 08:01]` bracket his stated stop sizes without matching either:

| reading | median risk | his stated |
|---|---|---|
| the swept extreme | 58 pts | **27–53 pts** |
| the FVG far edge | 3.75 pts | |

**A third attempt would be me tuning a stop definition until it reproduces his reported
numbers. That is fitting a spec to a target, and it is precisely what pre-registration
exists to prevent.** So the census stops here.

## The finding: a FOURTH unspecified component

Added to the three already open (order-block identification, bias aggregation, the
"clear draw" gate):

> **4. Stop placement.** *"The most recent short-term low"* is not mechanically resolvable.
> His own examples (27/28/51/53 pts) do not disambiguate it, and the two natural readings
> land an order of magnitude apart. **Stop distance sets R, and R sets the entire result** —
> this is not a detail, it is the load-bearing parameter.

## Trial accounting

**Zero trials recorded.** Nothing appended to `output/trial_ledger.parquet`; the merged
ledger stays at 52. An invalid measurement is not a lottery ticket, and recording it would
corrupt the §6.0 denominator with an arm that tested nothing.

## What IS established, and stands

The gate stack is real and countable — **73 / 72 entries, 0.54/day over 269 trading days**,
from macro → sweep → MSS → FVG → fill. The events exist at testable frequency. That result
required no outcome and is unaffected by the stop question.

## To make this testable

One of:
- **Ask him.** Four videos give stop sizes but never the rule; a direct answer closes it.
- **Find a video that states it** — `PmMsxenKlVY` ("FULLY EXPLAINED") is the best remaining
  candidate and is still rate-limit blocked.
- **Declare our own stop and label it ours** — e.g. fixed 30-point risk, which sits inside
  his observed range. Legitimate, but it tests *our* variant, and under §5.9.1 a null could
  not touch his model.

---

## Addendum — stop/target sizes, and a THIRD implementation error

**Stops and targets actually used:**

| variant | median stop | median target (2R) |
|---|---|---|
| v1 swept level | 58 pts | **116 pts** |
| v2 FVG far edge | 3.75 pts | 7.5 pts |
| **his stated** | **27 / 28 / 51 / 53 pts** | **54–106 pts** |

**How far price actually travels in each 30-minute window (median day range):**

| window | median | p75 | p90 |
|---|---|---|---|
| AM1 09:45 | **129.8** | 173.8 | 229.8 |
| AM2 10:45 | 90.2 | 131.0 | 171.4 |
| LUNCH 11:45 | 69.8 | 100.8 | 148.9 |
| PM 13:45 | **56.0** | 87.5 | 119.0 |

This confirms v1 was dead on arrival — a 116-point target exceeds the median range of
three of the four windows.

**But it also exposes a third error of mine.** His own stops (27–53 pts) imply targets of
54–106 points. **In the PM macro a 106-point target exceeds the entire median window range
of 56 points.** His trades therefore cannot be resolving inside the 30-minute window —
**the entry must occur in the macro, but the trade runs on past it.**

My census resolved every outcome **within the window** and marked unresolved trades to
market at the close. That truncates the model. It barely bit v2 (3/145 truncated, because
7.5-point targets resolve fast) but it would have been severe at his real target distances.

**Consequence:** the exit horizon is a fifth unspecified component, and my truncation was
wrong regardless of what he does.

## v2 results — recorded, still void, still not evidence

| window | n | win rate | mean R | 2025H2 → 2026H1 |
|---|---|---|---|---|
| AM1 | 48 | 31.3% | −0.22 | 36.0% → 26.1% |
| AM2 | 33 | 30.3% | −0.03 | 18.8% → 41.2% |
| LUNCH | 26 | 38.5% | +0.40 | 50.0% → 31.3% |
| PM | 38 | 34.2% | +0.33 | 27.3% → 43.8% |

Overall **33.1%** — indistinguishable from the 33.3% break-even rate, i.e. what a coin flip
at 2R produces.

**No window is stably better: every one flips direction between eras.** AM1 and LUNCH fall,
AM2 and PM rise. That is noise, and it is also the pattern PBO 0.891 predicts for
rank-and-pick on this kind of arm set.

Note it contradicts his claim that AM1 is highest-probability — AM1 is the *worst* cell
here. That is not evidence against him; it is evidence that this run measures my
specification, not his model.

**And v2 is untradeable anyway:** a 3.75-point stop is ~$75 on a 1-lot NQ. Commission plus
one tick of slippage each way is a double-digit percentage of risk. The §2.5 cost stack
would erase it.
