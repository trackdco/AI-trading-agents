"""Job 1 — build FIT-span profiles, construction gate inputs, and censuses.

Outputs (all under output/vp_census/):
- profiles.parquet           every construction variant, FIT span
- excursions.parquet         canonical construction census (bin 1.0, VA70, paired)
- excursions_variants.parquet all bar-construction variants, tagged
- construction_gate.csv      section 2.4 inputs (deltas + flip rate)
- trial_ledger.csv           one row per configuration executed
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from itertools import product

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/vp_census")
import vp_lib as V

FIT_START, FIT_END = "2025-06-01", "2026-07-31"
FP_FILES = [
    "data/reference/cvd/footprint_q3_2025.parquet",
    "data/reference/cvd/footprint_q4_2025.parquet",
    "data/reference/cvd/footprint_jan2026.parquet",
    "data/reference/cvd/footprint_feb_mar2026.parquet",
    "data/reference/cvd/footprint_apr2026.parquet",
    "data/reference/cvd/footprint_may_jul2026.parquet",
]
BINS = (0.25, 1.0, 2.0)
VAS = (0.68, 0.70, 0.75)
EXPS = ("paired", "single")
CANON = dict(bin_width=1.0, va_pct=0.70, expansion="paired")


def fit_sessions(bars: pd.DataFrame):
    s = pd.Series(sorted(set(bars["session"])))
    d = pd.to_datetime(s)
    m = (d >= FIT_START) & (d <= FIT_END)
    return list(s[m])


def main() -> int:
    git_sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    bars = V.load_master_bars()
    sessions = fit_sessions(bars)
    print(f"FIT sessions with bars: {len(sessions)}  "
          f"({sessions[0]} -> {sessions[-1]})")

    fp = V.load_footprint(FP_FILES)

    all_profiles = []
    ledger = []

    # ---- bar-construction variants (full 3x3x2 grid) --------------------
    for bw, va, exp in product(BINS, VAS, EXPS):
        prof = V.build_profiles(bars, sessions, bin_width=bw, va_pct=va,
                                expansion=exp, construction="bar_uniform")
        all_profiles.append(prof)
        for K in V.K_SWEEP:
            ledger.append(dict(run_id=f"bar_b{bw}_v{int(va*100)}_{exp}_K{K}",
                               K=K, bin_width=bw, va_pct=va,
                               va_expansion_rule=exp, construction="bar_uniform",
                               placebo_type="none",
                               timestamp=pd.Timestamp.now(tz="UTC").isoformat(),
                               git_sha=git_sha))
        print(f"profiles bar bw={bw} va={va} {exp}: "
              f"OK={int((prof.profile_status=='OK').sum())} "
              f"other={int((prof.profile_status!='OK').sum())}")

    # ---- footprint comparator (canonical settings only) ------------------
    prof_fp = V.build_profiles(bars, sessions, construction="footprint",
                               fp=fp, **CANON)
    all_profiles.append(prof_fp)
    ledger.append(dict(run_id="footprint_canonical_K15", K=15,
                       bin_width=CANON["bin_width"], va_pct=CANON["va_pct"],
                       va_expansion_rule=CANON["expansion"],
                       construction="footprint", placebo_type="none",
                       timestamp=pd.Timestamp.now(tz="UTC").isoformat(),
                       git_sha=git_sha))
    print(f"profiles footprint canonical: "
          f"OK={int((prof_fp.profile_status=='OK').sum())} "
          f"other={int((prof_fp.profile_status!='OK').sum())}")

    profiles = pd.concat(all_profiles, ignore_index=True)
    profiles = profiles.sort_values(
        ["construction", "bin_width", "va_pct", "expansion", "session_date"],
        kind="mergesort").reset_index(drop=True)
    profiles.to_parquet("output/vp_census/profiles.parquet", index=False)

    # ---- censuses ---------------------------------------------------------
    variants = []
    canon_ex = None
    for bw, va, exp in product(BINS, VAS, EXPS):
        sel = profiles[(profiles.construction == "bar_uniform") &
                       (profiles.bin_width == bw) & (profiles.va_pct == va) &
                       (profiles.expansion == exp)]
        ex = V.run_census(bars, sel)
        ex["bin_width"], ex["va_pct"], ex["expansion"] = bw, va, exp
        ex["construction"] = "bar_uniform"
        variants.append(ex)
        if (bw, va, exp) == (CANON["bin_width"], CANON["va_pct"], CANON["expansion"]):
            canon_ex = ex.copy()
        print(f"census bar bw={bw} va={va} {exp}: n={len(ex)}")

    sel_fp = profiles[profiles.construction == "footprint"]
    ex_fp = V.run_census(bars, sel_fp)
    ex_fp["bin_width"], ex_fp["va_pct"], ex_fp["expansion"] = (
        CANON["bin_width"], CANON["va_pct"], CANON["expansion"])
    ex_fp["construction"] = "footprint"
    variants.append(ex_fp)
    print(f"census footprint canonical: n={len(ex_fp)}")

    ex_all = pd.concat(variants, ignore_index=True)
    ex_all = ex_all.sort_values(
        ["construction", "bin_width", "va_pct", "expansion", "session_date",
         "side", "excursion_start"], kind="mergesort").reset_index(drop=True)
    ex_all.to_parquet("output/vp_census/excursions_variants.parquet", index=False)

    canon_ex["era"] = np.where(pd.to_datetime(canon_ex.session_date)
                               <= pd.Timestamp("2025-12-31"), "2025H2", "2026H1")
    canon_ex = canon_ex.sort_values(["session_date", "side", "excursion_start"],
                                    kind="mergesort").reset_index(drop=True)
    canon_ex.to_parquet("output/vp_census/excursions.parquet", index=False)
    print(f"canonical census: n={len(canon_ex)} "
          f"({canon_ex.groupby('era').size().to_dict()})")

    # ---- section 2.4 construction gate ------------------------------------
    pb = profiles[(profiles.construction == "bar_uniform") &
                  (profiles.bin_width == CANON["bin_width"]) &
                  (profiles.va_pct == CANON["va_pct"]) &
                  (profiles.expansion == CANON["expansion"]) &
                  (profiles.profile_status == "OK")][
        ["session_date", "vah", "val", "poc"]]
    pf = prof_fp[prof_fp.profile_status == "OK"][
        ["session_date", "vah", "val", "poc"]]
    both = pb.merge(pf, on="session_date", suffixes=("_bar", "_fp"))
    both["d_vah"] = (both.vah_bar - both.vah_fp).abs()
    both["d_val"] = (both.val_bar - both.val_fp).abs()
    both["d_poc"] = (both.poc_bar - both.poc_fp).abs()

    b = canon_ex[["session_date", "side", "excursion_start", "failed_15"]]
    f = ex_fp[["session_date", "side", "excursion_start", "failed_15"]]
    merged = b.merge(f, on=["session_date", "side", "excursion_start"],
                     how="outer", suffixes=("_bar", "_fp"), indicator=True)
    # tolerant match for near-miss starts (<=5 min) among the unmatched
    onlyb = merged[merged._merge == "left_only"]
    onlyf = merged[merged._merge == "right_only"]
    matched = merged[merged._merge == "both"].copy()
    extra_pairs = []
    used_f = set()
    for _, r in onlyb.iterrows():
        cand = onlyf[(onlyf.session_date == r.session_date) &
                     (onlyf.side == r.side) &
                     (~onlyf.index.isin(used_f))]
        if len(cand):
            dt = (cand.excursion_start - r.excursion_start).abs()
            j = dt.idxmin()
            if dt.loc[j] <= pd.Timedelta(minutes=5):
                used_f.add(j)
                extra_pairs.append((r.failed_15_bar, onlyf.loc[j, "failed_15_fp"]))
    n_exact = len(matched)
    flips_exact = int((matched.failed_15_bar != matched.failed_15_fp).sum())
    flips_near = sum(1 for a, bb in extra_pairs if a != bb)
    n_near = len(extra_pairs)
    n_unmatched = int(len(onlyb) - n_near + len(onlyf) - len(used_f))
    n_union = int(len(merged))
    flip_rate_matched = (flips_exact + flips_near) / max(n_exact + n_near, 1)
    conservative = (flips_exact + flips_near + n_unmatched) / max(n_union, 1)

    gate = pd.DataFrame([
        dict(metric="n_sessions_both_ok", value=len(both)),
        dict(metric="median_abs_dVAH_pts", value=both.d_vah.median()),
        dict(metric="p90_abs_dVAH_pts", value=both.d_vah.quantile(0.9)),
        dict(metric="median_abs_dVAL_pts", value=both.d_val.median()),
        dict(metric="p90_abs_dVAL_pts", value=both.d_val.quantile(0.9)),
        dict(metric="median_abs_dPOC_pts", value=both.d_poc.median()),
        dict(metric="p90_abs_dPOC_pts", value=both.d_poc.quantile(0.9)),
        dict(metric="n_excursions_union", value=n_union),
        dict(metric="n_matched_exact", value=n_exact),
        dict(metric="n_matched_near5min", value=n_near),
        dict(metric="n_unmatched", value=n_unmatched),
        dict(metric="label_flips_matched", value=flips_exact + flips_near),
        dict(metric="flip_rate_matched_K15", value=flip_rate_matched),
        dict(metric="flip_rate_conservative_K15", value=conservative),
    ])
    gate.to_csv("output/vp_census/construction_gate.csv", index=False)
    print(gate.to_string(index=False))
    verdict = "PASS" if flip_rate_matched <= 0.05 else "FAIL"
    print(f"SECTION 2.4 GATE (matched flip rate {flip_rate_matched:.4f} "
          f"vs 0.05): {verdict}; conservative incl. existence mismatch: "
          f"{conservative:.4f}")

    pd.DataFrame(ledger).to_csv("output/vp_census/trial_ledger.csv", index=False)

    # poc stability across bins (section 2.5)
    p025 = profiles[(profiles.construction == "bar_uniform") &
                    (profiles.bin_width == 0.25) & (profiles.va_pct == 0.70) &
                    (profiles.expansion == "paired") &
                    (profiles.profile_status == "OK")][["session_date", "poc"]]
    p200 = profiles[(profiles.construction == "bar_uniform") &
                    (profiles.bin_width == 2.0) & (profiles.va_pct == 0.70) &
                    (profiles.expansion == "paired") &
                    (profiles.profile_status == "OK")][["session_date", "poc"]]
    pj = p025.merge(p200, on="session_date", suffixes=("_025", "_200"))
    pj["d"] = (pj.poc_025 - pj.poc_200).abs()
    unstable = pj[pj.d > 3.0]["session_date"].tolist()
    frac = len(unstable) / max(len(pj), 1)
    print(f"POC instability (0.25 vs 2.0 > 3pts): {len(unstable)}/{len(pj)} "
          f"= {frac:.3f}  (flag threshold 0.20)")
    pd.Series(sorted(map(str, unstable))).to_csv(
        "output/vp_census/poc_unstable_sessions.csv", index=False, header=["session_date"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
