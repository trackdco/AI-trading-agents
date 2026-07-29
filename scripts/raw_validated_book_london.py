#!/usr/bin/env python3
"""L4 — the LONDON book: selection policy applied POST-HOC to the scored L3 population.

Reuses scripts/l4_select.select VERBATIM. That module is a pure causal walk over a DataFrame,
already unit-tested on synthetic data (tests/test_l4_select.py, 13 tests incl.
test_causality_no_best_of_day and test_causality_future_rows_cannot_change_past_decisions),
and it already treats `london` as a first-class session. Rewriting it here would throw away
the only part of L4 that is proven correct.

1-LOT ONLY. ANGUS: no sizing until the validated volume is visible. Dollars are normalised to
one contract (the engine sized 2 of 5,588 fit rows at half — `dollars / size`, which scales
commissions proportionally too; immaterial at n=2 but not worth being sloppy about).

LAYER 0 IS THE RISK GATE, and it is the one inherited rule the trial confirmed: risk >=
LON_RISK_MIN. L2 measured sub-9.5pt at meanR -0.278 (fit) / -0.291 (holdout) in every band and
era. It removes bleed rather than creating edge, which is exactly what a gate should do.

THE SCORING ARMS — the L3 trial changed what a score can honestly mean:

  old4   W + FAR + ROOM + ASIA, threshold 3        the SHIPPED London policy. Carried purely
                                                   as the comparison arm, because two of its
                                                   four terms failed the trial: ROOM is inside
                                                   the permutation null in both eras
                                                   (p=0.698 / 0.809) and ASIA is significantly
                                                   BACKWARDS in 2026 (lift -0.533, p=0.001).
  wall   1 if (W or FAR) else 0, threshold 1       what actually survived. W and FAR are not
                                                   two checks — r=0.834, agreeing on 94.2% of
                                                   rows, with near-empty off-diagonals — so
                                                   they are scored as the single structural
                                                   fact they are, not double-counted.

CAPPED vs UNCAPPED, measured not assumed (handoff §4-L4). Three constraint levels per arm:
capped (2/session + day stop), uncapped (day stop only), raw (neither). NY's cap turned out to
cost money once the junk was cut; London's flow density is different.

CONCURRENCY IS REPORTED, NOT ASSUMED (burn list #10). An uncapped table is meaningless without
knowing how many positions it wants open at once. Max concurrent and max simultaneous open
risk are printed for every arm. This matters more for London than NY: L1 showed that with the
distance cancel off (the ANGUS ruling), a resting order monopolises the single engine slot —
"an order is already working" fired 28 times on a sample day versus 14 with the cancel on. The
selector models cap slots at FILL time and cannot see that, so it is stated here rather than
silently assumed away.

HOLDOUT IS SEALED. --include-holdout is off by default and warns when used; the sealed 2023/24
days run once, frozen, at the very end (handoff §3).

    python -m scripts.raw_validated_book_london
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select  # noqa: E402
from src.canon.scorer import LON_RISK_MIN, london_checks  # noqa: E402

NY = "America/New_York"


def candidates(span: str) -> pd.DataFrame:
    F = pd.read_parquet(ROOT / f"output/l3_features_london_{span}.parquet")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = "holdout" if span == "holdout" else pd.to_datetime(F.day).dt.year.astype(str)
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True).dt.tz_convert(NY)
    F["exit_ts"] = pd.to_datetime(F["exit"], format="mixed", utc=True).dt.tz_convert(NY)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)      # normalise to 1 lot
    F["old4"] = F[["W", "FAR", "ROOM", "ASIA"]].sum(axis=1)
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    return F[F.risk >= LON_RISK_MIN].reset_index(drop=True)    # Layer 0


def stats(t: pd.DataFrame, days: int) -> dict:
    """1-lot verdict stats. maxDD is on the chronological equity curve, not on monthly sums."""
    if not len(t):
        return {"n": 0}
    t = t.sort_values("fill_ts")
    eq = t.dollars.cumsum()
    dd = (eq.cummax() - eq).max()
    mo = t.groupby(t.fill_ts.dt.strftime("%Y-%m")).dollars.sum()
    return {"n": len(t), "per_wk": round(len(t) / max(days / 5.0, 1e-9), 2),
            "WR": f"{(t.dollars > 0).mean() * 100:.0f}%", "meanR": round(t.R.mean(), 3),
            "$": round(t.dollars.sum()), "mo_green": f"{int((mo > 0).sum())}/{len(mo)}",
            "maxDD": round(dd), "worst_mo": round(mo.min())}


def concurrency(t: pd.DataFrame) -> tuple[int, float]:
    """Max simultaneously-open positions and max simultaneous open risk ($, 1 lot)."""
    if not len(t):
        return 0, 0.0
    ev = []
    for r in t.itertuples():
        ev.append((r.fill_ts, 1, float(r.risk) * 20.0))
        ev.append((r.exit_ts, -1, -float(r.risk) * 20.0))
    ev.sort(key=lambda x: (x[0], -x[1]))
    n = mx = 0
    risk = mxr = 0.0
    for _, d, rk in ev:
        n += d
        risk += rk
        mx, mxr = max(mx, n), max(mxr, risk)
    return mx, mxr


ARMS = {
    "old4  (shipped: W+FAR+ROOM+ASIA >= 3)": ("old4", 3.0, 3.0),
    "wall  (survivors: W or FAR)": ("wall", 1.0, 1.0),
}
LEVELS = {
    "capped 2/sess + day stop": dict(cap_per_session=2, day_stop_dollars=400.0),
    "uncapped, day stop only": dict(cap_per_session=999, day_stop_dollars=400.0),
    "raw (no cap, no day stop)": dict(cap_per_session=999, day_stop_dollars=1e12),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--include-holdout", action="store_true",
                    help="BURNS THE REFERENDUM — sealed days run once, at the very end")
    a = ap.parse_args()
    spans = ["fit"] + (["holdout"] if a.include_holdout else [])
    if a.include_holdout:
        print("!! sealed 2023/24 days are in this run — if anything changes after seeing it, "
              "the holdout is spent and Angus must be told.\n")

    C = pd.concat([candidates(s) for s in spans], ignore_index=True)
    eras = sorted(C.era.unique())
    print(f"L4 candidates (risk >= {LON_RISK_MIN}, 1 lot): {len(C)} on {C.day.nunique()} days "
          f"| eras {eras}")

    for arm_label, (col, thr, esc) in ARMS.items():
        print(f"\n{'=' * 104}\n{arm_label}\n{'=' * 104}")
        for lvl_label, kw in LEVELS.items():
            pol = L4Policy(threshold={"london": thr}, escalation_threshold={"london": esc}, **kw)
            book = select(C.assign(score=C[col]), pol)
            print(f"\n  {lvl_label}")
            for e in eras:
                b = book[book.era == e]
                t = b[b.taken]
                s = stats(t, b.day.nunique())
                mx, mxr = concurrency(t)
                if not s["n"]:
                    print(f"    {e:>8}: (no takes)")
                    continue
                print(f"    {e:>8}: n={s['n']:>4} {s['per_wk']:>5}/wk  WR {s['WR']:>4}  "
                      f"meanR {s['meanR']:>+6.3f}  ${s['$']:>+8,}  green {s['mo_green']:>5}  "
                      f"maxDD ${s['maxDD']:>6,}  worst ${s['worst_mo']:>+7,}  "
                      f"| concurrent max {mx}, open risk ${mxr:,.0f}")
            kills = book[~book.taken].kill_reason.value_counts().to_dict()
            print(f"    kills: {kills}")


if __name__ == "__main__":
    main()
