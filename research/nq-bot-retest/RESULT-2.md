# RESULT-2 — NQ-bot, the 30-point cap removed (PREREGISTRATION-2.md)

**Status: holdout-2 runs launched 2026-09-07 06:08 UTC; verdict NOT yet read.** Part B is appended
once, after the single read.

## 0. Identity

| item | value |
|---|---|
| pre-registration | `PREREGISTRATION-2.md`, blob `8427b725…`, commit `66aaeb93` — written before any holdout-2 data was assembled |
| change under test | the 30-point maximum-stop cap removed (`--cap-lifted`), on the three live cells of the pass-marked family (`RESULT.md` §B) |
| verdict rule | minimum across V2-1 (10pt floor, gate removed, RTH), V2-2 (10pt floor, gate kept, RTH), V2-3 (2×ATR14, gate removed, RTH); mean > 0 and session-block bootstrap LB > 0 at **97.5%** in every cell; seed 20260907 |
| driver | `retest_backtest.py` (fast paths, level recording on), `run_holdout2.sh` = §5 as code; execution model = the bot's own close-based evaluation (`RESULT.md` §C.1) |

## A. Holdout-2 data — provenance and integrity, recorded before the read

| item | value |
|---|---|
| source | the repository's own raw Databento files, delivered unedited with Databento's manifests: `data/reference/nq_2017_2019_raw/glbx-mdp3-20160902-20200101.ohlcv-1m.csv.zst` (job GLBX-20260903-VHT7FR9HD9) and `nq_2020_2022_raw/glbx-mdp3-20200101-20230101.ohlcv-1m.csv.zst` (job GLBX-20260903-MEGV83QD59); GLBX.MDP3, ohlcv-1m, `NQ.FUT` parent symbology (every contract). Pulled by the user's other research programme on 2026-09-03 for its own 2020–22 holdout; **never run by, or on behalf of, this bot** |
| construction | unadjusted NQ front month, roll at the start of the Monday-of-expiry-week session (`build_nq_series.py --roll monday_of_expiry_week`), contract codes resolved decade-aware; fourteen contracts NQU8 → NQZ1 in clean quarterly sequence; 1,109,754 bars 2018-07-31 22:00 UTC → 2021-09-30 |
| window | engine starts cold on 2018-08-01; verdict counts entries 2018-09-01 → 2021-08-31 (three years; includes the 2020 crash) |
| sessions | 799 trading days 2018-08-01 → 2021-09-01, median 1,365 one-minute bars per day, six days under 1,000 (holidays / half days), no gap longer than a weekend |
| overlap check | September 2021, 29,749 minutes shared with the bot's own series: prices a constant offset per contract (bot − tape +2,389.25 during NQU1, sd 0.01; +2,396.51 during NQZ1, sd 0.20 — the bot's roll adjustment, as in `RESULT.md` §0); volumes identical on 94.0% of minutes, the rest differing by a median 23 contracts (vendor revisions and the roll week). Same instrument. |
| union | the tape plus the bot's checked-in files, prepared by the bot's own `prepare_historical_data.py` (2,314,536 bars, HTF rebuilt); the bot's bars kept where both exist, none of which the runs reach (they end 2021-08-31) |
| roll-convention note | the other programme's own 2020–22 series rolled by session-day volume, one to two sessions earlier on some quarters (its `roll_days.json`); this test uses the convention pre-registered in `PREREGISTRATION-2.md` §2, consistently |
| kill switch | armed from the cold start, as the bot's backtests are; a trip is reported as §2 requires |
| reads | one, covering the three cells, the three capped controls, the untouched control, the 2× slippage stress and the intrabar counterfactual (`run_holdout2.sh`) |

## B. Holdout-2 — NOT YET READ
