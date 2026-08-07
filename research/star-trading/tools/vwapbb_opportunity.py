#!/usr/bin/env python3
"""OPPORTUNITY SET CHARACTERISATION — VWAP/BB. Measurement pass, not a backtest.

Emits one record per qualified candidate (post full filter stack, PRE Vault cap),
for all four trigger readings, over the workbench only.

Performance note: all four readings are evaluated in ONE pass over the bars.
The indicator work (VWAP, POC, BB) is identical across readings and is the
dominant cost; only the trigger predicate differs. Running four separate passes
costs 4x for no benefit.

No numpy in this environment (the Debian build is mismatched to the interpreter),
so the forward excursion is a plain running max/min over each candidate's
remaining-bar slice. That is O(candidates x bars_remaining) ~ 4M operations,
which is seconds in pure Python. pyarrow is available for the parquet write.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
from datetime import datetime
import json
import time
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from vwapbb_signals import (build_sessions, minute_of_day, RunningVWAP, cluster_levels,
                            htf_flag, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, B_MIN, QUARTILE)

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
SHARDS = OUT / "_shards"
WORKBENCH_END = "2025-01-31"          # HARD BOUNDARY — holdout begins 2025-02-01
TICK, RR_FLOOR, FRONT_RUN_F = 0.25, 1.5, 2.0
LOC_BAND = 0.20
READINGS = ("A", "B", "C", "D")


class HoldoutBreach(RuntimeError):
    pass


def assert_workbench(d: str):
    """Fail loud. An unattended run is exactly when a careless read goes unnoticed."""
    if d > WORKBENCH_END:
        raise HoldoutBreach(
            f"REFUSING to read {d}: holdout begins 2025-02-01 and is SEALED. "
            f"Workbench ends {WORKBENCH_END}."
        )


def trig(o, h, l, c, lo, hi, nib, mode):
    out = set()
    rng = h - l
    if rng <= 0:
        return out
    blo, bhi = min(o, c), max(o, c)
    pen_l = (l <= hi) if mode == "A" else (l <= lo)
    pen_s = (h >= lo) if mode == "A" else (h >= hi)
    wk_l = (l < blo) if mode in ("A", "B") else ((blo - l) / rng >= 0.5)
    wk_s = (h > bhi) if mode in ("A", "B") else ((h - bhi) / rng >= 0.5)
    if pen_l and c > hi and wk_l:
        out.add(("long", "rejection"))
    if pen_s and c < lo and wk_s:
        out.add(("short", "rejection"))
    if nib >= 2 and (bhi - blo) / rng >= B_MIN:
        if (c - l) / rng >= QUARTILE and c > hi:
            out.add(("long", "displacement"))
        if (h - c) / rng >= QUARTILE and c < lo:
            out.add(("short", "displacement"))
    return out


def process_session(d, bars, sym, days_to_roll, spans_roll, prev_hl, atr_d):
    """Return list of candidate dicts for this session, all readings."""
    idxs = sorted(bars)
    rth = [i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]
    if len(rth) < 300:
        return None

    # forward-excursion arrays, indexed by session minute-index
    hi_arr = {i: bars[i][1] for i in idxs}
    lo_arr = {i: bars[i][2] for i in idxs}
    last_idx = idxs[-1]

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {(tf, w): collections.deque(maxlen=BB_N) for tf in TFS for w in ("prior", "rth")}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    ib_hi, ib_lo = None, None                       # initial balance 09:31-10:30
    rng_sum = 0.0
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
        if RTH_OPEN <= mm < RTH_OPEN + 60:
            ib_hi = h if ib_hi is None else max(ib_hi, h)
            ib_lo = l if ib_lo is None else min(ib_lo, l)
        rng_sum += (h - l)

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
            bb[(tf, "prior")].append(tc_)
            if mm >= RTH_OPEN:
                bb[(tf, "rth")].append(tc_)
            cm = mm + 1
            if cm < FIRST_SIG or cm > RTH_CLOSE:
                continue

            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None:
                continue
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            flag = htf_flag(b15)

            for warm in ("prior", "rth"):
                dq = bb[(tf, warm)]
                if len(dq) < BB_N:
                    continue
                basis = sum(dq) / BB_N

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
                            # §7 invalidation
                            if nmid:
                                if direction == "long" and th_ >= nmid + nsig:
                                    continue
                                if direction == "short" and tl_ <= nmid - nsig:
                                    continue
                            # §7 location
                            if h4:
                                rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                                if rh > rl:
                                    pos = (tc_ - rl) / (rh - rl)
                                    if direction == "long" and pos >= 1 - LOC_BAND:
                                        continue
                                    if direction == "short" and pos <= LOC_BAND:
                                        continue
                            # §6.5 RR floor, E1 entry, stop = wick +/- 1 tick
                            entry = basis
                            if direction == "long":
                                stop = tl_ - TICK
                                if entry <= stop:
                                    continue
                                R = entry - stop
                                cs = [x - FRONT_RUN_F for x in menu if x - FRONT_RUN_F > entry]
                                opp = [x for x in lv if x[0] > entry]
                            else:
                                stop = th_ + TICK
                                if stop <= entry:
                                    continue
                                R = stop - entry
                                cs = [x + FRONT_RUN_F for x in menu if x + FRONT_RUN_F < entry]
                                opp = [x for x in lv if x[0] < entry]
                            if not cs:
                                continue
                            tgt = min(cs) if direction == "long" else max(cs)
                            avail_R = (tgt - entry) / R if direction == "long" else (entry - tgt) / R
                            if avail_R < RR_FLOOR:
                                continue

                            # ---- forward excursion, bar i+1 .. session close ----
                            mfe = mae = 0.0
                            t_mfe = t_mae = 0
                            hit_stop = False
                            res_min = None
                            j = i + 1
                            while j <= last_idx:
                                if j not in hi_arr:
                                    j += 1
                                    continue
                                hh, ll = hi_arr[j], lo_arr[j]
                                if direction == "long":
                                    up, dn = hh - entry, entry - ll
                                else:
                                    up, dn = entry - ll, hh - entry
                                if up > mfe:
                                    mfe, t_mfe = up, j - i
                                if dn > mae:
                                    mae, t_mae = dn, j - i
                                if not hit_stop and dn >= R:
                                    hit_stop = True
                                    res_min = j - i
                                    break
                                if up >= (tgt - entry if direction == "long" else entry - tgt):
                                    res_min = j - i
                                    break
                                j += 1

                            mfe_R, mae_R = mfe / R, mae / R
                            headroom = min(abs(x[0] - entry) for x in opp) if opp else None
                            conv = (1 if len(types) >= 3 else 0) \
                                 + (1 if not counter else 0) \
                                 + (1 if avail_R >= 2.0 else 0)

                            cands.append({
                                "session_date": d, "signal_minute": cm,
                                "signal_hhmm": f"{cm//60:02d}:{cm%60:02d}",
                                "direction": direction, "trigger_reading": mode,
                                "trigger_kind": kind, "entry_tf": tf,
                                "warmup_treatment": warm,
                                "conviction_score": conv,
                                "cluster_types": ",".join(sorted(types)),
                                "cluster_size": nlev,
                                "cluster_span_points": round(cl_hi - cl_lo, 4),
                                "htf_flag": flag, "counter_trend": counter,
                                "entry_price": round(entry, 4),
                                "spec_stop_price": round(stop, 4),
                                "stop_distance_points": round(R, 4),
                                "stop_distance_atr": round(R / atr_d, 4) if atr_d else None,
                                "headroom_points": round(headroom, 4) if headroom else None,
                                "available_R_to_spec_target": round(avail_R, 4),
                                "mfe_points": round(mfe, 4), "mfe_R": round(mfe_R, 4),
                                "mae_points": round(mae, 4), "mae_R": round(mae_R, 4),
                                "minutes_to_mfe": t_mfe, "minutes_to_mae": t_mae,
                                "reached_1R": (mfe_R >= 1.0) and not (mae_R >= 1.0 and t_mae < t_mfe),
                                "reached_1_5R": (mfe_R >= 1.5) and not (mae_R >= 1.0 and t_mae < t_mfe),
                                "reached_2R": (mfe_R >= 2.0) and not (mae_R >= 1.0 and t_mae < t_mfe),
                                "reached_3R": (mfe_R >= 3.0) and not (mae_R >= 1.0 and t_mae < t_mfe),
                                "hit_spec_stop": hit_stop,
                                "resolved_before_close": res_min is not None,
                                "minutes_to_resolution": res_min,
                                "tod_bucket": f"{cm//60:02d}:{(cm%60)//30*30:02d}",
                                "year": d[:4], "day_of_week": datetime.fromisoformat(d).strftime("%a"),
                                "days_to_roll": days_to_roll,
                                "lookback_spans_roll": spans_roll,
                                "initial_balance_range": round(ib_hi - ib_lo, 4) if ib_hi else None,
                                "session_range_to_signal": round(sess_hi - sess_lo, 4),
                            })
    return cands


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    SHARDS.mkdir(parents=True, exist_ok=True)
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    print(f"[{time.strftime('%H:%M:%S')}] workbench sessions: {len(days)} "
          f"({days[0]} .. {days[-1]}); holdout NOT addressed")

    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d])[0]
        if prev and s != prev:
            rolls.add(d)
        prev = s
    skip = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    failed, skipped = [], collections.Counter()
    prev_hl, prev_close, trs = None, None, collections.deque(maxlen=14)
    total = 0
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
            try:
                dtr = min((abs((datetime.fromisoformat(r) - datetime.fromisoformat(d)).days)
                           for r in rolls), default=999)
                c = process_session(d, bars, sorted(sym_of[d])[0], dtr, dtr <= 1, prev_hl, atr_d)
                if c is None:
                    skipped["holiday / short session"] += 1
                else:
                    shard.write_text(json.dumps(c))
                    total += len(c)
            except Exception as e:
                failed.append((d, f"{type(e).__name__}: {e}"))
        trs.append(tr); prev_close = list(bars.values())[-1][3]
        prev_hl = (hi, lo)
        if n % 50 == 0 or n == len(days):
            el = time.time() - t0
            print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(days)} sessions, "
                  f"{total} candidates, {el:.0f}s elapsed, "
                  f"project {el/n*len(days)/60:.1f} min total")

    rows = []
    for f in sorted(SHARDS.glob("*.json")):
        rows.extend(json.loads(f.read_text()))
    if rows:
        cols = {k: [r.get(k) for r in rows] for k in rows[0]}
        pq.write_table(pa.table(cols), OUT / "candidates.parquet", compression="snappy")
    print(f"\n[{time.strftime('%H:%M:%S')}] DONE  candidates={len(rows)}  "
          f"sessions_processed={len(days)-sum(skipped.values())-len(failed)}  "
          f"skipped={dict(skipped)}  failed={len(failed)}  "
          f"runtime={(time.time()-t0)/60:.1f} min")
    if failed:
        print("FAILURES:")
        for d, e in failed:
            print(f"   {d}: {e}")


if __name__ == "__main__":
    main()
