# LDN-OBK-01 / LDN-PO3-01 — L0 census

Authorised by `docs/PREREG-london-open-break-tree.md`. Bars only. 2023/24 untouched — no holdout look spent.
Universe: 396 London sessions (2025: 257, 2026: 139).

## 1. Does the pre-open range get broken? (LDN-OBK-01 census kill line)

| era | sessions | days with >=1 break | break freq | up-breaks | down-breaks |
|---|---:|---:|---:|---:|---:|
| 2025 | 257 | 237 | 92% | 155 | 121 |
| 2026 | 139 | 129 | 93% | 82 | 67 |

## 2. Do breaks fail? (LDN-PO3-01 census kill line, and the placebo control)

| era | range | breaks | fail 30m | fail 60m | fail 120m |
|---|---|---:|---:|---:|---:|
| 2025 | pre-open | 276 | 79% | 83% | 85% |
| 2025 | placebo | 305 | 60% | 67% | 73% |
| 2026 | pre-open | 149 | 77% | 81% | 84% |
| 2026 | placebo | 151 | 57% | 63% | 70% |

## 3. Side symmetry

| era | side | breaks | fail 30m | fail 120m | median excursion |
|---|---|---:|---:|---:|---:|
| 2025 | up | 155 | 78% | 85% | 7.5 pts |
| 2025 | down | 121 | 80% | 84% | 14.0 pts |
| 2026 | up | 82 | 74% | 82% | 15.8 pts |
| 2026 | down | 67 | 81% | 87% | 14.5 pts |

## 4. Excursion beyond the level (the family's 'is there an event' test)

| era | outcome | n | median | p25 | p75 | median range |
|---|---|---:|---:|---:|---:|---:|
| 2025 | failed <=120m | 234 | 8.6 | 4.5 | 17.4 | 49.6 |
| 2025 | continued | 42 | 63.9 | 41.6 | 96.2 | 62.0 |
| 2026 | failed <=120m | 125 | 11.5 | 6.8 | 20.5 | 86.0 |
| 2026 | continued | 24 | 96.5 | 72.4 | 117.0 | 82.8 |

## 5. Transfer test of NYA-FA-01's discriminators

NY found excursion depth discriminates traverse (23% vs 8% far-edge) and
time-outside discriminates nothing (16/19/12%). Same construction here.

**Excursion depth before re-entry** (failed breaks only, n=359)

| tercile | n | reaches far edge | reaches midpoint | median mins of window left |
|---|---:|---:|---:|---:|
| low | 120 | 25% | 52% | 104 |
| mid | 119 | 18% | 45% | 102 |
| high | 120 | 16% | 42% | 84 |


**Minutes spent outside the range** (failed breaks only, n=359)

| tercile | n | reaches far edge | reaches midpoint | median mins of window left |
|---|---:|---:|---:|---:|
| mid | 243 | 21% | 48% | 106 |
| high | 116 | 16% | 43% | 81 |


**POST-HOC, added after seeing the above — declared as a second look.**
Excursion is in points, and the trip to the far edge is `range + excursion`,
so a deeper excursion mechanically means a longer journey. NY's composites
are far wider than a 2-hour London range, so the same points-tercile is not
the same test. Normalising by range width is the like-for-like version.
Both are ledgered; the search is charged for both.

**Excursion as a FRACTION of range width** (failed breaks only, n=359)

| tercile | n | reaches far edge | reaches midpoint | median mins of window left |
|---|---:|---:|---:|---:|
| low | 120 | 18% | 50% | 102 |
| mid | 119 | 23% | 46% | 108 |
| high | 120 | 18% | 43% | 83 |


### Break quality — how many 'breaks' are bare touches

The prereg froze a break as a bare 1m close beyond the level, with no
minimum displacement. That is as-taught (neither source states a minimum in
the transcripts) but it admits noise touches. Counted here because it sets
up the obvious L1 declared variable, not because it changes the census.

| era | breaks | excursion < 5pt | < 10pt | < 0.10x range |
|---|---:|---:|---:|---:|
| 2025 | 276 | 27% | 48% | 25% |
| 2026 | 149 | 9% | 37% | 25% |

## 6. Headline trial — pre-open fail rate MINUS placebo fail rate

The raw fail rate cannot support either branch on its own; any boundary
gets poked and reverts. The trial is the margin over a range with no
claim on the open. Two-proportion z, unpaired, fail-within-120m.

| era | pre-open | placebo | margin | z |
|---|---:|---:|---:|---:|
| 2025 | 85% (276) | 73% (305) | +12 pp | +3.43 |
| 2026 | 84% (149) | 70% (151) | +14 pp | +2.94 |

