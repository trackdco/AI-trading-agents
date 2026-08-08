#!/usr/bin/env python3
"""STAGE 2 — SMOKE TEST. Compute outcomes, SEAL them, read nothing.

The result exists, hashed and immutable, BEFORE the pass marks are finalised.
That property is worth more than any number in the file, and it only holds if
nobody looks. So this script is written so that looking is awkward:

  - no outcome field is ever printed, summed, averaged or counted
  - the reporting block touches only: completion, session accounting, admitted
    trade count, trades/session, errors, runtime, path, row count, SHA-256
  - the parquet is written with an unseal-token guard matching the holdout's
  - a self-check asserts that no forbidden token appears in anything printed

SPEC AS AMENDED
  A1  RTH 09:31-16:00, first tradeable signal bar 09:36
  A4  target = first ladder level clearing the 1.5R floor
  A5  effective stop = max(structural stop, 10.00 pt)
  A7  first-come admission, one position at a time, max 3/session, MTF tie-break

ACCOUNTING (pre-registration section 4)
  4.1  ambiguous bars resolve STOP-FIRST
  4.2  entry fills at the OPEN of the bar after the signal bar closes
  4.3  contract rolls reset indicator state; the session AFTER each roll is
       skipped; roll sessions themselves are skipped
  4.4  spread symbols excluded (upstream, in alpha_data)
  4.5  EOD flatten at 15:55 ET
  4.6  costs at 0.50 / 0.975 / 1.50, deducted from realised R
  4.7  one unit of risk per trade, no sizing, no compounding

Workbench only. The holdout is never addressed.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import hashlib
import time
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import (ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F,
                                MAX_TRADES_DAY, LOC_BAND, TICK)

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
RESULTS = OUT / "workbench_results_SEALED.parquet"
EOD_FLATTEN = 15 * 60 + 55                      # 4.5
COSTS = {"c050": 0.50, "c0975": 0.975, "c150": 1.50}
UNSEAL_TOKEN = "RESULTS_UNSEAL_APPROVED_BY_ANGUS"
READING = "A"


class SealedResultsError(RuntimeError):
    pass


def read_results(token: str | None = None):
    """The only supported reader. Refuses without the token, exactly as the
    holdout loader does. Stage 2 must not call this."""
    if token != UNSEAL_TOKEN:
        raise SealedResultsError(
            f"REFUSING to read {RESULTS.name}: results are SEALED. The pre-registration's "
            f"pass marks are not signed. Pass the unseal token only after section 10.4 "
            f"of PREREGISTRATION.md is signed off."
        )
    return pq.read_table(RESULTS)


# ════════════════════════════════════════════════════════════════════
def run_session(d, bars, prev_hl):
    """Return list of trade dicts, or None if the session is a holiday/short.
    Applies A1/A4/A5/A7 and accounting 4.1, 4.2, 4.5."""
    idxs = sorted(bars)
    if len([i for i in idxs if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]) < 300:
        return None
    pos_of = {v: k for k, v in enumerate(idxs)}
    hi = {i: bars[i][1] for i in idxs}
    lo = {i: bars[i][2] for i in idxs}
    op = {i: bars[i][0] for i in idxs}

    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    cands = collections.defaultdict(list)

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
                for direction, kind in trig(to_, th_, tl_, tc_, cl_lo, cl_hi, nib, READING):
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
                    # signal-bar geometry; entry price is NOT set here (4.2)
                    if direction == "long":
                        struct_stop = tl_ - TICK
                        if basis <= struct_stop:
                            continue
                    else:
                        struct_stop = th_ + TICK
                        if struct_stop <= basis:
                            continue
                    cands[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": basis, "struct_stop": struct_stop,
                        "nlev": nlev, "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "menu": list(menu), "htf": flag, "counter": counter,
                        "types": len(types),
                    })

    # ---- collapse duplicate records of the same trade (A7) ----
    by_min = {}
    for cm, g in cands.items():
        keep = []
        for c in g:
            k = (c["tf"], c["direction"], round(c["entry"], 4), round(c["struct_stop"], 4))
            if k not in {(x["tf"], x["direction"], round(x["entry"], 4),
                          round(x["struct_stop"], 4)) for x in keep}:
                keep.append(c)
        by_min[cm] = keep

    # ---- A7 admission, strictly in signal-time order ----
    trades, open_until, n_adm = [], -1, 0
    for cm in sorted(by_min):
        if cm < open_until or n_adm >= MAX_TRADES_DAY:
            continue
        win, lvl = tie_break(by_min[cm])
        if win is None:
            continue
        # 4.2 — entry fills at the OPEN of the bar after the signal bar closes
        bpos = pos_of[win["bar"]]
        if bpos + 1 >= len(idxs):
            continue
        fill_bar = idxs[bpos + 1]
        if minute_of_day(fill_bar) >= EOD_FLATTEN:
            continue
        entry_px = op[fill_bar]
        d_ = win["direction"]
        R = max(entry_px - win["struct_stop"], MIN_STOP) if d_ == "long" \
            else max(win["struct_stop"] - entry_px, MIN_STOP)
        if R <= 0:
            continue
        lad = ladder(win["menu"], entry_px, d_, FRONT_RUN_F)
        tgt_d = None
        for x in lad:
            dd = abs(x - entry_px)
            if dd / R >= RR_FLOOR:
                tgt_d = dd
                break
        if tgt_d is None:
            continue

        # ---- resolution from fill_bar forward. 4.1 STOP-FIRST. 4.5 EOD flatten.
        exit_reason, exit_px, exit_bar = None, None, None
        for j in idxs[bpos + 1:]:
            if minute_of_day(j) >= EOD_FLATTEN:
                exit_reason, exit_px, exit_bar = "eod_flatten", bars[j][3], j
                break
            up = (hi[j] - entry_px) if d_ == "long" else (entry_px - lo[j])
            dn = (entry_px - lo[j]) if d_ == "long" else (hi[j] - entry_px)
            if dn >= R:                                   # 4.1 stop wins ties
                exit_reason = "stop"
                exit_px = (entry_px - R) if d_ == "long" else (entry_px + R)
                exit_bar = j
                break
            if up >= tgt_d:
                exit_reason = "target"
                exit_px = (entry_px + tgt_d) if d_ == "long" else (entry_px - tgt_d)
                exit_bar = j
                break
        if exit_reason is None:
            j = idxs[-1]
            exit_reason, exit_px, exit_bar = "session_end", bars[j][3], j

        gross = (exit_px - entry_px) if d_ == "long" else (entry_px - exit_px)
        rec = {
            "session_date": d, "signal_minute": cm,
            "signal_hhmm": f"{cm//60:02d}:{cm%60:02d}",
            "fill_minute": minute_of_day(fill_bar),
            "exit_minute": minute_of_day(exit_bar),
            "minutes_held": len([1 for x in idxs
                                 if pos_of[fill_bar] <= pos_of[x] <= pos_of[exit_bar]]) - 1,
            "entry_tf": win["tf"], "direction": d_, "trigger_kind": win["kind"],
            "htf_flag": win["htf"], "counter_trend": win["counter"],
            "cluster_size": win["nlev"], "cluster_types": win["types"],
            "tie_break_level": lvl,
            "entry_price": round(entry_px, 4),
            "stop_price": round(entry_px - R if d_ == "long" else entry_px + R, 4),
            "target_price": round(entry_px + tgt_d if d_ == "long" else entry_px - tgt_d, 4),
            "stop_distance_points": round(R, 4),
            "target_distance_points": round(tgt_d, 4),
            "planned_rr": round(tgt_d / R, 4),
            "stop_at_a5_floor": bool(R <= MIN_STOP + 1e-9),
            "exit_reason": exit_reason, "exit_price": round(exit_px, 4),
            "gross_points": round(gross, 4),
            "year": d[:4],
        }
        for tag, c in COSTS.items():
            rec[f"net_points_{tag}"] = round(gross - c, 4)
            rec[f"net_R_{tag}"] = round((gross - c) / R, 6)
        trades.append(rec)
        open_until = cm + max(1, minute_of_day(exit_bar) - minute_of_day(fill_bar))
        n_adm += 1
    return trades


def main():
    t0 = time.time()
    if RESULTS.exists():
        print(f"REFUSING to overwrite an existing sealed result: {RESULTS}")
        print("Delete it deliberately if a re-run is intended.")
        return 1

    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)

    # 4.3 — roll detection and session-after-roll
    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d])[0]
        if prev_sym and s != prev_sym:
            rolls.add(d)
        prev_sym = s
    after_roll = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    excluded = collections.Counter()
    errors, rows = [], []
    processed = 0
    prev_hl = None
    for n, d in enumerate(days, 1):
        assert_workbench(d)
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        try:
            if d in rolls:
                excluded["roll session (4.3)"] += 1
                prev_hl = None                        # 4.3 reset indicator state
            elif d in after_roll:
                excluded["session after roll (4.3)"] += 1
            elif len(sym_of[d]) > 1:
                excluded["mixed contract"] += 1
            else:
                r = run_session(d, bars, prev_hl)
                if r is None:
                    excluded["holiday / short session"] += 1
                else:
                    processed += 1
                    rows.extend(r)
        except Exception as e:
            errors.append((d, f"{type(e).__name__}: {e}"))
        if d not in rolls:
            prev_hl = this_hl
        if n % 100 == 0:
            print(f"  ...{n}/{len(days)} sessions, {time.time()-t0:.0f}s")

    OUT.mkdir(parents=True, exist_ok=True)
    cols = {k: [r.get(k) for r in rows] for k in rows[0]}
    pq.write_table(pa.table(cols), RESULTS, compression="snappy")
    sha = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
    runtime = time.time() - t0

    n_tr = len(rows)
    per = n_tr / processed if processed else 0.0
    print("\n" + "=" * 84)
    print("STAGE 2 — SMOKE TEST")
    print("=" * 84)
    print(f"  completed                : YES")
    print(f"  workbench sessions       : {len(days)}  (2023-01-03 .. 2025-01-31)")
    print(f"  sessions PROCESSED       : {processed}")
    print(f"  sessions EXCLUDED        : {sum(excluded.values())}")
    for k, v in sorted(excluded.items()):
        print(f"       {k:<32} {v}")
    print(f"  reconciliation           : {processed} + {sum(excluded.values())} + "
          f"{len(errors)} = {processed + sum(excluded.values()) + len(errors)} "
          f"(= {len(days)}: {'OK' if processed+sum(excluded.values())+len(errors)==len(days) else 'MISMATCH'})")
    print(f"  ADMITTED TRADES          : {n_tr}")
    print(f"  trades / session         : {per:.4f}")
    print(f"  gate-6 tripwire (0.4862) : {'CLEARS' if per >= 0.4862 else 'BELOW — GATE 6 REOPENS'}"
          f"  ({per/0.4862:.1f}x)")
    print(f"  errors                   : {len(errors)}")
    for d, e in errors:
        print(f"       {d}: {e}")
    print(f"  runtime                  : {runtime/60:.1f} min")
    print(f"  output                   : {RESULTS}")
    print(f"  rows                     : {n_tr}")
    print(f"  columns                  : {len(cols)}")
    print(f"  SHA-256                  : {sha}")
    print("=" * 84)
    print("  Results are SEALED. No outcome column has been read, printed or aggregated.")
    print("  Reader: stage2_smoke.read_results(token) — raises SealedResultsError without it.")
    print("=" * 84)

    (OUT / "workbench_results_SEALED.sha256").write_text(
        f"{sha}  {RESULTS.name}\nsealed {datetime.now().isoformat(timespec='seconds')}\n"
        f"rows {n_tr}\ncolumns {len(cols)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
