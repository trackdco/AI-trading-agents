#!/usr/bin/env python3
"""SIGNAL COUNT rev 3 — under amendments A4 (target rule) and A5 (minimum stop).

Identical to rev 2 in every respect EXCEPT the two amended rules:

  A5  §5.4  effective stop = max(wick + 1 tick, MIN_STOP)          MIN_STOP = 10.00 pt
  A4  §6.5  target = FIRST level walking outward whose front-run-adjusted
            distance clears the RR floor; skip only if no level clears it
            (rev 2 tested only the nearest level and skipped)

Cascade, in the spec's own order, reporting the count after each stage:
  0 raw trigger + §7 confluence minimum
  1 + §7 invalidation-at-entry
  2 + §7 location filter
  3 + §6.5 RR floor
  4 + §10 Vault max trades/day
  5 + §5.6 one position at a time

Run over the FULL workbench (rev 2 used a 150-session probe) so the result is
comparable to the gate-6 tripwire, which is denominated in 539 sessions.

Nothing is tuned. This is a frequency confirmation of two specification
amendments, not a search. No outcome is computed. N_trials remains 0.
"""
from __future__ import annotations

import collections
from vwapbb_signals import (build_sessions, minute_of_day, RunningVWAP, cluster_levels,
                            htf_flag, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, B_MIN, QUARTILE)

TICK = 0.25
MIN_STOP = 10.00            # §5.4 as amended — A5, 2026-08-08 [FIAT]
RR_FLOOR = 1.5              # §6.5
FRONT_RUN_F = 2.0           # §6.4 states "start 2-3"; 2 is the permissive end
MAX_TRADES_DAY = 3          # §10
HOLD_LOCKOUT_MIN = 30       # §1 "median trade resolves ~30 min" — approximation
LOC_BAND = 0.20             # PLACEHOLDER: "HTF range top" has no stated boundary
INVALIDATION_ON = True      # §7 marks this "[Hypothesis - test]", not a settled rule

PLACEHOLDERS = {
    "location band ('at HTF range top')": f"top/bottom {LOC_BAND:.0%} of trailing 4h range — NOT STATED IN SPEC",
    "front-run F": f"{FRONT_RUN_F} pts (spec: 'start 2-3'; low end chosen, most permissive)",
    "one-position lockout": f"{HOLD_LOCKOUT_MIN} min (spec §1: 'median trade resolves ~30 min')",
    "entry variant": "E1 = limit at BB MA (spec-1 Step 8 names W1/E1/V0 as defaults)",
}

READINGS = {"A": "penetrate cluster top, any wick",
            "B": "penetrate cluster fully, any wick",
            "C": "penetrate fully + wick >= 50% of range",
            "D": "as C, cluster must hold >=3 levels"}
STAGES = ["0 raw+confluence", "1 +invalidation", "2 +location", "3 +RR floor",
          "4 +Vault 3/day", "5 +one-at-a-time"]


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


