#!/usr/bin/env python3
"""2b — INVARIANTS OVER THE WHOLE TRADE LIST.

WHAT IS BEING CHECKED, stated before anything else, because the brief assumes an
artefact that does not exist in this repository:

  There is NO Stage 3 trade list. Nothing named Stage 3 has been run. The only
  sealed artefact is the Stage 2 workbench smoke result, archived unopened at
  data/archive/workbench_results_SEALED_PRE-A8_UNOPENED.parquet, produced under
  spec 8ead7259 which A9 and A10 have since superseded.

  These invariants are therefore asserted over a FRESHLY COMPUTED ADMISSION LIST
  under the current spec 42d6f0f6 (A1-A13), produced by spec_current.py. It is a
  geometry-only artefact: every trade carries entry, stop, target, timeframe,
  direction and timing, and NO outcome field exists anywhere in it. No exit
  reason, no P&L, no R multiple is computed, stored or reported.

Full workbench, every session, no sampling and no cap.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import hashlib
import json
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, RunningVWAP,
                            TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE, NY_VWAP_ANCHOR,
                            POC_BIN)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import (ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F,
                                MAX_TRADES_DAY, TICK)
from stage2_smoke import contract_key, EOD_FLATTEN, READING
import spec_current as SC

SC.SIGMA_RULE = "live"
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "invariants_2b.json"


# ─────────────────────────────────────────────────────────────────────
def build_trade_list():
    """Admission list under the current spec, instrumented with the extra fields
    the invariants need. Instrumentation records; it changes no decision."""
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
                for t in _admit(bars, cands, d, sorted(sym_of[d])):
                    trades.append(t)
        if d not in rolls:
            prev_hl = this_hl
    return trades, processed, dict(excl), len(days)


def _instrumented(bars, prev_hl):
    """spec_current.signal_candidates_current, with the trigger bar's extremes, the
    target ladder and the contract-bar span recorded on each candidate."""
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    by_min = collections.defaultdict(list)

    for i in idxs:
        o, h, l, c, v = bars[i]
        mm = minute_of_day(i)
        dv.add(h, l, c, v)
        if NY_VWAP_ANCHOR <= mm < RTH_CLOSE + 1:
            nv.add(h, l, c, v)
        nb = max(1, int((h - l) / POC_BIN) + 1)
        for k in range(nb):
            poc[int((l + k * POC_BIN) / POC_BIN)] += v / nb
        sess_hi, sess_lo = max(sess_hi, h), min(sess_lo, l)
        acc15.append((o, h, l, c))
        if (mm + 1) % 15 == 0:
            b15.append((acc15[0][0], max(x[1] for x in acc15),
                        min(x[2] for x in acc15), acc15[-1][3]))
            acc15 = []
        acc4.append((h, l))
        if (mm + 1) % 240 == 0:
            h4.append((max(x[0] for x in acc4), min(x[1] for x in acc4)))
            acc4 = []
        for tf in TFS:
            tfacc[tf].append((o, h, l, c))
            if (mm + 1) % tf:
                continue
            g = tfacc[tf]
            tfacc[tf] = []
            to_, th_, tl_, tc_ = (g[0][0], max(x[1] for x in g),
                                  min(x[2] for x in g), g[-1][3])
            bb[tf].append(tc_)
            cm = mm + 1
            if cm < FIRST_SIG or cm > RTH_CLOSE or len(bb[tf]) < BB_N:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None:
                continue
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            basis = sum(bb[tf]) / BB_N
            flag = SC.htf_flag_a10(b15)
            n_ny = max(0, cm - NY_VWAP_ANCHOR)
            ok = SC.ny_sigma_eligible(nmid, nsig, cm, n_ny)
            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv.append((nmid, "vwap"))
                if ok:
                    lv += [(nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                    sess_hi, sess_lo]
            if nmid:
                menu += [nmid, nmid + nsig, nmid - nsig, nmid + 2 * nsig, nmid - 2 * nsig]
            if prev_hl:
                menu += list(prev_hl)
            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)
            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):
                        continue
                    if ok:
                        if direction == "long" and th_ >= nmid + nsig:
                            continue
                        if direction == "short" and tl_ <= nmid - nsig:
                            continue
                    # A14: entry rounds against the trader first (spec_current.A14_ROUND
                    # toggles this off for a before/after comparison); every downstream
                    # quantity is derived from the rounded entry, same as spec_current.py.
                    entry_px = SC.round_against_trader(basis, direction) if SC.A14_ROUND \
                        else basis
                    if direction == "long":
                        struct = tl_ - TICK
                        if entry_px <= struct:
                            continue
                        R_int = max(entry_px - struct, MIN_STOP)
                        stop_px = entry_px - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= entry_px:
                            continue
                        R_int = max(struct - entry_px, MIN_STOP)
                        stop_px = entry_px + R_int
                    rungs = ladder(menu, entry_px, direction, FRONT_RUN_F)
                    tgt_px = None
                    skipped = []
                    for x in rungs:
                        if abs(x - entry_px) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                        skipped.append(x)
                    if tgt_px is None:
                        continue
                    if SC.A14_ROUND:
                        tgt_px = SC.round_away_from_entry(tgt_px, entry_px)
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": entry_px, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "htf": flag, "counter": counter, "types": len(types),
                        # ---- instrumentation, decision-free ----
                        "trig_high": th_, "trig_low": tl_, "struct_anchor": struct,
                        "rungs_skipped": skipped, "n_rungs": len(rungs),
                        "signal_bar_idx": i, "tf_bar_first_idx": i - tf + 1,
                    })
    out = {}
    for cm, g in by_min.items():
        keep, seen = [], set()
        for x in g:
            k = (x["tf"], x["direction"], round(x["entry"], 4),
                 round(x["stop_px"], 4), round(x["tgt_px"], 4))
            if k not in seen:
                seen.add(k)
                keep.append(x)
        out[cm] = keep
    return out


def _admit(bars, cands, d, syms):
    idxs = sorted(bars)
    pending, pos, n_adm = None, None, 0
    out = []
    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)
        if pending is not None and pos is None:
            if mj >= EOD_FLATTEN:
                pending = None
            else:
                w, pending = pending, None
                bad = (w["direction"] == "long" and o <= w["stop_px"]) or \
                      (w["direction"] == "short" and o >= w["stop_px"])
                if not bad:
                    pos = {**w, "fill_px": o, "fill_min": mj, "fill_bar": j}
                    n_adm += 1
        if pos is not None:
            if mj >= EOD_FLATTEN:
                rel = True
            elif pos["direction"] == "long":
                rel = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
            else:
                rel = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
            if rel and j > pos["fill_bar"]:
                out.append({**pos, "release_min": mj, "release_bar": j,
                            "session_date": d, "symbols": syms})
                pos = None
            elif rel and j == pos["fill_bar"]:
                # released on its own fill bar
                out.append({**pos, "release_min": mj, "release_bar": j,
                            "session_date": d, "symbols": syms})
                pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    if pos is not None:
        out.append({**pos, "release_min": None, "release_bar": None,
                    "session_date": d, "symbols": syms})
    return out


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

    # 1 — RR floor
    bad = [tid(t) for t in trades
           if abs(t["tgt_px"] - t["entry"]) / t["R_int"] < RR_FLOOR - 1e-9]
    rec(1, '§6.5/A4 "the first level whose front-run-adjusted distance is >= 1.5R"',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "measured against the INTENDED R at signal time, which is the quantity "
        "§6.5 is written about")

    # 2 — stop anchor
    bad = []
    for t in trades:
        anchor = t["trig_low"] - TICK if t["direction"] == "long" else t["trig_high"] + TICK
        want_R = max(abs(t["entry"] - anchor), MIN_STOP)
        want_stop = t["entry"] - want_R if t["direction"] == "long" else t["entry"] + want_R
        if abs(want_stop - t["stop_px"]) > 1e-9 or abs(want_R - t["R_int"]) > 1e-9:
            bad.append(tid(t))
    rec(2, '§5.4 "beyond the wick extreme of the trigger candle" + A2 "1 tick beyond '
           'the wick extreme" + A5 "Effective stop = max(structural stop, 10.00 pt)"',
        n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 3 — target is the nearest rung that clears
    bad = [tid(t) for t in trades
           if any(abs(x - t["entry"]) / t["R_int"] >= RR_FLOOR - 1e-9
                  for x in t["rungs_skipped"])]
    rec(3, '§6.5/A4 "Walk the ladder ... outward from entry. The working target is '
           'the FIRST level whose front-run-adjusted distance is >= 1.5R"',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "checks that no rung nearer than the chosen one also cleared the floor")

    # 4 — fill at the open of the bar AFTER the signal bar
    bad = []
    for t in trades:
        b = sess[t["session_date"]]
        want = t["signal_bar_idx"] + 1
        if t["fill_bar"] != want or abs(b[t["fill_bar"]][0] - t["fill_px"]) > 1e-9:
            bad.append(tid(t))
    rec(4, 'PREREGISTRATION.md accounting rule 4.2, quoted in stage2_smoke: '
           '"entry fills at the OPEN of the bar after the signal bar closes"',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "NOTE: 4.2 is an ACCOUNTING rule in the pre-registration. The SPEC itself "
        "(§5.3 E1) specifies a LIMIT at the BB MA and §5.5 a no-chase cancel; the "
        "next-bar-open fill is a documented handicap, not spec text")

    # 5 — signal window
    bad = [tid(t) for t in trades if not (FIRST_SIG <= t["cm"] <= RTH_CLOSE)]
    rec(5, 'A1 "RTH 09:31-16:00 ET, entry blackout 09:31-09:35, first tradeable '
           'signal bar 09:36"', n, len(bad), bad, "PASS" if not bad else "FAIL")

    # 6 — one position at a time
    bad = []
    per = collections.defaultdict(list)
    for t in trades:
        per[t["session_date"]].append(t)
    for d, g in per.items():
        g = sorted(g, key=lambda x: x["fill_bar"])
        for a, b in zip(g, g[1:]):
            if a["release_bar"] is None or b["fill_bar"] <= a["release_bar"]:
                bad.append(tid(b))
        if len(g) > MAX_TRADES_DAY:
            bad.append(f"{d}|CAP|{len(g)}")
    rec(6, '§5.6 "One position at a time. No overlapping trades ever." + §10.1(3) '
           '"At most 3 candidates are admitted per session"',
        n, len(bad), bad, "PASS" if not bad else "FAIL",
        "overlap is tested on bar indices; the release bar is recorded WITHOUT "
        "recording which side released it, so no outcome is exposed")

    # 7 — stop-first
    rec(7, '§4.1 (accounting) "ambiguous bars resolve STOP-FIRST"', 0, 0, [],
        "NOT TESTABLE",
        "the admission list carries NO exit attribution by construction, because "
        "recording which side released a position is outcome information barred by "
        "Part 0 rule 6. Stop-first is a property of a Stage 3 engine that does not "
        "exist. It cannot be tested here and is NOT marked PASS")

    # 8 — determinism: handled by the caller's double run

    # 9 — tick grid
    bad_entry = [tid(t) for t in trades if not on_grid(t["entry"])]
    bad_stop = [tid(t) for t in trades if not on_grid(t["stop_px"])]
    bad_tgt = [tid(t) for t in trades if not on_grid(t["tgt_px"])]
    bad_fill = [tid(t) for t in trades if not on_grid(t["fill_px"])]
    rec(9, 'NO CLAUSE. §5.3 says "E1: limit at the BB MA" and never requires '
           'rounding to the tick; §1 gives the instrument but no price-grid rule',
        n * 4, len(bad_entry) + len(bad_stop) + len(bad_tgt) + len(bad_fill),
        [], "UNSPECIFIED IN SPEC",
        f"off-grid counts of {n}: intended entry {len(bad_entry)}, "
        f"stop {len(bad_stop)}, target {len(bad_tgt)}, actual fill {len(bad_fill)}")

    # 10 — single contract
    bad = [tid(t) for t in trades if len(t["symbols"]) != 1]
    rec(10, '§4.3 (accounting) "contract rolls reset indicator state; roll sessions '
            'AND the session after each roll are skipped"',
        n, len(bad), bad, "PASS" if not bad else "FAIL")


def main():
    trades, processed, excl, ndays = build_trade_list()
    sess, _ = build_sessions()
    run_invariants(trades, sess)

    fields = sorted(trades[0].keys()) if trades else []
    print("=" * 96)
    print("2b — INVARIANTS OVER THE WHOLE TRADE LIST")
    print("=" * 96)
    print("ARTEFACT UNDER TEST — there is no Stage 3 trade list in this repository.")
    print("  Freshly computed ADMISSION LIST under spec 42d6f0f6 (A1-A13).")
    print(f"  workbench sessions {ndays}   processed {processed}   excluded {excl}")
    print(f"  TRADES: {len(trades)}   sampling: NONE   cap: NONE   truncation: NONE")
    print()
    print("FIELD AVAILABILITY")
    print(f"  fields present ({len(fields)}): {', '.join(fields)}")
    print()
    need = {
        1: ["entry", "tgt_px", "R_int"],
        2: ["entry", "stop_px", "R_int", "trig_low", "trig_high"],
        3: ["rungs_skipped", "entry", "R_int"],
        4: ["fill_bar", "fill_px", "signal_bar_idx"],
        5: ["cm"],
        6: ["fill_bar", "release_bar", "session_date"],
        7: ["exit_reason  <-- ABSENT BY DESIGN"],
        9: ["entry", "stop_px", "tgt_px", "fill_px"],
        10: ["symbols"],
    }
    for k in sorted(need):
        miss = [f for f in need[k] if f.split()[0] not in fields]
        print(f"  inv {k:>2}: requires {need[k]}"
              f"{'   MISSING: ' + str(miss) if miss else '   all present'}")
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
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True))
    # determinism hash over the trade list, geometry only
    h = hashlib.sha256()
    for t in sorted(trades, key=lambda x: (x["session_date"], x["cm"], x["tf"])):
        h.update(f"{t['session_date']}|{t['cm']}|{t['tf']}|{t['direction']}|"
                 f"{t['entry']:.6f}|{t['stop_px']:.6f}|{t['tgt_px']:.6f}|"
                 f"{t['fill_px']:.6f}|{t['fill_min']}\n".encode())
    print(f"\nTRADE-LIST SHA-256 (geometry only): {h.hexdigest()}")
    return h.hexdigest()


if __name__ == "__main__":
    main()
