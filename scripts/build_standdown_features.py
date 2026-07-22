#!/usr/bin/env python3
"""Build the no-trade (both-red) feature matrix (Angus 22 Jul). One row per day, every feature
causally knowable by ~09:45 ET, plus the both-red label and P&L columns for $ evaluation.
Covers the CVD+depth span (2025-06..2025-12 and 2026). Caches to output/standdown_features.parquet.

    python -m scripts.build_standdown_features
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import volume_profile                         # noqa: E402

NY = "America/New_York"
OUT = Path("output/standdown_features.parquet")


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
    g = pd.concat(fr).groupby(level=0).sum()
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")
    L["both_red"] = ((L.e3 <= 0) & (L.e4 <= 0)).astype(int)
    L["traded"] = L.act.isin(["MOMENTUM", "ROTATION"]).astype(int)
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(ny=df.ts_event.dt.tz_convert(NY))
    df["d"] = df.ny.dt.strftime("%Y-%m-%d")
    df["hm"] = df.ny.dt.hour * 60 + df.ny.dt.minute
    cvd = load_cvd()
    depth_idx = {Path(f).stem.split("_")[2]: f for f in
                 glob.glob("data/reference/depth_2025/*.csv") + glob.glob("data/reference/depth_2026/*.csv")}

    # prior-session RTH close per day (for the overnight gap): last bar <= 16:00 that day
    close_at = (df[df.hm <= 16 * 60].groupby("d").close.last())

    rows = []
    days = sorted(set(L.day) & set(df.d))
    for day in days:
        g = df[df.d == day]
        if g.empty:
            continue
        pre = cvd[(cvd.index >= pd.Timestamp(f"{day} 08:00", tz=NY)) &
                  (cvd.index < pd.Timestamp(f"{day} 09:30", tz=NY))]
        drive = cvd[(cvd.index >= pd.Timestamp(f"{day} 09:30", tz=NY)) &
                    (cvd.index < pd.Timestamp(f"{day} 09:40", tz=NY))]
        if not len(pre):
            continue                                          # no CVD -> outside covered span
        premkt = float(pre.sum()); odrive = float(drive.sum())

        rth10 = g[(g.hm >= 9 * 60 + 30) & (g.hm < 9 * 60 + 40)]
        rth15 = g[(g.hm >= 9 * 60 + 30) & (g.hm < 9 * 60 + 45)]
        if rth10.empty or rth15.empty:
            continue
        open_range = float(rth10.high.max() - rth10.low.min())
        try:
            P = volume_profile(rth15[["ts_event", "high", "low", "volume"]], 0.25, 70)
            va_width = float(P.vah - P.val)
        except Exception:
            va_width = np.nan
        # overnight gap: today's 9:30 open vs prior session's RTH close
        o930 = float(rth10.open.iloc[0])
        prev = close_at[close_at.index < day]
        gap = abs(o930 - float(prev.iloc[-1])) if len(prev) else np.nan

        # book coil: balance of bid/ask depth over 9:30-9:39
        coil = np.nan
        p = depth_idx.get(day)
        if p:
            dep = pd.read_csv(p, parse_dates=["ts"])
            hm = dep.ts.dt.hour * 60 + dep.ts.dt.minute
            w = dep[(hm >= 9 * 60 + 30) & (hm <= 9 * 60 + 39)]
            if len(w):
                per = w.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
                if "bid" in per and "ask" in per:
                    b, a = per["bid"].mean(), per["ask"].mean()
                    coil = float(min(b, a) / max(max(b, a), 1))

        lr = L[L.day == day].iloc[0]
        rows.append(dict(
            day=day, both_red=int(lr.both_red), traded=int(lr.traded),
            e3=float(lr.e3), e4=float(lr.e4), pl=float(lr.pl), act=lr.act,
            premkt_cvd=premkt, abs_cvd=abs(premkt), open_drive=odrive,
            drive_contra=int(np.sign(premkt) * np.sign(odrive) < 0
                            and abs(premkt) > 200 and abs(odrive) > 200),
            coil=coil, va_width=va_width, open_range=open_range, gap=gap,
        ))

    F = pd.DataFrame(rows)
    F["yr"] = F.day.str[:4].astype(int)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    F.to_parquet(OUT, index=False)
    print(f"wrote {len(F)} day-rows -> {OUT}")
    for yr in sorted(F.yr.unique()):
        s = F[F.yr == yr]
        print(f"  {yr}: n={len(s):3d}  both-red {s.both_red.mean()*100:.0f}%  "
              f"coil-cov {s.coil.notna().mean()*100:.0f}%  va-cov {s.va_width.notna().mean()*100:.0f}%")


if __name__ == "__main__":
    main()
