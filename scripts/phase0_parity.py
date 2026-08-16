#!/usr/bin/env python3
"""PHASE 0 GATE 3 — indicator parity between his chart and the research build.

docs/AGENT-OPERATING-SPEC.md Phase 0 says to read VWAP, VWAP+/-1 and the BB MA
off the chart at one known minute and compare. This prints the research-build
side of that comparison and applies the documented thresholds, so the gate is
mechanical instead of eyeballed.

    python -m scripts.phase0_parity 2026-06-25 04:06
    python -m scripts.phase0_parity 2026-06-25 04:06 \
        --vwap 29492.65 --bb-ma-2m 29477.00 --bb-ma-3m 29510.94

With observed values it exits non-zero on a FAIL, so it can gate a run.

THRESHOLDS (spec Phase 0.3): >1pt on VWAP or >0.5pt on a BB MA means the chart
config differs from the research build. Say so and STOP rather than proceeding.

PROFILE LEVELS ARE NOT GATED, deliberately. `agent_context.volume_profile`
documents a ~30pt unresolved residual — real profiles distribute volume by
traded ticks, not uniformly, and his chart's row size is unknown. They print
for orientation and the chart wins. Gating on them would fail a correct setup.

TIME CONVENTION, and it is the one that silently corrupts everything:
`minute` is the minute the decision is made AT. Following `agent_context.
context_at`, that reads the last completed 1m bar STRICTLY BEFORE it, and the
bar actually used is printed so it can be checked. His chart labels candles by
START time -- a "09:46 2-minute candle" spans 09:46-09:47 and closes at 09:48,
so the decision minute for that candle is 09:48, not 09:46.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.agent_context import (
    anchored_weekly_profile,
    prev_day_levels,
    session_day_of,
    volume_profile,
    weekly_levels,
)
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import CHART_VWAP_SOURCE, NY, bb_ma_asof, vwap_bands

VWAP_TOL = 1.0      # spec Phase 0.3
BB_TOL = 0.5        # spec Phase 0.3
TFS = (2, 3, 15, 60)
SOURCES = ("hlc3", "ohlc4", "open", "close")


def reference_at(bars: pd.DataFrame, sess_day: str, minute: str,
                 source: str = CHART_VWAP_SOURCE) -> dict:
    """Every level the parity gate compares, as-of `minute` on `sess_day`."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{sess_day} {minute}", tz=NY)
    if t < t0:                       # 00:00-17:59 belongs to the NEXT calendar
        t += pd.Timedelta(days=1)    # date within this 18:00-anchored day
    t1 = t0 + pd.Timedelta(hours=23)
    if not (t0 <= t < t1):
        raise SystemExit(f"{minute} is outside session-day {sess_day} "
                         f"({t0:%Y-%m-%d %H:%M} -> {t1:%Y-%m-%d %H:%M})")

    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        raise SystemExit(f"no bars for session-day {sess_day}")

    # Causal: a decision AT t sees bars strictly before t. Same convention as
    # agent_context.context_at, which subtracts 1 from its searchsorted index.
    prior = hist[hist.index < t]
    if prior.empty:
        raise SystemExit(f"no completed bars before {t:%Y-%m-%d %H:%M}")
    bar_t = prior.index[-1]

    out: dict = {"decision_minute": t, "bar_used": bar_t,
                 "close": float(prior.close.iloc[-1])}

    vb = vwap_bands(hist, source=source)
    row = vb.reindex([bar_t]).iloc[0]
    for k in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2",
              "vwap_m2", "vwap_p3", "vwap_m3"):
        if k in vb.columns:
            out[k] = float(row[k])

    # Every source, at this bar, so a config drift is REPORTED rather than
    # diagnosed by hand. See source_fit() and its caller in main().
    out["_all_sources"] = {}
    for s in SOURCES:
        r = vwap_bands(hist, source=s).reindex([bar_t]).iloc[0]
        out["_all_sources"][s] = {k: float(r[k])
                                  for k in ("vwap", "vwap_p1", "vwap_m1")}

    for tf in TFS:
        ma, _w = bb_ma_asof(hist, tf)
        v = ma.reindex([bar_t]).iloc[0]
        out[f"bb_ma_{tf}m"] = float(v) if np.isfinite(v) else np.nan

    seg = hist[(hist.index >= t0) & (hist.index < t)]       # developing daily
    poc, val, vah = volume_profile(seg)
    out["daily_poc"], out["daily_val"], out["daily_vah"] = poc, val, vah

    aw = anchored_weekly_profile(bars, sess_day, upto=t)
    out["weekly_poc"], out["weekly_val"] = aw["awPOC"], aw["awVAL"]
    out["weekly_vah"] = aw["awVAH"]
    out["weekly_high"], out["weekly_low"] = aw["awHIGH"], aw["awLOW"]
    out["weekly_anchor"] = aw["anchor"]

    all_days = sorted({session_day_of(x) for x in bars.index})
    out.update({k: v for k, v in prev_day_levels(bars, sess_day,
                                                 all_days).items()})
    out.update({f"research_{k}": v
                for k, v in weekly_levels(bars, sess_day, all_days).items()})
    return out


