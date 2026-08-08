#!/usr/bin/env python3
"""The two missing entry criteria, plus the §7 invalidation threshold, as
MEASURABLE FLAGS — not as adopted rules.

One pass over the workbench. For every candidate that survives the current filter
stack, record:

    largest_unfilled_imbalance   points of unfilled 3-candle FVG opposing the
                                 trade, left by the move price just made
    bars_since_sweep             bars since a confirmed swing extreme on the
                                 entry TF was traded through and reclaimed
    ext_vs_ny1s / ext_vs_ny2s    how far the trigger candle reaches past the
                                 NY VWAP band, at BOTH thresholds

Then frequency is counted for every combination in post-processing, from one run.

NOTHING IS ADOPTED. No filter is switched on, no threshold is chosen, no outcome
is read. The frozen spec is unchanged and the sealed result is untouched. This
produces the numbers Angus needs to state his own rules, and the definitions
below are DRAFTS for him to accept, amend or reject.

N_trials remains 0.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, FRACTAL_N)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import ladder, MIN_STOP, RR_FLOOR, FRONT_RUN_F, LOC_BAND, TICK

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
READING = "A"


class TFState:
    """Per-entry-timeframe state: closed bars, confirmed fractal swings, open
    imbalances, and sweep recency. All strictly causal — a swing at bar j is
    recorded only once bar j+FRACTAL_N exists, exactly as htf_flag requires."""

    def __init__(self):
        self.bars = []                 # (o,h,l,c)
        self.sw_hi = []                # (index, level) confirmed
        self.sw_lo = []
        self.fvg_up = []               # (lo, hi) unfilled bullish gaps
        self.fvg_dn = []
        self.last_sweep_lo = None      # bar index of last swing-low sweep
        self.last_sweep_hi = None

    def push(self, o, h, l, c):
        b = self.bars
        b.append((o, h, l, c))
        n = len(b) - 1

        # --- confirmed fractal swings, N bars either side ---
        k = n - FRACTAL_N
        if k >= FRACTAL_N:
            w = b[k - FRACTAL_N:k + FRACTAL_N + 1]
            mid = FRACTAL_N
            if all(w[mid][1] > w[j][1] for j in range(len(w)) if j != mid):
                self.sw_hi.append((k, w[mid][1]))
            if all(w[mid][2] < w[j][2] for j in range(len(w)) if j != mid):
                self.sw_lo.append((k, w[mid][2]))

        # --- three-candle imbalance (fair value gap) ---
        if n >= 2:
            if b[n][2] > b[n - 2][1]:                       # bullish gap
                self.fvg_up.append([b[n - 2][1], b[n][2]])
            if b[n][1] < b[n - 2][2]:                       # bearish gap
                self.fvg_dn.append([b[n][1], b[n - 2][2]])
        # fill them: a gap is filled when price trades back through it entirely
        self.fvg_up = [g for g in self.fvg_up if l > g[0]]
        self.fvg_dn = [g for g in self.fvg_dn if h < g[1]]

        # --- sweeps: trade through a confirmed swing, close back ---
        for _, lvl in self.sw_lo[-8:]:
            if l < lvl and c > lvl:
                self.last_sweep_lo = n
                break
        for _, lvl in self.sw_hi[-8:]:
            if h > lvl and c < lvl:
                self.last_sweep_hi = n
                break

    def unfilled_against(self, direction):
        """For a LONG, the concern is unfilled bullish gaps BELOW — space the
        up-move left behind that Angus expects to be filled first. Mirrored for
        a short. Returns the largest such gap in points, 0.0 if none."""
        gs = self.fvg_up if direction == "long" else self.fvg_dn
        return max((g[1] - g[0] for g in gs), default=0.0)

    def bars_since_sweep(self, direction):
        """For a LONG we want stops taken BELOW then reclaimed -> a swing-low
        sweep. None if no qualifying sweep has ever occurred this session."""
        idx = self.last_sweep_lo if direction == "long" else self.last_sweep_hi
        return None if idx is None else (len(self.bars) - 1 - idx)


def run_session(d, bars, prev_hl):
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    st = {tf: TFState() for tf in TFS}
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
            st[tf].push(to_, th_, tl_, tc_)
            cm = mm + 1
            if cm < FIRST_SIG or cm > RTH_CLOSE or len(bb[tf]) < BB_N:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None or not nmid:
                continue
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            basis = sum(bb[tf]) / BB_N
            flag = htf_flag(b15)
            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                    sess_hi, sess_lo, nmid, nmid + nsig, nmid - nsig,
                    nmid + 2 * nsig, nmid - 2 * nsig]
            if prev_hl:
                menu += list(prev_hl)
            blo, bhi = min(to_, tc_), max(to_, tc_)
            nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)

            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):
                        continue
                    # §7 location (unchanged)
                    if h4:
                        rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                        if rh > rl:
                            pos = (tc_ - rl) / (rh - rl)
                            if direction == "long" and pos >= 1 - LOC_BAND:
                                continue
                            if direction == "short" and pos <= LOC_BAND:
                                continue
                    # A5 / A4 geometry (unchanged)
                    if direction == "long":
                        struct = tl_ - TICK
                        if basis <= struct:
                            continue
                        R = max(basis - struct, MIN_STOP)
                    else:
                        struct = th_ + TICK
                        if struct <= basis:
                            continue
                        R = max(struct - basis, MIN_STOP)
                    tgt = None
                    for x in ladder(menu, basis, direction, FRONT_RUN_F):
                        if abs(x - basis) / R >= RR_FLOOR:
                            tgt = x
                            break
                    if tgt is None:
                        continue
                    # ---- the three flags, recorded not applied ----
                    if direction == "long":
                        e1 = th_ - (nmid + nsig)
                        e2 = th_ - (nmid + 2 * nsig)
                    else:
                        e1 = (nmid - nsig) - tl_
                        e2 = (nmid - 2 * nsig) - tl_
                    out.append({
                        "session_date": d, "cm": cm, "tf": tf, "direction": direction,
                        "imb": round(st[tf].unfilled_against(direction), 4),
                        "sweep": st[tf].bars_since_sweep(direction),
                        "ext1": round(e1, 4), "ext2": round(e2, 4),
                    })
    return out


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev = set(), None
    MO = {"H": 3, "M": 6, "U": 9, "Z": 12}
    ck = lambda s: (int(s[-1]), MO.get(s[-2], 0))
    for d in days:
        s = sorted(sym_of[d], key=ck)[-1]
        if prev and ck(s) > ck(prev):
            rolls.add(d)
        prev = s
    after = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    rows, ns, prev_hl = [], 0, None
    for n, d in enumerate(days, 1):
        assert_workbench(d)
        bars = sess[d]
        hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        if d in rolls:
            prev_hl = None
        elif d not in after and len(sym_of[d]) == 1:
            r = run_session(d, bars, prev_hl)
            if r is not None:
                ns += 1
                rows.extend(r)
        if d not in rolls:
            prev_hl = hl
        if n % 150 == 0:
            print(f"  ...{n}/{len(days)}")

    (OUT / "missing_filters_flags.json").write_text(json.dumps(rows))
    print(f"\nsessions {ns}   candidates {len(rows)}   "
          f"baseline {len(rows)/ns:.3f}/session\n")

    def count(imb_max, sweep_max, ext_sigma):
        keep = []
        for r in rows:
            if imb_max is not None and r["imb"] > imb_max:
                continue
            if sweep_max is not None and (r["sweep"] is None or r["sweep"] > sweep_max):
                continue
            e = r["ext1"] if ext_sigma == 1 else r["ext2"]
            if e >= 0:
                continue
            keep.append(r)
        s1 = len({r["session_date"] for r in keep})
        return len(keep) / ns, s1 / ns

    print("=" * 88)
    print("FREQUENCY ONLY. No outcome is read. Nothing here is adopted.")
    print("=" * 88)
    print("\nBASELINE — current spec, invalidation at 1σ, no new filters")
    a, b = count(None, None, 1)
    print(f"   {a:.3f} candidates/session   {b:.3f} sessions with >=1")
    print("\nINVALIDATION THRESHOLD ALONE (spec marks this rule '[Hypothesis — test]')")
    for sig in (1, 2):
        a, b = count(None, None, sig)
        print(f"   at {sig}σ : {a:>7.3f} cand/session   {b:.3f} sessions with >=1")

    print("\nIMBALANCE FILTER — max unfilled opposing gap allowed, points")
    for lim in (None, 20.0, 10.0, 5.0, 2.0, 0.01):
        for sig in (1, 2):
            a, b = count(lim, None, sig)
            lab = "off" if lim is None else f"<= {lim}"
            print(f"   imb {lab:>7}  inval {sig}σ : {a:>7.3f} cand/sess  {b:.3f} sess")

    print("\nSWEEP FILTER — require a swing sweep within N entry-TF bars")
    for k in (None, 50, 20, 10, 5):
        for sig in (1, 2):
            a, b = count(None, k, sig)
            lab = "off" if k is None else f"<= {k} bars"
            print(f"   sweep {lab:>11}  inval {sig}σ : {a:>7.3f} cand/sess  {b:.3f} sess")

    print("\nBOTH, at a middle setting")
    for lim in (10.0, 5.0):
        for k in (20, 10):
            for sig in (1, 2):
                a, b = count(lim, k, sig)
                print(f"   imb<={lim:<5} sweep<={k:<3} inval {sig}σ : "
                      f"{a:>7.3f} cand/sess  {b:.3f} sess")

    print("\ndistributions, for choosing thresholds structurally rather than by result:")
    im = sorted(r["imb"] for r in rows)
    sw = sorted(r["sweep"] for r in rows if r["sweep"] is not None)
    print(f"   unfilled opposing gap, pts: 0 on {sum(1 for x in im if x==0)/len(im)*100:.1f}% "
          f"| p50 {im[len(im)//2]:.2f} | p90 {im[int(.9*len(im))]:.2f} | max {im[-1]:.2f}")
    print(f"   bars since a qualifying sweep: never {(len(rows)-len(sw))/len(rows)*100:.1f}% "
          f"| p25 {sw[len(sw)//4]} | p50 {sw[len(sw)//2]} | p90 {sw[int(.9*len(sw))]}")


if __name__ == "__main__":
    main()
