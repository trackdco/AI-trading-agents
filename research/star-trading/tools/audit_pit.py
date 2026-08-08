#!/usr/bin/env python3
"""STAGE 1 — POINT-IN-TIME AUDIT. Blocking.

Method: a deliberately naive REFERENCE implementation, written independently of
the detector and recomputed from scratch over an explicit bar slice at each test
minute. Comparing the detector's incremental accumulators against a second
incremental implementation would let a shared bug pass; a plain loop over a slice
cannot share the detector's state bugs.

THREE COMPARISONS per indicator per test minute:

  A        reference over bars with OPEN <= T-1  — everything complete at T.
           This is the only correct value.
  B_full   reference over the WHOLE session, read at T. The accumulating-
           indicator failure mode: compute once, index back.
  A_plus1  reference over bars with OPEN <= T. One bar of lookahead. This is
           the close-label off-by-one failure mode, and it is the one a
           full-session test cannot see.
  D        what the detector actually used, dumped from an instrumented run.

DISCRIMINATING is reported separately for each comparison. For ROLLING
indicators (BB, ATR) B_full indexed at T equals A by construction — that is
stated, not reported as a pass — so those are tested by A_plus1, which does
discriminate.

CONTAMINATED = D matches B_full or A_plus1 where it differs from A.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
import math
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, FRACTAL_N)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END

TOL = 1e-6
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"

ROLLING = {"bb_basis", "atr_tf"}          # B_full == A by construction
STATIC = {"prev_hi", "prev_lo"}           # must not track the current session


# ════════════════════════════════════════════════════════════════════
# REFERENCE IMPLEMENTATION — naive, slice-based, no shared state
# ════════════════════════════════════════════════════════════════════
def ref_vwap(bars, idxs):
    pv = pv2 = vol = 0.0
    for i in idxs:
        o, h, l, c, v = bars[i]
        tp = (h + l + c) / 3.0
        pv += tp * v
        pv2 += tp * tp * v
        vol += v
    if vol <= 0:
        return None, None
    m = pv / vol
    var = pv2 / vol - m * m
    return m, (math.sqrt(var) if var > 0 else 0.0)


def ref_poc(bars, idxs):
    bins = collections.defaultdict(float)
    for i in idxs:
        o, h, l, c, v = bars[i]
        nb = max(1, int((h - l) / POC_BIN) + 1)
        share = v / nb
        for k in range(nb):
            bins[int((l + k * POC_BIN) / POC_BIN)] += share
    if not bins:
        return None
    return max(bins.items(), key=lambda kv: kv[1])[0] * POC_BIN


def ref_range(bars, idxs):
    return (max(bars[i][1] for i in idxs), min(bars[i][2] for i in idxs))


def ref_tf_bars(bars, idxs, tf):
    out, acc = [], []
    for i in idxs:
        o, h, l, c, v = bars[i]
        acc.append((o, h, l, c))
        if (minute_of_day(i) + 1) % tf == 0:
            out.append((acc[0][0], max(x[1] for x in acc),
                        min(x[2] for x in acc), acc[-1][3]))
            acc = []
    return out


def ref_bb(bars, idxs, tf):
    tb = ref_tf_bars(bars, idxs, tf)
    if len(tb) < BB_N:
        return None
    return sum(x[3] for x in tb[-BB_N:]) / BB_N


def ref_atr(bars, idxs, tf, n=20):
    tb = ref_tf_bars(bars, idxs, tf)
    if len(tb) < n + 1:
        return None
    trs = []
    for k in range(1, len(tb)):
        pc = tb[k - 1][3]
        trs.append(max(tb[k][1] - tb[k][2], abs(tb[k][1] - pc), abs(tb[k][2] - pc)))
    return sum(trs[-n:]) / n


def ref_periodic(bars, idxs, period, hl_only=False):
    out, acc = [], []
    for i in idxs:
        o, h, l, c, v = bars[i]
        acc.append((h, l) if hl_only else (o, h, l, c))
        if (minute_of_day(i) + 1) % period == 0:
            if hl_only:
                out.append((max(x[0] for x in acc), min(x[1] for x in acc)))
            else:
                out.append((acc[0][0], max(x[1] for x in acc),
                            min(x[2] for x in acc), acc[-1][3]))
            acc = []
    return out


# ════════════════════════════════════════════════════════════════════
# INSTRUMENTED DETECTOR — verbatim accumulator structure, dumps value_D
# ════════════════════════════════════════════════════════════════════
def detector_dump(bars, prev_hl, want):
    idxs = sorted(bars)
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    tfbars = {tf: [] for tf in TFS}
    tfatr = {tf: collections.deque(maxlen=20) for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    got = {}

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
            tb = tfbars[tf]
            if tb:
                pc = tb[-1][3]
                tfatr[tf].append(max(th_ - tl_, abs(th_ - pc), abs(tl_ - pc)))
            tb.append((to_, th_, tl_, tc_))
            bb[tf].append(tc_)
            cm = mm + 1
            if (cm, tf) not in want or len(bb[tf]) < BB_N:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            got[(cm, tf)] = {
                "bar_index": i, "bar_open_minute": mm,
                "dvwap_mid": dmid, "dvwap_sig": dsig,
                "nvwap_mid": nmid, "nvwap_sig": nsig,
                "bb_basis": sum(bb[tf]) / BB_N,
                "poc": max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN if poc else None,
                "sess_hi": sess_hi, "sess_lo": sess_lo,
                "htf_flag": htf_flag(b15),
                "atr_tf": (sum(tfatr[tf]) / len(tfatr[tf])
                           if len(tfatr[tf]) >= 20 else None),
                "h4_hi": max(x[0] for x in h4) if h4 else None,
                "h4_lo": min(x[1] for x in h4) if h4 else None,
                "prev_hi": prev_hl[0] if prev_hl else None,
                "prev_lo": prev_hl[1] if prev_hl else None,
            }
    return got


# ════════════════════════════════════════════════════════════════════
def pick_test_minutes(sess, sym_of, days, n_target=20):
    """Real signal minutes spread across the sample, and deliberately spread
    across the SESSION too — an all-10:05 sample would never discriminate the
    session-range indicators."""
    picks, seen = [], set()
    # sweep the day so late-session minutes are represented
    windows = [(FIRST_SIG + 30, 10 * 60 + 30), (10 * 60 + 30, 12 * 60),
               (12 * 60, 14 * 60), (14 * 60, 15 * 60 + 55)]
    # one pick per equal-width block of the sample, so the 20 minutes span
    # 2023-01 .. 2025-01 rather than clustering at whichever end we scan first
    blocks = [days[j * len(days) // n_target:(j + 1) * len(days) // n_target]
              for j in range(n_target)]
    cand_days = [d for blk in blocks for d in blk[:6]]
    wi, per_block = 0, {}
    for bidx, blk in enumerate(blocks):
        per_block[bidx] = 0
    def block_of(dd):
        for bidx, blk in enumerate(blocks):
            if dd in blk:
                return bidx
        return -1
    for d in cand_days:
        if len(picks) >= n_target:
            break
        bidx = block_of(d)
        if per_block.get(bidx, 0) >= 1:
            continue
        if len(sym_of[d]) > 1 or d in seen:
            continue
        bars = sess[d]
        if len([i for i in sorted(bars)
                if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
            continue
        wlo, whi = windows[wi % len(windows)]
        found = None
        dv, nv = RunningVWAP(), RunningVWAP()
        poc = collections.defaultdict(float)
        bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
        tfacc = {tf: [] for tf in TFS}
        for i in sorted(bars):
            if found:
                break
            o, h, l, c, v = bars[i]
            mm = minute_of_day(i)
            dv.add(h, l, c, v)
            if NY_VWAP_ANCHOR <= mm < RTH_CLOSE + 1:
                nv.add(h, l, c, v)
            nb = max(1, int((h - l) / POC_BIN) + 1)
            for k in range(nb):
                poc[int((l + k * POC_BIN) / POC_BIN)] += v / nb
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
                if not (wlo <= cm < whi) or len(bb[tf]) < BB_N:
                    continue
                dmid, dsig = dv.value()
                if dmid is None:
                    continue
                basis = sum(bb[tf]) / BB_N
                p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
                lv = [(basis, "bb"), (p, "poc")]
                for k in (0, 1, 2, 3):
                    lv.append((dmid + k * dsig, "vwap"))
                    if k:
                        lv.append((dmid - k * dsig, "vwap"))
                blo, bhi = min(to_, tc_), max(to_, tc_)
                nib = sum(1 for pp, _ in lv if blo <= pp <= bhi)
                for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                    if trig(to_, th_, tl_, tc_, cl_lo, cl_hi, nib, "A"):
                        found = (cm, tf)
                        break
                if found:
                    break
        if found:
            picks.append((d, found[0], found[1]))
            seen.add(d)
            per_block[bidx] = per_block.get(bidx, 0) + 1
            wi += 1
    return picks


def cmp(a, b, tol=TOL):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return abs(a - b) <= tol


FIELDS = [
    ("dvwap_mid", "daily VWAP mid"), ("dvwap_sig", "daily VWAP sigma"),
    ("nvwap_mid", "NY VWAP mid"), ("nvwap_sig", "NY VWAP sigma"),
    ("poc", "POC (volume profile)"), ("sess_hi", "session high"),
    ("sess_lo", "session low"), ("bb_basis", "BB basis (entry TF)"),
    ("atr_tf", "ATR(20) entry TF"), ("htf_flag", "HTF classification"),
    ("h4_hi", "4h range high"), ("h4_lo", "4h range low"),
    ("prev_hi", "prior-day high"), ("prev_lo", "prior-day low"),
]


def build_refs(bars, idxs, bi, tf, prev_hl):
    """Return (A, B_full, A_plus1) dicts for one test minute.
    A       : bars with index <= bi              (open <= T-1, all complete at T)
    A_plus1 : bars with index <= bi+1            (one bar of lookahead)
    B_full  : the whole session
    """
    def pack(sl, label):
        ny = [i for i in sl if NY_VWAP_ANCHOR <= minute_of_day(i) < RTH_CLOSE + 1]
        dm, ds = ref_vwap(bars, sl)
        nm, ns = ref_vwap(bars, ny)
        rh, rl = ref_range(bars, sl)
        b15 = ref_periodic(bars, sl, 15)
        h4 = ref_periodic(bars, sl, 240, hl_only=True)[-6:]
        # prior-day: A/A_plus1 use the true prior session; B_full models the
        # failure mode of recomputing it from the CURRENT session
        if label == "B":
            ph, pl = ref_range(bars, idxs)
        else:
            ph, pl = (prev_hl if prev_hl else (None, None))
        return {
            "dvwap_mid": dm, "dvwap_sig": ds, "nvwap_mid": nm, "nvwap_sig": ns,
            "poc": ref_poc(bars, sl), "sess_hi": rh, "sess_lo": rl,
            "bb_basis": ref_bb(bars, sl, tf), "atr_tf": ref_atr(bars, sl, tf),
            "htf_flag": htf_flag(b15),
            "h4_hi": max(x[0] for x in h4) if h4 else None,
            "h4_lo": min(x[1] for x in h4) if h4 else None,
            "prev_hi": ph, "prev_lo": pl,
        }

    up = [i for i in idxs if i <= bi]
    up1 = [i for i in idxs if i <= bi + 1]
    A = pack(up, "A")
    Ap = pack(up1, "A1")
    B = pack(idxs, "B")
    # rolling indicators: B_full positionally indexed at T is A by construction
    for k in ROLLING:
        B[k] = A[k]
    return A, B, Ap


def fractal_unit_test():
    """A swing at 15m bar j must not be knowable until j+N. Synthetic, decisive."""
    n = FRACTAL_N
    base = [(100, 101, 99, 100)] * (2 * n + 1)
    spike = list(base) + [(100, 200, 99, 100)]          # extreme high is the LAST bar
    def swings(b15):
        hs = []
        for i in range(n, len(b15) - n):
            h = b15[i][1]
            if all(h > b15[j][1] for j in range(i - n, i)) and \
               all(h > b15[j][1] for j in range(i + 1, i + n + 1)):
                hs.append(i)
        return hs
    now = swings(spike)
    later = swings(spike + [(100, 101, 99, 100)] * n)
    idx_last = len(spike) - 1
    return {
        "spike_counted_immediately": idx_last in now,
        "spike_counted_after_N_more": idx_last in later,
        "pass": (idx_last not in now) and (idx_last in later),
    }


def close_label_test(bars, bi, cm):
    """The bar the detector last consumed must OPEN at T-1 and close at T."""
    return {
        "last_bar_open_minute": minute_of_day(bi),
        "signal_close_minute": cm,
        "pass": (minute_of_day(bi) + 1) % 1440 == cm % 1440,
    }


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    print("=" * 108)
    print("STAGE 1 — POINT-IN-TIME AUDIT")
    print("=" * 108)
    print(f"workbench {len(days)} sessions ({days[0]}..{days[-1]}); holdout NOT addressed\n")

    prev_hl_map, prev = {}, None
    for d in days:
        prev_hl_map[d] = prev
        b = sess[d]
        prev = (max(x[1] for x in b.values()), min(x[2] for x in b.values()))

    picks = pick_test_minutes(sess, sym_of, days, 20)
    print(f"test minutes: {len(picks)}, spread across the sample AND across the session")
    for d, cm, tf in picks:
        print(f"   {d}  {cm//60:02d}:{cm%60:02d}  tf={tf}m")

    tally = {k: {"n": 0,
                 "disc_B": 0, "disc_A1": 0,
                 "D_eq_A": 0, "leak_full": 0, "leak_one": 0, "neither": 0}
             for k, _ in FIELDS}
    rows, cl_fails = [], []

    for d, cm, tf in picks:
        bars = sess[d]
        idxs = sorted(bars)
        dump = detector_dump(bars, prev_hl_map[d], {(cm, tf)})
        if (cm, tf) not in dump:
            print(f"  !! no dump for {d} {cm} tf{tf}")
            continue
        D = dump[(cm, tf)]
        bi = D["bar_index"]
        clt = close_label_test(bars, bi, cm)
        if not clt["pass"]:
            cl_fails.append((d, cm, tf, clt))
        A, B, Ap = build_refs(bars, idxs, bi, tf, prev_hl_map[d])

        for k, _lab in FIELDS:
            t = tally[k]
            t["n"] += 1
            dB = not cmp(A[k], B[k])
            dA1 = not cmp(A[k], Ap[k])
            t["disc_B"] += dB
            t["disc_A1"] += dA1
            eqA = cmp(D[k], A[k])
            if eqA:
                t["D_eq_A"] += 1
            elif dB and cmp(D[k], B[k]):
                t["leak_full"] += 1
            elif dA1 and cmp(D[k], Ap[k]):
                t["leak_one"] += 1
            else:
                t["neither"] += 1
            rows.append({"date": d, "close_min": cm, "tf": tf, "field": k,
                         "A": A[k], "B_full": B[k], "A_plus1": Ap[k], "D": D[k],
                         "disc_vs_B": dB, "disc_vs_A1": dA1, "D_eq_A": eqA})

    print("\n" + "=" * 108)
    print("PER-INDICATOR VERDICT")
    print("=" * 108)
    print(f"{'indicator':>24} {'n':>4} {'disc B':>7} {'disc +1':>8} {'D==A':>6} "
          f"{'LEAK full':>10} {'LEAK +1':>8} {'other':>6}   verdict")
    print("-" * 108)
    verdicts = {}
    for k, lab in FIELDS:
        t = tally[k]
        if t["leak_full"] or t["leak_one"]:
            v = "*** CONTAMINATED ***"
        elif t["neither"]:
            v = "!!! MISMATCH — D is none of A/B/+1"
        elif t["disc_B"] == 0 and t["disc_A1"] == 0:
            v = "UNTESTED — no discriminating minute"
        else:
            bits = []
            if t["disc_B"]:
                bits.append(f"full-session {t['disc_B']}")
            if t["disc_A1"]:
                bits.append(f"one-bar {t['disc_A1']}")
            v = "CLEAN (" + ", ".join(bits) + ")"
        verdicts[k] = v
        print(f"{lab:>24} {t['n']:>4} {t['disc_B']:>7} {t['disc_A1']:>8} "
              f"{t['D_eq_A']:>6} {t['leak_full']:>10} {t['leak_one']:>8} "
              f"{t['neither']:>6}   {v}")

    print("\nNOTE on rolling indicators (BB basis, ATR): a full-session array")
    print("positionally indexed at T equals the trailing-window value BY")
    print("CONSTRUCTION, so 'disc B' is 0 for them by definition and proves nothing.")
    print("They are tested by the one-bar-ahead column, which does discriminate.")

    print("\n" + "=" * 108)
    print("STRUCTURAL CHECKS")
    print("=" * 108)
    ft = fractal_unit_test()
    print(f"  fractal confirmation (swing at j not knowable until j+{FRACTAL_N}):")
    print(f"     counted immediately: {ft['spike_counted_immediately']}  "
          f"(must be False)")
    print(f"     counted after {FRACTAL_N} more bars: {ft['spike_counted_after_N_more']}  "
          f"(must be True)")
    print(f"     -> {'PASS' if ft['pass'] else '*** FAIL ***'}")
    print(f"\n  close-label shift (last consumed bar opens at T-1, closes at T):")
    print(f"     failures across {len(picks)} test minutes: {len(cl_fails)}  "
          f"-> {'PASS' if not cl_fails else '*** FAIL ***'}")
    for f in cl_fails[:5]:
        print(f"        {f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit_pit_detail.json").write_text(json.dumps(rows, indent=1, default=str))
    print(f"\nper-minute detail: {OUT/'audit_pit_detail.json'} ({len(rows)} comparisons)")

    bad = [k for k, v in verdicts.items() if "CONTAMIN" in v or "MISMATCH" in v]
    unt = [k for k, v in verdicts.items() if "UNTESTED" in v]
    print("\n" + "=" * 108)
    if bad:
        print(f"OVERALL: *** CONTAMINATED *** — {bad}. STAGE 2 IS BLOCKED.")
    elif unt:
        print(f"OVERALL: INCOMPLETE — untested indicators: {unt}")
    elif not ft["pass"] or cl_fails:
        print("OVERALL: *** STRUCTURAL FAILURE *** — STAGE 2 IS BLOCKED.")
    else:
        print("OVERALL: CLEAN — every indicator matches the point-in-time reference,")
        print("         on at least one discriminating comparison each.")
    print("=" * 108)
    return verdicts


if __name__ == "__main__":
    main()
