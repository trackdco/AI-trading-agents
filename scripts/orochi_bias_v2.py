#!/usr/bin/env python3
"""OROCHI BIAS v2 — AT SPEC (2026-09-10). Supersedes the S41 census.

Angus, correctly: "their shit works, ur application of it doesnt."
The S41 census deviated from the taught method in four material ways. Each
is corrected here, against the repo's own RESPEC (research/transcripts/
orochi/RESPEC-as-taught-2026-08-05.md) and the frozen composite definition
already in the repo (scripts/nya_composites.py, docs/PREREG-failed-auction).

  DEVIATION            S41 (wrong)              v2 (as taught)
  reference level      prior-day VA             multi-day COMPOSITE balance
                                                (frozen def) + developing WEEKLY
  acceptance clock     3 x 1-min closes (~3m)   N x 30-min closes (1h / 2h / 3h)
  forward horizon      <= 60 min                2h / 4h / 8h / 1 session / 1.5
  condition timeframe  1-min                    30-min structure

Still leak-proof by construction: state at bar t uses only bars <= t; the
measurement is close(t) -> close(t+h) on a continuous minute index. No
orders, no fills. Windows straddling weekend gaps are dropped (elapsed
wall-clock must be <= 1.5x nominal), so a "1.5 day hold" is a real one.

Composite (frozen, from nya_composites.py): a maximal run of >=2 consecutive
sessions whose RTH value areas overlap pairwise; edges = min VAL / max VAH of
members so far; strictly prior sessions only.

Episode-level throughout (one observation per state ENTRY), because S41
proved per-minute means overstate by ~7x through persistence.

    python -m scripts.orochi_bias_v2 --instrument nq
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                       # noqa: E402
from scripts.agent_context import volume_profile             # noqa: E402
import scripts.pd_va_backtest as BT                          # noqa: E402

HORIZ_H = (2.0, 4.0, 8.0, 23.0, 34.5)     # hours: his hours-to-1.5-days
ACCEPT_BARS = (2, 4, 6)                    # 30-min closes: 1h / 2h / 3h


def rth_value_areas(bars, days, bin_w):
    """One 70%-value area per RTH session (09:30-16:00) — the AMT day."""
    out = []
    for d in days:
        s = pd.Timestamp(f"{d} 09:30", tz=OB.NY)
        e = pd.Timestamp(f"{d} 16:00", tz=OB.NY)
        seg = bars[(bars.index >= s) & (bars.index < e)]
        if len(seg) < 200:
            continue
        poc, val, vah = volume_profile(seg, bin_w=bin_w)
        out.append(dict(day=d, poc=poc, val=val, vah=vah))
    return out


def composites(vas):
    """Frozen definition, causal: state as of each day's open."""
    comp = {}
    run = []
    for r in vas:
        if run:
            comp[r["day"]] = (len(run), min(m["val"] for m in run),
                              max(m["vah"] for m in run))
        if run:
            c_val = min(m["val"] for m in run)
            c_vah = max(m["vah"] for m in run)
            run = run + [r] if (r["val"] <= c_vah and r["vah"] >= c_val) else [r]
        else:
            run = [r]
    return comp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", choices=("nq", "nq20a"), default="nq")
    a = ap.parse_args()
    inst = BT.INSTRUMENTS[a.instrument]
    if inst["bars"]:
        b = pd.read_parquet(ROOT / inst["bars"])
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
        bars = b.set_index("mi").sort_index()[
            ["open", "high", "low", "close", "volume"]]
    else:
        bars = OB.get_bars()
    days = OB.all_session_days(bars)
    vas = rth_value_areas(bars, days, inst["bin_w"])
    comp = composites(vas)
    print(f"{a.instrument}: {len(vas)} RTH value areas, "
          f"composite(age>=2) on {sum(1 for v in comp.values() if v[0]>=2)} days",
          flush=True)

    # continuous 30-min structure over the whole tape
    c30 = bars.resample("30min").agg({"open": "first", "high": "max",
                                      "low": "min", "close": "last"}).dropna()
    t30 = c30.index
    cl30 = c30.close.to_numpy(float)
    n30 = len(cl30)
    # map each 30m bar to its session day (18:00 anchor)
    sday = pd.Series(t30, index=t30).apply(
        lambda ts: (ts - pd.Timedelta(hours=18)).strftime("%Y-%m-%d")).to_numpy()

    edges = np.full((n30, 2), np.nan)      # composite val, vah live that day
    for i, d in enumerate(sday):
        c = comp.get(d)
        if c and c[0] >= 2:
            edges[i] = (c[1], c[2])

    # forward moves on the 30m close series, weekend-gap guarded
    tvals = t30.view("int64").astype(float) / 3.6e12   # hours
    fwd = {}
    for H in HORIZ_H:
        f = np.full(n30, np.nan)
        j = np.searchsorted(tvals, tvals + H)
        ok = (j < n30)
        idx = np.flatnonzero(ok)
        elapsed = np.where(ok, tvals[np.clip(j, 0, n30 - 1)] - tvals, np.nan)
        good = idx[(elapsed[idx] <= H * 1.5)]
        f[good] = cl30[j[good]] - cl30[good]
        fwd[H] = f

    res = defaultdict(list)
    for N in ACCEPT_BARS:
        # acceptance OUTSIDE the composite for N consecutive 30m closes,
        # then the first close back INSIDE = his failed auction / 80% rule
        above = cl30 > edges[:, 1]
        below = cl30 < edges[:, 0]
        live = np.isfinite(edges[:, 0])

        def runs(mask):
            out = np.zeros(n30, bool)
            c = 0
            for i in range(n30):
                c = c + 1 if mask[i] else 0
                out[i] = c >= N
            return out
        acc_up, acc_dn = runs(above), runs(below)
        seen_up = seen_dn = False
        for i in range(n30):
            if not live[i]:
                seen_up = seen_dn = False
                continue
            if acc_up[i]:
                seen_up = True
            elif seen_up and cl30[i] <= edges[i, 1]:
                res[(f"ACC_BACK_DN_n{N}",)].append((sday[i], i, -1))
                seen_up = False
            if acc_dn[i]:
                seen_dn = True
            elif seen_dn and cl30[i] >= edges[i, 0]:
                res[(f"ACC_BACK_UP_n{N}",)].append((sday[i], i, +1))
                seen_dn = False
        # plain location vs composite, entries only
        for nm, mask, d in (("BELOW_COMP", below & live, +1),
                            ("ABOVE_COMP", above & live, -1)):
            hit = np.flatnonzero(mask)
            if len(hit) == 0:
                continue
            ent = hit[np.concatenate(([True], np.diff(hit) > 1))]
            if N == ACCEPT_BARS[0]:
                for i in ent:
                    res[(nm,)].append((sday[i], i, d))

    out = {"states": {k[0]: [(d, int(i), int(sg)) for d, i, sg in v]
                      for k, v in res.items()},
           "fwd": {str(H): [None if not np.isfinite(x) else float(x)
                            for x in fwd[H]] for H in HORIZ_H},
           "base": {str(H): [float(np.nanmean(fwd[H])), float(np.nanstd(fwd[H])),
                             float(np.nanmean((fwd[H] > 0).astype(float)))]
                    for H in HORIZ_H}}
    p = ROOT / f"output/analysis/orochi_v2_{a.instrument}.json"
    p.write_text(json.dumps(out))
    print("wrote", p, {k: len(v) for k, v in out["states"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
