# PARITY BATCH P4–P9 — CLASS MEMBERSHIP AND EXPECTED STATE — SEALED

> # DO NOT OPEN UNTIL ALL SIX READINGS ARE SUBMITTED.
>
> This file says **which of P4–P9 are detector-fires and which are random draws**, and carries
> the detector's expected state at each. Reading any of it first destroys the batch —
> `PARITY-BATCH-PREREG.md` §6 makes early opening a voiding condition.

**Drawn 2026-08-08 under `PARITY-BATCH-PREREG.md` §3, seed `4617547402224582382`
(from PART-1 commit `4014d2e5c31fbeeefe579d35d19558a2850afe87`).**

The machine-readable detail — class, per-timeframe indicator snapshot at the instant, the
candidate list, and the admitted trade where one exists — is in
**`data/PARITY-BATCH-SEALED.json`**, one object per instant under `batch`.

| field | meaning |
|---|---|
| `cls` | **`F`** = drawn from the 857 admitted trades · **`R`** = drawn from the 192,384 (session, minute) pairs |
| `snapshot` | per entry timeframe 2/3/5: bar OHLC, BB basis and ±2σ, daily VWAP mid/σ, NY VWAP mid/σ, `ny_sigma_eligible` under A13, POC, session H/L, prior-day Globex H/L, 4h clock-block range, HTF flag under A10, cluster list |
| `candidates_at_minute` | post-filter candidates at that minute under spec `42d6f0f6` |
| `admitted_at_minute` | the A7-admitted trade, if any, with entry / stop / target / tie-break level |

**Nothing here was ranked, scored or chosen.** Both classes are uniform `rng.sample` draws from
their pools; the P3 test-design scoring is abandoned.

**No outcome field exists in this file.** No P&L, no exit, no win rate — only state at the
instant. The archived pre-A8 sealed result was not opened to produce it.

**N_trials: 0.**
