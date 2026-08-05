#!/usr/bin/env python3
"""STAGE 4 — PRE-REGISTERED OUT-OF-SAMPLE TEST of H2 and H1-magnitude.

NOT a filter search. Two hypotheses, fixed before these trades existed, tested exactly as
written. No feature scan, no threshold tuning, no additional order-flow tools.

PRE-REGISTRATION: research/ash10hazard/strategies/ash-unicorn-sb-forward-protocol.md (2026-08-07)
  H2  retrace_ratio orders win < loss < break-even   (a STALL predictor, not a loss predictor)
  H1  winners carry LARGER F1_disp_delta than losers (magnitude, not sign)
Both were generated on ash-unicorn-sb's 29 trades and have never been evaluated anywhere else.
zxck-10am-keyopen's decidable flow-covered trades are a different trader, a different setup and
identical feature definitions — the first genuine out-of-sample sample available.

The F1 SIGN test is NOT run. It was settled as vacuous (it removed 0 of 29) because delta agrees
with a structurally-defined directional move by construction.

--------------------------------- FLOW FRAME: LOCAL, NOT SHARED --------------------------------
output/fp_minutes.parquet is missing January 2026 (60 rows vs 27-31k/month) even though
footprint_jan2026.parquet holds 1,542,534 rows for it. That artifact is tracked, shared with the
canon work, and has no in-repo builder, so it is NOT regenerated here. Instead this script builds
its own per-minute frame from the raw footprint files, and the derivation was VERIFIED against
fp_minutes on 31,271 minutes of July 2025:

    fp.a = footprint side A      fp.b = footprint side B
    fp.vol   = A + B             max|diff| 0.0
    fp.delta = B - A             max|diff| 0.0     <- exact

⚠️ NOTE FOR WHOEVER OWNS scripts/build_cvd_minute.py: its docstring says "Side 'A' = ask-lift
(buy aggressor)... delta = A - B". That is INVERTED relative to fp_minutes. The empirical check
settles it in fp_minutes' favour: fp.delta correlates +0.645 with the minute's (close-open) over
369,045 minutes and agrees in sign on 75.5% of non-zero minutes, so delta = B - A is the
buy-positive convention and side B is the buy aggressor. Not fixed here — out of scope.

    python -m scripts.f2_oos_test
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import load_bars  # noqa: E402
from scripts.zxck_keyopen_baseline import (  # noqa: E402
    FOMC, MANIP_PTS, OPEN_MIN, RTH_END, STOP_PTS, WIN_END, calendar,
)

PHI = NormalDist()
COST_USD, PT = 25.0, 20.0
SPAN_LO, SPAN_HI = "2025-06-01", "2026-07-15"


# ------------------------------------------------------------------ flow frame
def flow_frame() -> pd.DataFrame:
    parts = []
    for p in sorted((ROOT / "data/reference/cvd").glob("footprint_*.parquet")):
        if "holdout" in p.name:                      # sealed 2023/24 — never opened
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        d["ts_minute"] = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert("America/New_York")
        parts.append(d)
    raw = pd.concat(parts, ignore_index=True)
    g = raw.groupby(["ts_minute", "side"]).volume.sum().unstack("side").fillna(0.0)
    for c in ("A", "B"):
        if c not in g:
            g[c] = 0.0
    out = pd.DataFrame({"vol": g.A + g.B, "delta": g.B - g.A}, index=g.index)  # verified mapping
    return out[~out.index.duplicated(keep="first")].sort_index()


# ------------------------------------------------------------------ zxck trades + flow
def zxck_trades(bars: pd.DataFrame, fp: pd.DataFrame) -> pd.DataFrame:
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    rows = []
    for day, g in bars.groupby("day", sort=False):
        if day in fomc:
            continue
        g = g.reset_index(drop=True)
        o = g[g.mins == OPEN_MIN]
        if o.empty:
            continue
        P = float(o.open.iloc[0])
        w = g[(g.mins >= OPEN_MIN) & (g.mins <= WIN_END)].reset_index(drop=True)
        if len(w) < 5:
            continue
        up, dn = w.high >= P + MANIP_PTS, w.low <= P - MANIP_PTS
        if not up.any() and not dn.any():
            continue
        iu = int(up.idxmax()) if up.any() else 10 ** 9
        idn = int(dn.idxmax()) if dn.any() else 10 ** 9
        if iu == idn:                                 # ambiguous direction — EXCLUDED per brief
            continue
        m, side = min(iu, idn), (+1 if idn < iu else -1)
        post = w.iloc[m + 1:]
        clo = (post.close > P) if side > 0 else (post.close < P)
        if not len(post) or not clo.any():
            continue
        ci = int(clo.idxmax())
        fwd = w.iloc[ci + 1:]
        hit = (fwd.low <= P) if side > 0 else (fwd.high >= P)
        if not len(fwd) or not hit.any():
            continue
        t = int(hit.idxmax())
        entry = P
        stop, target, half = entry - side * STOP_PTS, entry + side * 2 * STOP_PTS, \
            entry + side * STOP_PTS
        # SAME-BAR FILL-AND-STOP (fixed 2026-08-07, mirrors zxck_keyopen_baseline.py).
        fb = w.iloc[t]
        same_bar_stop = (fb.low <= stop) if side > 0 else (fb.high >= stop)
        tail = pd.concat([w.iloc[t + 1:], g[(g.mins > WIN_END) & (g.mins <= RTH_END)]])
        cur, be, out = stop, False, None
        if same_bar_stop:
            out = -1.0
        for _, bar in (tail.iterrows() if out is None else iter([])):
            if side > 0:
                if bar.low <= cur:
                    out = 0.0 if be else -1.0; break
                if bar.high >= target:
                    out = 2.0; break
                if not be and bar.high >= half:
                    cur, be = entry, True
            else:
                if bar.high >= cur:
                    out = 0.0 if be else -1.0; break
                if bar.low <= target:
                    out = 2.0; break
                if not be and bar.low <= half:
                    cur, be = entry, True
        if out is None:
            last = float(tail.close.iloc[-1]) if len(tail) else entry
            out = float(side * (last - entry) / STOP_PTS)

        # ---- flow, identical definitions to ash-unicorn-sb, minutes <= entry only ----
        t0, t1, te = w.ts.iloc[m], w.ts.iloc[ci], w.ts.iloc[t]
        disp = fp[(fp.index >= t0) & (fp.index <= t1)]
        ret = fp[(fp.index > t1) & (fp.index <= te)]
        sess = fp[(fp.index >= w.ts.iloc[0]) & (fp.index <= te)].vol
        assert not len(disp) or disp.index.max() <= te
        assert not len(ret) or ret.index.max() <= te
        med = float(sess.median()) if len(sess) else np.nan
        f1 = float(disp.delta.sum()) * side / med if (len(disp) and med) else np.nan
        dv, rv = float(disp.vol.sum()), float(ret.vol.sum())
        f2 = rv / dv if dv > 0 and len(ret) else np.nan
        rows.append({"date": day, "src": "zxck-10am-keyopen", "R": round(out, 3),
                     "disp_start": t0, "disp_end": t1, "entry_ts": te,
                     "risk_pts": STOP_PTS,
                     "outcome": "win" if out >= 2 else ("BE" if out == 0 else
                                ("loss" if out <= -1 else "timeout")),
                     "F1_disp_delta": f1, "F2_retrace_ratio": f2})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ stats
def cliffs(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x) < 2 or len(y) < 2:
        return np.nan
    gt = sum(int((xi > y).sum()) for xi in x)
    lt = sum(int((xi < y).sum()) for xi in x)
    return (gt - lt) / (len(x) * len(y))


def mannwhitney_one_sided(x, y):
    """H: x stochastically GREATER than y."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x) < 3 or len(y) < 3:
        return np.nan
    r = pd.Series(np.concatenate([x, y])).rank().to_numpy()
    u = r[:len(x)].sum() - len(x) * (len(x) + 1) / 2
    mu = len(x) * len(y) / 2
    sd = np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
    return float(1 - PHI.cdf((u - mu) / sd)) if sd > 0 else np.nan


