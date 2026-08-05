#!/usr/bin/env python3
"""STAGE 3 — CONFLUENCE SCAN. Hypothesis-GENERATING only. Nothing here is a finding.

⚠️ THE ENTIRE OWNED SPAN THROUGH 2026-07-15 IS IN-SAMPLE. Every number this file produces is
IN-SAMPLE by construction and is not evidence of anything. The output is a shortlist of
PRE-REGISTERED HYPOTHESES for future data, and a count of how many comparisons were scanned.

THE QUESTION: do any 2-condition confluence stacks discriminate outcomes WITHIN our existing
event streams? Not "do they make money" — discrimination within a stream, including streams whose
base rate is negative. A null base is a clean test bed.

RULES, fixed before running:
  * base events: EXISTING detectors only, reused as event generators. No new detectors.
  * stacks of AT MOST TWO conditions.
  * thresholds ONLY at the 25th / 50th / 75th percentile of each feature's own distribution
    within each stream. No threshold search beyond those three.
  * every comparison scanned is COUNTED. That count is tonight's ledger N and goes in the
    headline. There are no unscanned-but-considered comparisons.
  * the identical search is run on MATCHED RANDOM CONTROLS (outcomes permuted within stream,
    which breaks any feature-outcome link while preserving the outcome distribution, the event
    count, the clustering and the search width). Every effect is reported as a PERCENTILE of
    that null. Raw p-values without it are banned.

MINIMUM SUBSET SIZE. A condition that selects 3 events can post any expectancy at all. Subsets
below MIN_N events or MIN_SESS sessions are not scannable and are excluded from the count — they
were never comparisons, so counting them would inflate N dishonestly.

    python -m scripts.confluence_scan
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MIN_N, MIN_SESS = 25, 20
PCTS = (25, 50, 75)
COST_USD, PT = 25.0, 20.0
NY = "America/New_York"
NULL_REPS = 400
RNG = np.random.default_rng(20260808)

CTX_FEATURES = ["entry_min_into_window", "atr_pct", "htf_aligned", "dist_to_level_R",
                "news_day", "risk_pts", "direction_long"]


# ------------------------------------------------------------------ event streams
def load_streams() -> dict[str, pd.DataFrame]:
    """Every existing event stream in the repo, reused as an event generator."""
    out = {}
    for p in sorted((ROOT / "research/_shared/sweep-logs").glob("*.csv")):
        d = pd.read_csv(p)
        out[p.stem] = d
    ash = ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-raw-trades.csv"
    if ash.exists():
        out["ash-unicorn-sb"] = pd.read_csv(ash)
    rem = ROOT / "research/zxcked/strategies/zxck-remaining-raw-trades.csv"
    if rem.exists():
        d = pd.read_csv(rem)
        for c in d.card.unique():
            out[c] = d[d.card == c].copy()
    for nm, p in (("zxck-wick-ce", "research/zxcked/strategies/zxck-wick-ce-raw-trades.csv"),
                  ("zxck-10am-keyopen", "research/zxcked/strategies/zxck-10am-keyopen-raw-trades.csv"),
                  ("orb-fvg-nyopen", "research/orb-fvg/strategies/orb-fvg-nyopen-raw-trades.csv")):
        f = ROOT / p
        if not f.exists():
            continue
        d = pd.read_csv(f)
        if "taken" in d:
            d = d[d.taken == "y"]
        if "arm_brk" in d:                       # orb: the locked primary arm only
            d = d[(d.arm_brk == "close") & (d.arm_entry == "retrace") & (d.arm_stop == "fvg")]
        out[nm] = d.copy()
    return {k: v for k, v in out.items() if len(v) >= MIN_N and "R" in v}


# ------------------------------------------------------------------ flow features on events
def attach_flow(streams: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Compute the Stage-2 library on every event. Proofs already passed in test_flow_features."""
    from scripts.flow_features import REGISTRY, FeatureInput, compute
    from scripts.footprint_clean import minute_frame, price_frame
    from scripts.nya_sb01_feasibility import load_bars

    fpm = minute_frame(clean=True)
    fpp = price_frame().set_index("ts")[["price", "volume", "side"]]
    bars = load_bars().set_index("ts")[["open", "high", "low", "close"]]
    names = [n for n, f in REGISTRY.items() if n not in
             ("participation_to_touch", "disp_delta_magnitude")]   # need a displacement leg

    for key, d in streams.items():
        if "time" not in d or "date" not in d:
            continue
        ts = pd.to_datetime(d.date.astype(str) + " " + d.time.astype(str), errors="coerce")
        ts = ts.dt.tz_localize(NY, ambiguous="NaT", nonexistent="NaT")
        vals = {n: [] for n in names}
        for i, (t, side) in enumerate(zip(ts, np.where(d.direction.to_numpy() == "long", 1, -1))):
            if t is pd.NaT or t != t:
                for n in names:
                    vals[n].append(np.nan)
                continue
            lo, hi = t.normalize(), t + pd.Timedelta(hours=4)
            x = FeatureInput(day=str(t.date()), entry_ts=t, cut=t - pd.Timedelta(minutes=1),
                             side=int(side), sess_start=t.normalize() + pd.Timedelta(hours=8),
                             disp_start=None, disp_end=None,
                             bars=bars[(bars.index >= lo) & (bars.index <= hi)],
                             fpm=fpm[(fpm.index >= lo) & (fpm.index <= hi)],
                             fpp=fpp[(fpp.index >= lo) & (fpp.index <= hi)])
            for n in names:
                vals[n].append(compute(n, x))
        for n in names:
            d[n] = vals[n]
    return streams


