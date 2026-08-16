#!/usr/bin/env python3
"""WHERE THE MONEY LEAKS — the PREREG-june-leak-analysis buckets, computed.

    python -m scripts.leak_report

Runs over the two complete agent weeks:

  jn1   2026-05-31..2026-06-04   UNSEEN June week 1 (0.4.7-era stack,
                                 break-even ruling landed mid-week)
  wk1   2026-06-21..2026-06-25   the NARRATED week the doctrine was built on
                                 (earlier stack; in-sample, flattered)

Every section states which week, which n, and — where a what-if is priced —
exactly what was assumed. What-ifs use the same touch-model bar walk as the
rest of the repo: optimistic on fills, honest about it.

The reasoning-first anchor governs the read: a "leak" here is a candidate
finding for HIM, not a change. Three behaviours are excluded from the
optimisation surface by his standing rulings (stall-BE, the pass rate,
C-grade no-trail) — they are REPORTED, never scored as defects.
"""
from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.offline_briefings import get_bars, session_bounds   # noqa: E402
from scripts.raw_trigger_census import day_rows                  # noqa: E402
from src.htf_ma.levels import NY                                 # noqa: E402

WEEKS = {
    "jn1 (UNSEEN)": ["2026-05-31", "2026-06-01", "2026-06-02",
                     "2026-06-03", "2026-06-04"],
    "wk1 (narrated, in-sample)": ["2026-06-21", "2026-06-22", "2026-06-23",
                                  "2026-06-24", "2026-06-25"],
}
LOG = {"jn1 (UNSEEN)": "{d}_jn1.jsonl",
       "wk1 (narrated, in-sample)": "{d}_wk1.jsonl"}


def _rows(path: Path):
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _num(v):
    return float(v) if isinstance(v, (int, float)) else None


def _first_num(r: dict, keys):
    for k in keys:
        v = _num(r.get(k))
        if v is not None:
            return v
    return None


R_FULL = ("r_result", "r_full_target_whole_position_at_final_exit")
R_BLEND = ("r_blended", "r_blended_across_partials")


def _short_cid(cid) -> str:
    """Join key across schemas: 'jn1-0531-P2' / 'WK1-D21-L1-0342' / 'P2'
    all reduce to their window-serial token (P2, L1, A5...)."""
    parts = str(cid).split("-")
    for p in parts:
        if len(p) <= 4 and p[:1] in "LPA" and any(ch.isdigit() for ch in p):
            return p
    return str(cid)


def _classify_exit(e: dict) -> str:
    """One label per exit, derived when the log doesn't state one."""
    raw = str(e.get("reason") or "")
    low = raw.lower()
    for k, lab in (("breakeven", "breakeven_stop"), ("trail", "trailed_stop"),
                   ("flatten", "flattened_pre_open"), ("flip", "flipped"),
                   ("final_target", "final_target"), ("target", "target"),
                   ("stop", "full_stop")):
        if k in low:
            return lab
    r = e.get("r")
    if r is not None:
        if r <= -0.9:
            return "full_stop"
        if abs(r) < 0.05:
            return "breakeven_stop"
    if "portion" in low:                    # wk1 partial-ledger exit_detail
        return "target" if (r or 0) > 0.4 else "managed_exit"
    return "managed_exit"


