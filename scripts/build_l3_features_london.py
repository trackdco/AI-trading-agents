#!/usr/bin/env python3
"""L3 Stage A — LONDON: the order-flow/geometry feature matrix for every L2 outcome.

REUSES THE FEATURE CODE VERBATIM. Nothing here computes a feature. `london_matrix.py`'s loop
and `london_depth.py`'s depth_at carry the as-of discipline (every window ends strictly before
the fill minute; depth reads the last snapshot at/before it), and a faithful-to-spec rewrite is
exactly how the champion-vs-canon divergence happened — 14% shared trades. This script only:

  1. shapes the L2 outcomes into the substrate frame those loops expect,
  2. dedups so identical inputs are featured once,
  3. drives the two existing scripts through their new path overrides,
  4. joins the features back onto the per-trigger L2 rows,
  5. gates the result against the cached london_matrix.

DEDUP-THEN-JOIN. The feature loop reads only (day, fill, exit, direction, entry) off each row.
Several census triggers routinely share all five — MTF siblings resolving to the same level,
or the same limit re-detected minutes apart. Featuring the unique set once and left-joining
back guarantees identical inputs get identical features by construction, keeps the per-trigger
key (`ts`) intact, and cuts the work substantially.

WHAT THE GATE PROVES (--gate): on fills matched to the cached output/london_matrix.parquet,
every shared feature column must agree to 1e-6.

  MATCH KEY: (day, fill-minute, direction, ENTRY). Entry is in the key deliberately — same-
  minute sibling triggers share a fill minute with different limits, and a join without entry
  compares different trades. That cost the NY rebuild half a day (burn list #4).

  EXCLUDED, with reasons: `trigdens_30` counts triggers in the prior 30 min and is fed from the
  L0 census rather than the old trigger CSV, so it is EXPECTED to differ — the census is the
  honest parity-gated stream and includes January 2026, which the cache never had. `hold_min`,
  `win` and the passthrough trade columns are outcomes, not features, and they legitimately
  differ because L2 runs with v8_be_at_open=False and no 22pt distance cancel.

  COVERAGE CAVEAT: the cached matrix is 749 rows across BOTH books (E3 and E4) built from the
  2-capped substrate. L2 is uncapped and E3-only, so only a subset matches. The gate reports
  the matched count and fails on any disagreement within it; a small matched set weakens the
  evidence and is printed rather than hidden.

    python -m scripts.build_l3_features_london --span fit
    python -m scripts.build_l3_features_london --span fit --gate
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
CACHED_MATRIX = ROOT / "output/london_matrix.parquet"

# Columns that are inputs/outcomes rather than computed features.
PASSTHRU = {"day", "book", "fill", "exit", "direction", "entry", "stop", "exit_price",
            "exit_reason", "dollars", "pattern", "tf", "wgroup", "yr", "risk", "ts",
            "hold_min", "win", "mo", "win_et"}
GATE_EXCLUDE = {"trigdens_30"}          # census-fed, expected to differ — see docstring


def substrate_frame(oc: pd.DataFrame) -> pd.DataFrame:
    """L2 outcomes -> the columns london_matrix's loop and london_depth expect."""
    f = pd.to_datetime(oc.fill_ts, format="mixed", utc=True).dt.tz_convert(NY)
    x = pd.to_datetime(oc.exit_ts, format="mixed", utc=True).dt.tz_convert(NY)
    return pd.DataFrame({
        "day": oc.day.values,
        "book": "E3",
        # ISO STRINGS WITH OFFSET, matching london_substrate's `str(r.fill_ts)`. The loops do
        # `pd.Timestamp(t.fill).tz_convert(NY)`, which needs tz-aware input — and `.values` on
        # a tz-aware Series silently strips the tz to naive UTC.
        "fill": f.astype(str).values,
        "exit": x.astype(str).values,
        "direction": oc.direction.values,
        "entry": oc.entry.astype(float).values,
        "stop": oc.stop.astype(float).values,
        "exit_price": oc.exit_price.astype(float).values,
        "exit_reason": oc.exit_reason.values,
        "dollars": oc.dollars_1lot.astype(float).values,
        "pattern": oc.pattern.values,
        "tf": oc.tf.values,
        "wgroup": np.where(oc.dst_shifted.values, "LDN_DST", "LDN"),
        "yr": pd.to_datetime(oc.day).dt.year.values,
        "risk": oc.risk.astype(float).values,
    })


def key(df: pd.DataFrame, fill_col: str = "fill", full: bool = True) -> pd.Series:
    """The trade identity key.

    (day, fill-minute, direction, entry) is NOT sufficient: the determinism audit
    (docs/LONDON-AUDIT-DETERMINISM.md) found 581 tied groups / 1,321 rows sharing those four
    fields whose `stop` differs in 325 groups, `exit` in 222 and `risk` in 335. So `stop` and
    `exit` are part of identity — without them `drop_duplicates` picks an arbitrary sibling
    whose outcome differs, and only an accident of which columns PASSTHRU excludes kept that
    from changing the book.

    `full=False` yields the legacy 4-field form, used ONLY for the gate join against the cached
    london_matrix, which predates this fix and carries no `stop` column.
    """
    f = pd.to_datetime(df[fill_col], format="mixed", utc=True).dt.tz_convert(NY).dt.floor("min")
    k = (df.day.astype(str) + "|" + f.dt.strftime("%H:%M") + "|"
         + df.direction.astype(str) + "|" + df.entry.astype(float).round(2).astype(str))
    if not full:
        return k
    x = pd.to_datetime(df["exit"], format="mixed", utc=True).dt.tz_convert(NY)
    return (k + "|" + df.stop.astype(float).round(2).astype(str)
            + "|" + x.dt.strftime("%Y-%m-%dT%H:%M:%S"))


