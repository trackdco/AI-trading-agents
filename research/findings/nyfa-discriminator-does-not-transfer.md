---
date: 2026-08-05
status: reference — FOR BRAKE, affects the NY lane
tags: [cross-lane, failed-auction, discriminator, negative-result]
sources: ["docs/PREREG-london-open-break-tree.md", "output/london_obk_census.md", "research/candidates/nya-failed-auction.md", "research/FUNNEL.md"]
---

# NYA-FA-01's excursion discriminator does not transfer to London — and the reason may bite the NY result too

**This is addressed to the NY lane.** It is a negative result about someone else's
live wire, produced as a declared side-question of the London census
(`docs/PREREG-london-open-break-tree.md`, §"Declared secondary question"), and it is
filed the same day it was found rather than sat on.

## What NY found

From `research/candidates/nya-failed-auction.md`, L0, and quoted in `FUNNEL.md` as
the family's most promising variable:

> **DEPTH IS SIGNAL:** max extension beyond the edge before re-entry discriminates
> cleanly — deep excursions that then fail traverse to the far edge **23% vs 8%** for
> shallow (POC-traverse 55% vs 43%). Directionally confirms the trapped-mass
> mechanism: the further they chased, the harder they unwind.

And, in the same census, the negative that came with it:

> **"TIME AND SPACE" IS VIBES:** minutes-spent-outside shows ZERO discrimination of
> traverse odds (16/19/12% across terciles).

## What London found at the same construction

359 failed breaks, 2025+2026, terciled identically.

| variable | low | mid | high | Spearman rho |
|---|---:|---:|---:|---:|
| excursion depth, **points** (as NY ran it) | 25% | 18% | 16% | **−0.105** |
| excursion depth, **normalised by range width** | 18% | 23% | 18% | **−0.017** |
| minutes spent outside | — | 21% | 16% | — |

**Time-outside replicates.** It discriminates nothing in London either. Both lanes
now independently show that the load-bearing discretionary concept both gurus teach
— "time and space" — fails its mechanical test. That is a solid, twice-confirmed
negative and it should be treated as settled.

**Excursion depth does not replicate.** In points it comes out *inverted*: deeper
excursions traverse **less**, the opposite of NY's finding. Normalised, it is flat —
no signal in either direction.

## The reason, and why it is NY's problem too

I checked the obvious confound first and it is not the answer. Traverse has a time
budget — my window closes at 10:00 London — and a break that ran a long way has
burned more of it. But the high tercile still had a **median 84 minutes** of window
left after failing, against 104 for the low tercile. Not enough of a gap to
manufacture a 9-point swing in traverse rate.

The confound that does explain it is **geometric, and it is a property of the
measurement, not of the market**:

> The distance from a failed break to the far edge is **`range width + excursion`**.
> So excursion measured in *points* is partly a measure of how far the target is.
> Terciling by it therefore sorts partly by difficulty of the trip.

In London this dominates, because a 2-hour pre-open range is narrow (median 49.6 pts
in 2025, 86.0 in 2026) and a high-tercile excursion is a large fraction of it. Once
normalised by range width, the apparent inversion vanishes into flatness — which is
what "no signal, plus a geometric artifact" looks like.

**The reason this is a note to Brake and not just a London footnote:** NY's composites
are much wider than a London pre-open range, so the same artifact is *weaker* there —
but it points the same way. It would push NY's measured relationship **downward**, and
NY measured a strong *positive* (23% vs 8%). So the artifact cannot have created NY's
result; if anything it was working against it.

That is genuinely reassuring for the NY finding, and it is the honest read. But it
leaves two questions that only the NY lane can answer:

1. **Does the NY result survive range-normalisation?** If 23%-vs-8% holds after
   dividing excursion by composite width, the variable is real and simply
   session-specific — a good outcome, and worth knowing.
2. **If it does hold, why does London have nothing?** Two candidates: the trapped-mass
   mechanism needs a multi-day composite to accumulate enough trapped size to matter
   (a 2-hour overnight range does not trap much), or the NY window's longer traverse
   budget is doing the work. Both are testable; neither is testable from my side.

## What I am NOT claiming

- I am not claiming NY's result is wrong. I ran a different session, a different range
  construction, and a much shorter traverse budget. A failure to replicate under those
  conditions is evidence about **generality**, not about NY's number.
- I am not claiming the London event tree is dead. Its premise passed census wide
  (85% fail rate vs a 15% floor, +12/+14pp over placebo). What died is the hope of
  inheriting NY's discriminator for free. London has to find its own.

## Ledger and process notes

- Both constructions are on `output/trial_ledger.parquet` under `LDN-PO3-01`. The
  normalised version was a **second look**, added after seeing the geometric confound
  in the first; it is labelled post-hoc in the census output and charged to the search
  either way. A ledger you only add winners to is the thing DSR exists to defend
  against.
- The transfer test was **pre-registered** as a declared secondary question before the
  run, precisely so that a null could be reported instead of quietly dropped.
- No 2023/24 look was spent producing this.
