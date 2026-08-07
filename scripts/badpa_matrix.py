#!/usr/bin/env python3
"""BAD-PRICE-ACTION matrix (Angus 26-Jul: 'mechanical judgement layer on bad price action').

Target = the residual losers of the SHIPPED canon book. One row per trade of the 7-60pt
universe with ~20 NEW pre-fill PA/flow/structure features (windows 30/60 min BEFORE the fill,
zero lookahead), plus canon linkage (in_canon, canon pl).

PA (bars): vwap flatness+crosses, entry-level churn, net-path efficiency, wickiness,
indecision bars, range compression, BB-width state.
Flow (footprint): delta z, big prints, two-sided churn, 30m CVD divergence.
Structure: engine trigger density last 30m (over-firing = chop), canon sequencing
(prior same-day trade outcome, yesterday's canon day sign).

    python -m scripts.badpa_matrix
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
NY = "America/New_York"


def main():
    TM = pd.read_parquet("output/trade_matrix.parquet")
    TM = TM[(TM.risk >= 7) & (TM.risk <= 60)].copy()
    canon = pd.read_parquet("output/canon_book.parquet")
    csub = canon[canon["size"] > 0][["day", "book", "fill", "pl", "score", "governor"]]
    TM = TM.merge(csub, on=["day", "book", "fill"], how="left")
    TM["in_canon"] = TM.pl.notna()

    # bars + vwap
    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars = pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    ind = daily_vwap(bars, bands=[1, 2])
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(mi=bt, vw=ind["vwap"].values)
    B = bars.set_index("mi").sort_index()

    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index); M = M.sort_index()
    daymed = M.groupby("sday").vol.median()

    # engine trigger density: v2 caches
    from scripts.grade_window_cap import load as tload
    trigs = tload(["output/triggers_hist2326_ob_v2.csv", "output/triggers_feb_ob_v2.csv",
                   "output/triggers_marjul_ob_v2.csv"])
    tt = pd.DataFrame({"day": [t.ts[:10] for t in trigs]})
    tt["ts"] = pd.to_datetime([t.ts for t in trigs], utc=True).tz_convert(NY)
    tby = {d: g.ts.sort_values().values for d, g in tt.groupby("day")}

    # canon sequencing helpers
    cs = csub.copy()
    cs["fillts"] = pd.to_datetime(cs.fill, utc=True, format="mixed")
    cs = cs.sort_values("fillts")
    daypl = cs.groupby("day").pl.sum()
    days_sorted = sorted(daypl.index)
    prev_day_pl = {}
    for i, d in enumerate(days_sorted):
        prev_day_pl[d] = daypl[days_sorted[i - 1]] if i > 0 else np.nan

    rows = []
    for i, t in enumerate(TM.itertuples()):
        f = pd.Timestamp(t.fill).tz_convert(NY)
        out = {}
        try:
            w60 = B.loc[f - pd.Timedelta(minutes=60): f - pd.Timedelta(minutes=1)]
            w30 = w60.loc[f - pd.Timedelta(minutes=30):]
            if len(w30) >= 15:
                c = w30.close
                out["netpath_30"] = abs(c.iloc[-1] - c.iloc[0]) / max(c.diff().abs().sum(), 1e-9)
                out["rng_30"] = w30.high.max() - w30.low.min()
                # entry-level churn: crosses of the entry price
                s = np.sign(c - t.entry)
                out["lvl_churn_30"] = int((pd.Series(s).diff().abs() > 0).sum())
                sv = np.sign(c - w30.vw)
                out["vwap_cross_30"] = int((pd.Series(sv).diff().abs() > 0).sum())
                out["vwap_slope_30"] = abs(w30.vw.iloc[-1] - w30.vw.iloc[0])
                hl = (w30.high - w30.low).replace(0, np.nan)
                out["wicky_10"] = float(((hl - (w30.close - w30.open).abs()) / hl).tail(10).mean())
                body = (w30.close - w30.open).abs() / hl
                out["indec_30"] = float((body < 0.3).mean())
                std20 = c.rolling(20).std().iloc[-1]
                day_c = B.loc[f.normalize() + pd.Timedelta(hours=2): f - pd.Timedelta(minutes=1)].close
                out["bbw_state"] = float(std20 / max(day_c.rolling(20).std().median(), 1e-9)) if len(day_c) > 40 else np.nan
            if len(w60) >= 30:
                c6 = w60.close
                out["netpath_60"] = abs(c6.iloc[-1] - c6.iloc[0]) / max(c6.diff().abs().sum(), 1e-9)
        except Exception:
            pass
        try:
            g = M.loc[f - pd.Timedelta(minutes=30): f - pd.Timedelta(minutes=1)]
            g15 = g.loc[f - pd.Timedelta(minutes=15):]
            if len(g) >= 10:
                med = daymed.get(t.day, np.nan)
                out["churn_flow_30"] = abs(g.delta.sum()) / max(g.vol.sum(), 1)     # low = two-sided grind
                out["bigprint_15"] = int((g15.vol >= 3 * med).sum()) if med == med else np.nan
                d15s = g15.delta.sum()
                sd15 = M.loc[f.normalize(): f - pd.Timedelta(minutes=1)]
                roll = sd15.delta.rolling(15).sum().dropna()
                out["deltaz_15"] = d15s / max(roll.std(), 1) if len(roll) > 20 else np.nan
                px30 = g.vwp.dropna()
                if len(px30) > 5:
                    out["cvddiv_30"] = int(np.sign(px30.iloc[-1] - px30.iloc[0]) != np.sign(g.delta.sum())
                                           and abs(px30.iloc[-1] - px30.iloc[0]) > 5 and abs(g.delta.sum()) > 200)
        except Exception:
            pass
        arr = tby.get(t.day)
        if arr is not None:
            out["trigdens_30"] = int(((arr >= (f - pd.Timedelta(minutes=30)).to_datetime64())
                                      & (arr < f.to_datetime64())).sum())
        # sequencing
        prior = cs[(cs.day == t.day) & (cs.fillts < pd.Timestamp(t.fill).tz_convert("UTC").tz_convert(NY))]
        out["prior_ct"] = len(prior)
        out["prior_pl"] = prior.pl.sum() if len(prior) else 0.0
        out["prior_loss"] = int(len(prior) > 0 and prior.pl.iloc[-1] < 0)
        out["yday_canon_red"] = int(prev_day_pl.get(t.day, np.nan) < 0) if prev_day_pl.get(t.day, 1) == prev_day_pl.get(t.day, 1) else np.nan
        rows.append(out)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(TM)}", flush=True)

    X = pd.DataFrame(rows, index=TM.index)
    keep = ["day", "book", "fill", "direction", "entry", "risk", "dollars", "pattern", "yr",
            "win_", "in_canon", "pl", "score"]
    out = pd.concat([TM[keep], X], axis=1)
    out["win"] = out.dollars > 0
    out["mo"] = out.day.str[:7]
    out.to_parquet("output/badpa_matrix.parquet")
    print(f"wrote output/badpa_matrix.parquet: {len(out)} trades ({int(out.in_canon.sum())} canon) "
          f"x {X.shape[1]} new features")


if __name__ == "__main__":
    main()
