---
date: 2026-08-06
status: RESULT — T1 partially supported (HVN half only), T5 answered (prev_session)
tags: [amt, volume-profile, hvn, lvn, poc, census, t1, t5]
script: scripts/vp_lvn_census.py
report: output/vp_lvn_census.md
data: output/vp_lvn_visits.parquet
---

# Volume-profile nodes: the magnet is real, the vacuum is not

Census only (§5.9.1) — a mechanism test on 32,014 node-session-widths over 354 RTH
sessions, 2025-01 → 2026-07. **No expectancy claim.**

## The short version

Price holds at prices where volume traded **yesterday**. It does not move faster through
prices where volume did not. Those are two halves of the same textbook claim and only one
of them survives measurement.

And the profile window is not a matter of taste: **only yesterday's profile works.** The
previous week, the rolling 5 and the rolling 20 are flat or era-inconsistent — averaging
sessions together smears the nodes until they stop being levels.

## What was actually tested

| | |
|---|---|
| **T1** | price moves fast through low-volume nodes (LVN) and stalls at high-volume nodes (HVN) |
| **T5** | which profile period to build levels on — prev session / prev week / rolling 5 / rolling 20 |
| measure | **dwell** = minutes whose bar range touched a band around the price |
| control | every node scored against **its own flanks at ±3× the band width** |
| bands | ±2.5, ±5, ±10, ±20pt — swept, not chosen |
| positive control | POC/VAH/VAL through identical machinery |

## Three design decisions that changed the answer

**1. The flank control.** The obvious test — LVN dwell vs HVN dwell — is confounded and
would have returned a false PASS. HVNs sit mid-range where volume piled up; LVNs sit in the
tails. Price levels are autocorrelated day to day, so today's session naturally spends more
time near the middle of yesterday's range for reasons that have nothing to do with
liquidity. The naive ratio reads **0.899–0.973** on `prev_session` — thesis apparently
confirmed. Controlled against flanks ten points away, it collapses. That gap *is* the
confound, measured.

**2. Bar range, not closes.** The first pass scored `|close − level| ≤ tol`. A minute that
rips straight through a level and closes four points past it scores **zero** — which biases
hardest against exactly the fast-traversal case T1 is about.

**3. Sweeping the band width, and a positive control.** At ±2.5pt every level type,
including the POC, came back at 1.000. A ±2.5pt band is **narrower than a typical NQ
1-minute bar**, so that number is a statement about resolution, not the market. Without
POC/VAH/VAL as a positive control this would have been filed as a clean null. It was not
one.

## Result

**The separation `HVN − LVN` is the actual prediction** — T1 says the two kinds differ from
each other *in opposite directions* — and it is immune to any bias hitting both kinds
equally, including resolution dilution.

| band | `prev_session` HVN−LVN | 2025 | 2026 |
|---:|---:|---:|---:|
| ±5 | **+0.027** | +0.027 | +0.028 |
| ±10 | **+0.057** | +0.079 | +0.021 |
| ±20 | **+0.107** | +0.147 | +0.054 |

Era-consistent at every width, and **monotonically increasing with band width**. A spurious
separation has no reason to scale with the width of the measuring band; a real one being
smeared by 1-minute resolution does exactly this. `prev_week`, `roll_5` and `roll_20` do
not separate era-consistently at any width.

**Which half carries it.** At ±20pt on `prev_session`:

- **HVN = 1.069** (eras 1.078 / 1.058) — holds price ~7% longer than its own flanks
- **LVN = 0.962** (eras 0.932 / **1.004**) — 2026 fails the direction outright

So *acceptance* survives and *rejection* does not. **The tradeable object is the HVN as a
level, not the LVN as a fast lane.**

## Why this matters beyond the thesis

This is the **second** time we have failed to find the vacuum. `LQV-01` died asking the
same question — where is there no liquidity — from once-a-minute MBP-10 snapshots, with
aggregate side size never falling below 0.56× its own median. Two instruments, two
methods, same answer: **we can find where liquidity is, and we cannot find where it
isn't.** That should now be treated as a property of what we can measure, not a gap to
keep re-attacking with 1-minute data.

## Caveats, stated plainly

- The positive control rises monotonically with band width (1.000 → 1.024 → 1.066 →
  1.080) but **never clears p<0.05**. Widening the band cures dilution and costs sample at
  the same rate (n falls 1,132 → 201). On 1-minute bars this trade-off has no sweet spot.
- The separation result stands *because* it is dilution-immune, but effect sizes are a few
  percent of dwell.
- **This is a level-quality finding, not a strategy.** It says which levels deserve to be
  in the level menu and which profile window to build them from. It does not say a trade
  at an HVN makes money.

## What it changes

1. `_gather_levels` exposes **only the current session's POC**. Yesterday's HVNs are the
   levels with measured holding power and they are not in the menu at all.
2. Build profile levels from **the previous session**. Longer windows are context, not
   levels — which is a direct answer to *"what time period is best"*.
3. **Do not build an LVN-traversal family.** Twice-failed, and the half of AMT that fails
   is the half that would have justified it.
