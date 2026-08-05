---
date: 2026-08-05
kind: feature study result (NYA-CVD-01, P6)
status: primary window KILLED; 08:00 variant ADOPTED as feature (small n)
tags: [ny-am, pre-market, cvd, feature-study]
sources: ["scripts/nya_cvd_gate_study.py (declaration in header, committed before run)"]
---

# Pre-market CVD pressure gate — study verdict

CLAIM: strong one-sided pre-market aggressive flow against balanced price
predicts the open's direction (Fabervaale Dec-30 pattern, generalized).

RESULT (264 flow-span sessions, declared bars):
- 06:00-09:29 PRIMARY window: KILLED. Gate fires 12% of days; directional
  hit on the 09:30→10:30 move 42% overall (2025H2 50%, 2026H1 20%) — below
  the declared 55% bar in both required eras, worse than the 59% base
  up-drift. The full-overnight pressure read is noise, or slightly
  contrarian (a contrarian variant would be a NEW declared study, not a
  retune of this one).
- 08:00-09:29 VARIANT window: PASSES. Fires 9% of days (n=24); hit 73%
  (2025H2) / 71% (2026H1) / 100% (2026H2, n=3); average with-gate move
  +14 pts by day-end, +34.6 pts in 2026H1. The signal lives in the LAST 90
  minutes of pre-market — same lesson as the canon's d5 gate: recency of
  flow matters, long windows dilute.

ADOPTION: `pm_press_0800` (delta sum 08:00-09:29 / 20-day baseline, with the
balanced-price condition) enters the conditioning library as a declared
feature. CAVEAT ON THE LABEL: n=24 gate-days over 13.5 months — feature-grade
evidence, not strategy-grade; every use in a candidate's search is its own
ledgered arm.

CROSS-PROGRAM NOTES:
- Other chat / pre-market program: do NOT adopt the full-overnight version;
  the 08:00 variant is the one with evidence, and it predicts the OPEN, not
  pre-market entries themselves.
- Canon pre leg: the canon enters 08:00-09:30 — a same-window pressure read
  is a legal conditioning candidate for the 5-day-loop optimization file
  (NOT applied live; goes through the standard process).
- Machine ledger: both windows recorded (2 trials, NYA-CVD-01).
