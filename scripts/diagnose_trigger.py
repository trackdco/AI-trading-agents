#!/usr/bin/env python3
"""Diagnostic replay: dump the engine's entry/stop/target/cluster state for the trigger
nearest a (date, HH:MM, direction). This is the programmatic version of an eyeball chart
replay — it answers "why did the engine take / veto this?" with the exact numbers.

    python scripts/diagnose_trigger.py 2026-02-12 09:40 short
    python scripts/diagnose_trigger.py 2026-02-25 09:25 long
"""
import ast
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import (  # noqa: E402
    default_target_resolver, load_backtest_config,
)
from src.engine.indicators import indicators_asof, load_indicators_config  # noqa: E402
from src.engine.snapshot import build_snapshot  # noqa: E402
from src.engine.sessions import load_news_calendar  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"


def load_triggers() -> list[Trigger]:
    rows = pd.read_csv("output/triggers_feb.csv").to_dict("records")
    for r in rows:
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
    return [Trigger(**r) for r in rows]


def main():
    date, hhmm, direction = sys.argv[1], sys.argv[2], sys.argv[3]
    target_ts = pd.Timestamp(f"{date} {hhmm}", tz=NY)

    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    df = pd.read_parquet(full if full.exists() else ref)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)
    cfg = load_backtest_config()
    cal = load_news_calendar()

    trigs = [t for t in load_triggers()
             if pd.Timestamp(t.ts).date() == target_ts.date() and t.direction == direction]
    if not trigs:
        print(f"no {direction} triggers on {date}")
        return
    # nearest by |ts - target|, prefer within 15 min
    trigs.sort(key=lambda t: abs((pd.Timestamp(t.ts) - target_ts).total_seconds()))
    print(f"### {date} {hhmm} {direction} — {len(trigs)} same-day {direction} triggers; "
          f"showing nearest 3 by time\n")

    resolve = default_target_resolver(feb, cal)
    for t in trigs[:3]:
        ts = pd.Timestamp(t.ts)
        off = (ts - target_ts).total_seconds() / 60
        print(f"--- trigger {ts:%H:%M} {t.tf} {t.kind} pattern={t.pattern} "
              f"htf={t.htf_flag} ({off:+.0f}m from target)")
        print(f"    cluster_types={sorted(t.cluster_types)} conf={t.confluence_count} "
              f"center={t.cluster_center:.2f}")
        print(f"    wick_low={t.wick_low:.2f} wick_high={t.wick_high:.2f} "
              f"entry_ref(E3)={t.entry_ref:.2f} stop_ref={t.stop_ref:.2f}")
        # E1 entry = BB basis of the trigger TF
        ind = indicators_asof(feb, ts, load_indicators_config())
        tf_ind = ind["tfs"].get(t.tf, {})
        bb_basis = tf_ind.get("bb_basis")
        bb_u = tf_ind.get("bb_upper")
        bb_l = tf_ind.get("bb_lower")
        # E1 = BB basis of the trigger TF (same as engine.entry_limit for E1)
        e1 = bb_basis if cfg.entry_variant == "E1" else (
            (t.wick_low + t.wick_high) / 2 if cfg.entry_variant == "E2" else t.entry_ref)
        sgn = 1 if direction == "long" else -1
        print(f"    BB[{t.tf}] basis={bb_basis} upper={bb_u} lower={bb_l}")
        if e1 is not None:
            stop = t.stop_ref
            risk = sgn * (e1 - stop)
            print(f"    E1 entry(bb_basis)={e1:.2f}  stop={stop:.2f}  risk={risk:+.2f}pt "
                  f"{'<< BAD GEOMETRY (risk<=0)' if risk <= 0 else ''}"
                  f"{'  << MIN_STOP (<10)' if 0 < risk < cfg.min_stop_points else ''}")
            if risk > 0:
                tgt = resolve(t, e1, stop)
                if tgt:
                    name, level, aux = tgt
                    working = level - sgn * cfg.front_run
                    rr = sgn * (working - e1) / risk
                    print(f"    TARGET picked: {name} @ {level:.2f}  RR={rr:.2f} "
                          f"{'<< RR_FLOOR VETO' if rr < cfg.rr_floor else ''}")
                    print(f"    (aux partial_level={aux.get('partial_level')} v2_band={aux.get('v2_band')})")
                else:
                    print("    TARGET: none beyond entry")
        # snapshot VWAP + BB menu levels and clusters
        snap = build_snapshot(feb, ts, calendar=cal)
        vwaps = [(lv.name, lv.price) for lv in snap.target_menu if lv.type == "vwap"]
        print(f"    snapshot VWAP menu levels: {[(n, round(p,2)) for n,p in vwaps]}")
        print(f"    clusters: {[(c.types, round(c.center,2)) for c in snap.clusters]}")
        # candle at trigger: did wick/body touch VWAP mid/±1?
        print()


if __name__ == "__main__":
    main()
