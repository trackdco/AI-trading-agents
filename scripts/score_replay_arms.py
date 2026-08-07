#!/usr/bin/env python3
"""Score the walk-forward replay arms A vs B (Pat lane — the scoreboard).

Arm A = static champion (Blend v1.1, docs/CHAMPION-v1.1-FROZEN.md): per day pick the
E3 (balance) or E4 (war) book by the pre-open imbal_share_20>=0.5 switch, run that
book's triggers, sum dollars. This reproduces the frozen baseline exactly (same books,
switch, config, trigger caches as scripts/l2_analog_benchmark.py).

Arm B = SAME champion, plus the agents' combined de-risk gate on top
(output/combined_gate_schedule.csv via simulate(day_gate=...)). The two arms differ
ONLY on days the agents ruled; every other day is identical by construction, so the
delta is purely the agents' effect.

    python -m scripts.score_replay_arms                 # scores every day the agents ruled
    python -m scripts.score_replay_arms --start 2026-03-01 --end 2026-03-31

Arm C (with news) is the same harness once the news archive lands; not run here.
"""

from __future__ import annotations

import argparse
import ast
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.desk.combined_gate import day_gate_from_schedule  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

TRIGGER_CACHES = ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv",
                  "output/triggers_junjul_ob.csv"]
SCHEDULE = Path("output/combined_gate_schedule.csv")
VECTOR = Path("output/regime_vector.csv")
PARQUET = Path("data/reference/nq_1m_feb_jul2026.parquet")


def _load_triggers() -> list[Trigger]:
    out = []
    for path in TRIGGER_CACHES:
        if not Path(path).exists():
            continue
        for r in pd.read_csv(path).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def _books(base):
    # frozen champion books (l2 benchmark parity): E3+V8 balance book, E4 tight war book
    return {"E3": base.model_copy(update={"mgmt_variant": "V8"}),
            "E4": base.model_copy(update={"entry_variant": "E4"})}


def _per_day_dollars(df, trigs, cfgs, day_gate=None) -> dict:
    """Run BOTH books over the data (optionally gated); return {date: {E3, E4}} dollars."""
    daily: dict = {}
    for book, tt in (("E3", trigs),
                     ("E4", [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0])):
        tr, _, _ = simulate(df, tt, cfgs[book], day_gate=day_gate)
        for r in tr:
            daily.setdefault(r.trade_date, {"E3": 0.0, "E4": 0.0})[book] += r.dollars
    return daily


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="0000")
    ap.add_argument("--end", default="9999")
    args = ap.parse_args(argv)

    if not SCHEDULE.exists():
        print(f"no gate schedule at {SCHEDULE} — run the agents + build_gate_schedule first")
        return 1
    ruled = {str(d) for d in pd.read_csv(SCHEDULE)["date"]
             if args.start <= str(d) <= args.end}
    if not ruled:
        print("no ruled days in range")
        return 0

    df = pd.read_parquet(PARQUET)
    # slice to the ruled range (+ a lead-in for prior-day/warm-up context) — scoring a
    # few days does not need the full 161k-bar dataset simulated four times
    lo = (pd.Timestamp(min(ruled), tz="America/New_York") - pd.Timedelta(days=5))
    hi = (pd.Timestamp(max(ruled), tz="America/New_York") + pd.Timedelta(days=2))
    df = df[(df["ts_event"] >= lo) & (df["ts_event"] <= hi)].reset_index(drop=True)
    base = load_backtest_config().model_copy(update={"win_end": dtime(10, 15),
                                                     "max_trades_per_day": 2})
    cfgs = _books(base)
    dg = day_gate_from_schedule(SCHEDULE)
    trigs = [t for t in _load_triggers()
             if lo <= pd.Timestamp(t.ts) <= hi]

    a = _per_day_dollars(df, trigs, cfgs, day_gate=None)   # arm A
    b = _per_day_dollars(df, trigs, cfgs, day_gate=dg)     # arm B

    vec = pd.read_csv(VECTOR).set_index("day")

    def book(day: str) -> str:
        if day not in vec.index:
            return "E3"
        s = vec.loc[day, "imbal_share_20"]
        return "E4" if (pd.notna(s) and s >= 0.5) else "E3"

    rows = []
    for d in sorted(ruled):
        bk = book(d)
        pa = a.get(d, {}).get(bk, 0.0)
        pb = b.get(d, {}).get(bk, 0.0)
        rows.append({"day": d, "book": bk, "armA_$": round(pa, 0),
                     "armB_$": round(pb, 0), "delta_$": round(pb - pa, 0)})
    sb = pd.DataFrame(rows)
    ta, tb = sb["armA_$"].sum(), sb["armB_$"].sum()
    print(f"\nReplay scoreboard — {len(sb)} agent-ruled days ({args.start}..{args.end})\n")
    print(sb.to_string(index=False))
    print(f"\n  arm A (static champion)     : ${ta:+,.0f}")
    print(f"  arm B (champion + agents)   : ${tb:+,.0f}")
    print(f"  agents' effect on these days: ${tb - ta:+,.0f}")
    print("\n(Days the agents did NOT rule are identical in both arms by construction.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
