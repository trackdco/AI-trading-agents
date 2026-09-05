#!/usr/bin/env python3
"""
Equivalence test for fast_features.py: replay N bars from a saved engine state with the ORIGINAL
feature-engine methods and with the fast ones, dumping per-bar snapshot fields, the full zone
state (every order block / gap with flags and fill), engine counters and trade records.
The two dumps must be identical.  usage: test_fast_features.py {original,fast} CKPT N OUT.json
"""
import asyncio
import json
import pickle
import sys
import time

sys.argv, mode, ckpt, N, out = sys.argv[:1], sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
import retest_backtest as rb  # noqa: E402

main = sys.modules["__main__"]
main.RetestEngine = rb.RetestEngine
main.BoundedList = rb.BoundedList
if mode == "fast":
    import fast_features
    fast_features.install()

st = pickle.load(open(ckpt, "rb"))
eng = st["engine"]
eng._patch_executor()
fb = rb.fb
B = "/home/user/prat617/ai-trading-bot/nq_bot_vscode/data/historical"
bars = fb.aggregate_to_2m(fb.load_1min_csv(B + "/combined_1min.csv"))
sched = fb.HTFScheduler(fb.load_all_htf(B))
sched._indices = st["sched_indices"]
rb._sxe.uuid = rb._SequentialUUID()
rb._sxe.uuid.n = st["ids"]
i0 = st["next_bar"]
seq = bars[i0:i0 + N]
n_rec0 = len(eng.trades)

snaps = []
orig_update = eng.feature_engine.update
FIELDS = ("atr_14", "session_vwap", "near_bullish_ob", "near_bearish_ob", "inside_bullish_fvg",
          "inside_bearish_fvg", "recent_buy_sweep", "recent_sell_sweep", "structural_stop_long",
          "structural_stop_short", "trend_direction", "trend_strength")


def logged_update(bar):
    s = orig_update(bar)
    snaps.append([getattr(s, f, None) for f in FIELDS] + [len(getattr(s, "active_order_blocks", [])),
                                                            len(getattr(s, "active_fvgs", [])),
                                                            len(getattr(s, "recent_sweeps", []))])
    return s


eng.feature_engine.update = logged_update


async def drive():
    for b in seq:
        await eng.process_bar(b, sched)

t0 = time.time()
asyncio.run(drive())
el = time.time() - t0
fe = eng.feature_engine
dump = {
    "mode": mode, "bars": N, "elapsed": round(el, 1), "bars_per_sec": round(N / el, 1),
    "snapshots": snaps,
    "obs": [(o.direction, o.zone_high, o.zone_low, o.bar_index, o.is_valid, o.mitigated, o.detected_at.isoformat()) for o in fe._order_blocks],
    "fvgs": [(f.gap_type, f.gap_high, f.gap_low, f.gap_size, f.is_inverse, f.filled_pct, f.is_valid, f.detected_at.isoformat()) for f in fe._fvgs],
    "sweeps": [(s.sweep_type, s.swept_level, s.sweep_price, s.confirmed) for s in fe._sweeps],
    "counters": [eng._entry_count, eng._rejection_count, eng._signals_with_direction, eng._bars_processed,
                 round(eng._cumulative_pnl, 6), eng.sweep_detector.total_sweeps_confirmed],
    "new_records": eng.trades[n_rec0:],
    "pending": eng._pending_entry,
}
json.dump(dump, open(out, "w"), default=str)
print(f"{mode}: {N} bars in {el:.1f}s = {N/el:.1f} bars/s | obs {len(fe._order_blocks)} fvgs {len(fe._fvgs)} | new records {len(dump['new_records'])}")