def run(mode, days, sess, sym_of):
    counts = collections.Counter()
    nsess = 0
    for d in days:
        if len(sym_of[d]) > 1:
            continue
        bars = sess[d]
        rth = [i for i in sorted(bars) if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]
        if len(rth) < 300:
            continue
        nsess += 1

        dv, nv = RunningVWAP(), RunningVWAP()
        poc = collections.defaultdict(float)
        bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
        tfacc = {tf: [] for tf in TFS}
        b15, acc15 = [], []
        h4 = collections.deque(maxlen=6)        # trailing 4h context (6 x 4h = 1 day)
        acc4 = []
        sess_hi, sess_lo = -1e18, 1e18
        prev_hi, prev_lo = None, None
        stage_hits = {s: {} for s in STAGES}    # stage -> {close_min: tf}

        for i in sorted(bars):
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

                basis = sum(bb[tf]) / BB_N
                dmid, dsig = dv.value()
                nmid, nsig = nv.value()
                if dmid is None:
                    continue
                p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN

                lv = [(basis, "bb"), (p, "poc")]
                for k in (0, 1, 2, 3):
                    lv.append((dmid + k * dsig, "vwap"))
                    if k:
                        lv.append((dmid - k * dsig, "vwap"))
                if nmid:
                    lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]

                # target menu (§6): VWAP mid/+-1/+-2 sigma, POC, session + prior-day extremes
                menu = [dmid, dmid + dsig, dmid - dsig, dmid + 2 * dsig, dmid - 2 * dsig, p,
                        sess_hi, sess_lo]
                if nmid:
                    menu += [nmid, nmid + nsig, nmid - nsig, nmid + 2 * nsig, nmid - 2 * nsig]
                if prev_hi:
                    menu += [prev_hi, prev_lo]

                flag = htf_flag(b15)
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

                        def mark(stage):
                            if stage_hits[stage].get(cm, 0) < tf:
                                stage_hits[stage][cm] = tf
                        mark(STAGES[0])

                        # --- 1. §7 invalidation-at-entry -------------------
                        if INVALIDATION_ON and nmid:
                            if direction == "long" and th_ >= nmid + nsig:
                                continue
                            if direction == "short" and tl_ <= nmid - nsig:
                                continue
                        mark(STAGES[1])

                        # --- 2. §7 location --------------------------------
                        if h4:
                            rh = max(x[0] for x in h4)
                            rl = min(x[1] for x in h4)
                            if rh > rl:
                                pos = (tc_ - rl) / (rh - rl)
                                if direction == "long" and pos >= 1 - LOC_BAND:
                                    continue
                                if direction == "short" and pos <= LOC_BAND:
                                    continue
                        mark(STAGES[2])

                        # --- 3. §5.4 (A5) stop, then §6.5 (A4) RR floor ----
                        entry = basis                                   # E1
                        if direction == "long":
                            stop = tl_ - TICK
                            # A5 floors a stop that is already structural. It does
                            # NOT rescue a geometrically invalid setup — if E1's
                            # entry is on the wrong side of the wick extreme the
                            # trigger is still skipped, exactly as in rev 2.
                            if entry <= stop:
                                continue
                            R = max(entry - stop, MIN_STOP)
                            cands = sorted(x - FRONT_RUN_F for x in menu
                                           if x - FRONT_RUN_F > entry)
                            dists = [x - entry for x in cands]
                        else:
                            stop = th_ + TICK
                            if stop <= entry:
                                continue
                            R = max(stop - entry, MIN_STOP)
                            cands = sorted((x + FRONT_RUN_F for x in menu
                                            if x + FRONT_RUN_F < entry), reverse=True)
                            dists = [entry - x for x in cands]
                        # A4: walk outward, take the FIRST level that clears the
                        # floor. "nearest VALID target" — valid means it clears.
                        rr = 0.0
                        for dd in dists:
                            if dd / R >= RR_FLOOR:
                                rr = dd / R
                                break
                        if rr < RR_FLOOR:
                            continue
                        mark(STAGES[3])

        # --- 4/5 Vault caps, applied to the post-RR survivors --------------
        surv = sorted(stage_hits[STAGES[3]])
        stage_hits[STAGES[4]] = {cm: stage_hits[STAGES[3]][cm] for cm in surv[:MAX_TRADES_DAY]}
        ser, last = [], -10**9
        for cm in surv:
            if cm - last >= HOLD_LOCKOUT_MIN:
                ser.append(cm)
                last = cm
            if len(ser) >= MAX_TRADES_DAY:
                break
        stage_hits[STAGES[5]] = {cm: stage_hits[STAGES[3]][cm] for cm in ser}

        for s in STAGES:
            counts[s] += len(stage_hits[s])
    return counts, nsess


if __name__ == "__main__":
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= "2025-01-31"]   # FULL workbench
    print("SIGNAL COUNT rev 3 — under amendments A4 + A5. Entry logic only, no outcomes.")
    print(f"FULL workbench; holdout never addressed.")
    print(f"A5 minimum stop = {MIN_STOP:.2f} pt   |   A4 target = first level clearing {RR_FLOOR}R\n")
    print("DECLARED PLACEHOLDERS (spec states no value):")
    for k, v in PLACEHOLDERS.items():
        print(f"   {k:38s} {v}")
    print()
    hdr = f"{'stage':22s}" + "".join(f"{r:>14}" for r in READINGS)
    res = {}
    for m in READINGS:
        res[m], ns = run(m, days, sess, sym_of)
    print(f"probe sessions: {ns}\n")
    print(hdr)
    print("-" * len(hdr))
    for s in STAGES:
        print(f"{s:22s}" + "".join(f"{res[m][s]/ns:>14.2f}" for m in READINGS))
    print("-" * len(hdr))
    print(f"{'total reduction':22s}" +
          "".join(f"{(1-res[m][STAGES[-1]]/max(1,res[m][STAGES[0]]))*100:>13.1f}%" for m in READINGS))
    print(f"\n{'per-filter reduction (%% of stage-0)':22s}")
    for j in range(1, len(STAGES)):
        print(f"  {STAGES[j]:20s}" +
              "".join(f"{(res[m][STAGES[j-1]]-res[m][STAGES[j]])/max(1,res[m][STAGES[0]])*100:>13.1f}%"
                      for m in READINGS))
    print(f"\nhand-log benchmark: 1.00 signals/session    gate-6 tripwire: 0.4862")
    for m in READINGS:
        v = res[m][STAGES[-1]] / ns
        print(f"   reading {m}: {v:.3f} trades/session  ->  {'CLEARS' if v >= 0.4862 else 'FAILS'} the tripwire")
