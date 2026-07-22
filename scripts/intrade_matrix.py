#!/usr/bin/env python3
"""IN-TRADE order-flow matrix (Angus 25-Jul: 'what does the flow say once we're IN the trade').

One row per trade (both-books universe, risk 7-60, with exit data). At horizons h = 3/5/10
minutes AFTER the fill (only trades still alive at h; only data from (fill, fill+h]):

  flow    : fw_h  net delta signed WITH the position; fa_frac_h fraction of minutes adverse;
            adv_press_h  delta while price below/behind entry (pressing at adverse prices);
            absorb_h  price adverse but delta WITH us (absorption = holders defending)
  price   : r_h  position P&L in R at h; maeR_h  worst adverse so far in R;
            eff_h  path efficiency since fill
  volume  : relvol_h  per-minute vol since fill vs day median
  depth   : dthick_h  book thickness change vs fill; dimb_h  direction-signed imbalance shift;
            wallb_h  depth appeared BEHIND the position since fill (crowd underneath = trapped?)
  outcome : win, dollars, pl (canon), R, hold_min, in_canon

    python -m scripts.intrade_matrix
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.trade_matrix import load_depth_day
NY = "America/New_York"
HOR = [3, 5, 10]


def main():
    TM = pd.read_parquet("output/trade_matrix.parquet")
    TM = TM[(TM.risk >= 7) & (TM.risk <= 60)].copy()
    X = pd.read_parquet("output/substrate_v2_signals.parquet")[
        ["day", "book", "fill", "exit"]].drop_duplicates(["day", "book", "fill"])
    TM = TM.merge(X, on=["day", "book", "fill"], how="left").dropna(subset=["exit"])
    canon = pd.read_parquet("output/canon_book.parquet")
    ck = set(map(tuple, canon[canon["size"] > 0][["day", "book", "fill"]].values))
    TM["in_canon"] = [tuple(x) in ck for x in TM[["day", "book", "fill"]].values]

    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()
    daymed = M.groupby("sday").vol.median()

    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars = pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event").sort_values("ts_event")
    bars["mi"] = bars.ts_event.dt.tz_convert(NY)
    B = bars.set_index("mi")[["high", "low", "close"]].sort_index()

    dep_cache = {}
    rows = []
    for i, t in enumerate(TM.itertuples()):
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        e = pd.Timestamp(t.exit).tz_convert(NY)
        sgn = 1 if t.direction == "long" else -1
        hold = (e - f).total_seconds() / 60
        out = {"hold_min": hold}
        day = t.day
        if day not in dep_cache:
            dep_cache[day] = load_depth_day(day)
        dep = dep_cache[day]
        dep0 = None
        if dep is not None:
            s0 = dep[dep.ts <= f]
            dep0 = s0[s0.ts == s0.ts.max()] if len(s0) else None
        for h in HOR:
            if hold < h:
                continue
            hi = f + pd.Timedelta(minutes=h)
            seg = M.loc[f + pd.Timedelta(minutes=1): hi]
            pseg = B.loc[f: hi]
            if len(seg) < 2 or len(pseg) < 2:
                continue
            d_dir = seg.delta.values * sgn
            out[f"fw_{h}"] = d_dir.sum()
            out[f"fa_frac_{h}"] = float((d_dir < 0).mean())
            px = pseg.close.iloc[-1]
            out[f"r_{h}"] = (px - t.entry) * sgn / t.risk
            mae = (t.entry - pseg.low.min()) if sgn == 1 else (pseg.high.max() - t.entry)
            out[f"maeR_{h}"] = max(mae, 0) / t.risk
            # flow at adverse prices: minutes whose vwp is behind entry
            adv = seg[(seg.vwp - t.entry) * sgn < 0]
            out[f"adv_press_{h}"] = float((adv.delta * sgn).sum()) if len(adv) else 0.0
            out[f"absorb_{h}"] = int(out[f"r_{h}"] < 0 and out[f"fw_{h}"] > 0)
            net = abs(pseg.close.iloc[-1] - pseg.close.iloc[0])
            path = pseg.close.diff().abs().sum()
            out[f"eff_{h}"] = net / max(path, 1e-9)
            out[f"relvol_{h}"] = seg.vol.mean() / max(daymed.get(day, np.nan), 1)
            if dep is not None and dep0 is not None and len(dep0):
                sh = dep[dep.ts <= hi]
                deph = sh[sh.ts == sh.ts.max()] if len(sh) else None
                if deph is not None and len(deph):
                    out[f"dthick_{h}"] = deph["size"].sum() - dep0["size"].sum()
                    def imb(b_):
                        bid = b_[b_.side == "bid"]["size"].sum(); ask = b_[b_.side == "ask"]["size"].sum()
                        return (bid - ask) / max(bid + ask, 1) * sgn
                    out[f"dimb_{h}"] = imb(deph) - imb(dep0)
                    behind0 = (dep0.price < t.entry).any() if sgn == 1 else (dep0.price > t.entry).any()
                    behindh = (deph.price < t.entry).any() if sgn == 1 else (deph.price > t.entry).any()
                    out[f"wallb_{h}"] = int((not behind0) and behindh)
        rows.append(out)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(TM)}", flush=True)

    F = pd.DataFrame(rows, index=TM.index)
    out = pd.concat([TM[["day", "book", "fill", "direction", "entry", "stop", "risk", "dollars",
                         "pattern", "yr", "win_", "in_canon"]], F], axis=1)
    out["win"] = out.dollars > 0
    out["R"] = out.dollars / (out.risk * 20)
    out["mo"] = out.day.str[:7]
    out.to_parquet("output/intrade_matrix.parquet")
    print(f"wrote output/intrade_matrix.parquet: {len(out)} trades "
          f"(alive@3m {out.fw_3.notna().sum()}, @5m {out.fw_5.notna().sum()}, @10m {out.fw_10.notna().sum()}; "
          f"canon {int(out.in_canon.sum())})")


if __name__ == "__main__":
    main()
