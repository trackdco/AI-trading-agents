#!/usr/bin/env python3
"""April, fixed engine, champion triggers (E3 non-WAR + E4 WAR), max 2/day, in two windows:
09:45-10:15 and 10:15-11:00. Grade each trade with CVD confirm/divergence (exhaustion) and
heatmap absorption. No invented entries, no tuned thresholds (MAG=15 >> p95~8, as before)."""
import ast, sys, glob
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY = "America/New_York"
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
MAG, DIST = 15, 6

# per-minute price + CVD delta (NY tz)
b = pd.read_parquet(DATA); b["ts"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
bidx = b.set_index("ts")[["high", "low", "close"]].sort_index()
fp = pd.concat([pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
                for f in glob.glob("data/reference/cvd/footprint_*2026.parquet")])
fp["ts"] = pd.to_datetime(fp.ts_minute, utc=True).dt.tz_convert(NY)
delta = fp.assign(sg=np.where(fp.side == "B", fp.volume, -fp.volume)).groupby("ts").sg.sum().sort_index()
_depth = {}


def depth_snap(day, t):
    if day not in _depth:
        try:
            d = pd.read_csv(f"data/reference/depth_apr2026/nq_depth_{day}_ny.csv")
            d["ts"] = pd.to_datetime(d.ts)
            _depth[day] = d
        except Exception:
            _depth[day] = None
    d = _depth[day]
    return None if d is None else d[d.ts == t]


def cvd_pre(t, mins=3):
    w = delta.loc[t - pd.Timedelta(minutes=mins): t - pd.Timedelta(minutes=1)]
    return float(w.sum()) if len(w) else np.nan


def exhaustion(t, direction, win=5):
    seg = delta.loc[t - pd.Timedelta(minutes=win): t - pd.Timedelta(minutes=1)]
    p = bidx.loc[t - pd.Timedelta(minutes=win): t - pd.Timedelta(minutes=1)]
    if len(seg) < 3 or len(p) < 3:
        return False
    cum = seg.cumsum()
    if direction == "short":                            # fading up-move: higher high, lower CVD high
        j = p.high.values.argmax(); pre = p.high.values[:j]
        if not len(pre): return False
        k = pre.argmax()
        return p.high.values[j] > p.high.values[k] and cum.iloc[j] < cum.iloc[k]
    j = p.low.values.argmin(); pre = p.low.values[:j]
    if not len(pre): return False
    k = pre.argmin()
    return p.low.values[j] < p.low.values[k] and cum.iloc[j] > cum.iloc[k]


def absorption(day, t, entry, direction, cp):
    snap = depth_snap(day, t)
    if snap is None or not len(snap) or np.isnan(cp):
        return None
    if direction == "long":
        wall = snap[(snap.side == "bid") & (entry - snap.price >= 0) & (entry - snap.price <= DIST)]["size"]
        return (float(wall.max()) if len(wall) else 0.0, bool(len(wall) and wall.max() >= MAG and cp < 0))
    wall = snap[(snap.side == "ask") & (snap.price - entry >= 0) & (snap.price - entry <= DIST)]["size"]
    return (float(wall.max()) if len(wall) else 0.0, bool(len(wall) and wall.max() >= MAG and cp > 0))


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types"); r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def run_window(ws, we):
    allt = [t for t in load_triggers() if t.ts[:7] == "2026-04"]
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    end = pd.Timestamp("2026-05-01", tz=NY); seg = b[b.ts <= end].reset_index(drop=True)
    base = load_backtest_config().model_copy(update={"win_start": ws, "win_end": we, "max_trades_per_day": 2})
    E3 = base.model_copy(update={"mgmt_variant": "V8"}); E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for tt, cfg in (([t for t in allt if t.ts[:10] not in war], E3),
                    ([t for t in allt if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0], E4)):
        for x in simulate(seg, tt, cfg)[0]:
            t = pd.Timestamp(x.fill_ts).tz_convert(NY)
            cp = cvd_pre(t)
            ab = absorption(x.trade_date, t, x.entry, x.direction, cp)
            rows.append(dict(date=x.trade_date, t=t.strftime("%H:%M"), dir=x.direction,
                             r=round(x.r_multiple, 2), d=x.dollars, reason=x.exit_reason,
                             cvd_confirm=(cp > 0) if not np.isnan(cp) else None,
                             exhaust=exhaustion(t, x.direction),
                             wall=None if ab is None else round(ab[0], 1),
                             absorb=None if ab is None else ab[1]))
    return pd.DataFrame(rows)


for lab, (ws, we) in [("09:45-10:15", (dtime(9, 45), dtime(10, 15))),
                      ("10:15-11:00", (dtime(10, 15), dtime(11, 0)))]:
    J = run_window(ws, we)
    print(f"\n===== APRIL {lab} — champion trades (max 2/day, fixed engine) =====")
    if not len(J):
        print("  no trades"); continue
    print(J.to_string(index=False))
    w = (J.r > 0).mean() * 100
    print(f"  ALL: {len(J)}t  win {w:.0f}%  ${J.d.sum():+,.0f}  R {J.r.sum():+.1f}  exp {J.r.mean():+.3f}")
    for name, m in [("CVD-confirm", J.cvd_confirm == True), ("exhaustion", J.exhaust == True),
                    ("absorption(heatmap)", J.absorb == True)]:
        s = J[m]
        print(f"    {name:20s} {len(s):2d}t" + (f"  win {(s.r>0).mean()*100:.0f}%  R {s.r.sum():+.1f}" if len(s) else ""))
    print(f"    max resting wall seen on rejection side: {J.wall.dropna().max() if J.wall.notna().any() else 'n/a'} "
          f"(MAG threshold {MAG})")