def build(span: str, procs_note: str = "") -> Path:
    oc = pd.read_parquet(ROOT / f"output/l2_outcomes_london_{span}.parquet")
    oc = oc[oc.status == "outcome"].reset_index(drop=True)
    print(f"L2 outcomes ({span}): {len(oc)} rows on {oc.day.nunique()} days")

    S = substrate_frame(oc)
    # `ts` (the per-trigger key) must exist on S BEFORE the dedup: it is the tiebreak that makes
    # survivor selection deterministic, and it also has to survive the merge back.
    S["ts"] = oc.ts.values
    S["_k"] = key(S)
    # ORDERED dedup, mergesort: which row survives must be DEFINED, not whatever order the
    # input happened to arrive in. Ties in _k now imply identical inputs AND identical outcome,
    # so the choice is immaterial — but it is pinned anyway so a future column change cannot
    # silently reintroduce order-dependence.
    uniq = (S.sort_values(["_k", "ts"], kind="mergesort")
            .drop_duplicates("_k", keep="first").reset_index(drop=True))
    print(f"unique feature inputs: {len(uniq)} "
          f"({len(S) - len(uniq)} duplicate (day,fill,dir,entry) rows collapsed)")

    tmp_sub = ROOT / f"output/_l3_london_sub_{span}.parquet"
    tmp_mat = ROOT / f"output/_l3_london_matrix_{span}.parquet"
    uniq.drop(columns=["_k"]).to_parquet(tmp_sub, index=False)

    census = ROOT / f"output/l0_triggers_london_{span}.parquet"
    for cmd in (
        [sys.executable, "-m", "scripts.london_matrix", "--span", span,
         "--sub", str(tmp_sub), "--trigs", str(census), "--out", str(tmp_mat)],
        [sys.executable, "-m", "scripts.london_depth", "--span", span,
         "--matrix", str(tmp_mat)],
    ):
        print(f"\n$ {' '.join(Path(c).name if '/' in c else c for c in cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode:
            raise SystemExit(f"stage failed: {cmd[2]}")

    feats = pd.read_parquet(tmp_mat)
    feats["_k"] = key(feats)
    fcols = [c for c in feats.columns if c not in PASSTHRU and c != "_k"]
    out = S.merge(feats[["_k", *fcols]], on="_k", how="left").drop(columns=["_k"])
    out.insert(0, "ts", out.pop("ts"))             # per-trigger key survives the dedup
    for c in ("kind", "htf_flag", "confluence_count", "target", "R"):
        out[c] = oc[c].values

    dest = ROOT / f"output/l3_features_london_{span}.parquet"
    out.to_parquet(dest, index=False)
    print(f"\nwrote {dest.relative_to(ROOT)} — {len(out)} rows x {len(fcols)} features")
    dep = out.dep_thick.notna() if "dep_thick" in out else pd.Series(False, index=out.index)
    print(f"depth coverage: {int(dep.sum())}/{len(out)} ({dep.mean() * 100:.0f}%) — "
          f"days without a depth file carry NaN dep_* and are excluded downstream")
    return dest


def gate(span: str) -> None:
    dest = ROOT / f"output/l3_features_london_{span}.parquet"
    if not dest.exists():
        raise SystemExit(f"{dest.relative_to(ROOT)} missing — run without --gate first")
    if not CACHED_MATRIX.exists():
        raise SystemExit("cached london_matrix.parquet missing — nothing to gate against")

    new = pd.read_parquet(dest)
    old = pd.read_parquet(CACHED_MATRIX)
    old = old[old.book == "E3"] if "book" in old else old
    # legacy 4-field key: the cached matrix predates the identity fix
    new["_k"], old["_k"] = key(new, full=False), key(old, full=False)

    shared = [c for c in new.columns
              if c in old.columns and c not in PASSTHRU and c not in GATE_EXCLUDE
              and pd.api.types.is_numeric_dtype(new[c]) and pd.api.types.is_numeric_dtype(old[c])]
    m = new.merge(old[["_k", *shared]], on="_k", suffixes=("", "_old"))
    print(f"cached matrix: {len(old)} E3 rows | rebuild: {len(new)} rows | "
          f"MATCHED on (day, fill-min, direction, entry): {len(m)}")
    if not len(m):
        raise SystemExit("GATE INCONCLUSIVE — no matched fills; check the join key")
    print(f"comparing {len(shared)} shared feature columns to 1e-6 "
          f"(excluded: {sorted(GATE_EXCLUDE)})\n")

    bad = []
    for c in shared:
        a, b = m[c].astype(float), m[f"{c}_old"].astype(float)
        both_nan = a.isna() & b.isna()
        diff = (~both_nan) & ~np.isclose(a, b, rtol=0, atol=1e-6, equal_nan=True)
        if diff.any():
            bad.append((c, int(diff.sum()), float((a - b).abs().max())))
    for c, n, mx in bad:
        print(f"  MISMATCH {c}: {n}/{len(m)} rows differ, max |delta| {mx:.6g}")
    if bad:
        raise SystemExit(f"GATE FAILED — {len(bad)} of {len(shared)} feature columns diverge "
                         f"from the cached matrix on matched fills")
    print(f"gate OK — all {len(shared)} shared feature columns reproduce the cached "
          f"london_matrix to 1e-6 on {len(m)} matched fills")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout"], default="fit")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    if a.gate:
        return gate(a.span)
    build(a.span)


if __name__ == "__main__":
    main()
