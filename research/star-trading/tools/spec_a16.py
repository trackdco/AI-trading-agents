#!/usr/bin/env python3
"""A16 (limit-order entry) + A17 (bounded-span clustering), layered on spec_current
(f6b38bf4, A1-A15). Frozen files (stage2_smoke / vwapbb_signals / vwapbb_opportunity) and
spec_current.py itself are NOT edited — this module adds the two deltas Amendment 05 round 2's
follow-up authorized, nothing else.

DELTAS vs spec_current, and nothing else:

  A17  Cluster formation uses BOUNDED-SPAN (mutual proximity) grouping, not
       vwapbb_signals.cluster_levels()'s single-linkage chaining. New function
       cluster_levels_bounded(), defined here. Measured reason: 21.0% of clusters formed by
       chaining span more than the stated tolerance (60-session sample; largest observed span
       50.53 pts, 5x tolerance) — see strategy-definition-v1.0.md A17.

  A16  Entry is a true limit order. admit_a16() fills at the limit or better if the bar
       immediately following the signal bar reaches it (single-bar window — T_cancel has no
       stated value and is disabled everywhere in this project); no trade otherwise. Every
       admitted (filled) trade ALSO carries `sensitivity_open_px`: the SAME fill bar's open,
       unconditional — PREREGISTRATION 4.2's convention, computed as a companion field on the
       SAME trade, never as an independently-admitted second population (an independent
       market-at-open admission run would select a different population via different one-at-a-
       time gating dynamics, which is exactly the "competing candidate" A16 rules out).

No outcome is computed anywhere in this module. Exit resolution (stop-vs-target) is used only to
gate one-at-a-time re-entry, exactly as invariants_2b._admit already does — no exit label is
ever stored. Workbench only.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections

from vwapbb_signals import (minute_of_day, RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG,
                            RTH_CLOSE, NY_VWAP_ANCHOR, POC_BIN, CLUSTER_TOL)
from vwapbb_opportunity import trig
from vwapbb_a7_selector import tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F, MAX_TRADES_DAY, TICK
from vwapbb_a7_selector import ladder as _ladder_raw
import spec_current as SC

SC.SIGMA_RULE = "live"


def cluster_levels_bounded(levels, tol=CLUSTER_TOL):
    """A17. A cluster's span (max - min) never exceeds tol, which for a sorted set is exactly
    'every member within tol of every other' (mutual proximity). Compares each candidate to the
    GROUP'S MINIMUM (the first member accepted), not to the most recently accepted member —
    that is the one-line difference from vwapbb_signals.cluster_levels's chaining."""
    if len(levels) < 2:
        return []
    ls = sorted(levels)
    out, cur = [], [ls[0]]
    for p, t in ls[1:]:
        if p - cur[0][0] <= tol:
            cur.append((p, t))
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = [(p, t)]
    if len(cur) >= 2:
        out.append(cur)
    return [(c[0][0], c[-1][0], {t for _, t in c}, len(c)) for c in out]


def limit_fill(direction, limit, o, h, l):
    """A16, the fill decision, extracted as a standalone pure function so it can be unit-
    tested directly against the amendment text alone (mirrors how resolve_bar_stop_first was
    extracted in item 5 of the overnight queue). One bar's own OHLC only.

    long:  fills iff bar_low  <= limit;  fill = min(open, limit) - the limit, or the open if
           the bar gapped through favourably (opened below the limit, better than the limit).
    short: fills iff bar_high >= limit;  fill = max(open, limit) - symmetric.
    No fill -> (False, None). Touch is inclusive (<=/>=), matching this spec's touch semantics
    elsewhere (S7 invalidation, over-extension, resolve_bar_stop_first)."""
    if direction == "long":
        if l <= limit:
            return True, min(o, limit)
        return False, None
    if h >= limit:
        return True, max(o, limit)
    return False, None


def signal_candidates_a16(bars, prev_hl, audit=None):
    """spec_current.signal_candidates_current, with cluster_levels_bounded (A17) in place of
    vwapbb_signals.cluster_levels. Candidate GEOMETRY (entry/stop/target proposal) is otherwise
    unchanged — A16 only changes what happens to a candidate at the fill step, in admit_a16()."""
    audit = audit if audit is not None else collections.Counter()
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
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
            ny_sig_ok = SC.ny_sigma_eligible(nmid, nsig, cm, n_ny)

            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv.append((nmid, "vwap"))
                if ny_sig_ok:
                    lv += [(nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                    sess_hi, sess_lo]
            if nmid:
                menu += [nmid, nmid + nsig, nmid - nsig, nmid + 2 * nsig, nmid - 2 * nsig]
            if prev_hl:
                menu += list(prev_hl)
            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            for cl_lo, cl_hi, types, nlev in cluster_levels_bounded(lv):        # A17
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, SC.READING)):
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):                     # A19
                        audit["dropped: confluence"] += 1
                        continue
                    if ny_sig_ok:                                              # A18
                        if direction == "long" and th_ >= nmid + nsig:
                            audit["dropped: invalidation"] += 1
                            continue
                        if direction == "short" and tl_ <= nmid - nsig:
                            audit["dropped: invalidation"] += 1
                            continue
                    else:
                        audit["invalidation SKIPPED (A8, NY sigma ineligible)"] += 1
                    entry_px = SC.round_against_trader(basis, direction) if SC.A14_ROUND \
                        else basis
                    if direction == "long":
                        struct = tl_ - TICK
                        if entry_px <= struct:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(entry_px - struct, MIN_STOP)
                        stop_px = entry_px - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= entry_px:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - entry_px, MIN_STOP)
                        stop_px = entry_px + R_int
                    tgt_px = None
                    for x in _ladder_raw(menu, entry_px, direction, FRONT_RUN_F):  # A20
                        if abs(x - entry_px) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                    if tgt_px is None:
                        audit["dropped: no target clears the RR floor"] += 1
                        continue
                    if SC.A14_ROUND:
                        tgt_px = SC.round_away_from_entry(tgt_px, entry_px)
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": entry_px, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "htf": flag, "counter": counter, "types": len(types),
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


def admit_a16(bars, cands, d=None, syms=None):
    """A16 streaming admission: true single-bar limit-or-better fill; no fill -> no trade.
    Each admitted trade also carries sensitivity_open_px (same fill bar's open, unconditional
    - PREREGISTRATION 4.2's convention, disclosed alongside, never a second admitted population).
    Counts, identities, and this one companion price only; no outcome is produced."""
    idxs = sorted(bars)
    pending, pos, n_adm = None, None, 0
    out = []
    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)
        if pending is not None and pos is None:
            if mj >= SC.EOD_FLATTEN:
                pending = None
            else:
                w, pending = pending, None
                reaches, fill_px = limit_fill(w["direction"], w["entry"], o, h, l)
                if reaches:
                    pos = {**w, "fill_px": fill_px, "sensitivity_open_px": o,
                           "fill_min": mj, "fill_bar": j}
                    n_adm += 1
        if pos is not None:
            if mj >= SC.EOD_FLATTEN:
                rel = True
            elif pos["direction"] == "long":
                rel = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
            else:
                rel = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
            if rel:
                extra = {"release_min": mj, "release_bar": j}
                if d is not None:
                    extra["session_date"] = d
                if syms is not None:
                    extra["symbols"] = syms
                out.append({**pos, **extra})
                pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    if pos is not None:
        extra = {"release_min": None, "release_bar": None}
        if d is not None:
            extra["session_date"] = d
        if syms is not None:
            extra["symbols"] = syms
        out.append({**pos, **extra})
    return out
