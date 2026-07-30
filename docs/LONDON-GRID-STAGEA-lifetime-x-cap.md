# London grid audit — Stage A: order lifetime x cap

**Fit only. Sealed 2023/24 never loaded.**

**Grid size declared upfront: 8 lifetimes x 3 cap levels = 24 cells.** Shrinkage charged to every winner at this breadth: **+0.218 R** (interpolated on the stage-3 curve; see module docstring — three anchor points, so a correction of the right order, not a precise quantity).

Lifetime is derived from L1's `max_away_before_fill`: a distance cancel of X pts is the filter `max_away < X`. `inf` = no distance cancel, order lives to the session window end (the ANGUS ruling).

## The grid — per era, 1 NQ lot

| lifetime | cap | era | n | WR | raw R | **adj R** | net | maxDD |
|---|---|---|---|---|---|---|---|---|
| 10pt | 1/session | 2025 | 33 | 64% | +0.602 | **+0.384** | $+4,921 | $422 |
| 10pt | 1/session | 2026 | 36 | 42% | +0.441 | **+0.223** | $+3,011 | $1,260 |
| 10pt | 2/session | 2025 | 41 | 61% | +0.550 | **+0.332** | $+5,569 | $542 |
| 10pt | 2/session | 2026 | 46 | 41% | +0.438 | **+0.220** | $+4,206 | $1,662 |
| 10pt | uncapped | 2025 | 43 | 58% | +0.483 | **+0.265** | $+5,164 | $672 |
| 10pt | uncapped | 2026 | 53 | 42% | +0.449 | **+0.231** | $+4,958 | $1,341 |
| 15pt | 1/session | 2025 | 45 | 64% | +0.590 | **+0.372** | $+6,162 | $735 |
| 15pt | 1/session | 2026 | 43 | 42% | +0.323 | **+0.105** | $+2,665 | $1,460 |
| 15pt | 2/session | 2025 | 58 | 60% | +0.503 | **+0.285** | $+6,485 | $1,842 |
| 15pt | 2/session | 2026 | 62 | 44% | +0.411 | **+0.193** | $+5,844 | $1,420 |
| 15pt | uncapped | 2025 | 60 | 58% | +0.456 | **+0.238** | $+6,080 | $1,842 |
| 15pt | uncapped | 2026 | 72 | 43% | +0.396 | **+0.178** | $+6,408 | $1,341 |
| 20pt | 1/session | 2025 | 49 | 61% | +0.493 | **+0.275** | $+5,200 | $735 |
| 20pt | 1/session | 2026 | 45 | 47% | +0.492 | **+0.274** | $+4,789 | $950 |
| 20pt | 2/session | 2025 | 65 | 62% | +0.482 | **+0.264** | $+6,918 | $1,609 |
| 20pt | 2/session | 2026 | 67 | 48% | +0.541 | **+0.323** | $+8,379 | $1,255 |
| 20pt | uncapped | 2025 | 69 | 59% | +0.424 | **+0.206** | $+6,411 | $1,710 |
| 20pt | uncapped | 2026 | 81 | 48% | +0.542 | **+0.324** | $+10,450 | $1,245 |
| 22pt | 1/session | 2025 | 50 | 62% | +0.506 | **+0.287** | $+5,500 | $735 |
| 22pt | 1/session | 2026 | 47 | 51% | +0.594 | **+0.376** | $+6,100 | $950 |
| 22pt | 2/session | 2025 | 66 | 64% | +0.516 | **+0.298** | $+7,585 | $1,609 |
| 22pt | 2/session | 2026 | 71 | 51% | +0.643 | **+0.425** | $+10,520 | $1,235 |
| 22pt | uncapped | 2025 | 71 | 61% | +0.436 | **+0.218** | $+6,829 | $1,710 |
| 22pt | uncapped | 2026 | 85 | 51% | +0.627 | **+0.409** | $+12,591 | $1,245 |
| 25pt | 1/session | 2025 | 50 | 62% | +0.506 | **+0.287** | $+5,500 | $735 |
| 25pt | 1/session | 2026 | 49 | 49% | +0.434 | **+0.216** | $+4,312 | $1,075 |
| 25pt | 2/session | 2025 | 66 | 64% | +0.516 | **+0.298** | $+7,905 | $1,289 |
| 25pt | 2/session | 2026 | 73 | 51% | +0.574 | **+0.356** | $+9,279 | $1,305 |
| 25pt | uncapped | 2025 | 71 | 61% | +0.436 | **+0.218** | $+7,149 | $1,390 |
| 25pt | uncapped | 2026 | 91 | 52% | +0.646 | **+0.428** | $+13,490 | $1,245 |
| 30pt | 1/session | 2025 | 50 | 62% | +0.506 | **+0.287** | $+5,500 | $735 |
| 30pt | 1/session | 2026 | 51 | 47% | +0.376 | **+0.158** | $+3,782 | $1,132 |
| 30pt | 2/session | 2025 | 66 | 64% | +0.516 | **+0.298** | $+7,905 | $1,289 |
| 30pt | 2/session | 2026 | 77 | 49% | +0.519 | **+0.301** | $+9,171 | $2,380 |
| 30pt | uncapped | 2025 | 71 | 61% | +0.436 | **+0.218** | $+7,149 | $1,390 |
| 30pt | uncapped | 2026 | 93 | 49% | +0.543 | **+0.325** | $+11,968 | $2,582 |
| 40pt | 1/session | 2025 | 50 | 62% | +0.506 | **+0.287** | $+5,500 | $735 |
| 40pt | 1/session | 2026 | 53 | 49% | +0.342 | **+0.124** | $+3,535 | $950 |
| 40pt | 2/session | 2025 | 66 | 64% | +0.516 | **+0.298** | $+7,905 | $1,289 |
| 40pt | 2/session | 2026 | 80 | 51% | +0.522 | **+0.304** | $+9,670 | $1,660 |
| 40pt | uncapped | 2025 | 71 | 61% | +0.436 | **+0.218** | $+7,149 | $1,390 |
| 40pt | uncapped | 2026 | 101 | 50% | +0.548 | **+0.330** | $+13,194 | $2,385 |
| window-end | 1/session | 2025 | 53 | 62% | +0.495 | **+0.277** | $+5,821 | $1,008 |
| window-end | 1/session | 2026 | 54 | 52% | +0.448 | **+0.230** | $+5,062 | $950 |
| window-end | 2/session | 2025 | 71 | 63% | +0.466 | **+0.248** | $+7,579 | $1,619 |
| window-end | 2/session | 2026 | 84 | 54% | +0.582 | **+0.364** | $+11,269 | $1,825 |
| window-end | uncapped | 2025 | 78 | 62% | +0.434 | **+0.216** | $+8,178 | $1,720 |
| window-end | uncapped | 2026 | 109 | 53% | +0.570 | **+0.352** | $+14,618 | $2,550 |

## Slot contention — measured

| lifetime | cap | candidates whose trigger fell inside an open trade |
|---|---|---|
| window-end | 1/session | 55 |
| window-end | 2/session | 75 |
| window-end | uncapped | 93 |
| 22pt | 1/session | 45 |
| 22pt | 2/session | 62 |
| 22pt | uncapped | 67 |
| 15pt | 1/session | 35 |
| 15pt | 2/session | 45 |
| 15pt | uncapped | 49 |

## Winning cell

**lifetime `window-end` x cap `uncapped`** — combined net $+22,795, worse-era adjusted R +0.216, n=187.

## 14-month leave-one-out at the winning lifetime

Baseline cap at lifetime `window-end`: **uncapped**.

**The cap level STOPS FLIPPING once lifetime is set to `window-end`.** Every single-month removal keeps `uncapped` as the winner. This is a real change to the freeze: the earlier level instability (4 of 14 months) was an artifact of leaving order lifetime unset, not a property of the cap.
