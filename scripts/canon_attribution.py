#!/usr/bin/env python3
"""WHY was each canon candidate rejected? — the missing field in the journal.

`output/canon_book.parquet` already carries the full candidate universe (713 rows over the
fit window: 264 taken, 449 rejected) with every check result, every Q bit, and — critically
— the counterfactual `dollars` each rejected candidate WOULD have produced. What it does not
carry is which layer of the ladder killed it. Without that you cannot ask "what do the Q<=1
rejects look like versus the score<=2 rejects", which is the question any adaptive layer has
to answer before it can earn discretion.

This script derives that attribution POST HOC. It deliberately does NOT modify
`scripts/canon_mechanical.py`: that module produces the arming reference
(`canon_news_clean` -> +$55,989.81 / 383) and on launch day the certified commit must not
move. Nothing here is imported by the trade path.

SELF-VALIDATING: the attribution re-applies the ladder in the same order build_canon does,
and re-derives `size` from scratch. If the re-derived size does not match the committed
book row-for-row, the ordering is wrong and the script FAILS rather than reporting a
plausible-looking lie.

    python -m scripts.canon_attribution                # report
    python -m scripts.canon_attribution --write        # + output/canon_attribution.parquet

Reason codes, in the order build_canon applies them:

  score_le_2        Layer 2   ladder floor: fewer than 3 of the window's 5 checks passed
  gold_Q_le_1       Layer 2q  golden structure without quality (WATCH ITEM: 16-trade cell)
  dead_zone         "         09:55-10:00 entry cut (Angus 2026-07-26)
  news_blackout     "         pre-open high-impact release after the fill
  nth_needs_4       Layer 2b  trade #2+ of the day requires score >= 4
  day_escalation    Layer 2c  day red -> both structure checks required (A-setups exempt)
  day_stop_400      "         day P&L <= -$400: done for the day
  taken             survived the ladder
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "output/canon_book.parquet"
OUT = ROOT / "output/canon_attribution.parquet"

ORDER = ["score_le_2", "gold_Q_le_1", "dead_zone", "news_blackout",
         "nth_needs_4", "day_escalation", "day_stop_400", "taken"]


def attribute(C: pd.DataFrame, dead_zones=None) -> pd.DataFrame:
    """Re-walk the ladder recording the FIRST layer that zeroed each candidate.

    Mirrors build_canon's ordering exactly. Returns the book with `rejected_by` plus the
    size after each stage, so a later layer's veto never masks an earlier one.

    `dead_zones` defaults to None to match `canon_mechanical.main()`, which builds the
    committed book with NO gate. The 09:55-10:00 cut and the news blackout are applied by
    `canon_news_clean` on the way to the arming reference, so pass them explicitly when
    attributing THAT book. Guessing wrong is caught by the self-validation, not silently
    absorbed — that is how this default was found in the first place.
    """
    T = C.copy().sort_values("fill").reset_index(drop=True)
    reason = pd.Series(["taken"] * len(T), index=T.index, dtype=object)

    # --- Layer 2: the score ladder -----------------------------------------
    size = pd.Series(np.select([T.score <= 2, T.score == 3, T.score == 4, T.score == 5],
                               [0.0, 0.5, 1.0, 1.5], default=0.0), index=T.index)
    reason[size == 0] = "score_le_2"
    T["size_after_ladder"] = size.copy()

    # --- Layer 2q: golden quality tier -------------------------------------
    gold_live = (T.win_ == "gold") & (size > 0)
    kill = gold_live & (T.Q <= 1)
    reason[kill] = "gold_Q_le_1"
    size[kill] = 0.0
    boost = gold_live & (T.Q >= 3) & (size > 0)
    size[boost] = np.minimum(size[boost] + 0.5, 1.5)
    T["size_after_Q"] = size.copy()

    # --- dead zone (09:55-10:00) -------------------------------------------
    for z0, z1 in (dead_zones or ()):
        kill = (T.fillhm >= z0) & (T.fillhm < z1) & (size > 0)
        reason[kill] = "dead_zone"
        size[kill] = 0.0

    # --- news blackout ------------------------------------------------------
    # The committed book was built WITHOUT a news gate (canon_mechanical.main passes
    # none); canon_news_clean supplies one. Detect it by disagreement rather than
    # recomputing the calendar, so this stays honest about which book it was handed.
    if "news_blocked" in T.columns:
        kill = T.news_blocked.fillna(False).astype(bool) & (size > 0)
        reason[kill] = "news_blackout"
        size[kill] = 0.0

    # --- Layer 2b: trade #2+ needs score >= 4 -------------------------------
    taken_mask = size > 0
    nth = taken_mask[taken_mask].groupby(T.loc[taken_mask, "day"]).cumcount() + 1
    nth = nth.reindex(T.index)
    kill = (nth >= 2) & (T.score < 4)
    kill = kill.fillna(False)
    reason[kill] = "nth_needs_4"
    size[kill] = 0.0

    # --- Layer 2e: sizing mods (never zero, so no reason code) --------------
    r1 = T.get("cold", pd.Series(False, index=T.index)).fillna(False).astype(bool) & \
        (T.get("churn_flow_30", pd.Series(np.nan, index=T.index)) > 0.0292).fillna(False)
    r2 = (T.get("netpath_30", pd.Series(np.nan, index=T.index)) >= 0.3328).fillna(False) & ~r1
    size[r1] *= 0.5
    size[r2] *= 1.5

    # --- Layer 2c: within-day escalation ------------------------------------
    pl = T.eff_dollars * size * T.governor
    struct = np.where(T.win_ == "pre", T.W + T.Tp, T.D.fillna(0) + T.Tc)
    T["_struct_calc"] = struct
    live_idx = T.index[size > 0]
    for _day, grp in T.loc[live_idx].groupby("day"):
        daypl, out = 0.0, False
        for i in grp.index:
            if out:
                reason[i] = "day_stop_400"
                size[i] = 0.0
                continue
            if daypl < 0 and T.at[i, "_struct_calc"] < 2 and T.at[i, "pattern"] != "A":
                reason[i] = "day_escalation"
                size[i] = 0.0
                continue
            daypl += pl[i]
            if daypl <= -400:
                out = True

    T["rejected_by"] = reason
    T["size_rederived"] = size
    return T.drop(columns=["_struct_calc"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write output/canon_attribution.parquet")
    ap.add_argument("--dead-zones", action="store_true",
                    help="attribute a book built WITH the 09:55-10:00 cut (canon_news_clean)")
    a = ap.parse_args()

    if not BOOK.exists():
        raise SystemExit(f"missing {BOOK.relative_to(ROOT)} — run scripts/canon_mechanical first")
    C = pd.read_parquet(BOOK)
    T = attribute(C, dead_zones=((595, 600),) if a.dead_zones else None)

    # ---- SELF-VALIDATION: the re-derived ladder must reproduce the book ----
    ref = C.sort_values("fill").reset_index(drop=True)["size"].to_numpy()
    got = T["size_rederived"].to_numpy()
    mismatch = int((~np.isclose(ref, got)).sum())
    if mismatch:
        bad = T.loc[~np.isclose(ref, got), ["day", "fill", "win_", "score", "Q", "rejected_by"]]
        print(bad.head(15).to_string())
        raise SystemExit(
            f"ATTRIBUTION UNSOUND: {mismatch}/{len(T)} rows disagree with the committed book.\n"
            "The ladder ordering here does not match build_canon — do not trust these reasons.")
    print(f"attribution validated: re-derived size matches all {len(T)} rows of the book\n")

    taken = T[T.rejected_by == "taken"]
    rej = T[T.rejected_by != "taken"]
    print(f"universe {len(T)} candidates over {T.day.nunique()} days — "
          f"{len(taken)} taken, {len(rej)} rejected\n")

    print(f"{'reason':<18}{'n':>5}{'cf $ (1-lot)':>15}{'WR':>7}{'$/trade':>10}   verdict")
    print("-" * 74)
    for r in ORDER:
        g = T[T.rejected_by == r]
        if not len(g):
            continue
        d = g.dollars
        wr = (d > 0).mean() * 100
        avg = d.mean()
        if r == "taken":
            verdict = ""
        elif d.sum() < 0:
            verdict = "correctly skipped"
        else:
            verdict = "** LEFT MONEY ON THE TABLE **"
        print(f"{r:<18}{len(g):>5}{d.sum():>15,.0f}{wr:>6.0f}%{avg:>10,.0f}   {verdict}")
    print("-" * 74)
    print(f"{'ALL REJECTED':<18}{len(rej):>5}{rej.dollars.sum():>15,.0f}"
          f"{(rej.dollars > 0).mean() * 100:>6.0f}%{rej.dollars.mean():>10,.0f}")

    print("\nby window:")
    for w in sorted(T.win_.dropna().unique()):
        g = T[(T.win_ == w) & (T.rejected_by != "taken")]
        if len(g):
            print(f"  {w:<6} {len(g):>4} rejected, cf ${g.dollars.sum():>9,.0f}, "
                  f"WR {(g.dollars > 0).mean() * 100:.0f}%")

    print("\nrejects by hour of fill (ET) — the time-of-day question:")
    rr = rej.assign(hr=(rej.fillhm // 60).astype(int))
    for hr, g in rr.groupby("hr"):
        print(f"  {hr:02d}:00  {len(g):>4} rejected, cf ${g.dollars.sum():>9,.0f}, "
              f"WR {(g.dollars > 0).mean() * 100:>3.0f}%")

    if a.write:
        T.to_parquet(OUT, index=False)
        print(f"\nwrote {OUT.relative_to(ROOT)} ({len(T)} rows, +rejected_by)")


if __name__ == "__main__":
    main()