def load_week(week: str):
    """Normalise both log schemas into one record set. Keys are
    (day, short_cid) so day-1's long ids join day-2's bare ones."""
    fills, exits, manages, passes, convs, takes = {}, {}, [], [], {}, []
    for day in WEEKS[week]:
        p = ROOT / "output/agent_runs" / LOG[week].format(d=day)
        if not p.exists():
            continue
        for r in _rows(p):
            t, cid = r.get("row"), (day, _short_cid(r.get("candidate_id")))
            if t == "fill":
                side = str(r.get("side") or r.get("position", "")).lower()
                fills[cid] = {
                    "day": day, "cid": cid, "window": r.get("window"),
                    "conviction": r.get("conviction")
                    or r.get("size_label", "?"),
                    "entry": _num(r.get("entry") or r.get("fill_price")),
                    "stop": _num(r.get("stop")),
                    "side": +1 if "long" in side or "buy" in side else -1,
                    "targets": r.get("targets") or [],
                    "beyond_cap": bool(r.get("beyond_written_cap")),
                    "fill_bar": r.get("fill_bar_start") or r.get("filled_at")}
            elif t == "exit":
                exits[cid] = {
                    "day": day, "cid": cid,
                    "r": _first_num(r, R_FULL),
                    "rb": _first_num(r, R_BLEND),
                    "reason": str(r.get("exit_reason")
                                  or r.get("exit_detail", "?"))[:60],
                    "exit_minute": r.get("exit_minute"),
                    "exit_price": _num(r.get("exit_price")),
                    "orig_stop": _num(r.get("original_stop")),
                    "conviction": r.get("conviction", "?"),
                    "window": r.get("window"),
                    "beyond_cap": bool(r.get("beyond_written_cap")),
                    "mae": _num(r.get("mae_pts") or r.get("mae_post_fill")),
                    "partials": r.get("partials_taken")}
            elif t == "manage" and not r.get("voided"):
                out = r.get("output") or {}
                action = (out.get("action") if isinstance(out, dict)
                          else None) or r.get("action")
                open_r = _num(r.get("open_r_at_call"))
                if open_r is None and r.get("briefing"):
                    bp = ROOT / str(r["briefing"])
                    if bp.exists():
                        try:
                            pos = json.loads(bp.read_text()).get("position", {})
                            open_r = _num(pos.get("open_pnl_in_R"))
                        except json.JSONDecodeError:
                            pass
                manages.append({"day": day, "cid": cid, "action": action,
                                "open_r": open_r,
                                "why": r.get("reason_for_call")})
            elif t == "trigger":
                out = r.get("output") if isinstance(r.get("output"), dict) \
                    else {}
                d = r.get("decision") or out.get("decision")
                dm = str(r.get("decision_minute", ""))
                minute = dm[-8:-3] if dm.endswith(" ET") else dm[-5:]
                cv = out.get("conviction") or r.get("conviction")
                if cv:
                    convs[cid] = str(cv)[:1].upper()
                if str(d).startswith("pass"):
                    passes.append({"day": day, "minute": minute})
                elif str(d).startswith("take"):
                    takes.append({"day": day, "minute": minute})
    # backfill conviction/window onto exits from fills and trigger verdicts
    for k, e in exits.items():
        f = fills.get(k, {})
        if str(e.get("conviction", "?")) in ("?", "None"):
            e["conviction"] = convs.get(k) or f.get("conviction", "?")
        if not e.get("window"):
            e["window"] = f.get("window")
    return fills, exits, manages, passes, takes


def walk_outcome(bars, day, side, entry, stop, targets, t_from):
    """From t_from to session end with the ORIGINAL stop: which of
    (tp1, final target, stop) is touched first?  Touch model, like replay."""
    t0, t = session_bounds(day, t_from)
    seg = bars[(bars.index >= t) & (bars.index < t0 + pd.Timedelta(hours=23))]
    tps = [_num(x.get("price")) for x in targets if _num(x.get("price"))]
    tp1 = tps[0] if tps else None
    tpF = tps[-1] if tps else None
    risk = abs(entry - stop) if entry and stop else None
    hit = {"tp1": None, "tpF": None, "stop": None}
    for ts, b in seg.iterrows():
        if tp1 and hit["tp1"] is None and (
                (side > 0 and b.high >= tp1) or (side < 0 and b.low <= tp1)):
            hit["tp1"] = ts
        if tpF and hit["tpF"] is None and (
                (side > 0 and b.high >= tpF) or (side < 0 and b.low <= tpF)):
            hit["tpF"] = ts
        if stop and hit["stop"] is None and (
                (side > 0 and b.low <= stop) or (side < 0 and b.high >= stop)):
            hit["stop"] = ts
        if hit["stop"] is not None and hit["tpF"] is not None:
            break
    first = min((v, k) for k, v in hit.items() if v is not None)[1] \
        if any(v is not None for v in hit.values()) else "none"
    # price only what actually printed: final target if it printed, else
    # TP1 if it printed — never a target the market did not reach.
    if risk and hit["tpF"] is not None and tpF:
        r_reached = abs(tpF - entry) / risk
    elif risk and hit["tp1"] is not None and tp1:
        r_reached = abs(tp1 - entry) / risk
    else:
        r_reached = None
    return first, hit, r_reached


