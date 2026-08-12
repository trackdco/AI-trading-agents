# Order flow on the London book — measured results

Declarations pinned before measurement: `output/DECLARATIONS-london-orderflow.md`.
Fit-era measurement, **not a holdout look** — the bar-only venue is closed, so
nothing here can confirm in the holdout sense.

## Substrate

Built the per-minute flow table from the committed footprint files using their
`aggregate()` verbatim, convention `delta = b − a` (**positive = SELL
aggression** — the inverse of the usual reading, and the exact sign trap their
own convention gate caught).

**400,488 minutes, 2025-06-01 → 2026-07-19 — 35,039 inside the London window
across 292 session days.** That is full coverage of the fit era, not the thin
~6-month venue the earlier flow work was priced against, so the resolution
problem that forced their "interesting but unconfirmable" clause does not bind
this measurement. `flowconf` and `closeloc` populate on 100% of rows.

London book with flow attached: **686 trades, 245 days, EV +0.292R.**

---

## R1 — S1 flow-confirmation cut (declared replication)

Declared direction: dropping fights whose decision-bar delta disagrees with
trade direction raises EV.

| | Lift | Kept n | Kept EV |
|---|---|---|---|
| Full book | **+0.136R** | 407 (1.66/day) | +0.372R |
| half 1 | **+0.040R** | 203 | +0.381R |
| half 2 | **+0.232R** | 204 | +0.364R |

**Replicates in direction, not in magnitude.** Positive on both halves, but
half 1 is nearly nothing. Their published London-specific figure was
**+0.062R** — my half 1 (+0.040R) sits much closer to that than my pooled
+0.136R does. Read honestly, this supports their original conclusion: S1 is a
real but *small* effect in London, and a much larger one in NY_PRE (+0.157R).
Cost: frequency falls 2.80 → 1.66/day, a 41% cut, which under the payout
objective is a material loss of qualifying days.

## N1 — flow × sweep_b (new, exploratory) — **NULL**

sweep_b is 55% of the book and the component that passed the sealed holdout
alone. No flow construct had ever been scored against it.

| | Lift | Kept n | Kept EV |
|---|---|---|---|
| Full | +0.145R | 205 (0.84/day) | +0.280R |
| half 1 | **−0.031R** | 103 | +0.189R |
| half 2 | +0.325R | 102 | +0.371R |

**Fails the split-half.** The entire effect lives in one half; the other is
negative. Under the programme's own protocol — derive on half 1, attempt to
kill on half 2 — this is what a killed candidate looks like.

**Recorded as a new null for the base-rate library: decision-bar flow
confirmation does not improve sweep_b.** That is a genuinely useful negative,
because sweep_b is the book's strongest component and the obvious next place
someone would try to bolt flow on. It also fits the programme's standing
pattern — sweep_b's edge is in the *re-entry context* (a prior stopped
attempt), not in agreement from another data family.

## Section A — constructs already recorded dead

Reported for completeness, **not promoted**, per the declaration.

| Construct | Lift (full book) | Consistent with recorded verdict? |
|---|---|---|
| `thru_delta_conf` | −0.016R | Yes — dead |
| `d30_conf` | +0.044R | Yes — negligible |
| `delta_z` | +0.062R | Yes — weak/unstable |
| `cvd_slope30` | +0.089R | Yes — weak |

**Heatmap / depth deliberately not re-tested.** The depth data exists on their
branch (`data/reference/depth_london/`, `depth_apr2026/`), but all six MBP-10
depth features are recorded dead (BR-21) and **WALL_AHEAD measured
significantly negative** (M3 −0.356; WALLSZ −0.406) — directly contradicting
the old canon's `D` gate, which *required* a wall. Re-running them as fresh
hypotheses would be re-litigating a settled null against the base-rate
library's whole purpose.

---

## The undeclared result — `d15_conf`, a HYPOTHESIS only

| | Lift | Kept n | Kept EV |
|---|---|---|---|
| Full | **+0.391R** | 303 (1.24/day) | +0.465R |
| half 1 | **+0.467R** | 153 | +0.566R |
| half 2 | **+0.309R** | 150 | +0.361R |
| G1 max single-day | 9.0% of kept profit | | |

This is the strongest result in the run and it **survives the split-half on
both halves**, with no single-day concentration problem. It is also the one
result I did **not declare in advance** — it fell out of a section-A table.

Per the pipeline's own rule, exploratory output is a **hypothesis, not a
finding**, no matter how good it looks. Three specific reasons to hold it at
arm's length:

1. **Multiplicity.** I looked at roughly five section-A constructs plus the
   declared ones. Finding one that clears at +0.391R among many is precisely
   the garden-of-forking-paths shape their own null-calibration work warns
   about — 8,721 real tests were once beaten outright by 9 of 10 equal-sized
   *null* searches.
2. **Their cut study already killed `d15_conf`** on the break arm. This is a
   different population (the full London book), so it isn't a contradiction,
   but it is a reason for suspicion rather than excitement.
3. **Frequency cost is severe**: 2.80 → 1.24/day, a 56% cut. Under the payout
   objective, frequency manufactures qualifying days, and a cut this deep can
   reduce them even while raising EV. It would need scoring on both axes
   before it meant anything.

**Disposition:** queued as a pre-declared cut, with its own declared bar, on
data it has not touched. Since the bar-only holdout is permanently closed,
that venue is **forward-recorded data only**.

---

## What this run establishes

- The flow substrate for London is **complete over the fit era**, which is
  better than the programme assumed when it wrote its unconfirmability clause.
  Flow work on London is no longer resolution-limited.
- **S1 replicates directionally and is genuinely small in London** — their
  original read was right, and my larger pooled number is the unstable one.
- **A new null: flow does not improve sweep_b.** The book's best component
  gets nothing from delta confirmation.
- One strong but undeclared candidate (`d15_conf`) exists and is queued
  forward, not adopted.
- Nothing here licenses a change to the book. The only action item is the
  live recorder, which is the sole remaining venue where any of this can be
  confirmed.