def jonckheere(groups):
    """One-sided JT trend test for the PRE-REGISTERED ordering groups[0] < groups[1] < ..."""
    gs = [np.asarray(g, float) for g in groups]
    gs = [g[~np.isnan(g)] for g in gs]
    if min(len(g) for g in gs) < 3:
        return np.nan, np.nan
    J = 0.0
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            for xi in gs[i]:
                J += float((xi < gs[j]).sum()) + 0.5 * float((xi == gs[j]).sum())
    ns = np.array([len(g) for g in gs], float)
    N = ns.sum()
    mu = (N ** 2 - (ns ** 2).sum()) / 4
    var = (N ** 2 * (2 * N + 3) - (ns ** 2 * (2 * ns + 3)).sum()) / 72
    z = (J - mu) / np.sqrt(var)
    return float(z), float(1 - PHI.cdf(z))


def summarise(d, label):
    if not len(d):
        return {"arm": label, "n": 0}
    eq = d.R.cumsum()
    c = float((COST_USD / (d.risk_pts * PT)).mean())
    return {"arm": label, "n": len(d), "win%": 100 * (d.R >= 2).mean(),
            "avgR": d.R.mean(), "exp": d.R.mean() - c, "totR": d.R.sum(),
            "maxDD": float((eq.cummax() - eq).max())}


