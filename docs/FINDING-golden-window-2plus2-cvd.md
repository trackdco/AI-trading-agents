# FINDING: golden-window un-starve (2+2) + CVD gate — best 2026 shape; day×window pockets (21 Jul 2026)

**TL;DR:** Give the 9:40–10:15 golden window its own 2-trade cap (pre-market keeps its own 2)
and apply the shipped selection gate (cut below-value opens + require CVD absorption, cvd≤0).
Feb–Jul 2026: **89t, +$15,381, 43% win, 5/6 green** — beats the shipped single-cap gate
(78t / +$14,351 / 41%) on every axis. The prior *raw* un-starve was a +$1.1k lean gain that
failed OOS; the CVD gate on top keeps the money at a much higher win rate. Dashboard artifact
summarizes this visually. 2026-in-sample by design (we trade 2026 forward, not 2023–25).

## The shape (per-window 2+2 caps, gated)

| filter | trades | P&L | win | green |
|---|---|---|---|---|
| raw (no gate) | 154 | +$15,119 | 34% | 5/6 |
| CVD absorption only (cvd≤0) | 93 | +$14,291 | 41% | 4/6 |
| **shipped gate (below-value + cvd≤0)** | **89** | **+$15,381** | **43%** | **5/6** |

Trust check: raw un-starve = +$1,110 over the single-cap — **exactly** matches the prior
"real engine +$1.1k" finding. The gate's value on top is **selectivity** (154→89t, 34→43% win,
money held), not more dollars — consistent with "CVD is a win-rate lever, not a P&L multiplier."

Monthly (gated): Feb +$6,268 (47%) · Mar +$98 (22%) · Apr +$5,910 (56%) · May +$645 (35%) ·
Jun +$3,110 (47%) · **Jul −$650 (0%, 4t — the lone red)**.

## Golden window alone (9:40–10:15)

Gate lifts it 41%→**54% win**, +$5,179→**+$6,809** — proof the golden edge is real *when flow
confirms it*. **But only 3/6 months green:** Feb (100%) + Apr (69%) carry it; May/Jun/Jul red
even gated. Same Feb-carried fragility, shifted forward.

## Day-of-week — a per-window inversion (Angus's "some days carry it")

At the aggregate every weekday is green ($119–$208/t), so nothing looks broken. Split by window
and two pockets bleed **and mask each other** because the same day runs opposite in each window:

| day | pre-market $/t | golden $/t |
|---|---|---|
| Mon | +$199 (44%) | +$151 (57%) |
| Tue | +$123 (36%) | +$109 (60%) |
| **Wed** | **−$144 (14%, −$1,005)** | **+$516 (62%, +$4,128)** |
| Thu | +$120 (31%) | +$522 (67%, n=3) |
| **Fri** | **+$302 (56%, +$2,720)** | **−$97 (20%, −$485)** |

**Wednesday pre-market** and **Friday golden** are the bleeders; **Wednesday golden** (best cell)
and **Friday pre-market** cover for them. A day×window filter (skip Wed pre-market / Fri golden)
is the obvious next test.

## Honest caveats

- **2026 in-sample** by explicit choice (we trade 2026 forward). The raw un-starve failed OOS in
  2023–25; CVD is 2026-only so its OOS durability is untested — the full-year heatmap + Bar's
  delta-divergence work are how we'd probe it.
- **Day×window cells are 3–9 trades each.** The inversion is a striking *hypothesis*, not a proven
  edge — same small-n trap as July (4t). Do not tune on it without more data.
- **July won't crack** (−$650, 4 absorption losers): CVD can't conjure edge that isn't in the tape.

## ⚠ CVD sign landmine (fix before any pipeline re-run or agent wiring)

The repo's `conviction()` / `load_cvd_delta()` produce the **negative** of the committed champion
journal's CVD. Applying the validated gate (cvd≤0 = absorption) to *freshly computed* CVD inverts
the edge (24% win instead of 41%). The diagnostics negate at point of use; verified it reproduces
78t/+$14,351/41% exactly. **The shared sign needs Angus's ruling before flipping in place** — and
must be fixed before CVD is wired into the chained agent's briefing (else it learns the wrong trades).

## Scripts / artifacts

- `scripts/window22_cvd.py` — per-window 2+2 + CVD gate, month + day-of-week; writes
  `output/window22_trades.csv` (persisted trade frame, slice freely).
- `scripts/july_cvd_probe.py` — global-cap sweep (shows more volume ≠ green July).
- `docs/golden-window-dashboard.html` — the rendered summary.
- Gate itself: `src/backtest/selection.py` + `config/strategy.yaml` filters (shipped default).
