#!/usr/bin/env python3
"""zxck-10am-keyopen — READING A on the tick-covered span, with the ambiguity BOUNDED.

WHY THIS IS NOT THE TICK RESOLVER THAT WAS ASKED FOR
----------------------------------------------------
The brief says to resolve intrabar sequence with "the aggressor-tagged NQ trades". We do not
hold them. Verified 2026-08-07:

  data/reference/cvd/footprint_*.parquet   (ts_minute, price, side, volume, trades)
      -> aggregated to (MINUTE x PRICE x SIDE). `ts_minute` is the only time column, and rows
         within a minute are PRICE LEVELS, not a sequence. Volume-at-price is identical whether
         price went up-then-down or down-then-up, so it carries ZERO sequence information.
  data/reference/depth_*/nq_depth_*.csv    (ts, side, price, size)
      -> exactly 20 rows per timestamp (10 levels x 2 sides), 150 timestamps/session = ONE
         snapshot per minute. Not sub-minute. Also carries the known look-ahead defect
         (docs/FINDING-depth-snapshot-lookahead.md).
  no `databento` client, no DATABENTO_API_KEY -> we cannot fetch the trades either.

So the 106 same-bar sessions CANNOT be resolved. Rather than guess the sequence (an OHLC
close-direction heuristic would be a guess dressed as a measurement), this script BOUNDS the
answer: every ambiguous session is run under BOTH possible orderings. If the baseline is the
null under both extremes, the ambiguity cannot be concealing an edge — that is a proof, not an
estimate. If the two bounds straddle something interesting, we know exactly what to buy.

Everything else is unchanged from scripts/zxck_keyopen_baseline.py: rules R1-R14, the same
deliberate non-implementations N1-N6, the FIXED 10pt manipulation floor (never ATR-scaled), and
the LOCKED exit convention verified against ash-unicorn-sb's 37-row log.

    python -m scripts.zxck_keyopen_bounded
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import load_bars  # noqa: E402
from scripts.zxck_keyopen_baseline import (  # noqa: E402
    COST_USD, FOMC, MANIP_PTS, OPEN_MIN, OUT, PT, RTH_END, STOP_PTS, WIN_END, calendar,
)

TICK_LO, TICK_HI = "2025-06-01", "2026-07-15"   # the aggressor-tagged span we own


def resolve(w: pd.DataFrame, P: float):
    """Returns (kind, side) — 'decidable' with the true side, or 'ambiguous' with None."""
    up, dn = w.high >= P + MANIP_PTS, w.low <= P - MANIP_PTS
    if not up.any() and not dn.any():
        return "no_manip", None
    iu = int(up.idxmax()) if up.any() else 10 ** 9
    idn = int(dn.idxmax()) if dn.any() else 10 ** 9
    if iu == idn:
        return "ambiguous", None          # both sides inside one bar — unresolvable on OHLC
    return "decidable", (+1 if idn < iu else -1)


def simulate(g: pd.DataFrame, w: pd.DataFrame, P: float, side: int, m: int):
    """R5 distribution -> R6 entry -> R8/R9/R11/R12 locked exit. None if no trade."""
    post = w.iloc[m + 1:]
    clo = (post.close > P) if side > 0 else (post.close < P)
    if not len(post) or not clo.any():
        return None, "no close through the level"
    ci = int(clo.idxmax())
    fwd = w.iloc[ci + 1:]
    hit = (fwd.low <= P) if side > 0 else (fwd.high >= P)
    if not len(fwd) or not hit.any():
        return None, "limit never filled"
    t = int(hit.idxmax())
    entry = P
    stop = entry - side * STOP_PTS
    target = entry + side * 2 * STOP_PTS
    half = entry + side * STOP_PTS
    tail = pd.concat([w.iloc[t + 1:], g[(g.mins > WIN_END) & (g.mins <= RTH_END)]])
    cur, be, out = stop, False, None
    for _, bar in tail.iterrows():
        if side > 0:
            if bar.low <= cur:
                out = 0.0 if be else -1.0; break
            if bar.high >= target:
                out = 2.0; break
            if not be and bar.high >= half:
                cur, be = entry, True
        else:
            if bar.high >= cur:
                out = 0.0 if be else -1.0; break
            if bar.low <= target:
                out = 2.0; break
            if not be and bar.low <= half:
                cur, be = entry, True
    if out is None:
        last = float(tail.close.iloc[-1]) if len(tail) else entry
        out = float(side * (last - entry) / STOP_PTS)
    return {"R": round(out, 3), "entry_min": int(w.mins.iloc[t] - OPEN_MIN),
            "direction": "long" if side > 0 else "short"}, None


def stats(R: pd.Series) -> dict:
    if not len(R):
        return {}
    eq = R.cumsum(); c = COST_USD / (STOP_PTS * PT)
    return {"n": len(R), "win%": 100 * (R >= 2).mean(), "BE%": 100 * (R == 0).mean(),
            "loss%": 100 * (R <= -1).mean(), "avgR": R.mean(), "exp": R.mean() - c,
            "totR": R.sum(), "maxDD": float((eq.cummax() - eq).max())}


def show(label: str, R: pd.Series) -> None:
    s = stats(R)
    if not s:
        print(f"  {label:<44} no trades"); return
    print(f"  {label:<44} n={s['n']:>4}  {s['win%']:>5.1f}/{s['BE%']:>5.1f}/{s['loss%']:>5.1f}"
          f"  avgR {s['avgR']:+.3f}  exp {s['exp']:+.3f}  tot {s['totR']:+6.1f}R"
          f"  DD {s['maxDD']:4.1f}R")


def main() -> None:
    bars = load_bars()
    bars = bars[(bars.day >= TICK_LO) & (bars.day <= TICK_HI)]
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    by = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}

    rows, skips = [], {}
    for day, g in by.items():
        if day in fomc:
            skips["FOMC/Powell"] = skips.get("FOMC/Powell", 0) + 1; continue
        o = g[g.mins == OPEN_MIN]
        if o.empty:
            skips["no 10:00 bar (Sun/holiday)"] = skips.get("no 10:00 bar (Sun/holiday)", 0) + 1
            continue
        P = float(o.open.iloc[0])
        w = g[(g.mins >= OPEN_MIN) & (g.mins <= WIN_END)].reset_index(drop=True)
        if len(w) < 5:
            skips["short window"] = skips.get("short window", 0) + 1; continue
        kind, side = resolve(w, P)
        if kind == "no_manip":
            skips["no 10pt manipulation"] = skips.get("no 10pt manipulation", 0) + 1; continue
        up, dn = w.high >= P + MANIP_PTS, w.low <= P - MANIP_PTS
        m = int(min(int(up.idxmax()) if up.any() else 10 ** 9,
                    int(dn.idxmax()) if dn.any() else 10 ** 9))
        rng = float(g.high.max() - g.low.min())
        if kind == "decidable":
            tr, why = simulate(g, w, P, side, m)
            rows.append({"date": day, "kind": "decidable", "day_range": rng,
                         **(tr or {}), "skip": why})
        else:
            up_tr, up_why = simulate(g, w, P, -1, m)   # assume UP breached first -> SHORT
            dn_tr, dn_why = simulate(g, w, P, +1, m)   # assume DOWN breached first -> LONG
            rows.append({"date": day, "kind": "ambiguous", "day_range": rng,
                         "R_if_up_first": (up_tr or {}).get("R"),
                         "R_if_down_first": (dn_tr or {}).get("R"),
                         "skip_up": up_why, "skip_down": dn_why})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "zxck-10am-keyopen-bounded.csv", index=False)

    dec = d[(d.kind == "decidable") & d.R.notna()]
    amb = d[d.kind == "ambiguous"]
    amb_up = amb.R_if_up_first.dropna()
    amb_dn = amb.R_if_down_first.dropna()

    print("zxck-10am-keyopen — READING A, tick-covered span, ambiguity BOUNDED\n")
    print(f"span {TICK_LO} -> {TICK_HI}   sessions {len(by)}")
    for k, v in sorted(skips.items(), key=lambda x: -x[1]):
        print(f"   skipped: {k:<34} {v}")
    n_dec = int((d.kind == "decidable").sum())
    print(f"\n   DECIDABLE sessions {n_dec}  -> trades {len(dec)}")
    print(f"   AMBIGUOUS sessions {len(amb)}  -> trades {len(amb_up)} (up-first) / "
          f"{len(amb_dn)} (down-first)")
    print(f"\n   median daily range  decidable {dec.day_range.median():.0f}pt   "
          f"ambiguous {amb.day_range.median():.0f}pt")

    print("\n" + "=" * 96)
    print("  arm                                           n    win/ BE /loss    avgR      exp"
          "      total     maxDD")
    print("=" * 96)
    show("DECIDABLE only", dec.R)
    show("AMBIGUOUS only, if UP breached first", amb_up)
    show("AMBIGUOUS only, if DOWN breached first", amb_dn)
    print("  " + "-" * 92)
    show("BOUND LOW  (decidable + worse ambiguous)", pd.concat(
        [dec.R, amb_up if amb_up.sum() <= amb_dn.sum() else amb_dn]))
    show("BOUND HIGH (decidable + better ambiguous)", pd.concat(
        [dec.R, amb_dn if amb_up.sum() <= amb_dn.sum() else amb_up]))
    print("=" * 96)

    print("\nRANDOM-WALK NULL for a 2R target with break-even at 1R: 25.0 / 25.0 / 50.0")
    print(f"\nbounded file -> {(OUT/'zxck-10am-keyopen-bounded.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
