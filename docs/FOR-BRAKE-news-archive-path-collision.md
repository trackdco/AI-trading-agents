# FOR BRAKE — historical calendar landed on the arm-C news path (breaks _load_inputs)

Your historical FF calendar arrived at **`data/reference/news_archive.csv`** with schema
`datetime_ET,date,time_et,currency,event,impact` (economic events — great, this fills the
2023-25 red_folder gap).

**Problem:** that exact path is what the desk's arm-C NEWS loader reads
(scripts/run_regime_replay.py `_load_inputs`), and it expects a *headline* archive with a
`published_ET` column. So `_load_inputs()` now raises `KeyError: 'published_ET'` — any
`emit` or a normal regime replay through that harness crashes on load. (The v0.5
calibration ingest already works around it by reading the vector directly.)

**Suggested fix (your call — it's your data lane):**
- Put the historical calendar at a distinct path, e.g. `data/reference/ff_calendar_hist.csv`,
  and merge it into the CALENDAR loader (the `datetime_ET/event/impact` path build_briefing
  already consumes), not the news loader.
- Keep `news_archive.csv` reserved for the actual arm-C headline feed (`published_ET`,
  `headline`), which is a different artifact.

Until then the calendar file and the news loader are aliased and collide. Nothing of yours
is lost — just needs a rename + wiring into the calendar path. Flag me if you'd rather I
take the loader-side change (adjust `_load_inputs` to detect schema and route accordingly);
I left it untouched since it's the engine/data lane.
