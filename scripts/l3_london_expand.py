#!/usr/bin/env python3
"""L3 LONDON — the expanded variable battery. Classes the build never touched.

ANGUS 2026-08-05:

    "you have much more research behind order flow concepts and quant trading than we had
     before, id hope you have something to show for it. canon had none of that. there are
     way more variables we can look at for trade entry validation. market conditions as
     well, so many things"

Fair, and the gap is specific. Everything tested so far was the NY canon's inherited
battery plus seven trigger-candle flow features. Sitting unused in the repo the whole time:

  data/reference/vix_daily.csv     9,231 rows. NO regime conditioning existed anywhere.
  output/fp_minutes.parquet        carries `b` and `a` SEPARATELY; only their difference
                                   (delta) was ever used.
  data/reference/depth_london      10 levels per side; collapsed to totals and one wall.
                                   Book SHAPE was never computed.
  level_stack / cluster_members    every level at trigger time with type and price. Used
                                   once for a cancel rule, never as a feature. WHICH LEVEL
                                   IS BEING TRADED was never tested.

SIX NEW CLASSES, all strictly at-or-before the trigger candle's close.

  LEVEL IDENTITY   lvl_is_bb / lvl_is_vwap / lvl_is_poc -- which type the entry sits on;
                   lvl_n_types, lvl_stack_density (levels within 20pt of entry)
  REGIME           vix_level, vix_chg_5d, rel_range (overnight range vs its own trailing
                   20-session median) -- the volatility state the trade is born into
  EFFORT/RESULT    eff_result (trigger-candle volume per point of range) and
                   eff_result_rel vs the session median. High volume for little movement is
                   absorption; low volume for a lot is a vacuum.
  BOOK SHAPE       bk_slope (OLS of size against distance across all 10 levels, signed by
                   direction), bk_conc (share of total size in the top 3 levels),
                   bk_far_near (levels 6-10 size / levels 1-5 size)
  DIVERGENCE       cvd_div -- price makes a session extreme, cumulative delta does not
  SESSION CLOCK    lon_min (minutes since the London open) as an ordered variable

COST, STATED HONESTLY: every variable added enlarges the search, which raises the null's
family-wise bar and makes everything harder to clear. That is the correct trade -- an
untested variable is not a free option -- but it is a real cost and the null pays it.

    python -m scripts.l3_london_expand [--entry E3]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_depth import load_day  # noqa: E402
from scripts.score_canon_span import minute_tape  # noqa: E402

NY = "America/New_York"
DEPTH_DIR = ROOT / "data/reference/depth_london"
TF_MIN = {"1min": 1, "2min": 2, "3min": 3, "5min": 5}


def book_shape(dep: pd.DataFrame, minute: pd.Timestamp, entry: float, long: bool) -> dict:
    """Shape across ALL TEN levels, not the aggregates the build has been using."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    if b.empty:
        return {}
    d = np.abs(b.price.to_numpy(float) - entry)
    s = b["size"].to_numpy(float)
    if len(d) < 6 or s.sum() <= 0:
        return {}
    order = np.argsort(d)
    d, s = d[order], s[order]
    out = {"bk_conc": float(s[:6].sum() / s.sum()),
           "bk_far_near": float(s[len(s) // 2:].sum() / max(s[:len(s) // 2].sum(), 1.0))}
    if d.std() > 0:
        out["bk_slope"] = float(np.polyfit(d, s, 1)[0]) * (1.0 if long else -1.0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="E3")
    a = ap.parse_args()
    p = ROOT / ("output/l3_features_london_fit.parquet" if a.entry == "E3"
                else f"output/l3_features_london_fit_{a.entry}.parquet")
    F = pd.read_parquet(p)
    F = F.drop(columns=[c for c in F.columns if c.startswith(("lvl_", "vix_", "eff_",
                                                              "bk_", "cvd_div", "rel_range"))],
               errors="ignore")

    # --- regime: VIX + relative overnight range -----------------------------
    V = pd.read_csv(ROOT / "data/reference/vix_daily.csv")
    V["date"] = pd.to_datetime(V.date).dt.strftime("%Y-%m-%d")
    V = V.sort_values("date")
    V["vix_chg_5d"] = V.vix.diff(5)
    # shift(1): the trade only knows YESTERDAY's close when London opens
    V["vix_level"] = V.vix.shift(1)
    V["vix_chg_5d"] = V.vix_chg_5d.shift(1)
    F = F.merge(V[["date", "vix_level", "vix_chg_5d"]], left_on="day", right_on="date",
                how="left").drop(columns=["date"])
    dayrng = F.groupby("day").on_range.first()
    med20 = dayrng.rolling(20, min_periods=10).median().shift(1)     # strictly prior days
    F["rel_range"] = F.day.map(dayrng / med20)

    # --- level identity, effort/result, divergence, book shape --------------
    M = minute_tape({"tape": "output/fp_minutes.parquet"})
    ts = pd.to_datetime(F["ts"], utc=True, format="mixed").dt.tz_convert(NY)
    rows, dep, dday = [], None, None
    for i, t in enumerate(F.itertuples()):
        r: dict = {}
        cm = json.loads(t.cluster_members or "[]")
        types = {m[2] for m in cm}
        r["lvl_is_bb"] = float("bb" in types)
        r["lvl_is_vwap"] = float("vwap" in types)
        r["lvl_is_poc"] = float("poc" in types)
        r["lvl_n_types"] = float(len(types))
        stack = json.loads(t.level_stack or "[]")
        r["lvl_stack_density"] = float(sum(1 for m in stack if abs(m[1] - t.entry) <= 20))

        tt = ts.iloc[i]
        n = TF_MIN.get(t.tf, 1)
        cur = M.loc[tt - pd.Timedelta(minutes=n - 1): tt]
        if len(cur):
            rng = float(cur.high.max() - cur.low.min()) if "high" in cur else np.nan
            vol = float(cur.vol.sum())
            r["eff_result"] = vol / max(abs(float(cur.vwp.iloc[-1] - cur.vwp.iloc[0])), 1.0)
            sess = M.loc[: tt].tail(240)
            if len(sess) > 60:
                r["eff_result_rel"] = r["eff_result"] / max(
                    float(sess.vol.median()) / 1.0, 1.0)
        # divergence: price at a session extreme while cum-delta is not
        sess0 = (tt - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
        g = M.loc[sess0: tt]
        if len(g) > 60:
            cd = g.delta.cumsum()
            px_ext = float(g.vwp.iloc[-1] >= g.vwp.max() - 1e-9 or g.vwp.iloc[-1] <= g.vwp.min() + 1e-9)
            cd_ext = float(cd.iloc[-1] >= cd.max() - 1e-9 or cd.iloc[-1] <= cd.min() + 1e-9)
            r["cvd_div"] = float(px_ext == 1.0 and cd_ext == 0.0)

        if t.day != dday:
            dday, dep = t.day, load_day(t.day, DEPTH_DIR)
        if dep is not None:
            r.update(book_shape(dep, tt, float(t.entry), t.direction == "long"))
        rows.append(r)
        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{len(F)}", flush=True)

    X = pd.DataFrame(rows, index=F.index)
    F = pd.concat([F, X], axis=1)
    F.to_parquet(p, index=False)
    new = sorted(set(X.columns) | {"vix_level", "vix_chg_5d", "rel_range"})
    print(f"\nwrote {p.relative_to(ROOT)} — {len(new)} new columns")
    for c in new:
        print(f"  {c:<20} resolved {F[c].notna().mean():.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
