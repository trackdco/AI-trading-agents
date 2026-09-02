#!/usr/bin/env python3
"""PD VA BREAK-RETEST — report layer over the sweep's trade dump.

    python -m scripts.pd_va_report

Reads output/analysis/pd_va_trades.jsonl.gz (from scripts.pd_va_backtest)
and prints the tables his questions need:

  1. Config sweep, ASIA+LONDON strategy (signal AND fill before 09:30):
     depth x target R -> n, WR, net R, net points, R/day.
  2. Same sweep, NY window only — the "probably won't work in NY" check.
  3. Headline config (depth 0, 1.5R): monthly net points (his ~800pt/month
     claim), split-half and yearly stability, per-leg breakdown, trades/day
     distribution (his "0 or 5+" claim), day WR distribution (his "50-75%
     day on day"), PD-range quartile vs trade count (pump/dump -> 0 trades).

WR convention: wins = TARGET exits, losses = STOP exits, WR = W/(W+L);
FLAT (force-flat at session end) excluded from WR, included in net R/points.
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AL_CUT_H = 15.5
HEAD_DEPTH, HEAD_R = 0.0, 1.5


def is_al(t):
    return t["t_sig_hrs"] < AL_CUT_H and t["fill_hrs"] < AL_CUT_H


def agg(ts):
    w = sum(1 for t in ts if t["res"] == "TARGET")
    l = sum(1 for t in ts if t["res"] == "STOP")
    fl = sum(1 for t in ts if t["res"] == "FLAT")
    ndays = len({t["day"] for t in ts})
    net_r = sum(t["r"] for t in ts)
    return {"n": len(ts), "w": w, "l": l, "flat": fl,
            "wr": w / (w + l) if w + l else 0.0,
            "net_r": net_r, "net_pts": sum(t["pts"] for t in ts),
            "r_day": net_r / ndays if ndays else 0.0, "days": ndays,
            "ambig": sum(1 for t in ts if t["ambig"])}


def line(label, a):
    return (f"  {label:16} n={a['n']:6}  WR {a['wr']:6.1%}  "
            f"net {a['net_r']:+9.1f}R {a['net_pts']:+11.0f}pt  "
            f"{a['r_day']:+.3f}R/day  flat={a['flat']} ambig={a['ambig']}")


def main() -> int:
    rows = [json.loads(l) for l in
            gzip.open(ROOT / "output/analysis/pd_va_trades.jsonl.gz", "rt")]
    days_meta = json.loads((ROOT / "output/analysis/pd_va_days.json").read_text())
    cfg = defaultdict(list)
    for t in rows:
        cfg[(t["depth"], t["target_r"])].append(t)
    depths = sorted({d for d, _ in cfg})
    targets = sorted({r for _, r in cfg})

    print("=" * 78)
    print("1. ASIA+LONDON strategy (signal and fill before 09:30)")
    print("=" * 78)
    for d in depths:
        print(f"\n-- close-through depth {'any tick' if d == 0 else f'>={d:.0f}pt'}")
        for r in targets:
            al = [t for t in cfg[(d, r)] if is_al(t)]
            print(line(f"target {r}R", agg(al)))

    print("\n" + "=" * 78)
    print("2. NY window alone (signal 09:30-15:55) — his 'won't work in NY' check")
    print("=" * 78)
    for d in depths:
        print(f"\n-- depth {'any tick' if d == 0 else f'>={d:.0f}pt'}")
        for r in targets:
            nyt = [t for t in cfg[(d, r)] if t["window"] == "NY"]
            print(line(f"target {r}R", agg(nyt)))

    head = [t for t in cfg[(HEAD_DEPTH, HEAD_R)] if is_al(t)]
    print("\n" + "=" * 78)
    print(f"3. HEADLINE: depth=any tick, target {HEAD_R}R, Asia+London")
    print("=" * 78)

    print("\n3a. per window / per leg")
    for wname in ("ASIA", "LONDON"):
        print(line(wname, agg([t for t in head if t["window"] == wname])))
    for leg in ("breakout_up", "breakout_down", "reversion_up", "reversion_down"):
        print(line(leg, agg([t for t in head if t["leg"] == leg])))

    print("\n3b. yearly + split-half")
    years = sorted({t["day"][:4] for t in head})
    for y in years:
        print(line(y, agg([t for t in head if t["day"].startswith(y)])))
    all_days = sorted({t["day"] for t in head})
    mid = all_days[len(all_days) // 2]
    print(line("first half", agg([t for t in head if t["day"] < mid])))
    print(line(f"since {mid}", agg([t for t in head if t["day"] >= mid])))

    print("\n3c. monthly net points (his ~800pt month claim), last 15 months")
    mon = defaultdict(list)
    for t in head:
        mon[t["day"][:7]].append(t)
    mons = sorted(mon)
    pts_all = [sum(x["pts"] for x in mon[m]) for m in mons]
    for m in mons[-15:]:
        a = agg(mon[m])
        print(f"  {m}: {a['net_pts']:+8.0f}pt  {a['net_r']:+7.1f}R  "
              f"n={a['n']:4}  WR {a['wr']:5.1%}")
    print(f"  ALL {len(mons)} months: median {np.median(pts_all):+.0f}pt  "
          f"mean {np.mean(pts_all):+.0f}pt  "
          f"best {max(pts_all):+.0f}  worst {min(pts_all):+.0f}  "
          f"positive {sum(1 for p in pts_all if p > 0)}/{len(pts_all)}")

    print("\n3d. trades/day distribution (his '0 or 5+' claim)")
    per_day = defaultdict(int)
    for t in head:
        per_day[t["day"]] += 1
    for dm in days_meta:
        per_day.setdefault(dm, 0)
    counts = np.array(sorted(per_day.values()))
    hist = defaultdict(int)
    for c in counts:
        hist[min(c, 8)] += 1
    print("  " + "  ".join(f"{k if k < 8 else '8+'}:{hist[k]}"
                           for k in sorted(hist)))
    print(f"  mean {counts.mean():.1f}/day  zero-trade days "
          f"{(counts == 0).sum()}/{len(counts)}")

    print("\n3e. day-level WR distribution (his '50-75% day on day')")
    daywr = []
    for dday, nn in per_day.items():
        ts = [t for t in head if t["day"] == dday]
        w = sum(1 for t in ts if t["res"] == "TARGET")
        l = sum(1 for t in ts if t["res"] == "STOP")
        if w + l >= 2:
            daywr.append(w / (w + l))
    daywr = np.array(daywr)
    print(f"  days with >=2 decided trades: {len(daywr)}  "
          f"median {np.median(daywr):.0%}  "
          f"P25 {np.percentile(daywr, 25):.0%}  P75 {np.percentile(daywr, 75):.0%}  "
          f"days >=50% WR: {(daywr >= 0.5).mean():.0%}")

    print("\n3f. prior-day range vs activity (pump/dump -> 0 trades claim)")
    prs = np.array([days_meta[d]["pd_range"] for d in sorted(per_day) if d in days_meta])
    cnt = np.array([per_day[d] for d in sorted(per_day) if d in days_meta])
    qs = np.percentile(prs, [25, 50, 75])
    for i, (lo_q, hi_q, lab) in enumerate(
            [(0, qs[0], "Q1 small"), (qs[0], qs[1], "Q2"),
             (qs[1], qs[2], "Q3"), (qs[2], 1e9, "Q4 pump/dump")]):
        m = (prs >= lo_q) & (prs < hi_q)
        print(f"  {lab:12} mean {cnt[m].mean():.1f} trades/day  "
              f"zero-days {(cnt[m] == 0).mean():.0%}")

    print("\n3g. risk-size and hold-time shape")
    risks = np.array([t["risk"] for t in head])
    holds = np.array([t["hold_min"] for t in head])
    waitf = np.array([(t["fill_hrs"] - t["t_sig_hrs"]) * 60 for t in head])
    print(f"  stop size pts: median {np.median(risks):.1f}  "
          f"P25 {np.percentile(risks, 25):.1f}  P75 {np.percentile(risks, 75):.1f}  "
          f"max {risks.max():.1f}")
    print(f"  at 5pt floor: {(risks <= 5.01).mean():.0%} of trades")
    print(f"  minutes signal->fill: median {np.median(waitf):.0f}  "
          f"P90 {np.percentile(waitf, 90):.0f}")
    print(f"  minutes in trade: median {np.median(holds):.0f}  "
          f"P90 {np.percentile(holds, 90):.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
