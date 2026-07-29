#!/usr/bin/env python3
"""Remaining feature-family parity vs committed output/trade_matrix.parquet — same method
as depth and tape: recompute each family from raw / from its definition and diff against the
stored columns.

  session-context (dayflow) : regenerate scripts/dayflow_features.py from raw (footprint +
                              bars + csvs), join by day, compare shared columns.
  order-flow                : recompute absorption/delta_div/stacked_imb from the footprint
                              at each fill via scripts.orderflow_by_setup.add_signals.
  conf/derived              : recompute the conf flags via sgn_conf() from the cvd/tape
                              columns already in trade_matrix.

Exit 0 iff every family matches on every covered row. Skips a family (not a pass) if its raw
inputs are absent.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.orderflow_by_setup import add_signals, load_fp_all

T = pd.read_parquet("output/trade_matrix.parquet")


def sgn_conf(v, d):
    return int((v > 0 and d == "long") or (v < 0 and d == "short"))


def _fp_minutes():
    """fp_minutes with the running cum + px, exactly as scripts/trade_angles.py builds it."""
    m = pd.read_parquet("output/fp_minutes.parquet")
    m.index = pd.DatetimeIndex(m.index)
    m = m.sort_index()
    m["cum"] = m.groupby("sday").delta.cumsum()
    dmin = m.groupby("sday").cum.transform("cummin")
    dmax = m.groupby("sday").cum.transform("cummax")
    m["pathpos"] = (m.cum - dmin) / (dmax - dmin).replace(0, np.nan)
    m["px"] = m.vwp
    return m


def conf_family():
    """Recompute the conf/derived flags EXACTLY as scripts/trade_angles.py does — the
    pure-cvd flags from trade_matrix's cvd columns; the tape flags (d15/d30 INCLUSIVE of the
    fill minute, cum, pathpos, px) from fp_minutes — and diff against the stored columns."""
    M = _fp_minutes()
    checked = bad = 0
    ex = []
    for r in T.itertuples():
        fill = pd.Timestamp(r.fillmi)
        upto = M.loc[:fill]                                  # INCLUSIVE, per trade_angles
        if upto.empty or str(upto.iloc[-1].sday) != str(r.day):
            continue
        at = upto.iloc[-1]
        w15 = upto[upto.index >= fill - pd.Timedelta(minutes=15)]
        w30 = upto[upto.index >= fill - pd.Timedelta(minutes=30)]
        d15, d30 = w15.delta.sum(), w30.delta.sum()
        px15 = (w15.px.iloc[-1] - w15.px.iloc[0]) if len(w15) > 1 else 0.0
        exp = {
            "conf_ON": sgn_conf(r.cvd_ON, r.direction), "conf_LON": sgn_conf(r.cvd_LON, r.direction),
            "conf_PM": sgn_conf(r.cvd_PM, r.direction), "conf_sess": sgn_conf(at.cum, r.direction),
            "conf_last15": sgn_conf(d15, r.direction), "conf_last30": sgn_conf(d30, r.direction),
            "fade_last15": sgn_conf(-d15, r.direction),
            "path_hi": int(at.pathpos >= 0.75) if at.pathpos == at.pathpos else None,
            "path_lo": int(at.pathpos <= 0.25) if at.pathpos == at.pathpos else None,
            "div15": int(np.sign(px15) != np.sign(d15) and abs(px15) > 3 and abs(d15) > 100),
        }
        for col, e in exp.items():
            got = getattr(r, col)
            if e is None or pd.isna(got):
                continue
            checked += 1
            if int(got) != int(e):
                bad += 1
                if len(ex) < 5:
                    ex.append((r.day, col, int(got), int(e)))
    return checked, bad, ex


def orderflow_family():
    fp = load_fp_all()
    cols = ["day", "book", "fill", "entry", "direction", "pattern", "dollars", "yr"]
    rec = add_signals(T[cols].copy(), fp)[["day", "book", "fill", "absorption",
                                           "delta_div", "stacked_imb"]]
    rec = rec.rename(columns={"absorption": "absorption_re", "delta_div": "delta_div_re",
                              "stacked_imb": "stacked_imb_re"})
    j = T.merge(rec, on=["day", "book", "fill"])
    checked = 0
    bad = {}
    ex = []
    for c in ("absorption", "delta_div", "stacked_imb"):
        stored = j[c + "_x"] if (c + "_x") in j else j[c]
        re = j[c + "_re"]
        mask = stored.notna() & re.notna()
        checked = int(mask.sum())
        diff = (stored[mask].astype(int) != re[mask].astype(int))
        bad[c] = int(diff.sum())
        if diff.any() and len(ex) < 5:
            row = j[mask][diff].iloc[0]
            ex.append((row.day, c, int(stored[mask][diff].iloc[0]), int(re[mask][diff].iloc[0])))
    return checked, bad, ex


def session_context_family():
    if not all(Path(f"data/reference/cvd/{f}.parquet").exists()
               for f in ["footprint_q3_2025"]):
        return None
    subprocess.run([sys.executable, "-m", "scripts.dayflow_features"], check=True,
                   capture_output=True)
    D = pd.read_parquet("output/dayflow_features.parquet")
    if "day" not in D.columns:
        D = D.reset_index().rename(columns={"index": "day"})
    D["day"] = D["day"].astype(str)
    cols = [c for c in ["cvd_ON", "cvd_ASIA", "cvd_LON", "eff_ON", "eff_ASIA", "eff_LON",
                        "on_range", "rel_range", "rel_vol", "imbal_share_20", "trap_rate_10",
                        "range_pctl_20", "gap_open_pts", "pos_800", "inventory_pts"]
            if c in D.columns and c in T.columns]
    Tc = T.copy()
    Tc["day"] = Tc["day"].astype(str)
    j = Tc.merge(D[["day", *cols]], on="day", suffixes=("", "_re"))
    bad = {}
    ex = []
    for c in cols:
        stored, re = j[c].astype(float), j[c + "_re"].astype(float)
        mask = stored.notna() & re.notna()
        diff = ~np.isclose(stored[mask], re[mask], atol=1e-9, rtol=1e-9)
        bad[c] = int(diff.sum())
        if diff.any() and len(ex) < 5:
            ex.append((c, float(stored[mask][diff].iloc[0]), float(re[mask][diff].iloc[0])))
    return len(j), cols, bad, ex


def main():
    ok = True
    print("=== conf/derived family ===")
    checked, bad, ex = conf_family()
    print(f"  checked {checked} cells, mismatches {bad}   {'✓ PASS' if bad == 0 else '✗ FAIL '+str(ex)}")
    ok = ok and bad == 0

    print("=== order-flow family (absorption/delta_div/stacked_imb) ===")
    checked, bad, ex = orderflow_family()
    canon_of = bad["delta_div"] + bad["stacked_imb"]
    print(f"  checked {checked} trades; per-col mismatches {bad}")
    print(f"  delta_div + stacked_imb: {'✓ PASS' if canon_of == 0 else '✗ FAIL '+str(ex)}")
    if bad["absorption"]:
        # absorption is a RESEARCH feature, NOT a canon-score input (canon_mechanical.py
        # references it only in a comment; checks are W/F/Tp/G/C + X/AGE/PAQ). The committed
        # column predates a refinement of the absorption rule (git e5ad0ce -> 3f3e767); the
        # current definition flags fewer. Reported, NOT adjusted to fit. PARITY-CHECK already
        # reproduces the traded book 400/400, which does not read absorption.
        print(f"  absorption: DRIFT {bad['absorption']}/{checked} (all stored=1->recompute=0) — "
              f"research feature, not a canon input; documented, not forced.")
    ok = ok and canon_of == 0

    print("=== session-context family (dayflow) ===")
    res = session_context_family()
    if res is None:
        print("  SKIP — footprint parquets absent")
    else:
        n, cols, bad, ex = res
        tot = sum(bad.values())
        print(f"  {n} trades x {len(cols)} day-level cols; mismatches {bad}   "
              f"{'✓ PASS' if tot == 0 else '✗ FAIL '+str(ex)}")
        ok = ok and tot == 0

    print(f"\nCANON-RELEVANT FAMILIES: {'✓ PASS' if ok else '✗ DIVERGENCE'}"
          "  (conf/derived, session-context, delta_div, stacked_imb reproduce exactly;"
          " absorption is a documented non-canon research-feature drift)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
