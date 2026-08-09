#!/usr/bin/env python3
"""THE 32-COMBINATION IDENTITY-CHURN SWEEP. Amendment 05's pass-mark clause (a-i),
FORK-SET-ENUMERATION.md's five forks, run under the current A1-A22 base (A16 limit entry,
A17 bounded-span clustering as the default reading, A22 2xATR stop floor). Workbench only
(2023-01-03 .. 2025-01-31). The holdout is never addressed by this module.

THE FIVE FORKS, both readings each (FORK-SET-ENUMERATION.md):
  1. cluster       : "bounded" (A17, mutual proximity) / "chain" (single-linkage)
  2. invalidation  : "same" (A18, the band the trade heads into) / "opposite"
  3. confluence    : "base" (A19, range=2) / "counter" (range treated as needing 3)
  4. front_run_f   : 2.0 (A20) / 2.5 (the blind build's alternative reading)
  5. weekly_hl     : "absent" (A21, struck) / "present" (built fresh for this sweep only -
                     a real week-level H/L tracker, since no such computation exists
                     anywhere else in this project)

This is the first module in this project's Amendment 05 work that computes an OUTCOME:
gross points, net points and net R at each of the three pre-registered cost bases
(stage2_smoke.COSTS = 0.50 / 0.975 / 1.50), using resolve_bar_stop_first (ambiguous bars
resolve stop-first) exactly as stage3_sealed_a15.py's discarded run did, and the SAME
realized-R formula (R = |fill_px - stop_px|, not the intended R_int at signal time) -
stage2_smoke.py's own stated reason: "the risk actually taken, not the risk intended."

Cost basis note: stage3_sealed_a15.py's own COSTS dict (0.25/0.50/1.00) belongs to the
DISCARDED run and is stale. This module uses stage2_smoke.COSTS (0.50/0.975/1.50), the
dict PASS-MARKS-FOR-SIGNING.md's signed 10.4a and 10.4b actually govern.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import itertools
from datetime import date

from vwapbb_signals import (minute_of_day, cluster_levels as cluster_levels_chain,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN)
from vwapbb_opportunity import trig
from vwapbb_a7_selector import ladder as _ladder_raw
from vwapbb_a7_selector import RR_FLOOR, TICK, MAX_TRADES_DAY, tie_break
from stage2_smoke import EOD_FLATTEN, COSTS
import spec_current as SC
from spec_a16 import cluster_levels_bounded, limit_fill
from spec_a22 import true_range, ATR_N

FORK_READINGS = {
    "cluster": ("bounded", "chain"),
    "invalidation": ("same", "opposite"),
    "confluence": ("base", "counter"),
    "front_run_f": (2.0, 2.5),
    "weekly_hl": ("absent", "present"),
}


def all_combinations():
    """32 combinations, each a dict {fork_name: reading}, in a fixed, stated order -
    not selected, all 32 built and run."""
    keys = list(FORK_READINGS)
    out = []
    for combo in itertools.product(*(FORK_READINGS[k] for k in keys)):
        out.append(dict(zip(keys, combo)))
    return out


def iso_week_key(d):
    """(iso_year, iso_week) for a session_date string 'YYYY-MM-DD'. Monday-Friday RTH
    sessions of one Globex trading week all land in the same ISO calendar week."""
    y, m, dd = (int(x) for x in d.split("-"))
    iso = date(y, m, dd).isocalendar()
    return (iso[0], iso[1])


def signal_candidates_sweep(bars, prev_hl, prev_week_hl, forks, audit=None):
    """spec_a22.signal_candidates_a22, with the five forks parameterized. Everything NOT
    named by a fork (A16 fill semantics, A22's 2xATR floor, A14 rounding, A9's HTF flag)
    is unchanged from the A1-A22 base."""
    audit = audit if audit is not None else collections.Counter()
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    tfbars = {tf: [] for tf in TFS}
    tfatr = {tf: collections.deque(maxlen=ATR_N) for tf in TFS}
    b15, acc15 = [], []
    sess_hi, sess_lo = -1e18, 1e18
    by_min = collections.defaultdict(list)

    cluster_fn = cluster_levels_bounded if forks["cluster"] == "bounded" else cluster_levels_chain
    front_run_f = forks["front_run_f"]

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
            tb = tfbars[tf]
            if tb:
                pc = tb[-1][3]
                tfatr[tf].append(true_range(th_, tl_, pc))
            tb.append((to_, th_, tl_, tc_))
            bb[tf].append(tc_)
            cm = mm + 1
            if cm < FIRST_SIG or cm > RTH_CLOSE or len(bb[tf]) < BB_N:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None:
                continue
            atr_tf = sum(tfatr[tf]) / len(tfatr[tf]) if len(tfatr[tf]) >= ATR_N else None
            if atr_tf is None:
                audit["dropped: ATR not warmed up"] += 1
                continue
            floor = 2.0 * atr_tf

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
            if forks["weekly_hl"] == "present" and prev_week_hl:            # fork 5
                menu += list(prev_week_hl)
            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            for cl_lo, cl_hi, types, nlev in cluster_fn(lv):                 # fork 1
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, SC.READING)):
                    with_trend = (flag == "uptrend" and direction == "long") or \
                                 (flag == "downtrend" and direction == "short")
                    if forks["confluence"] == "base":                       # fork 3
                        counter = (flag == "uptrend" and direction == "short") or \
                                  (flag == "downtrend" and direction == "long")
                    else:
                        counter = not with_trend
                    if len(types) < (3 if counter else 2):
                        audit["dropped: confluence"] += 1
                        continue
                    if ny_sig_ok:
                        if forks["invalidation"] == "same":                 # fork 2
                            bad_long = direction == "long" and th_ >= nmid + nsig
                            bad_short = direction == "short" and tl_ <= nmid - nsig
                        else:
                            bad_long = direction == "long" and tl_ <= nmid - nsig
                            bad_short = direction == "short" and th_ >= nmid + nsig
                        if bad_long or bad_short:
                            audit["dropped: invalidation"] += 1
                            continue
                    entry_px = SC.round_against_trader(basis, direction) if SC.A14_ROUND \
                        else basis
                    if direction == "long":
                        struct = tl_ - TICK
                        if entry_px <= struct:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(entry_px - struct, floor)
                        stop_px = entry_px - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= entry_px:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - entry_px, floor)
                        stop_px = entry_px + R_int
                    if SC.A14_ROUND:
                        stop_px = SC.round_away_from_entry(stop_px, entry_px)
                        R_int = abs(entry_px - stop_px)
                    tgt_px = None
                    for x in _ladder_raw(menu, entry_px, direction, front_run_f):  # fork 4
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


def admit_and_resolve(bars, cands, d, syms):
    """A16 limit-or-better fill + resolve_bar_stop_first exit resolution + EOD flatten
    (accounting 4.5) + cost-adjusted net R at all three cost bases. This is the one
    function in the whole Amendment 05 round that computes an outcome - everywhere else
    in this project stopped short of this on purpose."""
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
                reaches, fill_px = limit_fill(w["direction"], w["entry"], o, h, l)
                if reaches:
                    pos = {**w, "fill_px": fill_px, "fill_min": mj, "fill_bar": j}
                    n_adm += 1
        if pos is not None:
            if mj >= EOD_FLATTEN:
                ex, px = "eod_flatten", o
            else:
                res = SC.resolve_bar_stop_first(pos["direction"], pos["stop_px"],
                                                pos["tgt_px"], o, h, l, c)
                ex, px = (res, pos["stop_px"] if res == "stop" else pos["tgt_px"]) \
                    if res else (None, None)
            if ex is not None:
                R = abs(pos["fill_px"] - pos["stop_px"])
                gross = (px - pos["fill_px"]) if pos["direction"] == "long" \
                    else (pos["fill_px"] - px)
                rec = {**pos, "exit_reason": ex, "exit_price": px, "exit_min": mj,
                       "R": R, "gross_points": gross, "session_date": d, "symbols": syms}
                for tag, cst in COSTS.items():
                    rec[f"net_points_{tag}"] = gross - cst
                    rec[f"net_R_{tag}"] = (gross - cst) / R
                out.append(rec)
                pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    return out
