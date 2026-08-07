# NQ MBP-10 depth — LONDON window, 2023/24 HOLDOUT

Per-minute top-10 book snapshots for **08:00–10:00 Europe/London**, covering the 128
pre-registered holdout days (`docs/HOLDOUT-2023-24-PREREGISTRATION.md`, seal `f4e17f17…`).

**Status: ✅ COMPLETE — 128/128 sealed days, 15,360 rows, 5.6 MB.**

| | |
|---|---|
| files | 128 (`glbx-mdp3-YYYYMMDD.mbp-10_condensed.csv`) |
| rows | 15,360 |
| minutes/day | **exactly 120 on every day** — no short sessions |
| columns | 74, the raw Databento MBP-10 set |

Wide format, matching `depth_london/`: one row per minute carrying all 20 levels as
columns, rather than the long format NY uses. `scripts/london_depth.load_day` reshapes it
internally, so the shape difference is deliberate, not an inconsistency.

## Kept SEPARATE from `depth_london/` on purpose

`scripts/london_depth.py` has `DIR = Path("data/reference/depth_london")`. To score the
holdout, point it here:

```python
import scripts.london_depth as L
L.DIR = Path("data/reference/depth_london_2023_24")
```

That one line is the entire integration, and it is verified — `load_day("2023-07-03")`
returns 2,400 long-form rows and `depth_at` produces a full feature dict.

The files could have been dropped into `depth_london/` (the dates do not collide) and
`load_day` would have worked with no change at all. They are not, deliberately: a single
folder holding both fit and holdout data is exactly how a holdout gets silently scored as
fit. The path parameter is cheap; that mistake is not.

## Window: 08:00–10:00 London, declared in London time

Localized per-day in `Europe/London`, so the March and November weeks where UK and US
daylight saving disagree resolve correctly — on 2023-03-15 the London window is 08:00Z
while the NY window is 12:00Z, four hours apart rather than five.

## Unlike the NY holdout, this format KEEPS the order count

All 20 `bid_ct_NN` / `ask_ct_NN` columns are present, so one order of 500 is
distinguishable from fifty of 10. `depth_2023_24/` (NY) does not carry it, and neither do
the fit-window NY folders — see that README. **London is therefore the only place where
whether order count carries signal can be tested, in-fit and out-of-fit, with no new data.**
