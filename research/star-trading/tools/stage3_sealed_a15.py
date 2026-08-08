#!/usr/bin/env python3
"""STAGE 3 — SEALED RUN, post-A15 spec. Compute outcomes, SEAL them, read nothing.

Overnight queue item 11. Runs ONLY if the gate passed: items 2-6 introduced no
behaviour contradicting an existing clause (A14 and A15 are additions closing
documented gaps, not bug fixes, and are explicitly exempted from tripping this
gate by the item's own text).

Modelled directly on stage2_smoke.py's sealing discipline, carried forward onto
the current spec (A1-A15) rather than the frozen A1-A7 detector:

  - no outcome field is printed, summed, averaged, counted, or branched on
    ANYWHERE in this script's own console output - stricter than stage2_smoke,
    which prints frequency/audit facts; this script prints nothing but
    completion, the sealed row count, the file path, the SHA-256, and the
    Amendment 02 floor check, per item 11's own report restriction
  - a self-check scans everything printed for outcome tokens and aborts if any
    appears, exactly as stage2_smoke's does
  - refuses to overwrite an existing sealed result
  - admission is spec_current.signal_candidates_current (A8 sigma eligibility,
    A9 location-as-covariate, A10 fractal plateau rule, A13 live sigma test,
    A14 tick rounding) + the A7 admission loop (vwapbb_a7_selector.tie_break)
  - resolution is spec_current.resolve_bar_stop_first (item 5's standalone,
    already-tested transcription of accounting rule 4.1) + EOD flatten (4.5)
  - A11: every trade carries entry_tf_1m
  - costs at three bases per item 11: lean 0.25, base 0.50, adverse 1.00 pt

Workbench only (2023-01-02 .. 2025-01-31). The holdout is never addressed.
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

from vwapbb_signals import build_sessions, minute_of_day
from vwapbb_opportunity import assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import tie_break, MAX_TRADES_DAY
from stage2_smoke import contract_key, EOD_FLATTEN
import spec_current as SC

SC.SIGMA_RULE = "live"          # A13
SC.A14_ROUND = True             # A14

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
RESULTS = OUT / "workbench_results_SEALED_A15.parquet"
SPEC_HASH = "f6b38bf4af1ca9696a12a6e9f80a12209ebff310"   # git blob, A1-A15
COSTS = {"lean025": 0.25, "base050": 0.50, "adverse100": 1.00}
UNSEAL_TOKEN = "RESULTS_UNSEAL_APPROVED_BY_ANGUS"
N_FLOOR = 661

LEAK_TOKENS = ("gross", "net_", "net r", "expectancy", "win rate", "winrate",
               "profit", "pnl", "p&l", "equity", "drawdown", "sharpe",
               "exit_reason", "exit_price", "target_hit", "stop_hit",
               "mean", "median", "positive", "negative")


class SealedResultsError(RuntimeError):
    pass


def read_results(token: str | None = None):
    """The only supported reader. Refuses without the token."""
    if token != UNSEAL_TOKEN:
        raise SealedResultsError(
            f"REFUSING to read {RESULTS.name}: results are SEALED. See "
            f"vwap-bb/STAGE3-UNSEAL-RULE.md."
        )
    return pq.read_table(RESULTS)


def run_session(d, bars, prev_hl, audit):
    """Admission (spec_current) + resolution (resolve_bar_stop_first) + EOD
    flatten. Returns a list of trade dicts, each carrying gross_points and, per
    cost basis, net_points and net_R - never printed by this script."""
    cands = SC.signal_candidates_current(bars, prev_hl, audit)
    if cands is None:
        return None
    idxs = sorted(bars)
    trades, pending, pos, n_adm = [], None, None, 0

    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)

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

        if pos is not None:
            if mj >= EOD_FLATTEN:
                ex, px = "eod_flatten", o
            else:
                res = SC.resolve_bar_stop_first(pos["direction"], pos["stop_px"],
                                                pos["tgt_px"], o, h, l, c)
                ex, px = (res, pos["stop_px"] if res == "stop" else pos["tgt_px"]) \
                    if res else (None, None)
            if ex is not None:
                gross = (px - pos["fill_px"]) if pos["direction"] == "long" \
                    else (pos["fill_px"] - px)
                rec = {
                    "session_date": d, "signal_minute": pos["cm"],
                    "fill_minute": pos["fill_min"], "exit_minute": mj,
                    "minutes_held": mj - pos["fill_min"],
                    "bars_held": idxs.index(j) - idxs.index(pos["fill_bar"]),
                    "entry_tf": pos["tf"], "entry_tf_1m": pos["tf"] == 1,   # A11
                    "direction": pos["direction"], "trigger_kind": pos["kind"],
                    "htf_flag": pos["htf"], "counter_trend": pos["counter"],
                    "cluster_size": pos["nlev"], "cluster_types": pos["types"],
                    "tie_break_level": pos["lvl"],
                    "entry_price": round(pos["fill_px"], 4),
                    "stop_price": round(pos["stop_px"], 4),
                    "target_price": round(pos["tgt_px"], 4),
                    "stop_distance_points": round(pos["R"], 4),
                    "exit_reason": ex, "exit_price": round(px, 4),
                    "gross_points": round(gross, 4), "year": d[:4],
                }
                for tag, cst in COSTS.items():
                    rec[f"net_points_{tag}"] = round(gross - cst, 4)
                    rec[f"net_R_{tag}"] = round((gross - cst) / pos["R"], 6)
                trades.append(rec)
                pos = None

        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is None:
                    audit["stand-down: long and short on one bar"] += 1
                else:
                    pending = {**win, "lvl": lvl}

    if pos is not None:
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

    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
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

    if not rows:
        say("NO TRADES PRODUCED — nothing to seal. Investigate before re-running.")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    cols = {k: [r.get(k) for r in rows] for k in keys}
    pq.write_table(pa.table(cols), RESULTS, compression="snappy")
    sha = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
    runtime = time.time() - t0

    n_tr = len(rows)
    tot = processed + sum(excluded.values()) + len(errors)
    clears = n_tr >= N_FLOOR

    # ---- THE ONLY THINGS THIS SCRIPT MAY EVER PRINT, per item 11 ----
    say("=" * 84)
    say("STAGE 3 — SEALED RUN, post-A15 spec")
    say("=" * 84)
    say(f"  spec hash                : {SPEC_HASH}")
    say(f"  completed                : YES")
    say(f"  reconciliation           : {processed} + {sum(excluded.values())} + "
        f"{len(errors)} = {tot}  ({'OK' if tot == len(days) else 'MISMATCH'})")
    say(f"  errors                   : {len(errors)}")
    say(f"  realised trade count     : {n_tr}")
    say(f"  Amendment 02 floor n>={N_FLOOR} : {'CLEARS' if clears else 'BELOW FLOOR'}")
    say(f"  runtime                  : {runtime/60:.1f} min")
    say(f"  output                   : {RESULTS}")
    say(f"  columns                  : {len(keys)}")
    say(f"  SHA-256                  : {sha}")
    say("=" * 84)
    say("  Results are SEALED. No outcome column has been read, printed or aggregated.")
    say("  Reader: stage3_sealed_a15.read_results(token) — raises SealedResultsError "
        "without it. Governed by vwap-bb/STAGE3-UNSEAL-RULE.md.")
    say("=" * 84)

    text = buf.getvalue().lower()
    leaked = [t for t in LEAK_TOKENS if t in text]
    if leaked:
        print(f"\n*** SELF-CHECK FAILED: printed output contains {leaked} ***")
        return 3
    print("\n  self-check: printed output contains no outcome token. PASS")

    (OUT / "workbench_results_SEALED_A15.sha256").write_text(
        f"{sha}  {RESULTS.name}\nsealed {datetime.now().isoformat(timespec='seconds')}\n"
        f"rows {n_tr}\ncolumns {len(keys)}\nspec_hash {SPEC_HASH}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