def source_fit(ref: dict, obs: dict, chosen: str) -> str | None:
    """Which VWAP source best matches the chart at this bar?

    Printed whenever a chart VWAP is supplied, PASS or FAIL. A source mismatch
    was found once by hand — the tell was that +1sd matched to 0.02pt while
    -1sd was 1.12pt out, which cannot happen by chance: a mid that sits low and
    a sigma that runs wide cancel on the upper band and add on the lower one.
    That diagnosis should never have to be re-derived, so it runs every time.
    """
    have = {k: v for k, v in obs.items() if v is not None}
    if not have:
        return None
    rows = []
    for s, vals in ref["_all_sources"].items():
        errs = {k: vals[k] - have[k] for k in have}
        rows.append((s, max(abs(e) for e in errs.values()), errs))
    rows.sort(key=lambda r: r[1])

    print("\n  VWAP SOURCE FIT -- build minus chart, per source")
    cols = list(have)
    print("    " + f"{'source':<8}" + "".join(f"{c:>12}" for c in cols)
          + f"{'worst':>9}")
    for s, worst, errs in rows:
        mark = "  <- in use" if s == chosen else ""
        best = "  BEST" if s == rows[0][0] and s != chosen else ""
        print("    " + f"{s:<8}"
              + "".join(f"{errs[c]:>+12.2f}" for c in cols)
              + f"{worst:>9.2f}" + mark + best)

    # Only flag a MATERIAL mismatch. Sources converge as a session accumulates,
    # so a 0.03pt win is noise and nagging about it trains everyone to ignore
    # the line that matters. Fire when the source in use is eating a real share
    # of the tolerance AND something else is clearly better.
    best_src, best_err, _ = rows[0]
    mine = next(w for s, w, _ in rows if s == chosen)
    if best_src != chosen and mine > VWAP_TOL / 2 and (mine - best_err) > 0.25:
        print(f"\n    !! '{best_src}' fits this chart materially better than "
              f"'{chosen}' ({best_err:.2f} vs {mine:.2f}pt).")
        print("       His chart is the authority, never a fit -- confirm the "
              "VWAP indicator's")
        print("       Source setting with him, then change CHART_VWAP_SOURCE "
              "in src/htf_ma/levels.py.")
        return best_src
    if best_src != chosen:
        print(f"\n    ('{best_src}' edges it by {mine - best_err:.2f}pt -- "
              f"noise at this bar, not a mismatch. Sources converge as a")
        print("     session accumulates; only a wide gap here means anything.)")
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sess_day", help="session-day, e.g. 2026-06-25 "
                                    "(18:00 NY anchor -- his Friday 26 June "
                                    "is session-day 2026-06-25)")
    p.add_argument("minute", help="decision minute NY, HH:MM")
    p.add_argument("--vwap", type=float, help="VWAP read off the chart")
    p.add_argument("--vwap-p1", type=float, help="VWAP+1 read off the chart")
    p.add_argument("--vwap-m1", type=float, help="VWAP-1 read off the chart")
    p.add_argument("--vwap-source", choices=SOURCES, default=CHART_VWAP_SOURCE,
                   help="override the source for THIS run only. To change it "
                        "permanently, edit CHART_VWAP_SOURCE in "
                        "src/htf_ma/levels.py -- it is a measurement of his "
                        "chart and every call site reads it from there.")
    for tf in TFS:
        p.add_argument(f"--bb-ma-{tf}m", type=float,
                       dest=f"bb_ma_{tf}m", help=f"{tf}m BB(20) MA off the chart")
    a = p.parse_args()

    ref = reference_at(load_bars_indexed(), a.sess_day, a.minute, a.vwap_source)

    print("\nPHASE 0 GATE 3 -- indicator parity")
    print(f"  session-day     {a.sess_day}   (18:00 NY anchor)")
    print(f"  decision minute {ref['decision_minute']:%Y-%m-%d %H:%M %Z}")
    print(f"  bar used        {ref['bar_used']:%Y-%m-%d %H:%M %Z}"
          f"   (last completed bar strictly before the decision minute)")
    print(f"  close           {ref['close']:.2f}")
    wa = ref["weekly_anchor"]
    sess_open = pd.Timestamp(f"{a.sess_day} 18:00", tz=NY)
    back_days = (sess_open - wa).days
    print(f"  weekly anchor   {wa:%Y-%m-%d %H:%M %Z}"
          f"   ({wa:%A} 18:00 NY, {back_days}d back, developing)")

    print(f"\n  VWAP (source={a.vwap_source}, 18:00 anchor)")
    for k in ("vwap_m3", "vwap_m2", "vwap_m1", "vwap",
              "vwap_p1", "vwap_p2", "vwap_p3"):
        if k in ref and np.isfinite(ref[k]):
            print(f"    {k:<10} {ref[k]:>12.2f}")

    print("\n  BB(20) MA -- 20, 2, SMA on close, per timeframe")
    for tf in TFS:
        v = ref[f"bb_ma_{tf}m"]
        print(f"    {tf:>3}m       {v:>12.2f}" if np.isfinite(v)
              else f"    {tf:>3}m       {'n/a':>12}")

    print("\n  Volume profile -- ORIENTATION ONLY, not gated (see module docstring)")
    print("    developing daily   POC {daily_poc:>10.2f}   VAL {daily_val:>10.2f}"
          "   VAH {daily_vah:>10.2f}".format(**ref))
    print("    anchored weekly    POC {weekly_poc:>10.2f}   VAL {weekly_val:>10.2f}"
          "   VAH {weekly_vah:>10.2f}".format(**ref))
    print(f"    weekly high/low    {ref['weekly_high']:.2f} / {ref['weekly_low']:.2f}")
    gap = abs(ref["daily_val"] - ref["weekly_val"])
    if np.isfinite(gap):
        print(f"\n    !! daily VAL and weekly VAL sit {gap:.1f}pt apart. "
              f'"Value area" is ambiguous in his speech --')
        print("       compute both, name which one, never guess "
              "(they were 165pt apart on 2026-06-25).")

    print("\n  Prior day")
    print("    POC {pPOC:>10.2f}   VAL {pVAL:>10.2f}   VAH {pVAH:>10.2f}"
          "   H {pHIGH:>10.2f}   L {pLOW:>10.2f}".format(**ref))

    checks = [("vwap", a.vwap, VWAP_TOL), ("vwap_p1", a.vwap_p1, VWAP_TOL),
              ("vwap_m1", a.vwap_m1, VWAP_TOL)]
    checks += [(f"bb_ma_{tf}m", getattr(a, f"bb_ma_{tf}m"), BB_TOL)
               for tf in TFS]
    checks = [(k, v, tol) for k, v, tol in checks if v is not None]

    if not checks:
        print("\n  No observed values given -- nothing gated.")
        print("  Read these off the chart and re-run with --vwap / --bb-ma-2m "
              "etc.\n")
        return 0

    source_fit(ref, {"vwap": a.vwap, "vwap_p1": a.vwap_p1,
                     "vwap_m1": a.vwap_m1}, a.vwap_source)

    print("\n  PARITY")
    failed = []
    for k, obs, tol in checks:
        exp = ref.get(k, np.nan)
        if not np.isfinite(exp):
            print(f"    {k:<10} chart {obs:>10.2f}   build {'n/a':>10}   SKIP")
            continue
        d = abs(obs - exp)
        ok = d <= tol
        print(f"    {k:<10} chart {obs:>10.2f}   build {exp:>10.2f}   "
              f"delta {d:>6.2f}   tol {tol:.1f}   {'ok' if ok else 'FAIL'}")
        if not ok:
            failed.append((k, d, tol))

    # ---- GATE 3b: the anchored weekly profile is anchored where he anchors it.
    # Added 2026-08-13 at his instruction ("make sure the weekly vp is anchored
    # correctly too, make sure its in the process"). This is a GATE, not a print,
    # because the anchor was silently wrong for an entire scored week: it used
    # same-weekday-minus-7 instead of the week's Monday, moving weekly POC ~900pt.
    # Anchored-weekly edges are the ONLY levels that grade A on their own and they
    # are named as thesis targets, so a wrong anchor changes verdicts, not just
    # numbers. Checked every run so it can never drift back unnoticed.
    anchor_bad = []
    if wa.weekday() != 0:
        anchor_bad.append(f"anchored to a {wa:%A}, not a Monday")
    if not (0 < back_days <= 7):
        anchor_bad.append(f"{back_days}d back from the session open; "
                          "expected 1-7 (this week's Monday, or the prior "
                          "Monday when the session IS Monday's)")
    print("\n  ANCHORED WEEKLY -- anchor check")
    if anchor_bad:
        print(f"    anchor {wa:%Y-%m-%d %H:%M} ({wa:%A}), {back_days}d back   FAIL")
        for m in anchor_bad:
            print(f"      - {m}")
        print("\n  GATE FAILED -- the anchored weekly profile is anchored wrong.")
        print("  Weekly POC/VAL/VAH are the only A-grade levels in the conviction")
        print("  rubric and are named as thesis targets. STOP; do not run a day on")
        print("  a mis-anchored weekly profile.\n")
        return 1
    print(f"    anchor {wa:%Y-%m-%d %H:%M} ({wa:%A}), {back_days}d back   ok")
    if back_days == 7:
        print("    NOTE: 7d back means this session IS the week's Monday, so the")
        print("    profile falls back to the PRIOR Monday and will read as last")
        print("    week's numbers. That is correct on a Monday, not a bug.")

    if failed:
        print("\n  GATE FAILED -- his chart config differs from the research "
              "build:")
        for k, d, tol in failed:
            print(f"    {k}: {d:.2f}pt off, tolerance {tol:.1f}pt")
        print("\n  Say so and STOP. Do not trade through a failed gate "
              "(spec Phase 0).\n")
        return 1

    print("\n  GATE PASSED. Phase 0.3 clear -- still run the NO-LEAK check "
          "(Phase 0.4),")
    print("  which is the one that matters most, and re-verify it after "
          "every replay jump.\n")
    return 0


def load_bars_indexed() -> pd.DataFrame:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    return (bars.set_index("mi").sort_index()
            [["open", "high", "low", "close", "volume"]])


if __name__ == "__main__":
    raise SystemExit(main())
