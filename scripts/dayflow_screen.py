#!/usr/bin/env python3
"""OOF screen of the day-flow feature library (Angus 23-Jul autonomous deep-dive).

Every feature (raw + |abs|) scored against BOTH day-read targets, separately per year:
  T1 both_red   (should we stand down?)      AUC red-vs-ok
  T2 book_label (E4 vs E3, tradeable days)   AUC E4-vs-E3
A feature survives only if the direction agrees in 2025 AND 2026 and AUC >= 0.57 both years.
Survivors then get quintile-capture tables, and 2025-fitted / 2026-frozen $-rules with
capture vs the oracle+SD ceiling.

    python -m scripts.dayflow_screen
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

META = {"E3", "E4", "oracle_sd", "both_red", "book_label", "yr"}


def auc(x, y):
    """rank AUC of x predicting binary y (1=positive class)."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 20:
        return np.nan
    r = d.x.rank()
    n1 = int(d.y.sum()); n0 = len(d) - n1
    u = r[d.y == 1].sum() - n1 * (n1 + 1) / 2
    return float(u / (n1 * n0))


def main():
    F = pd.read_parquet("output/dayflow_features.parquet")
    feats = [c for c in F.columns if c not in META and F[c].dtype.kind == "f"]
    for c in list(feats):
        if F[c].min() < 0:                       # add magnitude twin for signed features
            F["abs_" + c] = F[c].abs(); feats.append("abs_" + c)

    print(f"{len(F)} days, {len(feats)} candidate features\n")
    res = []
    for f in feats:
        r = {"feat": f}
        for yr in (2025, 2026):
            d = F[F.yr == yr]
            r[f"sd_{yr}"] = auc(d[f], d.both_red)
            t = d[d.both_red == 0]
            r[f"bk_{yr}"] = auc(t[f], (t.book_label == "E4").astype(int))
        res.append(r)
    R = pd.DataFrame(res).set_index("feat")

    def survivors(cols, tag):
        a, b = R[cols[0]], R[cols[1]]
        keep = R[((a - .5) * (b - .5) > 0) & ((a - .5).abs() >= .07) & ((b - .5).abs() >= .07)]
        keep = keep.assign(strength=(keep[cols[0]] - .5).abs() + (keep[cols[1]] - .5).abs())
        keep = keep.sort_values("strength", ascending=False)
        print(f"=== {tag} survivors (consistent direction, AUC>=0.57 both years) ===")
        if len(keep) == 0:
            print("  NONE")
        for f, row in keep.iterrows():
            print(f"  {f:22s} 2025 {row[cols[0]]:.2f}  2026 {row[cols[1]]:.2f}")
        print()
        return list(keep.index)

    sd_keep = survivors(["sd_2025", "sd_2026"], "STAND-DOWN")
    bk_keep = survivors(["bk_2025", "bk_2026"], "BOOK-PICK")

    # quintile capture tables for top survivors
    for tgt, keep in [("both_red", sd_keep[:6]), ("book", bk_keep[:6])]:
        for f in keep:
            print(f"--- {f} quintiles ({tgt}) ---")
            for yr in (2025, 2026):
                d = F[F.yr == yr].dropna(subset=[f])
                if tgt == "book":
                    d = d[d.both_red == 0]
                try:
                    q = pd.qcut(d[f], 5, labels=False, duplicates="drop")
                except ValueError:
                    continue
                if tgt == "both_red":
                    tab = d.groupby(q).apply(lambda g: f"{g.both_red.mean()*100:3.0f}%red ${g.oracle_sd.mean():5.0f}orc", include_groups=False)
                else:
                    tab = d.groupby(q).apply(lambda g: f"{(g.book_label=='E4').mean()*100:3.0f}%E4", include_groups=False)
                print(f"  {yr}: " + " | ".join(f"Q{int(k)+1} {v}" for k, v in tab.items()))
        print()

    # ---- $-rules: fit on 2025, frozen on 2026 ----
    print("=== $-RULES (fit 2025 -> frozen 2026) ===")
    tr, te = F[F.yr == 2025], F[F.yr == 2026]
    ceil25, ceil26 = tr.oracle_sd.sum(), te.oracle_sd.sum()

    def run_rule(d, sd_col, sd_thr, sd_gt, bk_col, bk_thr, bk_gt):
        trade = (d[sd_col] > sd_thr) if sd_gt else (d[sd_col] < sd_thr)
        pick_e4 = (d[bk_col] > bk_thr) if bk_gt else (d[bk_col] < bk_thr)
        pl = np.where(trade, np.where(pick_e4, d.E4, d.E3), 0.0)
        return float(pl.sum()), int(trade.sum())

    best = None
    sd_cands = sd_keep[:4] if sd_keep else ["inventory_pts"]
    bk_cands = bk_keep[:4] if bk_keep else ["cvd_PM"]
    for sc in sd_cands:
        for bc in bk_cands:
            for sq in (.3, .4, .5, .6, .7):
                for bq in (.3, .4, .5, .6, .7):
                    st, bt = tr[sc].quantile(sq), tr[bc].quantile(bq)
                    for sg in (True, False):
                        for bg in (True, False):
                            pl, n = run_rule(tr, sc, st, sg, bc, bt, bg)
                            if n < 30:
                                continue
                            if best is None or pl > best[0]:
                                best = (pl, sc, st, sg, bc, bt, bg, n)
    pl25, sc, st, sg, bc, bt, bg, n25 = best
    pl26, n26 = run_rule(te, sc, st, sg, bc, bt, bg)
    print(f"best 2025 rule: trade if {sc} {'>' if sg else '<'} {st:.1f}; book=E4 if {bc} {'>' if bg else '<'} {bt:.1f}")
    print(f"  2025 (fit):   ${pl25:+8,.0f}  ({n25} traded days)  capture {pl25/ceil25*100:4.0f}%  of ${ceil25:+,.0f}")
    print(f"  2026 (FROZEN):${pl26:+8,.0f}  ({n26} traded days)  capture {pl26/ceil26*100:4.0f}%  of ${ceil26:+,.0f}")

    # soft-score ensemble of survivors: z-sum with 2025-fitted directions
    print("\n=== soft-score ensemble (top-4 survivors each target, z-sum, dirs from 2025) ===")
    def zsum(d, cols, ref, target):
        s = pd.Series(0.0, index=d.index)
        for f in cols:
            mu, sd_ = ref[f].mean(), ref[f].std()
            if sd_ == 0 or np.isnan(sd_):
                continue
            direction = np.sign(auc(ref[f], (ref.both_red if target == "sd" else (ref.book_label == "E4").astype(int))) - .5)
            s = s.add(direction * (d[f] - mu) / sd_, fill_value=0.0)
        return s
    for yr, d in (("2025", tr), ("2026", te)):
        ssd = zsum(d, sd_cands, tr, "sd")      # higher => more likely red
        sbk = zsum(d, bk_cands, tr, "bk")      # higher => more likely E4
        trade = ssd < ssd.quantile(0.55)       # stand down the worst 45%
        pl = np.where(trade, np.where(sbk > 0, d.E4, d.E3), 0.0).sum()
        ceil = d.oracle_sd.sum()
        print(f"  {yr}: ${pl:+8,.0f}  capture {pl/ceil*100:4.0f}%  (traded {int(trade.sum())}/{len(d)})")

    R.to_csv("output/dayflow_screen.csv")
    print("\nwrote output/dayflow_screen.csv")


if __name__ == "__main__":
    main()
