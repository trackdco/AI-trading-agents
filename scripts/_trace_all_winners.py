#!/usr/bin/env python3
"""Batched order-build trace of all 18 MISSED winners (one process, data loaded once).
For each winner, take the nearest same-direction trigger to Angus's entry time and show the
engine's order-build outcome under E1 (BB basis) vs E3 (reclaim level) entry, at rr_floor 1.5.
This isolates the entry-model + target/RR mechanism per winner (fills/halts are separate; the
arm sweep captures those end-to-end)."""
import ast
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import default_target_resolver, load_backtest_config  # noqa: E402
from src.engine.indicators import indicators_asof, load_indicators_config  # noqa: E402
from src.engine.sessions import load_news_calendar  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
FLOOR = 1.5
MIN_STOP = 10.0

# (date, HH:MM, dir, hand_R, hand_TF, report_gate)
WINNERS = [
    ("2026-02-04", "09:48", "short", 3.30, "5min", "rr_floor"),
    ("2026-02-04", "10:30", "short", 3.57, "5min", "rr_floor"),
    ("2026-02-05", "09:36", "long",  2.15, "2min", "tcancel"),
    ("2026-02-06", "10:20", "long",  2.62, "5min", "rr_floor"),
    ("2026-02-09", "09:36", "long",  3.31, "1min", "tcancel"),
    ("2026-02-12", "09:40", "short", 3.37, "2min", "rr_floor"),
    ("2026-02-17", "09:32", "long",  3.69, "1min", "bad_geometry"),
    ("2026-02-17", "09:50", "short", 3.88, "2min", "bad_geometry"),
    ("2026-02-18", "08:35", "short", 4.17, "5min", "bb_vwap"),
    ("2026-02-18", "09:53", "long",  4.78, "1min", "tcancel"),
    ("2026-02-20", "08:06", "long",  4.79, "3min", "news_preopen"),
    ("2026-02-20", "09:31", "long",  3.18, "1min", "tcancel"),
    ("2026-02-20", "10:33", "long",  3.22, "3min", "bad_geometry"),
    ("2026-02-23", "10:20", "short", 2.74, "5min", "rr_floor"),
    ("2026-02-24", "08:20", "long",  3.67, "5min", "bad_geometry"),
    ("2026-02-25", "09:25", "long", 12.98, "5min", "min_stop"),
    ("2026-02-26", "09:18", "short", 4.22, "3min", "position_open"),
    ("2026-02-27", "09:54", "long",  4.62, "3min", "min_stop"),
]


def load_triggers():
    rows = pd.read_csv("output/triggers_feb.csv").to_dict("records")
    for r in rows:
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
    return [Trigger(**r) for r in rows]


def orderbuild(t, entry, resolve, cfg):
    """Mirror engine order-build gates. Returns (verdict, detail)."""
    sgn = 1 if t.direction == "long" else -1
    stop = t.stop_ref
    risk = sgn * (entry - stop)
    if risk <= 0:
        return "bad_geometry", f"risk={risk:+.1f}"
    if risk < MIN_STOP:
        return "min_stop", f"risk={risk:.1f}<{MIN_STOP:g}"
    tgt = resolve(t, entry, stop)
    if not tgt:
        return "no_target", ""
    name, level, _ = tgt
    working = level - sgn * cfg.front_run
    rr = sgn * (working - entry) / risk
    if rr < FLOOR:
        return "rr_floor", f"RR{rr:.2f} {name}"
    return "TRADE", f"RR{rr:.2f}->{name}"


def main():
    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    df = pd.read_parquet(full if full.exists() else ref)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)
    cfg = load_backtest_config()
    cal = load_news_calendar()
    resolve = default_target_resolver(feb, cal)
    trigs = load_triggers()
    icfg = load_indicators_config()

    print(f"{'winner':22s} {'handR':>6s} {'rep_gate':13s} | {'E1(bb)':>18s} | {'E3(reclaim)':>18s}")
    print("-" * 95)
    recov_e1 = recov_e3 = 0
    for date, hhmm, d, hr, tf, gate in WINNERS:
        tts = pd.Timestamp(f"{date} {hhmm}", tz=NY)
        cand = [t for t in trigs if pd.Timestamp(t.ts).date() == tts.date() and t.direction == d]
        # prefer same TF within 5 min, else nearest by time
        near = sorted(cand, key=lambda t: (abs((pd.Timestamp(t.ts) - tts).total_seconds())))
        pick = next((t for t in near if t.tf == tf
                     and abs((pd.Timestamp(t.ts) - tts).total_seconds()) <= 300), None)
        if pick is None:
            pick = near[0] if near else None
        if pick is None:
            print(f"{date} {hhmm} {d:5s}  {hr:>5.2f}  {gate:13s} | NO TRIGGER")
            continue
        ind = indicators_asof(feb, pd.Timestamp(pick.ts), icfg)
        bb = ind["tfs"].get(pick.tf, {}).get("bb_basis")
        e1v = orderbuild(pick, bb, resolve, cfg) if bb is not None else ("no_bb", "")
        e3v = orderbuild(pick, pick.entry_ref, resolve, cfg)
        recov_e1 += e1v[0] == "TRADE"
        recov_e3 += e3v[0] == "TRADE"
        label = f"{date[5:]} {hhmm} {d}"
        print(f"{label:22s} {hr:>6.2f} {gate:13s} | {e1v[0]:>8s} {e1v[1]:>9s} | {e3v[0]:>8s} {e3v[1]:>9s}")
    n = len(WINNERS)
    print("-" * 95)
    print(f"order-build clears (would TRADE) @ floor {FLOOR}:  E1(bb)={recov_e1}/{n}   E3(reclaim)={recov_e3}/{n}")
    print("(note: 'TRADE' = clears geometry/min_stop/target/RR; actual fill/halt/one-position are separate -> see arm sweep)")


if __name__ == "__main__":
    main()
