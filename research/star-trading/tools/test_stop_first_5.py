#!/usr/bin/env python3
"""ITEM 5 — STOP-FIRST ACCOUNTING, MOVED INTO 2a.

Was invariant 7 in invariants_2b.py, reported NOT TESTABLE there because attributing an
exit on the real trade list is outcome information (Part 0 rule 6). Testable here with
no outcome data at all: synthetic bars whose stop and target prices are both chosen by
this file, resolved by spec_current.resolve_bar_stop_first(), a faithful transcription
of accounting rule 4.1 — quoted below — extracted from stage2_smoke.run_session's
inline logic.

  4.1  "ambiguous bars resolve STOP-FIRST"  (PREREGISTRATION.md, quoted in
        stage2_smoke.py's own docstring)

EVERY expected value below was written from that clause plus the touch convention
already established elsewhere in the spec (§7 invalidation and over-extension both use
inclusive touch, "th_ >= nmid + nsig" / "touch of NY VWAP ±2σ"), BEFORE the function was
run against any case. No outcome is computed anywhere in this file — a resolution of
"stop" or "target" against a hand-built synthetic bar is a unit test of a rule, not a
report on the real trade list, and no dollar amount, R multiple, or win/loss is ever
produced.

Two-commit protocol: this file and resolve_bar_stop_first() are committed together as
literal transcriptions of an existing, already-implemented rule (not a hypothesis under
test); the run is the second commit.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import json
from pathlib import Path

RESULTS = []


def check(tid, clause, expected, actual):
    ok = expected == actual
    RESULTS.append((tid, clause, repr(expected), repr(actual), "PASS" if ok else "FAIL"))
    return ok


def group_stop_first(resolve):
    # SF1 [LIT] long, bar touches ONLY the stop.
    check("SF1", '4.1, long, stop only', "stop",
          resolve("long", 95.0, 110.0, 100.0, 101.0, 94.0, 100.5))

    # SF2 [LIT] long, bar touches ONLY the target.
    check("SF2", '4.1, long, target only', "target",
          resolve("long", 95.0, 110.0, 100.0, 111.0, 99.0, 108.0))

    # SF3 [LIT] long, bar touches NEITHER.
    check("SF3", '4.1, long, neither touched', None,
          resolve("long", 95.0, 110.0, 100.0, 102.0, 98.0, 101.0))

    # SF4 [LIT] THE CASE THIS ITEM EXISTS FOR — long, one bar's range spans BOTH the
    # stop and the target (a large range or a gap). Clause says STOP-FIRST: the
    # ambiguity must resolve to "stop", never "target".
    check("SF4", '4.1 "ambiguous bars resolve STOP-FIRST", long, both touched',
          "stop", resolve("long", 95.0, 110.0, 100.0, 112.0, 93.0, 105.0))

    # SF5 [LIT] mirror of SF1: short, stop only.
    check("SF5", '4.1, short, stop only', "stop",
          resolve("short", 110.0, 95.0, 100.0, 110.5, 99.0, 100.0))

    # SF6 [LIT] mirror of SF2: short, target only.
    check("SF6", '4.1, short, target only', "target",
          resolve("short", 110.0, 95.0, 100.0, 101.0, 94.0, 96.0))

    # SF7 [LIT] mirror of SF3: short, neither.
    check("SF7", '4.1, short, neither touched', None,
          resolve("short", 110.0, 95.0, 100.0, 102.0, 98.0, 100.0))

    # SF8 [LIT] mirror of SF4 — short, both touched, must resolve to stop.
    check("SF8", '4.1 STOP-FIRST, short, both touched', "stop",
          resolve("short", 110.0, 95.0, 100.0, 112.0, 93.0, 102.0))

    # SF9 [LIT] EXACT-TOUCH BOUNDARY, long stop. The spec's touch convention elsewhere
    # (§7 "th_ >= nmid + nsig") is inclusive, so a low landing EXACTLY on the stop
    # price counts as a hit, not a near-miss.
    check("SF9", 'touch convention, inclusive, long stop exact', "stop",
          resolve("long", 95.0, 110.0, 100.0, 101.0, 95.0, 100.5))

    # SF10 [LIT] exact-touch boundary, long target.
    check("SF10", 'touch convention, inclusive, long target exact', "target",
          resolve("long", 95.0, 110.0, 100.0, 110.0, 99.0, 108.0))

    # SF11 [LIT] exact-touch boundary, short stop.
    check("SF11", 'touch convention, inclusive, short stop exact', "stop",
          resolve("short", 110.0, 95.0, 100.0, 110.0, 99.0, 100.0))

    # SF12 [LIT] exact-touch boundary, short target.
    check("SF12", 'touch convention, inclusive, short target exact', "target",
          resolve("short", 110.0, 95.0, 100.0, 101.0, 95.0, 96.0))

    # SF13 [LIT] the boundary case that makes SF4/SF8 non-trivial: a bar that touches
    # the stop and the target at EXACTLY their levels simultaneously (the widest
    # possible ambiguous bar). STOP-FIRST must still win.
    check("SF13", '4.1 STOP-FIRST, long, both touched exactly', "stop",
          resolve("long", 95.0, 110.0, 100.0, 110.0, 95.0, 105.0))
    check("SF14", '4.1 STOP-FIRST, short, both touched exactly', "stop",
          resolve("short", 110.0, 95.0, 100.0, 110.0, 95.0, 100.0))

    # SF15 [LIT] a doji-like zero-range bar sitting exactly on neither level touches
    # neither — resolution is None, not a crash.
    check("SF15", '4.1, degenerate zero-range bar, no touch', None,
          resolve("long", 95.0, 110.0, 100.0, 101.0, 101.0, 101.0))


def main():
    from spec_current import resolve_bar_stop_first
    group_stop_first(resolve_bar_stop_first)

    npass = sum(1 for r in RESULTS if r[4] == "PASS")
    nfail = len(RESULTS) - npass
    print("=" * 92)
    print("ITEM 5 — STOP-FIRST ACCOUNTING (was invariant 7, NOT TESTABLE, in 2b)")
    print("=" * 92)
    print(f"{'id':<6} {'status':<6} {'clause':<52} expected -> actual")
    for tid, clause, exp, act, st in RESULTS:
        mark = "" if st == "PASS" else "  <<<<"
        print(f"{tid:<6} {st:<6} {clause[:52]:<52} {exp} -> {act}{mark}")
    print(f"\n  tests run {len(RESULTS)}   PASS {npass}   FAIL {nfail}")
    Path(__file__).with_name("test_stop_first_5_result.json").write_text(
        json.dumps({"pass": npass, "fail": nfail, "results": RESULTS}, indent=1,
                   sort_keys=True))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