def main() -> None:
    bars = load_bars()
    bars = bars[(bars.day >= SPAN_LO) & (bars.day <= SPAN_HI)]
    fp = flow_frame()
    z = zxck_trades(bars, fp)

    a = pd.read_csv(ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-orderflow-trades.csv")
    a = a.dropna(subset=["F1_disp_delta", "F2_retrace_ratio"]).assign(src="ash-unicorn-sb")

    prim = z.dropna(subset=["F1_disp_delta", "F2_retrace_ratio"])
    pool = pd.concat([prim, a[prim.columns.intersection(a.columns)]], ignore_index=True)

    print("STAGE 4 — PRE-REGISTERED OUT-OF-SAMPLE TEST. Not a filter search.\n")
    print(f"flow frame rebuilt locally from raw footprint (incl. January 2026): "
          f"{len(fp):,} minutes, {fp.index.min():%Y-%m-%d} -> {fp.index.max():%Y-%m-%d}")
    print(f"\nzxck-10am-keyopen decidable trades in span : {len(z)}")
    print(f"   of which flow computed  -> PRIMARY n    : {len(prim)}")
    print(f"ash-unicorn-sb flow-covered (CONTAMINATED)  : {len(a)}")
    print(f"   POOLED SECONDARY n                       : {len(pool)}")
    print("   ^ pooled is NOT an independent test: H2 and H1 were BORN on the ash 29.\n")

    tests = []
    for lab, d in (("PRIMARY (out-of-sample)", prim), ("SECONDARY (contaminated pool)", pool)):
        W = d[d.R >= 2].F2_retrace_ratio
        L = d[d.R <= -1].F2_retrace_ratio
        B = d[d.R == 0].F2_retrace_ratio
        print("=" * 78)
        print(f"H2 — {lab}   retrace_ratio, pre-registered ordering win < loss < break-even")
        print("=" * 78)
        for n, s in (("win", W), ("loss", L), ("break-even", B)):
            print(f"   {n:<12} n={len(s):>4}   median {np.nanmedian(s):.3f}")
        z_jt, p_jt = jonckheere([W, L, B])
        obs = np.nanmedian(W) < np.nanmedian(L) < np.nanmedian(B)
        print(f"   ordering observed as pre-registered? {'YES' if obs else 'NO'}")
        print(f"   Jonckheere-Terpstra  z = {z_jt:+.3f}   one-sided p = {p_jt:.4f}")
        if lab.startswith("PRIMARY"):
            tests.append(("H2 ordering", p_jt))
            wl = mannwhitney_one_sided(L, W)   # H: losers > winners on F2
            print(f"   (win vs loss alone, one-sided: p = {wl:.4f}, "
                  f"Cliff's d = {cliffs(W, L):+.3f})")
        print()

    print("=" * 78)
    print("H2 — the ORIGINAL FILTER FORM at its ORIGINAL threshold (retrace_ratio < 1.0)")
    print("=" * 78)
    kept, rej = prim[prim.F2_retrace_ratio < 1.0], prim[prim.F2_retrace_ratio >= 1.0]
    t = pd.DataFrame([summarise(prim, "unfiltered (primary)"),
                      summarise(kept, "KEPT   retrace_ratio < 1.0"),
                      summarise(rej, "REJECTED retrace_ratio >= 1.0")])
    print(t.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    print("   threshold NOT tuned. If 1.0 is wrong here, that is a finding.\n")

    print("=" * 78)
    print("H1-magnitude — PRIMARY   winners carry LARGER F1_disp_delta than losers")
    print("=" * 78)
    W1, L1, B1 = (prim[prim.R >= 2].F1_disp_delta, prim[prim.R <= -1].F1_disp_delta,
                  prim[prim.R == 0].F1_disp_delta)
    for n, s in (("win", W1), ("loss", L1), ("break-even", B1)):
        print(f"   {n:<12} n={len(s):>4}   median {np.nanmedian(s):.3f}")
    p_h1 = mannwhitney_one_sided(W1, L1)
    print(f"   direction observed as pre-registered (win > loss)? "
          f"{'YES' if np.nanmedian(W1) > np.nanmedian(L1) else 'NO'}")
    print(f"   Mann-Whitney one-sided p = {p_h1:.4f}   Cliff's d = {cliffs(W1, L1):+.3f}")
    tests.append(("H1 magnitude", p_h1))

    print("\n" + "=" * 78)
    print("HOLM CORRECTION across the two pre-registered tests")
    print("=" * 78)
    ts = sorted(tests, key=lambda x: (np.inf if x[1] != x[1] else x[1]))
    m = len(ts)
    for i, (name, p) in enumerate(ts):
        ph = min(1.0, p * (m - i)) if p == p else np.nan
        print(f"   {name:<16} p_raw {p:.4f}   p_holm {ph:.4f}   "
              f"{'SURVIVES' if ph <= 0.05 else 'does not survive'}")

    nw, nl = int((prim.R >= 2).sum()), int((prim.R <= -1).sum())
    za, zb = PHI.inv_cdf(0.95), PHI.inv_cdf(0.80)
    d_min = (za + zb) * np.sqrt(1 / nw + 1 / nl)
    print(f"\nPOWER — primary sample, {nw} winners vs {nl} losers")
    print(f"   smallest Cohen's d detectable at 80% power, one-sided a=0.05: {d_min:.2f}")
    print(f"   (in-sample effects being tested: H2 Cliff's d -0.635, H1 +0.596)")

    out = ROOT / "research/_shared/f2-oos-trades.csv"
    pool.to_csv(out, index=False)
    print(f"\npooled log -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
