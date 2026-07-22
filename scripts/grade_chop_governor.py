#!/usr/bin/env python3
"""Grade the fresh-eyes chop-governor walk (Angus 24-Jul).

Input: output/chop_verdicts.json = [{day, pre_mult, gold_mult, chop_score, reason}, ...]
Applies the agent's defensive multipliers per (day, window) to the conviction-sized ladder and
compares four books: baseline ladder / mechanical scoreboard governor (N=15) / agent governor /
agent + scoreboard combined. Also: does the agent's chop_score correlate with realized day
quality, and what did it read on the Jul-Sep 2025 bleed?

    python -m scripts.grade_chop_governor
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    V = pd.DataFrame(json.loads(Path("output/chop_verdicts.json").read_text()))
    V = V.drop_duplicates("day").set_index("day")
    print(f"verdicts: {len(V)} days | pre_mult mix {V.pre_mult.value_counts().to_dict()} | "
          f"gold_mult mix {V.gold_mult.value_counts().to_dict()}")

    S = pd.read_parquet("output/tier1_stack.parquet").sort_values("fill").reset_index(drop=True)
    S["size"] = np.select([S.score <= 2, S.score == 3, S.score == 4, S.score == 5], [0, .5, 1, 1.5])
    S["spl"] = S.dollars * S["size"]

    # mechanical scoreboard governor N=15 (only past trades)
    hi = S[S.score >= 4].reset_index()
    hi["trailWR"] = hi.dollars.gt(0).rolling(15).mean().shift(1)
    trail = dict(zip(hi["index"], hi.trailWR))
    cur = np.nan; mech = []
    twr = pd.Series(S.index.map(trail))
    for i in range(len(S)):
        if not np.isnan(twr[i]):
            cur = twr[i]
        mech.append(0.5 if (not np.isnan(cur) and cur < 0.35) else 1.0)
    S["mech"] = mech

    S["agent"] = [float(V.loc[r.day, "pre_mult" if r.win_ == "pre" else "gold_mult"])
                  if r.day in V.index else 1.0 for r in S.itertuples()]
    S["mo"] = S.day.str[:7]

    books = {"baseline ladder": S.spl,
             "mech governor (N=15)": S.spl * S.mech,
             "AGENT governor": S.spl * S.agent,
             "agent + mech": S.spl * S.agent * S.mech}
    print(f"\n{'book':24s} {'2025':>10s} {'2026':>10s} {'JulSep25':>9s} {'monthsGrn':>9s} {'maxDD25/26':>14s}")
    for nm, pl in books.items():
        t = S.assign(pl=pl)
        y25 = t[t.yr == 2025].pl.sum(); y26 = t[t.yr == 2026].pl.sum()
        js = t[(t.mo >= "2025-07") & (t.mo <= "2025-09")].pl.sum()
        mm = t.groupby("mo").pl.sum(); grn = int((mm > 0).sum())
        dds = []
        for yr in (2025, 2026):
            dl = t[t.yr == yr].groupby("day").pl.sum(); c = dl.cumsum()
            dds.append((c.cummax() - c).max() if len(c) else 0)
        print(f"{nm:24s} {y25:+10,.0f} {y26:+10,.0f} {js:+9,.0f} {grn:6d}/13 {dds[0]:7,.0f}/{dds[1]:,.0f}")

    # calibration: agent chop_score vs realized day quality
    day_pl = S.groupby("day").spl.sum()
    cal = V.join(day_pl.rename("sized_pl")).dropna(subset=["sized_pl"])
    print("\nchop_score calibration (agent read vs realized sized P&L of the raw ladder):")
    for lo, hi_ in ((0, 2), (3, 4), (5, 6), (7, 10)):
        g = cal[(cal.chop_score >= lo) & (cal.chop_score <= hi_)]
        if len(g):
            print(f"  score {lo}-{hi_}: n={len(g):3d}  mean day ${g.sized_pl.mean():+6.0f}  "
                  f"green days {(g.sized_pl > 0).mean()*100:.0f}%")
    js = cal[(cal.index >= "2025-07") & (cal.index <= "2025-09-30")]
    print(f"\nJul-Sep 2025: mean chop_score {js.chop_score.mean():.1f} vs rest {cal[~cal.index.isin(js.index)].chop_score.mean():.1f}; "
          f"days de-risked {int(((js.pre_mult < 1) | (js.gold_mult < 1)).sum())}/{len(js)}")


if __name__ == "__main__":
    main()
