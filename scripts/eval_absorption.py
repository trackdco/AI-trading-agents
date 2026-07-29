#!/usr/bin/env python3
"""OPENING-ABSORPTION as a no-trade signal (Angus 22 Jul). The guide's real order-flow edge is
DIVERGENCE/ABSORPTION (price makes a new extreme, CVD doesn't confirm -> aggression absorbed ->
reversal/chop), NOT conviction magnitude (which we already falsified). This builds several
opening-window absorption features from executed flow (footprint CVD) and runs each through the
same out-of-fit harness as the coil test: two-way AUC + precision at a fixed stand-down rate.

Window is 09:30-10:00 ET (causal for any entry taken >=10:00). All features oriented so
HIGHER = more absorptive / more no-trade lean.

    python -m scripts.eval_absorption
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"
CUT = 10 * 60          # window end 10:00 (minutes since midnight)


def load_cvd_minute():
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


def auc(score, label):
    s = pd.Series(np.asarray(score, float)); y = np.asarray(label)
    m = s.notna().values; s, y = s[m].values, y[m]
    if len(np.unique(y)) < 2:
        return np.nan
    r = pd.Series(s).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def build():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")
    L["both_red"] = ((L.e3 <= 0) & (L.e4 <= 0)).astype(int)
    L["traded"] = L.act.isin(["MOMENTUM", "ROTATION"]).astype(int)
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(ny=df.ts_event.dt.tz_convert(NY))
    df["d"] = df.ny.dt.strftime("%Y-%m-%d")
    df["hm"] = df.ny.dt.hour * 60 + df.ny.dt.minute
    cvd = load_cvd_minute()
    cmin = pd.DataFrame({"delta": cvd})
    cmin["d"] = cvd.index.strftime("%Y-%m-%d")
    cmin["hm"] = cvd.index.hour * 60 + cvd.index.minute

    rows = []
    for day in sorted(set(L.day) & set(df.d)):
        g = df[(df.d == day) & (df.hm >= 9 * 60 + 30) & (df.hm < CUT)].sort_values("hm")
        c = cmin[(cmin.d == day) & (cmin.hm >= 9 * 60 + 30) & (cmin.hm < CUT)].sort_values("hm")
        if len(g) < 10 or len(c) < 10:
            continue
        ret = g.close.diff().values[1:]
        dlt = g.hm.map(c.set_index("hm").delta).fillna(0).values[1:]   # align delta to price minutes
        cum = np.cumsum(g.hm.map(c.set_index("hm").delta).fillna(0).values)
        price = g.close.values
        rng_ticks = max((g.high.max() - g.low.min()) / 0.25, 1)

        # (1) flow/price disagreement: corr(return, delta) low/neg -> absorptive
        corr = np.corrcoef(ret, dlt)[0, 1] if np.std(ret) > 0 and np.std(dlt) > 0 else 0.0
        absorp_corr = -corr
        # (2) aggression per unit price progress: lots of |delta|, little net travel -> absorptive
        absorp_ratio = np.sum(np.abs(dlt)) / rng_ticks
        # (3) extreme divergence: price high not confirmed by CVD high (and low by CVD low)
        #     gap (in window fraction) between argmax price and argmax cum-CVD, + arg-min side
        n = len(price)
        div_hi = abs(np.argmax(price) - np.argmax(cum)) / n
        div_lo = abs(np.argmin(price) - np.argmin(cum)) / n
        extreme_div = max(div_hi, div_lo)
        # (4) net directional disagreement (binary): net price up but net CVD down (or vice versa)
        net_dis = int(np.sign(price[-1] - price[0]) * np.sign(cum[-1]) < 0)

        lr = L[L.day == day].iloc[0]
        rows.append(dict(day=day, both_red=int(lr.both_red), traded=int(lr.traded),
                         pl=float(lr.pl), absorp_corr=absorp_corr, absorp_ratio=absorp_ratio,
                         extreme_div=extreme_div, net_dis=net_dis))
    F = pd.DataFrame(rows); F["yr"] = F.day.str[:4].astype(int)
    return F


def main():
    F = build()
    print(f"{len(F)} days  both-red base {F.both_red.mean()*100:.0f}%  "
          f"(2025 {int((F.yr==2025).sum())}, 2026 {int((F.yr==2026).sum())})\n")
    feats = ["absorp_corr", "absorp_ratio", "extreme_div", "net_dis"]

    print("=== opening-absorption single-signal out-of-fit AUC (0.50 = coin flip) ===")
    print(f"  {'feature':13s} {'2025':>7s} {'2026':>7s}")
    for c in feats:
        print(f"  {c:13s} {auc(F[F.yr==2025][c], F[F.yr==2025].both_red):7.2f} "
              f"{auc(F[F.yr==2026][c], F[F.yr==2026].both_red):7.2f}")

    print("\n=== precision at fixed stand-down rate (flag top-40% by feature) ===")
    print(f"  {'feature':13s} {'dir':10s} {'prec':>5s} {'rec':>5s} {'$delta':>9s}")
    base = F.both_red.mean() * 100
    for c in feats:
        for test in (2025, 2026):
            te = F[F.yr == test]
            thr = np.nanquantile(te[c], 0.60)
            flag = te[c] >= thr
            tp = int((flag & (te.both_red == 1)).sum()); fp = int((flag & (te.both_red == 0)).sum())
            fn_ = int((~flag & (te.both_red == 1)).sum())
            prec = tp / max(tp + fp, 1) * 100; rec = tp / max(tp + fn_, 1) * 100
            d = np.where(flag, 0.0, te.pl).sum() - te.pl.sum()
            print(f"  {c:13s} {test:10d} {prec:4.0f}% {rec:4.0f}% ${d:+8,.0f}")
    print(f"\n  both-red base rate {base:.0f}% — precision must clear this. "
          f"coil benchmark was 58%/58%.")


if __name__ == "__main__":
    main()
