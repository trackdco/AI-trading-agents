#!/usr/bin/env python3
"""A22 — §5.4 stop floor changes from a fixed 10.00 pt to 2xATR(20, entry TF), layered on
spec_a16 (A16 limit entry + A17 bounded-span clustering). Frozen files, spec_current.py, and
spec_a16.py are NOT edited — this module adds the one delta A22 authorises, nothing else.

DELTA vs spec_a16, and nothing else:

  A22  Effective stop = max(structural stop, 2 x ATR(20, entry TF)), replacing A5's
       max(structural stop, 10.00 pt). ATR definition matches the one already computed (as a
       diagnostic, never wired into the live pipeline) in vwapbb_geometry.py: True Range on
       CLOSED bars of the candidate's own entry timeframe (TFS = 1,2,3,5 minutes), True Range
       = max(high-low, |high-prev_close|, |low-prev_close|) against the prior closed bar's
       close on the SAME timeframe, 20-bar simple average, ATR_N=20. A candidate's entry TF
       must have accumulated 20 closed bars before ATR is available - exactly as
       vwapbb_geometry.py requires - so candidates before that warmup are dropped, the same
       shape as the existing "if dmid is None: continue" VWAP warmup gate.

This was Angus's own decision among three already-computed, pre-existing figures (10.00 pt
floor / 16.29 pt median prior-swing / 25.32 pt median 2xATR) laid out in
PASS-MARKS-FOR-SIGNING.md 10.2, explicitly framed there as "genuinely yours to call" — not an
outcome comparison. No trade, fill, or result was computed to make this decision, and none of
this module computes one either.

No outcome is computed anywhere in this module. Workbench only.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections

from vwapbb_signals import (minute_of_day, RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG,
                            RTH_CLOSE, NY_VWAP_ANCHOR, POC_BIN)
from vwapbb_opportunity import trig
from vwapbb_a7_selector import ladder as _ladder_raw
from vwapbb_a7_selector import RR_FLOOR, FRONT_RUN_F, TICK
import spec_current as SC
from spec_a16 import cluster_levels_bounded, admit_a16, limit_fill  # noqa: F401 (re-exported)

ATR_N = 20                # matches vwapbb_geometry.py exactly


def true_range(h, l, prev_close):
    """A22, one closed bar's True Range against the prior closed bar's close on the SAME
    timeframe: max(high-low, |high-prev_close|, |low-prev_close|). Extracted as a standalone
    pure function so it (and compute_atr, below) can be unit-tested directly against the
    amendment text, mirroring how limit_fill (A16) and resolve_bar_stop_first were extracted."""
    return max(h - l, abs(h - prev_close), abs(l - prev_close))


def compute_atr(closed_bars, n=ATR_N):
    """A22, ATR(n) over a sequence of closed (o,h,l,c) bars on one timeframe, oldest first.
    Simple average of True Range (not Wilder's smoothing), matching vwapbb_geometry.py exactly.
    Requires at least n+1 closed bars (n True Range values, each needing a PRIOR close) - fewer
    returns None, the warmup gate. Uses only the most recent n True Range values if more than
    n+1 bars are given (matching the deque(maxlen=ATR_N) in both this module and the
    diagnostic it mirrors)."""
    if len(closed_bars) < n + 1:
        return None
    trs = [true_range(closed_bars[i][1], closed_bars[i][2], closed_bars[i - 1][3])
           for i in range(1, len(closed_bars))]
    trs = trs[-n:]
    return sum(trs) / len(trs)


def signal_candidates_a22(bars, prev_hl, audit=None):
    """spec_a16.signal_candidates_a16, with the A5 fixed 10.00pt floor replaced by A22's
    2xATR(20, entry TF). Everything else (cluster formation, invalidation, confluence
    minimum, front-run F, target menu) is unchanged from the A16/A17 pipeline."""
    audit = audit if audit is not None else collections.Counter()
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    tfbars = {tf: [] for tf in TFS}                          # closed entry-TF bars (o,h,l,c)
    tfatr = {tf: collections.deque(maxlen=ATR_N) for tf in TFS}
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
            if atr_tf is None:                                          # A22 warmup gate
                audit["dropped: ATR not warmed up (< 20 closed bars, entry TF)"] += 1
                continue
            floor = 2.0 * atr_tf                                        # A22

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
                        R_int = max(entry_px - struct, floor)                  # A22
                        stop_px = entry_px - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= entry_px:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - entry_px, floor)                  # A22
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
                        "tgt_px": tgt_px, "R_int": R_int, "atr_tf": atr_tf,
                        "nlev": nlev, "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
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
