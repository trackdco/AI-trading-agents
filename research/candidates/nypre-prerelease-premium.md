---
date: 2026-08-04
status: greenlit
tags: [ny-pre, news, overnight-structure]
sources: ["articles/sweep-2026-08-04-nypre-macro.md#M4"]
---

# nypre-prerelease-premium — get paid for holding into the number, flat before it prints

## Thesis (for Angus)

A published JFE result: index futures earn a small positive drift in the hours
BEFORE major prints (NFP/ISM/GDP class) — with no extra variance — as
compensation to whoever holds while everyone else de-risks into the event. The
leakage version of pre-announcement drift was killed by the 2018 lockup
reforms; this is the insurance-premium channel, which survives conditionally —
it concentrates when uncertainty is elevated. The trade: long 04:00→08:25 on
high-vol-regime tier-1 days, always flat before the print. Wrong side: capital
paying the insurance by de-risking. Honest framing: single-digit basis points
per event — a low-Sharpe tilt that only makes sense on leverage and possibly
as a directional bias on the canon's own window rather than a standalone.

## Skeleton

Tier-1 day + trailing 5-day realized vol top-tercile → long 04:00 (test 06:00/
07:00 accrual timing), exit 08:25 unconditionally. Disaster stop only. Never
through the print.

## Flags

- Candles + calendar only; no surprise data needed at all.
- Fully inside the pre window — no semantics ruling needed.
- Canon redundancy: LOW (time-based premium harvest, no setup logic).
- The famous FOMC cousin is dead unconditionally — test only as the
  high-uncertainty conditional; expectation modest by design.
