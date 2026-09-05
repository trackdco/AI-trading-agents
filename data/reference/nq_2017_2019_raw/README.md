# NQ.FUT 1m, 2016-09-02 -> 2020-01-01 — raw Databento pull (the second sealed holdout)

Job `GLBX-20260903-VHT7FR9HD9`, dataset GLBX.MDP3, schema ohlcv-1m, symbols `NQ.FUT`
(stype_in parent), pretty_px/pretty_ts/map_symbols on. Files exactly as delivered;
`manifest.json` carries Databento's own sha256 for each, verified before the build:

    glbx-mdp3-20160902-20200101.ohlcv-1m.csv.zst
    sha256 b30ed67bec46368e801ccdb2411f40cd06bac83fd8c66d19e395ef5d350d2879

Two `degraded` days in `condition.json` (2017-11-13 and any later ones) are kept —
the pre-registration does not exclude them and the engine's completeness filter
handles thin days. Scored window is 2017-01-01 -> 2019-12-31 (Amendment 1);
2016-09 -> 2016-12 is warmup only.

Rebuild: `python -m scripts.build_nq_2017_2019 <this .zst> data/reference`
