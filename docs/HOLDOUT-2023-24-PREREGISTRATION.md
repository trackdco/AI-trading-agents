# HOLDOUT PRE-REGISTRATION — 2023/2024 out-of-regime canon validation

**This file is the commitment.** It is written and committed BEFORE any depth or
trades data is pulled and before anything is scored. The SHA-256 below fixes the
day list. If a later result is reported against a different set of days, this file
is the evidence.

| field | value |
|---|---|
| mode | `months` |
| n requested | 6 |
| seed | `20260727` |
| days drawn | **128** |
| 2023 / 2024 split | 63 / 65 |
| eligible universe | 513 days (>= 1000 1m bars, 2023-2024) |
| **SHA-256 of day list** | `f4e17f1770a4d5314d02ccdda7d362b97ae891aa833ea21ef564fc5ca7c9a87e` |

Regenerate the digest to verify:

```bash
python3 -c "import hashlib,pandas as pd; d=pd.read_csv('data/reference/holdout_2023_24_days.csv'); print(hashlib.sha256(chr(10).join(d.day).encode()).hexdigest())"
```

## Why these days are out of fit

The canon is fitted on **2025-06-02 -> 2026-07-15** — the span begins on the exact
day MBP-10 depth coverage begins. Every threshold in `scripts/live_thresholds.py`
is a frozen 2025 quantile. No 2023 or 2024 day contributed to any of them.

## Blocks drawn (6)

| block | days |
|---|---|
| 2023-07 | 21 |
| 2023-09 | 21 |
| 2023-11 | 21 |
| 2024-03 | 20 |
| 2024-04 | 22 |
| 2024-10 | 23 |

## The sealed day list

```
2023-07-03  2023-07-04  2023-07-05  2023-07-06  2023-07-07  2023-07-10  2023-07-11  2023-07-12
2023-07-13  2023-07-14  2023-07-17  2023-07-18  2023-07-19  2023-07-20  2023-07-21  2023-07-24
2023-07-25  2023-07-26  2023-07-27  2023-07-28  2023-07-31  2023-09-01  2023-09-04  2023-09-05
2023-09-06  2023-09-07  2023-09-08  2023-09-11  2023-09-12  2023-09-13  2023-09-14  2023-09-15
2023-09-18  2023-09-19  2023-09-20  2023-09-21  2023-09-22  2023-09-25  2023-09-26  2023-09-27
2023-09-28  2023-09-29  2023-11-01  2023-11-02  2023-11-03  2023-11-06  2023-11-07  2023-11-08
2023-11-09  2023-11-10  2023-11-13  2023-11-14  2023-11-15  2023-11-16  2023-11-17  2023-11-20
2023-11-21  2023-11-22  2023-11-23  2023-11-27  2023-11-28  2023-11-29  2023-11-30  2024-03-01
2024-03-04  2024-03-05  2024-03-06  2024-03-07  2024-03-08  2024-03-11  2024-03-12  2024-03-13
2024-03-14  2024-03-15  2024-03-18  2024-03-19  2024-03-20  2024-03-21  2024-03-22  2024-03-25
2024-03-26  2024-03-27  2024-03-28  2024-04-01  2024-04-02  2024-04-03  2024-04-04  2024-04-05
2024-04-08  2024-04-09  2024-04-10  2024-04-11  2024-04-12  2024-04-15  2024-04-16  2024-04-17
2024-04-18  2024-04-19  2024-04-22  2024-04-23  2024-04-24  2024-04-25  2024-04-26  2024-04-29
2024-04-30  2024-10-01  2024-10-02  2024-10-03  2024-10-04  2024-10-07  2024-10-08  2024-10-09
2024-10-10  2024-10-11  2024-10-14  2024-10-15  2024-10-16  2024-10-17  2024-10-18  2024-10-21
2024-10-22  2024-10-23  2024-10-24  2024-10-25  2024-10-28  2024-10-29  2024-10-30  2024-10-31
```

## What happens next

1. Commit this file and `data/reference/holdout_2023_24_days.csv`. **Before the pull.**
2. Run `notebooks/colab_holdout_pull.ipynb` — it reads the sealed list verbatim and
   pulls MBP-10 depth + trades for exactly these days, nothing else.
3. Condensed artifacts land in `data/reference/depth_2023_24/` and
   `data/reference/cvd/`. Raw data never enters the repo.
4. Score with the canon **unchanged** — no refits, no new knobs. Any threshold that
   moves makes this a fit, not a holdout.

## Known limit, stated up front

The golden window fires 0.20 trades/day. The `Q <= 1` cut — already flagged in
`docs/CANON-MECHANICAL.md` as a 16-trade watch item and "first thing to re-test on
2023/24" — will land only a handful of trades at this sample size. **This holdout
cannot settle that layer.** It is recorded here so the result is not over-read later.
