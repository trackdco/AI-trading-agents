# NQ 2020-01-01 → 2023-01-01, 1-minute OHLCV — the holdout tape, raw

Databento batch job **GLBX-20260903-MEGV83QD59**, pulled 2026-09-03 *after*
`docs/PREREG-holdout-2020-2022.md` was committed (`80c3f23`). This is the
file exactly as delivered; `manifest.json`, `metadata.json` and
`condition.json` are Databento's own, unedited.

| | |
|---|---|
| dataset / schema | GLBX.MDP3 / ohlcv-1m |
| symbols | `NQ.FUT`, stype_in=parent (**not** `EURUSD.FUT`-style basis books — see docs/FINDINGS-6e-euro-port.md §1) |
| range | 2020-01-01 → 2023-01-01 UTC |
| file | `glbx-mdp3-20200101-20230101.ohlcv-1m.csv.zst`, 23,361,762 bytes |
| sha256 | `3eb70249f7d53d0c2ac438b85cff254c60b00599a94b5cebe3d552b9286eb558` (matches manifest) |
| raw rows | 1,519,338 |
| days Databento marks degraded | 2020-02-27, 2020-02-28, 2020-06-30, 2020-07-01, 2021-12-05, 2022-01-02 |

## Derived files (one directory up)

`nq_2020_2022_1m.parquet` and `nq_2020_2022_roll_days.json` are built from
this file by `scripts/build_nq_2020_2022.py` — outrights only, front month by
session-day volume, 12 roll session-days flagged. 1,057,201 bars / 779
session-days / 6,628.75–16,767.50.

Rebuilt from this raw file on 2026-09-03 and diffed against the parquet the
holdout was actually scored on: **bar-for-bar identical, roll days identical.**
The engine reads it via `--instrument nq20a` (frozen constants) or `nq20b`
(era-scaled) in `scripts/pd_va_backtest.py` and `scripts/vwap_revolve.py`.

## What was run on it

- `docs/FINDINGS-holdout-2020-2022.md` — PD value-area book, pre-registered, **PASS**
- `docs/FINDINGS-replication-2020-2022-empire.md` — full three-book stack + arming
- `docs/FINDINGS-loser-autopsy.md` — day-level autopsy across both eras

No news calendar exists for these years, so every run on this tape is
without G8 (`--no-news-gate` / no `_ng` suffix).
