#!/usr/bin/env python3
"""ENRICHED AGENT SIGNAL BLOCK (Angus 22 Jul). The fresh-eyes agent judged the day BLIND to
order flow -- no CVD, no developing profile, no book state. This assembles those into the
daily read the agent gets, using only the validated signals: pre-market CVD conviction (the
one that held out-of-fit), the DEVELOPING (live) volume profile + value migration, and the
book coil state. Usage-free -- this is the INPUT the agent consumes, not an LLM call.

    python -m scripts.agent_signal_block 2025-09-15 2026-06-12   (or no args -> samples)
"""
import glob
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import volume_profile                       # noqa: E402

NY = "America/New_York"


def load_cvd():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        d["s"] = np.where(d.side == "B", d.volume, -d.volume)
        fr.append(d.groupby("ts_minute")["s"].sum())
    if not fr:
        return pd.Series(dtype=float)
    g = pd.concat(fr).groupby(level=0).sum()
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def _lab(x, edges, labs):
    for e, l in zip(edges, labs):
        if x <= e:
            return l
    return labs[-1]


def block(day, df, cvd, depth_idx):
    g = df[df.ny.dt.strftime("%Y-%m-%d") == day]
    if g.empty:
        return None
    hm = g.ny.dt.hour * 60 + g.ny.dt.minute
    out = {"day": day}

    # --- pre-market CVD conviction (the one validated stand-down signal) ---
    if len(cvd):
        pre = float(cvd[(cvd.index >= pd.Timestamp(f"{day} 08:00", tz=NY)) &
                        (cvd.index < pd.Timestamp(f"{day} 09:30", tz=NY))].sum())
        drive = float(cvd[(cvd.index >= pd.Timestamp(f"{day} 09:30", tz=NY)) &
                          (cvd.index < pd.Timestamp(f"{day} 09:40", tz=NY))].sum())
        out["cvd_premkt"] = round(pre)
        out["cvd_conviction"] = _lab(pre, [-2000, -500, 500, 2000],
                                     ["heavy SELL", "sell lean", "NEUTRAL / no conviction", "buy lean", "heavy BUY"])
        out["cvd_open_drive"] = round(drive)
    # --- DEVELOPING (live) volume profile + value migration ---
    rth = g[hm >= 9 * 60 + 30]
    p945 = rth[hm[rth.index] < 9 * 60 + 45] if len(rth) else rth
    def prof(s):
        try:
            return volume_profile(s[["ts_event", "high", "low", "volume"]], 0.25, 70)
        except Exception:
            return None
    P1015 = prof(rth[hm[rth.index] < 10 * 60 + 15]) if len(rth) else None
    P945 = prof(p945) if len(p945) else None
    if P1015 is not None:
        price = rth[hm[rth.index] < 10 * 60 + 15].close.iloc[-1]
        out["dev_poc"] = round(P1015.poc, 1)
        out["dev_vah"] = round(P1015.vah, 1)
        out["dev_val"] = round(P1015.val, 1)
        out["price_vs_value"] = ("ABOVE value (accepting higher)" if price > P1015.vah
                                 else "BELOW value (accepting lower)" if price < P1015.val
                                 else "inside value (balanced)")
        out["price_vs_poc"] = round(price - P1015.poc, 1)
        if P945 is not None:
            mig = P1015.poc - P945.poc
            out["value_migration"] = ("value migrating UP (bullish development)" if mig > 3
                                      else "value migrating DOWN (bearish)" if mig < -3 else "value flat (balancing)")
        out["va_width"] = round(P1015.vah - P1015.val, 1)
        out["structure_lean"] = ("WIDE range / extension -> trend-day lean (momentum)"
                                 if (P1015.vah - P1015.val) > 40 else
                                 "NARROW value / balance-day lean (rotation or stand-down)")
    # --- book / heatmap coil state ---
    p = depth_idx.get(day)
    if p:
        d = pd.read_csv(p, parse_dates=["ts"])
        w = d[(d.ts.dt.hour * 60 + d.ts.dt.minute).between(9 * 60 + 30, 9 * 60 + 39)]
        if len(w):
            per = w.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
            if "bid" in per and "ask" in per:
                bid, ask = per["bid"].mean(), per["ask"].mean()
                bal = float(min(bid, ask) / max(max(bid, ask), 1))
                out["book_state"] = ("COILED / balanced (chop risk -> stand-down lean)" if bal > 0.8
                                     else "one-sided book (directional lean)")
                out["book_imbalance"] = round((bid - ask) / (bid + ask), 2)
    return out


def render(b):
    print(f"\n===== DESK READ — {b['day']} =====")
    print("ORDER FLOW (CVD):")
    print(f"  pre-market conviction : {b.get('cvd_conviction', 'n/a')}  ({b.get('cvd_premkt','?')} net)")
    print(f"  open drive (9:30-9:40): {b.get('cvd_open_drive','n/a')}")
    print("AUCTION (developing profile, live @ 10:15):")
    print(f"  POC {b.get('dev_poc','?')}  VA [{b.get('dev_val','?')} - {b.get('dev_vah','?')}]  width {b.get('va_width','?')}pt")
    print(f"  price vs value        : {b.get('price_vs_value','n/a')}")
    print(f"  price vs POC          : {b.get('price_vs_poc','n/a')}pt")
    print(f"  value migration       : {b.get('value_migration','n/a')}")
    print(f"  structure lean        : {b.get('structure_lean','n/a')}")
    print("BOOK (heatmap):")
    print(f"  state                 : {b.get('book_state','n/a')}  (imbal {b.get('book_imbalance','n/a')})")


def main():
    days = sys.argv[1:] or ["2025-09-15", "2025-11-19", "2026-06-12", "2026-02-25"]
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(ny=df.ts_event.dt.tz_convert(NY))
    cvd = load_cvd()
    depth_idx = {Path(f).stem.split("_")[2]: f for f in
                 glob.glob("data/reference/depth_2025/*.csv") + glob.glob("data/reference/depth_2026/*.csv")}
    for day in days:
        b = block(day, df, cvd, depth_idx)
        if b:
            render(b)
        else:
            print(f"\n{day}: no data")


if __name__ == "__main__":
    main()
