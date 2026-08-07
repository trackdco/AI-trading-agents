---
date: 2026-08-04
status: greenlit
tags: [london, overnight-structure, amt]
sources: ["articles/sweep-2026-08-04-amt.md#AMT1", "articles/sweep-2026-08-04-orderflow.md#OF8", "articles/sweep-2026-08-04-session-vwap.md#SS3"]
---

# london-inventory-fade — the overnight inventory correction at the first real liquidity

## Thesis (for Angus)

When the whole overnight session has traded one way — inventory ~100% net long or
short against yesterday's settlement — everyone who accumulated all night wants
the same thing at the first deep pool of counterparties: to lighten up. The
canonical version corrects at the 09:30 open, but the FIRST deep-liquidity event
after an Asian drift is the European open at 03:00 ET. The wrong side is the late
Asian-session chaser holding into the open at a stretched price; the trade fades
the overnight extension toward settlement exactly when holders finally have the
liquidity to exit. This one has institutional paper behind it: NY Fed research
documented the historical overnight equity premium concentrating in the
02:00–03:00 ET European-open hour, driven by dealers unwinding prior-close
imbalance. The honest caveat is in the same source: the naive always-long version
decayed to ~zero after 2021 once published. What's left is the conditional trade
— skew-triggered, either direction, location-gated (only when price is stretched
beyond ~1σ AND opened inside yesterday's range; an outside-range open with
acceptance is a different animal and feeds the drive candidate instead).

## Mechanical skeleton

At 02:55 ET: overnight inventory = fraction of 1-min closes since 18:00 above vs
below prior settlement; arm at ≥ ~90% one-sided. Classify location (σ vs
overnight VWAP; inside/outside prior RTH range). Fade branch: after 03:00, one
more extension that stalls (no new extreme for ~15 min) → enter toward
settlement. Stop beyond the post-03:00 extreme + buffer. Targets: Asia mid/POC,
then settlement. Time-stop 06:00 ET. Flow upgrade: CVD divergence or absorption
at the London-side extreme.

## Flags

- Data: candles-only (flow optional).
- Crowding: the published form is arbed away — the whole bet is that the
  CONDITIONAL form retains edge in a window nobody measures. Honest risk: maybe
  it doesn't.
- NY-canon input-family overlap: MEDIUM (overnight structure).
- Pairs with the open-type gate (fade only on non-drive opens).

## Trial ledger — LDN-INV-01

### Trial 1 — L0 census (2026-08-04, per PREREG spec exactly)

396 census days (2025: 257, 2026: 139). Mean NQ points by prior-US-RTH quintile
(q0 = worst days), era-local quintiles, no costs (L0):

- **2025**: q0 02:00→06:00 **+20.7 pts** (t≈1.7), concentrated 03:00→04:00
  (+17.6, t≈2.0); q4 **−3.8** (03:00→04:00 −13.0). Textbook inventory signature:
  Europe buys back bad US closes, fades good ones. The classic 02:00→03:00 hour
  is DEAD (−0.3) — consistent with the published post-2021 decay; the residual
  sits after the 03:00 open.
- **2026 (validate)**: q0 +17.9 (t≈0.65, n=28) — direction agrees, power weak —
  but **q4 +42.0**: the asymmetry is ABSENT; everything drifted up in the euro
  window in H1-2026 regardless of the prior day. Kill criterion 2 is live.

Status: NOT killed, NOT validated. The naive form fails the asymmetry test in
2026. Refinement (the actual thesis: condition on inv_skew_0255 AND σ-location
jointly, not prior-return alone) proceeds under the same family; inverse pass
and permutation null pending. If the joint conditioning cannot restore the
asymmetry in both eras, criterion 2 kills the candidate.
