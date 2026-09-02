#!/usr/bin/env python3
"""L1 — entry mechanics over the L0 census: which candidates does the market let you into.

ONE WALK, ALL POLICIES. Cancel rules only ever REMOVE fills, so L1 walks every trigger once
with NO cancel enforced and records the EVENTS each rule would key on. The rules become
derived boolean columns, and any future cancel policy is a filter over this artifact rather
than a rebuild:

  arm_none    filled                                     (the control)
  arm_dist22  filled & max_away_before_fill < 22         (what ships today; same-bar priority
                                                          matches the engine: the fill bar's
                                                          away extreme counts)
  arm_struct  filled & struct_event != 'rejected'        (ANGUS 30-Jul: cancel when price ran
                                                          away, TESTED a structural level and
                                                          REJECTED hard back into the entry;
                                                          hold a drift that touched nothing,
                                                          regardless of distance)

Measured on gold before this was built (scratchpad virgin_vs_consumed / vwap_mid_reject):
the 22pt distance cancel keeps the worse half of fills (27% WR, -0.19R) and kills the better
half (36% WR, +0.08R); the away-level rejection bucket is the worst bucket in the sample
(14% WR on n=7 at the VWAP mid alone — L1 is where it gets a real sample, all levels).

INDEPENDENT WALKS, DELIBERATELY. simulate() works one order at a time, so a trigger that
fires while an order rests is silently skipped — execution capacity shaping the population,
same defect class as the cap. L1 walks each trigger as if it were the only order; L4's
chronological selection re-imposes one-position-at-a-time when it CHOOSES trades. The gate
handles the difference by checking engine fills are a SUBSET of arm_dist22, matching exactly.

E3 LIMITS ONLY. The universal entry is a limit on the retest (ANGUS 29-Jul: "i never market
order"). The old E4 market book is deliberately not rebuilt.

FILL MODEL (mirrored from engine.py, gate-verified): limit at entry_ref; fill when the bar
trades 1 tick through (lo <= limit - 0.25 long); gap-open fills at the open, never better
than the first traded price; unfilled orders expire at the band end (11:00 ET).

    python -m scripts.build_l1_fills --span fit
    python -m scripts.build_l1_fills --gate      # engine-subset fidelity check, 2 days
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
TICK = 0.25
THROUGH = 1 * TICK              # cfg.through_ticks * cfg.tick
T_CANCEL = 22.0                 # recorded, never enforced here
BAND_END = "11:00"
STRUCT_ACCEPT = 5.0             # pts traded beyond a level = acceptance, not a rejection
STRUCT_REJECT = 8.0             # pts back off a touched level = "rejects hard"

BARFILES = ["data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet",
            "data/reference/nq_1m_aug_sep2026.parquet"]


def load_bars() -> pd.DataFrame:
    parts = [pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
             for f in BARFILES]
    b = pd.concat(parts, ignore_index=True).drop_duplicates("ts_event")
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.sort_values("mi").reset_index(drop=True)


def walk_one(bars: dict, t: dict) -> dict:
    """One trigger, one independent walk from its close time to the band end.

    bars: dict of numpy arrays (mi, o, h, l, c) for the trigger's day band.
    Returns fill facts + the event record every cancel policy keys on."""
    s = 1 if t["direction"] == "long" else -1
    # engine parity (gate-discovered): the limit is tick-rounded at order placement, and the
    # working order is first evaluated on the bar AFTER the trigger bar — searchsorted 'right'.
    lim = round(round(t["entry_ref"] / TICK) * TICK, 10)
    close = t["close"]
    mi, o, h, lo = bars["mi"], bars["o"], bars["h"], bars["l"]
    i0 = int(np.searchsorted(mi, np.datetime64(t["ts64"]), side="right"))

    # away-side structural levels: at/beyond the trigger close in the run-away direction
    levels = [(n, p, ty) for n, p, ty in json.loads(t["level_stack"] or "[]")
              if s * (p - close) >= 0]
    touched = [False] * len(levels)
    struct_event = ""            # '' | 'rejected' | 'broke'
    struct_name = struct_type = ""
    struct_price = np.nan
    struct_ts = None

    max_away = 0.0
    fill_i = -1
    for i in range(i0, len(mi)):
        hi_i, lo_i = h[i], lo[i]
        max_away = max(max_away, (hi_i - lim) if s == 1 else (lim - lo_i))
        if not struct_event:
            for j, (n, p, ty) in enumerate(levels):
                if not touched[j] and lo_i <= p <= hi_i:
                    touched[j] = True
                if touched[j]:
                    beyond = (hi_i - p) if s == 1 else (p - lo_i)
                    back = (p - lo_i) if s == 1 else (hi_i - p)
                    if beyond >= STRUCT_ACCEPT:
                        struct_event, struct_name, struct_type = "broke", n, ty
                    elif back >= STRUCT_REJECT:
                        struct_event, struct_name, struct_type = "rejected", n, ty
                    if struct_event:
                        struct_price, struct_ts = p, mi[i]
                        break
        filled = (lo_i <= lim - THROUGH) if s == 1 else (hi_i >= lim + THROUGH)
        if filled:
            fill_i = i
            break

    out = {"max_away_before_fill": round(max_away, 2),
           "struct_event": struct_event, "struct_level": struct_name,
           "struct_level_type": struct_type, "struct_level_price": struct_price,
           "struct_ts": str(struct_ts) if struct_ts is not None else "",
           "n_away_levels": len(levels)}
    if fill_i < 0:
        out |= {"status": "expired", "fill_ts": "", "fill_px": np.nan, "fill_hm": -1,
                "mins_to_fill": -1}
        return out
    fp = min(lim, o[fill_i]) if s == 1 else max(lim, o[fill_i])
    fts = pd.Timestamp(mi[fill_i]).tz_localize("UTC").tz_convert(NY) \
        if pd.Timestamp(mi[fill_i]).tzinfo is None else pd.Timestamp(mi[fill_i])
    out |= {"status": "filled", "fill_ts": fts.isoformat(), "fill_px": round(float(fp), 2),
            "fill_hm": fts.hour * 60 + fts.minute,
            "mins_to_fill": int((mi[fill_i] - np.datetime64(t["ts64"]))
                                / np.timedelta64(1, "m"))}
    return out


def run(trigs: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    # trigger ts are ET ISO strings whose UTC offset flips across DST — parse via UTC
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(ts_et=ts, day=ts.dt.strftime("%Y-%m-%d"),
                         trig_hm=ts.dt.hour * 60 + ts.dt.minute)
    bday = bars.mi.dt.strftime("%Y-%m-%d")
    rows = []
    for day, g in trigs.groupby("day", sort=True):
        end = pd.Timestamp(f"{day} {BAND_END}", tz=NY)
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
            rows.append({
                "day": day, "ts": r.ts, "tf": r.tf, "direction": r.direction,
                "kind": r.kind, "pattern": r.pattern, "htf_flag": r.htf_flag,
                "trig_hm": int(r.trig_hm),
                "limit": round(round(r.entry_ref / TICK) * TICK, 10),
                "stop": round(round(r.stop_ref / TICK) * TICK, 10),
                "risk_intended": round(abs(round(round(r.entry_ref / TICK) * TICK, 10)
                                           - round(round(r.stop_ref / TICK) * TICK, 10)), 2),
                "close": float(r.close), "confluence_count": r.confluence_count,
                "cluster_members": r.cluster_members, "level_stack": r.level_stack,
                **walk_one(arrs, t)})
        print(f"  {day}: {len(g):>3} triggers", flush=True)
    F = pd.DataFrame(rows)
    F["arm_none"] = F.status == "filled"
    F["arm_dist22"] = F.arm_none & (F.max_away_before_fill < T_CANCEL)
    F["arm_struct"] = F.arm_none & (F.struct_event != "rejected")
    return F


def gate() -> None:
    """Fidelity: run the engine (uncapped E3, same band) over the same regenerated triggers.
    Engine fills are a SUBSET of arm_dist22 (its one-order-at-a-time serialization skips
    triggers L1 walks); every engine fill must match an L1 fill on trigger ts, fill minute
    and entry price, and no engine fill may land on an L1 row arm_dist22 excludes."""
    from datetime import time as dtime

    from scripts.build_l0_triggers import run_days
    from src.backtest.engine import load_backtest_config, simulate

    days = ["2025-06-10", "2025-09-17"]
    bars = load_bars()
    raw = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet").drop(
        columns=["roll"], errors="ignore")
    trigs = run_days(raw, days)
    F = run(trigs, bars)

    cfg = load_backtest_config().model_copy(update={
        "win_start": dtime(7, 45), "win_end": dtime(11, 0), "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None})
    from src.engine.triggers import Trigger
    tobjs = [Trigger(**{k: v for k, v in r.items()}) for r in trigs.to_dict("records")]
    ok, n_eng = True, 0
    for day in days:
        dtr = [t for t in tobjs if t.ts[:10] == day]
        seg = raw[(raw.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                   - pd.Timedelta(days=30))
                  & (raw.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))]
        tr, _, _ = simulate(seg.reset_index(drop=True), dtr, cfg)
        for e in tr:
            n_eng += 1
            m = F[(F.ts == e.trigger_ts) & (F.status == "filled")]
            row = m.iloc[0] if len(m) else None
            good = (row is not None and bool(row.arm_dist22)
                    and abs(row.fill_px - e.entry) < 1e-6
                    and pd.Timestamp(row.fill_ts) == pd.Timestamp(e.fill_ts))
            if not good:
                ok = False
                print(f"  MISMATCH {day} {e.trigger_ts}: engine fill {e.fill_ts} @ {e.entry}"
                      f" vs L1 {'no fill' if row is None else (row.fill_ts, row.fill_px, bool(row.arm_dist22))}")
    print(f"engine fills checked: {n_eng} | L1 rows: {len(F)} "
          f"(filled {int(F.arm_none.sum())}, arm_dist22 {int(F.arm_dist22.sum())})")
    if not ok:
        raise SystemExit("GATE FAILED — L1 fill mechanics diverge from the engine")
    print("gate OK — every engine fill reproduced exactly; L1 is the engine's fill model "
          "minus serialization and cancels")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.gate:
        return gate()
    if not a.span:
        raise SystemExit("--span or --gate required")
    trigs = pd.read_parquet(ROOT / f"output/l0_triggers_{a.span}.parquet")
    F = run(trigs, load_bars())
    out = Path(a.out) if a.out else ROOT / f"output/l1_fills_{a.span}.parquet"
    F.to_parquet(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} candidates on {F.day.nunique()} days")
    fl = F[F.arm_none]
    print(f"filled {len(fl)} ({len(fl) / max(len(F), 1) * 100:.0f}%) | "
          f"arm_dist22 {int(F.arm_dist22.sum())} | arm_struct {int(F.arm_struct.sum())}")
    print(f"struct events on filled: {fl.struct_event.value_counts().to_dict()}")
    print(f"median mins_to_fill: {fl.mins_to_fill.median():.0f} | "
          f"median risk: {fl.risk_intended.median():.1f}pt")


if __name__ == "__main__":
    main()
