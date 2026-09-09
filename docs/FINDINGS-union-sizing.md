# FINDINGS — funded-account odds on the union of eras (2026-09-04, Angus's ask)

Same mechanics as `FINDINGS-funded-sim-armed.md` (30% haircut, eval $3k → funded
$4k, $2,000 EOD-trailing floor locking at start, 5-day blocks, 120-day cap),
armed empire, 6,000 sims per cell. 2020–22 runs without the news gate.

| micros | 2023–26 payout | 2020–22 payout | **union 2020–26** |
|---:|---:|---:|---:|
| 4 | 99.9% | 96.0% | 98.4% |
| 8 | 94.4% | 85.5% | **88.6%** |
| 12 | 84.2% | 75.5% | 77.6% |
| 16 | 80.8% | 66.2% | 74.4% |
| 20 | 75.9% | 63.2% | 70.5% |

**At ≥80% start→payout odds the union supports about 10 micros, not 16.** The
16-micro figure is a 2023–26 fact — the calmer era. 2020–22's −30.1R drawdown
and its chained losses pull the line down. Literal union path at 1 micro:
worst peak-to-trough $515, so 3 micros fit $2,000 on the actual sequence —
the same answer Angus's dossier gives ($596 on his tape).

Ruling for sizing: **size to the union.** 8 micros is comfortably inside
(88.6%); 12 is the edge (77.6%); 16 is a calm-era number.

Script: `scripts/union_funded.py`.
