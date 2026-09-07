#!/usr/bin/env python3
"""
Diagnostics for steps 1 and 2 (development window only; reported, not binding).

  step 1  --stop-model SEALED.json INTRABAR.json [more pairs...]
          close-based (bot as shipped) vs resting-order stops: n, WR, mean, LB95, PF, DD,
          exit anatomy, loss per nominal stop, holding time, intrabar counters.
  step 2  --levels RUN_WITH_LEVELS.json
          outcomes by swept-level class and by the detector's own inputs, with per-year stability.
"""
import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from analyze_retest import block_bootstrap_lb  # noqa: E402

ET = ZoneInfo("America/New_York")


def load(path):
    d = json.load(open(path))
    ent = {r["trade_id"]: r for r in d["records"] if r["action"] == "entry"}
    out = []
    for r in d["records"]:
        if r["action"] != "exit" or r["trade_id"] not in ent:
            continue
        e = ent[r["trade_id"]]
        t = datetime.fromisoformat(e["timestamp"]).astimezone(ET)
        out.append({"entry_ts": e["timestamp"], "adjusted_pnl": r["adjusted_pnl"], "pnl": r["adjusted_pnl"],
                    "stop": e["stop_distance"], "atr": e["atr"], "c1r": r["c1_exit_reason"], "c2r": r["c2_exit_reason"],
                    "bars": r["bar_index"] - e["bar_index"], "year": t.year, "levels": e.get("swept_levels"),
                    "depth": e.get("sweep_depth_pts"), "vr": e.get("volume_ratio"), "rb": e.get("reclaim_bars")})
    return d, out


def summary(tr):
    p = [t["pnl"] for t in tr]
    n = len(p)
    if not n:
        return {"n": 0}
    w = [x for x in p if x > 0]; l = [x for x in p if x < 0]
    cum = peak = dd = 0.0
    for x in p:
        cum += x; peak = max(peak, cum); dd = max(dd, peak - cum)
    lb, _ = block_bootstrap_lb(tr)
    both_stop = sum(1 for t in tr if t["c1r"] == "stop" and t["c2r"] == "stop")
    lossR = [(-t["pnl"]) / (t["stop"] * 4) for t in tr if t["pnl"] < 0 and t["stop"] > 0]
    return {"n": n, "WR": 100 * len(w) / n, "mean": st.mean(p), "lb95": lb, "PF": (sum(w) / -sum(l)) if l else float("inf"),
            "total": sum(p), "dd": dd, "avg_win": st.mean(w) if w else 0, "avg_loss": st.mean(l) if l else 0,
            "both_stop_pct": 100 * both_stop / n, "loss_R_med": st.median(lossR) if lossR else 0,
            "hold_med_bars": st.median(t["bars"] for t in tr)}


def fmt(s):
    if s["n"] == 0:
        return "| 0 |"
    lb = f"{s['lb95']:+.2f}" if s['lb95'] is not None else "n/a"
    return (f"| {s['n']} | {s['WR']:.1f} | {s['mean']:+.2f} | {lb} | {s['PF']:.3f} | {s['total']:+,.0f} | {s['dd']:,.0f} | "
            f"{s['avg_win']:+.1f} / {s['avg_loss']:+.1f} | {s['both_stop_pct']:.0f}% | {s['loss_R_med']:.2f} | {s['hold_med_bars']:.0f} |")


HDR = "| run | n | WR% | mean $ | LB95 $ | PF | total $ | maxDD $ | avg win / loss | both-stopped | median loss / stop | median hold (bars) |\n|---|---|---|---|---|---|---|---|---|---|---|---|"


def step1(pairs):
    print("## Step 1 — stop model: bot as shipped (stops on 2m close, filled at close) vs resting-order stops on 1m bars\n")
    print(HDR)
    for sealed, ib in pairs:
        ds, ts = load(sealed); di, ti = load(ib)
        name = sealed.split("/")[-1].replace(".json", "")
        print(f"| {name} — close-based " + fmt(summary(ts)))
        print(f"| {ib.split('/')[-1].replace('.json', '')} — intrabar " + fmt(summary(ti)))
        c = di["meta"].get("intrabar_counters")
        print(f"|  intrabar counters: {c} |")
        # per-year
        print("|  per year (mean $/trade, n): " + "; ".join(
            f"{y}: close {st.mean([t['pnl'] for t in ts if t['year']==y]):+.1f} ({sum(1 for t in ts if t['year']==y)}) vs intrabar {st.mean([t['pnl'] for t in ti if t['year']==y]):+.1f} ({sum(1 for t in ti if t['year']==y)})"
            for y in sorted({t['year'] for t in ts})) + " |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")


