#!/usr/bin/env python3
"""Opening-character features for the INTRADAY READER (docs/SPEC-intraday-reader.md).
Two read windows from the 1m master, all strictly intraday-but-early:
  Read A  08:00-08:45 ET  (pre-market character)
  Read B  09:30-09:45 ET  (the CASH OPEN -- the key read, Angus)

This is the FREE mechanical validation: do opening-character features separate the
both-books-lose days (chop) from good days -- especially the ~62% of chop days that
pre-open features MISS? Grade net dollars per year, 2026-safe, walk-forward + frozen OOS.

    python -m scripts.build_opening_features   -> output/opening_features.csv + validation
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
MASTER = "data/reference/nq_1m_master.parquet"


def window_feats(bars, prefix):
    """Character of one read window."""
    if len(bars) < 3:
        return {}
    hi, lo = bars.high.max(), bars.low.min()
    rng = hi - lo
    o, c = bars.iloc[0].open, bars.iloc[-1].close
    # trap: did the first-third make an extreme that later reversed back through >60% of range?
    third = max(2, len(bars) // 3)
    fh, fl = bars.iloc[:third].high.max(), bars.iloc[:third].low.min()
    up_first = (fh - o) > (o - fl)
    if rng > 0:
        retr = (fh - c) / rng if up_first else (c - fl) / rng
    else:
        retr = 0.0
    return {
        f"{prefix}_range": round(rng, 2),
        f"{prefix}_persist": round(abs(c - o) / rng, 3) if rng > 0 else 0.0,  # drive vs chop
        f"{prefix}_loc": round((c - lo) / rng, 3) if rng > 0 else 0.5,        # close within range
        f"{prefix}_trap": round(retr, 3),                                     # early extreme reversed
        f"{prefix}_vol": int(bars.volume.sum()),
        f"{prefix}_dir": int(np.sign(c - o)),
    }


def main():
    df = pd.read_parquet(MASTER)
    df["d"] = df.ts_event.dt.strftime("%Y-%m-%d")
    df["t"] = df.ts_event.dt.time
    rows = []
    for day, g in df.groupby("d"):
        A = g[(g.t >= dtime(8, 0)) & (g.t < dtime(8, 45))]
        B = g[(g.t >= dtime(9, 30)) & (g.t < dtime(9, 45))]
        pre = g[(g.t >= dtime(8, 0)) & (g.t < dtime(9, 30))]
        rec = {"day": day}
        rec.update(window_feats(A, "a"))
        rec.update(window_feats(B, "b"))
        # cross-read: did the cash open confirm or reject the pre-market lean?
        if len(B) >= 3 and len(pre) >= 5:
            pre_dir = np.sign(pre.iloc[-1].close - pre.iloc[0].open)
            b_dir = np.sign(B.iloc[-1].close - B.iloc[0].open)
            rec["open_confirms_pre"] = int(pre_dir == b_dir and pre_dir != 0)
        rows.append(rec)
    out = pd.DataFrame(rows)

    # trailing-normalize range & volume (walk-forward: prior-20d median)
    for p in ["a", "b"]:
        for k in ["range", "vol"]:
            col = f"{p}_{k}"
            if col in out:
                med = out[col].rolling(20, min_periods=10).median().shift(1)
                out[f"{col}_rel"] = (out[col] / med).round(3)
    out.to_csv("output/opening_features.csv", index=False)
    print(f"wrote output/opening_features.csv ({len(out)} days, "
          f"{out.columns.size} cols)")

    # ---- VALIDATION: do opening features predict both-lose / champ P&L sign? ----
    b = pd.read_csv("output/allyears_daily_books_r1r2.csv")
    v = pd.read_csv("output/regime_vector.csv")[["day", "imbal_share_20", "inventory_pts"]]
    d = b.merge(v, on="day", how="left").merge(out, on="day", how="left").sort_values("day").reset_index(drop=True)
    d["champ_pl"] = np.where(d.imbal_share_20 >= 0.5, d.E4, d.E3)
    d["y"] = d.day.str[:4]
    d["both_lose"] = ((d.E3 <= 0) & (d.E4 <= 0)).astype(int)

    # simple, interpretable chop tells from the OPEN (Read B):
    #  - weak persistence (oscillation not drive)  - low relative range early then... etc.
    # walk-forward conditional-expectancy gate on a candidate feature
    def wf_gate(col, min_n=20, fb=60):
        vals = d[col].values
        cpl = d.champ_pl.values
        flat = np.zeros(len(d), bool)
        for i in range(len(d)):
            x = vals[i]
            if pd.isna(x) or i < 40:
                prior = cpl[max(0, i - fb):i]
            else:
                past = vals[:i]
                ok = ~np.isnan(past)
                q1, q2 = np.nanquantile(past[ok], [1/3, 2/3])
                m = past <= q1 if x <= q1 else ((past > q1) & (past <= q2) if x <= q2 else past > q2)
                pb = cpl[:i][ok & m] if False else cpl[:i][np.where(ok, m, False)]
                prior = pb if len(pb) >= min_n else cpl[max(0, i - fb):i]
            prior = prior[~np.isnan(prior)]
            flat[i] = bool(len(prior) >= 10 and prior.mean() < 0)
        return flat

    def report(flat, label):
        pl = np.where(flat, 0.0, d.champ_pl.values)
        s = {y: g.pl.sum() for y, g in pd.DataFrame({"y": d.y, "pl": pl}).groupby("y")}
        print(f"{label:26s} " + "  ".join(f"{y}:${s.get(y,0):+7,.0f}" for y in ["2023","2024","2025","2026"]) + f"  ALL ${sum(pl):+,.0f}")

    print("\n=== intraday-reader signal test (champion book, opening-character gates) ===")
    report(np.zeros(len(d), bool), "always trade")
    for col in ["b_persist", "b_trap", "b_loc", "b_range_rel", "a_persist", "b_vol_rel"]:
        if col in d:
            report(wf_gate(col), f"gate: {col}")

    # the KEY measure: of both-lose days pre-open MISSED, does the open catch them?
    # pre-open miss proxy: both_lose day where inventory bucket wasn't flagged (approx via inv sign)
    d["open_chop"] = ((d.b_persist < 0.35) | (d.b_trap > 0.6)).fillna(False)  # weak drive or trap at open
    bl = d[d.both_lose == 1]
    print(f"\nboth-lose days: {len(bl)} | open_chop flags {bl.open_chop.mean()*100:.0f}% of them")
    good = d[d.champ_pl > 0]
    print(f"good (champ>0) days: {len(good)} | open_chop false-flags {good.open_chop.mean()*100:.0f}% of them")
    print("(separation = both-lose flag rate MINUS good-day flag rate; >0 and wide = real signal)")


if __name__ == "__main__":
    main()
