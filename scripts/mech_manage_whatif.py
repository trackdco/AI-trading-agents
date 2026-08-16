#!/usr/bin/env python3
"""AGENT ENTRIES, MECHANICAL MANAGEMENT — the counterfactual he asked for.

    python -m scripts.mech_manage_whatif

Keep the selection layer exactly as it traded — every actual fill, its entry
price, its original stop, its named targets — and replace tier-3 judgement
with a fixed bracket. Walk committed bars from each fill to session end.

VARIANTS
  hold_tp1       everything off at the first named target
  hold_final     everything off at the final named target
  partial_75_25  75% at TP1, 25% at the final target, stop NEVER moved
                 (his written partial convention, no discretion)
  be_after_tp1   75% at TP1, stop to entry, runner to final — his
                 break-even-only-after-TP1 ruling made mechanical
  fixed_2R       2R bracket, reference to the census convention
  no_mgmt        hold to stop or session end (the do-nothing bound)

CONVENTIONS, stated because they decide the number:
  - R on the ORIGINAL stop distance; partial variants report blended R,
    single-exit variants full R. Session end marks at the last bar.
  - Touch = fill (same as replay and every what-if in this repo). When a
    bar touches BOTH a target and the stop, the TARGET is credited first —
    OPTIMISTIC for the mechanical side; collision count is printed so the
    reader can see how much of the result rests on that call.
  - The agent book's realised numbers include everything the manager did
    (partials, trails, flips). Books are compared, not row-by-row pairs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.leak_report import (LOG, WEEKS, _rows, _short_cid,  # noqa: E402
                                 load_week)
from scripts.offline_briefings import get_bars, session_bounds   # noqa: E402

import json
import re


def enrich_fills(week, fills):
    """Day-1-era logs are thin on fill rows: backfill entry/stop/targets/
    side/minute from limit_placed rows and manage-briefing positions."""
    for day in WEEKS[week]:
        path = ROOT / "output/agent_runs" / LOG[week].format(d=day)
        if not path.exists():
            continue
        for r in _rows(path):
            cid = (day, _short_cid(r.get("candidate_id")))
            t = r.get("row")
            f = fills.setdefault(cid, {"day": day, "cid": cid})
            if t == "limit_placed":
                f.setdefault("stop", r.get("stop"))
                f.setdefault("targets", r.get("targets") or [])
                sd = str(r.get("side", "")).lower()
                if sd:
                    f.setdefault("side", +1 if "long" in sd or "buy" in sd
                                 else -1)
            elif t == "manage" and r.get("briefing"):
                bp = ROOT / str(r["briefing"])
                if not bp.exists():
                    continue
                try:
                    pos = json.loads(bp.read_text()).get("position") or {}
                except json.JSONDecodeError:
                    continue
                if pos.get("entry") is not None:
                    f.setdefault("entry", pos.get("entry"))
                stops = pos.get("stop")
                f.setdefault("targets", pos.get("targets") or [])
                f.setdefault("orig_stop_hint", stops)
                sd = str(pos.get("side", "")).lower()
                if sd:
                    f.setdefault("side", +1 if "long" in sd else -1)
                if pos.get("opened_at"):
                    f.setdefault("fill_bar", pos.get("opened_at"))
    return fills


def fill_minute(f):
    m = re.findall(r"(\d\d?:\d\d)", str(f.get("fill_bar", "")))
    return m[-1] if m else None

VARIANTS = ("hold_tp1", "hold_final", "partial_75_25", "be_after_tp1",
            "fixed_2R", "no_mgmt")


def sim(bars, day, side, entry, stop, targets, fill_minute, variant):
    """R for one fill under one bracket. Returns (r, collided)."""
    t0, tf = session_bounds(day, fill_minute)
    seg = bars[(bars.index >= tf) & (bars.index < t0 + pd.Timedelta(hours=23))]
    if seg.empty:
        return None, False
    risk = abs(entry - stop)
    if not risk:
        return None, False
    tps = [float(t.get("price")) for t in targets
           if isinstance(t, dict) and isinstance(t.get("price"), (int, float))]
    tp1 = tps[0] if tps else None
    tpF = tps[-1] if tps else None
    if variant == "fixed_2R":
        tp1 = tpF = entry + side * 2.0 * risk
    if variant in ("hold_tp1",) and tp1 is None:
        return None, False
    if variant in ("hold_final", "partial_75_25", "be_after_tp1") \
            and tpF is None:
        return None, False

    def r_at(px):
        return side * (px - entry) / risk

    cur_stop = stop
    tp1_done = False
    collided = False
    for ts, b in seg.iterrows():
        hi, lo = float(b.high), float(b.low)
        tgt = tp1 if (variant != "hold_final" and not tp1_done) else tpF
        if variant == "no_mgmt":
            tgt = None
        hit_t = tgt is not None and (hi >= tgt if side > 0 else lo <= tgt)
        hit_s = (lo <= cur_stop) if side > 0 else (hi >= cur_stop)
        if hit_t and hit_s:
            collided = True                     # target credited first
        if hit_t:
            if variant in ("hold_tp1", "fixed_2R"):
                return r_at(tgt), collided
            if variant == "hold_final":
                return r_at(tpF), collided
            if not tp1_done:
                tp1_done = True
                if variant == "be_after_tp1":
                    cur_stop = entry
                if tp1 == tpF:                  # single named target
                    return r_at(tpF), collided
                # runner continues toward tpF
                hit_f = (hi >= tpF if side > 0 else lo <= tpF)
                if hit_f:
                    return 0.75 * r_at(tp1) + 0.25 * r_at(tpF), collided
                continue
            else:                               # runner reached tpF
                return 0.75 * r_at(tp1) + 0.25 * r_at(tpF), collided
        if hit_s:
            if tp1_done:                        # 75% banked, runner stopped
                return 0.75 * r_at(tp1) + 0.25 * r_at(cur_stop), collided
            return r_at(cur_stop), collided
    mark = float(seg.close.iloc[-1])            # session end
    if tp1_done:
        return 0.75 * r_at(tp1) + 0.25 * r_at(mark), collided
    return r_at(mark), collided


def main() -> int:
    bars = get_bars()
    print("\n" + "=" * 78)
    print("  AGENT ENTRIES + MECHANICAL MANAGEMENT — same fills, no tier-3")
    print("=" * 78)

    for week in WEEKS:
        fills, exits, *_ = load_week(week)
        fills = enrich_fills(week, fills)
        book = []
        for k, f in fills.items():
            e = exits.get(k)
            if not e:
                continue
            # exit rows carry entry/original_stop too — final backfill
            f.setdefault("entry", e.get("exit_price") and None)
            if not f.get("entry"):
                f["entry"] = e.get("entry") if isinstance(e.get("entry"),
                                                          (int, float)) else \
                    f.get("entry")
            if not f.get("stop"):
                f["stop"] = e.get("orig_stop") or f.get("orig_stop_hint")
            if e.get("r") is None or not f.get("entry") or not f.get("stop") \
                    or not fill_minute(f) or not f.get("side"):
                continue
            book.append((k, f, e))
        n_all = len([1 for k in fills if exits.get(k, {}).get("r") is not None])
        agent_full = sum(e["r"] for _, _, e in book)
        agent_blend = sum(e["rb"] if e["rb"] is not None else e["r"]
                          for _, _, e in book)
        print(f"\n  {week}: {len(book)}/{n_all} fills with complete geometry")
        print(f"    AGENT-MANAGED (as traded)      "
              f"{agent_full:>+8.2f}R full   {agent_blend:>+8.2f}R blended")

        print(f"    {'mechanical variant':<28}{'total R':>10}{'WR':>7}"
              f"{'n':>4}{'collisions':>12}")
        print("    " + "-" * 62)
        deltas = {}
        for v in VARIANTS:
            rs, coll, used = [], 0, []
            for k, f, e in book:
                fm = fill_minute(f)
                try:
                    r, c = sim(bars, f["day"], f["side"], f["entry"],
                               f["stop"], f["targets"], fm, v)
                except (ValueError, KeyError, IndexError):
                    r, c = None, False
                if r is None:
                    continue
                rs.append(r)
                coll += int(c)
                used.append((k, r, e))
            if not rs:
                continue
            tot = sum(rs)
            deltas[v] = [(k, r, e["r"], e["rb"]) for k, r, e in used]
            print(f"    {v:<28}{tot:>+10.2f}{100 * np.mean([x > 0 for x in rs]):>6.0f}%"
                  f"{len(rs):>4}{coll:>12}")

        # where the manager and the bracket disagree most (vs be_after_tp1,
        # the mechanical twin of his current ruling)
        if "be_after_tp1" in deltas:
            dd = [(k, r_m, r_a, rb) for k, r_m, r_a, rb in deltas["be_after_tp1"]]
            dd.sort(key=lambda x: (x[1] - (x[3] if x[3] is not None else x[2])))
            print(f"\n    manager vs be_after_tp1 bracket — biggest disagreements"
                  f" (blended basis):")
            for k, r_m, r_a, rb in (dd[:2] + dd[-2:]):
                base = rb if rb is not None else r_a
                print(f"      {k[0]} {k[1]:<5} manager {base:>+6.2f}R   "
                      f"bracket {r_m:>+6.2f}R   Δ {r_m - base:>+6.2f}R")
    print("\n  Touch-model, target-before-stop on collisions: the mechanical")
    print("  side is flattered wherever collisions are nonzero. In-sample")
    print("  caveat applies to wk1 twice over — entries AND doctrine.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
