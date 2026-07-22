#!/usr/bin/env python3
"""Day-flow feature library (Angus 23-Jul, autonomous deep-dive).

One row per labeled day (Jun-2025 -> Jul-2026, footprint-covered), every CVD/order-flow
variable we can compute per session window, joined to the day labels from the committed
daily books (oracle_sd / both_red / which-book-was-better). This is the substrate for the
out-of-fit screen: which information, known BEFORE or AT the open, predicts what kind of
day it is.

Windows (NY): ON = prev 18:00->08:00, ASIA = 18:00->02:00, LON = 02:00->08:00,
              PM = 08:00->09:30, OP = 09:30->09:50 (post-open read).

    python -m scripts.dayflow_features
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
NY = "America/New_York"
FP_FILES = ["footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
            "footprint_apr2026", "footprint_may_jul2026"]


def minute_table():
    """Per-minute b/a/vol/delta/vwprice across all footprint files, with session_day."""
    frames = []
    for f in FP_FILES:
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"])
        ny = d.ts_minute.dt.tz_convert(NY)
        d = pd.DataFrame({"mi": ny.dt.floor("min"), "price": d.price.values,
                          "side": d.side.values, "volume": d.volume.values})
        d["pv"] = d.price * d.volume
        g = d.groupby(["mi", "side"]).agg(vol=("volume", "sum"), pv=("pv", "sum"))
        g = g.unstack("side").fillna(0.0)
        m = pd.DataFrame({"b": g[("vol", "B")] if ("vol", "B") in g else 0.0,
                          "a": g[("vol", "A")] if ("vol", "A") in g else 0.0,
                          "pv": g[("pv", "B")].add(g[("pv", "A")], fill_value=0.0)})
        m["vol"] = m.b + m.a
        m["delta"] = m.b - m.a
        m["vwp"] = m.pv / m.vol.replace(0, np.nan)
        frames.append(m.drop(columns="pv"))
        print(f"  {f}: {len(m)} minutes", flush=True)
    M = pd.concat(frames).sort_index()
    M = M[~M.index.duplicated(keep="first")]
    idx = M.index
    M["sday"] = (idx + pd.Timedelta(hours=6)).strftime("%Y-%m-%d")
    hm = idx.hour * 60 + idx.minute
    M["hm"] = hm
    return M


def win_masks(hm):
    return {"ON":  (hm >= 18 * 60) | (hm < 8 * 60),
            "ASIA": (hm >= 18 * 60) | (hm < 2 * 60),
            "LON": (hm >= 2 * 60) & (hm < 8 * 60),
            "PM":  (hm >= 8 * 60) & (hm < 9 * 60 + 30),
            "OP":  (hm >= 9 * 60 + 30) & (hm < 9 * 60 + 50)}


def r2_of_cum(x):
    if len(x) < 10:
        return np.nan
    c = np.cumsum(x); t = np.arange(len(c))
    if c.std() == 0:
        return 0.0
    return float(np.corrcoef(t, c)[0, 1] ** 2)


def load_bars():
    m = pd.read_parquet("data/reference/nq_1m_master.parquet")
    m = m[m.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    f = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    df = pd.concat([m, f], ignore_index=True).drop_duplicates("ts_event").sort_values("ts_event")
    return df.reset_index(drop=True)


def main():
    print("building minute table ...", flush=True)
    M = minute_table()
    masks = win_masks(M.hm)

    print("bars + vwap bands ...", flush=True)
    bars = load_bars()
    ind = daily_vwap(bars, bands=[1, 2, 3])
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(sday=(bt + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"),
                       hm=bt.dt.hour * 60 + bt.dt.minute,
                       lo2=ind["lower_2"].values, up2=ind["upper_2"].values)

    rows = {}
    for w, mk in masks.items():
        sub = M[mk]
        g = sub.groupby("sday")
        agg = pd.DataFrame({f"cvd_{w}": g.delta.sum(), f"vol_{w}": g.vol.sum()})
        agg[f"eff_{w}"] = agg[f"cvd_{w}"] / agg[f"vol_{w}"].replace(0, np.nan)
        rows[w] = agg
        if w == "PM":
            rows["r2"] = pd.DataFrame({"cvd_r2_PM": g.delta.apply(lambda x: r2_of_cum(x.values))})
            med = g.vol.median().rename("medvol")
            j = sub.join(med, on="sday")
            hot = j[j.vol >= 2.0 * j.medvol]
            two = hot[np.minimum(hot.b, hot.a) / np.maximum(np.maximum(hot.b, hot.a), 1) >= 0.65]
            one = hot[np.minimum(hot.b, hot.a) / np.maximum(np.maximum(hot.b, hot.a), 1) <= 0.25]
            rows["absorb"] = pd.DataFrame({
                "absorb_ct_PM": two.groupby("sday").size(),
                "burst_ct_PM": one.groupby("sday").size(),
                "burst_net_PM": one.groupby("sday").delta.sum(),
                "maxmin_delta_PM": sub.groupby("sday").delta.apply(lambda x: float(np.abs(x).max()))})

    F = pd.concat(rows.values(), axis=1)

    # price-change + edge deltas per window (bar-based ranges, minute-vwp deltas at edges)
    print("edge/price features ...", flush=True)
    px = {}
    for w, lo_hm, hi_hm in [("ON", 18 * 60, 8 * 60), ("PM", 8 * 60, 9 * 60 + 30), ("OP", 9 * 60 + 30, 9 * 60 + 50)]:
        if w == "ON":
            bm = (bars.hm >= lo_hm) | (bars.hm < hi_hm)
        else:
            bm = (bars.hm >= lo_hm) & (bars.hm < hi_hm)
        bw = bars[bm].groupby("sday").agg(hi=("high", "max"), lo=("low", "min"),
                                          o=("open", "first"), c=("close", "last"))
        px[w] = bw
    # ON edge deltas: minutes whose vw-price sits in top/bottom quartile of ON range
    on = M[masks["ON"]].join(px["ON"][["hi", "lo"]], on="sday")
    rng = (on.hi - on.lo).replace(0, np.nan)
    top = on[on.vwp >= on.lo + 0.75 * rng]; bot = on[on.vwp <= on.lo + 0.25 * rng]
    F["edge_top_delta_ON"] = top.groupby("sday").delta.sum()
    F["edge_bot_delta_ON"] = bot.groupby("sday").delta.sum()

    F["px_chg_ON"] = px["ON"].c - px["ON"].o
    F["px_chg_PM"] = px["PM"].c - px["PM"].o
    F["px_chg_OP"] = px["OP"].c - px["OP"].o
    F["on_range"] = px["ON"].hi - px["ON"].lo
    F["pos_800"] = (px["PM"].o - px["ON"].lo) / (px["ON"].hi - px["ON"].lo).replace(0, np.nan)
    # divergence: price move vs cvd disagreement, signed magnitude products
    F["div_ON"] = -np.sign(F.px_chg_ON) * np.sign(F.cvd_ON) * (F.px_chg_ON.abs() > 20) * 1.0
    F["div_PM"] = -np.sign(F.px_chg_PM) * np.sign(F.cvd_PM) * (F.px_chg_PM.abs() > 10) * 1.0
    F["flip_PM_ON"] = (np.sign(F.cvd_PM) != np.sign(F.cvd_ON)) * 1.0
    F["cvd_accel_PM"] = F.eff_PM - F.eff_ON

    # London sweep during PM + vwap ±2 touch during PM (bar-based)
    lon = bars[(bars.hm >= 2 * 60) & (bars.hm < 8 * 60)].groupby("sday").agg(lh=("high", "max"), ll=("low", "min"))
    pm = bars[(bars.hm >= 8 * 60) & (bars.hm < 9 * 60 + 30)]
    pm = pm.join(lon, on="sday")
    sw = pm.groupby("sday").apply(lambda d: pd.Series({
        "sweep_lh_PM": float((d.high > d.lh).any()), "sweep_ll_PM": float((d.low < d.ll).any())}),
        include_groups=False)
    F = F.join(sw)
    t2 = pm.groupby("sday").apply(lambda d: pd.Series({
        "vwap2_lo_PM": float((d.low <= d.lo2 + 0.5).any()), "vwap2_up_PM": float((d.high >= d.up2 - 0.5).any())}),
        include_groups=False)
    F = F.join(t2)

    # joins: regime vector + AMT value-area context + labels
    V = pd.read_csv("output/regime_vector.csv").set_index("day")
    A = pd.read_csv("output/amt_daytypes.csv").set_index("day")
    B = pd.read_csv("output/allyears_daily_books_r1r2.csv").set_index("day")
    F = F.join(V[["imbal_share_20", "imbal_share_10", "trap_rate_10", "range_pctl_20",
                  "gap_open_pts", "inventory_pts", "on_nr_rank", "pdc_loc"]], how="left")
    if "overlap" in A:
        F = F.join(A[["overlap", "value_position"]].rename(columns={"value_position": "val_pos"}), how="left")
    F = F.join(B[["E3", "E4", "oracle_sd"]], how="inner")
    F["both_red"] = (F[["E3", "E4"]].max(axis=1) <= 0).astype(int)
    F["book_label"] = np.where(F.E4 > F.E3, "E4", "E3")
    F["yr"] = F.index.str[:4].astype(int)
    F.index.name = "day"
    F.to_parquet("output/dayflow_features.parquet")
    print(f"\nwrote output/dayflow_features.parquet: {len(F)} days x {F.shape[1]} cols "
          f"(2025 {int((F.yr==2025).sum())}, 2026 {int((F.yr==2026).sum())})")
    print("features:", [c for c in F.columns if c not in ("E3", "E4", "oracle_sd", "both_red", "book_label", "yr")])


if __name__ == "__main__":
    main()