def classify(levels):
    if not levels:
        return "unknown"
    kinds = set()
    for n in levels:
        if n.startswith("round_"):
            kinds.add("round")
        elif n in ("PDH", "PDL", "PWH", "PWL"):
            kinds.add("structural")
        elif n == "VWAP":
            kinds.add("vwap")
        else:
            kinds.add(n)
    if kinds == {"round"}:
        return "round only"
    if kinds == {"structural"}:
        return "structural only (PDH/PDL/PWH/PWL)"
    if kinds == {"vwap"}:
        return "VWAP only"
    return "mixed (" + "+".join(sorted(kinds)) + ")"


def table(title, tr, key, order=None):
    g = defaultdict(list)
    for t in tr:
        g[key(t)].append(t)
    keys = order or sorted(g, key=lambda k: -len(g[k]))
    print(f"\n**{title}**\n")
    print("| bucket | n | share | WR% | mean $ | LB95 $ | total $ | " + " | ".join(f"{y} mean (n)" for y in (2021, 2022, 2023, 2024)) + " |")
    print("|---|---|---|---|---|---|---|" + "---|" * 4)
    for k in keys:
        x = g.get(k, [])
        if not x:
            continue
        s = summary(x)
        yrs = []
        for y in (2021, 2022, 2023, 2024):
            xy = [t for t in x if t["year"] == y]
            yrs.append(f"{st.mean(t['pnl'] for t in xy):+.1f} ({len(xy)})" if xy else "—")
        lb = f"{s['lb95']:+.2f}" if s['lb95'] is not None else "n/a"
        print(f"| {k} | {s['n']} | {100*s['n']/len(tr):.0f}% | {s['WR']:.1f} | {s['mean']:+.2f} | {lb} | {s['total']:+,.0f} | " + " | ".join(yrs) + " |")


def step2(path):
    d, tr = load(path)
    print(f"\n## Step 2 — swept-level types, {path.split('/')[-1]} (dev window, n={len(tr)})\n")
    table("By level class", tr, lambda t: classify(t["levels"]))
    table("By number of levels swept (the '≥2 levels' score bonus)", tr, lambda t: f"{min(len(t['levels'] or []), 3)} level(s)" if t["levels"] else "unknown", ["1 level(s)", "2 level(s)", "3 level(s)"])
    table("By sweep depth (pts past the level)", tr, lambda t: "2–3" if t["depth"] < 3 else ("3–8 (bonus band)" if t["depth"] <= 8 else (">8–15" if t["depth"] <= 15 else ">15")), ["2–3", "3–8 (bonus band)", ">8–15", ">15"])
    table("By volume ratio at the sweep", tr, lambda t: "<1.5" if t["vr"] < 1.5 else ("1.5–2" if t["vr"] < 2 else ("2–3 (bonus)" if t["vr"] < 3 else "≥3 (bonus)")), ["<1.5", "1.5–2", "2–3 (bonus)", "≥3 (bonus)"])
    table("By reclaim bars (sweep candle → reclaim close)", tr, lambda t: f"{t['rb']} bar(s)", ["1 bar(s)", "2 bar(s)", "3 bar(s)"])
    # round-number grid position: is the level a 100/500/1000 multiple?
    def grid(t):
        rs = [int(n.split("_")[1]) for n in (t["levels"] or []) if n.startswith("round_")]
        if not rs:
            return "no round level"
        r = rs[0]
        return "x1000" if r % 1000 == 0 else ("x500" if r % 500 == 0 else ("x100" if r % 100 == 0 else "x50 only"))
    table("Round-number sweeps by grid coarseness", tr, grid, ["x50 only", "x100", "x500", "x1000", "no round level"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stop-model", nargs="+", help="pairs: SEALED.json INTRABAR.json ...")
    ap.add_argument("--levels", default=None)
    a = ap.parse_args()
    if a.stop_model:
        it = iter(a.stop_model); step1(list(zip(it, it)))
    if a.levels:
        step2(a.levels)
