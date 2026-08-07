# Conventions — proven properties of this repo's data

Everything below was established empirically on 2026-08-07. Nothing is inherited
from documentation or column names. Reproduce command for §2–§3:
`python3 scripts/verify_conventions.py`. Guard tests (all shown failing red on
deliberately broken cases in the same run): `python3 tests/test_chokepoint_guards.py`.
All data access goes through `src/chokepoint.py` — the only module permitted to
read raw files, enforced by AST taint analysis with a known-positive violator
fixture.

## 1. Inventory

### OHLCV 1-minute bars (Databento GLBX.MDP3, CSV zstd)

| Archive | Span (UTC dates) | Days | Rows | Clock verdict |
|---|---|---|---|---|
| arch1 `glbx-mdp3-20230101-20250301` | 2023-01-02 → 2025-02-28 | 674 | 1,102,836 | UNVERIFIABLE |
| arch2 `glbx-mdp3-20250101-20250501` | 2025-01-01 → 2025-05-01 | 103 | 175,785 | UNVERIFIABLE |
| arch3 `glbx-mdp3-20250502-20251001` | 2025-05-02 → 2025-10-01 | 131 | 214,857 | CLEAN (verified) |
| arch4 `glbx-mdp3-20251002-20260131` | 2025-10-02 → 2026-01-30 | 104 | 162,748 | CLEAN (verified) |

- Full 24h CME session per day: front month prints exactly ~1,380 one-minute
  bars (23h trading day). A "continuous 24h ATR feed" is constructible.
- **Calendar spreads share the feed** (e.g. `NQH5-NQM5`) — defect #9. The
  loader filters to outrights by default.
- Missing weekdays across the whole 2023-01-02 → 2026-01-30 span: exactly 2 —
  2024-03-29 and 2025-04-18, both Good Friday full closures. No unexplained
  gaps. (Dates are UTC calendar dates, not CME session dates; holiday
  early-closes appear as low-bar days, not missing days.)
- arch1∩arch2 overlap (2025-01-01 → 2025-02-28): 75,659 rows in each, 100%
  row-identical. Same-vendor consistency, not an independent clock.
- Vendor condition report (`condition.json`, spans 2025-03-02 → 2026-01-30):
  285 days available, 3 degraded — 2025-09-17, 2025-09-24, 2025-11-28.

### MBP-10 book snapshots (condensed extracts, ~1 row/minute, top 10 levels, no trades)

| Family | Pattern | Days | Span | Window (wall clock) | Continuous symbol |
|---|---|---|---|---|---|
| london | `glbx-mdp3-*.mbp-10_condensed.csv` | 295 | 2025-06-02 → 2026-07-22 | 08:00–10:00 London | `NQ.v.0` (volume-roll) |
| ny2025 | `condensed_glbx-mdp3-*.mbp-10.csv` | 115 | 2025-06-02 → 2025-11-20 | 08:00–10:29 New York | `NQ.c.0` (calendar-roll) |
| ny2026 | `condensed_GLBX-20260720-*.csv` | 100 | 2026-02-02 → 2026-07-08 | 08:00–10:29 New York | `NQ.c.0` (calendar-roll) |

- **These files contain book messages only (actions A/C/M). No trades, no
  aggressor side.** ~120–150 rows/day. Each row is the last book update inside
  its minute (see §3).
- Two ny2025 files (2025-06-20, 2025-09-19) carry float-typed sizes and
  float-formatted fixed-point prices; the loader normalises both. Zero rows
  are silently dropped; drop counts are exposed via `chokepoint.last_load_stats`.
- The 09:30–10:30 ET strategy session is covered by ny-family snapshots only
  up to the 10:29 sample; there is no 10:30 observation.
- **Book+bars joint coverage (what an order-book-dependent rule can be tested
  on): ny2025 ∩ OHLCV = 2025-06-02 → 2025-11-20, 115 sessions.** ny2026 has NO
  overlapping OHLCV (bars end 2026-01-30 < 2026-02-02).

### Other

- `data/reference/feb2026_hand_log.csv` — 27 manually recorded trades,
  February 2026, MNQ. Single human clock: UNVERIFIABLE. Reference only.
- Images/PDF/screenshots at repo root: non-machine-readable artifacts, not data.

## 2. Bar labelling — PROVEN: START-labelled

