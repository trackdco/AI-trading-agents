#!/usr/bin/env python3
"""CURRENT-SPEC harness — spec 59edd5b2, amendments A1-A12.

The frozen detector (stage2_smoke / vwapbb_signals / vwapbb_opportunity) is NOT
edited. This module re-implements the same pipeline with the three A8-A12 changes
that alter behaviour, so "under the current spec" can be evaluated without
touching the files the sealed run was produced from.

DELTAS vs the superseded spec (8ead7259), and nothing else:

  A8  NY VWAP sigma bands are INELIGIBLE for cluster membership (§3) and as the
      §7 invalidation reference until NY_SIGMA_MIN_OBS completed 1-minute bars
      have elapsed since the 09:30 anchor. The NY MID stays eligible throughout.
      A8 says nothing about the §6 target menu, so the menu is left alone; that
      silence is recorded as a residual ambiguity, not resolved here.
      The VWAP feed itself is unchanged - the detector already used 1m bars.

  A9  The §7 location gate is REMOVED. Range position is computed and carried as
      a covariate on every candidate (both definitions where available), and
      removes nothing.

  A10 Fractal swing: H[i] >  H[i-1..i-N] AND H[i] >= H[i+1..i+N]
                     L[i] <  L[i-1..i-N] AND L[i] <= L[i+1..i+N]
      First bar of a plateau is the swing.

  A11 is output-only and is emitted as entry_tf_1m.

No outcome is computed anywhere in this module. Workbench only.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections

from vwapbb_signals import (minute_of_day, cluster_levels, RunningVWAP, TFS, BB_N,
                            RTH_OPEN, FIRST_SIG, RTH_CLOSE, NY_VWAP_ANCHOR, POC_BIN,
                            FRACTAL_N)
from vwapbb_opportunity import trig
from vwapbb_a7_selector import (ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F,
                                MAX_TRADES_DAY, TICK)
from stage2_smoke import EOD_FLATTEN, READING

NY_SIGMA_MIN_OBS = 30                                   # A8 as first written
NY_SIGMA_OK_CM = NY_VWAP_ANCHOR + NY_SIGMA_MIN_OBS      # 600 = 10:00 ET
CLUSTER_TOL_HALF = 5.0                                  # A13: half the 10-pt §3 tolerance
Z95 = 1.959964
SIGMA_RULE = "live"      # "live" = A13 per-instant CI test; "fixed30" = A8 as first written


def ny_sigma_eligible(nmid, nsig, cm, n_bars):
    """A13: a NY VWAP sigma band is cluster-eligible when the 95% CI on its
    distance from the mid is <= HALF the cluster tolerance.
        z * sigma_hat / sqrt(2(n-1))  <=  tol/2
    Evaluated per instant from that session's own sigma_hat. No fitted constant."""
    if not nmid or n_bars < 2:
        return False
    if SIGMA_RULE == "fixed30":
        return cm >= NY_SIGMA_OK_CM
    return Z95 * nsig / ((2 * (n_bars - 1)) ** 0.5) <= CLUSTER_TOL_HALF


def htf_flag_a10(b15, n=FRACTAL_N):
    """A10: strict on the left, non-strict on the right. First bar of a plateau wins."""
    if len(b15) < 2 * n + 1:
        return "range"
    hs, lo = [], []
    for i in range(n, len(b15) - n):
        h, l = b15[i][1], b15[i][2]
        if all(h > b15[j][1] for j in range(i - n, i)) and \
           all(h >= b15[j][1] for j in range(i + 1, i + n + 1)):
            hs.append(h)
        if all(l < b15[j][2] for j in range(i - n, i)) and \
           all(l <= b15[j][2] for j in range(i + 1, i + n + 1)):
            lo.append(l)
    if len(hs) >= 2 and len(lo) >= 2:
        if hs[-1] > hs[-2] and lo[-1] > lo[-2]:
            return "uptrend"
        if hs[-1] < hs[-2] and lo[-1] < lo[-2]:
            return "downtrend"
    return "range"


def signal_candidates_current(bars, prev_hl, audit=None):
    """Post-filter candidates under A8 + A9 + A10. Same shape as
    stage2_smoke.signal_candidates, plus loc_pos as a covariate."""
    audit = audit if audit is not None else collections.Counter()
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
            flag = htf_flag_a10(b15)                              # A10
            n_ny = max(0, cm - NY_VWAP_ANCHOR)
            ny_sig_ok = ny_sigma_eligible(nmid, nsig, cm, n_ny)   # A8 / A13

            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv.append((nmid, "vwap"))
                if ny_sig_ok:                                     # A8
                    lv += [(nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                    sess_hi, sess_lo]
            if nmid:
                menu += [nmid, nmid + nsig, nmid - nsig, nmid + 2 * nsig, nmid - 2 * nsig]
            if prev_hl:
                menu += list(prev_hl)
            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            loc_pos = None
            if h4:
                rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                if rh > rl:
                    loc_pos = (tc_ - rl) / (rh - rl)

            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                if READING == "D" and nlev < 3:
                    continue
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):
                        audit["dropped: confluence"] += 1
                        continue
                    if ny_sig_ok:                                  # A8: gate only when eligible
                        if direction == "long" and th_ >= nmid + nsig:
                            audit["dropped: invalidation"] += 1
                            continue
                        if direction == "short" and tl_ <= nmid - nsig:
                            audit["dropped: invalidation"] += 1
                            continue
                    else:
                        audit["invalidation SKIPPED (A8, NY sigma ineligible)"] += 1
                    # A9: location gate removed. loc_pos rides along as a covariate.
                    if direction == "long":
                        struct = tl_ - TICK
                        if basis <= struct:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(basis - struct, MIN_STOP)
                        stop_px = basis - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= basis:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - basis, MIN_STOP)
                        stop_px = basis + R_int
                    tgt_px = None
                    for x in ladder(menu, basis, direction, FRONT_RUN_F):
                        if abs(x - basis) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                    if tgt_px is None:
                        audit["dropped: no target clears the RR floor"] += 1
                        continue
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": basis, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "htf": flag, "counter": counter, "types": len(types),
                        "loc_pos": loc_pos, "ny_sigma_eligible": ny_sig_ok,
                        "entry_tf_1m": tf == 1,                   # A11
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


def admit_current(bars, cands):
    """A7 streaming admission. Counts and identities only; no outcome is produced."""
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
                    pos = w
                    n_adm += 1
                    out.append({**w, "fill_px": o, "fill_min": mj})
        if pos is not None:
            if mj >= EOD_FLATTEN:
                pos = None
            else:
                if pos["direction"] == "long":
                    done = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
                else:
                    done = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
                if done:
                    pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    return out
