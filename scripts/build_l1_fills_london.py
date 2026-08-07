#!/usr/bin/env python3
"""L1 LONDON — entry mechanics over the L0 London census: which candidates does the
market let you into.

Authorised by docs/PREREG-london-canon-rebuild.md. Mirrors scripts/build_l1_fills.py
(NY) and REUSES its walk, deliberately — the handoff's rule is reuse the as-of-clean
builders, never reimplement. `walk_one` is imported, not copied, so the London fill
model cannot drift from the NY one.

THE TWO LONDON DIFFERENCES, both from standing rulings:

1. ORDERS DIE AT THE LONDON WINDOW END, per day, DST-correct (03:00-05:00 ET normally,
   04:00-06:00 on misaligned weeks). NY expires at a fixed 11:00 ET. ANGUS: *"the order
   lives while its session window lives"*.

2. NO DISTANCE CANCEL is the London default. NY ships a 22pt distance cancel; the London
   ruling is that orders are not cancelled on distance at all. So `arm_none` IS the
   standing policy here, and the distance arm is recorded ONLY as a comparison column —
   it is not the control and it is not enforced.

ONE WALK, ALL POLICIES. Cancel rules only ever REMOVE fills, so every trigger is walked
once with NOTHING enforced and the events each rule keys on are recorded. Policies become
derived boolean columns and any future one is a filter over this artifact, not a rebuild.

INDEPENDENT WALKS, DELIBERATELY. simulate() holds one order at a time and silently skips
triggers while one rests — execution capacity shaping the population, the same defect
class as a trade cap. L1 walks each trigger as if it were the only order; capacity is
re-imposed at L4 where it is a declared policy. The gate handles the difference by
requiring engine fills to be a SUBSET of L1's.

    python -m scripts.build_l1_fills_london --gate     # engine fidelity, 2 days
    python -m scripts.build_l1_fills_london --span fit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l1_fills import T_CANCEL, TICK, load_bars, walk_one  # noqa: E402
from scripts.build_l0_triggers_london import window_et  # noqa: E402

NY = "America/New_York"
PREREG = "docs/PREREG-london-canon-rebuild.md"


def run(trigs: pd.DataFrame, bars: pd.DataFrame, quiet: bool = False) -> pd.DataFrame:
    """Walk every L0 London trigger once. Orders expire at that day's London window end."""
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(ts_et=ts, trig_hm=ts.dt.hour * 60 + ts.dt.minute)
    if "day" not in trigs:
        trigs["day"] = ts.dt.strftime("%Y-%m-%d")
    bday = bars.mi.dt.strftime("%Y-%m-%d")
    rows = []
    for day, g in trigs.groupby("day", sort=True):
        _, end = window_et(day, ("08:00", "10:00"))     # per-day, DST-correct
        db = bars[(bday == day) & (bars.mi <= end)]
        if db.empty:
            continue
        arrs = {"mi": db.mi.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(),
                "o": db.open.to_numpy(float), "h": db.high.to_numpy(float),
                "l": db.low.to_numpy(float)}
        for r in g.itertuples():
            t = {"direction": r.direction, "entry_ref": float(r.entry_ref),
                 "close": float(r.close), "level_stack": r.level_stack,
                 "ts64": r.ts_et.tz_convert("UTC").tz_localize(None)}
            lim = round(round(r.entry_ref / TICK) * TICK, 10)
            stp = round(round(r.stop_ref / TICK) * TICK, 10)
            rows.append({
                "day": day, "ts": r.ts, "tf": r.tf, "direction": r.direction,
                "kind": r.kind, "pattern": r.pattern, "htf_flag": r.htf_flag,
                "trig_hm": int(r.trig_hm),
                "lon_min": int((r.ts_et - window_et(day, ("08:00", "10:00"))[0])
                               .total_seconds() // 60),
                "limit": lim, "stop": stp, "risk_intended": round(abs(lim - stp), 2),
                "close": float(r.close), "confluence_count": int(r.confluence_count),
                "vwap_touched": bool(r.vwap_touched),
                "cluster_types": list(r.cluster_types),
                "cluster_members": r.cluster_members, "level_stack": r.level_stack,
                **walk_one(arrs, t)})
        if not quiet:
            print(f"  {day}: {len(g):>3} triggers", flush=True)
    F = pd.DataFrame(rows)
    # arm_none IS the London standing policy (no distance cancel). The others are
    # recorded for comparison and are NOT enforced anywhere in this file.
    F["arm_none"] = F.status == "filled"
    F["arm_struct"] = F.arm_none & (F.struct_event != "rejected")
    F["arm_dist22"] = F.arm_none & (F.max_away_before_fill < T_CANCEL)   # NY's policy, FYI
    return F


def gate() -> bool:
    """GATE — engine subset reproduction. Every fill the real engine produces over the
    same triggers, with an uncapped London config, must match an L1 fill on trigger ts,
    fill minute and entry price. L1 may have MORE fills (no serialization); it may never
    disagree about one the engine found."""
    from datetime import time as dtime

    from scripts.build_l0_triggers_london import load_bars as l0_bars, run_days
    from src.backtest.engine import load_backtest_config, simulate
    from src.engine.triggers import Trigger

    # DST-aligned days only, so the engine's fixed ET window equals the London window.
    # Six of them, not NY's two: the engine serializes hard in this window (one order at a
    # time over two hours), so a two-day gate only checks a handful of fills.
    days = ["2025-06-10", "2025-07-22", "2025-09-17", "2025-12-03",
            "2026-04-15", "2026-06-24"]
    raw = l0_bars()
    trigs = run_days(raw, days, ("08:00", "10:00"), procs=2, quiet=True)
    F = run(trigs, load_bars(), quiet=True)

    cfg = load_backtest_config().model_copy(update={
        "win_start": dtime(3, 0), "win_end": dtime(5, 0), "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None})
    drop = {"day", "et_hour_start"}
    tobjs = [Trigger(**{k: v for k, v in r.items() if k not in drop})
             for r in trigs.to_dict("records")]
    ok, n_eng = True, 0
    for day in days:
        dtr = [t for t in tobjs if t.ts[:10] == day]
        seg = raw[(raw.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY) - pd.Timedelta(days=30))
                  & (raw.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))]
        tr, _, _ = simulate(seg.reset_index(drop=True), dtr, cfg)
        for e in tr:
            n_eng += 1
            m = F[(F.ts == e.trigger_ts) & (F.status == "filled")]
            row = m.iloc[0] if len(m) else None
            good = (row is not None and abs(row.fill_px - e.entry) < 1e-6
                    and pd.Timestamp(row.fill_ts) == pd.Timestamp(e.fill_ts))
            if not good:
                ok = False
                print(f"  MISMATCH {day} {e.trigger_ts}: engine {e.fill_ts} @ {e.entry} vs "
                      f"L1 {'no fill' if row is None else (row.fill_ts, row.fill_px)}")
    print(f"engine fills checked: {n_eng} | L1 rows {len(F)} "
          f"(filled {int(F.arm_none.sum())})")
    print("gate OK — every engine fill reproduced exactly; L1 is the engine's fill model "
          "minus serialization and cancels" if ok else
          "GATE FAILED — do not build L2 on this until explained")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", default="",
                    help="census arm suffix, e.g. `_pp` for the prior-session-profile L0. "
                         "Suffixes input AND output so an arm never overwrites the baseline.")
    a = ap.parse_args()
    if a.gate:
        return 0 if gate() else 1
    if not a.span:
        ap.error("--span fit or --gate")

    src = ROOT / f"output/l0_triggers_london_fit_std{a.arm}.parquet"
    if not src.exists():
        ap.error(f"{src.relative_to(ROOT)} does not exist — build that L0 arm first")
    trigs = pd.read_parquet(src)
    F = run(trigs, load_bars())
    out = ROOT / f"output/l1_fills_london_fit{a.arm}.parquet"
    F.to_parquet(out, index=False)
    fl = F[F.arm_none]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F):,} candidates on {F.day.nunique()} days")
    print(f"filled {len(fl):,} ({len(fl)/max(len(F),1):.0%}) | "
          f"arm_struct {int(F.arm_struct.sum()):,} | arm_dist22 (NY policy, FYI) "
          f"{int(F.arm_dist22.sum()):,}")
    print(f"struct events on filled: {fl.struct_event.value_counts().to_dict()}")
    print(f"median mins_to_fill {fl.mins_to_fill.median():.0f} | "
          f"median intended risk {fl.risk_intended.median():.2f}pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
