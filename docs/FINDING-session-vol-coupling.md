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

## 4. Part 2 (same day): what DOES sort "better or worse" for the strategy

His follow-up: *"how does this help for when I know trading with my
strategy may be better or worse."* Tested at corpus scale:

- **TRIGGER DENSITY is the real signal — within the window, as it
  happens.** Days by candidate count: sparsest quartile 30.0% 2R-rate,
  densest 22.3% (corr −0.425, monotone, 914 days). Within London alone,
  concurrent: −0.330. Confirms the old n=10 prereg §1 finding at ~90× the
  sample: when the tape is begging you to trade, the offers are worse.
- **But it barely forecasts ACROSS windows** (morning density → NY
  quality: −0.085; only the most spam-heavy morning quartile shows NY
  degradation, 22.9% vs ~26%). And per-candidate quality does not persist
  across windows at all (London day-rate vs NY day-rate corr +0.05; Asia
  vs rest +0.05). **Each window re-rolls.**
- Combined with Part 1's nulls (vol regime, direction, calendar, year all
  R-flat): day quality is not forecastable — it REVEALS itself, window by
  window, through the window's own trigger pace and states.

**Proposed (awaiting his word):** a `trigger_pace` briefing field —
candidates so far this window vs the trailing-120-day typical count by the
same clock time, as a percentile. Mechanical, as-of. High pace = the
churn-day signature his T82/06-02 experience already knows.

## 5. Part 3 (2026-08-31): the variable test — trade NY BY the overnight?

His follow-up: *"How does asia and London effect New York and does trading
according to that knowledge affect WR do variable test."* Eight
overnight/London-derived conditions applied as candidate FILTERS on the
23,499 NY candidates of the v2 full-day corpus, scored by mechanical
2R-rate, split-half validated by session-day count: IS = 2023-01-02 →
2024-10-05, OOS = 2024-10-06 → 2026-07-14 (~455 days each). A rule earns
nothing unless its spread holds in BOTH halves. Script:
`scripts/ny_conditioning_test.py` (rerun 2026-08-31 reproduces every
number below exactly).

Baseline NY 2R-rate: **23.4% IS (n=11,612) / 24.0% OOS (n=11,887)**.

### The nulls (most of the overnight is not tradeable knowledge)

| rule tested | IS | OOS | verdict |
|---|---|---|---|
| overnight range quartile (Q1..Q4) | 22.1/22.4/24.1/24.3 | 22.9/25.3/22.5/24.8 | non-monotone OOS — null |
| overnight trend_on (eff ≥ 0.45) vs chop_on | 22.5 vs 24.4 | 24.7 vs 23.3 | sign FLIPS — noise |
| candidate against vs with London drift | 24.0 vs 22.9 | 24.5 vs 23.4 | ~1pt, both halves, too thin to act on |
| against vs with late-London (08:30–09:29) drift | 23.6 vs 23.2 | 24.3 vs 23.6 | null |
| 09:30 above/inside/below prior-day range (position alone) | 23.5/23.6/22.4 | 22.8/24.1/25.0 | reorders — null |

Consistent with Parts 1–2: the overnight predicts NY's SIZE in points, not
its quality in R, and direction does not carry. Six of eight rules die.

### The survivor: mean-reversion toward value

The two conditions that INTERACT candidate side with where 09:30 sits
relative to yesterday's structure both hold in both halves, and both point
the same way:

| condition (open outside PD structure) | IS 2R% (n) | OOS 2R% (n) |
|---|---|---|
| **toward_value** (open above VA → short, below → long) | **24.8** (3,339) | **26.6** (3,691) |
| away_from_value | 22.8 (3,276) | 22.8 (3,564) |
| **back_into_range** (open beyond PD high/low, trading back in) | **24.1** (1,865) | **26.6** (2,077) |
| breakout_continuation (open beyond PD extreme, trading on through) | 22.1 (1,859) | **20.7** (2,023) |

Plain language: when NY opens OUTSIDE the prior day's value area or range,
candidates fading BACK toward value beat candidates chasing continuation —
and the gap WIDENS out-of-sample (back-into-range 26.6% vs continuation
20.7%, a ~6pt spread on ~2k candidates a side). This is the one
overnight-derived condition where "trading according to that knowledge"
moves WR: prefer the fade toward value on an outside open; treat
open-beyond-PD-extreme continuation candidates as the worst bucket in the
whole test. It coheres with doctrine that already exists (T59 fade-only at
knife levels, the value-area framework in his narrations) rather than
inventing a new idea.

### Caveats, stated before anyone acts

- Crude mechanical outcome model (2R-or-stop @120m) — a ranker, not P&L.
- Eight variables were tested; one family survived. That is exactly the
  multiple-comparisons shape Pat's seven gates exist for — this is a
  **prereg candidate**, not doctrine. No contract changes without his word
  and a proper grading pass.
- Magnitude is modest (~+2.6pt over the OOS baseline for the good bucket;
  the bigger edge is AVOIDING the 20.7% continuation bucket).
- `va_side`/`pd_side` overlap (an open beyond the PD extreme is usually
  also outside value) — one effect wearing two hats, not two effects.
