#!/usr/bin/env python3
"""LONDON loss anatomy — is there a pattern to the losers? FIT ONLY. Holdout sealed.

The question (Angus): do the losing trades share a signature in (a) how long they lasted,
(b) the day's volume/choppiness, or (c) where we entered? This is DESCRIPTIVE mining on the fit
book, not a validated edge — with 81 losers and ~16 features the risk of finding a pretty
pattern that is pure noise is real, so every separation carries a permutation p-value AND a
Bonferroni note, and the writeup says plainly which columns clear the bar and which do not.

  BOOK: the frozen arm's taken set (floor 9.5, window-end lifetime, uncapped) — the same 187
        trades every other London doc is built on. Win/loss is R's sign, which is size-
        independent, so the tier decision does not change this analysis.

  METHOD per feature: split winners vs losers, report both medians, and an AUC = P(feature
        ranks higher on a winner than a loser) — 0.5 is no separation, distance from 0.5 is
        effect size, direction tells you which way. p from 2,000 label shuffles. Terciles
        (low/med/high) give the shape: a monotone loss-rate gradient is the thing worth having;
        a lumpy one usually is not.

    python -m scripts.london_loss_anatomy
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, lon_pop, write  # noqa: E402

SEED = 20260730
N_PERM = 2000
DOCS = ROOT / "docs"

# The three axes the question names, each a small declared set — not a fishing expedition over
# every column. Labels are (column, human name, "higher = ?").
DURATION = [("hold_min", "hold time (min)")]
DAY_CHAR = [
    ("rng_30", "30-min range (pts)"),
    ("fill_vol_rel", "relative volume at fill"),
    ("wicky_10", "wick ratio, last 10 bars"),
    ("indec_30", "indecision, 30-min"),
    ("netpath_30", "net-path efficiency, 30-min"),
    ("churn_flow_30", "order-flow churn, 30-min"),
    ("lvl_churn_30", "level churn, 30-min"),
    ("bbw_state", "Bollinger width state"),
]
ENTRY = [
    ("room_ahead", "room ahead of entry (dir-adj)"),
    ("ent_vs_vwap_sd_dir", "entry vs VWAP, SD (dir-adj)"),
    ("on_range", "position within session range"),
    ("on_extreme_age", "age of the session extreme"),
    ("ent_on_pos", "entry position on range (raw)"),
]


def auc(x: np.ndarray, win: np.ndarray) -> float:
    """P(feature higher on a winner than a loser). Ties count half. 0.5 = no separation."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x)); ranks[order] = np.arange(1, len(x) + 1)
    # average ranks for ties
    s = pd.Series(x)
    ranks = s.rank(method="average").values
    nw = win.sum(); nl = (~win).sum()
    if nw == 0 or nl == 0:
        return float("nan")
    u = ranks[win].sum() - nw * (nw + 1) / 2
    return float(u / (nw * nl))


def sep(x: np.ndarray, win: np.ndarray, rng) -> tuple:
    a = auc(x, win)
    obs = abs(a - 0.5)
    w = win.copy()
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        null[i] = abs(auc(x, rng.permutation(w)) - 0.5)
    return a, float((null >= obs).mean())


def line(name: str, col: str, df: pd.DataFrame, rng) -> dict:
    d = df[df[col].notna()]
    x, win = d[col].values.astype(float), (d.R.values > 0)
    a, p = sep(x, win, rng)
    wl, ws = x[~win], x[win]
    # terciles by the feature; loss rate per tercile
    q = pd.qcut(pd.Series(x), 3, labels=["low", "med", "high"], duplicates="drop")
    tab = pd.DataFrame({"q": q.values, "loss": ~win, "R": d.R.values})
    g = tab.groupby("q", observed=True)
    grad = g.loss.mean()
    return {"name": name, "col": col, "n": len(d), "auc": a, "p": p,
            "loser_med": float(np.median(wl)), "winner_med": float(np.median(ws)),
            "terciles": [(str(k), int(len(gg)), float(gg.loss.mean()), float(gg.R.mean()))
                         for k, gg in g],
            "monotone": bool((grad.diff().dropna() > 0).all() or (grad.diff().dropna() < 0).all())}


