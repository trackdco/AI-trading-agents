#!/usr/bin/env python3
"""MECHANICAL vs AGENT JUDGEMENT — the same week, the same trigger, no discretion.

    python -m scripts.mech_vs_agent 2026-06-21 2026-06-22 2026-06-23 \
        2026-06-24 2026-06-25 --agent-logs "output/agent_runs/*_wk1.jsonl"

His question: over the week the agents were built on, what would the RAW
MECHANICAL trigger have produced? The agent programme's whole claim is that
judgement beats the unfiltered trigger. This is the control that tests it.

THREE THINGS ARE REPORTED, and the third is the one he asked about second.

  1. THE MECHANICAL BOOK. Every trigger in his own 2026-08-08 census
     definition (2m/3m candle whose open sits one side of BOTH its own BB(20)
     MA and a VWAP band, closing through both), inside his three windows, no
     thesis, no conviction, no passes. Priced at several fixed targets from
     the excursion walk, plus hold-to-session-end.

  2. THE AGENT BOOK, from the run logs, same days.

  3. THE GIVE-BACK TAX. For every agent fill, the trade is re-walked from its
     own fill price and stop to session end, so realised R can be set against
     the R that was actually available on that exact position. That is the
     measurable form of "the agents cut profit early / break even too soon" —
     it prices the management style rather than arguing about it.

TWO STRUCTURAL DIFFERENCES that make this a comparison of styles, not a
like-for-like race, and both favour different sides:

  - ENTRY. The mechanical census enters AT MARKET on the next bar's open. He
    enters on a limit at the retest. The limit gets a better price when it
    fills and no trade at all when it does not, so the agent book is smaller
    and cheaper per trade by construction.
  - STOP. The census uses the trigger candle's extreme ± a tick. The agents
    use his structural rule (clear the live level, body not wick on an
    oversized candle), which is usually wider. Wider stops mean smaller R
    numbers on the same points of movement — which is why POINTS are reported
    alongside R throughout.

FIT-ONLY, REPORT-ONLY. Nothing here is adopted, and the week is the corpus
the agents were built on, so the agent side is in-sample and flattered.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.raw_trigger_census import day_rows                     # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

WINDOWS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (575, 660)}
R_FULL = ("r_result", "r_full_target_whole_position_at_final_exit")
R_BLEND = ("r_blended", "r_blended_across_partials")


def _num(d: dict, keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def window_of(hm: int) -> str | None:
    for w, (a, b) in WINDOWS.items():
        if a <= hm <= b:
            return w
    return None


def price_fixed(df: pd.DataFrame, target_r: float) -> np.ndarray:
    """Price a fixed-R target from the excursion walk.

    Reached the target before the stop -> +target. Stopped -> -1. Neither ->
    the session-end mark. This is the standard way to price a target from
    excursion data and it is exact whenever MFE and the stop cannot both
    occur inside one bar; where they can, it is optimistic, and that
    optimism favours the MECHANICAL side of this comparison.
    """
    out = np.where(df.run_mfe_r >= target_r, target_r,
                   np.where(df.stopped, -1.0, df.eod_r))
    return out.astype(float)


def walk_from(bars_day: pd.DataFrame, t_fill, entry: float, stop: float,
              d: int):
    """Re-walk one agent position from its own fill to session end."""
    seg = bars_day[bars_day.index >= t_fill]
    if seg.empty:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
    mfe = 0.0
    for j in range(len(seg)):
        adv = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
        mfe = max(mfe, adv)
        if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
            break
    return mfe


def load_agent(paths, bars):
    """Agent fills with realised R and the R that was available to them."""
    rows = []
    for p in sorted(paths):
        recs, conv, side, fillinfo = [], {}, {}, {}
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        for r in recs:
            pay = {**r, **(r.get("output") or {})}
            cid = pay.get("candidate_id")
            if not cid:
                continue
            if pay.get("conviction"):
                conv[cid] = str(pay["conviction"]).upper()[:1]
            if pay.get("direction") or pay.get("side") or pay.get("position"):
                side[cid] = str(pay.get("direction") or pay.get("side")
                                or pay.get("position")).lower()
            if r.get("row") == "fill":
                fillinfo[cid] = {
                    "entry": r.get("fill_price", r.get("entry")),
                    "stop": r.get("stop"),
                    "bar": r.get("fill_bar_start"),
                    "window": r.get("window"),
                    "pos": str(r.get("position", "")).lower()}
        sess = p.stem.replace("_wk1", "").replace("_jn1", "")
        t0 = pd.Timestamp(f"{sess} 18:00", tz=NY)
        bday = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        for r in recs:
            if r.get("row") != "exit":
                continue
            cid = r.get("candidate_id", "?")
            rr = _num(r, R_FULL) or _num(r, R_BLEND)
            rb = _num(r, R_BLEND) or rr
            fi = fillinfo.get(cid, {})
            s = (fi.get("pos") or side.get(cid, "")).lower()
            d = 1 if "long" in s or "buy" in s else -1
            entry = fi.get("entry") or r.get("entry")
            stop = fi.get("stop") or r.get("original_stop")
            avail = None
            if entry and stop and fi.get("bar"):
                try:
                    hh, mm = str(fi["bar"]).split(":")[:2]
                    base = t0 + pd.Timedelta(days=1) if int(hh) < 18 else t0
                    tf = base.normalize() + pd.Timedelta(hours=int(hh),
                                                         minutes=int(mm))
                    tf = tf.tz_localize(NY) if tf.tzinfo is None else tf
                    avail = walk_from(bday, tf, float(entry), float(stop), d)
                except (ValueError, TypeError):
                    avail = None
            rows.append({"sess_day": sess, "cid": cid,
                         "window": fi.get("window") or r.get("window"),
                         "conv": conv.get(cid, "?"), "r": rr, "r_blended": rb,
                         "available_r": avail,
                         "risk_pts": _num(r, ("r_points", "R_in_points"))})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("days", nargs="+", help="session-days")
    ap.add_argument("--agent-logs", default=None)
    a = ap.parse_args()

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]

    rows = []
    for d in a.days:
        rows += day_rows(bars, d)
    T = pd.DataFrame(rows)
    if T.empty:
        raise SystemExit("no triggers found")
    T["window"] = T.hm.map(window_of)
    T = T[T.window.notna()].copy()

    print("\n" + "=" * 80)
    print("  MECHANICAL TRIGGER BOOK — no thesis, no conviction, no passes")
    print("=" * 80)
    print(f"  {len(a.days)} session-days · {len(T)} in-window triggers "
          f"({len(T) / len(a.days):.1f}/day)   2m: {(T.tf == 2).sum()}  "
          f"3m: {(T.tf == 3).sum()}")

    print(f"\n  {'exit rule':<20}{'total R':>10}{'mean R':>9}{'WR':>8}"
          f"{'total pts':>12}{'stopped':>9}")
    print("  " + "-" * 68)
    for tgt in (1.0, 1.5, 2.0, 2.5):
        r = price_fixed(T, tgt)
        pts = (r * T.risk).sum()
        print(f"  fixed {tgt:.1f}R{'':<12}{r.sum():>10.1f}{r.mean():>9.2f}"
              f"{100 * (r > 0).mean():>7.1f}%{pts:>12,.0f}"
              f"{100 * T.stopped.mean():>8.1f}%")
    eod = T.eod_r.to_numpy()
    print(f"  hold to session end {eod.sum():>10.1f}{eod.mean():>9.2f}"
          f"{100 * (eod > 0).mean():>7.1f}%{(eod * T.risk).sum():>12,.0f}")

    print(f"\n  per window (fixed 2.0R):")
    for w in WINDOWS:
        g = T[T.window == w]
        if g.empty:
            continue
        r = price_fixed(g, 2.0)
        print(f"    {w:<9} n={len(g):>3}  total {r.sum():>7.1f}R  "
              f"mean {r.mean():>+6.2f}R  WR {100 * (r > 0).mean():>5.1f}%  "
              f"pts {(r * g.risk).sum():>+8,.0f}")

    if not a.agent_logs:
        print()
        return 0

    paths = [Path(x) for x in glob.glob(a.agent_logs)]
    A = load_agent([p for p in paths if p.is_file()], bars)
    A = A[A.r.notna()]
    if A.empty:
        print("\n  no agent fills parsed\n")
        return 0

    print("\n" + "=" * 80)
    print("  AGENT BOOK — same days, same trigger family, judgement applied")
    print("=" * 80)
    print(f"  {len(A)} fills ({len(A) / len(a.days):.1f}/day vs mechanical "
          f"{len(T) / len(a.days):.1f}/day — judgement declined "
          f"{100 * (1 - len(A) / len(T)):.0f}% of the population)")
    print(f"  total {A.r.sum():+.2f}R full-target · "
          f"{A.r_blended.sum():+.2f}R blended · "
          f"mean {A.r.mean():+.2f}R · WR {100 * (A.r > 0).mean():.1f}%")

    have = A[A.available_r.notna()].copy()
    if len(have):
        have["left"] = have.available_r - have.r
        print("\n" + "=" * 80)
        print("  THE GIVE-BACK TAX — realised vs what the same position offered")
        print("=" * 80)
        print(f"  {len(have)}/{len(A)} fills re-walked from their own entry"
              f" and stop to session end\n")
        print(f"  {'candidate':<24}{'conv':>5}{'realised':>10}"
              f"{'available':>11}{'left on table':>15}")
        print("  " + "-" * 65)
        for _, x in have.sort_values("left", ascending=False).iterrows():
            print(f"  {str(x.cid)[:23]:<24}{x.conv:>5}{x.r:>+10.2f}"
                  f"{x.available_r:>+11.2f}{x.left:>+15.2f}")
        print("  " + "-" * 65)
        print(f"  {'TOTAL':<24}{'':>5}{have.r.sum():>+10.2f}"
              f"{have.available_r.sum():>+11.2f}{have.left.sum():>+15.2f}")
        cap = 100 * have.r.sum() / have.available_r.sum() \
            if have.available_r.sum() else float("nan")
        print(f"\n  capture rate: {cap:.0f}% of the R the positions offered.")
        print("  'available' = the trade's own MFE before its own stop, held to")
        print("  session end. It is an UPPER BOUND nobody trades — no exit rule")
        print("  catches every peak — so the honest read is the SHAPE: which")
        print("  trades gave back most, and whether they cluster by conviction")
        print("  or by management action.")

    print("\n  Both books are FIT — this week built the agents' doctrine.")
    print("  Mechanical entries are market-on-next-open with candle-extreme")
    print("  stops; agent entries are limit-on-retest with structural stops.")
    print("  Compare styles, not a race.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
