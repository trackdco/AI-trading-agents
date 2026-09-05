#!/usr/bin/env python3
"""
Exact-reproduction check: a retest_backtest.py output vs. the bot's own 4-year trade log
(or vs. another retest output) over a window.  Trade IDs are uuid4 in the bot's log and
sequential in retest outputs, so identity is NOT compared; everything else is:

  entry: timestamp, signal_timestamp, direction, entry_price, raw_open, slippage_applied,
         stop_distance, signal_score, signal_source, regime, htf_bias, htf_strength, atr, is_rth
  exit:  timestamp, c1_exit_price, c2_exit_price, raw_pnl, exit_slippage_cost, adjusted_pnl,
         c1_pnl, c2_pnl, c1_exit_reason, c2_exit_reason, commission_total

Reference trades whose exit falls after the window end cannot be compared (the retest run
stopped) and are listed separately; a retest trade open at the end is already excluded.

usage: compare_trades.py --ref <bot log or retest json> --test <retest json> [--start D] [--end D]
"""
import argparse
import json
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ENTRY_FIELDS = ("timestamp", "signal_timestamp", "direction", "entry_price", "raw_open",
                "slippage_applied", "stop_distance", "signal_score", "signal_source", "regime",
                "htf_bias", "htf_strength", "atr", "is_rth")
EXIT_FIELDS = ("timestamp", "c1_exit_price", "c2_exit_price", "raw_pnl", "exit_slippage_cost",
               "adjusted_pnl", "c1_pnl", "c2_pnl", "c1_exit_reason", "c2_exit_reason",
               "commission_total")


def et_date(iso: str) -> date:
    return datetime.fromisoformat(iso).astimezone(ET).date()


def pairs(doc):
    recs = doc.get("records") or doc.get("trades")
    ent = {r["trade_id"]: r for r in recs if r["action"] == "entry"}
    out = []
    for r in recs:
        if r["action"] == "exit" and r["trade_id"] in ent:
            out.append((ent[r["trade_id"]], r))
    out.sort(key=lambda p: p[0]["timestamp"])
    return out


def norm(v):
    if isinstance(v, float):
        return round(v, 6)
    return v


def key(entry, exit_):
    return tuple(norm(entry.get(f)) for f in ENTRY_FIELDS) + tuple(norm(exit_.get(f)) for f in EXIT_FIELDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    a = ap.parse_args()
    start = date.fromisoformat(a.start) if a.start else None
    end = date.fromisoformat(a.end) if a.end else None

    ref = pairs(json.load(open(a.ref)))
    test = pairs(json.load(open(a.test)))

    def in_window(e):
        d = et_date(e["timestamp"])
        return (start is None or d >= start) and (end is None or d <= end)

    ref_w = [p for p in ref if in_window(p[0])]
    ref_cmp = [p for p in ref_w if end is None or et_date(p[1]["timestamp"]) <= end]
    ref_uncmp = [p for p in ref_w if p not in ref_cmp]
    test_w = [p for p in test if in_window(p[0])]

    print(f"reference trades in window: {len(ref_w)}  (comparable: {len(ref_cmp)}, exit after window end: {len(ref_uncmp)})")
    print(f"test trades in window:      {len(test_w)}")

    rk = [key(*p) for p in ref_cmp]
    tk = [key(*p) for p in test_w]
    n = min(len(rk), len(tk))
    first_mismatch = next((i for i in range(n) if rk[i] != tk[i]), None)
    exact = (len(rk) == len(tk)) and first_mismatch is None
    if exact:
        print(f"EXACT MATCH: {len(rk)} trades identical on {len(ENTRY_FIELDS)} entry + {len(EXIT_FIELDS)} exit fields")
    else:
        print("MISMATCH")
        if first_mismatch is not None:
            i = first_mismatch
            re_, rx = ref_cmp[i]
            te, tx = test_w[i]
            print(f"  first divergence at trade #{i} (ref entry {re_['timestamp']}, test entry {te['timestamp']})")
            for f in ENTRY_FIELDS:
                if norm(re_.get(f)) != norm(te.get(f)):
                    print(f"    entry.{f}: ref={re_.get(f)!r} test={te.get(f)!r}")
            for f in EXIT_FIELDS:
                if norm(rx.get(f)) != norm(tx.get(f)):
                    print(f"    exit.{f}: ref={rx.get(f)!r} test={tx.get(f)!r}")
        else:
            print(f"  same prefix of {n} trades, then counts differ ({len(rk)} vs {len(tk)})")
    ref_pnl = sum(p[1]["adjusted_pnl"] for p in ref_cmp)
    test_pnl = sum(p[1]["adjusted_pnl"] for p in test_w)
    print(f"sum adjusted_pnl: ref {ref_pnl:+.2f}  test {test_pnl:+.2f}")
    sys.exit(0 if exact else 1)


if __name__ == "__main__":
    main()
