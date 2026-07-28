#!/usr/bin/env python3
"""L3 Stage A — the full order-flow/geometry feature matrix for every L2 outcome.

REUSES `score_canon_span.build_features` VERBATIM — the forward feature assembly whose
builders (src/canon/features.py) carry the as-of discipline: every window truncates
strictly before the fill minute, depth reads the last snapshot at/before it, AGE uses the
completed-overnight `on_extreme_age_day` form (the wrong variant made AGE fire at 14%
instead of 47% — recon 2026-07-30). Nothing here recomputes a feature; this script only
shapes inputs and parallelizes by day-chunk.

DIFFERENCES from the score_canon_span run, both deliberate:

  trigger stamps   `trigdens_30` counts triggers in the prior 30min. Fed from the L0
                   census (the honest, parity-gated stream), NOT the old v2 CSVs. This is
                   the one feature EXPECTED to differ from the cached matrices, so it is
                   excluded from the parity gate and flagged in every lift table.
  depth-less days  ANGUS 2026-07-30: the 14 days with no depth file (8 scattered 2026
                   days + the 2026-07-09..15 tail) are EXCLUDED from L3/L4 entirely —
                   "no point really testing those days". Logged on every run.

DEDUP-THEN-JOIN: features depend only on (day, fill, direction, entry, stop); multiple
census triggers can share all five (same level, minutes apart, MTF siblings). Feature the
unique set once, then left-join back onto the per-trigger L2 rows — identical inputs get
identical features by construction, and the per-trigger key (`ts`) survives.

GATE (--gate): every feature column shared with the old cached matrices
(trade_matrix / badpa_matrix / gold_quality) must reproduce ON THE MATCHED FILLS to
1e-6. Matching keys: (day, fill minute, direction), E3 book only. `trigdens_30` and
`conf_PM`-family are excluded with stated reasons (census stamps; the cached conf_PM is
the leaky full-window form the arming build replaced).

    python -m scripts.build_l3_features --gate
    python -m scripts.build_l3_features --run [--procs 3]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.score_canon_span import SPANS, build_features, depth_file, minute_tape  # noqa: E402

NY = "America/New_York"
DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026"]
KEY = ["day", "fill", "direction", "entry", "stop"]

_CTX: dict = {}          # fork-inherited read-only inputs for the Pool


def load_inputs():
    spec = dict(SPANS["fit"])
    M = minute_tape(spec)
    parts = [pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
             for f in spec["bars"]]
    bars = (pd.concat(parts, ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    # trigger stamps for trigdens_30 — from the L0 census, tz-naive UTC (features.py contract)
    L0 = pd.read_parquet(ROOT / "output/l0_triggers_fit.parquet")
    t_utc = pd.to_datetime(L0.ts, format="mixed", utc=True)
    tday = t_utc.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    trig_times = {d: g.dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
                  for d, g in t_utc.groupby(tday)}
    return M, bars, trig_times


def candidates(gate_only: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(S_unique, L2-outcome rows kept) — depth-less days excluded, S shaped for
    build_features (needs day/book/fill/direction/entry/stop/exit_price/dollars/pattern/tf)."""
    O = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet")
    oc = O[O.status == "outcome"].copy()
    have = {os.path.basename(f).split("_")[2]
            for d in DEPTH_DIRS for f in glob.glob(str(ROOT / d / "nq_depth_*_ny.csv"))}
    dropped = sorted(set(oc.day) - have)
    oc = oc[oc.day.isin(have)].copy()
    print(f"outcomes kept {len(oc)} | EXCLUDED {len(dropped)} depth-less days "
          f"(ANGUS 2026-07-30): {dropped}", flush=True)
    oc["fill"] = pd.to_datetime(oc.fill_ts, format="mixed", utc=True).dt.tz_convert(NY)
    S = (oc.assign(book="E3", dollars=oc.dollars_1lot)
         [["day", "book", "fill", "direction", "entry", "stop", "exit_price",
           "dollars", "pattern", "tf"]]
         .drop_duplicates(["day", "fill", "direction", "entry", "stop"])
         .reset_index(drop=True))
    if gate_only:
        TM = pd.read_parquet(ROOT / "output/trade_matrix.parquet")
        TM = TM[TM.book == "E3"]
        tmf = pd.to_datetime(TM.fill, format="mixed", utc=True).dt.tz_convert(NY)
        keys = set(zip(TM.day.astype(str), tmf.dt.strftime("%Y-%m-%d %H:%M"), TM.direction))
        sk = list(zip(S.day, S.fill.dt.strftime("%Y-%m-%d %H:%M"), S.direction))
        S = S[[k in keys for k in sk]].reset_index(drop=True)
        print(f"gate mode: {len(S)} candidates matched to cached E3 fills", flush=True)
    print(f"unique feature jobs: {len(S)} on {S.day.nunique()} days", flush=True)
    return S, oc


