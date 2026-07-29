# Contract roll dates — what the BACKTEST actually rolled on

**For Pat's question 3.** The backtest consumed Databento `NQ.v.0` — a **volume-based** continuous
contract. Sierra/RollWatcher rolls on a **calendar** rule. If they disagree, live and backtest are
scoring different contracts and **gate A1 (feature parity) fails**. These are the real dates.

## Method (reproducible)

`NQ.v.0` is an alias; the underlying contract shows up as `instrument_id`. A roll is the day
`instrument_id` changes. Extracted from `data/reference/depth_london/*.csv` (295 daily files,
2025-06-02 → 2026-07-22 — the backtest span):

```python
rows = [(f.split("mdp3-")[1][:8], pd.read_csv(f, usecols=["instrument_id"], nrows=1).iloc[0,0])
        for f in sorted(glob.glob("data/reference/depth_london/*.csv"))]
r = pd.DataFrame(rows, columns=["day","iid"]); r[r.iid != r.iid.shift()]
```

## The dates

| volume roll (first day on new contract) | instrument_id | expiry (3rd Friday) | days before expiry | weekday |
|---|---|---|---|---|
| *2025-06-02* | 42005804 | — | *(start of data, not a roll)* | |
| **2025-06-18** | 42008487 | 2025-06-20 | **2** | Wed |
| **2025-09-18** | 158704 | 2025-09-19 | **1** | Thu |
| **2025-12-17** | 42002475 | 2025-12-19 | **2** | Wed |
| **2026-03-18** | 42004058 | 2026-03-20 | **2** | Wed |
| **2026-06-17** | 42004177 | 2026-06-19 | **2** | Wed |

6 distinct contracts across 295 days.

## The pattern, and the risk

**Databento's volume roll lands on the Wednesday 2 days before expiry** — 4 of 5 rolls. The one
exception (2025-09-18) was 1 day before, a Thursday. So the volume roll is **very late**: it waits
until front-month volume actually transfers, which for NQ is the middle of expiry week.

**This is the divergence to check.** Most calendar rules roll *earlier* than this:

| convention | Sep-2026 roll date | vs Databento |
|---|---|---|
| Databento volume (observed pattern) | **~2026-09-16** (Wed) | — |
| "8 days before expiry" | 2026-09-10 | **6 days early** |
| "Thursday before expiry week" | 2026-09-10 | **6 days early** |
| "Monday of expiry week" | 2026-09-14 | **2 days early** |

If RollWatcher uses any of those, live switches to the back month **while the backtest was still
scoring the front month** — for up to 6 sessions per quarter. Prices differ by the calendar spread,
so every level-based feature (VWAP bands, POC, walls, fib) is computed on a different instrument.
**A1 fails, and it fails silently** — nothing crashes, the numbers are just wrong.

**Action for Pat:** state RollWatcher's exact rule, diff it against the table above, and align it
to the volume roll (or make the roll date a config constant set from this table).

## Next roll inside the likely paper window

**Sep 2026 expiry = Friday 2026-09-18 → expected volume roll ≈ Wednesday 2026-09-16.**

Any paper window running August into mid-September contains this roll. Two consequences:
1. It is the §E rollover event — see the §E ruling.
2. **Do not pick a reconciliation day within ~3 sessions of a roll** (Pat's question 4). A
   contract mismatch there would look like a feature-parity failure and send everyone hunting a
   bug that is really a calendar artifact.
