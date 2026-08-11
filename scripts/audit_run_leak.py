#!/usr/bin/env python3
"""LEAK AUDIT — prove a replay run could not see the future. Adversarial by design.

    python -m scripts.audit_run_leak output/agent_runs/2026-06-25.jsonl

Assume the run is dirty and try to prove it. Every check below either finds
evidence of foreknowledge or exits clean, and "clean" is only as strong as
the checks — so each one states what it can and cannot rule out.

Exit 0 = no leak evidence found. Exit 1 = evidence found (details printed).

WHY THIS EXISTS. Agent decisions in this stack are worthless if the chart or
the briefing carried bars after the decision minute, and the error is
invisible in aggregate (AGENT-OPERATING-SPEC Phase 0.4). Self-reported
"leak_check: pass" rows are the orchestrator grading its own homework, so
this re-derives the answer from the committed bars instead.

THE CHECKS

  A  every decision row carries an explicit passing leak_check
  B  decision minutes are non-decreasing (no back-dated adjudications)
  C  no briefing file mentions a clock time later than its own decision
     minute (catches future bars pasted into a payload)
  D  no briefing file carries narrated-corpus markers (trader_time, his
     result/R fields) — i.e. nobody handed the agents the answer key
  E  every entry / stop / target price must be explicable at its minute,
     either as a structural level computable AS OF then (VWAP bands, BB
     MAs 2/3/15/60, developing daily profile, anchored weekly profile,
     prior-day levels) or as a price already printed that session.

E'S REAL SCOPE — measured, not assumed. A planted target at the day's true
high (29,665.25, which prints at 10:20) inserted into an 03:18 decision does
NOT trip E, because that price already sat inside the printed range by
03:18. E catches only a number that is BOTH away from every as-of level AND
outside everything price has traded — i.e. genuine clairvoyance about a new
extreme. Level density at a typical minute is 30 levels / ~26pt median gap,
covering ~18% of the range at 6pt tolerance, so E is a real filter, not a
rubber stamp — but it is the weakest of the five, not the strongest.

The load-bearing guarantees are structural, not statistical:
  1. replay truncates the chart at the decision minute (re-verified every
     step; check A confirms it was run and logged);
  2. `.claude/settings.json` DENIES the Read tool on data/narrated_days/**
     and docs/CORPUS-narrated-days.md, so no agent can open the answer key
     even if its prompt were ignored;
  3. checks C and D prove no future timestamp or corpus marker reached a
     briefing.

WHAT THIS CANNOT PROVE. It cannot see a model's private reasoning, and it
cannot rule out an agent having been *told* the future in prose that never
reached the log. It also cannot fix IN-SAMPLE contamination: on the narrated
week the agents' own prompt doctrine was distilled from those five days, so
a clean audit there means "no lookahead", NOT "out of sample". The
out-of-sample claim requires post-corpus days (bars run to 2026-07-15).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase0_parity import load_bars_indexed, reference_at
from src.htf_ma.levels import NY

PRICE_TOL = 6.0        # pts; a limit is placed a few points inside a level
# NOT \b-anchored: an ISO stamp writes the time as "...T03:18", and \b fails
# between two word chars ("T" then "0"), so a \b regex silently skips the real
# time and matches a later one ("18:00 NY anchor") — which reads as a leak.
HHMM = re.compile(r"(?<![\d:])([01]?\d|2[0-3]):([0-5]\d)(?!:?\d)")
CORPUS_MARKERS = ("trader_time", "trader_label", "his_words", "the_wait",
                  "result_r", "day_pnl_r", "narrated", "declared_rules")

# Clock times that are DOCTRINE CONSTANTS, not observations: window bounds,
# the session anchor, the fib-validity threshold, and the standard red-folder
# release slot. A briefing states them at every decision minute, and they are
# knowable a week in advance — flagging them as lookahead is a false positive.
# Deliberately narrow: any OTHER future time still trips check C. Scheduled
# news times from the as-of calendar are likewise legitimate by construction.
KNOWN_CONSTANTS = {"03:00", "04:59", "08:00", "08:30", "09:29", "09:30",
                   "10:00", "11:00", "17:00", "18:00"}
PRICE_FIELDS = ("entry", "stop", "limit_price", "retest_price")


def _mins(s: str) -> int | None:
    """Minutes since the 18:00 NY session anchor, so an 18:00-anchored day
    orders correctly: 19:25 (evening) is EARLIER than 03:00 (next morning).
    Comparing raw clock minutes here is a bug that manufactures fake leaks."""
    m = HHMM.search(str(s))
    if not m:
        return None
    clock = int(m.group(1)) * 60 + int(m.group(2))
    return clock - 1080 if clock >= 1080 else clock + 360


def _payload(r: dict) -> dict:
    """Decision fields may sit at the row top level or nested under `output`."""
    out = dict(r)
    if isinstance(r.get("output"), dict):
        out.update(r["output"])
    return out


def _agentless(r: dict) -> bool:
    """Orchestrator-mechanical passes (window_cap, stand_aside, precedent)
    spawn no agent and read no chart — there is no chart-read to leak."""
    return str(r.get("agent_spawn", "")).strip().lower().startswith("none")


def _decision_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if "decision" in _payload(r) and r.get("decision_minute")]


def check_a(rows, out):
    dec = _decision_rows(rows)
    bad = []
    for r in dec:
        if _agentless(r):
            continue                      # no chart consulted, nothing to leak
        lc = str(r.get("leak_check", "")).strip().lower()
        if not (lc.startswith("pass") or lc.startswith("ok") or lc == "true"):
            bad.append(r)
    if bad:
        out.append(("A", f"{len(bad)} agent-adjudicated rows without a passing "
                         f"leak_check: "
                         + ", ".join(str(r.get("candidate_id", r.get("decision_minute")))
                                     for r in bad[:6])))
    return len(dec), sum(1 for r in dec if _agentless(r))


def check_b(rows, out):
    ts = [(_mins(r["decision_minute"]), r.get("candidate_id", "?"))
          for r in _decision_rows(rows)]
    ts = [(t, i) for t, i in ts if t is not None]
    # session-day wraps past midnight; allow one wrap
    wraps = sum(1 for k in range(1, len(ts)) if ts[k][0] < ts[k - 1][0])
    if wraps > 1:
        out.append(("B", f"decision minutes go backwards {wraps} times "
                         f"(>1 wrap is back-dating, not a session rollover)"))


def check_cd(brief_dir: Path, out):
    n = 0
    for f in sorted(brief_dir.glob("*.json")):
        n += 1
        raw = f.read_text()
        stem_t = _mins(f.stem.split("_")[1]) if "_" in f.stem else None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            out.append(("C", f"{f.name}: unparseable"))
            continue
        dm = _mins(payload.get("decision_minute", ""))
        if dm is None:
            dm = _mins(stem_t) if isinstance(stem_t, str) else stem_t
        if dm is not None:
            # session-relative minutes on both sides (see _mins)
            seen = {(int(a) * 60 + int(b)) for a, b in HHMM.findall(raw)
                    if f"{int(a):02d}:{b}" not in KNOWN_CONSTANTS}
            late = sorted({(c - 1080 if c >= 1080 else c + 360) for c in seen})
            late = [m for m in late if m > dm]
            if late:
                shown = ", ".join(
                    f"{((m + 1080) % 1440) // 60:02d}:{((m + 1080) % 1440) % 60:02d}"
                    for m in late[:6])
                out.append(("C", f"{f.name}: mentions {len(late)} time(s) after its "
                                 f"decision minute -> {shown}"))
        hits = [k for k in CORPUS_MARKERS if k in raw]
        if hits:
            out.append(("D", f"{f.name}: corpus answer-key markers present: {hits}"))
    return n


def check_e(rows, sess_day, bars, out, by_level=None):
    """Every quoted price must match a level computable as-of its minute."""
    checked = unexplained = 0
    if by_level is None:
        by_level = [0, 0]
    for r in _decision_rows(rows):
        dm = str(r["decision_minute"])
        m = HHMM.search(dm)
        if not m:
            continue
        hhmm = f"{m.group(1)}:{m.group(2)}"
        try:
            ref = reference_at(bars, sess_day, hhmm)
        except SystemExit:
            continue
        levels = {k: v for k, v in ref.items()
                  if isinstance(v, (int, float)) and np.isfinite(v)}
        # prices already printed this session-day, up to the decision minute
        t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0) & (bars.index <= ref["decision_minute"])]
        lo, hi = (float(seg.low.min()), float(seg.high.max())) if len(seg) else (np.nan, np.nan)

        pay = _payload(r)
        quoted = []
        for f in PRICE_FIELDS:
            v = pay.get(f)
            if isinstance(v, (int, float)) and v:
                quoted.append((f, float(v)))
        for tgt in (pay.get("targets") or []):
            v = tgt.get("price") if isinstance(tgt, dict) else tgt
            if isinstance(v, (int, float)) and v:
                quoted.append(("target", float(v)))
        cir = pay.get("cancel_if_reaches")
        if isinstance(cir, dict) and isinstance(cir.get("price"), (int, float)):
            quoted.append(("cancel_if_reaches", float(cir["price"])))

        for field, px in quoted:
            checked += 1
            near = min((abs(px - v), k) for k, v in levels.items()) if levels else (1e9, "")
            printed = np.isfinite(lo) and (lo - PRICE_TOL) <= px <= (hi + PRICE_TOL)
            if near[0] <= PRICE_TOL:
                by_level[0] += 1
                continue
            if printed:
                by_level[1] += 1        # in-range: knowable, but weak evidence
                continue
            unexplained += 1
            out.append(("E", f"{r.get('candidate_id', hhmm)} {field}={px:.2f}: matches no "
                             f"as-of level (nearest {near[1]} {near[0]:.1f}pt) and outside "
                             f"the printed range {lo:.2f}-{hi:.2f}"))
    return checked, unexplained


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_jsonl")
    p.add_argument("--sess-day", default=None)
    p.add_argument("--briefings", default=None)
    a = p.parse_args()

    run = Path(a.run_jsonl)
    sess_day = a.sess_day or run.stem
    brief_dir = Path(a.briefings) if a.briefings else run.parent / "briefings"
    rows = [json.loads(l) for l in run.read_text().splitlines() if l.strip()]

    findings: list[tuple[str, str]] = []
    n_dec, n_mech = check_a(rows, findings)
    check_b(rows, findings)
    n_brief = check_cd(brief_dir, findings) if brief_dir.is_dir() else 0
    bars = load_bars_indexed()
    by_level = [0, 0]
    n_px, n_bad = check_e(rows, sess_day, bars, findings, by_level)

    print(f"\nLEAK AUDIT — {run.name}  (session-day {sess_day})")
    print(f"  {n_dec} decision rows ({n_dec - n_mech} agent-adjudicated, {n_mech} "
          f"orchestrator-mechanical) · {n_brief} briefings · {n_px} quoted prices\n")

    if not findings:
        print("  A  leak_check passing on every agent-adjudicated row         OK")
        print("  B  decision minutes chronological                            OK")
        print("  C  no briefing mentions a time after its decision minute     OK")
        print("  D  no narrated-corpus answer-key markers in briefings        OK")
        print(f"  E  all {n_px} quoted prices explicable as-of their minute        OK")
        print(f"       ({by_level[0]} matched an as-of level, {by_level[1]} were inside the\n        printed range — the latter is weak evidence; see E'S REAL SCOPE)")
        print("\n  NO LEAK EVIDENCE FOUND.")
        print("  Scope: this rules out lookahead. It does NOT establish out-of-sample —")
        print("  on the narrated week the prompt doctrine was distilled from those days.")
        print("  Out-of-sample requires post-corpus days (bars run to 2026-07-15).\n")
        return 0

    by = {}
    for code, msg in findings:
        by.setdefault(code, []).append(msg)
    for code in sorted(by):
        print(f"  [{code}] {len(by[code])} finding(s):")
        for msg in by[code][:12]:
            print(f"       - {msg}")
        if len(by[code]) > 12:
            print(f"       … {len(by[code]) - 12} more")
        print()
    print("  LEAK EVIDENCE FOUND — do not score this run until each item is "
          "explained or the run is redone.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
