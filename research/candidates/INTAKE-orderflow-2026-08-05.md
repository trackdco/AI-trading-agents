---
date: 2026-08-05
status: INTAKE — four order-flow candidates, awaiting Angus's pick
tags: [intake, orderflow, absorption, cvd, ofi, london, ny]
sources: ["research/findings/GEX-and-microstructure-intake.md", "research/transcripts/fabervaale/EXTRACTION-A-models.md"]
---

# Order-flow intake — four candidates, two per session

ANGUS 2026-08-05: *"id be keen to see if you could build some order flow based strategies.
obviously with available depth data, CVD, footprint data, absorption… come to me with some
strategies per session."*

**Constraint applied to every candidate below: it must be buildable from data already on
disk.** No purchases, no ES, no options. Depth = `data/reference/depth_london` +
`depth_2025/2026` (MBP-10, ten levels, one snapshot per minute). Tape =
`output/fp_minutes.parquet` (per-minute `b`, `a`, `vol`, `delta`, `vwp`).

**Second constraint, from the portfolio audit:** the candidate book is 112 "sweep" / 89
"fade" mentions against 18 "breakout". **Almost everything we own is mean reversion at a
level, so it all fails in the same regime.** Two of the four below are deliberately NOT
fades. That is the point of them.

---

## LDN-OFI-01 — Order-flow imbalance continuation, London open *(NOT a fade)*

**Mechanism.** Cont, Kukanov & Stoikov: over short horizons, price change is driven by
**order-flow imbalance** — the cumulative *signed change* in queue size at the best bid and
ask — linearly, with slope inversely proportional to depth. We have never built this. What
the canon calls `dep_imb` is a **level**; OFI is a **change**, and the change is the
predictive object.

**Trigger.** In the first 30 minutes of London, compute OFI per minute from consecutive
MBP-10 snapshots. Fire when cumulative OFI over a rolling window exceeds its own trailing
quantile **and price has not yet moved proportionally** (impact lag).

**Direction.** With the OFI sign — this is momentum, not reversion.

**Entry.** Limit at the micro-price — `(bid_sz·ask + ask_sz·bid)/(bid_sz+ask_sz)` — which
Stoikov shows beats mid and weighted-mid as a short-horizon estimator.

**Stop / target.** Stop beyond the opposing best-level queue; target a declared R grid,
because we have learned twice this week that testing one geometry answers nothing.

**Known limitation, on the record before testing:** OFI is designed for event-level data
and we hold one snapshot per minute, so this is a **minute-resolution approximation**. If it
fails, that failure does not close OFI as a concept — only this resolution of it.

---

## LDN-ABS-01 — Absorption reversal at the Asian range extreme *(a fade)*

**Mechanism.** Price extends beyond the Asian session's range, aggressive volume arrives
in size, and **price fails to travel** — size is being absorbed by resting liquidity. The
absorbed side is trapped; the reversal is the unwind.

**Trigger.** Price trades beyond the 18:00–02:00 ET range extreme; in that minute
`vol` is in its top trailing quintile **and** `|delta|/vol` is low (effort without result)
**and** the MBP-10 book shows size *ahead* of price rather than behind it.

**Why it is not the London-canon fade.** The canon fades a *confluence level*. This fades
*flow behaviour at a session boundary*, with no BB / VWAP / POC dependency at all — a
genuinely different input family, which is what the correlation battery cares about.

**Note.** `eff_result` (volume per point of movement) was built today and came in
era-consistent at −7.3pp on the London fade — below the noise floor there, but it is the
core variable of this candidate rather than one of seventy.

---

## NYA-ABS-01 — Absorption at the IB extreme *(a fade — and an OWED arm, not a new idea)*

**This is not intake. It is a debt.** `research/candidates/nya-ivb.md` trial 3 records that
branch B was censused as a **strawman**: the taught setup is *"fade the touch ON ABSORPTION
AT THE EXTREME"* (Fabervaale, extraction A) and **the mandatory flow trigger was omitted
from the tested expression.** Trial 4 then found the ungated fade positive and noted
*"absorption fires 4% (n=4 — definition too strict, looser variant = new declared arm)"*.

**That looser variant was declared and never run.** The IB fade is our healthiest candidate
(PSR 0.994, PF 1.41) and it ships **without the gate its own source says is mandatory**.

**Trigger.** At an IB-extreme touch: top-quintile volume, low `|delta|/vol`, and
delta *opposing* the touch direction — the three-part absorption definition, each part
swept over a declared threshold grid instead of one hard-coded cut that fires four times.

---

## NYA-THRUST-01 — Delta thrust continuation *(NOT a fade)*

**Mechanism.** The opposite of absorption: a minute where **delta and volume are both
extreme and price travels**, i.e. effort *with* result. Aggressors are paying up and getting
paid. The literature's short-horizon impact result says this persists.

**Trigger.** In 09:30–11:00 ET, a minute with `|delta|` and `vol` both in their top decile
**and** `|delta|/vol` high **and** the move confirmed by the book thinning ahead
(`bk_slope`, built today).

**Direction.** With the thrust.

**Why it matters to the portfolio.** This is the diversifier. It pays when price **does not
come back** — precisely the state in which every fade we own is losing. If it works at all,
its correlation to the existing book should be near zero or negative by construction, and
that is testable at the day-series level with the existing correlation battery.

---

## What I would run, and why

**`NYA-ABS-01` first.** It is not speculative — it is a declared, never-run arm on a
live-eligible candidate whose own source calls the trigger mandatory. It is the cheapest
real work on the board and it touches a book we may already be shipping under-specified.

**`NYA-THRUST-01` second**, because the portfolio needs a non-fade more than it needs
another edge, and because the same data answers it.

**Both London candidates are worth having and neither is urgent** — the London book has no
live exposure and `LDN-CAN-01` still owes its L4.

**Every one of these needs the full ladder** — prereg, census with a declared kill line,
fills, outcomes, feature trial, family-wise null. Roughly a day each. The constraint is not
ideas. It is that n is small and the noise floor is real, and no amount of searching
changes that.
