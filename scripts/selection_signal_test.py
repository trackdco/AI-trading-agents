#!/usr/bin/env python3
"""SELECTION SIGNAL TEST (data-lane, 20 Jul 2026) — reproduces the winner/loser findings.
Which entry-known signals separate champion winners from losers? Runs on the committed
journal + CVD footprint + April depth. Read docs/HANDOFF-datalane-session.md for context.

    python scripts/selection_signal_test.py
"""
import glob
import numpy as np, pandas as pd

NY = "America/New_York"


def load():
    J = pd.read_csv("output/journal_champion.csv"); J["day"] = J["day"].astype(str)
    J["entry_utc"] = J.apply(lambda r: pd.Timestamp(f"{r['day']} {r['fill']}", tz=NY)
                             .tz_convert("UTC").floor("min"), axis=1)
    J["entry_et"] = J["entry_utc"].dt.tz_convert(NY)
    J["R"] = J.points / J.risk_pts
    # CVD confirmation: net-buy over the 3-min pre-entry window, oriented to trade direction
    fp = pd.concat([pd.read_parquet(f) for f in glob.glob("data/reference/cvd/footprint_*2026.parquet")],
                   ignore_index=True)
    g = fp.groupby(["ts_minute", "side"])["volume"].sum().unstack(fill_value=0)
    nb = (g.get("B", 0) - g.get("A", 0))

    def w3(t):
        w = nb.loc[t - pd.Timedelta(minutes=3): t - pd.Timedelta(minutes=1)]
        return float(w.sum()) if len(w) else np.nan
    J["cvd_confirm"] = J["entry_utc"].map(w3) * J["dir"].map({"long": 1, "short": -1}) > 0
    J["real_stop"] = J.risk_pts >= 6
    return J


def add_magnet(apr):
    """Heatmap LIQUIDITY MAGNET: resting size on the TARGET side (wall price travels toward).
    This is the framing that separates — NOT support behind entry (which does nothing)."""
    dc = {}

    def barrier(r):
        d = dc.get(r["day"], "miss")
        if d == "miss":
            try:
                d = pd.read_csv(f"data/reference/depth_apr2026/nq_depth_{r['day']}_ny.csv")
                d["ts"] = pd.to_datetime(d["ts"])
            except Exception:
                d = None
            dc[r["day"]] = d
        if d is None:
            return np.nan
        m = d[d["ts"] == r["entry_et"]]
        if not len(m):
            return np.nan
        e = r["entry"]
        return (m[(m.side == "ask") & (m.price >= e)]["size"].sum() if r["dir"] == "long"
                else m[(m.side == "bid") & (m.price <= e)]["size"].sum())
    apr = apr.copy()
    apr["barrier"] = apr.apply(barrier, axis=1)
    apr["magnet"] = apr["barrier"] >= apr["barrier"].median()
    return apr


def rep(v, name):
    if not len(v):
        print(f"  {name:34s}  0t"); return
    print(f"  {name:34s} {len(v):3d}t  win {v.win.mean()*100:2.0f}%  ${v.dollars.sum():+7,.0f}  {v.R.mean():+.2f}R")


if __name__ == "__main__":
    J = load()
    print(f"FULL Feb-Jul 2026 champion (n={len(J)}):")
    rep(J, "baseline")
    rep(J[J.cvd_confirm], "CVD confirm")
    rep(J[J.real_stop], "real stop >=6pt")
    rep(J[J.cvd_confirm & J.real_stop], "CVD confirm + real stop")
    apr = add_magnet(J[J.day.str.startswith("2026-04")])
    print(f"\nAPRIL 2026 only (has depth, n={len(apr)}):")
    rep(apr, "baseline")
    rep(apr[apr.magnet], "magnet (wall on target side)")
    rep(apr[apr.cvd_confirm], "CVD confirm")
    rep(apr[apr.magnet & apr.cvd_confirm], "magnet + CVD  <-- 60% lead (n=10)")
    print("\nNOTE: magnet+CVD=60% is n=10, April-only, in-sample. LEAD not PROOF. Confirm on more depth months.")
