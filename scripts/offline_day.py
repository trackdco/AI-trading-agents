#!/usr/bin/env python3
"""THE OFFLINE DAY HARNESS — the runbook's orchestration, as a state machine.

    python -m scripts.offline_day 2026-06-21 --run v09 --next
    python -m scripts.offline_day 2026-06-21 --run v09 --submit <verdict.json>

WHY A STATE MACHINE AND NOT A SCRIPT THAT CALLS AGENTS. Agents cannot be
called from Python here, and a workflow cannot read files. So the day is
driven as a resumable protocol: `--next` advances the mechanical state as far
as it can and stops at the first point that needs a judgement, writing the
briefing and printing a DIRECTIVE naming which agent to call. The caller runs
that agent, writes the verdict back with `--submit`, and calls `--next`
again. The entire day's state lives in the run log, so it is resumable,
auditable, parallel across days, and identical in structure to what his Mac
produces.

WHAT IT IMPLEMENTS, from `docs/RUNBOOK-replay-scoring.md`:

  - windows LONDON 03:00-04:59 / NY_PRE 08:00-09:29 / NY_AM 09:30-11:00,
    NY_PRE entries cut off 09:10 (T52)
  - thesis at each window open; trigger per scanned candidate in time order
  - one position at a time; candidates arriving while a position is open are
    logged as gated passes unless the flip licence applies (T68)
  - limit lifecycle: placed at the agent's entry, 5 bars (10 min) expiry,
    cancelled if price reaches the named cancel level first, touch = fill
  - management minutes computed mechanically: intermediate level reached or
    broken, TP1, stall episode, pre_cash_open, window_closing — coalesced to
    at most one call per bar (runbook 2c)
  - stop only ever tightens; T51 flatten by 09:29:59 for pre-market carries
  - exits at stop / final target / flatten / session end

WHAT IT DOES NOT DO, and says so in every briefing it writes: there is no
chart screenshot offline. Every candle, level and behaviour block is stated
numerically and was certified to reproduce his Mac's briefings exactly
(`scripts/certify_offline_briefings.py`), and causality is gated
adversarially (`scripts/gate_offline_causality.py`). But the agents on his
Mac also SEE the chart, and early evidence is that its absence pushes
borderline takes toward passes. Read an offline book as "how it reasons from
the numbers", not as a claim about what the Mac would have done.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.chop_state import state_at as chop_at                # noqa: E402
from scripts.htf_level_behavior import behavior_at                # noqa: E402
from scripts.level_visits import freshness                        # noqa: E402
from scripts.offline_scan import scan_day                         # noqa: E402

WINDOWS = [("LONDON", "03:00", "04:59", "04:59"),
           ("NY_PRE", "08:00", "09:29", "09:10"),   # entries cut off 09:10
           ("NY_AM", "09:30", "11:00", "11:00")]
CAPS = {"LONDON": 2, "NY_PRE": 1, "NY_AM": 2}
LIMIT_BARS = 5            # 5 x 2m = 10 minutes
NO_CHART = ("NO CHART IMAGE EXISTS in this environment. Every candle, level "
            "and higher-timeframe behaviour block below is stated numerically "
            "and reproduces exactly from committed bars. Adjudicate on the "
            "numbers; do not refuse for the missing image.")


def hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def mstr(v: int) -> str:
    return f"{v // 60:02d}:{v % 60:02d}"


class Day:
    """One session-day's state, reconstructed from its log every call."""

    def __init__(self, sess_day: str, run: str):
        self.day = sess_day
        self.run = run
        self.path = ROOT / f"output/agent_runs/{sess_day}_{run}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows = []
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                line = line.strip()
                if line:
                    try:
                        self.rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def write(self, row: dict):
        self.rows.append(row)
        with self.path.open("a") as f:
            f.write(json.dumps(row) + "\n")

    # ---- derived state -------------------------------------------------
    def thesis_for(self, window: str):
        for r in reversed(self.rows):
            if r.get("row") == "thesis" and r.get("window") == window:
                return r.get("output")
        return None

    def adjudicated(self) -> set:
        return {r["candidate_id"] for r in self.rows
                if r.get("row") in ("trigger", "candidate_gated")
                and r.get("candidate_id")}

    def fills_in(self, window: str) -> int:
        return sum(1 for r in self.rows
                   if r.get("row") == "fill" and r.get("window") == window)

    def open_position(self):
        pos = None
        for r in self.rows:
            if r.get("row") == "fill":
                pos = dict(r)
                pos["stop_now"] = r["stop"]
                pos["actions"] = []
            elif r.get("row") == "manage" and pos:
                o = r.get("output") or {}
                if o.get("new_stop") is not None:
                    pos["stop_now"] = o["new_stop"]
                pos["actions"].append({"minute": r.get("minute"),
                                       "action": o.get("action"),
                                       "reason": o.get("reason")})
            elif r.get("row") == "exit":
                pos = None
        return pos

    def pending(self):
        """The last directive awaiting a verdict, if any."""
        for r in reversed(self.rows):
            if r.get("row") == "DIRECTIVE":
                return r
            if r.get("row") in ("thesis", "trigger", "manage"):
                return None
        return None