# ------------------------------------------------------------------ the scan
def conditions(d: pd.DataFrame, feats: list[str]):
    """Boolean condition matrix at fixed percentiles. Returns (matrix, labels)."""
    cols, labs = [], []
    for f in feats:
        v = pd.to_numeric(d[f], errors="coerce").to_numpy(dtype=float)
        ok = np.isfinite(v)
        if ok.sum() < MIN_N:
            continue
        for p in PCTS:
            thr = np.nanpercentile(v[ok], p)
            for sgn, lab in ((1, ">"), (-1, "<=")):
                m = (v > thr) if sgn > 0 else (v <= thr)
                m = m & ok
                if m.sum() < MIN_N:
                    continue
                cols.append(m); labs.append(f"{f}{lab}p{p}")
    return (np.array(cols).T if cols else np.zeros((len(d), 0), bool)), labs


def scan_stream(d: pd.DataFrame, R: np.ndarray, cost: np.ndarray, sess: np.ndarray,
                feats: list[str]):
    """All 1- and 2-condition subsets. Returns (labels, improvement, n, nsess, mask matrix)."""
    C, labs = conditions(d, feats)
    if not len(labs):
        return [], np.array([]), np.array([]), np.array([]), C
    base = float((R - cost).mean())
    cols, names = [], []
    for i in range(len(labs)):
        cols.append(C[:, i]); names.append(labs[i])
    for i, j in itertools.combinations(range(len(labs)), 2):
        if labs[i].split(">")[0].split("<=")[0] == labs[j].split(">")[0].split("<=")[0]:
            continue                                   # same feature -> not a confluence
        m = C[:, i] & C[:, j]
        if m.sum() < MIN_N:
            continue
        cols.append(m); names.append(f"{labs[i]} AND {labs[j]}")
    if not cols:
        return [], np.array([]), np.array([]), np.array([]), C
    M = np.array(cols).T
    n = M.sum(axis=0)
    ns = np.array([len(np.unique(sess[M[:, k]])) for k in range(M.shape[1])])
    keep = (n >= MIN_N) & (ns >= MIN_SESS)
    M, names = M[:, keep], [names[k] for k in np.where(keep)[0]]
    n, ns = n[keep], ns[keep]
    if not len(names):
        return [], np.array([]), np.array([]), np.array([]), C
    net = R - cost
    imp = (M.T @ net) / n - base
    return names, imp, n, ns, M


