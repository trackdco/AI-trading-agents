#!/usr/bin/env python3
"""HEATMAP COIL DETECTOR (Angus 21 Jul). Read the order book at the open (09:30-09:40, the
sit-out) and ask: is it a COILED/BALANCED book (chop forming -> stand down the golden window)
or a ONE-SIDED/THINNING book (real move coming -> trade)? Test the depth features against the
golden stand-down labels, train Feb-Apr / test May-Jul.

Depth features over 09:30-09:40 (MBP-10, per-minute, top-10/side):
  balance     mean min(bid,ask)/max(bid,ask)   -- 1.0 = perfectly balanced (coil)
  abs_imbal   |bid-ask|/(bid+ask)              -- low = balanced (coil); high = one-sided
  thickness   mean total resting size          -- thick book = providers holding = mean-revert
  thin_delta  thickness end-vs-start           -- book PULLING (negative) = move coming
  wall_ratio  max single-level / mean level    -- a dominant wall = rejection/absorption

44 days only (golden labels ∩ depth). This is a DIRECTION check, not a confirmation.

    python -m scripts.heatmap_coil
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TRAIN = {"2026-02", "2026-03", "2026-04"}
DEPTH = "data/reference/depth_2026"


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 6:
        return np.nan
    r = d.x.rank()
    n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def day_features(path):
    d = pd.read_csv(path, parse_dates=["ts"])
    w = d[(d.ts.dt.hour == 9) & (d.ts.dt.minute.between(30, 39))]
    if not len(w):
        return None
    per = w.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
    if "bid" not in per or "ask" not in per:
        return None
    bid, ask = per["bid"], per["ask"]
    tot = bid + ask
    balance = (np.minimum(bid, ask) / np.maximum(bid, ask)).mean()
    abs_imbal = ((bid - ask).abs() / tot.replace(0, np.nan)).mean()
    thickness = tot.mean()
    thin_delta = tot.iloc[-1] - tot.iloc[0] if len(tot) > 1 else 0.0
    # wall: largest single price level vs mean level size, over the window
    lvl = w.groupby(["ts", "side", "price"])["size"].sum()
    wall_ratio = lvl.max() / lvl.mean() if lvl.mean() else np.nan
    return dict(balance=balance, abs_imbal=abs_imbal, thickness=thickness,
                thin_delta=thin_delta, wall_ratio=wall_ratio)


def main():
    lab = pd.read_csv("output/golden_read.csv")
    lab["date"] = lab.date.astype(str)
    lab["standdown"] = (lab.action == "STAND_DOWN").astype(int)
    rows = []
    for f in sorted(glob.glob(f"{DEPTH}/nq_depth_*_ny.csv")):
        ds = Path(f).stem.split("_")[2]
        feat = day_features(f)
        if feat:
            feat["date"] = ds
            rows.append(feat)
    D = pd.DataFrame(rows)
    M = lab.merge(D, on="date", how="inner")
    M["mo"] = M.date.str[:7]
    tr, te = M[M.mo.isin(TRAIN)], M[~M.mo.isin(TRAIN)]
    print(f"{len(M)} days with depth+label   train {len(tr)} (SD {tr.standdown.mean()*100:.0f}%)   "
          f"test {len(te)} (SD {te.standdown.mean()*100:.0f}%)\n")

    print("=== depth feature AUC for 'both books lose' (0.5=noise), train vs test ===")
    feats = ["balance", "abs_imbal", "thickness", "thin_delta", "wall_ratio"]
    res = []
    for f in feats:
        a_tr, a_te = auc(tr[f], tr.standdown), auc(te[f], te.standdown)
        res.append((f, a_tr, a_te))
    for f, a_tr, a_te in sorted(res, key=lambda r: -abs((r[1] or .5) - .5)):
        holds = a_tr and a_te and (a_tr - .5) * (a_te - .5) > 0 and abs(a_te - .5) > 0.12
        print(f"  {f:11s} train {a_tr:.2f}   test {a_te:.2f}   {'<- holds direction' if holds else ''}")

    # mean value of each feature on stand-down vs tradeable days (interpretable)
    print("\n=== mean feature: stand-down days vs tradeable days (all 44) ===")
    for f in feats:
        sd = M[M.standdown == 1][f].mean(); go = M[M.standdown == 0][f].mean()
        print(f"  {f:11s} stand-down {sd:8.3f}   tradeable {go:8.3f}   Δ {sd-go:+.3f}")

    # best-holding feature -> simple coil rule -> $ impact vs always-E4
    best = max(res, key=lambda r: abs((r[1] or .5) - .5) if r[2] and (r[1]-.5)*(r[2]-.5) > 0 else 0)
    f = best[0]
    thr = tr[f].median()
    hi_sd = tr[tr[f] >= thr].standdown.mean() > tr[tr[f] < thr].standdown.mean()
    print(f"\n=== coil rule: STAND DOWN when {f} {'>=' if hi_sd else '<'} {thr:.3f} (train median) ===")
    for name, s in (("TRAIN", tr), ("TEST", te)):
        flag = (s[f] >= thr) if hi_sd else (s[f] < thr)
        acc = (flag.astype(int) == s.standdown).mean() * 100
        prec = s[flag].standdown.mean() * 100 if flag.sum() else float("nan")
        base = s.E4.sum(); kept = s[~flag].E4.sum()
        print(f"  {name}: flag {int(flag.sum())}/{len(s)}  precision {prec:3.0f}%  acc {acc:3.0f}%   "
              f"E4 ${base:+7,.0f} -> GO-only ${kept:+7,.0f}")
    M.to_csv("output/heatmap_coil.csv", index=False)
    print("\n-> output/heatmap_coil.csv")


if __name__ == "__main__":
    main()
