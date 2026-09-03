#!/usr/bin/env python3
"""CONVICTION SIZING, IN-ENGINE — does sizing by tier beat flat risk?

    python -m scripts.conviction_sizing

His ask (2026-09-03), after the conviction audit: test the sizing layer
in-engine rather than post-hoc.

WHAT "IN-ENGINE" MEANS HERE, PRECISELY. Sizing cannot change which
trades are taken, when they fill, or when they exit — a half-size
position occupies the book exactly like a full-size one, and every
guard rail (G1 one-per-book, G3 first-in-wins, G5/G6 caps) is keyed on
position existence and direction, not size. So the trade set is
identical by construction and the honest in-engine question is only:
is the TIER computed correctly, from exact bars, with no lookahead?
That is what `--conviction` does inside `simulate_day`/`simulate`:
the tier is written at fill time from the running session extremes and
the pre-fill excursion window, with the fill bar excluded. Applying a
multiplier to a tagged trade afterwards is exact arithmetic, not an
approximation — so this script does that, and sweeps schemes.

The one rail that could interact is G7 (total open risk <= 4R). Tiered
sizing lowers open risk on every non-A trade, so G7 binds strictly less
often than it does flat — and G5/G6 (its position-count form) never bind
at all in four years. Checked and reported below.

PREREGISTERED DECISION RULE — written before any result was read:
  ADOPT if, after scaling the tiered book so its max drawdown equals the
  flat book's max drawdown, R/day improves by >= 5% in BOTH halves of
  the sample (IS < 2024-10-21 <= OOS).
  WATCH if it improves in both halves by less than 5%.
  KILL otherwise — including any scheme that improves total R only by
  taking more risk.
Drawdown-matched is the bar because the dial (S32) already buys R/day
for drawdown at any multiple; a sizing layer must beat that trade, not
re-sell it. Schemes are fixed below, not tuned; the audit's own
recommendation (A 1.0 / B 0.5 / C 0.5 / D 0.25) is scheme "audit".

Tiers (from the audit, both books, both halves):
  A  ran >= 1R past the level before the retest AND session range >= 0.5x
     prior-day range
  B  displaced only     C  moved-day only     D  neither

Inputs (regenerate with --conviction on both engines):
  output/analysis/pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz
  output/analysis/vwap_rev_tf1_retest_xr30_dd.jsonl.gz
  output/analysis/vwap_rev_tf1_retest_xr30_nyanc_dd.jsonl.gz
Output: printed tables + output/analysis/conviction_sizing.json
"""
from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "analysis"
COST_PTS = 0.5
MID = "2024-10-21"
FLOOR = 5.0