def null_best(M: np.ndarray, R: np.ndarray, cost: np.ndarray, reps: int) -> np.ndarray:
    """Best improvement under PERMUTED outcomes, same search width. The matched control."""
    net = R - cost
    n = M.sum(axis=0)
    base = float(net.mean())
    out = np.empty(reps)
    for r in range(reps):
        p = RNG.permutation(net)
        out[r] = float(np.max((M.T @ p) / n - base))
    return out


def main() -> None:
    print("STAGE 3 — CONFLUENCE SCAN. IN-SAMPLE BY CONSTRUCTION. NOTHING HERE IS A FINDING.\n")
    streams = attach_flow(load_streams())
    from scripts.flow_features import REGISTRY
    flow = [n for n in REGISTRY if n not in ("participation_to_touch", "disp_delta_magnitude")]

    total, rows, nulls = 0, [], {}
    for key, d in sorted(streams.items()):
        feats = [f for f in flow + CTX_FEATURES if f in d]
        if not feats:
            continue
        R = pd.to_numeric(d.R, errors="coerce").to_numpy(dtype=float)
        rp = pd.to_numeric(d.get("risk_pts", pd.Series(np.nan, index=d.index)),
                           errors="coerce").to_numpy(dtype=float)
        cost = np.where(np.isfinite(rp) & (rp > 0), COST_USD / (rp * PT), 0.0)
        ok = np.isfinite(R)
        if ok.sum() < MIN_N:
            continue
        d2 = d[ok].reset_index(drop=True)
        R, cost = R[ok], cost[ok]
        sess = d2.date.to_numpy()
        names, imp, n, ns, _ = scan_stream(d2, R, cost, sess, feats)
        if not len(names):
            continue
        total += len(names)
        M = _mask_matrix(d2, feats, names)
        nulls[key] = null_best(M, R, cost, NULL_REPS)
        base = float((R - cost).mean())
        for k in range(len(names)):
            pct = float((nulls[key] < imp[k]).mean())
            rows.append({"stream": key, "stack": names[k], "n": int(n[k]), "sess": int(ns[k]),
                         "base_exp": base, "subset_exp": base + imp[k], "improvement": imp[k],
                         "null_pct": pct})
        print(f"  {key:<34}{len(names):>7} comparisons   base exp {base:>+7.3f}"
              f"   null best-of p95 {np.percentile(nulls[key],95):+.3f}")

    res = pd.DataFrame(rows).sort_values("null_pct", ascending=False)
    out = ROOT / "research/_shared/confluence-scan-2026-08-08.csv"
    res.to_csv(out, index=False)
    print(f"\n{'='*90}\nTOTAL COMPARISONS SCANNED (tonight's ledger N): {total:,}\n{'='*90}")
    print(f"streams {len(nulls)}   null reps per stream {NULL_REPS}")
    print(f"\nTop 15 by NOISE-FLOOR PERCENTILE (in-sample; percentile is the only honest column):")
    cols = ["stream", "stack", "n", "sess", "base_exp", "subset_exp", "improvement", "null_pct"]
    print(res.head(15)[cols].to_string(index=False,
          formatters={"base_exp": "{:+.3f}".format, "subset_exp": "{:+.3f}".format,
                      "improvement": "{:+.3f}".format, "null_pct": "{:.4f}".format}))
    hi = res[res.null_pct >= 0.99]
    print(f"\ncomparisons at or above the 99th percentile of their own null: {len(hi)} of {total:,}")
    print(f"expected by chance at 1%: ~{total*0.01:,.0f}")
    print(f"-> {'MORE than chance' if len(hi) > total*0.01 else 'NO MORE than chance'}")
    print(f"\nwritten -> {out}")


def _mask_matrix(d, feats, names):
    C, labs = conditions(d, feats)
    idx = {l: i for i, l in enumerate(labs)}
    cols = []
    for nm in names:
        if " AND " in nm:
            a, b = nm.split(" AND ")
            cols.append(C[:, idx[a]] & C[:, idx[b]])
        else:
            cols.append(C[:, idx[nm]])
    return np.array(cols).T


if __name__ == "__main__":
    main()
