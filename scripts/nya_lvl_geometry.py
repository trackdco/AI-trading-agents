#!/usr/bin/env python3
"""NYA-LVL-01 stage 2 — geometry grid, early-cut overlay, and the placebo-level null.

Authorised by docs/PREREG-level-interaction-stage2.md, committed before this file.
Every arm and the null design are frozen there.

Declared default (named on mechanism, not searched): stop 20pts / target 30pts.
Grid: stops 10/15/20/25/30/40 x targets 15/20/25/30/40/50 + T_LADDER + TRAIL_BE = 48.
Overlay: early cut if not green by t+5/15/30, default geometry only = 3.
Plus Version A vs B at the default = 1.  Total 52 declared arms.

Null: replace the six real levels with six random levels drawn from the same day's
pre-RTH range, re-run the ENTIRE 52-arm search, take the family-wise max. 200 perms.

    python -m scripts.nya_lvl_geometry [--perms N] [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import (LEVELS, PM_WINDOW, PD_WINDOW, RTH, TICK,  # noqa: E402
                                    load_bars, m15)
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-stage2.md"
OUT_MD = ROOT / "output/nya_lvl_geometry.md"
OUT_PARQUET = ROOT / "output/nya_lvl_geometry.parquet"

FIT_START, FIT_END = "2025-06-02", "2026-07-15"
STOPS = [10.0, 15.0, 20.0, 25.0, 30.0, 40.0]
TARGETS = [15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
DEF_STOP, DEF_TGT = 20.0, 30.0
TRAIL_GAP = 15.0
COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
SEED = 20260805
MAX_HOLD = 240          # minutes; hard flat at RTH end anyway


def paths(bars: pd.DataFrame, rng: np.random.Generator | None = None):
    """One row per touch, carrying the forward 1-minute path indices.

    rng not None -> PLACEBO: six random levels drawn from the day's pre-RTH range.
    """
    days = [d for d in sorted(bars["day"].unique()) if FIT_START <= d <= FIT_END]
    prior = None
    ev_dir, ev_lvl, ev_day, ev_type, ev_pathstart, ev_ladder = [], [], [], [], [], []
    paths_store: list[np.ndarray] = []

    for day in days:
        db = bars[bars["day"] == day]
        pm = db[(db["min"] >= PM_WINDOW[0]) & (db["min"] < PM_WINDOW[1])]
        pdw = db[(db["min"] >= PD_WINDOW[0]) & (db["min"] < PD_WINDOW[1])]
        rth = db[(db["min"] >= RTH[0]) & (db["min"] < RTH[1])]

        if len(pm) >= 60 and len(rth) >= 200 and prior is not None:
            if rng is None:
                lv = {"PM_HIGH": float(pm["high"].max()), "PM_LOW": float(pm["low"].min()),
                      "PD_HIGH": prior["hi"], "PD_LOW": prior["lo"]}
                lv["PM_50"] = (lv["PM_HIGH"] + lv["PM_LOW"]) / 2
                lv["PD_50"] = (lv["PD_HIGH"] + lv["PD_LOW"]) / 2
            else:
                lo = min(float(pm["low"].min()), prior["lo"])
                hi = max(float(pm["high"].max()), prior["hi"])
                draw = rng.uniform(lo, hi, size=6)
                lv = dict(zip(LEVELS, draw))
            b15 = m15(rth)
            if len(b15) >= 4:
                mb = rth[["high", "low", "close"]].to_numpy(float)
                ts = list(rth["ts_event"])
                rth_open = float(rth.iloc[0]["open"])
                for bi in range(len(b15)):
                    bar = b15.iloc[bi]
                    bts = b15.index[bi]
                    prev_c = float(b15.iloc[bi - 1]["close"]) if bi else rth_open
                    for name in LEVELS:
                        level = lv[name]
                        if not (bar["low"] <= level <= bar["high"]):
                            continue
                        d = -1 if prev_c < level else 1
                        filled = (bar["high"] >= level + TICK) if d < 0 else \
                                 (bar["low"] <= level - TICK)
                        if not filled:
                            continue
                        start = next((i for i, t in enumerate(ts) if t > bts), None)
                        if start is None or start >= len(mb) - 2:
                            continue
                        cands = [v for v in lv.values()
                                 if (v > level + TICK if d > 0 else v < level - TICK)]
                        lad = (min(cands) if d > 0 else max(cands)) if cands else np.nan
                        ev_dir.append(d); ev_lvl.append(level); ev_day.append(day)
                        ev_type.append(name); ev_ladder.append(lad)
                        ev_pathstart.append(len(paths_store))
                        paths_store.append(mb[start:start + MAX_HOLD])
        if len(pdw) >= 100:
            prior = {"hi": float(pdw["high"].max()), "lo": float(pdw["low"].min()),
                     "close": float(pdw.iloc[-1]["close"])}
    return (np.array(ev_dir), np.array(ev_lvl), np.array(ev_day), np.array(ev_type),
            np.array(ev_ladder), paths_store)


def run_cell(d: int, entry: float, path: np.ndarray, stop_pts: float,
             tgt: float | None, trail: bool, cut_min: int | None) -> float:
    """Points for one event under one geometry. Conservative: stop before target."""
    stop = entry - d * stop_pts
    best = 0.0
    for i, (hi, lo, cl) in enumerate(path):
        # ORDER MATTERS. The stop in force during this bar is the one set at the END of
        # the previous bar. Updating the trail from this bar's high and then testing
        # this bar's low is intrabar lookahead — it assumes the favourable extreme came
        # first, which the data cannot tell us. Check first, trail after.
        if (lo <= stop) if d > 0 else (hi >= stop):
            return (stop - entry) if d > 0 else (entry - stop)
        if tgt is not None and ((hi >= tgt) if d > 0 else (lo <= tgt)):
            return abs(tgt - entry)
        if cut_min is not None and (i + 1) >= cut_min:
            cur = (cl - entry) if d > 0 else (entry - cl)
            if cur <= 0:
                return cur
        fav = (hi - entry) if d > 0 else (entry - lo)
        best = max(best, fav)
        if trail and best >= stop_pts:              # break-even at +1R, then trail
            stop = (max(stop, entry + (best - TRAIL_GAP)) if d > 0
                    else min(stop, entry - (best - TRAIL_GAP)))
    cl = path[-1][2]
    return (cl - entry) if d > 0 else (entry - cl)


def arm_grid() -> list[tuple]:
    """(label, stop_pts, target_mode, target_pts, trail, cut) — the 52 declared arms."""
    arms = []
    for s in STOPS:
        for t in TARGETS:
            arms.append((f"S{s:.0f}/T{t:.0f}", s, "fixed", t, False, None))
        arms.append((f"S{s:.0f}/LADDER", s, "ladder", None, False, None))
        arms.append((f"S{s:.0f}/TRAIL", s, "none", None, True, None))
    for c in (5, 15, 30):
        arms.append((f"DEFAULT+cut{c}", DEF_STOP, "fixed", DEF_TGT, False, c))
    return arms


def evaluate(ev, arms, cost: float) -> dict[str, np.ndarray]:
    d, lvl, day, typ, lad, ps = ev
    out = {}
    for label, s, tmode, tpts, trail, cut in arms:
        pts = np.empty(len(d))
        for i in range(len(d)):
            if tmode == "fixed":
                tgt = lvl[i] + d[i] * tpts
            elif tmode == "ladder":
                tgt = lad[i]
                if not np.isfinite(tgt):
                    pts[i] = np.nan
                    continue
            else:
                tgt = None
            pts[i] = run_cell(int(d[i]), float(lvl[i]), ps[i], s, tgt, trail, cut)
        out[label] = pts - cost
    return out


def r_of(net: np.ndarray, stop_pts: float) -> float:
    v = net[np.isfinite(net)]
    return float(np.mean(v / stop_pts)) if len(v) else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bars = load_bars()
    arms = arm_grid()
    print(f"{len(arms)} declared arms")
    ev = paths(bars)
    d, lvl, day, typ, lad, ps = ev
    print(f"{len(d):,} filled events on the fit span")

    era = np.array([x[:4] for x in day])
    half = np.array([x[:4] + ("H1" if int(x[5:7]) <= 6 else "H2") for x in day])
    rows = []
    for cost, cl in COSTS:
        res = evaluate(ev, arms, cost)
        for (label, s, tmode, tpts, trail, cut) in arms:
            net = res[label]
            ok = np.isfinite(net)
            rec = {"arm": label, "stop": s, "cost": cl, "n": int(ok.sum()),
                   "wr": float((net[ok] > 0).mean()), "pts": float(net[ok].sum()),
                   "pf": float(net[ok][net[ok] > 0].sum() /
                               max(-net[ok][net[ok] <= 0].sum(), 1e-9)),
                   "r": r_of(net, s)}
            for e in ("2025", "2026"):
                m = ok & (era == e)
                rec[f"r_{e}"] = r_of(net[m], s) if m.sum() else float("nan")
                rec[f"n_{e}"] = int(m.sum())
            for h in ("2025H1", "2025H2", "2026H1", "2026H2"):
                m = ok & (half == h)
                rec[f"pf_{h}"] = (float(net[m][net[m] > 0].sum() /
                                        max(-net[m][net[m] <= 0].sum(), 1e-9))
                                  if m.sum() else float("nan"))
            rows.append(rec)
    G = pd.DataFrame(rows)

    # --- the placebo-level null: re-run the WHOLE search on random levels -----------
    rng = np.random.default_rng(SEED)
    obs_best = G[(G.cost == "base")]["r"].max()
    null_best = []
    for k in range(args.perms):
        pev = paths(bars, rng)
        if len(pev[0]) < 100:
            continue
        pres = evaluate(pev, arms, 1.0)
        bb = max(r_of(pres[a[0]], a[1]) for a in arms)
        null_best.append(bb)
        if (k + 1) % 25 == 0:
            arr = np.array(null_best)
            print(f"  perm {k+1}/{args.perms}  p={np.mean(arr >= obs_best):.4f}", flush=True)
    nb = np.array(null_best)
    p_fw = float(np.mean(nb >= obs_best)) if len(nb) else float("nan")

    text, ledger = report(G, obs_best, nb, p_fw, len(d))
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    G.to_parquet(OUT_PARQUET, index=False)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    print(trial_ledger.summary())
    return 0


def report(G, obs_best, nb, p_fw, nev) -> tuple[str, list[dict]]:
    base = G[G.cost == "base"].sort_values("r", ascending=False)
    strict = G[G.cost == "strict"].set_index("arm")
    dflt = f"S{DEF_STOP:.0f}/T{DEF_TGT:.0f}"
    L = ["# NYA-LVL-01 stage 2 — geometry grid + placebo-level null", "",
         f"Authorised by `{PREREG}`. {len(G)//2} declared arms x 2 cost levels, "
         f"{nev:,} events, fit span only.", "",
         "## 1. The declared default (named on mechanism BEFORE the grid ran)", "",
         "| arm | cost | n | WR | net pts | PF | R/trade | 2025 R | 2026 R |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for cl in ("base", "strict"):
        r = G[(G.arm == dflt) & (G.cost == cl)].iloc[0]
        L.append(f"| **{dflt}** | {cl} | {r.n:,} | {r.wr:.0%} | {r.pts:+,.0f} | "
                 f"{r.pf:.2f} | {r.r:+.3f} | {r.r_2025:+.3f} | {r.r_2026:+.3f} |")
    L.append("")

    L += ["## 2. Top 12 of the 52 arms (base cost) — REPORTED, NOT PROMOTED", "",
          "§6.0.1: in-sample rank never promotes. The default above stays the spec.", "",
          "| arm | n | WR | net pts | PF | R base | R strict | 2025 R | 2026 R | both eras + |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for _, r in base.head(12).iterrows():
        rs = strict.loc[r.arm, "r"]
        both = (r.r_2025 > 0) and (r.r_2026 > 0)
        L.append(f"| `{r.arm}` | {r.n:,} | {r.wr:.0%} | {r.pts:+,.0f} | {r.pf:.2f} | "
                 f"{r.r:+.3f} | {rs:+.3f} | {r.r_2025:+.3f} | {r.r_2026:+.3f} | "
                 f"{'YES' if both else 'no'} |")
    L.append("")

    pos = base[(base.r_2025 > 0) & (base.r_2026 > 0)]
    posb = pos[[strict.loc[a, "r"] > 0 for a in pos.arm]]
    L += [f"**{len(pos)} of {len(base)} arms are positive in BOTH eras at base cost; "
          f"{len(posb)} of those survive strict cost.**", ""]

    L += ["## 3. The null — do the six real levels beat random lines?", "",
          "Six random levels drawn from the same day's pre-RTH range, identical grammar,",
          f"the ENTIRE {len(base)}-arm search re-run, {len(nb)} times. Statistic is the",
          "family-wise best cell.", "",
          "| | value |", "|---|---:|",
          f"| observed best arm (R/trade) | **{obs_best:+.4f}** |",
          f"| null median | {np.median(nb):+.4f} |",
          f"| null 95th pct | {np.percentile(nb, 95):+.4f} |",
          f"| null 99th pct | {np.percentile(nb, 99):+.4f} |",
          f"| **family-wise p** | **{p_fw:.4f}** |", "",
          f"**Declared bar was p <= 0.01. Result: "
          f"{'PASS' if p_fw <= 0.01 else 'FAIL'}.**", ""]
    if p_fw > 0.01:
        L += ["Random lines drawn from the same price zone reach the same best-cell",
              "result as the real six. **On this test the six levels are not doing the",
              "work — the geometry is.** That is a premise finding, not a geometry",
              "finding, and it is the thing the family was built on.", ""]
    else:
        L += ["The real six levels beat random lines in the same zone under an identical",
              "search. The premise survives its own placebo.", ""]

    L += ["## 4. Half-year stability of the default", "",
          "| half | PF (base) |", "|---|---:|"]
    r = G[(G.arm == dflt) & (G.cost == "base")].iloc[0]
    for h in ("2025H1", "2025H2", "2026H1", "2026H2"):
        L.append(f"| {h} | {r[f'pf_{h}']:.2f} |")
    L.append("")

    L += ["## 5. The early-cut overlay (losers never go green — does cutting them help?)",
          "", "| arm | n | WR | PF | R base | R strict |", "|---|---:|---:|---:|---:|---:|"]
    for a in [dflt] + [f"DEFAULT+cut{c}" for c in (5, 15, 30)]:
        rr = G[(G.arm == a) & (G.cost == "base")]
        if rr.empty:
            continue
        rr = rr.iloc[0]
        L.append(f"| `{a}` | {rr.n:,} | {rr.wr:.0%} | {rr.pf:.2f} | {rr.r:+.3f} | "
                 f"{strict.loc[a,'r']:+.3f} |")
    L.append("")

    ledger = []
    for _, r in G[G.cost == "base"].iterrows():
        ledger.append({
            "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
            "trial": f"geom {r.arm} R per trade",
            "stat_type": "mean", "estimate": round(float(r.r), 4), "n": int(r.n),
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"stage-2 grid arm: WR {r.wr:.0%} PF {r.pf:.2f} "
                        f"R {r.r:+.3f} (2025 {r.r_2025:+.3f} / 2026 {r.r_2026:+.3f})"),
        })
    ledger.append({
        "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
        "trial": "placebo-level family-wise null",
        "stat_type": "mean", "estimate": round(p_fw, 5), "n": len(nb),
        "t_stat": 0.0, "effect": 0.0,
        "verdict": (f"{'PASS' if p_fw <= 0.01 else 'FAIL'} vs declared 0.01: observed "
                    f"best {obs_best:+.4f} vs null 95th {np.percentile(nb,95):+.4f}"),
    })
    return "\n".join(L), ledger


if __name__ == "__main__":
    raise SystemExit(main())
