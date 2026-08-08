#!/usr/bin/env python3
"""PARITY GATE STAGE B — detector dump for 2025-01-22, instant = close of the 09:49 bar.

READ-ONLY. Nothing in the detector is modified. This script re-executes the SEALED
engine's state evolution (stage2_smoke.signal_candidates) verbatim, adding dump hooks,
and then calls the real signal_candidates() to confirm the trigger decision matches.
No outcome field is touched; the sealed parquet is never opened.

Instant: minute-of-day 589 (09:49) has just closed, so the detector's close-minute
label is cm = 590 = "09:50". Only TFs with 590 % tf == 0 evaluate at that label
(1m, 2m, 5m); the 3m bar last closed at cm = 588 and its state is dumped there.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, FRACTAL_N, CLUSTER_TOL)
from vwapbb_opportunity import trig, assert_workbench
from vwapbb_a7_selector import ladder, MIN_STOP, RR_FLOOR, FRONT_RUN_F, LOC_BAND, TICK
import stage2_smoke as ENG

DATE = "2025-01-22"
INSTANT_MM = 9 * 60 + 49          # last completed 1-minute bar
CM = INSTANT_MM + 1               # detector close-minute label = 09:50
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "parity_p2_detector.json"


def swings(bars15, n=FRACTAL_N):
    """Same fractal construction htf_flag() uses, but returning the swing list with
    the index so the reading can be compared, not just the flag."""
    hs, lo = [], []
    for i in range(n, len(bars15) - n):
        h, l = bars15[i][1], bars15[i][2]
        if all(h > bars15[j][1] for j in range(i - n, i)) and \
           all(h > bars15[j][1] for j in range(i + 1, i + n + 1)):
            hs.append((i, h))
        if all(l < bars15[j][2] for j in range(i - n, i)) and \
           all(l < bars15[j][2] for j in range(i + 1, i + n + 1)):
            lo.append((i, l))
    return hs, lo


def main():
    assert_workbench(DATE)
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= ENG.WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    k = days.index(DATE)
    prev = days[k - 1]
    pb = sess[prev]
    prev_hl = (max(b[1] for b in pb.values()), min(b[2] for b in pb.values()))

    bars = sess[DATE]
    D = {"date": DATE, "prev_session": prev,
         "contract": sorted(sym_of[DATE], key=ENG.contract_key),
         "prev_day_high_globex": prev_hl[0], "prev_day_low_globex": prev_hl[1],
         "prev_session_bars": len(pb), "session_bars": len(bars)}

    # ---- prior-session RTH-only H/L, for the §1c basis question (not used by the detector)
    rth_h, rth_l = -1e18, 1e18
    for i, b in pb.items():
        if RTH_OPEN - 1 <= minute_of_day(i) < RTH_CLOSE:
            rth_h, rth_l = max(rth_h, b[1]), min(rth_l, b[2])
    D["prev_day_high_rth_only"], D["prev_day_low_rth_only"] = rth_h, rth_l

    # ════════════════ state evolution, verbatim from stage2_smoke ════════════════
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    h4_win, acc4_win = collections.deque(maxlen=6), []      # provenance only
    sess_hi, sess_lo = -1e18, 1e18
    pre_hi, pre_lo = -1e18, 1e18                            # 18:00 -> 09:29, reporting only
    per_tf = {}

    instant_idx = (INSTANT_MM - 1080) % 1440       # session index of the 09:49 bar
    for i in sorted(bars):
        if i > instant_idx:
            break                                  # nothing after the instant is read
        o, h, l, c, v = bars[i]
        mm = minute_of_day(i)
        dv.add(h, l, c, v)
        if NY_VWAP_ANCHOR <= mm < RTH_CLOSE + 1:
            nv.add(h, l, c, v)
        nb = max(1, int((h - l) / POC_BIN) + 1)
        for kk in range(nb):
            poc[int((l + kk * POC_BIN) / POC_BIN)] += v / nb
        sess_hi, sess_lo = max(sess_hi, h), min(sess_lo, l)
        if mm >= 1080 or mm < NY_VWAP_ANCHOR:
            pre_hi, pre_lo = max(pre_hi, h), min(pre_lo, l)

        acc15.append((o, h, l, c))
        if (mm + 1) % 15 == 0:
            b15.append((acc15[0][0], max(x[1] for x in acc15),
                        min(x[2] for x in acc15), acc15[-1][3]))
            acc15 = []
        acc4.append((h, l))
        acc4_win.append(mm)
        if (mm + 1) % 240 == 0:
            h4.append((max(x[0] for x in acc4), min(x[1] for x in acc4)))
            h4_win.append((acc4_win[0], acc4_win[-1], len(acc4_win)))
            acc4, acc4_win = [], []

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
            sd = (sum((x - basis) ** 2 for x in bb[tf]) / BB_N) ** 0.5
            flag = htf_flag(b15)

            lv = [(basis, "bb"), (p, "poc")]
            for kk in (0, 1, 2, 3):
                lv.append((dmid + kk * dsig, "vwap"))
                if kk:
                    lv.append((dmid - kk * dsig, "vwap"))
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

            cl = cluster_levels(lv)
            hs, ls = swings(b15)
            rec = {
                "cm": cm, "bar_mm": mm, "tf": tf,
                "bar": {"open": to_, "high": th_, "low": tl_, "close": tc_},
                "bb": {"basis": basis, "upper2": basis + 2 * sd, "lower2": basis - 2 * sd,
                       "sigma": sd, "n": len(bb[tf])},
                "daily_vwap": {"mid": dmid, "sigma": dsig,
                               **{f"{s}{kk}": dmid + s_ * kk * dsig
                                  for kk in (1, 2, 3) for s, s_ in (("+", 1), ("-", -1))}},
                "ny_vwap": {"mid": nmid, "sigma": nsig,
                            **{f"{s}{kk}": (nmid + s_ * kk * nsig) if nmid else None
                               for kk in (1, 2, 3) for s, s_ in (("+", 1), ("-", -1))}},
                "poc": p, "sess_hi": sess_hi, "sess_lo": sess_lo,
                "pre_hi": pre_hi, "pre_lo": pre_lo,
                "htf_flag": flag,
                "swing_highs": [(b15_i, hv) for b15_i, hv in hs][-4:],
                "swing_lows": [(b15_i, lv_) for b15_i, lv_ in ls][-4:],
                "n_b15": len(b15),
                "h4_blocks": [list(x) for x in h4],
                "h4_windows": [list(x) for x in h4_win],
                "h4_high": max(x[0] for x in h4) if h4 else None,
                "h4_low": min(x[1] for x in h4) if h4 else None,
                "levels": sorted([(round(pp, 4), tt) for pp, tt in lv]),
                "menu": sorted(round(x, 4) for x in menu),
                "n_in_body": nib,
                "clusters": [{"lo": a, "hi": b_, "types": sorted(t), "n": n_}
                             for a, b_, t, n_ in cl],
            }
            trg = []
            for a, b_, t, n_ in cl:
                for direction, kind in sorted(trig(to_, th_, tl_, tc_, a, b_, nib, "A")):
                    trg.append({"cluster": [a, b_], "direction": direction, "kind": kind,
                                "types": sorted(t)})
            rec["triggers"] = trg
            # filter states, evaluated for BOTH directions so a null is explainable
            fs = {}
            for direction in ("long", "short"):
                counter = (flag == "uptrend" and direction == "short") or \
                          (flag == "downtrend" and direction == "long")
                inval = None
                if nmid:
                    inval = (th_ >= nmid + nsig) if direction == "long" else (tl_ <= nmid - nsig)
                pos = None
                loc = None
                if h4:
                    rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                    if rh > rl:
                        pos = (tc_ - rl) / (rh - rl)
                        loc = (pos >= 1 - LOC_BAND) if direction == "long" else (pos <= LOC_BAND)
                fs[direction] = {"counter_trend": counter, "types_needed": 3 if counter else 2,
                                 "invalidation_blocks": inval,
                                 "range_position": pos, "location_blocks": loc}
            rec["filters"] = fs
            per_tf.setdefault(tf, []).append(rec)

    D["per_tf_last"] = {str(tf): v[-1] for tf, v in per_tf.items() if v}
    D["cm_evaluated"] = {str(tf): [r["cm"] for r in v][-3:] for tf, v in per_tf.items()}

    # ═════════════ cross-check against the real sealed engine ═════════════
    audit = collections.Counter()
    real = ENG.signal_candidates(bars, prev_hl, audit)
    D["engine_audit"] = dict(audit)
    D["engine_candidate_minutes"] = sorted(real.keys()) if real else []
    D["engine_candidates_at_instant"] = [
        {kk: vv for kk, vv in c.items() if kk != "bar"} for c in (real.get(CM, []) if real else [])]
    D["engine_candidates_0936_0950"] = {
        str(m): [{"tf": c["tf"], "dir": c["direction"], "kind": c["kind"],
                  "entry": c["entry"], "stop": c["stop_px"], "tgt": c["tgt_px"]}
                 for c in real[m]]
        for m in sorted(real) if FIRST_SIG <= m <= CM} if real else {}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(D, indent=1, default=str))
    print(f"written {OUT}")
    print(f"contract {D['contract']}  prev session {prev}")
    print(f"prior-day Globex H/L {prev_hl}   RTH-only H/L ({rth_h}, {rth_l})")
    for tf in sorted(per_tf):
        r = per_tf[tf][-1]
        print(f"\n--- TF {tf}m  last close cm={r['cm']} ({r['cm']//60:02d}:{r['cm']%60:02d}) ---")
        print(f"  bar O{r['bar']['open']} H{r['bar']['high']} L{r['bar']['low']} C{r['bar']['close']}")
        print(f"  BB basis {r['bb']['basis']:.2f}  up {r['bb']['upper2']:.2f}  lo {r['bb']['lower2']:.2f}")
        print(f"  dVWAP {r['daily_vwap']['mid']:.2f} sig {r['daily_vwap']['sigma']:.2f}   "
              f"nVWAP {r['ny_vwap']['mid']:.2f} sig {r['ny_vwap']['sigma']:.2f}")
        print(f"  POC {r['poc']}  sess {r['sess_lo']}/{r['sess_hi']}  htf {r['htf_flag']}")
        print(f"  4h {r['h4_low']}/{r['h4_high']}  blocks {r['h4_windows']}")
        print(f"  clusters {[(round(c['lo'],2), round(c['hi'],2), c['types']) for c in r['clusters']]}")
        print(f"  triggers {r['triggers']}")
        print(f"  filters {r['filters']}")
    print(f"\nengine candidate minutes (whole session): {D['engine_candidate_minutes']}")
    print(f"engine candidates at cm={CM}: {D['engine_candidates_at_instant']}")
    print(f"engine audit: {D['engine_audit']}")


if __name__ == "__main__":
    main()
