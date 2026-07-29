#!/usr/bin/env python3
"""COIL DETECTOR — FULL SAMPLE (Angus 21 Jul). Expand golden stand-down labels to EVERY
depth day (not just days that traded), then judge the heatmap chop signal against the
hindsight truth ("both books lose") and adjust P&L.

  * label   : per-day golden action from book P&L; a day with no golden trade = stand-down (0/0)
  * signal  : coil = balanced book at 09:30-09:40 (causal). Fires -> "chop, stand down"
  * compare : coil signal vs books-say-stand-down (precision/recall), and the P&L when we
              stand down on the coil signal (causal) vs perfect stand-down (hindsight ceiling).
  train Feb-Apr / test May-Jul. Writes output/coil_full.csv for the localhost summary.

    python -m scripts.coil_full
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import load                              # noqa: E402
from scripts.champion_journal_cvd import load_cvd_delta                # noqa: E402
from scripts.golden_read import golden_book_pnl                        # noqa: E402
from scripts.heatmap_coil import day_features                          # noqa: E402
from src.backtest.selection import load_selection_filters             # noqa: E402

TRAIN = {"2026-02", "2026-03", "2026-04"}
DEPTH = "data/reference/depth_2026"


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    filt = load_selection_filters()
    print("loading CVD ...", flush=True)
    cvd = load_cvd_delta()
    print("golden book P&L labels ...", flush=True)
    lab = golden_book_pnl(allt, df, cvd, V, filt)          # days that traded
    lab["date"] = lab.date.astype(str)

    print("coil features over ALL depth days ...", flush=True)
    rows = []
    for f in sorted(glob.glob(f"{DEPTH}/nq_depth_*_ny.csv")):
        ds = Path(f).stem.split("_")[2]
        feat = day_features(f)
        if feat:
            feat["date"] = ds
            rows.append(feat)
    D = pd.DataFrame(rows)

    # LEFT join on depth days -> days with no golden trade get E3=E4=0 (=stand-down)
    M = D.merge(lab[["date", "E3", "E4"]], on="date", how="left")
    M[["E3", "E4"]] = M[["E3", "E4"]].fillna(0.0)
    M["standdown"] = (M[["E3", "E4"]].max(axis=1) <= 0).astype(int)     # hindsight truth
    M["mo"] = M.date.str[:7]
    M = M[M.mo.isin(TRAIN | {"2026-05", "2026-06", "2026-07"})]

    # coil signal: balanced book => chop. Threshold from TRAIN median of abs_imbal (low=coil).
    tr0 = M[M.mo.isin(TRAIN)]
    thr = tr0.abs_imbal.median()
    M["coil"] = (M.abs_imbal < thr).astype(int)             # 1 = signal "chop, stand down"

    tr, te = M[M.mo.isin(TRAIN)], M[~M.mo.isin(TRAIN)]
    print(f"\n### COIL DETECTOR — FULL SAMPLE ###")
    print(f"days: {len(M)}  (train {len(tr)}, test {len(te)});  coil fires when abs_imbal < {thr:.3f}\n")

    def block(s, name):
        base_sd = s.standdown.mean() * 100
        fire = s[s.coil == 1]
        prec = fire.standdown.mean() * 100 if len(fire) else float("nan")   # coil fires -> books lose?
        rec = (s[s.standdown == 1].coil.mean() * 100) if s.standdown.sum() else float("nan")
        acc = (s.coil == s.standdown).mean() * 100
        # P&L, always-E4 book: no filter vs coil-standdown (causal) vs perfect standdown (hindsight)
        for book in ("E4", "E3"):
            no_f = s[book].sum()
            coil_f = s[s.coil == 0][book].sum()
            perfect = s[s.standdown == 0][book].sum()
            if book == "E4":
                pnl_line = (f"    E4 book:  no-filter ${no_f:+7,.0f}   coil-standdown ${coil_f:+7,.0f}   "
                            f"perfect-standdown ${perfect:+7,.0f}")
            else:
                pnl_line = (f"    E3 book:  no-filter ${no_f:+7,.0f}   coil-standdown ${coil_f:+7,.0f}   "
                            f"perfect-standdown ${perfect:+7,.0f}")
            if book == "E4":
                first = pnl_line
            else:
                second = pnl_line
        print(f"== {name} ==  n={len(s)}  actual stand-down {base_sd:.0f}%")
        print(f"    coil fires {int(s.coil.sum())}/{len(s)}  ->  precision {prec:.0f}% (fires & books lose)  "
              f"recall {rec:.0f}% (of stand-downs caught)  signal-accuracy {acc:.0f}%")
        print(first); print(second); print()

    block(tr, "TRAIN Feb-Apr")
    block(te, "TEST  May-Jul")
    block(M, "ALL")
    M.to_csv("output/coil_full.csv", index=False)
    print("-> output/coil_full.csv")


if __name__ == "__main__":
    main()
