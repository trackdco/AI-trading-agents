# US red-folder news archive — Jan 2023 → Jul 2026

`news_archive.csv` — timestamped high-impact (Forex Factory red-folder) US releases,
for Pat's news-aware agent ("arm C" of the regime-adaptation replay) and future
multi-year analog work.

- **Source:** Brake (Forex Factory red-folder export), 2026-07-18. 616 events, 307 unique
  days, span 2023-01-04 → 2026-07-16. All impact = high (red-folder only, by construction).
- **Columns:** `datetime_ET` (ISO, America/New_York wall clock), `date`, `time_et` (24h),
  `currency` (USD), `event`, `impact`. Times parsed from 12h am/pm — 0 unparseable.
- **Event families (19 types):** CPI (core/headline/yoy), PCE, NFP/AHE/Unemployment,
  ISM Mfg/Services, Retail Sales (core/headline), Advance GDP, FOMC (rate/statement/
  projections/minutes/presser), Fed Chair testimony.
- **Coverage for the current work:** 87 events fall in Feb–Jul 2026 (the OOS window).
- **Relation to `config/news_calendar.csv`:** that file is the engine's Feb calendar
  (hand-log-seeded). THIS archive is the broader, FF-verified reference — it supersedes the
  guessed Feb tags and extends through Jul + back to 2023. Wiring the engine to read this
  (vs the Feb-only calendar) is an engine-lane change, flagged, not done here.
- **Timezone note:** stored as ET wall-clock strings (no offset). DST is implicit in the
  clock time as FF publishes it; consumers localize to America/New_York.
