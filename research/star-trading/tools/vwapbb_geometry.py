#!/usr/bin/env python3
"""TARGET-VS-STOP RECONCILIATION — geometry re-run.

Diagnostic only. Emits one record per qualified trigger *before* the §6.5 RR
floor, because the RR floor's verdict depends on which stop anchor and which
target rule are in force — filtering on the spec pairing first would condition
the sample on the very thing under test.

Same filter stack as vwapbb_opportunity.py in every other respect (cluster,
trigger reading, confluence count, §7 invalidation, §7 location). Warmup =
`prior` only; the warmup difference is a measured 0.2% and is second-order here.

No selector adopted, no P&L, no threshold tuned. N_trials unchanged.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
import time
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from vwapbb_signals import (build_sessions, minute_of_day, RunningVWAP, cluster_levels,
                            htf_flag, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, B_MIN, QUARTILE)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
SHARDS = OUT / "_geom_shards"
TICK, FRONT_RUN_F, LOC_BAND = 0.25, 2.0, 0.20
READINGS = ("A", "B", "C", "D")
SWING_N = 2          # same fractal definition as the HTF flag [FIAT, gate 4 #3]
ATR_N = 20


def ladder(levels, entry, direction, f):
    """Front-run-adjusted opposing levels beyond entry, nearest first, deduped
    to 1 tick so 'second nearest' is a genuinely different level."""
    if direction == "long":
        xs = sorted(x - f for x in levels if x - f > entry)
    else:
        xs = sorted((x + f for x in levels if x + f < entry), reverse=True)
    out = []
    for x in xs:
        if not out or abs(x - out[-1]) > TICK:
            out.append(x)
    return out


def process_session(d, bars, prev_hl, atr_d):
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    tfbars = {tf: [] for tf in TFS}            # closed entry-TF bars (o,h,l,c)
    tfatr = {tf: collections.deque(maxlen=ATR_N) for tf in TFS}
    swing_lo = {tf: [] for tf in TFS}          # confirmed fractal lows, in order
    swing_hi = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    cands = []

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
            tb = tfbars[tf]
            if tb:
                pc = tb[-1][3]
                tfatr[tf].append(max(th_ - tl_, abs(th_ - pc), abs(tl_ - pc)))
            tb.append((to_, th_, tl_, tc_))
            bb[tf].append(tc_)
            # confirm the fractal that is now SWING_N bars back
            k = len(tb) - 1 - SWING_N
            if k >= SWING_N:
                w = tb[k - SWING_N:k + SWING_N + 1]
                if all(w[SWING_N][2] < w[j][2] for j in range(len(w)) if j != SWING_N):
                    swing_lo[tf].append(w[SWING_N][2])
                if all(w[SWING_N][1] > w[j][1] for j in range(len(w)) if j != SWING_N):
                    swing_hi[tf].append(w[SWING_N][1])

            cm = mm + 1
            if cm < FIRST_SIG or cm > RTH_CLOSE or len(bb[tf]) < BB_N:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None:
                continue
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            flag = htf_flag(b15)
            basis = sum(bb[tf]) / BB_N
            atr_tf = sum(tfatr[tf]) / len(tfatr[tf]) if len(tfatr[tf]) >= ATR_N else None

            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig,
                    p, sess_hi, sess_lo]
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

                        entry = basis                      # E1, unchanged
                        # ---- stop anchors, all as DISTANCES from entry ----
                        if direction == "long":
                            s_wick = entry - (tl_ - TICK)
                            s_clus = entry - (cl_lo - TICK)
                            sw = [x for x in swing_lo[tf] if x < entry]
                            s_swing = (entry - (sw[-1] - TICK)) if sw else None
                        else:
                            s_wick = (th_ + TICK) - entry
                            s_clus = (cl_hi + TICK) - entry
                            sw = [x for x in swing_hi[tf] if x > entry]
                            s_swing = ((sw[-1] + TICK) - entry) if sw else None
                        s_range = th_ - tl_                # candle range as the risk unit

                        tl3 = ladder([x for x, _ in lv] + menu, entry, direction, FRONT_RUN_F)
                        if not tl3:
                            continue
                        dist = [abs(x - entry) for x in tl3[:3]]
                        while len(dist) < 3:
                            dist.append(None)
                        # deepest rung the spec's own menu offers, and the nearest
                        # "opposing liquidity" extreme (§6 rule 2's default for B)
                        extremes = [sess_hi, sess_lo] + (list(prev_hl) if prev_hl else [])
                        ex = ladder(extremes, entry, direction, FRONT_RUN_F)
                        d_max = abs(tl3[-1] - entry)
                        d_ex = abs(ex[0] - entry) if ex else None
                        d_exmax = abs(ex[-1] - entry) if ex else None

                        cands.append({
                            "session_date": d, "signal_minute": cm, "direction": direction,
                            "trigger_reading": mode, "trigger_kind": kind, "entry_tf": tf,
                            "cluster_types": ",".join(sorted(types)), "cluster_size": nlev,
                            "cluster_span_points": round(cl_hi - cl_lo, 4),
                            "htf_flag": flag, "counter_trend": counter,
                            "entry_price": round(entry, 4),
                            "candle_range_points": round(th_ - tl_, 4),
                            "entry_inside_cluster": bool(cl_lo <= entry <= cl_hi),
                            "stop_wick_1tick": round(s_wick, 4) if s_wick > 0 else None,
                            "stop_cluster_far_edge": round(s_clus, 4) if s_clus > 0 else None,
                            "stop_prior_swing": round(s_swing, 4) if s_swing and s_swing > 0 else None,
                            "stop_candle_range": round(s_range, 4) if s_range > 0 else None,
                            "atr_entry_tf": round(atr_tf, 4) if atr_tf else None,
                            "atr_daily": round(atr_d, 4) if atr_d else None,
                            "tgt1_points": round(dist[0], 4),
                            "tgt2_points": round(dist[1], 4) if dist[1] else None,
                            "tgt3_points": round(dist[2], 4) if dist[2] else None,
                            "n_targets": len(tl3),
                            "tgt_deepest_points": round(d_max, 4),
                            "tgt_nearest_extreme_points": round(d_ex, 4) if d_ex else None,
                            "tgt_furthest_extreme_points": round(d_exmax, 4) if d_exmax else None,
                            "year": d[:4],
                        })
    return cands


def main():
    t0 = time.time()
    SHARDS.mkdir(parents=True, exist_ok=True)
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    print(f"workbench sessions {len(days)} ({days[0]}..{days[-1]}); holdout NOT addressed")

    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d])[0]
        if prev and s != prev:
            rolls.add(d)
        prev = s
    skip = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    prev_hl, prev_close, trs = None, None, collections.deque(maxlen=14)
    skipped, total = collections.Counter(), 0
    for n, d in enumerate(days, 1):
        assert_workbench(d)
        shard = SHARDS / f"{d}.json"
        bars = sess[d]
        hi = max(b[1] for b in bars.values()); lo = min(b[2] for b in bars.values())
        tr = hi - lo if prev_close is None else max(hi - lo, abs(hi - prev_close), abs(lo - prev_close))
        atr_d = sum(trs) / len(trs) if trs else None
        if d in rolls:
            trs.clear(); prev_close = None
        if shard.exists():
            total += len(json.loads(shard.read_text()))
        elif d in rolls:
            skipped["roll session"] += 1
        elif d in skip:
            skipped["session after roll"] += 1
        elif len(sym_of[d]) > 1:
            skipped["mixed contract"] += 1
        else:
            c = process_session(d, bars, prev_hl, atr_d)
            if c is None:
                skipped["holiday / short session"] += 1
            else:
                shard.write_text(json.dumps(c))
                total += len(c)
        trs.append(tr); prev_close = list(bars.values())[-1][3]
        prev_hl = (hi, lo)
        if n % 100 == 0 or n == len(days):
            print(f"  {n}/{len(days)}  {total} records  {time.time()-t0:.0f}s")

    rows = []
    for f in sorted(SHARDS.glob("*.json")):
        rows.extend(json.loads(f.read_text()))
    cols = {k: [r.get(k) for r in rows] for k in rows[0]}
    pq.write_table(pa.table(cols), OUT / "geometry.parquet", compression="snappy")
    print(f"DONE  records={len(rows)}  sessions={len(days)-sum(skipped.values())}  "
          f"skipped={dict(skipped)}  {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
