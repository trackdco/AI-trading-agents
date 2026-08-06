#!/usr/bin/env python3
"""Layer conditioning onto the FVT continuation baseline, with PBO/DSR guarding every pick.

ANGUS 2026-08-06: *"i think we can test variables on this baseline and add other bits and
pieces of knowledge to make this strategy better."*

WHY THIS BASELINE AND NOT THE CANON. The canon sat on a frontier
(research/findings/the-geometry-frontier.md): corr(win rate, average win size) = -0.855,
because every variable we recorded was a proxy for how far the target sat from the stop, so
filtering only slid the same trade along a fixed trade-off and 1 of 93 buckets cleared zero.

FVT is not on that frontier, and the reason is structural: **the target is a fixed 1.5R off a
fixed-point stop, so target distance is no longer a function of the setup.** Conditioning can
therefore move expectancy here in a way it provably could not there. That is the whole case
for this file.

THE BASELINE, fixed before any conditioner is tried:
    continuation phase only, FIRST attempt per window, all five windows, ATR(1m) tiers.
    +0.19 pt/trade, 2.72/day, 43.4% win, 39.1% target-hit, 49.8% green days.

Reversion is excluded because it loses in all five sessions in both eras -- that is a finding,
not a filter choice.

THE GUARD. Every conditioner is one more thing tried, and the whole point of the harness is
that trying many things inflates the best one. So the full conditioner set is scored as ONE
family: CSCV/PBO over all cells, and a Deflated Sharpe on the winner that knows how many
trials produced it. A cell that beats baseline but fails DSR is noise, and this file says so
rather than reporting the cell.

    python -m scripts.fvt_condition
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402
from scripts.build_htf_features import build as htf_build  # noqa: E402
from src.validation.overfit import cscv_pbo, deflated_sharpe, sharpe, walk_forward  # noqa: E402

NY = "America/New_York"
MIN_N = 150


def baseline(b: pd.DataFrame) -> pd.DataFrame:
    F.WINDOWS = F.WINDOW_SETS["all"]
    T = F.run(b, 1)
    T = T.sort_values(["day", "win", "hm"])
    T["attempt"] = T.groupby(["day", "win"]).cumcount() + 1
    T = T[(T.attempt == 1) & (T.phase == "cont")].copy()
    T["era"] = T.day.str[:4]
    T["ts"] = pd.to_datetime(T.day) + pd.to_timedelta(T.hm, unit="m")
    T["ts"] = T.ts.dt.tz_localize(NY, ambiguous=True, nonexistent="shift_forward")
    T["direction"] = np.where(T["dir"] == 1, "long", "short")
    return T


def enrich(T: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    # daily regime, built from strictly prior sessions
    C = pd.read_parquet(ROOT / "output/daily_context.parquet")
    T = T.merge(C, on="day", how="left")

    # HTF features (premium/discount, midnight-open side, day's move already spent)
    H = htf_build(T[["ts", "day", "direction"]].copy())
    T = T.merge(H, on="ts", how="left")

    # JJ'S OWN STATED GATE, never yet tested: "If trading Asia session, only trade it if it
    # provides a surge in volume/volatility." Measured on the window BEFORE the entry so it is
    # causal -- volume and range of the 30 minutes preceding, against their own 20-day median
    # for that same clock window.
    b = b.copy()
    key = list(zip(b.day, b.hm))
    vol = dict(zip(key, b.volume))
    rng = dict(zip(key, b.high - b.low))
    days = sorted(b.day.unique())
    dpos = {d: i for i, d in enumerate(days)}

    def pre(dayv, hmv, src):
        return np.nansum([src.get((dayv, hmv - k), np.nan) for k in range(1, 31)])

    surge_v, surge_r = [], []
    for d, h in zip(T.day, T.hm):
        i = dpos.get(d, 0)
        hist = days[max(0, i - 20):i]
        v_now, r_now = pre(d, h, vol), pre(d, h, rng)
        v_hist = [pre(x, h, vol) for x in hist]
        r_hist = [pre(x, h, rng) for x in hist]
        mv = np.nanmedian(v_hist) if v_hist else np.nan
        mr = np.nanmedian(r_hist) if r_hist else np.nan
        surge_v.append(v_now / mv if mv and np.isfinite(mv) and mv > 0 else np.nan)
        surge_r.append(r_now / mr if mr and np.isfinite(mr) and mr > 0 else np.nan)
    T["surge_vol"], T["surge_rng"] = surge_v, surge_r

    # setup-shape features, all known at entry
    T["dist_fv"] = np.nan
    T["risk_pts"] = T.risk
    T["mins_in"] = T.hm - T.win.map({w[0]: w[1] for w in F.WINDOW_SETS["all"]})
    return T


def main() -> int:
    b = F.load()
    b = b[b.day >= "2025-01-01"]
    T = enrich(baseline(b), b)
    days = sorted(b.day.unique())
    di = {d: i for i, d in enumerate(days)}
    base_net = T.pts.mean()
    print(f"baseline: {len(T):,} trades, {len(T)/len(days):.2f}/day, "
          f"{base_net:+.3f} pt, {(T.pts>0).mean():.1%} win, {(T.why=='target').mean():.1%} target")

    NUM = [c for c in ["surge_vol", "surge_rng", "risk_pts", "mins_in", "trend_atr", "trend_pct",
                       "atr_pct", "vix_pct", "range_atr", "va_overlap", "poc_streak",
                       "close_pos", "pd_position", "pd_edge", "vs_mid_norm"]
           if c in T.columns and T[c].notna().sum() > 400]
    CAT = [c for c in ["win", "trend_state", "vol_state", "balance_state", "direction",
                       "fades_open", "already_moved", "opposite_taken"] if c in T.columns]

    cells, names = [], []

    def add(mask, nm):
        X = T[mask]
        if len(X) < MIN_N:
            return
        v = np.zeros(len(days))
        for d, g in X.groupby("day"):
            v[di[d]] = g.pts.sum()
        cells.append(v)
        names.append(nm)
        rows.append({"cell": nm, "n": len(X), "per_day": len(X) / len(days),
                     "net": X.pts.mean(), "win": (X.pts > 0).mean(),
                     "tgt": (X.why == "target").mean(),
                     "e25": X[X.era == "2025"].pts.mean() if (X.era == "2025").sum() > 50 else np.nan,
                     "e26": X[X.era == "2026"].pts.mean() if (X.era == "2026").sum() > 50 else np.nan})

    rows = []
    add(np.ones(len(T), bool), "BASELINE (no condition)")
    for c in CAT:
        for k in T[c].dropna().unique():
            add(T[c] == k, f"{c}={k}")
    for c in NUM:
        q = T[c].quantile([1 / 3, 2 / 3]).values
        add(T[c] <= q[0], f"{c}=LOW")
        add((T[c] > q[0]) & (T[c] < q[1]), f"{c}=MID")
        add(T[c] >= q[1], f"{c}=HIGH")

    R = pd.DataFrame(rows).sort_values("net", ascending=False)
    X = np.column_stack(cells)
    srs = np.array([sharpe(X[:, i]) for i in range(X.shape[1])])
    best = int(np.nanargmax(srs))

    L = ["# FVT conditioning — layering knowledge onto the continuation baseline", "",
         "Baseline: continuation only, first attempt per window, all five windows.",
         f"**{len(T):,} trades, {len(T)/len(days):.2f}/day, {base_net:+.3f} pt/trade.**", "",
         "The canon could not be improved by conditioning because every variable there was a",
         "proxy for target distance (corr(win rate, win size) = −0.855). FVT's target is a",
         "fixed 1.5R off a fixed-point stop, so that frontier does not apply here.", "",
         f"**{len(names)} cells tested — scored as ONE family, because trying many things is",
         "exactly what inflates the best one.**", "",
         "| cell | n | /day | net pt | win% | target% | 2025 | 2026 |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in R.head(22).iterrows():
        L.append(f"| `{r.cell}` | {r.n:,.0f} | {r.per_day:.2f} | **{r.net:+.2f}** | "
                 f"{r['win']:.1%} | {r.tgt:.1%} | "
                 + " | ".join(f"{r[k]:+.2f}" if np.isfinite(r[k]) else "—" for k in ("e25", "e26"))
                 + " |")

    p = cscv_pbo(X, S=16)
    d = deflated_sharpe(X[:, best], X.shape[1], srs)
    wf = walk_forward(X, train=120, test=20)
    L += ["", "---", "", "## The guard", "",
          f"Best by daily Sharpe: **`{names[best]}`**", "",
          "| test | value | bar | verdict |", "|---|---:|---|---|",
          f"| PBO | **{p['pbo']:.3f}** | < 0.10 | {'**PASS**' if p['pbo'] < 0.10 else '**FAIL**'} |",
          f"| Deflated Sharpe | **{d['dsr']:.4f}** | > 0.95 | "
          f"{'**PASS**' if d['dsr'] > 0.95 else '**FAIL**'} |",
          f"| observed Sharpe | {d['sharpe']:+.4f} | vs SR0 {d['sr0']:+.4f} on {d['n_trials']} trials | |",
          f"| walk-forward OOS | {wf['mean']:+.3f} pt/day | > 0 | "
          f"{'**PASS**' if wf['mean'] > 0 else '**FAIL**'} |", ""]
    ok = p["pbo"] < 0.10 and d["dsr"] > 0.95 and wf["mean"] > 0
    L += [("**A conditioner survives.** Take it to the sealed 2023/24 holdout next — and once,"
           " frozen." if ok else
           "**Nothing survives the guard.** Cells that beat baseline do not beat what the best "
           "of this many trials would produce by chance. Reporting the table above as leads, "
           "not findings — and specifically NOT taking any of them to the holdout, because "
           "spending the holdout on a cell that already failed DSR wastes the only clean test "
           "we have left."), ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_condition.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
