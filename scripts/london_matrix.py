#!/usr/bin/env python3
"""LONDON feature matrix: one row per London-substrate trade with every at-fill /
pre-fill feature family EXCEPT depth (heatmap not yet purchased). Zero lookahead —
all windows end strictly before the fill; session context is overnight-so-far only
(no US pre-market exists at London fill time).

    python -m scripts.london_matrix
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
NY = "America/New_York"


def main():
    S = pd.read_parquet("output/london_substrate.parquet")
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()

    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars = (pd.concat([mb, fb], ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    ind = daily_vwap(bars, bands=[1, 2])
    bars = bars.assign(mi=bars.ts_event.dt.tz_convert(NY), vw=ind["vwap"].values,
                       sd1u=ind["upper_1"].values, sd1d=ind["lower_1"].values)
    B = bars.set_index("mi").sort_index()

    trig = pd.read_csv("output/triggers_london.csv")
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
    out.to_parquet("output/london_matrix.parquet")
    print(f"wrote output/london_matrix.parquet: {len(out)} trades x {X.shape[1]} features")
    for yr in (2025, 2026):
        d = out[out.yr == yr]
        print(f"  {yr}: n={len(d)} WR {(d.dollars>0).mean()*100:.0f}% raw ${d.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
