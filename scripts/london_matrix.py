#!/usr/bin/env python3
"""LONDON feature matrix: one row per London-substrate trade with every at-fill /
pre-fill feature family EXCEPT depth (heatmap not yet purchased). Zero lookahead —
all windows end strictly before the fill; session context is overnight-so-far only
(no US pre-market exists at London fill time).

`--span holdout` runs the identical feature loop over the sealed 2023/24 substrate. The only
things that change are the file paths: the tape comes from the holdout footprint parquets
folded to minutes (fp_minutes covers the fit window only) and the triggers from the holdout
detection. Every window, threshold and formula below is untouched.

    python -m scripts.london_matrix
    python -m scripts.london_matrix --span holdout
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.score_canon_span import minute_tape  # noqa: E402
from src.engine.indicators import daily_vwap
NY = "America/New_York"

SPANS = {
    "fit": {
        "sub": "output/london_substrate.parquet",
        "tape": "output/fp_minutes.parquet",
        "bars": [("data/reference/nq_1m_master.parquet", "2025-05-20"),
                 ("data/reference/nq_1m_feb_jul2026.parquet", None)],
        "trigs": "output/triggers_london.csv",
        "out": "output/london_matrix.parquet",
        "years": (2025, 2026),
    },
    "holdout": {
        "sub": "output/london_substrate_holdout.parquet",
        "tape": "data/reference/cvd/footprint_holdout_*.parquet",
        "bars": [("data/reference/nq_1m_master.parquet", "2023-05-01")],
        "trigs": "output/triggers_london_holdout.csv",
        "out": "output/london_matrix_holdout.parquet",
        "years": (2023, 2024),
    },
    # Forward span — days AFTER the fit span, for forward/shadow logging. Same tape and
    # bar sources as `fit`: they are the LIVE files, appended to as new sessions land, so
    # the only thing distinguishing a forward run is WHICH DAYS are fed in (via
    # build_l0_triggers_london --days-file). sub/trigs/out are supplied by
    # build_l3_features_london's overrides. NOTE: unexercised as of this commit — the bar
    # tape ends 2026-07-15, so no post-fit day is buildable yet.
    "forward": {
        "sub": "output/london_substrate_forward.parquet",
        "tape": "output/fp_minutes.parquet",
        "bars": [("data/reference/nq_1m_master.parquet", "2025-05-20"),
                 ("data/reference/nq_1m_feb_jul2026.parquet", None)],
        "trigs": "output/l0_triggers_london_forward.parquet",
        "out": "output/london_matrix_forward.parquet",
        "years": (2026, 2027),
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), default="fit")
    # L3 overrides: the rebuild feeds this loop the L2 outcomes and the L0 census instead of
    # the old substrate/trigger caches. The feature code below is untouched — that is the
    # point, since the L3 gate reproduces the cached matrix to 1e-6 on matched fills.
    ap.add_argument("--sub", default=None, help="override the substrate parquet")
    ap.add_argument("--trigs", default=None, help="override the trigger stream (csv or parquet)")
    ap.add_argument("--out", default=None, help="override the output matrix path")
    a = ap.parse_args()
    spec = dict(SPANS[a.span])
    for _k, _v in (("sub", a.sub), ("trigs", a.trigs), ("out", a.out)):
        if _v:
            spec[_k] = _v

    S = pd.read_parquet(spec["sub"])
    M = minute_tape({"tape": spec["tape"]})
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()

    frames = []
    for path, since in spec["bars"]:
        b = pd.read_parquet(path).drop(columns=["roll"], errors="ignore")
        if since:
            b = b[b.ts_event >= pd.Timestamp(since, tz=NY)]
        frames.append(b)
    bars = (pd.concat(frames, ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    ind = daily_vwap(bars, bands=[1, 2])
    bars = bars.assign(mi=bars.ts_event.dt.tz_convert(NY), vw=ind["vwap"].values,
                       sd1u=ind["upper_1"].values, sd1d=ind["lower_1"].values)
    B = bars.set_index("mi").sort_index()

    trig = (pd.read_parquet(spec["trigs"]) if str(spec["trigs"]).endswith(".parquet")
            else pd.read_csv(spec["trigs"]))
    tts = pd.to_datetime(trig.ts, utc=True, format="mixed").dt.tz_convert(NY)
    tby = {d: g.sort_values().values for d, g in tts.groupby(tts.dt.strftime("%Y-%m-%d"))}

    rows = []
    for i, t in enumerate(S.itertuples()):
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        sgn = 1 if t.direction == "long" else -1
        sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)  # 18:00 prior evening
        out = {}
        try:
            e = pd.Timestamp(t.exit).tz_convert(NY)
            out["hold_min"] = (e - f).total_seconds() / 60
        except Exception:
            out["hold_min"] = np.nan
        # --- footprint windows (strictly pre-fill) ---
        g = M.loc[sess0: f - pd.Timedelta(minutes=1)]
        if len(g) >= 60:
            for k in (5, 15, 30):
                dk = g.delta.tail(k).sum()
                out[f"d{k}"] = dk
                out[f"d{k}_conf"] = int(np.sign(dk) == sgn)
            fd = g.delta.iloc[-1]
            out["fill_delta"] = fd
            out["fill_delta_conf"] = int(np.sign(fd) == sgn)
            med = g.vol.median()
            out["fill_vol_rel"] = g.vol.iloc[-1] / max(med, 1)
            out["cvd_ON_sofar"] = g.delta.sum()
            out["conf_ON_sofar"] = int(np.sign(g.delta.sum()) == sgn)
            asia = g.loc[: sess0 + pd.Timedelta(hours=8)]           # 18:00-02:00 ET
            out["cvd_ASIA"] = asia.delta.sum() if len(asia) > 60 else np.nan
            out["conf_ASIA"] = int(np.sign(out["cvd_ASIA"]) == sgn) if out["cvd_ASIA"] == out["cvd_ASIA"] else np.nan
            lon_open = f - pd.Timedelta(minutes=int((f - sess0).total_seconds() // 60))  # placeholder
            g30 = g.tail(30)
            out["churn_flow_30"] = abs(g30.delta.sum()) / max(g30.vol.sum(), 1)
            roll = g.delta.rolling(15).sum().dropna()
            out["deltaz_15"] = g.delta.tail(15).sum() / max(roll.std(), 1) if len(roll) > 30 else np.nan
        # --- bars / geometry / PA (strictly pre-fill) ---
        try:
            w = B.loc[sess0: f - pd.Timedelta(minutes=1)]
            if len(w) >= 90:
                c = w.close
                out["ent_on_pos"] = (t.entry - w.low.min()) / max(w.high.max() - w.low.min(), 1e-9)
                out["on_range"] = w.high.max() - w.low.min()
                ext_t = w.high.idxmax() if ((t.entry - w.low.min()) > (w.high.max() - t.entry)) else w.low.idxmin()
                out["on_extreme_age"] = (f - ext_t).total_seconds() / 60
                sd = (w.sd1u.iloc[-1] - w.vw.iloc[-1])
                out["ent_vs_vwap_sd"] = (t.entry - w.vw.iloc[-1]) / max(sd, 1e-9)
                out["ent_vs_vwap_sd_dir"] = out["ent_vs_vwap_sd"] * sgn
                w30 = w.tail(30)
                c30 = w30.close
                out["netpath_30"] = abs(c30.iloc[-1] - c30.iloc[0]) / max(c30.diff().abs().sum(), 1e-9)
                out["rng_30"] = w30.high.max() - w30.low.min()
                s_ = np.sign(c30 - t.entry)
                out["lvl_churn_30"] = int((pd.Series(s_).diff().abs() > 0).sum())
                sv = np.sign(c30 - w30.vw)
                out["vwap_cross_30"] = int((pd.Series(sv).diff().abs() > 0).sum())
                out["vwap_slope_30"] = abs(w30.vw.iloc[-1] - w30.vw.iloc[0])
                hl = (w30.high - w30.low).replace(0, np.nan)
                out["wicky_10"] = float(((hl - (w30.close - w30.open).abs()) / hl).tail(10).mean())
                out["indec_30"] = float(((w30.close - w30.open).abs() / hl < 0.3).mean())
                std20 = c.rolling(20).std()
                out["bbw_state"] = float(std20.iloc[-1] / max(std20.median(), 1e-9)) if len(c) > 60 else np.nan
        except Exception:
            pass
        arr = tby.get(t.day)
        if arr is not None:
            out["trigdens_30"] = int(((arr >= (f - pd.Timedelta(minutes=30)).to_datetime64())
                                      & (arr < f.to_datetime64())).sum())
        rows.append(out)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(S)}", flush=True)

    X = pd.DataFrame(rows, index=S.index)
    out = pd.concat([S.reset_index(drop=True), X.reset_index(drop=True)], axis=1)
    out["win"] = out.dollars > 0
    out["mo"] = out.day.str[:7]
    out["win_et"] = out.wgroup
    out.to_parquet(spec["out"])
    print(f"wrote {spec['out']}: {len(out)} trades x {X.shape[1]} features")
    for yr in spec["years"]:
        d = out[out.yr == yr]
        print(f"  {yr}: n={len(d)} WR {(d.dollars>0).mean()*100:.0f}% raw ${d.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
