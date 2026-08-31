# FINDING — Asia/London character vs New York: volatility clusters, it does not rotate

His question (2026-08-31): *"if asia and london are choppy does New York
[get] more volatile and vice versa?"* Measured over 874 usable session-days
(2023-11 → 2026-07), ranges normalized as percentiles against each
session's own trailing 120 days so the 2023→2026 price doubling cannot fake
the result. Script: `scripts/session_coupling.py`.

## 1. The headline: NO — the coupling runs the other way, and it is strong

NY range percentile conditioned on the combined overnight (Asia+London)
range quartile:

| overnight | NY median range pct | P(NY in its top quartile) |
|---|---:|---:|
| Q1 (most compressed) | 0.28 | **9%** |
| Q2 | 0.45 | 22% |
| Q3 | 0.57 | 29% |
| Q4 (widest) | **0.74** | **50%** |

Monotone across the whole 4×4 Asia×London grid (compressed×compressed
0.17 → widest×widest 0.82). A choppy/tight overnight predicts a QUIET New
York; expansion follows expansion. This is textbook volatility clustering
showing up cleanly at session granularity — one of the strongest
conditional effects measured anywhere in this project.

## 2. The nulls, stated as loudly

- **Trendiness barely moves** (median |net|/range 0.46 → 0.51 across
  overnight quartiles): loud days are bigger, not meaningfully more
  directional. A wide NY after a wide overnight is both trend AND swing.
- **London→NY direction continuation is a coin flip** (51% overall;
  52/62/49/44% by London-range quartile — no monotone structure; the lone
  62% cell is one of four comparisons and earns nothing without a
  prereg). Consistent with every prior trend-filter test in this repo:
  direction does not carry; only magnitude does.
- **THE SYSTEM-RELEVANT NULL: NY candidate quality in R is FLAT across
  overnight regimes** (reach-2R 23.3–24.7% from Q1 to Q4, n≈22k NY
  candidates). Because the mechanical stop scales with volatility, the
  overnight state predicts POINT ranges, not R-outcomes. In R-space the
  day types are equivalent.

## 3. What it is good for

Not a gate (the R-null says never veto NY off the overnight), and not a
direction signal (the coin flip says so). It is an EXPECTATION field:

- After a compressed overnight, far targets in POINTS are unlikely to be
  reachable — TP2 selection and "is 100pt available today" should know
  the day's realistic envelope.
- Stop sizes in points will run systematically larger after loud
  overnights (same R, more points) — position sizing in contracts, and
  his "some stops are too big" instinct, live here.

**Proposed (awaiting his word, not shipped):** add
`overnight_range_pct` — the trailing-120-day percentile of the 18:00→09:30
range — as a briefing context field for the NY thesis. Mechanical, as-of,
one number. For v2/V3 it is a ready-made context feature either way.
