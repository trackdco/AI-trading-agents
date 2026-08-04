---
date: 2026-08-04
status: thesis-pending
tags: [london, session-structure]
sources: ["articles/sweep-2026-08-04-orderflow.md#OF2", "articles/sweep-2026-08-04-session-vwap.md#SS2"]
---

# london-asia-sweep-continuation — go with the early sweep, conditioned on timing and narrow Asia

## Thesis (for Angus)

The anti-crowd complement of the sweep-reversal, and the more interesting half
because almost nobody trades it. An NQ-native 17-year 1-minute study (Herman,
4,262 days) found the timing of the sweep decides its meaning: when the Asian
extreme is breached in the 02:00–03:00 ET dead hour — BEFORE deep liquidity
arrives — London tends to confirm and extend that direction rather than reverse
it, especially after an abnormally narrow Asia. The read: a pre-open sweep is
more often informed early positioning that European real money then validates,
and the wrong side is the reflexive fader who treats every sweep as a fake.
Narrow Asia is the second condition — unresolved overnight positioning that the
European open must resolve, with the study showing narrow-Asia sessions make
London markedly more aggressive. Third condition (your σ principle): only take
breaks launching from near VWAP — a break fired from +2σ has already spent its
fuel.

## Mechanical skeleton

Filters: Asia range < X-percentile of trailing 20 days; direction = the side
already breached in 00:00–03:00 ET. Trigger: retest-and-hold of the broken
extreme after 03:00 (pullback to within Y ticks, 1-min close fails to re-enter),
or stop order beyond the extreme if price sits within ~1σ of overnight VWAP.
Stop: back inside the range / Asia mid. Exit: 1× Asia-range projection, flat by
06:00 ET. Re-entry into range with N closes back inside = reversal candidate
fires instead.

## Flags

- **Event-tree pair** with `london-asia-sweep-reversal` — one family, one ledger.
- Data: candles-only.
- Crowding: LOW — niche NQ session-stats work, not mass-market. The one caution:
  the supporting stats come from one community's study (claims-from-snippets, not
  verified reads) — our own census is the real test.
- NY-canon input-family overlap: MEDIUM-LOW.
