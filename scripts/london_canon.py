#!/usr/bin/env python3
"""THE LONDON CANON (Angus ruling 28-Jul: third canon; sessions are structurally
different — each gets its own mechanically-derived book, agents execute per session).

Window: first 2 hours of London, 08:00-10:00 Europe/London (03:00-05:00 ET normal,
04:00-06:00 ET during UK/US DST misalignment). Universe: both books, every day, no
book choosing, no day forecasting (london_substrate + london_matrix + london_depth).

Layer 0  GATES     : stop >= 9.5 pts (2025-London median; sub-7pt is a hard kill zone
                     at 11-15% WR — third window where micro-stops are toxic).
                     NO upper stop cap (London-native evidence: wide stops fine).
Layer 1  VALIDATION: 4 London-native checks (2025-London-frozen thresholds) —
                     W    no wall BEHIND entry (pre-like; +28/+19pp)
                     FAR  wall AHEAD at distance > 4.5 pts (magnet, not choking)
                     ROOM 2.48 < room_ahead_R <= 9.56 (room to the target-side
                          overnight extreme, in R; the London flagship construct)
                     ASIA Asia-session flow not deeply opposed (dir*cvd_ASIA >= -748)
Layer 2  SIZING    : score<=1 -> 0 | 2 -> 0.5 | 3 -> 1.0 | 4 -> 1.5
Layer 2p PATTERN   : B (continuation) requires score >= 3 (score-2 B = 37%/26% WR
                     bleeder; 4/4 half-periods). B2/A trade the normal ladder.
Layer 2f OF STACK  : order-flow confirmations = ASIA aligned + clean tape (opp5 < 2,
                     fewer than 2 of last 5 pre-fill 1-min deltas against direction).
                     Within structure >= 2 (of W/FAR/ROOM):
                       both OF confirmations -> x1.5 boost (76%/80% WR cell, cap 1.5)
                     zero OF confirmations -> x0.5; if score == 2 -> NO TRADE
                     (Angus 28-Jul: 'remove it, we are trading more than enough').
Layer 2b ESCALATION: trade #2+ of the day requires score >= 3.
IN-TRADE           : NONE — verified: loss-cuts EV-null, stall/time-stops EV-NEGATIVE
                     (stalled London trades recover to full targets 31-52% of the
                     time; the engine's partial/stop management already harvests the
                     alpha). London holds to the stop. Do not port NY/gold cuts.

Validated (thresholds 2025-frozen, 2026 out-of-fit): 2025 +$22,219 / 2026 +$13,000
(see main() print for exact regenerated figures), WR ~60%/56%, PF 3.3/2.4,
maxDD ~$1.6k/yr, 10/13 green months, all four half-periods positive.
Combined with the NY canon: ~+$106k/2yr, day-corr +0.11, combined maxDD BELOW NY alone.
Holdout list (2023/24): B>=3 + OF-stack recalibration, TAPE-check ablation,
W/FAR collapse (r=0.86), ROOM band edges, DST-week behavior.

Inputs: output/london_matrix.parquet (needs london_substrate + london_matrix +
london_depth), output/fp_minutes.parquet. Writes output/london_canon_book.parquet.

`--span holdout` scores the sealed 2023/24 matrix through the SAME build_london — every
threshold above is 2025-frozen and none is re-derived here, which is the whole point of the
holdout. The only substitution is the minute tape build_london reads for the opp5 clean-tape
bit: fp_minutes covers the fit window only.

    python -m scripts.london_canon
    python -m scripts.london_canon --span holdout
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"

SPANS = {
    "fit": {"matrix": "output/london_matrix.parquet", "tape": "output/fp_minutes.parquet",
            "out": "output/london_canon_book.parquet", "years": (2025, 2026)},
    "holdout": {"matrix": "output/london_matrix_holdout.parquet",
                "tape": "data/reference/cvd/footprint_holdout_*.parquet",
                "out": "output/london_canon_book_holdout.parquet", "years": (2023, 2024)},
}


def build_london(L, fp=None):
    L = L[L.risk > 0].copy()
    long = L.direction == "long"
    sgn = np.where(long, 1, -1)
    # checks (frozen 2025-London thresholds)
    L["W"] = pd.Series(np.where(long, L.dep_wall_below_d.isna(), L.dep_wall_above_d.isna()),
                       index=L.index).astype(float)
    wall_ahead_d = pd.Series(np.where(long, L.dep_wall_above_d, L.dep_wall_below_d), index=L.index)
    L["FAR"] = (wall_ahead_d > 4.5).fillna(False).astype(float)
    room = np.where(long, (1 - L.ent_on_pos) * L.on_range, L.ent_on_pos * L.on_range)
    L["room_R"] = room / L.risk
    L["ROOM"] = ((L.room_R > 2.48) & (L.room_R <= 9.56)).astype(float)
    L["ASIA"] = ((L.cvd_ASIA * sgn) >= -748).astype(float)
    # clean-tape OF bit from fp_minutes (count of last-5 pre-fill 1-min deltas opposed)
    if fp is None:
        fp = pd.read_parquet("output/fp_minutes.parquet")
        fp.index = pd.DatetimeIndex(fp.index)
        fp = fp.sort_index()
    opp = []
    for t in L.itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        seg = fp.loc[f - pd.Timedelta(minutes=5): f - pd.Timedelta(minutes=1)]
        s = 1 if t.direction == "long" else -1
        opp.append(int((np.sign(seg.delta.values * s) < 0).sum()) if len(seg) == 5 else np.nan)
    L["opp5"] = opp

    # Layer 0
    L = L[L.risk >= 9.5].sort_values("fill").copy()
    L["score"] = L[["W", "FAR", "ROOM", "ASIA"]].sum(axis=1)
    # Layer 2
    L["size"] = np.select([L.score <= 1, L.score == 2, L.score == 3, L.score == 4], [0, .5, 1, 1.5])
    # Layer 2p
    L.loc[(L.pattern == "B") & (L.score == 2), "size"] = 0.0
    # Layer 2f
    struct = L[["W", "FAR", "ROOM"]].sum(axis=1)
    of2 = (L.ASIA == 1) & (L.opp5 < 2)
    of0 = (L.ASIA == 0) & (L.opp5 >= 2)
    boost = (L["size"] > 0) & (struct >= 2) & of2
    L.loc[boost, "size"] = np.minimum(L.loc[boost, "size"] * 1.5, 1.5)
    L.loc[(L["size"] > 0) & of0 & (L.score == 2), "size"] = 0.0   # 28-Jul ruling: no trade
    L.loc[(L["size"] > 0) & of0, "size"] *= 0.5
    # Layer 2b
    taken = L[L["size"] > 0]
    nth = taken.groupby("day").cumcount() + 1
    L["nth"] = nth.reindex(L.index)
    L.loc[((L.nth >= 2) & (L.score < 3)).fillna(False), "size"] = 0.0
    L["pl"] = L.dollars * L["size"]
    return L


def main():
    from scripts.score_canon_span import minute_tape

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), default="fit")
    a = ap.parse_args()
    spec = SPANS[a.span]

    M = pd.read_parquet(spec["matrix"])
    C = build_london(M, fp=minute_tape({"tape": spec["tape"]}))
    C.to_parquet(spec["out"])
    for yr in spec["years"]:
        d = C[C.yr == yr]
        t = d[d["size"] > 0]
        cum = t.groupby("day").pl.sum().cumsum()
        dd = (cum.cummax() - cum).max() if len(cum) else 0
        gw = t[t.pl > 0].pl.sum()
        gl = -t[t.pl < 0].pl.sum()
        print(f"{yr}: ${d.pl.sum():+9,.0f}  ({len(t)} trades, {t.day.nunique()} days, "
              f"WR {(t.dollars>0).mean()*100:.0f}%, PF {gw/max(gl,1):.2f}, maxDD ${dd:,.0f})")
    mo = C.groupby(C.day.str[:7]).pl.sum()
    print(f"green months {int((mo>0).sum())}/{len(mo)}, worst ${mo.min():+,.0f}")
    print(f"\nwrote {spec['out']} ({len(C)} rows)")


if __name__ == "__main__":
    main()
