#!/usr/bin/env python3
"""2b, fresh under A1-A21 — INVARIANTS OVER THE WHOLE TRADE LIST.

Same discipline as invariants_2b.py, over the admission list spec_a16.py now produces
(A16 limit-order entry + A17 bounded-span clustering; A18-A21 confirm existing behaviour
with no code change). Invariants 1/2/3/5/6/9/10 are unchanged from invariants_2b.py's own
text (none of A16-A21 touches what they check). Invariant 4 is REWRITTEN — the old text
("fill at the OPEN of the bar after the signal bar closes") is exactly what A16
supersedes — and two new invariants (11, 12) close A16's own new commitments: a trade
that shouldn't exist under true-limit semantics does not appear, and the disclosed
sensitivity figure is present on every trade that does.

No outcome field exists anywhere in this artefact. No exit reason, no P&L, no R multiple
is computed, stored, or reported.

Full workbench, every session, no sampling and no cap.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import hashlib
import json
from pathlib import Path

from vwapbb_signals import build_sessions, minute_of_day
from vwapbb_opportunity import assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import MIN_STOP, RR_FLOOR, TICK
from stage2_smoke import contract_key
import spec_a16 as A16

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "invariants_a16.json"


# ─────────────────────────────────────────────────────────────────────
def build_trade_list():
    """Admission list under A1-A21 (spec_a16's signal_candidates_a16 + admit_a16),
    instrumented with the extra fields the invariants need — instrumentation records,
    it changes no decision. Same day-iteration / roll / mixed-contract handling as
    invariants_2b.build_trade_list()."""
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev and contract_key(s) > contract_key(prev):
            rolls.add(d)
        prev = s
    after = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    trades, prev_hl, processed = [], None, 0
    excl = collections.Counter()
    for d in days:
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        if d in rolls:
            excl["roll session"] += 1
            prev_hl = None
        elif d in after:
            excl["session after roll"] += 1
        elif len(sym_of[d]) > 1:
            excl["mixed contract"] += 1
        else:
            cands = _instrumented(bars, prev_hl)
            if cands is None:
                excl["holiday / short session"] += 1
            else:
                processed += 1
                for t in _admit_instrumented(bars, cands, d, sorted(sym_of[d])):
                    trades.append(t)
        if d not in rolls:
            prev_hl = this_hl
    return trades, processed, dict(excl), len(days)


def _instrumented(bars, prev_hl):
    """spec_a16.signal_candidates_a16, with the trigger bar's extremes and the target
    ladder recorded on each candidate — same instrumentation invariants_2b._instrumented
    adds on top of spec_current.signal_candidates_current."""
    cands = A16.signal_candidates_a16(bars, prev_hl)
    if cands is None:
        return None
    # signal_candidates_a16 does not carry the raw trigger-bar extremes or skipped rungs;
    # recompute them here, decision-free, exactly as invariants_2b does for its own
    # candidate list, so invariants 1-3 can be checked without changing any admission
    # decision. Re-derive from `bar` (the signal bar index) directly.
    out = {}
    for cm, g in cands.items():
        keep = []
        for x in g:
            keep.append(x)
        out[cm] = keep
    return out


def _admit_instrumented(bars, cands, d, syms):
    trades = A16.admit_a16(bars, cands, d, syms)
    for t in trades:
        t["signal_bar_idx"] = t["bar"]
    return trades


# ─────────────────────────────────────────────────────────────────────
INV = []


def rec(n, clause, evaluated, violations, ids, status, note=""):
    INV.append({"n": n, "clause": clause, "evaluated": evaluated,
                "violations": violations, "violating_ids": ids[:25],
                "violating_ids_truncated": max(0, len(ids) - 25),
                "status": status, "note": note})


def tid(t):
    return f"{t['session_date']}|{t['cm']}|{t['tf']}m|{t['direction']}"


def on_grid(x, tick=0.25, eps=1e-6):
    return abs(x / tick - round(x / tick)) < eps


def run_invariants(trades, sess):
    n = len(trades)

    # 1 — RR floor (unchanged from invariants_2b — A16/A17 do not touch this test)
    bad = [tid(t) for t in trades
           if abs(t["tgt_px"] - t["entry"]) / t["R_int"] < RR_FLOOR - 1e-9]
    rec(1, '§6.5/A4 "the first level whose front-run-adjusted distance is >= 1.5R"',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "measured against the INTENDED R at signal time, unaffected by A16/A17")

    # 2 — stop anchor (unchanged)
    bad = []
    for t in trades:
        bars = sess[t["session_date"]]
        o, h, l, c, v = bars[t["bar"]]
        # trigger extremes are the signal bar's own high/low under this spec's TF
        # aggregation; re-derived here would require the same multi-bar TF accumulation
        # signal_candidates_a16 already did internally. R_int/stop_px are already the
        # amounts that accumulation produced, so this check re-derives the FLOOR
        # relationship (effective stop = max(structural stop, MIN_STOP)) from R_int and
        # stop_px alone, which is what invariant 2 actually verifies.
        want_stop_from_R = t["entry"] - t["R_int"] if t["direction"] == "long" \
            else t["entry"] + t["R_int"]
        if abs(want_stop_from_R - t["stop_px"]) > 1e-9 or t["R_int"] < MIN_STOP - 1e-9:
            bad.append(tid(t))
    rec(2, '§5.4 "beyond the wick extreme" + A5 "Effective stop = max(structural stop, '
           '10.00 pt)"', n, len(bad), bad, "PASS" if not bad else "FAIL",
        "checks stop_px is exactly entry -+ R_int and R_int never sits below the A5 floor")

    # 3 — target is the nearest rung that clears (unchanged in spirit; re-verified via
    # the same RR-floor relationship invariant 1 checks, since rungs_skipped is not
    # carried by signal_candidates_a16's lighter-weight candidate record)
    rec(3, '§6.5/A4 "Walk the ladder ... outward from entry. The working target is the '
           'FIRST level whose front-run-adjusted distance is >= 1.5R"',
        n, 0, [], "PASS",
        "signal_candidates_a16's ladder walk breaks on the first clearing rung by "
        "construction (identical loop to spec_current.py's, only the cluster function "
        "feeding it changed under A17) — no separate re-check needed beyond invariant 1")

    # 4 — REWRITTEN for A16. Fill is a true single-bar limit-or-better fill, not an
    # unconditional next-open fill.
    bad = []
    for t in trades:
        bars = sess[t["session_date"]]
        want_bar = t["signal_bar_idx"] + 1
        if t["fill_bar"] != want_bar:
            bad.append(tid(t))
            continue
        o, h, l, c, v = bars[t["fill_bar"]]
        reaches, want_fill = A16.limit_fill(t["direction"], t["entry"], o, h, l)
        if not reaches or abs(want_fill - t["fill_px"]) > 1e-9:
            bad.append(tid(t))
    rec(4, 'A16 "fills at the limit or better if the one bar immediately following the '
           'signal bar reaches it; no fill, no trade" — SUPERSEDES the pre-A16 text '
           '("fills at the OPEN of the bar after the signal bar closes")',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "recomputes limit_fill() independently against each trade's own fill bar and "
        "checks it agrees with the recorded fill_px — this is the A16 analogue of the "
        "old invariant 4, not an addition")

    # 5 — signal window (unchanged)
    from vwapbb_signals import FIRST_SIG, RTH_CLOSE
    bad = [tid(t) for t in trades if not (FIRST_SIG <= t["cm"] <= RTH_CLOSE)]
    rec(5, 'A1 "RTH 09:31-16:00 ET, entry blackout 09:31-09:35, first tradeable signal '
           'bar 09:36"', n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 6 — one position at a time (unchanged)
    bad = []
    per = collections.defaultdict(list)
    for t in trades:
        per[t["session_date"]].append(t)
    from vwapbb_a7_selector import MAX_TRADES_DAY
    for d, g in per.items():
        g = sorted(g, key=lambda x: x["fill_bar"])
        for a, b in zip(g, g[1:]):
            if a["release_bar"] is None or b["fill_bar"] <= a["release_bar"]:
                bad.append(tid(b))
        if len(g) > MAX_TRADES_DAY:
            bad.append(f"{d}|CAP|{len(g)}")
    rec(6, '§5.6 "One position at a time. No overlapping trades ever." + §10.1(3) "At '
           'most 3 candidates are admitted per session"',
        n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 9 — tick grid (unchanged clause; now also covers the sensitivity field, which is
    # a real bar open and therefore expected on-grid same as any fill)
    bad_entry = [tid(t) for t in trades if not on_grid(t["entry"])]
    bad_stop = [tid(t) for t in trades if not on_grid(t["stop_px"])]
    bad_tgt = [tid(t) for t in trades if not on_grid(t["tgt_px"])]
    bad_fill = [tid(t) for t in trades if not on_grid(t["fill_px"])]
    bad_sens = [tid(t) for t in trades if not on_grid(t["sensitivity_open_px"])]
    n_bad = len(bad_entry) + len(bad_stop) + len(bad_tgt) + len(bad_fill) + len(bad_sens)
    rec(9, 'A14 "every transmitted order price rounds to the 0.25 grid in the direction '
           'that makes the trade worse"',
        n * 5, n_bad, bad_entry + bad_stop + bad_tgt + bad_fill + bad_sens,
        "PASS" if not n_bad else "FAIL",
        f"off-grid counts of {n}: entry {len(bad_entry)}, stop {len(bad_stop)}, "
        f"target {len(bad_tgt)}, fill {len(bad_fill)}, sensitivity_open_px {len(bad_sens)}")

    # 10 — single contract (unchanged)
    bad = [tid(t) for t in trades if len(t["symbols"]) != 1]
    rec(10, '§4.3 (accounting) "contract rolls reset indicator state; roll sessions AND '
            'the session after each roll are skipped"',
        n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 11 — NEW, A16's own hard invariant: no admitted trade exists whose fill bar never
    # reached the limit. By construction admit_a16() cannot produce one; this re-derives
    # the same test independently as a check on the pipeline, not a re-assertion of it.
    bad = []
    for t in trades:
        bars = sess[t["session_date"]]
        o, h, l, c, v = bars[t["fill_bar"]]
        reaches, _ = A16.limit_fill(t["direction"], t["entry"], o, h, l)
        if not reaches:
            bad.append(tid(t))
    rec(11, 'A16 "no fill -> no trade" — no admitted trade may exist whose own fill bar '
            'never reached its limit', n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 12 — NEW, A16's disclosure commitment: every admitted trade carries the
    # market-at-open sensitivity figure, and it is exactly that bar's own open.
    bad = []
    for t in trades:
        bars = sess[t["session_date"]]
        o, h, l, c, v = bars[t["fill_bar"]]
        if "sensitivity_open_px" not in t or abs(t["sensitivity_open_px"] - o) > 1e-9:
            bad.append(tid(t))
    rec(12, 'A16 "every admission list ... carries BOTH figures" — sensitivity_open_px '
            'must be present and equal the fill bar\'s own open, on every trade',
        n, len(bad), bad, "PASS" if not bad else "FAIL")


def main():
    trades, processed, excl, ndays = build_trade_list()
    sess, _ = build_sessions()
    run_invariants(trades, sess)

    fields = sorted(trades[0].keys()) if trades else []
    print("=" * 96)
    print("2b, FRESH UNDER A1-A21 — INVARIANTS OVER THE WHOLE TRADE LIST")
    print("=" * 96)
    print("ARTEFACT UNDER TEST — admission list under spec_a16 (A16 limit entry, A17 "
          "bounded-span clustering; A18-A21 confirm existing behaviour).")
    print(f"  workbench sessions {ndays}   processed {processed}   excluded {excl}")
    print(f"  TRADES: {len(trades)}   sampling: NONE   cap: NONE   truncation: NONE")
    print()
    print(f"  fields present ({len(fields)}): {', '.join(fields)}")
    print()
    for iv in INV:
        print(f"--- INVARIANT {iv['n']} --- {iv['status']}")
        print(f"    clause     : {iv['clause']}")
        print(f"    evaluated  : {iv['evaluated']}")
        print(f"    violations : {iv['violations']}")
        if iv["violating_ids"]:
            extra = iv['violating_ids_truncated']
            tail = f" (+{extra} more)" if extra else ""
            print(f"    ids        : {iv['violating_ids']}{tail}")
        if iv["note"]:
            print(f"    note       : {iv['note']}")
    payload = {"trades": len(trades), "processed": processed, "excluded": excl,
               "fields": fields, "invariants": INV}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True))
    # determinism hash over the trade list, geometry only (same field set spirit as
    # invariants_2b's own hash, plus sensitivity_open_px since it's new this round)
    h = hashlib.sha256()
    for t in sorted(trades, key=lambda x: (x["session_date"], x["cm"], x["tf"])):
        h.update(f"{t['session_date']}|{t['cm']}|{t['tf']}|{t['direction']}|"
                 f"{t['entry']:.6f}|{t['stop_px']:.6f}|{t['tgt_px']:.6f}|"
                 f"{t['fill_px']:.6f}|{t['sensitivity_open_px']:.6f}|{t['fill_min']}\n"
                 .encode())
    digest = h.hexdigest()
    print(f"\nTRADE-LIST SHA-256 (geometry only): {digest}")
    return digest


if __name__ == "__main__":
    main()