def build_trigger_briefing(bars, day, minute, cand, thesis, macro,
                           window, fills, cap, pos, prior_takes, all_days):
    core = OB.build_levels(bars, day, minute, all_days)
    above, below = OB.above_below(core)
    _, t = OB.session_bounds(day, minute)
    lm = OB.level_map(core)
    # up to 3 candidate levels (runbook 10j: keep briefings lean)
    names = list(dict.fromkeys(
        [n for n in cand.get("second_levels_closed", [])][:2]
        + [f"bb_ma_{cand['tfs'][0]}m"]))[:3]
    htf = {n: behavior_at(bars[["open", "high", "low", "close"]], day,
                          minute, lm[n])
           for n in names if n in lm}
    rl_px = lm.get(names[0]) if names and names[0] in lm else None
    return {
        "role": "tv-trigger", "candidate_id": cand["cid"],
        "window": f"{window} {cand['window']}",
        "decision_minute": f"{day}T{minute} ET",
        "chart_image": NO_CHART,
        "leak_check": ("pass - computed from committed bars strictly before "
                       "this minute; gated adversarially by "
                       "scripts.gate_offline_causality"),
        "price_at_decision": core["price_at_decision"],
        "signal_candle_2m": OB.candle(bars, t, 2) if 2 in cand["tfs"] else None,
        "signal_candle_3m": OB.candle(bars, t, 3) if 3 in cand["tfs"] else None,
        "pair_shape": cand["shape"],
        "signal_direction_2m_3m": cand["direction"],
        "levels_closed_SCANNER": cand["second_levels_closed"],
        "levels_rejected_SCANNER": cand["second_levels_rejected"],
        "levels_closed_note": ("Scanner output is mechanical. Verify against "
                               "the candle and the level values and correct it "
                               "in your reason if it is wrong."),
        "higher_timeframe_at_candidate_levels": htf,
        "levels_at_decision_CHART": {},
        "levels_at_decision_BUILD": core["levels_at_decision_BUILD"],
        "levels_above_price": above, "levels_below_price": below,
        "chop_state": chop_at(bars, day, minute),
        "level_visits_this_session": (
            freshness(bars[["open", "high", "low", "close"]], day, minute,
                      rl_px, prior_takes) if rl_px else None),
        "fills_this_window": fills, "window_cap": cap,
        "position_state": ("FLAT." if not pos else
                           f"OPEN {pos['side']} from {pos['entry']}, "
                           f"stop {pos['stop_now']}"),
        "thesis": thesis, "macro": macro,
        "fill_model_note": ("Limits fill on touch, 5 bars (10 min) expiry, "
                            "cancelled if price reaches your cancel level "
                            "first."),
        "what_to_emit": "your trigger JSON, per your contract.",
    }


