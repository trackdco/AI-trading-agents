"""Reporting layer. Computes the full metric set the user asked for and renders the
breakdowns, monthly split, CVD-mode comparison, and an equity-curve chart."""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]


def metrics(T: pd.DataFrame) -> dict:
    """Core metrics for a per-trade frame. Money is per-micro dollars (the `dollars` column)."""
    if not len(T):
        return dict(n=0)
    wins = T[T.net_pts > 0]; losses = T[T.net_pts <= 0]
    gross_w = wins.net_pts.sum(); gross_l = -losses.net_pts.sum()
    pf = gross_w / gross_l if gross_l > 0 else np.inf
    eq = T.sort_values("ts").dollars.cumsum()
    dd = float((eq - eq.cummax()).min()) if len(eq) else 0.0
    # max consecutive losses
    mcl = cur = 0
    for x in T.sort_values("ts").net_pts:
        cur = cur + 1 if x <= 0 else 0
        mcl = max(mcl, cur)
    return dict(
        n=len(T), win=round((T.net_pts > 0).mean() * 100, 1),
        avg_win_pts=round(wins.net_pts.mean(), 1) if len(wins) else 0.0,
        avg_loss_pts=round(losses.net_pts.mean(), 1) if len(losses) else 0.0,
        avg_win_usd=round(wins.dollars.mean(), 0) if len(wins) else 0.0,
        avg_loss_usd=round(losses.dollars.mean(), 0) if len(losses) else 0.0,
        pf=round(pf, 2) if np.isfinite(pf) else 99.0,
        exp_pts=round(T.net_pts.mean(), 2), exp_usd=round(T.dollars.mean(), 1),
        net_usd=round(T.dollars.sum(), 0), net_pts=round(T.net_pts.sum(), 0),
        maxdd_usd=round(dd, 0), max_consec_loss=mcl,
        rr_planned=round(T.rr_planned.mean(), 2), rr_real=round(T.rr_real.mean(), 2),
        liq_override_pct=round(T.liq_override.mean() * 100, 0),
        months_green=sum(T[T.mo == m].dollars.sum() > 0 for m in MONTHS if (T.mo == m).any()),
        months=T.mo.nunique(),
    )


def line(m: dict, label: str) -> str:
    if m.get("n", 0) == 0:
        return f"  {label:30s} 0t"
    return (f"  {label:30s} {m['n']:4d}t  win {m['win']:4.1f}%  PF {m['pf']:5.2f}  "
            f"exp {m['exp_pts']:+6.2f}pt/{m['exp_usd']:+6.0f}$  net ${m['net_usd']:+9,.0f}  "
            f"DD ${m['maxdd_usd']:+8,.0f}  mcl {m['max_consec_loss']:2d}  "
            f"RR {m['rr_planned']:.2f}->{m['rr_real']:+.2f}  m+ {m['months_green']}/{m['months']}")


def breakdown(T: pd.DataFrame, by: str, order=None) -> str:
    keys = order if order is not None else sorted(T[by].dropna().unique())
    rows = [line(metrics(T[T[by] == k]), f"{by}={k}") for k in keys]
    return "\n".join(rows)


def stop_distribution(T: pd.DataFrame) -> str:
    if not len(T):
        return "  (no trades)"
    q = T.stop_pts.quantile([0.25, 0.5, 0.75, 0.9, 1.0]).round(1)
    tiers = T.tier.value_counts().to_dict()
    return (f"  stop pts  p25 {q[0.25]}  p50 {q[0.5]}  p75 {q[0.75]}  p90 {q[0.9]}  max {q[1.0]}\n"
            f"  sizing tier fired: " + ", ".join(f"{k}:{v}t" for k, v in tiers.items())
            + f"   (max stop taken {T.stop_pts.max():.1f}pt / hard cap 70)")


def cvd_mode_table(sims: pd.DataFrame) -> str:
    """CVD-mode a–d comparison at a fixed TF/min_conf/target (spec §CVD-mode comparison)."""
    lines = ["  mode  trades  win%   PF   exp$/t   net$      DD$     m+"]
    for mode in ["a", "b", "c", "d"]:
        r = sims[sims.cvd_mode == mode]
        if not len(r):
            lines.append(f"  {mode}     (none)"); continue
        r = r.iloc[0]
        lines.append(f"  {mode}    {r['n']:5d}  {r['win']:4.1f}  {r['pf']:5.2f}  "
                     f"{r['exp_usd']:+7.0f}  {r['net_usd']:+9,.0f}  {r['maxdd_usd']:+8,.0f}  "
                     f"{r['months_green']}/{r['months']}")
    return "\n".join(lines)


def equity_curve(T: pd.DataFrame, path: str, title: str):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    if not len(T):
        return None
    T = T.sort_values("ts")
    eq = T.dollars.cumsum().values
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(len(eq)), eq, lw=1.3)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title(title); ax.set_xlabel("trade #"); ax.set_ylabel("cum $ (per-micro sizing)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def monthly_split(T: pd.DataFrame) -> str:
    rows = []
    for m in MONTHS:
        sub = T[T.mo == m]
        if not len(sub):
            continue
        mm = metrics(sub)
        rows.append(f"  {m}  {mm['n']:3d}t  win {mm['win']:4.1f}%  PF {mm['pf']:5.2f}  "
                    f"net ${mm['net_usd']:+8,.0f}")
    return "\n".join(rows) if rows else "  (no trades)"


def full_report(T: pd.DataFrame, cfg: dict, title: str) -> str:
    m = metrics(T)
    buckets = [b["name"] for b in cfg["reporting"]["entry_time_buckets"]]

    def bucket_of(hhmm):
        for b in cfg["reporting"]["entry_time_buckets"]:
            if b["start"] <= hhmm <= b["end"]:
                return b["name"]
        return "other"
    Tb = T.copy()
    if len(Tb):
        Tb["bucket"] = Tb.entry_min.map(bucket_of)
    s = [f"=== {title} ===", line(m, "OVERALL"), "",
         "by setup:", breakdown(T, "setup", ["A", "B", "B2"]), "",
         "by direction:", breakdown(T, "dir", ["long", "short"]), "",
         "by entry-time bucket:",
         "\n".join(line(metrics(Tb[Tb.bucket == b]), f"bucket={b}") for b in buckets) if len(Tb) else "  (none)",
         "", "stop-size distribution / sizing tiers:", stop_distribution(T),
         "", "monthly split:", monthly_split(T)]
    return "\n".join(s)
