#!/usr/bin/env python3
"""CANDIDATE CORPUS EXPORT — every scanner candidate, every day, one file.

    python -m scripts.export_candidate_corpus            # full history
    python -m scripts.export_candidate_corpus --since 2026-01-01

The hand-off dataset for (a) the elicitation labeling drive — Angus calls
take/skip + why on real historical setups at volume — and (b) ai-trading-v2's
statistical grading (seven gates, walk-forward, holdout). One row per
candidate emitted by the CERTIFIED scanner (scripts/offline_scan.py —
reproduces the Mac-adjudicated candidate minutes 100% on the certified era;
no-lookahead proven by scripts/gate_offline_causality.py).

Row fields:
  sess_day, minute, window, direction, shape, tfs, price,
  second_levels_closed, second_levels_rejected,
  chop_state/chop_context/chop_width/chop_zone   (chop v2, as-of, causal)
  drift_2h                                        (sign of 2h close drift)
  dow                                             (0=Mon session-day anchor)
  mech_entry, mech_stop, mech_rpts                (decision close; last-15m
                                                   extreme +2pt, floored at
                                                   0.75x trailing 2m range)
  mech_outcome (2R|STOP|FLAT), mech_best_r        (120m walk, 2R-capped)
  reserved     (tag: tape already used by agent runs — hold out or handle)

The mechanical outcome model is deliberately crude and IDENTICAL to the
pass-ledger model used in this repo's own analyses — a finder/ranker, not a
P&L. v2 should re-derive outcomes its own way from bars; entry/stop are
included so any re-model is anchored.

NO-LOOKAHEAD: every feature is as-of (bars strictly before the decision
minute); the outcome walk reads only forward bars, as an outcome should.
Calibration constants inside chop v2 are frozen on 2026-01..04.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.chop_state import state_at                           # noqa: E402
from scripts.offline_scan import scan_day, FULL_WINDOWS           # noqa: E402

RESERVED = {
    # tapes already consumed by agent runs / narration — flag for holdout
    "2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25",
    "2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04",
    "2026-07-05", "2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09",
}


def price_mech(bars, day, hm, side):
    _, t = OB.session_bounds(day, hm)
    hist = bars[(bars.index >= t - pd.Timedelta(minutes=15)) & (bars.index < t)]
    if len(hist) < 10:
        return None
    entry = float(hist.close.iloc[-1])
    r2 = hist.resample("2min").agg({"high": "max", "low": "min"}).dropna()
    floor = 0.75 * float((r2.high - r2.low).mean())
    stop = max(float(hist.high.max()) + 2.0, entry + floor) if side == "short" \
        else min(float(hist.low.min()) - 2.0, entry - floor)
    rpts = abs(entry - stop)
    seg = bars[(bars.index >= t) & (bars.index < t + pd.Timedelta(minutes=120))]
    best = 0.0
    for _, b in seg.iterrows():
        if side == "short":
            if b.high >= stop:
                return entry, stop, rpts, "STOP", best
            best = max(best, (entry - float(b.low)) / rpts)
        else:
            if b.low <= stop:
                return entry, stop, rpts, "STOP", best
            best = max(best, (float(b.high) - entry) / rpts)
        if best >= 2.0:
            return entry, stop, rpts, "2R", best
    return entry, stop, rpts, "FLAT", best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default=None)
    ap.add_argument("--full-day", action="store_true",
                    help="sweep ASIA/LONDON/NY full-day windows (his 2026-08-20 frequency ruling)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    bars = OB.get_bars()
    days = OB.all_session_days(bars)
    if a.since:
        days = [d for d in days if d >= a.since]
    out = ROOT / (a.out or ("output/analysis/candidate_corpus_fullday.jsonl.gz"
                            if a.full_day else "output/analysis/candidate_corpus.jsonl.gz"))
    win = FULL_WINDOWS if a.full_day else None
    out.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with gzip.open(out, "wt") as fh:
        for i, day in enumerate(days):
            try:
                cands = scan_day(bars, day, windows=win) if win else scan_day(bars, day)
            except Exception as e:
                print(f"{day}: scan failed ({type(e).__name__})", flush=True)
                continue
            for c in cands:
                hm = c["minute"]
                side = "short" if c["direction"] == "DOWN" else "long"
                try:
                    ch = state_at(bars, day, hm)
                except Exception:
                    ch = {}
                mech = price_mech(bars, day, hm, side)
                _, t = OB.session_bounds(day, hm)
                h2 = bars[(bars.index >= t - pd.Timedelta(hours=2)) & (bars.index < t)]
                drift = 0
                if len(h2):
                    d = float(h2.close.iloc[-1]) - float(h2.close.iloc[0])
                    drift = 1 if d > 0 else (-1 if d < 0 else 0)
                row = {
                    "sess_day": day, "minute": hm, "window": c.get("window"),
                    "direction": c["direction"], "side": side,
                    "shape": c.get("shape"), "tfs": c.get("tfs"),
                    "price": c.get("price"),
                    "second_levels_closed": c.get("second_levels_closed"),
                    "second_levels_rejected": c.get("second_levels_rejected"),
                    "chop_state": ch.get("state"), "chop_context": ch.get("context"),
                    "chop_width": ch.get("range_width"), "chop_zone": ch.get("zone_now"),
                    "drift_2h": drift,
                    "dow": pd.Timestamp(day).dayofweek,
                    "reserved": day in RESERVED,
                }
                if mech:
                    e, s, r, res, best = mech
                    row.update({"mech_entry": e, "mech_stop": s,
                                "mech_rpts": round(r, 2), "mech_outcome": res,
                                "mech_best_r": round(best, 3)})
                fh.write(json.dumps(row) + "\n")
                n += 1
            if i % 50 == 0:
                print(f"[{i}/{len(days)}] {day} — {n} rows", flush=True)
    print(f"DONE: {n} candidates across {len(days)} days -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
