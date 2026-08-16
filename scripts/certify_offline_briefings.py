#!/usr/bin/env python3
"""CERTIFY THE OFFLINE GENERATOR AGAINST EVERY BRIEFING THE MAC EVER SERVED.

    python -m scripts.certify_offline_briefings
    python -m scripts.certify_offline_briefings --prefix v44 --verbose

For every saved briefing under output/briefings/, regenerate every
DETERMINISTIC field from committed bars with scripts/offline_briefings.py and
diff it against what the Mac orchestrator actually served the agent. The
saved corpus is the ground truth here; the generator earns trust only by
reproducing it.

Field classes, reported separately:

  exact        regenerated and identical (floats to 1e-9 after the same
               rounding the briefings use)
  MISMATCH     regenerated and different — a convention the generator has
               wrong, or a data/era difference; every one is listed
  state        position/window/cascade fields (thesis, macro, fills, caps,
               management trail) — produced by the harness at runtime, not
               regenerable from bars alone; counted, never diffed
  prose        run-specific text (leak_check, provenance, screenshot paths,
               scanner_detail wording) — the offline harness writes its own

KNOWN ERA FINGERPRINTS the report is expected to show, not hide: prefixes
that ran while the chart VWAP source was mis-measured as `open` (see
CHART_VWAP_SOURCE in src/htf_ma/levels.py) will mismatch on every VWAP field
by construction — the generator computes today's convention (hlc3). That is
history being caught, which is the certifier doing its job.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_level_behavior import behavior_at               # noqa: E402
from scripts.offline_briefings import (all_session_days,         # noqa: E402
                                       above_below, build_levels, candle,
                                       flush_inputs, get_bars,
                                       last_15m_candles, recent_2m_bars,
                                       scanner_closed)
from src.htf_ma.levels import NY                                 # noqa: E402

BRIEF_DIR = ROOT / "output/briefings"
ADVISORY: list = []          # scanner-string agreement, reported separately

STATE_FIELDS = {
    "role", "candidate_id", "window", "session", "event_trigger",
    "thesis", "prior_thesis", "macro", "position", "position_state",
    "window_state", "fills_this_window", "window_cap",
    "management_actions_so_far", "intermediate_calls_not_adjudicated",
    "reason_for_call", "level_in_question", "tp1_detail",
    "what_happened_since_the_last_read", "what_to_emit", "flip_candidate",
    "crowded_path", "nwog", "swept_lows", "swept_highs", "defended_levels",
}
PROSE_FIELDS = {
    "leak_check", "screenshot", "HOW_TO_READ_THIS_SCREENSHOT",
    "level_provenance", "levels_closed_note", "fill_model_note",
    "entry_geometry_note", "scanner_detail", "fib_source",
    "candle_start_3m", "candle_start_2m", "decision_minute",
    "levels_at_decision_CHART", "pair_shape", "signal_direction_2m_3m",
}


def parse_when(b: dict):
    """(sess_day, minute) from the briefing's own timestamps. Some eras embed
    the session-day: "2026-06-22T03:00 (session-day 2026-06-21)" — trust it."""
    dm = b.get("decision_minute", "").replace(" ET", "").strip()
    sess = None
    if "(session-day" in dm:
        dm, _, rest = dm.partition("(session-day")
        sess = rest.strip(" )")
        dm = dm.strip()
    t = pd.Timestamp(dm, tz=NY)
    if sess is None:
        sess = str((t - pd.Timedelta(hours=18)).date())
    return sess, f"{t:%H:%M}", t


def diff(path: str, saved, mine, out: list, atol: float = 1e-9):
    """Recursive exact diff; every discrepancy appends (path, saved, mine)."""
    if isinstance(saved, dict) and isinstance(mine, dict):
        for k in saved:
            if k in mine:
                diff(f"{path}.{k}", saved[k], mine[k], out, atol)
            else:
                out.append((f"{path}.{k}", saved[k], "<absent>"))
        return
    if isinstance(saved, list) and isinstance(mine, list):
        if len(saved) != len(mine):
            out.append((f"{path}.len", len(saved), len(mine)))
        for i, (s, m) in enumerate(zip(saved, mine)):
            diff(f"{path}[{i}]", s, m, out, atol)
        return
    if isinstance(saved, (int, float)) and isinstance(mine, (int, float)) \
            and not isinstance(saved, bool) and not isinstance(mine, bool):
        if not (np.isfinite(saved) and np.isfinite(mine)):
            if str(saved) != str(mine):
                out.append((path, saved, mine))
        elif abs(float(saved) - float(mine)) > atol:
            out.append((path, saved, mine))
        return
    if saved != mine:
        out.append((path, saved, mine))


def certify_one(b: dict, bars, all_days, mm: list) -> set[str]:
    """Diff one briefing; returns the set of top-level fields compared."""
    sess, minute, _ = parse_when(b)
    compared = set()

    core = build_levels(bars, sess, minute, all_days)
    if "price_at_decision" in b:
        compared.add("price_at_decision")
        diff("price_at_decision", b["price_at_decision"],
             core["price_at_decision"], mm)
    if "levels_at_decision_BUILD" in b:
        compared.add("levels_at_decision_BUILD")
        diff("levels_at_decision_BUILD", b["levels_at_decision_BUILD"],
             core["levels_at_decision_BUILD"], mm)
    if "levels_above_price" in b or "levels_below_price" in b:
        above, below = above_below(core)
        compared |= {"levels_above_price", "levels_below_price"}
        diff("levels_above_price", b.get("levels_above_price", []), above, mm)
        diff("levels_below_price", b.get("levels_below_price", []), below, mm)

    role = b.get("role", "")
    if role == "tv-trigger":
        for tf in (2, 3):
            key = f"signal_candle_{tf}m"
            if key in b and isinstance(b[key], dict):
                compared.add(key)
                _, t = None, parse_when(b)[2]
                diff(key, b[key], candle(bars, t, tf), mm)
        if isinstance(b.get("levels_closed_SCANNER"), list):
            # ADVISORY, not a defect gate: the served list is authored by the
            # Mac ORCHESTRATOR in prose-varying tag formats (own_ma_2m_and_3m,
            # _at_HH:MM suffixes appear inconsistently) and is occasionally
            # wrong on its own arithmetic — which is why the briefing carries
            # levels_closed_note telling the agent to verify and correct it.
            # The offline scanner is deterministic code; agreement is
            # reported, disagreement is not a generator failure.
            mine = scanner_closed(bars, core, sess, minute)
            saved = b["levels_closed_SCANNER"]
            ADVISORY.append((b.get("candidate_id", "?"), saved, mine))
        htf = b.get("higher_timeframe_at_candidate_levels")
        if isinstance(htf, dict):
            compared.add("higher_timeframe_at_candidate_levels")
            for name, block in htf.items():
                if not isinstance(block, dict) or "level" not in block:
                    continue
                mine = behavior_at(bars, sess, minute, float(block["level"]),
                                   window_min=block.get("window_min", 60))
                diff(f"htf.{name}", block, mine, mm)
    elif role == "tv-thesis":
        if "last_completed_2m_bar" in b:
            compared.add("last_completed_2m_bar")
            diff("last_completed_2m_bar", b["last_completed_2m_bar"],
                 candle(bars, parse_when(b)[2], 2), mm)
        if "flush_inputs" in b:
            compared.add("flush_inputs")
            fi = dict(flush_inputs(bars, sess, minute))
            fi["note"] = b["flush_inputs"].get("note")
            diff("flush_inputs", b["flush_inputs"], fi, mm)
        if "last_15m_candles" in b:
            compared.add("last_15m_candles")
            diff("last_15m_candles", b["last_15m_candles"],
                 last_15m_candles(bars, sess, minute), mm)
    elif role == "tv-manage":
        if "last_completed_2m_bar" in b:
            compared.add("last_completed_2m_bar")
            diff("last_completed_2m_bar", b["last_completed_2m_bar"],
                 candle(bars, parse_when(b)[2], 2), mm)
        if "recent_2m_bars" in b:
            compared.add("recent_2m_bars")
            diff("recent_2m_bars", b["recent_2m_bars"],
                 recent_2m_bars(bars, sess, minute), mm)
    return compared


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(BRIEF_DIR))
    ap.add_argument("--prefix", default=None,
                    help="only briefings whose filename starts with this")
    ap.add_argument("--verbose", action="store_true",
                    help="print every mismatch, not just the summary")
    a = ap.parse_args()

    files = sorted(Path(a.dir).glob("*.json"))
    if a.prefix:
        files = [f for f in files if f.name.startswith(a.prefix)]
    if not files:
        raise SystemExit("no briefing files matched")

    bars = get_bars()
    all_days = all_session_days(bars)

    per_prefix = defaultdict(lambda: {"files": 0, "fields": 0, "clean": 0,
                                      "mm": []})
    skipped = []
    for f in files:
        try:
            b = json.loads(f.read_text())
        except json.JSONDecodeError:
            skipped.append((f.name, "unparseable"))
            continue
        role = b.get("role", "")
        if role not in ("tv-trigger", "tv-thesis", "tv-manage"):
            skipped.append((f.name, f"role={role or '?'}"))
            continue
        prefix = f.name.split("_")[0]
        mm: list = []
        try:
            compared = certify_one(b, bars, all_days, mm)
        except (ValueError, KeyError) as e:
            skipped.append((f.name, f"error: {e}"))
            continue
        st = per_prefix[prefix]
        st["files"] += 1
        st["fields"] += len(compared)
        st["clean"] += len(compared) - len({p.split(".")[0].split("[")[0]
                                            for p, _, _ in mm})
        st["mm"] += [(f.name, *m) for m in mm]

    print("\n" + "=" * 78)
    print("  OFFLINE GENERATOR CERTIFICATION — regenerated vs served")
    print("=" * 78)
    total_mm = 0
    for prefix in sorted(per_prefix):
        st = per_prefix[prefix]
        total_mm += len(st["mm"])
        print(f"\n  {prefix}: {st['files']} briefings, "
              f"{st['fields']} top-level fields compared, "
              f"{st['clean']} clean ({100 * st['clean'] / max(st['fields'], 1):.1f}%), "
              f"{len(st['mm'])} leaf mismatches")
        by_path = defaultdict(list)
        for fn, p, s, m in st["mm"]:
            root = p.split(".")[0].split("[")[0]
            by_path[root].append((fn, p, s, m))
        for root in sorted(by_path):
            rows = by_path[root]
            deltas = [abs(float(s) - float(m)) for _, _, s, m in rows
                      if isinstance(s, (int, float))
                      and isinstance(m, (int, float))
                      and not isinstance(s, bool)]
            dd = f", max |Δ| {max(deltas):.2f}" if deltas else ""
            print(f"      {root:<38} {len(rows):>4} mismatches{dd}")
            if a.verbose:
                for fn, p, s, m in rows[:12]:
                    print(f"        {fn}  {p}\n"
                          f"          served: {s!r}\n"
                          f"          mine:   {m!r}")
                if len(rows) > 12:
                    print(f"        ... {len(rows) - 12} more")
    if ADVISORY:
        same = sum(1 for _, s, m in ADVISORY if s == m)
        print(f"\n  levels_closed_SCANNER (advisory — Mac strings are "
              f"orchestrator-authored): {same}/{len(ADVISORY)} identical")
        if a.verbose:
            for cid, s, m in ADVISORY:
                if s != m:
                    print(f"      {cid}\n        served: {s}\n        mine:   {m}")
    if skipped:
        print(f"\n  skipped {len(skipped)}: "
              + ", ".join(f"{n} ({r})" for n, r in skipped[:8])
              + (" ..." if len(skipped) > 8 else ""))
    print(f"\n  TOTAL leaf mismatches: {total_mm}")
    print("  state/cascade and prose fields are not diffed by design —"
          " the harness owns them.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
