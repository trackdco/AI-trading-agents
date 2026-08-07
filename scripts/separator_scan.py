#!/usr/bin/env python3
"""Exhaustive winner/loser separator scan on the LIMIT-ENTRY book.

ANGUS 2026-08-06:

    "also for limit orders since we cant hindsight maxx with order flow, it would be
     ineteresting to see if theres any other variables we can validate winnners against
     losers for and see if we can actually find shit that seperates the winners from losers.
     thousands of triggers, there HAS to be something that can seperate the winners from
     losers, wherever that gap is"

WHY A SCAN AND NOT A HYPOTHESIS. Every separator tried so far was one somebody thought of
first -- and the ones I picked myself (daily trend alignment, risk buckets, book imbalance)
have died on era-consistency. Picking favourites is how a scan becomes a story. So this walks
EVERY causally-legal variable in the book, applies the identical test to each, and ranks them.
The point is coverage, not cleverness.

THE CAUSALITY BAR, AND IT IS THE WHOLE GAME. A limit order's decision happens at PLACEMENT,
not at fill. So a variable qualifies only if it was knowable when the order went in:

  LEGAL     trigger geometry (tf, pattern, kind, htf_flag, confluence, level stack), the
            intended risk (limit->stop, fixed at placement), clock time, and the daily
            context layer (built from sessions STRICTLY BEFORE the day -- see
            scripts/build_daily_context.py).
  ILLEGAL   anything read at or after the fill: depth, footprint delta, the fill bar's close.
            On a limit entry the order fills mid-bar, so a bar-close read is one bar late --
            `research/findings/LDN-depth-read-one-bar-late.md`, and again today when a
            +8.90 pt/trade "confirmation" signal turned out to be a +10.57 pt head start.

MULTIPLE COMPARISONS ARE THE OBVIOUS FAILURE MODE HERE. Scanning ~30 variables x 3 buckets on
12,000 trades WILL produce impressive-looking cells by chance. Two defences, both declared
before looking: (1) a split must point the SAME WAY in 2025 and 2026 independently, and
(2) numeric splits must be MONOTONIC across terciles -- a middle bucket that beats both ends
is noise wearing a pattern. Neither is sufficient; both are cheap. Anything that survives is
a CANDIDATE owed a family-wise permutation null (§2.3), not a finding.

    python -m scripts.separator_scan [--book output/l2_outcomes_fit.parquet]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
CTX = ROOT / "output/daily_context.parquet"

# Context columns that are numeric and causally clean (built from strictly prior sessions).
CTX_NUM = ["trend_atr", "ret5_atr", "trend_pct", "close_pos", "va_overlap", "va_overlap_3",
           "poc_streak", "poc_dir3", "poc_dir5", "atr20", "atr_pct", "range_atr",
           "vix", "vix_pct"]
CTX_CAT = ["trend_state", "vol_state", "balance_state"]


def load(book: Path) -> pd.DataFrame:
    O = pd.read_parquet(book)
    D = O[O.status == "outcome"].copy()
    C = pd.read_parquet(CTX)
    D = D.merge(C, on="day", how="left")
    D["era"] = D.day.str[:4]
    D["dir"] = np.where(D.direction.astype(str).str.lower().str.startswith(("l", "b")), 1, -1)

    ts = pd.to_datetime(D.fill_ts, utc=True, format="mixed").dt.tz_convert(NY)
    D["hour"] = ts.dt.hour
    D["mins_into_session"] = ts.dt.hour * 60 + ts.dt.minute - (9 * 60 + 30)

    # trigger geometry, all fixed at order placement
    def _n(s):
        if isinstance(s, (list, tuple, np.ndarray)):
            return len(s)
        return len(str(s).split(",")) if s not in (None, "", "nan") else 0
    for c in ("cluster_members", "level_stack"):
        if c in D.columns:
            D[f"n_{c}"] = D[c].map(_n)
    D["risk_pts"] = D.risk

    # ROOM. The single feature that has ever beaten a family-wise permutation null in this
    # project -- `room_ahead_R` on the London L3 (24.7% vs a null median of 7.7%). It is not
    # in the NY book as a column, but it is derivable: the distance from entry to the target
    # level, in units of the trade's own risk. Both forms are kept because they differ:
    # `target_level` is the menu level chosen, `working_target` is it AFTER the rr_floor
    # walkout has pushed it outward, so in a 2R-floor book the latter is bounded below at 2R
    # by construction and the former is not.
    for src, nm in (("target_level", "room_R"), ("working_target", "room_work_R")):
        if src in D.columns:
            D[nm] = (D[src] - D.entry).abs() / D.risk.replace(0, np.nan)
            D.loc[~np.isfinite(D[nm]), nm] = np.nan

    # context expressed RELATIVE to the trade's own direction -- a raw trend number cannot
    # separate anything until it is stated as "with me" or "against me"
    for c in ("trend_atr", "ret5_atr", "poc_streak", "poc_dir3", "poc_dir5"):
        if c in D.columns:
            D[f"{c}_dir"] = D[c] * D["dir"]
    return D


def split_stats(D: pd.DataFrame, col: str, cat: bool) -> list[dict]:
    out = []
    if cat:
        groups = [(str(k), D[D[col] == k]) for k in sorted(D[col].dropna().unique().tolist())]
    else:
        s = D[col].dropna()
        if s.nunique() < 5:
            groups = [(str(k), D[D[col] == k]) for k in sorted(s.unique().tolist())]
        else:
            q = s.quantile([1 / 3, 2 / 3]).values
            groups = [("LOW", D[D[col] <= q[0]]),
                      ("MID", D[(D[col] > q[0]) & (D[col] < q[1])]),
                      ("HIGH", D[D[col] >= q[1]])]
    for nm, S in groups:
        if len(S) < 150:
            continue
        e = {x: (S[S.era == x].R.mean() if len(S[S.era == x]) > 60 else np.nan)
             for x in ("2025", "2026")}
        out.append({"bucket": nm, "n": len(S), "R": S.R.mean(), "pts": S.pts.mean(),
                    "wr": (S.R > 0).mean(), "r25": e["2025"], "r26": e["2026"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="output/l2_outcomes_fit.parquet")
    a = ap.parse_args()
    D = load(ROOT / a.book)

    num = [c for c in (["confluence_count", "risk_pts", "hour", "mins_into_session",
                        "n_cluster_members", "n_level_stack", "room_R", "room_work_R"]
                       + CTX_NUM + [f"{c}_dir" for c in
                                    ("trend_atr", "ret5_atr", "poc_streak",
                                     "poc_dir3", "poc_dir5")])
           if c in D.columns and D[c].notna().sum() > 1000]
    cat = [c for c in (["tf", "direction", "kind", "pattern", "htf_flag"] + CTX_CAT)
           if c in D.columns]

    base_R, base_p = D.R.mean(), D.pts.mean()
    rows = []
    for col in num + cat:
        st = split_stats(D, col, cat=col in cat)
        if len(st) < 2:
            continue
        best = max(st, key=lambda r: r["R"])
        worst = min(st, key=lambda r: r["R"])
        spread = best["R"] - worst["R"]
        # DECLARED BAR 1: the best bucket must beat base in BOTH eras independently
        consistent = (np.isfinite(best["r25"]) and np.isfinite(best["r26"])
                      and best["r25"] > base_R and best["r26"] > base_R)
        # DECLARED BAR 2: numeric splits must be monotonic across terciles
        mono = True
        if col in num and len(st) == 3:
            v = [r["R"] for r in st]
            mono = (all(x >= y for x, y in zip(v, v[1:]))
                    or all(x <= y for x, y in zip(v, v[1:])))
        rows.append({"var": col, "spread": spread, "best": best["bucket"], "n": best["n"],
                     "bR": best["R"], "bp": best["pts"], "bwr": best["wr"],
                     "r25": best["r25"], "r26": best["r26"],
                     "consistent": consistent, "mono": mono, "stats": st})

    rows.sort(key=lambda r: -r["spread"])
    L = ["# Separator scan — limit-entry book", "",
         "**Census/screen only (§5.9.1).** Every causally-legal variable, identical test, ranked.",
         "", "A variable qualifies only if it was knowable **at order placement** — depth and",
         "footprint are excluded because a limit fills mid-bar, so any bar-close read is one",
         "bar late (that defect cost us a +8.90 pt/trade 'signal' today that was really a",
         "+10.57 pt head start).", "",
         f"**{len(D):,} fills over {D.day.nunique()} sessions.** "
         f"Base mean R **{base_R:+.3f}**, net **{base_p:+.2f}** pt, "
         f"win rate **{(D.R > 0).mean():.1%}**.", "",
         "Two bars, both declared before looking: the best bucket must beat base in **2025 and",
         "2026 independently**, and numeric splits must be **monotonic** across terciles.", "",
         "| variable | best bucket | n | mean R | net pt | WR | 2025 | 2026 | R spread | eras | mono |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        L.append(f"| `{r['var']}` | {r['best']} | {r['n']:,} | **{r['bR']:+.3f}** | "
                 f"{r['bp']:+.2f} | {r['bwr']:.1%} | "
                 + " | ".join(f"{r[k]:+.3f}" if np.isfinite(r[k]) else "—"
                              for k in ("r25", "r26"))
                 + f" | {r['spread']:.3f} | {'**yes**' if r['consistent'] else 'no'} "
                 f"| {'yes' if r['mono'] else 'no'} |")

    surv = [r for r in rows if r["consistent"] and r["mono"] and r["bR"] > base_R]
    L += ["", "---", "", "## Survivors", ""]
    if surv:
        L += [f"**{len(surv)} of {len(rows)} variables** clear both declared bars.", "",
              "| variable | bucket | n | mean R | net pt | 2025 | 2026 |", "|---|---|---:|---:|---:|---:|---:|"]
        for r in surv:
            L.append(f"| `{r['var']}` | {r['best']} | {r['n']:,} | **{r['bR']:+.3f}** | "
                     f"{r['bp']:+.2f} | {r['r25']:+.3f} | {r['r26']:+.3f} |")
        L += ["", "**These are CANDIDATES, not findings.** Roughly "
              f"{len(rows)} variables were scanned; at a 5% false-positive rate you would "
              f"expect ~{len(rows) * 0.05:.0f} to clear a single bar by chance. Two bars cut "
              "that hard but do not eliminate it. Each survivor is owed a family-wise "
              "permutation null (§2.3) over the whole scanned family before it earns a name.", ""]
    else:
        L += ["**Nothing clears both bars.** No single causally-legal variable in this book "
              "separates winners from losers in a way that holds in both eras and behaves "
              "monotonically.", "",
              "That is a real result rather than a failure to look: it says the separation, if "
              "it exists, is not in any single variable we currently record — it is either in "
              "an interaction, or in information the book does not contain.", ""]

    L += ["", "## Full bucket detail, top 8 by spread", ""]
    for r in rows[:8]:
        L += [f"**`{r['var']}`**", "",
              "| bucket | n | mean R | net pt | WR | 2025 | 2026 |", "|---|---:|---:|---:|---:|---:|---:|"]
        for s in r["stats"]:
            L.append(f"| {s['bucket']} | {s['n']:,} | {s['R']:+.3f} | {s['pts']:+.2f} | "
                     f"{s['wr']:.1%} | "
                     + " | ".join(f"{s[k]:+.3f}" if np.isfinite(s[k]) else "—"
                                  for k in ("r25", "r26")) + " |")
        L.append("")

    text = "\n".join(L)
    print(text)
    (ROOT / "output/separator_scan.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
