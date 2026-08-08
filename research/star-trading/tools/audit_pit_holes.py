#!/usr/bin/env python3
"""STAGE 1, part 2 — the two holes audit_pit.py could not close.

HOLE 1: audit_pit.py imports htf_flag and uses it as BOTH the reference and the
        detector value, so it cannot detect a bug INSIDE htf_flag. Closed here by
        a reference built the opposite way round: htf_flag scans a finished array
        with a bound of range(n, len-n); the reference accumulates swings
        STREAMING, recording each only at the bar where it first becomes
        confirmable. If the batch bound is wrong the two diverge.

HOLE 2: the one-at-a-time gate sets open_until = cm + hold, and hold comes from
        bars after cm. Closed here by re-deciding every admission with a strictly
        STREAMING simulator that walks the session bar by bar, holds one position
        at a time, and never looks past the bar it is on. If the batch and
        streaming admission sets are identical, the batch form uses no
        information a live system would lack.

Workbench only. No outcome is aggregated. N_trials remains 0.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, FRACTAL_N)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F, \
    MAX_TRADES_DAY, LOC_BAND, TICK


# ════════════════════════════════════════════════════════════════════
# HOLE 1 — independent HTF reference, built streaming not batch
# ════════════════════════════════════════════════════════════════════
def ref_htf_streaming(b15):
    """Accumulate confirmed swings causally. A swing at index j is recorded only
    once bar j+FRACTAL_N has arrived — i.e. at the moment it first becomes
    knowable — rather than by scanning a finished array with a bound.

    Deliberately NOT the same construction as htf_flag(). If htf_flag's loop
    bound admits unconfirmed swings, this diverges.
    """
    n = FRACTAL_N
    hs, lo = [], []
    for k in range(len(b15)):                      # k = bars seen so far, 0-based
        j = k - n                                  # the bar that becomes confirmable now
        if j < n:
            continue
        hi_j, lo_j = b15[j][1], b15[j][2]
        left = range(j - n, j)
        right = range(j + 1, j + n + 1)
        if max(right) > k:                         # not yet knowable — never happens
            continue                                # by construction; guard anyway
        if all(hi_j > b15[q][1] for q in left) and all(hi_j > b15[q][1] for q in right):
            hs.append(hi_j)
        if all(lo_j < b15[q][2] for q in left) and all(lo_j < b15[q][2] for q in right):
            lo.append(lo_j)
    if len(hs) >= 2 and len(lo) >= 2:
        if hs[-1] > hs[-2] and lo[-1] > lo[-2]:
            return "uptrend"
        if hs[-1] < hs[-2] and lo[-1] < lo[-2]:
            return "downtrend"
    return "range"


def hole1(sess, days, n_sessions=60):
    """Compare htf_flag against the streaming reference at EVERY 15m boundary of
    a sample of sessions — not just at signal minutes, so the comparison covers
    the whole distribution of b15 lengths."""
    step = max(1, len(days) // n_sessions)
    cmp_n = agree = 0
    disagree = []
    flag_dist = collections.Counter()
    prefix_lengths = set()
    for d in days[::step][:n_sessions]:
        bars = sess[d]
        b15, acc15 = [], []
        for i in sorted(bars):
            o, h, l, c, v = bars[i]
            mm = minute_of_day(i)
            acc15.append((o, h, l, c))
            if (mm + 1) % 15 == 0:
                b15.append((acc15[0][0], max(x[1] for x in acc15),
                            min(x[2] for x in acc15), acc15[-1][3]))
                acc15 = []
                a = htf_flag(b15)
                b = ref_htf_streaming(b15)
                cmp_n += 1
                prefix_lengths.add(len(b15))
                flag_dist[a] += 1
                if a == b:
                    agree += 1
                else:
                    disagree.append((d, len(b15), a, b))
    return {
        "comparisons": cmp_n, "agree": agree, "disagree": disagree,
        "distinct_prefix_lengths": len(prefix_lengths),
        "flag_distribution": dict(flag_dist),
        "pass": not disagree and cmp_n > 0 and len(flag_dist) > 1,
    }


# ════════════════════════════════════════════════════════════════════
# HOLE 2 — streaming admission simulator
# ════════════════════════════════════════════════════════════════════
def qualify(d, bars, prev_hl, mode="A"):
    """Post-stage-3 candidates, identical filter stack to vwapbb_a7_selector."""
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None, None
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    out = []
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
                    out.append({"cm": cm, "bar": i, "tf": tf, "direction": direction,
                                "entry": entry, "R": R, "tgt_d": tgt_d, "nlev": nlev,
                                "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2})
    return out, idxs


def dedupe_by_minute(cands):
    by_min = collections.defaultdict(list)
    for c in cands:
        g = by_min[c["cm"]]
        k = (c["tf"], c["direction"], round(c["entry"], 4),
             round(c["R"], 4), round(c["tgt_d"], 4))
        if k not in {(x["tf"], x["direction"], round(x["entry"], 4),
                      round(x["R"], 4), round(x["tgt_d"], 4)) for x in g}:
            g.append(c)
    return by_min


def admit_batch(cands, bars, idxs):
    """The CURRENT implementation: resolve each admitted trade in one shot, then
    set open_until = cm + hold."""
    by_min = dedupe_by_minute(cands)
    hi = {i: bars[i][1] for i in idxs}
    lo = {i: bars[i][2] for i in idxs}
    last = idxs[-1]
    admitted, open_until, n_adm = [], -1, 0
    for cm in sorted(by_min):
        if cm < open_until:
            continue
        if n_adm >= MAX_TRADES_DAY:
            continue
        win, lvl = tie_break(by_min[cm])
        if win is None:
            continue
        j, res = win["bar"] + 1, None
        while j <= last:
            if j in hi:
                up = (hi[j] - win["entry"]) if win["direction"] == "long" else (win["entry"] - lo[j])
                dn = (win["entry"] - lo[j]) if win["direction"] == "long" else (hi[j] - win["entry"])
                if dn >= win["R"] or up >= win["tgt_d"]:
                    res = j - win["bar"]
                    break
            j += 1
        hold = res if res is not None else (last - win["bar"])
        open_until = cm + hold
        n_adm += 1
        admitted.append((cm, win["tf"], win["direction"]))
    return admitted


def admit_streaming(cands, bars, idxs):
    """STRICTLY CAUSAL: walk the session bar by bar. A position, once opened, is
    checked for resolution only against bars that have arrived. Admission of a
    later candidate consults nothing beyond the bar being processed."""
    by_min = dedupe_by_minute(cands)
    admitted, n_adm = [], 0
    pos = None                       # {"entry","R","tgt_d","direction"} or None
    for i in idxs:
        o, h, l, c, v = bars[i]
        # 1. resolve an open position against THIS bar, before anything else
        if pos is not None:
            up = (h - pos["entry"]) if pos["direction"] == "long" else (pos["entry"] - l)
            dn = (pos["entry"] - l) if pos["direction"] == "long" else (h - pos["entry"])
            if dn >= pos["R"] or up >= pos["tgt_d"]:
                pos = None
        # 2. candidates whose signal minute is this bar's CLOSE minute
        cm = minute_of_day(i) + 1
        if cm in by_min and pos is None and n_adm < MAX_TRADES_DAY:
            win, lvl = tie_break(by_min[cm])
            if win is not None:
                pos = {"entry": win["entry"], "R": win["R"],
                       "tgt_d": win["tgt_d"], "direction": win["direction"]}
                n_adm += 1
                admitted.append((cm, win["tf"], win["direction"]))
    return admitted


def hole2(sess, sym_of, days, n_sessions=120):
    step = max(1, len(days) // n_sessions)
    prev_hl_map, prev = {}, None
    for d in days:
        prev_hl_map[d] = prev
        b = sess[d]
        prev = (max(x[1] for x in b.values()), min(x[2] for x in b.values()))
    same = diff = 0
    diffs = []
    tot_batch = tot_stream = 0
    for d in days[::step][:n_sessions]:
        if len(sym_of[d]) > 1:
            continue
        bars = sess[d]
        cands, idxs = qualify(d, bars, prev_hl_map[d])
        if cands is None:
            continue
        a = admit_batch(cands, bars, idxs)
        b = admit_streaming(cands, bars, idxs)
        tot_batch += len(a)
        tot_stream += len(b)
        if a == b:
            same += 1
        else:
            diff += 1
            diffs.append((d, a, b))
    return {"sessions": same + diff, "identical": same, "different": diff,
            "diffs": diffs[:8], "trades_batch": tot_batch,
            "trades_streaming": tot_stream, "pass": diff == 0}


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    print("=" * 96)
    print("STAGE 1 PART 2 — closing the two holes audit_pit.py could not")
    print("=" * 96)
    print(f"workbench {len(days)} sessions; holdout NOT addressed\n")

    print("-" * 96)
    print("HOLE 1 — htf_flag was its own reference. Independent streaming reference:")
    print("-" * 96)
    h1 = hole1(sess, days)
    print(f"  comparisons          : {h1['comparisons']} (every 15m boundary, sampled sessions)")
    print(f"  distinct b15 lengths : {h1['distinct_prefix_lengths']}")
    print(f"  flag distribution    : {h1['flag_distribution']}")
    print(f"  agree                : {h1['agree']}")
    print(f"  DISAGREE             : {len(h1['disagree'])}")
    for x in h1["disagree"][:8]:
        print(f"      {x}")
    print(f"  -> {'PASS' if h1['pass'] else '*** FAIL ***'}")
    if len(h1["flag_distribution"]) <= 1:
        print("     WARNING: only one flag value observed — the test is not discriminating.")

    print("\n" + "-" * 96)
    print("HOLE 2 — one-at-a-time gate. Batch (open_until = cm + hold) vs strictly")
    print("         causal streaming simulator:")
    print("-" * 96)
    h2 = hole2(sess, sym_of, days)
    print(f"  sessions compared    : {h2['sessions']}")
    print(f"  identical admissions : {h2['identical']}")
    print(f"  DIFFERENT            : {h2['different']}")
    print(f"  trades batch / stream: {h2['trades_batch']} / {h2['trades_streaming']}")
    for x in h2["diffs"]:
        print(f"      {x[0]}\n         batch : {x[1]}\n         stream: {x[2]}")
    print(f"  -> {'PASS' if h2['pass'] else '*** FAIL ***'}")

    print("\n" + "=" * 96)
    ok = h1["pass"] and h2["pass"]
    print(f"BOTH HOLES: {'CLOSED' if ok else '*** NOT CLOSED ***'}")
    print("=" * 96)
    return ok


if __name__ == "__main__":
    main()
