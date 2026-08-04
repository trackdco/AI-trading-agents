---
date: 2026-08-04
status: greenlit
tags: [london, session-structure, news]
sources: ["findings/strategy-classes-evidence.md#10", "findings/strategy-classes-evidence.md#shortlist-3"]
---

# london-eu-macro-windows — the scheduled European news nobody prices in NQ

## Thesis (for Angus)

Surfaced by the evidence survey, not the concept sweeps — and it's the survey's
highest evidence-to-crowding pick after the inventory trade. Scheduled European
data lands at fixed clock times inside our window every week: German prints and
UK data around 02:00 ET, flash PMIs 03:15–04:00 ET, Eurozone aggregates around
05:00 ET. Announcement-window effects are among the most robust facts in
empirical finance at the daily level (the pre-FOMC drift literature; Gao's
finding that intraday momentum is STRONGER on macro-news days) — yet no
published work prices these specific windows in US index futures. Nobody is
trading NQ at 04:00 ET around a flash PMI with any published system; the crowd
that prices FOMC to the second simply isn't at this desk at this hour. The wrong
side is whoever holds stale positions through a surprise, plus the
slow-to-reprice European reaction that a fast tape collects. Even a NULL result
pays: clean event dummies upgrade every other London candidate (news-day
conditioning was already flagged in the euro-open-drive thesis).

## Mechanical skeleton

Build the recurring EU release calendar 2023–2026 (fixed clock times; UK/CET
clock per the DST spec layer). Event-study NQ 1-min returns/vol in ±30 min
around each release type. Two candidate rules: (a) post-release drift — enter in
the surprise direction (proxy: the first 1-min reaction) 1–2 min after the
print, hold 15–60 min, vol-scaled stop/target; (b) pre-release stand-aside — a
veto window for all other London candidates (no fresh entries N min before a
release; flatten or hold rule decided per candidate). Trade count is naturally
low; the thin-book cost hurdle amortizes over event-sized moves.

## Flags

- Data: candles-only (calendar reconstruction needed — release times are
  deterministic; historical surprise magnitudes proxied from the tape itself).
- Crowding: near zero in NQ at these hours per the survey; announcement premia
  are uncertainty-dependent, not gone.
- NY-canon input-family overlap: LOW (news/time family — a genuinely NEW input
  family for the portfolio, which the diversity criterion wants).
- Interaction: rule (b) is a spec layer for all candidates regardless of whether
  rule (a) survives — the H4 news-buffer idea from the old NY parked list,
  finally testable.
