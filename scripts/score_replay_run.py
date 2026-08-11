#!/usr/bin/env python3
"""AGREEMENT SCORER v0 — one replay run against the trader's recorded day.

    python -m scripts.score_replay_run output/agent_runs/2026-06-25.jsonl

Reads the run JSONL the orchestrator writes (docs/RUNBOOK-replay-scoring.md
Phase R3) and the matching data/narrated_days/<file>.json, and prints:

  1. per-window counts, his vs the agent's (TAKE / PASS / NO_FILL);
  2. a best-effort side-by-side row match (same window, +/-15 min) for the
     teaching loop — every disagreement is a question to put to him;
  3. the PLAYBOOK §7 guard when the day contains one of the two decisions a
     naive scorer marks wrong.

v0 is deliberately window-level + best-effort. The narrated files carry
heterogeneous free-text times ("09:04 London / 04:04 NY", "08:42 London",
ranges, or nothing), so exact row matching cannot be assumed; unmatched rows
are LISTED, never silently dropped. This is a report, not a gate — exit 0.

The outcome axis (in-window P(2R) vs same-day baseline) is NOT here; it needs
stable agreement runs first and a widened sample to mean anything (his own 20
matched picks clear the bar only at p ~= 0.07).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATED = ROOT / "data/narrated_days"
LONDON_MINUS_NY_H = 5          # his labels: "09:04 London / 04:04 NY"
MATCH_TOL_MIN = 15
WINDOWS = ("LONDON", "NY_PRE", "NY_AM")

# PLAYBOOK §7 — the two decisions that look like errors and are not.
GUARDS = {
    "2026-06-24": ("PRE1 break-even before the open: the market then fell 897pt "
                   "and 29.2R was available had he held. HIS CALL WAS CORRECT "
                   "('that's straight gambling for me'). Do not score it as a miss."),
    "2026-06-25": ("the refusal to limit a nearer level for a tighter fill "
                   "('I'm sticking to my fucking rules'). A rule that pays out "
                   "over a year is not refuted by the day it costs the most."),
}

HHMM = re.compile(r"(\d{1,2}):(\d{2})")


def _to_min(h: int, m: int) -> int:
    return h * 60 + m


def his_time_ny(dec: dict) -> int | None:
    """Best-effort NY minute-of-day from the heterogeneous narrated fields."""
    t = dec.get("trader_time") or ""
    if "-" in t:                                   # a range: window-level only
        return None
    toks = HHMM.findall(t)
    if toks:
        if "/" in t and "NY" in t:                 # "09:04 London / 04:04 NY"
            h, m = toks[-1]
            return _to_min(int(h), int(m))
        if "London" in t and "NY" not in t:        # "08:42 London"
            h, m = toks[0]
            return (_to_min(int(h), int(m)) - LONDON_MINUS_NY_H * 60) % 1440
        h, m = toks[0]                             # "09:42 NY"
        return _to_min(int(h), int(m))
    fill = (dec.get("entry") or {}).get("fill_ny") or ""
    toks = HHMM.findall(str(fill))
    if toks:
        h, m = toks[0]
        return _to_min(int(h), int(m))
    return None


def agent_time_ny(row: dict) -> int | None:
    for k in ("decision_minute", "candle_start", "t"):
        v = row.get(k)
        if not v:
            continue
        toks = HHMM.findall(str(v))
        if toks:
            h, m = toks[-1]
            return _to_min(int(h), int(m))
    return None


def norm_his(dec: dict) -> str:
    t = dec.get("type", "")
    if t == "take":
        return "TAKE"
    if t == "pass":
        return "PASS"
    if "never_filled" in t or "no_fill" in t:
        return "NO_FILL"
    return t.upper() or "?"


def norm_agent(row: dict) -> str:
    if str(row.get("outcome", "")).startswith("no_fill"):
        return "NO_FILL"
    d = str(row.get("decision", ""))
    if d.startswith("take"):
        return "TAKE"
    if d == "pass":
        return "PASS"
    return d.upper() or "?"


def load_narrated(sess_day: str) -> dict:
    for f in sorted(NARRATED.glob("*.json")):
        d = json.loads(f.read_text())
        if d.get("session_day") == sess_day:
            return d
    raise SystemExit(f"no narrated day with session_day={sess_day} under "
                     f"{NARRATED} — agreement needs ground truth; for a "
                     f"non-narrated day only the outcome axis applies")


def load_run(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"  !! line {i} unparseable, skipped: {e}", file=sys.stderr)
    # candidate adjudications are the rows carrying a decision
    return [r for r in rows if "decision" in r]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_jsonl", help="output/agent_runs/<sess_day>.jsonl")
    p.add_argument("--sess-day", default=None,
                   help="override; default = the file's stem")
    a = p.parse_args()

    run_path = Path(a.run_jsonl)
    sess_day = a.sess_day or run_path.stem
    his_day = load_narrated(sess_day)
    agent = load_run(run_path)
    his = his_day.get("decisions", [])

    print(f"\nAGREEMENT v0 — session-day {sess_day} "
          f"({his_day.get('trader_label', '?')})")
    print(f"  his rows: {len(his)}   agent candidate rows: {len(agent)}\n")

    print(f"  {'window':<8} {'his T/P/NF':>12} {'agent T/P/NF':>14}")
    for w in WINDOWS:
        hw = [norm_his(d) for d in his if d.get("window") == w]
        aw = [norm_agent(r) for r in agent if r.get("window") == w]
        fmt = lambda xs: "/".join(str(xs.count(k))
                                  for k in ("TAKE", "PASS", "NO_FILL"))
        print(f"  {w:<8} {fmt(hw):>12} {fmt(aw):>14}")

    # -- best-effort row matching, greedy by time distance within a window
    print(f"\n  side-by-side (same window, ±{MATCH_TOL_MIN} min, best-effort):")
    used: set[int] = set()
    n_match = n_agree = 0
    for d in his:
        w, ht = d.get("window"), his_time_ny(d)
        label = (f"his {d.get('id', '?'):<5} {norm_his(d):<8} "
                 f"{d.get('direction', '?'):<6}")
        best, best_dt = None, MATCH_TOL_MIN + 1
        if ht is not None:
            for i, r in enumerate(agent):
                if i in used or r.get("window") != w:
                    continue
                at = agent_time_ny(r)
                if at is None:
                    continue
                dt = abs(at - ht)
                if dt < best_dt:
                    best, best_dt = i, dt
        if best is None:
            print(f"    {w or '?':<8} {label} <-> (no agent row matched)")
            continue
        used.add(best)
        r = agent[best]
        n_match += 1
        same = norm_his(d) == norm_agent(r)
        n_agree += int(same)
        print(f"    {w or '?':<8} {label} <-> agent {r.get('decision', '?'):<10}"
              f" {r.get('direction', '?'):<6} Δ{best_dt}m "
              f"{'AGREE' if same else 'DISAGREE'}")
    for i, r in enumerate(agent):
        if i not in used:
            print(f"    {r.get('window', '?'):<8} (no his row)          <-> "
                  f"agent {r.get('decision', '?'):<10} "
                  f"{r.get('direction', '?'):<6} "
                  f"reason: {str(r.get('reason', ''))[:60]}")

    if n_match:
        print(f"\n  matched {n_match}, agreed {n_agree} "
              f"({100 * n_agree // n_match}% of matched)")
    print("  every unmatched or disagreeing row above is a question for him — "
          "that is the teaching loop, not a defect in the report.")

    if sess_day in GUARDS:
        print(f"\n  ⚠ PLAYBOOK §7 GUARD — this day contains {GUARDS[sess_day]}")

    print("\n  v0 scores agreement only. High agreement whose picks don't run "
          "is cosmetic —\n  the outcome axis comes once agreement runs are "
          "stable.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
