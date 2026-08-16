# STANDING CONSTRAINT — what MBP-10 can and cannot see (NQ)

**Nobody should build a heatmap feature that cannot exist.** This file is
here so that never happens again.

## The measurement (empirical, 2026-08-07)

NQ tick = 0.25 pt. MBP-10 publishes **ten price levels per side**. Measured
directly on the raw condensed MBP-10 files (`data/reference/depth_london/
glbx-*.mbp-10_condensed.csv`, level 0 -> level 9 span):

| side | median span | p90 | max |
|---|---|---|---|
| bid (L0→L9) | **2.25 pt** | 2.50 pt | 3.25 pt |
| ask (L0→L9) | **2.25 pt** | 2.50 pt | 3.00 pt |

The simple per-minute files (`nq_depth_*_ny.csv`) agree: 10 levels/side/
minute, span 2.25 pt.

## What follows, and it is not negotiable

- **"Is there a wall right here?" is ANSWERABLE.** Anything inside ~2.25 pt
  (≈9 ticks) of touch is inside the book we receive.
- **"Is there a magnet 30 points away?" is NOT ANSWERABLE.** It is roughly
  13x beyond the deepest level MBP-10 carries. No amount of feature
  engineering recovers a price level the feed never published.
- Any depth feature whose definition references a distance materially
  beyond ~2.5 pt is measuring the ABSENCE of data, not the presence of
  structure. Such a feature will look stable (it is mostly a constant or a
  NaN pattern) and mean nothing.
- Deep-book "liquidity magnet" / "heatmap target" ideas require a
  full-depth (MBO or full-book) feed. They are out of scope on MBP-10 and
  must be declared out of scope rather than approximated.

## Coverage, separately from reach

Reach is not the only limit — the archive's TIME coverage is narrow:

| source | window (NY) | files |
|---|---|---|
| `nq_depth_*_ny.csv` | 08:00–10:29 | 381 |
| `nq_depth_*_london.csv` | 02:00–05:58 | 22 |
| `glbx-*.mbp-10_condensed.csv` | 03:00–04:59 | 423 |

Against the composite book this is **799 of 3,336 fights = 24.0%**, and the
depth-eligible subpopulation is better than average (EV +0.286 vs +0.186),
so any depth result carries a selection confound that must be declared in
advance (see PREREG-flow-depth-intrade.md, section B Law 7).
