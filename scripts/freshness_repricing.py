#!/usr/bin/env python3
"""WHAT THE FRESHNESS CAP WOULD HAVE DONE — deterministic, no agent involved.

    python -m scripts.freshness_repricing

The 0.4.8 amendment caps the GRADE, never the licence: every trade that was
taken is still taken, at the same entry, same stop, same targets. The only
thing that changes is the conviction label — and the label is load-bearing,
because `tv-manage` books 50% at TP1 on an A, 75% on a B and 100% on a C.

So the effect is computable exactly, with no re-run and no LLM sampling:
regrade each take under the cap, then price both grade-sets through the SAME
partial policy on committed bars. The difference is attributable to the
regrade alone.

POLICY HELD FIXED FOR BOTH ARMS (his rulings, mechanised):
  - book `partial_pct` at TP1 by grade (A 50 / B 75 / C 100)
  - break-even ONLY after TP1 (his ruling, 2026-08-16)
  - runner to the final named target, else session end
  - touch model, original stop, target credited before stop on a collision

THIS IS NOT THE AGENT BOOK. It is one fixed policy applied twice, so its
absolute totals differ from what was traded; only the DELTA between arms
means anything, and the realised book is printed beside it for scale.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.leak_report import (LOG, WEEKS, _rows, _short_cid,   # noqa: E402
                                 load_week)
from scripts.level_visits import freshness                        # noqa: E402
from scripts.mech_manage_whatif import enrich_fills, fill_minute  # noqa: E402
from scripts.offline_briefings import get_bars, session_bounds    # noqa: E402

PCT = {"A": 0.50, "B": 0.75, "C": 1.00}
RISK = {"A": 250.0, "B": 200.0, "C": 150.0}      # his stated dollar sizing


def regrade(logged: str, fresh: dict | None) -> str:
    """0.4.8: only a FRESH level may grade A; a 3rd+ visit caps at C."""
    g = (logged or "B").upper()[:1]
    if g not in PCT:
        g = "B"
    if not fresh:
        return g
    if fresh["level_visits_this_session"] >= 3:
        return "C"
    if g == "A" and not fresh["fresh"]:
        return "B"
    return g


def price(bars, day, side, entry, stop, targets, minute, pct):
    """Blended R under: partial at TP1, BE after TP1, runner to final."""
    t0, tf = session_bounds(day, minute)
    seg = bars[(bars.index >= tf) & (bars.index < t0 + pd.Timedelta(hours=23))]
    if seg.empty:
        return None
    risk = abs(entry - stop)
    tps = [float(t.get("price")) for t in targets
           if isinstance(t, dict) and isinstance(t.get("price"), (int, float))]
    if not risk or not tps:
        return None
    tp1, tpF = tps[0], tps[-1]

    def r_at(px):
        return side * (px - entry) / risk

    cur_stop, banked = stop, False
    for _, b in seg.iterrows():
        hi, lo = float(b.high), float(b.low)
        if not banked:
            if (hi >= tp1) if side > 0 else (lo <= tp1):
                banked = True
                cur_stop = entry                       # BE only after TP1
                if pct >= 1.0 or tp1 == tpF:
                    return r_at(tp1)
                if (hi >= tpF) if side > 0 else (lo <= tpF):
                    return pct * r_at(tp1) + (1 - pct) * r_at(tpF)
                continue
            if (lo <= cur_stop) if side > 0 else (hi >= cur_stop):
                return r_at(cur_stop)
        else:
            if (hi >= tpF) if side > 0 else (lo <= tpF):
                return pct * r_at(tp1) + (1 - pct) * r_at(tpF)
            if (lo <= cur_stop) if side > 0 else (hi >= cur_stop):
                return pct * r_at(tp1) + (1 - pct) * r_at(cur_stop)
    mark = float(seg.close.iloc[-1])
    return (pct * r_at(tp1) + (1 - pct) * r_at(mark)) if banked else r_at(mark)


def main() -> int:
    bars = get_bars()
    hb = bars[["open", "high", "low", "close"]]
    print("\n" + "=" * 78)
    print("  FRESHNESS CAP (0.4.8) — deterministic regrade + re-price")
    print("=" * 78)

    grand = defaultdict(float)
    for week in WEEKS:
        fills, exits, *_ = load_week(week)
        fills = enrich_fills(week, fills)
        # logged grade + rejected level per candidate, in session order
        # DEDUPE FIRST. An escalation re-adjudicates the same candidate and
        # logs it again — on 2026-06-02 candidate A1 appears three times. A
        # naive pass counts those as three visits to the level and penalises
        # a trade for revisiting ITSELF, which is both wrong and (since A1
        # won) wrong in the direction that flatters the change. Keep the last
        # verdict per candidate, then order by decision minute.
        seen = {}
        for day in WEEKS[week]:
            p = ROOT / "output/agent_runs" / LOG[week].format(d=day)
            if not p.exists():
                continue
            for r in _rows(p):
                if r.get("row") != "trigger":
                    continue
                o = r.get("output") if isinstance(r.get("output"), dict) else {}
                dec = str(o.get("decision") or r.get("decision") or "")
                if not dec.startswith("take"):
                    continue
                dm = str(r.get("decision_minute", ""))
                minute = dm[-8:-3] if dm.endswith(" ET") else dm[-5:]
                px = (o.get("rejected_level") or {}).get("price")
                seen[(day, _short_cid(r.get("candidate_id")))] = {
                    "grade": str(o.get("conviction") or "B")[:1].upper(),
                    "px": px if isinstance(px, (int, float)) else None,
                    "minute": minute}
        meta, prior = {}, defaultdict(list)
        for key in sorted(seen, key=lambda k: (k[0], seen[k]["minute"])):
            m = seen[key]
            meta[key] = {**m, "prior": list(prior[key[0]])}
            if m["px"] is not None:
                prior[key[0]].append(float(m["px"]))

        rows, chg = [], []
        for key, m in meta.items():
            f, e = fills.get(key), exits.get(key)
            if not f or not e or e.get("r") is None:
                continue
            fm = fill_minute(f)
            if not fm or not f.get("entry") or not f.get("stop") \
                    or not f.get("side"):
                continue
            fr = (freshness(hb, key[0], m["minute"], m["px"], m["prior"])
                  if m["px"] is not None else None)
            g0 = m["grade"] if m["grade"] in PCT else "B"
            g1 = regrade(g0, fr)
            r0 = price(bars, key[0], f["side"], f["entry"], f["stop"],
                       f["targets"], fm, PCT[g0])
            r1 = price(bars, key[0], f["side"], f["entry"], f["stop"],
                       f["targets"], fm, PCT[g1])
            if r0 is None or r1 is None:
                continue
            rows.append((key, g0, g1, r0, r1, e["r"], fr))
            if g0 != g1:
                chg.append((key, g0, g1, r0, r1, fr))

        b0 = sum(x[3] for x in rows)
        b1 = sum(x[4] for x in rows)
        realised = sum(x[5] for x in rows)
        # DOLLARS on the REALISED book: grade drives his risk per trade, and
        # that is where a cap actually bites — the partial split only matters
        # on trades that reach TP1, and stale trades mostly do not.
        d0 = sum(x[5] * RISK[x[1]] for x in rows)
        d1 = sum(x[5] * RISK[x[2]] for x in rows)
        grand[week] = b1 - b0
        grand["$" + week] = 0.0
        print(f"\n  {week}   n={len(rows)} priced   "
              f"(realised, as traded: {realised:+.2f}R full)")
        print(f"    same policy, LOGGED grades    {b0:>+8.2f}R")
        print(f"    same policy, 0.4.8 grades     {b1:>+8.2f}R"
              f"    delta {b1 - b0:>+6.2f}R")
        print(f"    realised book at his sizing: logged grades ${d0:>+8.0f}"
              f"   0.4.8 grades ${d1:>+8.0f}   delta ${d1 - d0:>+7.0f}")
        print(f"    grades changed: {len(chg)}/{len(rows)}")
        for key, g0, g1, r0, r1, fr in chg:
            v = fr["level_visits_this_session"] if fr else "?"
            t = fr["tests_15m_60min"] if fr else "?"
            print(f"      {key[0]} {key[1]:<5} {g0}->{g1}  "
                  f"(visit {v}, 15m tests {t})   "
                  f"{r0:+.2f}R -> {r1:+.2f}R")
    print(f"\n  TOTAL DELTA across both weeks: "
          f"{sum(grand.values()):+.2f}R")
    print("  One fixed policy priced twice; the delta isolates the regrade.")
    print("  Absolute totals are NOT the agent book — the manager is absent"
          " from both arms.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
