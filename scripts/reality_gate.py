#!/usr/bin/env python3
"""REALITY GATE - run this on every trade dump BEFORE reading its results.

It does not measure edge. It measures whether the numbers are believable. Each check is a
symptom that, in this repository's history, came from an execution assumption rather than a
market edge (the 2026-09-04 fill-bar finding tripped all five hard checks). If any hard check
trips, the script exits 1 and the summary must not be quoted anywhere.

Usage:
    python3 scripts/reality_gate.py DUMP.jsonl.gz [DUMP2 ...] [--depth 3.0] [--target 1.0]
                                    [--cost-pts 0.5] [--tick 0.25]

Dumps are the engine's jsonl.gz trade files (fields: day, dir, entry, risk, res, r, fill_hrs,
hold_min, target_r, depth, ...). VWAP dumps carry a depth x target grid: pass --depth/--target
to score one cell, as the rail pass does.
"""
import argparse, gzip, json, sys, math
import numpy as np, pandas as pd

HARD = [  # (key, label, threshold text, direction, threshold, why it matters)
    ("same_bar_win_share", "winners that exited on their own fill bar", "> 5%", ">", 0.05,
     "a bar's high/low can print BEFORE the fill; crediting it is lookahead inside the bar"),
    ("win_excess", "win rate above the break-even rate for the target size", "> +15 pts", ">", 0.15,
     "with a 1:1 stop/target a real level edge shows up as a few points, not fifteen"),
    ("sharpe_ann", "annualised Sharpe (daily net R)", "> 3", ">", 3.0,
     "no discretionary or systematic book prints this; simulators do"),
    ("worst_eq_dd", "worst day equals the max drawdown (>=200 days)", "within 1%", ">", 0.99,
     "losses never chaining means the simulator is smoothing something real"),
    ("months_all_green", "no losing month (>=12 months)", "0 red months", ">", 0.999,
     "a perfect monthly record is a modelling artefact until proven on live fills"),
]
SOFT = [
    ("hold_median", "median hold time", "< 2 minutes", "<", 2.0,
     "sub-2-minute holds mean the result lives inside single bars; verify on 1-second data"),
    ("edge_over_cost", "net edge per trade divided by cost per trade", "< 3x", "<", 3.0,
     "an edge this thin is inside the slippage error band"),
    ("ambig_share", "trades whose exit bar touched both stop and target", "> 3%", ">", 0.03,
     "each one is a coin flip the simulator is deciding for you"),
]

def load(paths, depth, target):
    rows = []
    for p in paths:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                t = json.loads(line)
                if depth is not None and "depth" in t and float(t["depth"]) != depth: continue
                if target is not None and "target_r" in t and float(t["target_r"]) != target: continue
                t["_src"] = p.split("/")[-1]
                rows.append(t)
    return pd.DataFrame(rows)

def compute(df, cost_pts):
    df = df.copy()
    df["netr"] = df["r"] - cost_pts / df["risk"]
    tgt = df["target_r"].median() if "target_r" in df else 1.0
    wins = df[df["res"] == "TARGET"]
    ts = df["res"].isin(["TARGET", "STOP"])
    m = {}
    m["trades"] = len(df); m["days"] = df["day"].nunique()
    m["same_bar_win_share"] = float((wins["hold_min"] == 0).mean()) if len(wins) else 0.0
    wr = float((df["res"] == "TARGET").sum() / max(1, ts.sum()))
    m["win_rate"] = wr; m["breakeven"] = 1.0 / (1.0 + tgt); m["win_excess"] = wr - m["breakeven"]
    day = df.groupby("day")["netr"].sum().sort_index()
    m["sharpe_ann"] = float(day.mean() / day.std() * math.sqrt(252)) if len(day) > 1 and day.std() > 0 else 0.0
    cum = day.cumsum(); dd = float((cum - cum.cummax()).min()); worst = float(day.min())
    m["max_dd"] = dd; m["worst_day"] = worst
    m["worst_eq_dd"] = (worst / dd) if (dd < 0 and len(day) >= 200) else 0.0
    month = day.groupby(day.index.str[:7]).sum()
    m["months"] = len(month); m["red_months"] = int((month < 0).sum())
    m["months_all_green"] = 1.0 if (len(month) >= 12 and m["red_months"] == 0) else 0.0
    m["hold_median"] = float(df["hold_min"].median())
    cost_r = float((cost_pts / df["risk"]).mean())
    m["net_per_trade"] = float(df["netr"].mean()); m["cost_per_trade"] = cost_r
    m["edge_over_cost"] = m["net_per_trade"] / cost_r if cost_r > 0 else 0.0
    m["ambig_share"] = float(df["ambig"].mean()) if "ambig" in df else float("nan")
    m["net_R"] = float(df["netr"].sum()); m["R_day"] = float(day.mean())
    return m

def trip(val, direction, thr):
    if val is None or (isinstance(val, float) and math.isnan(val)): return False
    return val > thr if direction == ">" else val < thr

def fmt(key, v):
    if key in ("same_bar_win_share", "win_excess", "ambig_share", "worst_eq_dd"): return f"{v:.1%}" if not math.isnan(v) else "n/a"
    if key == "months_all_green": return "yes" if v else "no"
    return f"{v:.2f}"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dumps", nargs="+"); ap.add_argument("--depth", type=float); ap.add_argument("--target", type=float)
    ap.add_argument("--cost-pts", type=float, default=0.5); ap.add_argument("--tick", type=float, default=0.25)
    a = ap.parse_args()
    df = load(a.dumps, a.depth, a.target)
    if df.empty: print("no trades loaded"); return 2
    m = compute(df, a.cost_pts)
    print(f"REALITY GATE  {', '.join(sorted(df['_src'].unique()))}")
    print(f"  {m['trades']:,} trades over {m['days']:,} days | net {m['net_R']:+,.0f}R | {m['R_day']:+.2f} R/day | "
          f"{m['net_per_trade']:+.4f} R/trade | win {m['win_rate']:.1%} (break-even {m['breakeven']:.1%}) | "
          f"max DD {m['max_dd']:+.1f} | worst day {m['worst_day']:+.1f} | red months {m['red_months']}/{m['months']}")
    tripped = []
    print("\n  HARD CHECKS (any trip = do not quote these results)")
    for key, label, thr_txt, d, thr, why in HARD:
        t = trip(m[key], d, thr); tripped += [key] if t else []
        print(f"  [{'TRIP' if t else ' ok '}] {label:<58} {fmt(key, m[key]):>8}   limit {thr_txt}")
        if t: print(f"         -> {why}")
    print("\n  SOFT CHECKS (warnings)")
    for key, label, thr_txt, d, thr, why in SOFT:
        t = trip(m[key], d, thr)
        print(f"  [{'WARN' if t else ' ok '}] {label:<58} {fmt(key, m[key]):>8}   limit {thr_txt}")
        if t: print(f"         -> {why}")
    print()
    if tripped:
        print(f"  VERDICT: NOT BELIEVABLE ({len(tripped)} hard check(s) tripped). Find the modelling error before anything else.")
        print("  Next steps: (1) exits must be scanned from the bar AFTER the fill (--exit-next-bar); "
              "(2) replay a few days on 1-second data (scripts/sec_replay.py); (3) run the rules in a second simulator.")
        return 1
    print("  VERDICT: passes the believability checks. This says the numbers are not obviously an artefact; it does not say they are good.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
