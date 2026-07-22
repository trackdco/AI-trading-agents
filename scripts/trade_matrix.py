#!/usr/bin/env python3
"""PER-TRADE MEGA-MATRIX (Angus 24-Jul, 'test everything'). One row per trade of the 970-trade
both-books universe, with EVERY at-entry variable we can compute, leakage-clean:

  tape (truncated AT FILL): pm_sofar cvd/|cvd|/eff/crosses/path-eff, op_sofar cvd/eff,
        last 5/15/30-min delta, CVD path position (running min/max, no lookahead),
        minute vol/delta at fill vs day median
  session context (pre-08:00, safe for all fills): ON/Asia/London cvd + eff + |z|,
        inventory, rel_range, rel_vol, yday_red, gap, on_extreme_age, on_eff_path
  geometry: entry vs daily-VWAP bands (pts), position in ON range, London sweep state at fill,
        entry minute-of-day, risk pts, tf, direction, book, pattern
  depth AT ENTRY (where covered): book thickness/imbalance/near-imb, support-vs-resist,
        wall above/below distance+size, 5-min thickness delta, spread
  entry-tick signals (already scored): absorption, delta_div, stacked_imb, conf_* flags
  outcome: dollars, win, R

    python -m scripts.trade_matrix
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
NY = "America/New_York"


def path_eff(p):
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    return float(abs(p.iloc[-1] - p.iloc[0]) / max(p.diff().abs().sum(), 1e-9))


def crosses(p):
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    s = np.sign(p - p.mean())
    return float((s.diff().abs() > 0).sum())


def load_depth_day(day):
    for folder in ("depth_2025", "depth_2026", "depth_apr2026"):
        p = Path(f"data/reference/{folder}/nq_depth_{day}_ny.csv")
        if p.exists():
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
            return d
    return None


def depth_at(dep, minute, entry, direction):
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1),
         "dep_spread": ask.price.min() - bid.price.max(),
         "dep_support": tb if direction == "long" else ta,
         "dep_resist": ta if direction == "long" else tb}
    f["dep_sup_m_res"] = f["dep_support"] - f["dep_resist"]
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry); f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price); f["dep_wall_below_sz"] = float(w["size"])
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
    return f


def main():
    S = pd.read_parquet("output/trade_angles.parquet")           # 970 trades + conf flags
    U = pd.read_parquet("output/universal_orderflow.parquet")[
        ["day", "book", "fill", "absorption", "delta_div", "stacked_imb"]]
    S = S.merge(U, on=["day", "book", "fill"], how="left")
    V2 = pd.read_parquet("output/substrate_v2_signals.parquet")[
        ["day", "book", "fill", "stop", "tf", "exit_price"]].drop_duplicates(["day", "book", "fill"])
    S = S.merge(V2, on=["day", "book", "fill"], how="left")
    S["risk"] = (S.entry - S.stop).abs()
    S["R"] = np.where(S.risk > 0, S.dollars / (S.risk * 20.0), np.nan)   # $20/pt NQ micro-adjusted scale
    S["fillhm"] = S.fillmi.dt.hour * 60 + S.fillmi.dt.minute
    S["win_"] = np.where(S.fillhm < 570, "pre", "gold")

    # ---- day-level SAFE (pre-08:00) context ----
    F = pd.read_parquet("output/dayflow_v2.parquet")
    safe = ["cvd_ON", "cvd_ASIA", "cvd_LON", "eff_ON", "eff_ASIA", "eff_LON", "on_range",
            "absz_cvd_ON", "rel_range", "rel_vol", "inventory_pts", "on_extreme_age",
            "on_eff_path", "yday_red", "red_streak", "gap_open_pts", "pos_800",
            "imbal_share_20", "trap_rate_10", "range_pctl_20", "pdc_loc", "dow"]
    S = S.drop(columns=[c for c in safe if c in S.columns])
    S = S.join(F[[c for c in safe if c in F]], on="day")

    # ---- minute tape, truncated at fill ----
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index); M = M.sort_index()
    M["cum"] = M.groupby("sday").delta.cumsum()
    M["runmin"] = M.groupby("sday").cum.cummin()
    M["runmax"] = M.groupby("sday").cum.cummax()
    daymed = M.groupby("sday").vol.median()
    bydayM = {d: g for d, g in M.groupby("sday")}

    # ---- bars + vwap bands for geometry ----
    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars = pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    ind = daily_vwap(bars, bands=[1, 2])
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(mi=bt.dt.floor("min"), sday=(bt + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"),
                       hm=bt.dt.hour * 60 + bt.dt.minute,
                       vw=ind["vwap"].values, lo1=ind["lower_1"].values, up1=ind["upper_1"].values,
                       lo2=ind["lower_2"].values, up2=ind["upper_2"].values)
    barmi = bars.set_index("mi")
    byday_bars = {d: g for d, g in bars.groupby("sday")}

    depth_cache = {}
    rows = []
    for i, t in enumerate(S.itertuples()):
        f = {}
        g = bydayM.get(t.day)
        if g is not None:
            upto = g[g.index < t.fillmi]
            pm = upto[(upto.hm >= 480)]
            op = upto[(upto.hm >= 570)]
            if len(pm):
                f["pm_sofar_cvd"] = pm.delta.sum(); f["pm_sofar_abscvd"] = abs(f["pm_sofar_cvd"])
                f["pm_sofar_eff"] = f["pm_sofar_cvd"] / max(pm.vol.sum(), 1)
                f["pm_sofar_crosses"] = crosses(pm.vwp); f["pm_sofar_patheff"] = path_eff(pm.vwp)
                f["pm_sofar_conf"] = int((f["pm_sofar_cvd"] > 0) == (t.direction == "long"))
            if len(op):
                f["op_sofar_cvd"] = op.delta.sum()
                f["op_sofar_eff"] = f["op_sofar_cvd"] / max(op.vol.sum(), 1)
                f["op_sofar_conf"] = int((f["op_sofar_cvd"] > 0) == (t.direction == "long"))
            for k in (5, 15, 30):
                w = upto[upto.index >= t.fillmi - pd.Timedelta(minutes=k)]
                f[f"d{k}"] = w.delta.sum() if len(w) else np.nan
                f[f"d{k}_conf"] = int((f[f"d{k}"] > 0) == (t.direction == "long")) if len(w) else np.nan
            if len(upto):
                last = upto.iloc[-1]
                rng = last.runmax - last.runmin
                f["pathpos"] = (last.cum - last.runmin) / rng if rng > 0 else np.nan
                f["fill_vol_rel"] = last.vol / max(daymed.get(t.day, np.nan), 1)
                f["fill_delta"] = last.delta
                f["fill_delta_conf"] = int((last.delta > 0) == (t.direction == "long"))
        bd = byday_bars.get(t.day)
        if bd is not None:
            pre = bd[bd.mi < t.fillmi]
            bar = pre.iloc[-1] if len(pre) else None
            if bar is not None and bar.vw == bar.vw:
                sgn = 1 if t.direction == "long" else -1
                bw = max(bar.up1 - bar.vw, 1e-9)
                f["ent_vs_vwap_sd"] = (t.entry - bar.vw) / bw          # entry in band-σ units
                f["ent_vs_vwap_sd_dir"] = sgn * f["ent_vs_vwap_sd"]     # + = entering above vwap for long
                onr = pre[(pre.hm >= 1080) | (pre.hm < 480)]
                if len(onr):
                    hi, lo = onr.high.max(), onr.low.min()
                    f["ent_on_pos"] = (t.entry - lo) / max(hi - lo, 1e-9)
                lon = pre[(pre.hm >= 120) & (pre.hm < 480)]
                if len(lon):
                    f["lon_hi_swept"] = int(pre[pre.hm >= 480].high.max() > lon.high.max()) if len(pre[pre.hm >= 480]) else 0
                    f["lon_lo_swept"] = int(pre[pre.hm >= 480].low.min() < lon.low.min()) if len(pre[pre.hm >= 480]) else 0
        if t.day not in depth_cache:
            depth_cache[t.day] = load_depth_day(t.day)
        if depth_cache[t.day] is not None:
            f.update(depth_at(depth_cache[t.day], t.fillmi, t.entry, t.direction))
        rows.append(f)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(S)}", flush=True)

    X = pd.DataFrame(rows, index=S.index)
    out = pd.concat([S, X], axis=1)
    out.to_parquet("output/trade_matrix.parquet")
    ncols = out.shape[1]
    print(f"wrote output/trade_matrix.parquet: {len(out)} trades x {ncols} cols")
    print(f"depth coverage: {out.get('dep_thick', pd.Series(dtype=float)).notna().sum()}/{len(out)}")


if __name__ == "__main__":
    main()
