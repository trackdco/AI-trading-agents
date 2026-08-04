---
date: 2026-08-04
status: thesis-pending
tags: [london, volume-profile, amt]
sources: ["articles/sweep-2026-08-04-amt.md#AMT5", "articles/sweep-2026-08-04-amt.md#AMT6", "articles/sweep-2026-08-04-amt.md#AMT8"]
---

# london-value-traverse — destination trades against the profile map

## Thesis (for Angus)

Absent fresh news, London's job is repricing overnight inventory against the
references that already exist — and the profile map says where rotations GO. Three
composable pieces. Destination: a naked POC (a prior day's fairest price that was
abandoned untested) holds resting two-sided interest and demonstrably attracts
price; when one sits within reach beyond the Asian extreme, it's the rotation's
magnet — ride the traverse into it, scale out into the touch. Verdict: Dalton's
80% rule re-anchored — Asia held outside yesterday's value all night, London
drives back INSIDE and holds = the overnight extension is judged mispriced, and
the stranded overnight crowd's stop-outs fuel a rotation through the whole value
area (published ES testing says the true traverse rate is nearer 60% than 80% —
a bias, not a certainty, and the full traverse often finishes in NY, so a runner
is part of the design). Path: low-volume nodes are air pockets — price entering
one traverses fast to the next high-volume node because there's no established
business to slow it; the wrong side is whoever fades inside the air pocket.

## Mechanical skeleton

Volume-at-price built from 1-min bars (bar volume distributed across range —
approximation, stated). Maintain naked-POC list + prior-RTH value area + rolling
10–20-day composite HVN/LVN map. Traverse entry: 1-min close beyond the Asian
extreme on the magnet side (or VA re-entry held ~45–60 min for the 80% variant)
→ with the rotation. Stop: Asia mid / back outside the VA edge. Targets: the
naked POC / VA POC → opposite VA extreme; LVN entries target the next HVN.
Optional responsive fade of the first POC touch, tight stop beyond.

## Flags

- Data: candles-only (volume-at-price is an approximation from 1-min OHLCV — the
  fidelity question goes on the trial ledger, and footprint data can calibrate
  the approximation on the flow span).
- Crowding: the vocabulary (naked POC, 80% rule) is everywhere; the
  London-window mechanization against prior US value is non-standard. Known
  risk: node/VA definitional fragility — parameter honesty matters.
- NY-canon input-family overlap: MEDIUM (overnight structure; NY reads daily POC
  in its reference set).
- Traverse-speed expectations must scale to London's 20–30%-of-US volume.
