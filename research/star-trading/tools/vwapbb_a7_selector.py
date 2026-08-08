#!/usr/bin/env python3
"""A7 CONFIRMATION COUNT — §10 Vault selector, first-come.

Full filter stack + A4 (target = first ladder level clearing the RR floor)
+ A5 (minimum stop 10.00 pt) + A7 (first-come admission, one at a time,
max 3/session, MTF tie-break).

RESOLUTION TIMING. The one-at-a-time rule cannot be applied without knowing
when a position closes, so this run walks each admitted candidate's bars
forward until the stop distance or the target distance is touched first, and
uses the elapsed minutes ONLY to decide when the next candidate may be
admitted. Stop-first ordering is computed as an unavoidable by-product. It is
NOT aggregated, NOT reported, and NOT examined — no win rate, no expectancy,
no P&L exists anywhere in this file. Search it for `win` and you will find
nothing.

Workbench only; the holdout is never addressed. N_trials remains 0.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections

from vwapbb_signals import (build_sessions, minute_of_day, RunningVWAP, cluster_levels,
                            htf_flag, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, B_MIN, QUARTILE)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END

TICK = 0.25
MIN_STOP = 10.00            # §5.4 as amended — A5
RR_FLOOR = 1.5              # §6.5
FRONT_RUN_F = 2.0           # §6.4 "start 2-3"; low end, most permissive
MAX_TRADES_DAY = 3          # §10
LOC_BAND = 0.20             # PLACEHOLDER — "HTF range top" has no stated boundary
READINGS = ("A", "B", "C", "D")
TRIPWIRE = 0.4862


def ladder(levels, entry, direction, f):
    if direction == "long":
        xs = sorted(x - f for x in levels if x - f > entry)
    else:
        xs = sorted((x + f for x in levels if x + f < entry), reverse=True)
    out = []
    for x in xs:
        if not out or abs(x - out[-1]) > TICK:
            out.append(x)
    return out


def tie_break(cands):
    """A7 tie-break for candidates sharing a signal minute. Returns
    (winner, level_that_decided). Levels, in order:
      1 highest entry TF          — §1 MTF arbitration [SPEC, CONFIRMED - Angus]
      2 stand down on conflict    — long and short on one bar is not confluence
      3 largest cluster           — §3 confluence count, the spec's own quality measure
      4 cluster nearest entry     — the cluster actually being traded against
      5 lowest cluster low        — pure determinism backstop, arbitrary but stated
    """
    if len(cands) == 1:
        return cands[0], 0
    top = max(c["tf"] for c in cands)
    g = [c for c in cands if c["tf"] == top]
    if len(g) == 1:
        return g[0], 1
    if len({c["direction"] for c in g}) > 1:
        return None, 2                       # contradictory signals -> no trade
    mx = max(c["nlev"] for c in g)
    g2 = [c for c in g if c["nlev"] == mx]
    if len(g2) == 1:
        return g2[0], 3
    mn = min(abs(c["cl_mid"] - c["entry"]) for c in g2)
    g3 = [c for c in g2 if abs(c["cl_mid"] - c["entry"]) == mn]
    if len(g3) == 1:
        return g3[0], 4
    return min(g3, key=lambda c: c["cl_lo"]), 5


def process(d, bars, prev_hl):
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None
    hi_arr = {i: bars[i][1] for i in idxs}
    lo_arr = {i: bars[i][2] for i in idxs}
    last_idx = idxs[-1]

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    qual = {m: [] for m in READINGS}          # post-stage-3 candidates

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
            to_, th_, tl_, tc_ = g[0][0], max(x[1] for x in g), min(x[2] for x in g), g[-1][3]
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
            flag = htf_flag(b15)

            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                    sess_hi, sess_lo]
            if nmid:
                menu += [nmid, nmid + nsig, nmid - nsig, nmid + 2 * nsig, nmid - 2 * nsig]
            if prev_hl:
                menu += list(prev_hl)

            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                for mode in READINGS:
                    if mode == "D" and nlev < 3:
                        continue
                    for direction, kind in trig(to_, th_, tl_, tc_, cl_lo, cl_hi, nib, mode):
                        counter = (flag == "uptrend" and direction == "short") or \
                                  (flag == "downtrend" and direction == "long")
                        if len(types) < (3 if counter else 2):
                            continue
                        if nmid:
                            if direction == "long" and th_ >= nmid + nsig:
                                continue
                            if direction == "short" and tl_ <= nmid - nsig:
                                continue
                        if h4:
                            rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                            if rh > rl:
                                pos = (tc_ - rl) / (rh - rl)
                                if direction == "long" and pos >= 1 - LOC_BAND:
                                    continue
                                if direction == "short" and pos <= LOC_BAND:
                                    continue
                        entry = basis
                        if direction == "long":
                            stop = tl_ - TICK
                            if entry <= stop:
                                continue
                            R = max(entry - stop, MIN_STOP)
                        else:
                            stop = th_ + TICK
                            if stop <= entry:
                                continue
                            R = max(stop - entry, MIN_STOP)
                        lad = ladder(menu, entry, direction, FRONT_RUN_F)
                        tgt_d = None
                        for x in lad:
                            dd = abs(x - entry)
                            if dd / R >= RR_FLOOR:
                                tgt_d = dd
                                break
                        if tgt_d is None:
                            continue
                        qual[mode].append({
                            "cm": cm, "bar": i, "tf": tf, "direction": direction,
                            "entry": entry, "R": R, "tgt_d": tgt_d, "nlev": nlev,
                            "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        })

    # ---------------- A7 admission, per reading ----------------
    out = {}
    for mode in READINGS:
        cands = qual[mode]
        # Collapse duplicate records for the SAME trade before tie-breaking.
        # trig() can emit both a rejection and a displacement for one
        # cluster/direction/TF; those share entry, stop and target and are one
        # trade, not two. Counting them as a tie inflates the tie statistic and
        # hands the decision to the arbitrary backstop for no reason.
        by_min = collections.defaultdict(list)
        for c in cands:
            g = by_min[c["cm"]]
            k = (c["tf"], c["direction"], round(c["entry"], 4),
                 round(c["R"], 4), round(c["tgt_d"], 4))
            if k not in {(x["tf"], x["direction"], round(x["entry"], 4),
                          round(x["R"], 4), round(x["tgt_d"], 4)) for x in g}:
                g.append(c)
        stats = {"qualified": len(cands), "minutes": len(by_min), "admitted": 0,
                 "blocked_open": 0, "blocked_cap": 0, "cap_bound": 0,
                 "ties": 0, "tie_levels": collections.Counter(),
                 "standdown": 0, "holds": []}
        open_until, n_adm = -1, 0
        for cm in sorted(by_min):
            group = by_min[cm]
            if len(group) > 1:
                stats["ties"] += 1
            if cm < open_until:
                stats["blocked_open"] += len(group)
                continue
            if n_adm >= MAX_TRADES_DAY:
                stats["blocked_cap"] += len(group)
                continue
            win, lvl = tie_break(group)
            stats["tie_levels"][lvl] += 1
            if win is None:
                stats["standdown"] += 1
                continue
            # resolution timing only — direction of resolution is not recorded
            j, res = win["bar"] + 1, None
            while j <= last_idx:
                if j in hi_arr:
                    if win["direction"] == "long":
                        up, dn = hi_arr[j] - win["entry"], win["entry"] - lo_arr[j]
                    else:
                        up, dn = win["entry"] - lo_arr[j], hi_arr[j] - win["entry"]
                    if dn >= win["R"] or up >= win["tgt_d"]:
                        res = j - win["bar"]
                        break
                j += 1
            hold = res if res is not None else (last_idx - win["bar"])
            stats["holds"].append(hold)
            open_until = cm + hold
            n_adm += 1
            stats["admitted"] += 1
        if n_adm >= MAX_TRADES_DAY:
            stats["cap_bound"] = 1
        out[mode] = stats
    return out


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    print(f"A7 CONFIRMATION COUNT — first-come selector, full filter stack + A4 + A5")
    print(f"workbench {len(days)} sessions ({days[0]}..{days[-1]}); holdout NOT addressed")
    print(f"A5 min stop {MIN_STOP:.2f} pt | A4 first level clearing {RR_FLOOR}R | "
          f"A7 first-come, one-at-a-time, max {MAX_TRADES_DAY}/session\n")

    agg = {m: collections.Counter() for m in READINGS}
    holds = {m: [] for m in READINGS}
    tl = {m: collections.Counter() for m in READINGS}
    ns = 0
    prev_hl = None
    for n, d in enumerate(days, 1):
        assert_workbench(d)
        bars = sess[d]
        if len(sym_of[d]) > 1:
            prev_hl = (max(b[1] for b in bars.values()), min(b[2] for b in bars.values()))
            continue
        r = process(d, bars, prev_hl)
        prev_hl = (max(b[1] for b in bars.values()), min(b[2] for b in bars.values()))
        if r is None:
            continue
        ns += 1
        for m in READINGS:
            s = r[m]
            for k in ("qualified", "minutes", "admitted", "blocked_open",
                      "blocked_cap", "cap_bound", "ties", "standdown"):
                agg[m][k] += s[k]
            holds[m].extend(s["holds"])
            tl[m].update(s["tie_levels"])
        if n % 100 == 0:
            print(f"  ...{n}/{len(days)}")

    print(f"\nsessions processed: {ns}\n")
    print(f"{'':28}" + "".join(f"{m:>13}" for m in READINGS))
    print("-" * 80)
    rows = [
        ("qualified candidates/sess", lambda m: agg[m]["qualified"] / ns),
        ("distinct signal minutes/sess", lambda m: agg[m]["minutes"] / ns),
        ("ADMITTED trades/session", lambda m: agg[m]["admitted"] / ns),
        ("blocked: position open", lambda m: agg[m]["blocked_open"] / ns),
        ("blocked: 3/day cap", lambda m: agg[m]["blocked_cap"] / ns),
        ("stand-down (tie level 2)", lambda m: agg[m]["standdown"] / ns),
    ]
    for lab, fn in rows:
        print(f"{lab:28}" + "".join(f"{fn(m):>13.3f}" for m in READINGS))
    print("-" * 80)
    print(f"{'% blocked by one-at-a-time':28}" + "".join(
        f"{agg[m]['blocked_open']/max(1,agg[m]['qualified'])*100:>12.1f}%" for m in READINGS))
    print(f"{'% blocked by 3/day cap':28}" + "".join(
        f"{agg[m]['blocked_cap']/max(1,agg[m]['qualified'])*100:>12.1f}%" for m in READINGS))
    print(f"{'% of sessions cap binds':28}" + "".join(
        f"{agg[m]['cap_bound']/ns*100:>12.1f}%" for m in READINGS))
    print(f"{'% signal-minutes tied':28}" + "".join(
        f"{agg[m]['ties']/max(1,agg[m]['minutes'])*100:>12.1f}%" for m in READINGS))
    print(f"{'median hold, minutes':28}" + "".join(
        f"{sorted(holds[m])[len(holds[m])//2] if holds[m] else 0:>13.0f}" for m in READINGS))

    print(f"\nTIE-BREAK: which level decided each admission")
    names = {0: "0 no tie (single candidate)", 1: "1 highest entry TF [SPEC]",
             2: "2 stand down, conflict", 3: "3 largest cluster",
             4: "4 cluster nearest entry", 5: "5 lowest cluster low (backstop)"}
    print(f"{'':32}" + "".join(f"{m:>13}" for m in READINGS))
    for k in sorted(names):
        tot = {m: sum(tl[m].values()) for m in READINGS}
        print(f"{names[k]:32}" + "".join(
            f"{tl[m][k]/max(1,tot[m])*100:>12.1f}%" for m in READINGS))

    print(f"\n{'TRIPWIRE CHECK (>= ' + str(TRIPWIRE) + ' trades/session)':60}")
    for m in READINGS:
        v = agg[m]["admitted"] / ns
        print(f"   reading {m}: {v:.3f}  ->  "
              f"{'CLEARS' if v >= TRIPWIRE else 'FAILS'}  ({v/TRIPWIRE:.1f}x)")
    print("\nNo outcome was aggregated. Resolution timing was used only to determine")
    print("when the next candidate could be admitted. N_trials remains 0.")


if __name__ == "__main__":
    main()