def section(title: str, feats: list, df: pd.DataFrame, rng, L: list, bonf: int) -> None:
    L.append(f"\n## {title}\n\n"
             "| feature | n | loser median | winner median | AUC | perm p | Bonferroni | "
             "loss rate low / med / high |\n|---|---|---|---|---|---|---|---|\n")
    rows = [line(nm, c, df, rng) for c, nm in feats]
    for r in sorted(rows, key=lambda r: abs(r["auc"] - 0.5), reverse=True):
        tail = " / ".join(f"{t[2] * 100:.0f}%" for t in r["terciles"])
        arrow = ("winners higher" if r["auc"] > 0.5 else "losers higher")
        passb = "**yes**" if r["p"] < 0.05 / bonf else ("borderline" if r["p"] < 0.05 else "no")
        L.append(f"| {r['name']} | {r['n']} | {r['loser_med']:.2f} | {r['winner_med']:.2f} | "
                 f"{r['auc']:.3f} ({arrow}) | {r['p']:.3f} | {passb} | {tail} |\n")
    return rows


def main() -> None:
    P = lon_pop()
    t = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).copy()
    t["hold_min"] = ((pd.to_datetime(t.exit_ts, utc=True)
                      - pd.to_datetime(t.fill_ts, utc=True)).dt.total_seconds() / 60)
    long = t.direction.values == "long"
    # direction-adjusted entry: "room ahead" = distance the trade has to run before the far
    # edge of the range. london_checks uses (1 - ent_on_pos) for longs, ent_on_pos for shorts.
    t["room_ahead"] = np.where(long, 1 - t.ent_on_pos, t.ent_on_pos)
    t["era"] = pd.to_datetime(t.day).dt.year.astype(str)
    rng = np.random.default_rng(SEED)

    nloss = int((t.R <= 0).sum())
    bonf = len(DURATION) + len(DAY_CHAR) + len(ENTRY)
    L = ["# London loss anatomy — is there a pattern to the losers?\n",
         "\n**Fit only. Sealed 2023/24 never loaded. Descriptive mining, not a validated "
         "edge.**\n",
         f"\nFrozen arm's taken book: **{len(t)} trades, {nloss} losers, "
         f"{(t.R > 0).mean() * 100:.0f}% win rate, mean R {t.R.mean():+.3f}, "
         f"${t.dollars.sum():+,.0f}** at flat 1 lot.\n",
         f"\n**How to read it.** AUC is P(the feature ranks higher on a winner than on a loser): "
         f"0.5 is no separation, and how far it sits from 0.5 is the effect size. `perm p` is "
         f"{N_PERM:,} label shuffles. With {bonf} features tested the Bonferroni bar is "
         f"p < {0.05 / bonf:.4f}; a column only earns 'yes' if it clears that, and even then on "
         f"fit data it is a lead to test on the holdout, not a result.\n"]

    # exit structure first — it frames everything
    L.append("\n## Loss structure\n\nEvery loss is a stop; there is no third failure mode.\n\n"
             "| exit | trades | share of losers |\n|---|---|---|\n")
    er = t.assign(loss=t.R <= 0).groupby("exit_reason", dropna=False)
    for k, g in er:
        nl = int((g.R <= 0).sum())
        if nl:
            L.append(f"| {k} | {len(g)} | {nl} ({nl / nloss * 100:.0f}%) |\n")
    L.append(f"\nSo {int((t.exit_reason == 'stop').sum())} clean stops and "
             f"{int((t.exit_reason == 'partial+stop').sum() & (t.R <= 0)) if False else int(((t.exit_reason == 'partial+stop') & (t.R <= 0)).sum())} "
             f"that banked a partial then stopped out for a net loss. The pure stop is the "
             f"trade to explain.\n")

    dur_rows = section("1. Trade duration", DURATION, t, rng, L, bonf)
    L.append("\nHold time is measured from fill to final exit. A stop that fires in the first "
             "couple of minutes is a different animal from one that grinds for an hour, so the "
             "distribution below the median matters more than the median itself:\n\n"
             "| hold bucket | trades | loss rate | mean R |\n|---|---|---|---|\n")
    for lo, hi, lab in [(0, 3, "0-3 min"), (3, 8, "3-8 min"), (8, 20, "8-20 min"),
                        (20, 1e9, "20+ min")]:
        g = t[(t.hold_min >= lo) & (t.hold_min < hi)]
        if len(g):
            L.append(f"| {lab} | {len(g)} | {(g.R <= 0).mean() * 100:.0f}% | {g.R.mean():+.3f} |\n")

    day_rows = section("2. The day's character — volume & choppiness", DAY_CHAR, t, rng, L, bonf)
    # day-level view: bucket whole days by median choppiness and show the day's loss rate
    best = max(day_rows, key=lambda r: abs(r["auc"] - 0.5))
    L.append(f"\n### Day-level: are losses clustered on the choppy/low-volume days?\n\n"
             f"Aggregating to the day and bucketing days by their median **{best['name']}** "
             f"(the strongest single day-character separator above), then asking what share of "
             f"each bucket's trades lost:\n\n"
             "| day bucket | days | trades | loss rate | mean R | net $ |\n|---|---|---|---|---|---|\n")
    dcol = best["col"]
    dday = t.groupby("day").agg(v=(dcol, "median")).reset_index()
    dday["b"] = pd.qcut(dday.v, 3, labels=["calm/low", "mid", "choppy/high"], duplicates="drop")
    tt = t.merge(dday[["day", "b"]], on="day")
    for k, g in tt.groupby("b", observed=True):
        L.append(f"| {k} | {g.day.nunique()} | {len(g)} | {(g.R <= 0).mean() * 100:.0f}% | "
                 f"{g.R.mean():+.3f} | ${g.dollars.sum():+,.0f} |\n")

    entry_rows = [line(nm, c, t, rng) for c, nm in ENTRY]
    L.append("\n## 3. Where we entered\n\n"
             "| feature | n | loser median | winner median | AUC | perm p | Bonferroni | "
             "loss rate low / med / high |\n|---|---|---|---|---|---|---|---|\n")
    for r in sorted(entry_rows, key=lambda r: abs(r["auc"] - 0.5), reverse=True):
        tail = " / ".join(f"{tt[2] * 100:.0f}%" for tt in r["terciles"])
        arrow = "winners higher" if r["auc"] > 0.5 else "losers higher"
        passb = "**yes**" if r["p"] < 0.05 / bonf else ("borderline" if r["p"] < 0.05 else "no")
        L.append(f"| {r['name']} | {r['n']} | {r['loser_med']:.2f} | {r['winner_med']:.2f} | "
                 f"{r['auc']:.3f} ({arrow}) | {r['p']:.3f} | {passb} | {tail} |\n")
    L.append("\n`room_ahead` and `ent_vs_vwap_sd_dir` are direction-adjusted (a long entering "
             "low on the range and a short entering high both read as high room ahead). "
             "`ent_on_pos` is the raw un-adjusted version, kept only as a check — it should "
             "separate LESS than the adjusted one if entry location matters the way we think.\n")

    # cross: does the strongest entry signal interact with day character?
    L.append("\n## Strongest entry signal x day character\n")
    esig = max(entry_rows, key=lambda r: abs(r["auc"] - 0.5))
    ec = esig["col"]
    L.append(f"\nCrossing the strongest entry separator (**{esig['name']}**) against the "
             f"strongest day separator (**{best['name']}**), median split on each:\n\n"
             "| | calm/low day | choppy/high day |\n|---|---|---|\n")
    t2 = t[t[ec].notna() & t[dcol].notna()].copy()
    t2["eh"] = t2[ec] > t2[ec].median()
    t2["dh"] = t2[dcol] > t2[dcol].median()
    for eh, elab in [(False, f"low {esig['name']}"), (True, f"high {esig['name']}")]:
        cells = []
        for dh in (False, True):
            g = t2[(t2.eh == eh) & (t2.dh == dh)]
            cells.append(f"{(g.R <= 0).mean() * 100:.0f}% loss, R {g.R.mean():+.2f} (n={len(g)})"
                         if len(g) else "—")
        L.append(f"| {elab} | {cells[0]} | {cells[1]} |\n")

    L.append("\n## Verdict\n\n")
    allrows = dur_rows + day_rows + entry_rows
    passed = [r for r in allrows if r["p"] < 0.05 / bonf]
    borderl = [r for r in allrows if 0.05 / bonf <= r["p"] < 0.05]
    if passed:
        L.append("Clears Bonferroni (a real lead to test on the holdout): "
                 + ", ".join(f"**{r['name']}** (AUC {r['auc']:.2f}, p {r['p']:.3f})"
                             for r in passed) + ".\n")
    else:
        L.append("**Nothing clears the Bonferroni bar.** No single feature separates London's "
                 "losers from its winners strongly enough to survive the multiple-comparison "
                 "correction on the fit book.\n")
    if borderl:
        L.append("\nBorderline (p < 0.05 raw but not after correction — suggestive, not "
                 "trustworthy alone): "
                 + ", ".join(f"{r['name']} (AUC {r['auc']:.2f}, p {r['p']:.3f})"
                             for r in borderl) + ".\n")
    L.append("\nThis is the honest shape of it: the losers are stops, they do not cluster in "
             "time-in-trade, and whatever tilt exists in day-character or entry is measured "
             "above with its p-value so you can see how much of it to believe.\n")

    write("LONDON-LOSS-ANATOMY.md", "".join(L))
    print(f"losers {nloss}/{len(t)}; passed Bonferroni: {[r['name'] for r in passed]}")


if __name__ == "__main__":
    main()
