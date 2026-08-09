#!/usr/bin/env python3
"""Amendment 05 round 2, follow-up — MINIMAL FROZEN SPEC population count.

A single, explicitly-stated build: what is the admitted trade count if the detector
is restricted to (a) only the levels STRUCTURAL-LEVELS-AUDIT.md found genuinely
computed in the live path, (b) true limit-order entry semantics instead of the
next-open accounting rule, and (c) all five identity-churn forks resolved to the
CURRENT code reading (FORK-SET-ENUMERATION.md, corrected 1-bis).

NOT touching spec_current.py or invariants_2b.py. This is a new, separate,
parallel build, same discipline spec_current.py itself used against stage2_smoke.py.
No outcome is computed: exit resolution (stop-vs-target) is used ONLY to gate
one-at-a-time re-entry, exactly as invariants_2b._admit already does and as
invariant 6's own note states ("the release bar is recorded WITHOUT recording
which side released it, so no outcome is exposed"). This script prints and
records COUNTS ONLY. No win rate, no expectancy, no P&L, no R-multiple outcome.

------------------------------------------------------------------------------
(a) LEVEL RESTRICTION — the 5 rows STRUCTURAL-LEVELS-AUDIT.md marked COMPUTED:
    prior-day H/L, POC, 4h-range (recorded only, inert to admission - dropped
    from this build since it decides nothing), pullback-origin/B2 (a selection
    RULE over the menu, not a level in its own right - already subsumed by
    walking the menu ladder outward, exactly as current code does; nothing to
    add), BB MA. Net effect on the two lists that matter:
      lv (cluster-eligible)   : {BB MA, POC} only  — ALL VWAP terms removed
      menu (target ladder)    : {POC, prior-day H/L} only — ALL VWAP terms,
                                 session extremes, weekly H/L (already absent)
                                 removed
    NOT restricted: the S7 invalidation gate (NY VWAP +/-1sigma). That gate is
    fork 2, not one of the 18 audited "structural levels" - it is a validity
    check, not a cluster/target candidate, and fork 2 is explicitly pinned to
    its CURRENT reading per this build's own stated rule (resolve all 5 forks
    to current). Excluding it would be a SIXTH, unrequested restriction; it
    stays active, computed from NY VWAP mid/sigma exactly as today.

(b) FILL SEMANTICS — declared explicitly, not inherited from PREREGISTRATION 4.2:
    the one bar after the signal bar closes (same bar invariants_2b calls
    fill_bar) is checked for TRUE single-bar limit reachability, matching the
    "reaches" test already computed in fill_fork_report.py:
      long:  fills iff bar_low  <= limit;  fill_px = min(bar_open, limit)
      short: fills iff bar_high >= limit;  fill_px = max(bar_open, limit)
    "fill at limit or better" - the fill is the limit price, or the bar's own
    open if the open itself already cleared the limit favourably. No fill,
    no trade, no waiting for a later bar: T_cancel has no stated value and is
    disabled everywhere in this project (FILL-MECHANICS-QUOTES.md S2), so a
    multi-bar rest cannot be operationalised without inventing a parameter
    the spec does not supply. This is the single-bar reading, stated as such.

(c) FORKS — all five resolved to CURRENT, per FORK-SET-ENUMERATION.md as
    corrected (1-bis): cluster formation = single-linkage chaining (imported
    unmodified from vwapbb_signals.cluster_levels); S7 invalidation = same-side
    band; range confluence minimum = 2; front-run F = 2.0; weekly H/L = absent
    (moot here - already excluded by the level restriction in (a)).
------------------------------------------------------------------------------
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, RunningVWAP,
                            TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE, NY_VWAP_ANCHOR,
                            POC_BIN)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F, \
                               MAX_TRADES_DAY, TICK
from stage2_smoke import contract_key, EOD_FLATTEN, READING
import spec_current as SC

SC.SIGMA_RULE = "live"
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "minimal_frozen_spec.json"


def _candidates_minimal(bars, prev_hl):
    """Same shape as invariants_2b._instrumented, lv/menu restricted per (a) above."""
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None
    nv = RunningVWAP()                       # kept: feeds the S7 invalidation gate only
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    by_min = collections.defaultdict(list)

    for i in idxs:
        o, h, l, c, v = bars[i]
        mm = minute_of_day(i)
        if NY_VWAP_ANCHOR <= mm < RTH_CLOSE + 1:
            nv.add(h, l, c, v)
        nb = max(1, int((h - l) / POC_BIN) + 1)
        for k in range(nb):
            poc[int((l + k * POC_BIN) / POC_BIN)] += v / nb
        acc15.append((o, h, l, c))
        if (mm + 1) % 15 == 0:
            b15.append((acc15[0][0], max(x[1] for x in acc15),
                        min(x[2] for x in acc15), acc15[-1][3]))
            acc15 = []
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
            nmid, nsig = nv.value()
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            basis = sum(bb[tf]) / BB_N
            flag = SC.htf_flag_a10(b15)
            n_ny = max(0, cm - NY_VWAP_ANCHOR)
            ok = SC.ny_sigma_eligible(nmid, nsig, cm, n_ny)          # fork 2 infra, kept

            # ---- (a) restricted lists ----
            lv = [(basis, "bb"), (p, "poc")]
            menu = [p]
            if prev_hl:
                menu += list(prev_hl)

            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):     # fork 1: current (chaining)
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):           # fork 3: current (min=2)
                        continue
                    if ok:                                           # fork 2: current (same-side)
                        if direction == "long" and th_ >= nmid + nsig:
                            continue
                        if direction == "short" and tl_ <= nmid - nsig:
                            continue
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
                    tgt_px = None
                    for x in ladder(menu, entry_px, direction, FRONT_RUN_F):  # fork 4: F=2.0
                        if abs(x - entry_px) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                    if tgt_px is None:
                        continue
                    if SC.A14_ROUND:
                        tgt_px = SC.round_away_from_entry(tgt_px, entry_px)
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": entry_px, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
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


def _admit_limit(bars, cands, d, syms, stats):
    """(b) true single-bar limit fill, replacing invariants_2b._admit's
    unconditional next-open fill. Resolution (stop-vs-target) is used ONLY to
    gate one-at-a-time re-entry - no exit label is stored or returned."""
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
                stats["candidates_seen"] += 1
                if w["direction"] == "long":
                    reaches = (l <= w["entry"])
                    fill_px = min(o, w["entry"])
                else:
                    reaches = (h >= w["entry"])
                    fill_px = max(o, w["entry"])
                if reaches:
                    stats["filled"] += 1
                    pos = {**w, "fill_px": fill_px, "fill_min": mj, "fill_bar": j}
                    n_adm += 1
                else:
                    stats["no_fill"] += 1
        if pos is not None:
            if mj >= EOD_FLATTEN:
                rel = True
            elif pos["direction"] == "long":
                rel = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
            else:
                rel = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
            if rel:
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


def main():
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
    stats = collections.Counter()
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
            cands = _candidates_minimal(bars, prev_hl)
            if cands is None:
                excl["holiday / short session"] += 1
            else:
                processed += 1
                for t in _admit_limit(bars, cands, d, sorted(sym_of[d]), stats):
                    trades.append(t)
        if d not in rolls:
            prev_hl = this_hl

    n = len(trades)
    report = {
        "n_trades_admitted_and_filled": n,
        "clears_661": n >= 661,
        "comparison_baseline_661": 661,
        "candidates_seen_at_fill_decision": stats["candidates_seen"],
        "filled": stats["filled"],
        "no_fill_bar_never_reached_limit": stats["no_fill"],
        "sessions_processed": processed,
        "sessions_excluded": dict(excl),
        "workbench_days_total": len(days),
    }
    print("=" * 92)
    print("MINIMAL FROZEN SPEC — 5 implemented levels, true-limit fill, forks = current")
    print("=" * 92)
    print(f"workbench sessions {len(days)}   processed {processed}   excluded {dict(excl)}")
    print()
    print(f"candidates reaching the fill decision : {stats['candidates_seen']}")
    print(f"  filled (bar reached the limit)      : {stats['filled']}")
    print(f"  NOT filled (bar never reached it)   : {stats['no_fill']}")
    print()
    print(f"ADMITTED-AND-FILLED TRADE COUNT: {n}")
    print(f"clears 661? {'YES' if n >= 661 else 'NO'}  ({n} vs 661)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwritten {OUT}")


if __name__ == "__main__":
    main()
