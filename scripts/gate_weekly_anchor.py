#!/usr/bin/env python3
"""GATE — the anchored weekly VP is anchored where HIS RULE says. Every day.

    python -m scripts.gate_weekly_anchor 2026-06-23            # exit 1 on FAIL
    python -m scripts.gate_weekly_anchor 2026-06-21 --minute 03:00
    python -m scripts.gate_weekly_anchor 2026-06-23 --briefing output/briefings/x.json
    python -m scripts.gate_weekly_anchor 2026-06-23 --chart-poc 29733 --chart-val 29655

His ask, 2026-08-15, after the anchor failed twice: *"Monday was anchored to
last Thursday from the last test or some shit, and it completely changed how
the day performed when we fixed it. Can we add that as a safe gate mechanism,
making sure that the anchored volume profile is correctly anchored?"*

THE RULE (his correction 2026-08-13, unchanged here): anchor = THIS WEEK'S
calendar-Monday 18:00 NY, developing to now. A Monday cash session, whose own
Monday-18:00 hasn't happened yet, falls back to the PRIOR Monday 18:00.
Weekly edges are the only levels that grade A alone, so a wrong anchor is not
cosmetic - the first bad pass had the POC ~900pt out.

THREE CHECKS, independent of the code they audit:
  A  the expected anchor is re-derived HERE from pure calendar arithmetic and
     compared to what agent_context.anchored_weekly_profile actually used.
     This is the exact failure class (Monday -> last Thursday): a clamp to
     available replay history, a weekday-vs-session-day slip, anything.
  B  bars actually exist at the anchor - an anchor pointing before the data
     silently degrades into "anchored at the first bar we happened to have".
  C  optional cross-checks: --briefing compares any weekly poc/val/vah found
     in a briefing JSON against the recomputed profile (catches a briefing
     builder drifting from agent_context, the m1 failure); --chart-* compares
     the hand-anchored chart drawing, ADVISORY ONLY (the ~30pt profile-binning
     residual is documented; the chart wins, the gate does not fail on it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.agent_context import anchored_weekly_profile           # noqa: E402
from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

BRIEF_TOL = 2.0      # pts: briefing vs recompute must agree (same code lineage)
CHART_TOL = 45.0     # pts: chart drawing vs recompute, advisory (binning residual)


def expected_anchor(sess_day: str, decision: pd.Timestamp) -> pd.Timestamp:
    """Pure calendar: this cash-week's Monday 18:00 NY, else prior Monday."""
    cash = pd.Timestamp(sess_day) + pd.Timedelta(days=1)      # label -> cash day
    monday = cash - pd.Timedelta(days=int(cash.weekday()))    # calendar Monday
    anchor = pd.Timestamp(f"{monday:%Y-%m-%d} 18:00", tz=NY)
    if anchor >= decision:                                    # Monday cash session
        anchor -= pd.Timedelta(days=7)                        # -> prior Monday
    return anchor


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sess_day")
    ap.add_argument("--minute", default="03:00",
                    help="landing/decision minute NY (default 03:00)")
    ap.add_argument("--briefing", help="briefing JSON to cross-check (check C)")
    ap.add_argument("--chart-poc", type=float)
    ap.add_argument("--chart-val", type=float)
    ap.add_argument("--chart-vah", type=float)
    a = ap.parse_args()

    t = pd.Timestamp(f"{a.sess_day} {a.minute}", tz=NY)
    t0 = pd.Timestamp(f"{a.sess_day} 18:00", tz=NY)
    if t < t0:
        t += pd.Timedelta(days=1)

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]

    exp = expected_anchor(a.sess_day, t)
    aw = anchored_weekly_profile(bars, a.sess_day, upto=t)
    got = pd.Timestamp(aw["anchor"])
    if got.tzinfo is None:
        got = got.tz_localize(NY)

    fails = []
    print(f"\nWEEKLY-ANCHOR GATE — session-day {a.sess_day}, as of {t:%a %H:%M} NY")
    print(f"  expected anchor (calendar rule): {exp:%a %Y-%m-%d %H:%M %Z}")
    print(f"  computed anchor (agent_context): {got:%a %Y-%m-%d %H:%M %Z}")

    # A — the anchor is the rule's anchor
    if abs((got - exp).total_seconds()) > 60:
        fails.append(f"A: anchor mismatch — computed {got:%a %d %b %H:%M}, "
                     f"rule says {exp:%a %d %b %H:%M}")
        print("  A  FAIL — this is the Monday->Thursday failure class")
    else:
        print("  A  pass")

    # B — data actually reaches the anchor
    win = bars[(bars.index >= exp) & (bars.index < exp + pd.Timedelta(hours=2))]
    if win.empty:
        fails.append("B: no bars within 2h of the anchor — the profile is "
                     "silently anchored at whatever data begins")
        print("  B  FAIL — no bars at the anchor")
    else:
        print(f"  B  pass — first bar at anchor: {win.index[0]:%a %H:%M}")

    print(f"  profile: POC {aw['awPOC']:.2f}  VAL {aw['awVAL']:.2f}  "
          f"VAH {aw['awVAH']:.2f}")

    # C — optional cross-checks
    if a.briefing:
        j = json.loads(Path(a.briefing).read_text())
        found = {}
        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    kp = f"{path}/{k}".lower()
                    if isinstance(v, (int, float)) and "weekly" in kp:
                        for tag, ours in (("poc", aw["awPOC"]),
                                          ("val", aw["awVAL"]),
                                          ("vah", aw["awVAH"])):
                            if kp.endswith(tag) or f"_{tag}" in kp.split("/")[-1]:
                                found[kp] = (float(v), ours)
                    else:
                        walk(v, kp)
        walk(j)
        for k, (bv, ours) in sorted(found.items()):
            d = abs(bv - ours)
            ok = d <= BRIEF_TOL
            print(f"  C  briefing {k}: {bv:.2f} vs recompute {ours:.2f} "
                  f"(Δ{d:.2f}) {'ok' if ok else 'FAIL'}")
            if not ok:
                fails.append(f"C: briefing {k} off by {d:.1f}pt — the builder "
                             f"has drifted from agent_context")
        if not found:
            print("  C  briefing carries no weekly poc/val/vah fields — "
                  "nothing cross-checked")

    for tag, chart, ours in (("poc", a.chart_poc, aw["awPOC"]),
                             ("val", a.chart_val, aw["awVAL"]),
                             ("vah", a.chart_vah, aw["awVAH"])):
        if chart is not None:
            d = abs(chart - ours)
            note = "ok" if d <= CHART_TOL else \
                "LARGE — advisory only, but re-check the drawing's anchor by eye"
            print(f"  C  chart {tag}: {chart:.2f} vs {ours:.2f} (Δ{d:.2f}) {note}")

    if fails:
        print("\n  GATE FAILED:")
        for f in fails:
            print(f"    {f}")
        print("  A day run on a wrong weekly anchor is not worth scoring — "
              "weekly edges grade A alone.\n")
        return 1
    print("\n  GATE PASSED.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