A bar stamped `T` spans `[T, T+60s)`. Proven against the independent
`ts_recv` clock of the book snapshots (not against any file's prose):

- Method: compare each OHLCV front-month bar close against the book mid
  observed at candidate times; four hypotheses (START, CLOSE, nonsense ±120s).
- Result (78 clean days, n=11,701 comparisons): START median error **0.250 pts
  (one tick), 98.6% within 1 point**. CLOSE: 3.5 pts median, 18.4% within 1
  point — statistically indistinguishable from the deliberate nonsense
  alignments (3.375/6.0 pts). The test therefore demonstrably discriminates.
- arch4 verified the same way on its 27 book-overlap days: all day-medians
  ≤ 0.375 pts, zero mismatch days.
- The 10 excluded days (2025-06-16..20, 2025-09-15..19) are the two quarterly
  expiry weeks, where the `NQ.c.0` calendar-roll book tracks the next
  contract while the volume-max front month has not yet rolled (§5). Errors
  there (~220–244 pts) are the calendar carry, not a labelling failure.

## 3. Clock verdicts (defect #2 assertion)

| Source | Verdict | Evidence |
|---|---|---|
| london book | **FLOORED** | 35,401 rows: `ts_event` always exactly on the minute; `ts_recv − ts_event` median 59.889s, 99.97% in [55, 61]s |
| ny2025 book | **FLOORED** | 17,143 rows: median 59.961s, 99.90% in [55, 61]s |
| ny2026 book | **FLOORED** | 14,875 rows: median 59.981s, 99.93% in [55, 61]s |
| arch3, arch4 OHLCV | **CLEAN** | bar timestamps behave exactly as START-labelled bars against the book's `ts_recv` (§2) |
| arch1, arch2 OHLCV | **UNVERIFIABLE** | no independent clock exists before 2025-06-02; internally consistent with each other on their overlap |
| hand log | **UNVERIFIABLE** | single human clock |

**Consequence, applied by the loader:** a book row labelled `T` is the state at
`≈T+60s` (the last update inside minute `T`). The loader exposes `ts_true`
(from `ts_recv`) as the only observation time and quarantines the floored label
as `minute_label_raw`. The correction is fingerprint-guarded in both
directions: a file whose median offset is outside [55, 61]s is refused, so the
correction can never be applied to data that doesn't need it.

## 4. Timezone and session handling

- All raw timestamps are UTC. Session boundaries are defined in
  IANA `America/New_York` (or `Europe/London` for the london family) and
  resolved per day — never a fixed UTC offset. The two book-window UTC shifts
  observed across the DST change confirm the collection windows were wall-clock
  anchored.
- Strategy session (per `docs/constitution.md`): 09:30:00–10:30:00
  America/New_York.
- UTC calendar dates ≠ CME session dates: the Sunday-evening open (23:00 UTC)
  places early-session bars on the prior UTC date. Any per-session logic must
  bucket by exchange session, not UTC date.

## 5. Front-month convention

- Rule: per UTC date, the outright symbol with the maximum summed volume;
  ties broken by ascending symbol sort (stable, deterministic — defect #11).
- Known divergence: the ny book families use `NQ.c.0` (calendar roll, rolls
  the Monday of expiry week). Divergence days observed: 2025-06-16..20 and
  2025-09-15..19. Any analysis joining bars to ny-book data during expiry
  weeks must reconcile the two mappings explicitly or exclude those days —
  explicitly, not silently.

## 6. Fill model (recorded for the prereg; owner-directed)

- A resting limit/stop fills only on **trade-through by ≥ 1 tick**, never on a
  touch.
- The post-entry path starts at the **fill minute**, not the next bar boundary
  (defect #5).
- Same-bar fill and stop → **stop taken first, always** (defect #6).
- Where one bar contains both target and stop and no tick sequence exists:
  **bound both orderings**; never guess, never drop (defect #7).

## 7. Loader guard summary

- Sealed-path guard: spans in `docs/sealed_spans.json` (append-only; currently
  empty) raise `SealedPathError` unless `authorize_sealed=True`. Shown red and
  green in tests.
- Clock-fingerprint guard: shown red (synthetic honest-clock file refused) and
  green (real floored file corrected).
- Chokepoint AST test: variable-built-path violator fixture is detected
  (known positive); unparseable modules fail the test rather than being
  skipped; zero violations across the repo.
