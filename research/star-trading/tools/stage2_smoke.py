#!/usr/bin/env python3
"""STAGE 2 — SMOKE TEST. Compute outcomes, SEAL them, read nothing.

The result exists, hashed and immutable, BEFORE the pass marks are finalised.
That property is worth more than any number in the file, and it only holds if
nobody looks. So this script is written so that looking is awkward:

  - no outcome field is printed, summed, averaged, counted or branched on
  - a self-check scans everything printed for outcome tokens and aborts if any
    appears (LEAK_TOKENS below) — the docstring does not merely claim this
  - the parquet carries an unseal-token guard matching the holdout's
  - the reporting block touches only: completion, session accounting, admitted
    trade count, trades/session, errors, runtime, path, row count, SHA-256

SPEC AS AMENDED
  A1  RTH 09:31-16:00, first tradeable signal bar 09:36
  A4  target = first ladder level clearing the 1.5R floor
  A5  effective stop = max(structural stop, 10.00 pt)
  A7  first-come admission, one position at a time, max 3/session, MTF tie-break

ACCOUNTING (pre-registration section 4)
  4.1  ambiguous bars resolve STOP-FIRST
  4.2  entry fills at the OPEN of the bar after the signal bar closes
  4.3  contract rolls reset indicator state; roll sessions AND the session after
       each roll are skipped
  4.4  spread symbols excluded (upstream, in alpha_data)
  4.5  EOD flatten at 15:55 ET
  4.6  costs at 0.50 / 0.975 / 1.50, deducted from realised R
  4.7  one unit of risk per trade, no sizing, no compounding

DESIGN NOTES on decisions a pre-run review forced, recorded because they are
choices and not obvious:

  ORDER PLACEMENT. Stop and target are absolute PRICES fixed at SIGNAL time from
  the intended E1 entry (the BB MA), exactly as a live order would be. The fill
  then happens at the next bar's open per 4.2, and realised risk is
  |fill - stop_price| — the risk actually taken, not the risk intended. A4
  feasibility is therefore evaluated at signal time, BEFORE the tie-break, so an
  infeasible winner cannot suppress a feasible runner-up.

  ADMISSION is a strictly causal streaming loop, the same construction verified
  equivalent to the batch form in STAGE1-PIT-AUDIT.md section 4. No open_until
  arithmetic; the loop simply holds at most one position.

  EOD FLATTEN exits at the OPEN of the first bar at or after 15:55, so none of
  that bar's range is used either to flatten or to trigger a stop. The earlier
  form tested the flatten before the stop on the same bar, which let 4.5
  silently override 4.1.

  DETERMINISM. trig() returns a set; iterating it unsorted made candidate order,
  and therefore the sealed SHA-256, vary between runs. It is sorted here.

Workbench only. The holdout is never addressed.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import hashlib
import io
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
EOD_FLATTEN = 15 * 60 + 55
COSTS = {"c050": 0.50, "c0975": 0.975, "c150": 1.50}
UNSEAL_TOKEN = "RESULTS_UNSEAL_APPROVED_BY_ANGUS"
READING = "A"

# pre-registration section 6: required n / 539, by correction divisor, at
# p0 = 43.90%. The axis structure is OPEN (section 10.3) so no single value is
# hardcoded as THE tripwire.
TRIPWIRES = {1: 0.7631, 4: 1.1720, 5: 1.2373, 8: 1.3745, 16: 1.5758, 72: 2.0091}

LEAK_TOKENS = ("gross", "net_", "net R", "expectancy", "win rate", "winrate",
               "profit", "pnl", "p&l", "equity", "drawdown", "sharpe",
               "exit_reason", "exit_price", "target_hit", "stop_hit")

MONTH_ORDER = {"H": 3, "M": 6, "U": 9, "Z": 12}


def contract_key(sym: str):
    """Chronological expiry order. sorted() is ALPHABETICAL, which puts NQH4
    before NQZ3 — wrong, and it shifted roll detection."""
    return (int(sym[-1]), MONTH_ORDER.get(sym[-2], 0))


class SealedResultsError(RuntimeError):
    pass


def read_results(token: str | None = None):
    """The only supported reader. Refuses without the token, as the holdout
    loader does. Stage 2 must not call this."""
    if token != UNSEAL_TOKEN:
        raise SealedResultsError(
            f"REFUSING to read {RESULTS.name}: results are SEALED. The pre-registration's "
            f"pass marks are not signed (PREREGISTRATION.md section 10.4)."
        )
    return pq.read_table(RESULTS)


# ════════════════════════════════════════════════════════════════════
def signal_candidates(bars, prev_hl, audit):
    """All post-filter candidates keyed by signal close-minute, each already
    carrying its A4 target and A5 stop as absolute PRICES decided at signal
    time. Returns {close_minute: [candidate, ...]} or None for short sessions."""
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
                # sorted(): trig() returns a set and unsorted iteration made the
                # sealed hash vary between runs
                for direction, kind in sorted(trig(to_, th_, tl_, tc_,
                                                   cl_lo, cl_hi, nib, READING)):
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
                    # ---- order geometry decided HERE, at signal time ----
                    if direction == "long":
                        struct = tl_ - TICK
                        if basis <= struct:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(basis - struct, MIN_STOP)
                        stop_px = basis - R_int
                    else:
                        struct = th_ + TICK
                        if struct <= basis:
                            audit["dropped: entry beyond wick"] += 1
                            continue
                        R_int = max(struct - basis, MIN_STOP)
                        stop_px = basis + R_int
                    tgt_px = None
                    for x in ladder(menu, basis, direction, FRONT_RUN_F):
                        if abs(x - basis) / R_int >= RR_FLOOR:
                            tgt_px = x
                            break
                    if tgt_px is None:
                        audit["dropped: no target clears the RR floor"] += 1
                        continue
                    by_min[cm].append({
                        "cm": cm, "bar": i, "tf": tf, "direction": direction,
                        "kind": kind, "entry": basis, "stop_px": stop_px,
                        "tgt_px": tgt_px, "R_int": R_int, "nlev": nlev,
                        "cl_lo": cl_lo, "cl_mid": (cl_lo + cl_hi) / 2,
                        "htf": flag, "counter": counter, "types": len(types),
                    })

    # collapse duplicate records of one trade (A7)
    out = {}
    for cm, g in by_min.items():
        keep = []
        seen = set()
        for c in g:
            k = (c["tf"], c["direction"], round(c["entry"], 4),
                 round(c["stop_px"], 4), round(c["tgt_px"], 4))
            if k not in seen:
                seen.add(k)
                keep.append(c)
        out[cm] = keep
    return out


def run_session(d, bars, prev_hl, audit):
    """Strictly causal streaming pass. At most one position; fills at the next
    bar's open; stop-first; flatten at the open of the first bar >= 15:55."""
    cands = signal_candidates(bars, prev_hl, audit)
    if cands is None:
        return None
    idxs = sorted(bars)
    trades, pending, pos, n_adm = [], None, None, 0

    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)

        # 1. fill a pending order at THIS bar's open (4.2)
        if pending is not None and pos is None:
            if mj >= EOD_FLATTEN:
                audit["dropped: fill would land at/after EOD flatten"] += 1
                pending = None
            else:
                w = pending
                pending = None
                bad = (w["direction"] == "long" and o <= w["stop_px"]) or \
                      (w["direction"] == "short" and o >= w["stop_px"])
                if bad:
                    audit["dropped: open gapped through the stop"] += 1
                else:
                    R = abs(o - w["stop_px"])
                    pos = {**w, "fill_px": o, "fill_bar": j, "fill_min": mj, "R": R}
                    n_adm += 1

        # 2. resolve an open position against THIS bar
        if pos is not None:
            if mj >= EOD_FLATTEN:                       # 4.5, at the OPEN
                ex, px = "eod_flatten", o
            else:
                dn = (pos["fill_px"] - l) if pos["direction"] == "long" else (h - pos["fill_px"])
                up = (h - pos["fill_px"]) if pos["direction"] == "long" else (pos["fill_px"] - l)
                hit_stop = (l <= pos["stop_px"]) if pos["direction"] == "long" \
                    else (h >= pos["stop_px"])
                hit_tgt = (h >= pos["tgt_px"]) if pos["direction"] == "long" \
                    else (l <= pos["tgt_px"])
                if hit_stop:                            # 4.1 STOP-FIRST
                    ex, px = "stop", pos["stop_px"]
                elif hit_tgt:
                    ex, px = "target", pos["tgt_px"]
                else:
                    ex = None
            if ex is not None:
                gross = (px - pos["fill_px"]) if pos["direction"] == "long" \
                    else (pos["fill_px"] - px)
                rec = {
                    "session_date": d, "signal_minute": pos["cm"],
                    "signal_hhmm": f"{pos['cm']//60:02d}:{pos['cm']%60:02d}",
                    "fill_minute": pos["fill_min"], "exit_minute": mj,
                    "minutes_held": mj - pos["fill_min"],
                    "bars_held": idxs.index(j) - idxs.index(pos["fill_bar"]),
                    "entry_tf": pos["tf"], "direction": pos["direction"],
                    "trigger_kind": pos["kind"], "htf_flag": pos["htf"],
                    "counter_trend": pos["counter"], "cluster_size": pos["nlev"],
                    "cluster_types": pos["types"], "tie_break_level": pos["lvl"],
                    "intended_entry": round(pos["entry"], 4),
                    "entry_price": round(pos["fill_px"], 4),
                    "slippage_vs_intended": round(
                        (pos["fill_px"] - pos["entry"]) if pos["direction"] == "long"
                        else (pos["entry"] - pos["fill_px"]), 4),
                    "stop_price": round(pos["stop_px"], 4),
                    "target_price": round(pos["tgt_px"], 4),
                    "stop_distance_points": round(pos["R"], 4),
                    "intended_stop_distance": round(pos["R_int"], 4),
                    "target_distance_points": round(abs(pos["tgt_px"] - pos["fill_px"]), 4),
                    "planned_rr": round(abs(pos["tgt_px"] - pos["fill_px"]) / pos["R"], 4),
                    "stop_at_a5_floor": bool(pos["R_int"] <= MIN_STOP + 1e-9),
                    "exit_reason": ex, "exit_price": round(px, 4),
                    "gross_points": round(gross, 4), "year": d[:4],
                }
                for tag, cst in COSTS.items():
                    rec[f"net_points_{tag}"] = round(gross - cst, 4)
                    rec[f"net_R_{tag}"] = round((gross - cst) / pos["R"], 6)
                trades.append(rec)
                pos = None

        # 3. a signal closing at this bar may become the next pending order
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is None:
                    audit["stand-down: long and short on one bar"] += 1
                else:
                    pending = {**win, "lvl": lvl}

    if pos is not None:                     # cannot happen: EOD flatten catches
        audit["ERROR: position open at session end"] += 1
    return trades