def build_thesis_briefing(bars, day, minute, window, prior, since, all_days):
    core = OB.build_levels(bars, day, minute, all_days)
    _, t = OB.session_bounds(day, minute)
    return {
        "role": "tv-thesis", "event_trigger": "window_open",
        "window": f"{window} {minute}", "decision_minute": f"{day}T{minute} ET",
        "chart_image": NO_CHART,
        "leak_check": "pass - committed bars strictly before this minute.",
        "price_at_decision": core["price_at_decision"],
        "last_completed_2m_bar": OB.candle(bars, t, 2),
        "levels_at_decision_CHART": {},
        "levels_at_decision_BUILD": core["levels_at_decision_BUILD"],
        "flush_inputs": OB.flush_inputs(bars, day, minute),
        "last_15m_candles": OB.last_15m_candles(bars, day, minute),
        "chop_state": chop_at(bars, day, minute),
        "prior_thesis": prior,
        "what_happened_since_the_last_read": since,
        "what_to_emit": "your thesis JSON for this window, per your contract.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sess_day")
    ap.add_argument("--run", required=True, help="run prefix, must be unique")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--submit", default=None, help="path to a verdict JSON")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    bars = OB.get_bars()
    all_days = OB.all_session_days(bars)
    D = Day(a.sess_day, a.run)

    if a.status:
        print(json.dumps({"rows": len(D.rows),
                          "fills": sum(1 for r in D.rows if r.get("row") == "fill"),
                          "exits": sum(1 for r in D.rows if r.get("row") == "exit"),
                          "pending": bool(D.pending())}, indent=1))
        return 0

    if a.submit:
        d = D.pending()
        if not d:
            print("nothing pending"); return 1
        verdict = json.loads(Path(a.submit).read_text())
        D.write({"row": d["for_role"].replace("tv-", ""),
                 "candidate_id": d.get("candidate_id"),
                 "window": d.get("window"), "minute": d.get("minute"),
                 "decision_minute": f"{a.sess_day}T{d.get('minute')} ET",
                 "briefing": d.get("briefing"),
                 "agent_model": verdict.get("_model", "sonnet"),
                 "decision": verdict.get("decision"),
                 "output": verdict})
        print(f"recorded {d['for_role']} verdict for {d.get('candidate_id') or d.get('window')}")
        return 0

    if not a.next:
        print("use --next, --submit or --status"); return 1

    if D.pending():
        print(json.dumps(D.pending(), indent=1)); return 0

    if not D.rows:
        D.write({"row": "run_header", "session_day": a.sess_day,
                 "run_prefix": a.run, "agent_versions": {
                     "tv-trigger": "0.4.9", "tv-thesis": "0.4.2",
                     "tv-manage": "0.3.2", "tv-macro-events": "0.2.0"},
                 "orchestrator": "scripts.offline_day",
                 "chart": "NONE - offline, numeric briefings only",
                 "caps": CAPS, "fill_model": "touch"})

    cands = scan_day(bars, a.sess_day)
    # candidate ids in his Mac's shape: L1/L2.. P1.. A1.. per window, in time
    seq = {"LONDON": 0, "NY_PRE": 0, "NY_AM": 0}
    for c in cands:
        seq[c["window"]] += 1
        c["cid"] = f"{c['window'][0] if c['window'] != 'NY_PRE' else 'P'}" \
                   f"{seq[c['window']]}" if c["window"] != "NY_AM" \
                   else f"A{seq[c['window']]}"
    done = D.adjudicated()
    pos = D.open_position()

    for wname, wopen, wclose, cutoff in WINDOWS:
        if D.thesis_for(wname) is None:
            b = build_thesis_briefing(bars, a.sess_day, wopen, wname,
                                      D.thesis_for("LONDON") if wname != "LONDON"
                                      else None, "", all_days)
            p = ROOT / f"output/briefings/{a.run}_{a.sess_day}_{wname}_thesis.json"
            p.write_text(json.dumps(b, indent=1))
            d = {"row": "DIRECTIVE", "for_role": "tv-thesis", "window": wname,
                 "minute": wopen, "briefing": str(p),
                 "instruction": (f"Call tv-thesis (model: sonnet) on {p}. "
                                 "Emit exactly one JSON object per contract.")}
            D.write(d)
            print(json.dumps(d, indent=1))
            return 0

        for c in cands:
            if c["window"] != wname or c["cid"] in done:
                continue
            if hm(c["minute"]) > hm(cutoff):
                continue
            prior = [x["output"]["rejected_level"]["price"]
                     for x in D.rows if x.get("row") == "trigger"
                     and str(x.get("decision", "")).startswith("take")
                     and (x.get("output") or {}).get("rejected_level")]
            b = build_trigger_briefing(
                bars, a.sess_day, c["minute"], c, D.thesis_for(wname), None,
                wname, D.fills_in(wname), CAPS[wname], pos, prior, all_days)
            p = ROOT / f"output/briefings/{a.run}_{a.sess_day}_{c['cid']}.json"
            p.write_text(json.dumps(b, indent=1))
            d = {"row": "DIRECTIVE", "for_role": "tv-trigger",
                 "candidate_id": c["cid"], "window": wname,
                 "minute": c["minute"], "briefing": str(p),
                 "instruction": (f"Call tv-trigger (model: sonnet) on {p}. "
                                 "Emit exactly one JSON object per contract.")}
            D.write(d)
            print(json.dumps(d, indent=1))
            return 0

    D.write({"row": "day_complete", "session_day": a.sess_day,
             "candidates": len(cands)})
    print(json.dumps({"row": "day_complete", "candidates": len(cands)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
