#!/usr/bin/env python3
"""NYO-ROT-01 trial 1 — overnight rotation census + L1, per
docs/PREREG-orochi-overnight.md. §5.11 standards in force from birth:
event-universe sensitivity (first-touch AND all-touches), year-level
reporting, no bin off raw.

    python -m scripts.nyo_rotation_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    yrs = " ".join(f"{y}:{x.sum():+.0f}" for y, x in net.groupby(T.year))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {yrs}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    ON = B[(B.clock >= "18:00") | (B.clock < "09:25")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")

    first, allt = [], []
    n_days = 0
    for d, r in ON.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc, width = float(C.loc[d, "comp_poc"]), float(C.loc[d, "comp_vah"]) - float(C.loc[d, "comp_val"])
        if width <= 0:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 400:
            continue
        n_days += 1
        in_pos, day_first_done = None, False
        for k, row in r.iterrows():
            if in_pos is None:
                if row.close > vah or row.close < val:
                    break  # left the balance overnight -> rotation state over
                side = -1 if row.high >= vah else (1 if row.low <= val else 0)
                if side:
                    edge = vah if side < 0 else val
                    stop = edge - side * 0.25 * width
                    in_pos = dict(side=side, entry=edge, stop=stop, first=not day_first_done)
                    day_first_done = True
            else:
                s = in_pos["side"]
                pts = None
                if s < 0:
                    if row.high >= in_pos["stop"]: pts = in_pos["entry"] - in_pos["stop"]
                    elif row.low <= poc: pts = in_pos["entry"] - poc
                else:
                    if row.low <= in_pos["stop"]: pts = in_pos["stop"] - in_pos["entry"]
                    elif row.high >= poc: pts = poc - in_pos["entry"]
                if pts is not None:
                    rec = dict(day=d, year=d[:4], pts=pts,
                               risk=abs(in_pos["entry"] - in_pos["stop"]))
                    allt.append(rec)
                    if in_pos["first"]:
                        first.append(rec)
                    in_pos = None
                    if row.close > vah or row.close < val:
                        break
        if in_pos is not None:
            cl = r.close.iloc[-1]
            pts = (in_pos["entry"] - cl) if in_pos["side"] < 0 else (cl - in_pos["entry"])
            rec = dict(day=d, year=d[:4], pts=pts, risk=abs(in_pos["entry"] - in_pos["stop"]))
            allt.append(rec)
            if in_pos["first"]:
                first.append(rec)
    F, A = pd.DataFrame(first), pd.DataFrame(allt)
    A.to_parquet(ROOT / "output/nyo_rotation_census.parquet", index=False)
    print(f"composite-live overnight sessions: {n_days}")
    rep(F, "first-touch (as-taught primary)")
    rep(A, "all-touches (§5.11 event sensitivity)")


if __name__ == "__main__":
    main()