def _chunk(days: list[str]) -> pd.DataFrame:
    S = _CTX["S"]
    return build_features(S[S.day.isin(days)], _CTX["M"], _CTX["bars"],
                          _CTX["trig_times"], DEPTH_DIRS)


def feature_all(S: pd.DataFrame, procs: int) -> pd.DataFrame:
    global _CTX
    M, bars, trig_times = load_inputs()
    _CTX = {"S": S, "M": M, "bars": bars, "trig_times": trig_times}
    days = sorted(S.day.unique())
    if procs <= 1:
        return _chunk(days)
    groups = [days[i::procs] for i in range(procs)]
    with Pool(procs) as p:
        parts = p.map(_chunk, groups)
    return pd.concat(parts, ignore_index=True)


# columns shared with the cached matrices, compared to 1e-6 on matched fills.
# EXCLUDED with reasons: trigdens_30 (census stamps vs v2 CSVs — expected differ),
# conf_PM/pm_* family vs trade_matrix.conf_PM (cached form is the LEAKY full-window
# variant; the arming build replaced it with pm_sofar_conf — we compare against THAT),
# r_3/fw_3 (post-fill layer-2d inputs, not selection features).
TM_COLS = ["dep_thick", "dep_imb", "dep_wall_above_d", "dep_wall_above_sz",
           "dep_wall_below_d", "dep_wall_below_sz", "fill_delta", "fill_delta_conf",
           "ent_vs_vwap_sd_dir", "d15", "d15_conf", "on_extreme_age", "pm_sofar_conf"]
BP_COLS = ["netpath_30", "bbw_state", "churn_flow_30"]
GQ_COLS = ["bp5opp", "lon_slope_d"]


def gate(procs: int) -> None:
    S, _ = candidates(gate_only=True)
    F = feature_all(S, procs)
    F["k"] = list(zip(F.day, pd.to_datetime(F["fill"]).dt.strftime("%Y-%m-%d %H:%M"),
                      F.direction))

    def matched(cached: pd.DataFrame, cols: list[str], label: str) -> bool:
        c = cached[cached.book == "E3"].copy() if "book" in cached else cached.copy()
        cf = pd.to_datetime(c.fill, format="mixed", utc=True).dt.tz_convert(NY)
        c["k"] = list(zip(c.day.astype(str), cf.dt.strftime("%Y-%m-%d %H:%M"), c.direction))
        j = F.merge(c[["k"] + [x for x in cols if x in c]], on="k",
                    suffixes=("", "_ref"))
        ok = True
        for col in cols:
            if f"{col}_ref" not in j:
                continue
            a, b = j[col].astype(float), j[f"{col}_ref"].astype(float)
            both = a.notna() & b.notna()
            diff = (a[both] - b[both]).abs()
            nan_mismatch = int((a.isna() != b.isna()).sum())
            bad = int((diff > 1e-6).sum())
            state = "OK " if bad == 0 and nan_mismatch == 0 else "FAIL"
            ok &= state == "OK "
            print(f"  [{state}] {label:<13} {col:<20} matched {both.sum():>4}  "
                  f"maxdiff {diff.max() if len(diff) else 0:.2e}  nan-mismatch {nan_mismatch}")
        return ok

    ok = matched(pd.read_parquet(ROOT / "output/trade_matrix.parquet"), TM_COLS, "trade_matrix")
    ok &= matched(pd.read_parquet(ROOT / "output/badpa_matrix.parquet"), BP_COLS, "badpa_matrix")
    ok &= matched(pd.read_parquet(ROOT / "output/gold_quality.parquet"), GQ_COLS, "gold_quality")
    if not ok:
        raise SystemExit("GATE FAILED — L3 features diverge from the cached matrices "
                         "on matched fills; do not run Stage B on this")
    print("gate OK — every shared feature reproduces on the matched fills "
          "(trigdens_30/conf_PM excluded by design, reasons in the module docstring)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args()
    if a.gate:
        return gate(a.procs)
    if not a.run:
        raise SystemExit("--gate or --run required")
    S, oc = candidates()
    F = feature_all(S, a.procs)
    # join features back onto the per-trigger L2 rows (dedup-then-join, see docstring)
    F2 = F.drop(columns=["book", "exit_price", "dollars", "pattern", "tf", "risk", "R",
                         "yr"], errors="ignore")
    out_rows = oc.merge(F2, left_on=["day", "fill", "direction", "entry", "stop"],
                        right_on=KEY, how="left")
    out = ROOT / "output/l3_features_fit.parquet"
    out_rows.to_parquet(out, index=False)
    feat_cols = [c for c in F2.columns if c not in KEY]
    cov = out_rows[feat_cols].notna().mean().sort_values()
    print(f"\nwrote {out.relative_to(ROOT)} — {len(out_rows)} rows, "
          f"{len(feat_cols)} feature columns")
    print(f"lowest coverage:\n{cov.head(8).to_string()}")


if __name__ == "__main__":
    main()