def main() -> int:
    bars = get_bars()
    print("\n" + "=" * 78)
    print("  LEAK REPORT — two complete agent weeks, prereg buckets")
    print("=" * 78)

    for week in WEEKS:
        fills, exits, manages, passes, takes = load_week(week)
        R = [e["r"] for e in exits.values() if e["r"] is not None]
        RB = [e["rb"] for e in exits.values() if e["rb"] is not None]
        print(f"\n{'#' * 78}\n  {week}: {len(exits)} closed, "
              f"{sum(R):+.2f}R full / {sum(RB):+.2f}R blended, "
              f"{len(passes)} passes, {len(manages)} manage calls")

        # ---- B-ADV: adverse-excursion holds (his explicit ask) -------------
        print(f"\n  [B-ADV] MANAGE CALLS WITH POSITION UNDER WATER "
              f"(open R < -0.10 at the call)")
        adv = [m for m in manages if m["open_r"] is not None
               and m["open_r"] < -0.10]
        cov = sum(1 for m in manages if m["open_r"] is not None)
        print(f"    coverage: {cov}/{len(manages)} manage calls carry an "
              f"open-R reading")
        per_day = defaultdict(lambda: [0, 0])
        rows = []
        for m in adv:
            held = str(m["action"]) in ("hold", "None")
            per_day[m["day"]][0 if held else 1] += 1
            ex = exits.get(m["cid"], {})
            m["_short"] = m["cid"][1]
            r = ex.get("r")
            out = ("full stop" if r is not None and r <= -0.9 else
                   "partial loss" if r is not None and r < 0 else
                   "recovered" if r is not None else "?")
            rows.append((m["day"], m["_short"], m["open_r"],
                         str(m["action"]), out, r))
        for day in WEEKS[week]:
            h, a = per_day.get(day, [0, 0])
            print(f"      {day}  held under water: {h}   acted: {a}")
        if rows:
            print(f"    {'day':<12}{'cid':<18}{'openR':>7} {'verdict':<11}"
                  f"{'final':<13}{'final R':>8}")
            for d, c, o, act, out, r in sorted(rows):
                print(f"    {d:<12}{str(c)[:17]:<18}{o:>+7.2f} {act:<11}"
                      f"{out:<13}{r if r is not None else float('nan'):>+8.2f}")
            held_rows = [x for x in rows if x[3] in ("hold", "None")]
            stopped = sum(1 for x in held_rows if x[4] == "full stop")
            rec = sum(1 for x in held_rows if x[4] == "recovered")
            print(f"    held-under-water positions: {len(held_rows)} -> "
                  f"{stopped} full-stopped, {rec} recovered")

        # ---- B1/B2: exit attribution + what the exit left ------------------
        print(f"\n  [B1] EXITS BY REASON, with the original-stop what-if")
        by_reason = defaultdict(list)
        for cid, e in exits.items():
            by_reason[_classify_exit(e)].append(cid)
        print(f"    {'exit reason':<28}{'n':>3}{'ΣR full':>9}{'ΣR blend':>9}")
        for reason, cids in sorted(by_reason.items(),
                                   key=lambda kv: -len(kv[1])):
            rr = sum(exits[c]["r"] or 0 for c in cids)
            rb = sum(exits[c]["rb"] or 0 for c in cids)
            print(f"    {reason:<28}{len(cids):>3}{rr:>+9.2f}{rb:>+9.2f}")
        # what-if for early exits: BE-stops, trails, flattens
        early = [c for c in exits
                 if _classify_exit(exits[c]) in
                 ("breakeven_stop", "trailed_stop", "flattened_pre_open",
                  "flipped")]
        printed_later, stopped_anyway, unresolved = [], [], []
        for c in early:
            e, f = exits[c], fills.get(c)
            if not f or not e.get("exit_minute") or not f.get("entry") \
                    or not e.get("orig_stop") and not f.get("stop"):
                unresolved.append(c)
                continue
            stop = e.get("orig_stop") or f.get("stop")
            try:
                first, hit, r_tpF = walk_outcome(
                    bars, e["day"], f["side"], f["entry"], stop,
                    f["targets"], str(e["exit_minute"])[-5:])
            except (ValueError, KeyError, IndexError):
                unresolved.append(c)
                continue
            if first in ("tp1", "tpF"):
                printed_later.append((c, first, r_tpF, e["r"]))
            elif first == "stop":
                stopped_anyway.append((c, e["r"]))
            else:
                unresolved.append(c)
        print(f"    early exits (BE/trail/flatten/flip): {len(early)}")
        if printed_later:
            left = sum((r_t or 0) - (r or 0)
                       for _, _, r_t, r in printed_later)
            print(f"      a named TARGET printed after the exit: "
                  f"{len(printed_later)}  (full-target R left ~{left:+.1f}R,"
                  f" touch-model upper bound)")
            for c, which, r_t, r in printed_later:
                print(f"        {c[0]} {c[1]}: exited {r:+.2f}R, {which} "
                      f"printed (full ~{r_t if r_t else 0:+.2f}R)")
        if stopped_anyway:
            saved = sum(1 + (r or 0) for _, r in stopped_anyway)
            print(f"      original stop would have hit FIRST: "
                  f"{len(stopped_anyway)}  (management saved ~{saved:+.1f}R"
                  f" vs full stops)")
        if unresolved:
            print(f"      unresolved (missing fields / no touch): "
                  f"{len(unresolved)}")

        # ---- A4: does the grade ladder sort? -------------------------------
        print(f"\n  [A4] R BY CONVICTION GRADE")
        byg = defaultdict(list)
        for e in exits.values():
            if e["r"] is not None:
                byg[str(e["conviction"])[:1].upper()].append(e["r"])
        for g in sorted(byg):
            v = byg[g]
            print(f"      {g}: n={len(v):>2}  total {sum(v):>+6.2f}R  "
                  f"mean {np.mean(v):>+5.2f}R  WR {100 * np.mean([x > 0 for x in v]):>4.0f}%")

        # ---- C2: windows + caps -------------------------------------------
        print(f"\n  [C2] R BY WINDOW  /  CAP TAG")
        byw = defaultdict(list)
        for e in exits.values():
            if e["r"] is not None:
                byw[str(e["window"] or "?").split()[0]].append(
                    (e["r"], e["beyond_cap"]))
        for w in ("LONDON", "NY_PRE", "NY_AM", "?"):
            if w not in byw:
                continue
            v = byw[w]
            bc = [r for r, b in v if b]
            print(f"      {w:<8} n={len(v):>2}  total "
                  f"{sum(r for r, _ in v):>+6.2f}R"
                  + (f"   beyond-written-cap: {len(bc)} fills "
                     f"{sum(bc):+.2f}R" if bc else ""))

        # ---- A1: what the passes left behind (census MFE proxy) ------------
        print(f"\n  [A1] PASS QUALITY — census-MFE proxy "
              f"(run_mfe_r before candle-extreme stop; NOT his entries)")
        pool = {}
        for day in WEEKS[week]:
            for row in day_rows(bars, day):
                pool[(day, f"{int(row['hm']) // 60:02d}:"
                            f"{int(row['hm']) % 60:02d}")] = row["run_mfe_r"]
        hits = [pool[(p['day'], p['minute'])] for p in passes
                if (p['day'], p['minute']) in pool]
        take_m = [pool[(tk['day'], tk['minute'])] for tk in takes
                  if (tk['day'], tk['minute']) in pool]
        if hits:
            print(f"      {len(hits)}/{len(passes)} passes matched to census "
                  f"triggers: P(mfe>=2R) {100 * np.mean([h >= 2 for h in hits]):.0f}%"
                  f"   median mfe {np.median(hits):.2f}R")
        if take_m:
            print(f"      {len(take_m)}/{len(takes)} takes matched:        "
                  f"P(mfe>=2R) {100 * np.mean([h >= 2 for h in take_m]):.0f}%"
                  f"   median mfe {np.median(take_m):.2f}R")

        # ---- C1: day concentration ----------------------------------------
        byd = defaultdict(float)
        for e in exits.values():
            byd[e["day"]] += e["r"] or 0
        days = sorted(byd.items())
        print(f"\n  [C1] DAYS: "
              + "  ".join(f"{d[5:]} {r:+.2f}" for d, r in days))
    print("\n  All what-ifs are touch-model and use the ORIGINAL stop — an")
    print("  upper bound on what holding offered, not a claim anyone",
          "captures it.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