SCHEMES = {
    "flat":      {"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0},
    "audit":     {"A": 1.0, "B": 0.5, "C": 0.5, "D": 0.25},
    "gentle":    {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.5},
    "excur":     {"A": 1.0, "B": 1.0, "C": 0.5, "D": 0.5},   # displacement alone
    "sess":      {"A": 1.0, "B": 0.5, "C": 1.0, "D": 0.5},   # session alone
    "steep*":    {"A": 1.0, "B": 0.5, "C": 0.25, "D": 0.0},
}
# steep* has a ZERO multiplier, so it is NOT size-only: a skipped trade
# frees the book and a later signal takes its place (S34 measured +41R
# from exactly that effect on the stop cap). Its row is an ESTIMATE and
# is excluded from the adoption verdict; the honest version of it is the
# arm-after-displacement build (audit recommendation 3), which pulls the
# resting limit rather than never placing it, and needs its own engine run.
SIZE_ONLY = {k for k, m in SCHEMES.items() if min(m.values()) > 0}


def load(name, champ_cell=False):
    with gzip.open(OUT / name, "rt") as f:
        ts = [json.loads(l) for l in f]
    if champ_cell:
        ts = [t for t in ts if t["depth"] == 3.0 and t["target_r"] == 1.0]
    return ts


def rail_pass(books):
    """The S32 rail pass, unchanged: G3 first-in-wins within one stop
    floor same-direction, G5 global cap 4, G6 same-direction cap 3.
    Size-independent, so it runs once and both schemes read the same
    kept set."""
    byday = defaultdict(list)
    for b in books:
        for t in b:
            byday[t["day"]].append(t)
    kept = defaultdict(list)
    g5 = g6 = 0
    for d, ts in byday.items():
        ts.sort(key=lambda t: (t["fill_hrs"], t["t_sig_hrs"]))
        open_pos = []
        for t in ts:
            f, en = t["fill_hrs"], t["fill_hrs"] + t["hold_min"] / 60
            open_pos = [p for p in open_pos if p[1] > f]
            if any(dr == t["dir"] and abs(px - t["entry"]) <= FLOOR
                   for _, _, dr, px in open_pos):
                continue
            if len(open_pos) >= 4:
                g5 += 1
                continue
            if sum(1 for *_, dr, _ in open_pos if dr == t["dir"]) >= 3:
                g6 += 1
                continue
            open_pos.append((f, en, t["dir"], t["entry"]))
            kept[d].append(t)
    print(f"rail pass: {sum(len(v) for v in kept.values()):,} trades kept "
          f"across {len(kept)} days (G5 bound {g5}x, G6 {g6}x)")
    return kept


def open_risk_p999(kept, mult):
    """G7 check: peak simultaneous open risk in R under a scheme."""
    peak = []
    for d, ts in kept.items():
        evts = []
        for t in ts:
            m = mult[t["tier"]]
            if m <= 0:
                continue
            evts.append((t["fill_hrs"], m))
            evts.append((t["fill_hrs"] + t["hold_min"] / 60, -m))
        evts.sort()
        cur = mx = 0.0
        for _, dv in evts:
            cur += dv
            mx = max(mx, cur)
        peak.append(mx)
    return np.percentile(peak, 99.8), max(peak)


def daily(kept, mult):
    """Per-day net R under a multiplier scheme, in day order."""
    days = sorted(kept)
    out = []
    for d in days:
        s = 0.0
        for t in kept[d]:
            m = mult[t["tier"]]
            if m:
                s += m * (t["r"] - COST_PTS / t["risk"])
        out.append(s)
    return days, np.array(out)


def maxdd(v):
    eq = np.cumsum(v)
    return float((eq - np.maximum.accumulate(eq)).min())


def stats(days, v, label, scale=1.0):
    v = v * scale
    is_m = np.array([d < MID for d in days])
    dd = maxdd(v)
    return {
        "label": label, "scale": round(scale, 4),
        "total_R": round(float(v.sum()), 1),
        "R_day": round(float(v.mean()), 3),
        "maxDD": round(dd, 1),
        "green": round(float((v > 0).mean()), 3),
        "sharpe": round(float(v.mean() / v.std()), 4),
        "worst_day": round(float(v.min()), 1),
        "R_day_IS": round(float(v[is_m].mean()), 3),
        "R_day_OOS": round(float(v[~is_m].mean()), 3),
        "maxDD_IS": round(maxdd(v[is_m]), 1),
        "maxDD_OOS": round(maxdd(v[~is_m]), 1),
    }


def main() -> int:
    lv = load("pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz")
    sv = load("vwap_rev_tf1_retest_xr30_dd.jsonl.gz", champ_cell=True)
    nv = load("vwap_rev_tf1_retest_xr30_nyanc_dd.jsonl.gz", champ_cell=True)
    for nm, b in (("8-level", lv), ("vwap-session", sv), ("vwap-ny", nv)):
        miss = sum(1 for t in b if "tier" not in t)
        print(f"{nm}: {len(b):,} trades, {miss} untagged")
        assert miss == 0, f"{nm} dump has no conviction tags - rerun with --conviction"
    kept = rail_pass([lv, sv, nv])

    # tier census on the railed set
    cen = defaultdict(lambda: {"n": 0, "r": 0.0, "w": 0, "l": 0, "is": [], "oos": []})
    for d, ts in kept.items():
        for t in ts:
            c = cen[t["tier"]]
            nr = t["r"] - COST_PTS / t["risk"]
            c["n"] += 1
            c["r"] += nr
            c["is" if d < MID else "oos"].append(nr)
            if t["res"] == "TARGET":
                c["w"] += 1
            elif t["res"] == "STOP":
                c["l"] += 1
    tot_n = sum(c["n"] for c in cen.values())
    print(f"\nTIER CENSUS (railed empire, {tot_n:,} trades, net of cost)")
    print(f"  {'tier':<6}{'n':>8}{'share':>8}{'WR':>8}{'net EV':>9}{'IS EV':>9}{'OOS EV':>9}{'net R':>9}")
    for k in sorted(cen):
        c = cen[k]
        print(f"  {k:<6}{c['n']:>8,}{c['n']/tot_n:>8.1%}"
              f"{c['w']/max(c['w']+c['l'],1):>8.3f}{c['r']/c['n']:>9.4f}"
              f"{np.mean(c['is']):>9.4f}{np.mean(c['oos']):>9.4f}{c['r']:>9.0f}")

    days, flat_v = daily(kept, SCHEMES["flat"])
    flat = stats(days, flat_v, "flat")
    flat_dd = maxdd(flat_v)          # UNROUNDED: rounding it put a spurious
    flat_sd = float(flat_v.std())    # +0.3% on every scheme in the first pass
    print(f"\nFLAT (the frozen spec): {flat['total_R']:+.0f}R, "
          f"{flat['R_day']:+.2f}R/day, maxDD {flat['maxDD']:.1f}R, "
          f"{flat['green']:.0%} green, daily Sharpe {flat['sharpe']:.3f}")

    print("\nDRAWDOWN-MATCHED COMPARISON (each scheme scaled so its maxDD "
          "equals flat's; the preregistered bar is +5% R/day in BOTH halves)")
    hdr = (f"  {'scheme':<9}{'scale':>7}{'R/day':>9}{'vs flat':>9}"
           f"{'IS':>9}{'vs':>8}{'OOS':>9}{'vs':>8}{'maxDD':>8}{'Sharpe':>8}{'mean risk':>11}")
    print(hdr)
    report = {"flat": flat, "tiers": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                                          for kk, vv in v.items() if kk in ("n", "r", "w", "l")}
                                      for k, v in cen.items()}, "schemes": {}}
    for name, mult in SCHEMES.items():
        _, v = daily(kept, mult)
        raw_dd = maxdd(v)
        scale = flat_dd / raw_dd if raw_dd < 0 else 1.0
        st = stats(days, v, name, scale)
        mean_risk = float(np.mean([mult[t["tier"]] for ts in kept.values() for t in ts])) * scale
        d_all = st["R_day"] / flat["R_day"] - 1
        d_is = st["R_day_IS"] / flat["R_day_IS"] - 1
        d_oos = st["R_day_OOS"] / flat["R_day_OOS"] - 1
        st.update({"vs_flat": round(d_all, 4), "vs_flat_IS": round(d_is, 4),
                   "vs_flat_OOS": round(d_oos, 4), "mean_risk": round(mean_risk, 3)})
        p999, pk = open_risk_p999(kept, mult)
        st["open_risk_p998"] = round(float(p999) * scale, 2)
        st["open_risk_max"] = round(float(pk) * scale, 2)
        report["schemes"][name] = st
        print(f"  {name:<9}{scale:>7.2f}{st['R_day']:>9.3f}{d_all:>+9.1%}"
              f"{st['R_day_IS']:>9.3f}{d_is:>+8.1%}{st['R_day_OOS']:>9.3f}"
              f"{d_oos:>+8.1%}{st['maxDD']:>8.1f}{st['sharpe']:>8.3f}{mean_risk:>11.3f}")

    print("\nSAME-RISK COMPARISON (each scheme scaled so mean risk per trade "
          "= 1.0, i.e. the same average contracts as flat)")
    print(f"  {'scheme':<9}{'R/day':>9}{'vs flat':>9}{'maxDD':>8}{'vs flat':>9}")
    for name, mult in SCHEMES.items():
        _, v = daily(kept, mult)
        mr = float(np.mean([mult[t["tier"]] for ts in kept.values() for t in ts]))
        sc = 1.0 / mr if mr else 1.0
        st = stats(days, v, name, sc)
        print(f"  {name:<9}{st['R_day']:>9.3f}{st['R_day']/flat['R_day']-1:>+9.1%}"
              f"{st['maxDD']:>8.1f}{st['maxDD']/flat['maxDD']-1:>+9.1%}")
        report["schemes"][name]["same_risk"] = st

    print("\nVOLATILITY-MATCHED (each scheme scaled to flat's daily stdev - "
          "a robust risk match; maxDD is one observation, stdev is 921)")
    print(f"  {'scheme':<9}{'scale':>7}{'R/day':>9}{'vs flat':>9}{'IS':>8}{'OOS':>8}"
          f"{'Sharpe':>9}{'S_IS':>8}{'S_OOS':>8}{'maxDD':>8}")
    is_m = np.array([d < MID for d in days])
    for name, mult in SCHEMES.items():
        _, v = daily(kept, mult)
        sc = flat_sd / float(v.std())
        vv = v * sc
        sh = lambda x: float(x.mean() / x.std())
        st = stats(days, v, name, sc)
        d_is = st["R_day_IS"] / flat["R_day_IS"] - 1
        d_oos = st["R_day_OOS"] / flat["R_day_OOS"] - 1
        flag = "" if name in SIZE_ONLY else "  (estimate: not size-only)"
        print(f"  {name:<9}{sc:>7.2f}{st['R_day']:>9.3f}"
              f"{st['R_day']/flat['R_day']-1:>+9.1%}{d_is:>+8.1%}{d_oos:>+8.1%}"
              f"{sh(vv):>9.3f}{sh(vv[is_m]):>8.3f}{sh(vv[~is_m]):>8.3f}"
              f"{st['maxDD']:>8.1f}{flag}")
        report["schemes"][name]["vol_matched"] = st
        report["schemes"][name]["sharpe_IS"] = round(sh(vv[is_m]), 4)
        report["schemes"][name]["sharpe_OOS"] = round(sh(vv[~is_m]), 4)

    print("\nPER-YEAR (drawdown-matched R/day, size-only schemes)")
    yrs = sorted({d[:4] for d in days})
    print("  " + "scheme".ljust(9) + "".join(y.rjust(9) for y in yrs))
    for name, mult in SCHEMES.items():
        if name not in SIZE_ONLY:
            continue
        _, v = daily(kept, mult)
        sc = flat_dd / maxdd(v)
        row = []
        for y in yrs:
            m = np.array([d[:4] == y for d in days])
            row.append((v[m] * sc).mean())
        base = [flat_v[np.array([d[:4] == y for d in days])].mean() for y in yrs]
        print(f"  {name:<9}" + "".join(f"{r:>9.2f}" for r in row)
              + ("   " + "".join(f"{r/b-1:>+8.0%}" for r, b in zip(row, base))
                 if name != "flat" else ""))

    print("\nG7 open-risk check (drawdown-matched scale): flat p99.8 "
          f"{open_risk_p999(kept, SCHEMES['flat'])[0]:.2f}R / max "
          f"{open_risk_p999(kept, SCHEMES['flat'])[1]:.2f}R")

    # verdict against the preregistered rule
    print("\nVERDICT (preregistered: adopt at >=+5% R/day in BOTH halves, "
          "drawdown-matched)")
    for name, st in report["schemes"].items():
        if name == "flat":
            continue
        if name not in SIZE_ONLY:
            print(f"  {name:<9}{'EXCLUDED':<7} zero multiplier = a skip, not "
                  f"sizing; needs its own engine run")
            st["verdict"] = "EXCLUDED (not size-only)"
            continue
        both = min(st["vs_flat_IS"], st["vs_flat_OOS"])
        v = ("ADOPT" if both >= 0.05 else
             "WATCH" if both > 0 else "KILL")
        print(f"  {name:<9}{v:<7} IS {st['vs_flat_IS']:+.1%}  OOS {st['vs_flat_OOS']:+.1%}")
        st["verdict"] = v
    (OUT / "conviction_sizing.json").write_text(json.dumps(report, indent=1))
    print(f"\n-> {OUT / 'conviction_sizing.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
