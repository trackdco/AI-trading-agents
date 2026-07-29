#!/usr/bin/env python3
"""FOOTPRINT (price-level) as a conviction signal (Angus 22 Jul). We already have true footprint
data (ts_minute, price, side A/B, volume) -- per-price-level bid/ask aggressor volume. This builds
opening-window footprint features and asks the decisive question: do they separate no-trade days
out-of-fit BEYOND the minute-delta absorption (absorp_corr) we already validated, or are they
redundant with it? Same harness as coil/absorption.

Sign convention (verified earlier): B = buy aggressor, A = sell aggressor; delta = B - A,
corr(1m return, delta) = +0.65. Window 09:30-10:00 ET, causal for entries >= 10:00.

    python -m scripts.eval_footprint
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"
CUT = 10 * 60


def load_footprint():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if p.exists():
            fr.append(pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"]))
    d = pd.concat(fr, ignore_index=True)
    ny = d.ts_minute.dt.tz_convert(NY)
    hm = ny.dt.hour.values * 60 + ny.dt.minute.values           # cheap int filter FIRST
    keep = (hm >= 9 * 60 + 30) & (hm < CUT)
    d = d[keep].copy()
    ny = ny[keep]
    d["ny"] = ny.values
    d["d"] = ny.dt.strftime("%Y-%m-%d").values                  # strftime only on ~300k survivors
    d["mi"] = ny.dt.strftime("%Y-%m-%d %H:%M").values
    return d


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
    bars = pd.read_parquet("data/reference/nq_1m_master.parquet")
    bars = bars.assign(ny=bars.ts_event.dt.tz_convert(NY))
    bars["hm"] = bars.ny.dt.hour * 60 + bars.ny.dt.minute
    bars = bars[(bars.hm >= 9 * 60 + 30) & (bars.hm < CUT)].copy()
    bars["d"] = bars.ny.dt.strftime("%Y-%m-%d")
    bars["mi"] = bars.ny.dt.strftime("%Y-%m-%d %H:%M")
    bars["ret"] = bars.close - bars.open
    fp = load_footprint()                                    # already windowed 09:30-10:00
    fp["sd"] = np.where(fp.side == "B", fp.volume, -fp.volume)

    # --- per-minute delta (B-A) + minute return, all vectorized ---
    md = fp.groupby("mi").agg(delta=("sd", "sum"), vol=("volume", "sum"))
    M = bars[["d", "mi", "ret"]].merge(md, on="mi", how="left").fillna({"delta": 0, "vol": 0})
    M["dvg"] = (np.sign(M.ret) * np.sign(M.delta) < 0).astype(float)
    # (1) volume-weighted delta divergence per day (vectorized, no apply)
    M["w"] = np.maximum(M["vol"], 1.0)
    M["dvw"] = M["dvg"] * M["w"]
    gd = M.groupby("d")
    wsum = gd["dvw"].sum() / gd["w"].sum()
    # inline absorp_corr = -corr(ret, delta) per day (reuse instead of re-importing slow builder)
    corr = gd.apply(lambda x: (np.corrcoef(x.ret, x.delta)[0, 1]
                               if x.ret.std() > 0 and x.delta.std() > 0 else 0.0), include_groups=False)

    # --- per-day range from bars, then extreme-zone B-share from the price-level book ---
    rng = bars.groupby("d").agg(hi=("high", "max"), lo=("low", "min"), close=("close", "last"))
    rng["r"] = (rng.hi - rng.lo).clip(lower=0.25)
    fpd = fp.merge(rng, left_on="d", right_index=True, how="inner")
    fpd["zone"] = np.where(fpd.price >= fpd.hi - 0.25 * fpd.r, "top",
                           np.where(fpd.price <= fpd.lo + 0.25 * fpd.r, "bot", "mid"))
    zb = (fpd.groupby(["d", "zone"]).sd.sum() / fpd.groupby(["d", "zone"]).volume.sum()).unstack()
    # (2) extreme absorption: bought the high but closed off it + sold the low but closed off it
    ea = pd.DataFrame(index=rng.index)
    ea["top_bshare"] = zb.get("top"); ea["bot_bshare"] = zb.get("bot")
    ea["top_off"] = (rng.close < rng.hi - 0.25 * rng.r).astype(int)
    ea["bot_off"] = (rng.close > rng.lo + 0.25 * rng.r).astype(int)
    fp_extreme = (ea.top_bshare.fillna(0) * ea.top_off) + (-ea.bot_bshare.fillna(0) * ea.bot_off)
    # (3) concentration: busiest single price level's share of window volume
    lvl = fp.groupby(["d", "price"]).volume.sum()
    conc = lvl.groupby(level=0).max() / lvl.groupby(level=0).sum()

    F = pd.DataFrame({"fp_delta_div": wsum, "absorp_corr": -corr,
                      "fp_extreme_absorp": fp_extreme, "fp_concentration": conc})
    F = F.merge(L.set_index("day")[["both_red", "traded", "pl"]], left_index=True, right_index=True)
    F = F.reset_index().rename(columns={"d": "day", "index": "day"})
    F["yr"] = F.day.str[:4].astype(int)
    covered = set(fp["d"].unique())                          # only days with real footprint coverage
    return F[F.day.isin(covered)].dropna(subset=["fp_delta_div", "fp_concentration"])


def main():
    F = build()
    print(f"{len(F)} days  both-red base {F.both_red.mean()*100:.0f}%  "
          f"(2025 {int((F.yr==2025).sum())}, 2026 {int((F.yr==2026).sum())})\n")
    feats = ["fp_delta_div", "fp_extreme_absorp", "fp_concentration"]
    print("=== footprint single-signal out-of-fit AUC (0.50 = coin flip) ===")
    print(f"  {'feature':18s} {'2025':>7s} {'2026':>7s}")
    for c in feats:
        print(f"  {c:18s} {auc(F[F.yr==2025][c], F[F.yr==2025].both_red):7.2f} "
              f"{auc(F[F.yr==2026][c], F[F.yr==2026].both_red):7.2f}")

    # decisive check: independence vs the minute-delta absorption we already have (computed inline)
    try:
        C = pd.read_parquet("output/standdown_features.parquet")[["day", "coil"]]
        M = F.merge(C, on="day", how="left")
        print("\n=== independence (corr with signals we already validated) ===")
        for c in feats:
            print(f"  {c:18s}  vs absorp_corr {M[c].corr(M.absorp_corr):+.2f}   vs coil {M[c].corr(M.coil):+.2f}")
    except Exception as e:
        print("  (independence check skipped:", e, ")")
    print("\n  redundant (|corr|>0.6) => price-level adds nothing over minute delta for the DAILY read;")
    print("  independent + AUC>0.5 both years => a genuine third conviction axis worth sizing on.")


if __name__ == "__main__":
    main()
