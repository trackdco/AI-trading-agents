---
date: 2026-08-04
status: thesis-pending
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
