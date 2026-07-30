#!/usr/bin/env python3
"""LONDON loser stats — the full profile of the losing trades on the current stack.

THE ASK (Brake, 2026-07-30): "stats of the losers, because I wanna see if there are any
patterns." Book = the working stack: cut@09:30 + score-0 veto + one position at a time
(110 trades). Prior art: docs/LONDON-LOSS-ANATOMY.md profiled the 81 losers of the old
187-trade book and found ONE Bonferroni-clearing discriminator (entry-vs-VWAP
dir-adjusted, AUC 0.628, p=0.003) plus two nulls (day character, duration borderline).
This doc re-profiles on the current stack and re-tests every discriminator with the
same discipline: era split + worst-of-K permutation on the AUC. DESCRIPTIVE unless a
row clears the charge; the S3 mild VWAP cut stays parked either way (profit trap).

    python -m scripts.london_loser_stats
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd, write
from scripts.london_conviction import lonmins, signed
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book

SEED = 20260730
N_PERM = 5000

FEATURES = [  # (column, signed-into-trade-frame) — sweep coverage rules apply
    ("ent_vs_vwap_sd_dir", False), ("room_ahead", False), ("stop_frac", False),
    ("on_range", False), ("on_extreme_age", False), ("risk", False),
    ("dep_thick", False), ("dep_resist", False), ("dep_support", False),
    ("dep_spread", False), ("dep_imb", True), ("dep_sup_m_res", True),
    ("trigdens_30", False), ("lvl_churn_30", False), ("rng_30", False),
    ("vwap_slope_30", True), ("vwap_cross_30", False), ("netpath_30", True),
    ("indec_30", False), ("wicky_10", False), ("bbw_state", False),
    ("confluence_count", False), ("conv", False),
]


def auc_rank(x: np.ndarray, y: np.ndarray) -> float:
    """P(loser value > winner value) via ranks; y=1 for losers."""
    order = pd.Series(x).rank().values
    n1, n0 = int(y.sum()), int((~y.astype(bool)).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    return (order[y.astype(bool)].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main() -> None:
    rng = np.random.default_rng(SEED + 5)
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    b["mins"] = lonmins(b.fill)
    b["bucket"] = pd.cut(b.mins, [480, 510, 540, 570, 600], right=False,
                         labels=["08:00-08:30", "08:30-09:00", "09:00-09:30",
                                 "09:30-10:00"])
    b["hold_min"] = ((pd.to_datetime(b.exit_ts, utc=True)
                      - pd.to_datetime(b.fill_ts, utc=True)).dt.total_seconds() / 60)
    lose = b.R <= 0
    Ls, Ws = b[lose], b[~lose]

    L = [f"# London loser stats — the {len(Ls)} losers of the working stack "
         f"(cut@09:30 + veto + one-at-a-time, {len(b)} trades)\n",
         "\n**FIT ONLY. Sealed untouched. Descriptive unless a row clears its charge; "
         "patterns found here are declared priors, not rules.**\n"]

    # ---------------- 1. what a loss looks like
    L.append(f"\n## 1. What a loss looks like\n\n"
             f"- {len(Ls)} losers / {len(b)} trades ({len(Ls) / len(b) * 100:.0f}%). "
             f"Exit reasons: {Ls.exit_reason.value_counts().to_dict()}\n"
             f"- Loss size: mean {Ls.R.mean():+.2f}R / ${Ls.dollars.mean():+,.0f}, "
             f"worst {Ls.R.min():+.2f}R / ${Ls.dollars.min():+,.0f}. "
             f"{int((Ls.R <= -0.9).sum())} of {len(Ls)} are full stops.\n"
             f"- Speed: median loser dies in {Ls.hold_min.median():.0f} min vs "
             f"{Ws.hold_min.median():.0f} min for winners; "
             f"{int((Ls.hold_min <= 3).sum())}/{len(Ls)} losers are gone within 3 "
             f"minutes of fill.\n"
             f"- Eras: 2025 {int((Ls.era == '2025').sum())} losers of "
             f"{int((b.era == '2025').sum())} trades; 2026 "
             f"{int((Ls.era == '2026').sum())} of {int((b.era == '2026').sum())}.\n")

    # ---------------- 2. where they live (categorical slices)
    L.append("\n## 2. Where the losers live (share of each cell that loses)\n")
    for cat in ("bucket", "tf", "pattern", "direction", "htf_flag"):
        L.append(f"\n**{cat}**\n\n| value | trades | losers | loss rate | cell net |\n"
                 "|---|---|---|---|---|\n")
        for v, g in b.groupby(cat, observed=True):
            if not len(g):
                continue
            gl = g[g.R <= 0]
            L.append(f"| {v} | {len(g)} | {len(gl)} | {len(gl) / len(g) * 100:.0f}% | "
                     f"${g.dollars.sum():+,.0f} |\n")
    both = ((b.W == 1) & (b.FAR == 1))
    L.append(f"\n**wall**: both {int((~(b[both].R > 0)).sum())}/{int(both.sum())} lose "
             f"({(b[both].R <= 0).mean() * 100:.0f}%) vs exactly-one "
             f"{int((b[~both].R <= 0).sum())}/{int((~both).sum())} "
             f"({(b[~both].R <= 0).mean() * 100:.0f}%)\n")

    # ---------------- 3. clustering
    seq = b.sort_values(["day", "fill_ts"], kind="mergesort").R.le(0).astype(int).values
    runs, cur = [], 0
    for v in seq:
        cur = cur + 1 if v else 0
        if cur:
            runs.append(cur)
    max_run = max(runs) if runs else 0
    d = b.groupby("day").dollars.sum()
    red = d[d < 0]
    L.append(f"\n## 3. Clustering\n\n"
             f"- Longest losing streak (chronological): {max_run} trades.\n"
             f"- Red days: {len(red)}/{len(d)} ({len(red) / len(d) * 100:.0f}%), mean "
             f"red day ${red.mean():+,.0f}, worst ${red.min():+,.0f}. Multi-loss days "
             f"(2+ losers): {int((b.groupby('day').apply(lambda g: (g.R <= 0).sum(), include_groups=False) >= 2).sum())}.\n"
             f"- Month with most losers: "
             f"{Ls.day.str[:7].value_counts().idxmax()} "
             f"({Ls.day.str[:7].value_counts().max()}).\n")

    # ---------------- 4. discriminators, charged
    usable = [(f, s) for f, s in FEATURES if b[f].notna().mean() >= 0.95]
    y = lose.values
    aucs = []
    for f, s in usable:
        v = signed(b, f, s)
        aucs.append((f, auc_rank(v, y)))
    # worst-of-K permutation: shuffle loser labels within era
    dev_obs = {f: abs(a - 0.5) for f, a in aucs}
    idx25 = np.where(b.era.values == "2025")[0]
    idx26 = np.where(b.era.values == "2026")[0]
    vals = {f: signed(b, f, s) for f, s in usable}
    null = np.empty(N_PERM)
    yp = y.copy()
    for i in range(N_PERM):
        yp[idx25] = y[idx25][rng.permutation(len(idx25))]
        yp[idx26] = y[idx26][rng.permutation(len(idx26))]
        null[i] = max(abs(auc_rank(vals[f], yp) - 0.5) for f, _ in usable)
    L.append(f"\n## 4. Loser-vs-winner discriminators ({len(usable)} declared "
             f"features; AUC = P(loser value > winner value); charged "
             f"worst-of-{len(usable)})\n\n"
             "| feature | AUC | 2025 AUC | 2026 AUC | p(worst-of-K) | consistent? |\n"
             "|---|---|---|---|---|---|\n")
    rows = []
    for f, s in usable:
        v = vals[f]
        a = auc_rank(v, y)
        a25 = auc_rank(v[idx25], y[idx25])
        a26 = auc_rank(v[idx26], y[idx26])
        p = float((null >= abs(a - 0.5)).mean())
        cons = (a25 - 0.5) * (a26 - 0.5) > 0
        rows.append((f, a, a25, a26, p, cons))
    rows.sort(key=lambda r: -abs(r[1] - 0.5))
    for f, a, a25, a26, p, cons in rows[:12]:
        L.append(f"| {f} | {a:.3f} | {a25:.3f} | {a26:.3f} | {p:.3f} | "
                 f"{'YES' if cons else 'no'} |\n")
    L.append(f"\n(Top 12 of {len(usable)} by |AUC-0.5| shown; all {len(usable)} were "
             "in the null. AUC > 0.5 = losers have MORE of it; < 0.5 = losers have "
             "less. 0.5 = no information.)\n")
    write("LONDON-LOSER-STATS.md", "".join(L))


if __name__ == "__main__":
    main()