def main():
    t0 = time.time()
    if RESULTS.exists():
        print(f"REFUSING to overwrite an existing sealed result: {RESULTS}")
        return 1

    buf = io.StringIO()

    def say(s=""):
        print(s)
        buf.write(s + "\n")

    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)

    # 4.3 — rolls, using CHRONOLOGICAL contract order, not alphabetical
    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]      # the furthest-dated front
        if prev_sym and contract_key(s) > contract_key(prev_sym):
            rolls.add(d)
        prev_sym = s
    after_roll = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    excluded = collections.Counter()
    audit = collections.Counter()
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
                prev_hl = None
            elif d in after_roll:
                excluded["session after roll (4.3)"] += 1
            elif len(sym_of[d]) > 1:
                excluded["mixed contract"] += 1
            else:
                r = run_session(d, bars, prev_hl, audit)
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

    if not rows:
        say("NO TRADES PRODUCED — nothing to seal. Investigate before re-running.")
        say(f"excluded={dict(excluded)} audit={dict(audit)} errors={len(errors)}")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    cols = {k: [r.get(k) for r in rows] for k in keys}
    pq.write_table(pa.table(cols), RESULTS, compression="snappy")
    sha = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
    runtime = time.time() - t0

    n_tr = len(rows)
    per = n_tr / processed if processed else 0.0
    say("=" * 84)
    say("STAGE 2 — SMOKE TEST")
    say("=" * 84)
    say("  completed                : YES")
    say(f"  workbench sessions       : {len(days)}  (2023-01-03 .. 2025-01-31)")
    say(f"  sessions PROCESSED       : {processed}")
    say(f"  sessions EXCLUDED        : {sum(excluded.values())}")
    for k, v in sorted(excluded.items()):
        say(f"       {k:<34} {v}")
    tot = processed + sum(excluded.values()) + len(errors)
    say(f"  reconciliation           : {processed} + {sum(excluded.values())} + "
        f"{len(errors)} = {tot}  ({'OK' if tot == len(days) else 'MISMATCH'})")
    say(f"  ADMITTED TRADES          : {n_tr}")
    say(f"  trades / session         : {per:.4f}")
    say("  vs pre-registration section 6 tripwires (axis structure is OPEN):")
    for div, tw in sorted(TRIPWIRES.items()):
        say(f"       /{div:<3} tripwire {tw:.4f}  ->  "
            f"{'CLEARS' if per >= tw else 'BELOW — GATE 6 REOPENS'}")
    say("  candidate audit (entry logic, not outcomes):")
    for k, v in sorted(audit.items()):
        say(f"       {k:<44} {v}")
    say(f"  errors                   : {len(errors)}")
    for d, e in errors:
        say(f"       {d}: {e}")
    say(f"  runtime                  : {runtime/60:.1f} min")
    say(f"  output                   : {RESULTS}")
    say(f"  rows                     : {n_tr}")
    say(f"  columns                  : {len(keys)}")
    say(f"  SHA-256                  : {sha}")
    say("=" * 84)
    say("  Results are SEALED. No outcome column has been read, printed or aggregated.")
    say("  Reader: stage2_smoke.read_results(token) — raises SealedResultsError without it.")
    say("=" * 84)

    # self-check: nothing printed may contain an outcome token
    text = buf.getvalue().lower()
    leaked = [t for t in LEAK_TOKENS if t in text]
    # 'exit_reason'/'exit_price' etc. appear only as column NAMES in this list,
    # never as values; the check is on the printed report, which lists neither
    if leaked:
        print(f"\n*** SELF-CHECK FAILED: printed output contains {leaked} ***")
        return 3
    print("\n  self-check: printed output contains no outcome token. PASS")

    (OUT / "workbench_results_SEALED.sha256").write_text(
        f"{sha}  {RESULTS.name}\nsealed {datetime.now().isoformat(timespec='seconds')}\n"
        f"rows {n_tr}\ncolumns {len(keys)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
