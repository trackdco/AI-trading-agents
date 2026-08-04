---
date: 2026-08-04
status: thesis-pending
tags: [london, session-structure, amt]
sources: ["articles/sweep-2026-08-04-orderflow.md#OF4", "articles/sweep-2026-08-04-amt.md#AMT3", "articles/sweep-2026-08-04-session-vwap.md#SS6"]
---

# london-euro-open-drive — ride the European repricing when it opens with conviction

## Thesis (for Angus)

08:00 UK is a genuine structural event — LSE and Xetra cash open together, and
European institutional desks reprice the entire overnight news stack in the first
deep two-sided book of the day. When that repricing opens OUTSIDE Asian value and
drives — never trading back through the open, each leg extending — other-timeframe
money has voted that overnight prices were wrong, and the wrong side is whoever
positioned overnight against the European information plus the responsive trader
fading the move out of value. Their forced adjustment is the momentum you ride.
Three independent supports: FDAX opening-range-breakout literature documents the
daily volatility expansion; Dalton's IB logic (first-hour range outside prior
value + one-time-framing = extension odds); and academic intraday momentum (Gao
et al., 17 index futures) — the first half-hour predicts the rest of the session,
strongest on news days. The discipline is the opposite of the fade candidates:
this trade ONLY exists on drive opens, which is why the open-type classifier
gates the whole London book.

## Mechanical skeleton

London IB = 03:00–04:00 ET high/low (or first K minutes for the ORB variant;
anchor to the detected European open, not hardcoded ET — DST spec layer). Gates:
open prints outside Asia range/value; one-time-framing on 5-min bars; skip if
opening range already > threshold (news spent). Entry: break of IB extreme away
from Asian value, or first shallow pullback that holds without touching the open.
Stop: IB midpoint / back inside prior range. Exit: 0.5–1× IB extensions, nearest
overnight reference, or trail; flat by 06:00–06:30 ET lull. One trade per side
per day.

## Flags

- Data: candles-only (CVD-confirming-extreme optional).
- Crowding: ORB is the most crowded template in existence at 09:30; the
  European-open NQ version is far less traded. FDAX published results are mixed —
  parameterization honesty matters, the trial ledger will be busy.
- NY-canon input-family overlap: MEDIUM (overnight structure).
- Natural regime complement to every fade candidate (same classifier, opposite arm).
