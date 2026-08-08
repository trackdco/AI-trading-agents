#!/usr/bin/env python3
"""AMENDMENT 03 §8.1 — DESCRIPTIVE COUNT of the current §7 location gate.

Not a hypothesis test. No outcome is computed, no P&L, no expectancy, no ranking.
The only quantities produced are counts, proportions and a distribution of the
gate's own input. N_trials is unaffected.

Method. One pass over the workbench, replicating stage2_smoke.signal_candidates
exactly, except that the location gate is EVALUATED AND RECORDED rather than
applied. Every other gate runs unchanged and in the same order, so an
"otherwise-valid candidate" means: passed confluence, passed §7 invalidation,
has a usable wick stop, and has a target clearing the 1.5R floor. The location
gate's block rate is then measured against that denominator.

Admission counts are produced by the same strictly causal streaming loop the
sealed engine uses (one position at a time, max 3/session, A7 tie-break), run
twice — gate ON and gate OFF — and counting admissions only. No trade is
resolved; no exit is computed.

Workbench only. The holdout is never addressed. The sealed parquet is not read.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
import time
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import (ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F,
                                MAX_TRADES_DAY, LOC_BAND, TICK)
from stage2_smoke import contract_key, EOD_FLATTEN, READING

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "loc_gate_measure.json"
N_FLOOR = 661          # Amendment 02 minimum runnable sample


def session_candidates(bars, prev_hl, stat):
    """Same construction as stage2_smoke.signal_candidates, with the location gate
    recorded instead of applied. Returns {cm: [cand]} where each cand carries
    loc_pos and loc_blocks."""
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
            flag = htf_flag(b15)

            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
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

            for cl_lo, cl_hi, types, nlev in cluster_levels(lv):
                if READING == "D" and nlev < 3:
                    continue
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
                    stat["raw triggers"] += 1
                    counter = (flag == "uptrend" and direction == "short") or \
                              (flag == "downtrend" and direction == "long")
                    if len(types) < (3 if counter else 2):
                        stat["dropped: confluence"] += 1
                        continue
                    if nmid:
                        if direction == "long" and th_ >= nmid + nsig:
                            stat["dropped: invalidation"] += 1
                            continue
                        if direction == "short" and tl_ <= nmid - nsig:
                            stat["dropped: invalidation"] += 1
                            continue
                    # ---- LOCATION GATE: evaluated, NOT applied ----
                    pos, blocks = None, False
                    if h4:
                        rh, rl = max(x[0] for x in h4), min(x[1] for x in h4)
                        if rh > rl:
                            pos = (tc_ - rl) / (rh - rl)
                            blocks = (pos >= 1 - LOC_BAND) if direction == "long" \
                                else (pos <= LOC_BAND)
                    # ---- order geometry, unchanged ----
                    if direction == "long":
                        struct = tl_ - TICK
                        if basis <= struct:
                            stat["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(basis - struct, MIN_STOP)
                        stop_px = basis - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= basis:
                            stat["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - basis, MIN_STOP)
                        stop_px = basis + R_int
                    tgt_px = None
                    for x in ladder(menu, basis, direction, FRONT_RUN_F):
                        if abs(x - basis) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                    if tgt_px is None:
                        stat["dropped: no target clears the RR floor"] += 1
                        continue
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": basis, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "htf": flag, "counter": counter, "types": len(types),
                        "loc_pos": pos, "loc_blocks": blocks,
                    })

    out = {}
    for cm, g in by_min.items():
        keep, seen = [], set()
        for c in g:
            k = (c["tf"], c["direction"], round(c["entry"], 4),
                 round(c["stop_px"], 4), round(c["tgt_px"], 4))
            if k not in seen:
                seen.add(k)
                keep.append(c)
        out[cm] = keep
    return out


def admit(bars, cands, apply_gate):
    """Streaming admission, identical construction to run_session, counting only.
    No position is resolved and no outcome field exists."""
    idxs = sorted(bars)
    pending, pos, n_adm, held_until = None, None, 0, None
    admitted = []
    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)
        if pending is not None and pos is None:
            if mj >= EOD_FLATTEN:
                pending = None
            else:
                w = pending
                pending = None
                bad = (w["direction"] == "long" and o <= w["stop_px"]) or \
                      (w["direction"] == "short" and o >= w["stop_px"])
                if not bad:
                    pos = w
                    n_adm += 1
                    admitted.append(w)
        if pos is not None:
            # occupancy only: resolve on stop OR target touch, stop-first, EOD flatten.
            # Prices are compared; no outcome is recorded, returned or counted.
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
                g = [x for x in g if not (apply_gate and x["loc_blocks"])]
                if g:
                    win, _lvl = tie_break(g)
                    if win is not None:
                        pending = win
    return admitted


def main():
    t0 = time.time()
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)

    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev_sym and contract_key(s) > contract_key(prev_sym):
            rolls.add(d)
        prev_sym = s
    after_roll = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    stat = collections.Counter()
    excluded = collections.Counter()
    processed = 0
    rows = []                      # one per otherwise-valid candidate
    adm_on, adm_off = [], []
    sess_on, sess_off = collections.Counter(), collections.Counter()
    prev_hl = None
    for n, d in enumerate(days, 1):
        assert_workbench(d)
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        if d in rolls:
            excluded["roll session"] += 1
            prev_hl = None
        elif d in after_roll:
            excluded["session after roll"] += 1
        elif len(sym_of[d]) > 1:
            excluded["mixed contract"] += 1
        else:
            cands = session_candidates(bars, prev_hl, stat)
            if cands is None:
                excluded["holiday / short session"] += 1
            else:
                processed += 1
                for cm, g in cands.items():
                    for c in g:
                        rows.append((d, cm, c["tf"], c["direction"], c["htf"],
                                     c["counter"], c["loc_pos"], c["loc_blocks"]))
                a_on = admit(bars, cands, True)
                a_off = admit(bars, cands, False)
                adm_on.extend((d, x["direction"], x["tf"]) for x in a_on)
                adm_off.extend((d, x["direction"], x["tf"]) for x in a_off)
                sess_on[d] = len(a_on)
                sess_off[d] = len(a_off)
        if d not in rolls:
            prev_hl = this_hl
        if n % 100 == 0:
            print(f"  ...{n}/{len(days)} sessions, {time.time()-t0:.0f}s")

    # ─────────────────────────── report ───────────────────────────
    def pct(a, b):
        return f"{100.0*a/b:.2f}%" if b else "n/a"

    tot = len(rows)
    blocked = [r for r in rows if r[7]]
    by_dir = collections.Counter(r[3] for r in rows)
    blk_dir = collections.Counter(r[3] for r in blocked)
    no_pos = sum(1 for r in rows if r[6] is None)

    L = []
    def say(s=""):
        print(s); L.append(s)

    say("=" * 84)
    say("LOCATION GATE — DESCRIPTIVE COUNT (Amendment 03 §8.1). No hypothesis tested.")
    say("=" * 84)
    say(f"  workbench sessions        : {len(days)}  ({days[0]} .. {days[-1]})")
    say(f"  sessions PROCESSED        : {processed}")
    for k, v in sorted(excluded.items()):
        say(f"       excluded {k:<28} {v}")
    say()
    say("  gate order upstream of location (all applied normally):")
    for k in ("raw triggers", "dropped: confluence", "dropped: invalidation"):
        say(f"       {k:<38} {stat[k]:>8,}")
    say("  gates downstream of location (applied normally, location NOT applied):")
    for k in ("dropped: entry beyond wick", "dropped: no target clears the RR floor"):
        say(f"       {k:<38} {stat[k]:>8,}")
    say()
    say("─" * 84)
    say("  OTHERWISE-VALID CANDIDATES (post-dedup, every gate except location)")
    say("─" * 84)
    say(f"       total                    {tot:>8,}")
    say(f"       long                     {by_dir['long']:>8,}")
    say(f"       short                    {by_dir['short']:>8,}")
    say(f"       no 4h range available    {no_pos:>8,}  (gate cannot fire)")
    say()
    say("  BLOCKED BY THE LOCATION GATE")
    say(f"       total                    {len(blocked):>8,}   {pct(len(blocked), tot)}")
    say(f"       long                     {blk_dir['long']:>8,}   "
        f"{pct(blk_dir['long'], by_dir['long'])} of longs")
    say(f"       short                    {blk_dir['short']:>8,}   "
        f"{pct(blk_dir['short'], by_dir['short'])} of shorts")
    say()
    say("─" * 84)
    say("  RANGE-POSITION DISTRIBUTION over otherwise-valid candidates")
    say("─" * 84)
    edges = [(-1e9, 0.0, "< 0.00  (below its own range)"),
             (0.0, 0.20, "0.00-0.20  [gate blocks SHORTS]"),
             (0.20, 0.40, "0.20-0.40"), (0.40, 0.60, "0.40-0.60"),
             (0.60, 0.80, "0.60-0.80"),
             (0.80, 1.0, "0.80-1.00  [gate blocks LONGS]"),
             (1.0, 1e9, "> 1.00  (above its own range) [blocks LONGS]")]
    vals = [r[6] for r in rows if r[6] is not None]
    for lo, hi, lab in edges:
        k = sum(1 for x in vals if lo <= x < hi) if hi < 1e9 else sum(1 for x in vals if x >= lo)
        say(f"       {lab:<44} {k:>8,}  {pct(k, len(vals))}")
    sv = sorted(vals)
    def q(p):
        return sv[min(len(sv) - 1, int(p * len(sv)))]
    say()
    say(f"       n={len(sv):,}   min {sv[0]:.4f}   p05 {q(.05):.4f}   p25 {q(.25):.4f}   "
        f"median {q(.50):.4f}")
    say(f"                    p75 {q(.75):.4f}   p95 {q(.95):.4f}   max {sv[-1]:.4f}   "
        f"mean {sum(sv)/len(sv):.4f}")
    say(f"       outside [0,1] entirely : {sum(1 for x in sv if x < 0 or x > 1):,}  "
        f"{pct(sum(1 for x in sv if x < 0 or x > 1), len(sv))}")
    for dd in ("long", "short"):
        v2 = sorted(r[6] for r in rows if r[3] == dd and r[6] is not None)
        if v2:
            say(f"       {dd:<5} median {v2[len(v2)//2]:.4f}   "
                f"mean {sum(v2)/len(v2):.4f}   n={len(v2):,}")
    say()
    say("─" * 84)
    say("  IMPLIED SURVIVING TRADE COUNT (A7 admission, counts only, no outcomes)")
    say("─" * 84)
    dON, dOFF = collections.Counter(x[1] for x in adm_on), collections.Counter(x[1] for x in adm_off)
    say(f"       gate ON  (as sealed)     {len(adm_on):>8,} trades   "
        f"long {dON['long']:,} / short {dON['short']:,}   "
        f"{len(adm_on)/processed:.4f}/session")
    say(f"       gate OFF (demoted)       {len(adm_off):>8,} trades   "
        f"long {dOFF['long']:,} / short {dOFF['short']:,}   "
        f"{len(adm_off)/processed:.4f}/session")
    say(f"       delta                    {len(adm_off)-len(adm_on):>+8,} trades   "
        f"{pct(len(adm_off)-len(adm_on), len(adm_on))} of the gated count")
    say()
    say(f"       Amendment 02 floor n >= {N_FLOOR}")
    for lab, k in (("gate ON ", len(adm_on)), ("gate OFF", len(adm_off))):
        say(f"       {lab}  {k:,}  ->  {'CLEARS' if k >= N_FLOOR else 'BELOW FLOOR'} "
            f"({k/N_FLOOR:.2f}x)")
    say()
    say(f"  runtime {time.time()-t0:.0f}s.  No outcome computed. N_trials unchanged: 0.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "processed_sessions": processed, "excluded": dict(excluded),
        "funnel": dict(stat),
        "otherwise_valid": tot, "by_direction": dict(by_dir),
        "blocked_total": len(blocked), "blocked_by_direction": dict(blk_dir),
        "pos_quantiles": {"min": sv[0], "p05": q(.05), "p25": q(.25), "median": q(.50),
                          "p75": q(.75), "p95": q(.95), "max": sv[-1],
                          "mean": sum(sv) / len(sv)},
        "admitted_gate_on": len(adm_on), "admitted_gate_off": len(adm_off),
        "admitted_on_by_dir": dict(dON), "admitted_off_by_dir": dict(dOFF),
        "n_floor": N_FLOOR, "report": "\n".join(L),
    }, indent=1))
    print(f"\nwritten {OUT}")


if __name__ == "__main__":
    main()
