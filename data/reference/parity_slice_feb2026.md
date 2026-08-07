# Parity data slice — Feb 2026 (for the Step 4 parity gate)

`parity_slice_feb2026.csv` is a small slice of the full (gitignored) NQ dataset, committed so
any session/branch can reproduce the Step 4 parity check without the ~30 MB raw file.

**Coverage:** two windows, each starting at the 18:00-ET CME session open of the prior evening
so the daily VWAP anchors correctly:
- 2026-02-10 18:00 ET → 2026-02-11 23:59 ET  (parity bar: **Feb 11 09:48 ET**)
- 2026-02-16 18:00 ET → 2026-02-17 23:59 ET  (parity bar: **Feb 17 09:50 ET**)

**Format (what Angus's chat asked for):**
- **CSV**, columns: `ts_event, open, high, low, close, volume, roll`
- **timezone:** America/New_York, tz-aware ISO 8601 with offset (e.g. `2026-02-10T18:00:00-0500`; February = EST, −05:00)
- prices are decimal NQ points; 1-minute bars
- **continuous front-month** (volume-based roll, unspliced) derived from the Databento GLBX.MDP3
  parent export; `roll` flags the first bar after a contract change (no rolls inside this slice)
- **bars are START-labeled** (ts_event = the open of the 1-minute interval; the 09:48 bar covers
  09:48:00–09:48:59 and is fully closed at 09:49)

Engine-computed indicator values for the two parity bars live in `output/parity_report.md`.
