#!/usr/bin/env python3
"""L2 — the outcome of every L0 candidate, walked independently through the REAL engine.

WHAT IT ANSWERS: the base strategy's honest performance before any selection — the number
the old pipeline never produced, because selection (caps, serialization, stop gates) was
fused into the same simulate() pass that produced outcomes.

NO RE-IMPLEMENTATION. Each trigger is run through `simulate()` itself, one trigger per call,
so entry vetoes, V8 management, partials, target resolution and EOD flatten are the engine's
own code path (the champion-vs-canon lesson: a faithful-to-spec rewrite shared 14% of trades
with the thing it rewrote). What changes is only the config:

  window 07:45-11:00, cap 99          the cap is L4 policy, not physics
  min_stop/post_open_min_stop 0       Layer-0 risk gates are L3/L4 policy
  max_stop_points None                same
  t_cancel effectively off            cancel rules are L1-derived columns; an outcome
                                      depends only on the fill, not on which cancel rule
                                      permitted it, so one outcome serves every arm
  no_trade window off                 the 09:30-09:40 cut is policy, applied downstream

WHAT SURVIVES INSIDE THE ENGINE, DELIBERATELY: tick rounding, bad-geometry veto, the §6
target menu with `rr_floor = 2.0` at order time (ANGUS 2026-07-17: "HARD 2R minimum every
trade" — part of the base strategy, not selection), V8 management with `rr_floor_partial`.
A candidate the engine refuses to order (no target / rr floor / bad geometry) is recorded
with that veto as its status — the census stays complete.

INDEPENDENT WALKS: one trigger per simulate() call kills the one-order-at-a-time
serialization the same way L1 does. L4 re-imposes it at selection time.

LOOKBACK: bars start LOOKBACK_DAYS before the day. --gate proves outcome invariance
against a 30-day lookback on sample days with real fills before the number is trusted.

    python -m scripts.build_l2_outcomes --span fit [--procs 3]
    python -m scripts.build_l2_outcomes --gate
"""
from __future__ import annotations

import argparse
import sys
from datetime import time as dtime
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
LOOKBACK_DAYS = 7
# nq_1m_jul_sep2026 closes the 2026-07-16 -> 2026-08-22 hole (spliced
# 2026-09-03, after the 2020-22 holdout was scored so that the holdout's
# baseline table kept describing the 927-day tape it was computed on).
# Overlap check on 14,616 shared minutes: 1 price bar differed (2.5pt on a
# low), 9 volume bars differed - ordinary vendor revision.
BARFILES = ["data/reference/nq_1m_master.parquet", "data/reference/nq_1m_jul_sep2026.parquet",
            "data/reference/nq_1m_feb_jul2026.parquet",
            "data/reference/nq_1m_aug_sep2026.parquet"]

_BARS: pd.DataFrame | None = None       # per-process cache (fork inherits the parent's copy)


_MGMT = "V8"        # module-level so Pool workers inherit it (exit-model arms: V5/V6
                     # walk the SAME fills with deeper structural targets — ANGUS 30-Jul,
                     # 2R floor hard, targets structural only, menu depth is the lever)


def l2_cfg(t_cancel: float = 100000.0):
    return load_backtest_config().model_copy(update={
        "win_start": dtime(7, 45), "win_end": dtime(11, 0), "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None, "t_cancel": t_cancel,
        "mgmt_variant": _MGMT})


def load_bars() -> pd.DataFrame:
    parts = [pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
             for f in BARFILES]
    return (pd.concat(parts, ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))


def day_outcomes(args) -> list[dict]:
    """All of one day's triggers, one simulate() each. Module-level for Pool pickling."""
    day, recs, lookback = args
    global _BARS
    if _BARS is None:
        _BARS = load_bars()
    seg = _BARS[(_BARS.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                 - pd.Timedelta(days=lookback))
                & (_BARS.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))].reset_index(drop=True)
    cfg = l2_cfg()
    out = []
    for rec in recs:
        t = Trigger(**{k: v for k, v in rec.items() if k in Trigger.model_fields})
        trades, verdicts, _ = simulate(seg, [t], cfg)
        row = {"day": day, "ts": t.ts, "tf": t.tf, "direction": t.direction,
               "kind": t.kind, "pattern": t.pattern, "htf_flag": t.htf_flag,
               "confluence_count": t.confluence_count,
               "cluster_members": rec.get("cluster_members", ""),
               "level_stack": rec.get("level_stack", "")}
        if trades:
            r = trades[0]
            risk = round(abs(float(r.limit_price) - float(r.stop_initial)), 4)
            row |= {"status": "outcome", "fill_ts": str(r.fill_ts), "entry": float(r.entry),
                    "stop": float(r.stop_initial), "risk": risk,
                    "exit_ts": str(r.exit_ts), "exit_price": float(r.exit_price),
                    "exit_reason": str(r.exit_reason), "target": str(r.target_name),
                    "target_level": float(r.target_level), "working_target": float(r.working_target),
                    "pts": float(r.points), "R": float(r.r_multiple),
                    "size_engine": float(r.size), "dollars_1lot": float(r.dollars),
                    "fill_hm": pd.Timestamp(r.fill_ts).hour * 60 + pd.Timestamp(r.fill_ts).minute}
        else:
            v = verdicts[0] if verdicts else None
            row |= {"status": v.status if v else "no_verdict",
                    "fill_ts": "", "fill_hm": -1, "R": float("nan")}
        out.append(row)
    return out


def run(trigs: pd.DataFrame, procs: int, lookback: int = LOOKBACK_DAYS) -> pd.DataFrame:
    # trigger ts are ET ISO strings whose UTC offset flips across DST — parse via UTC
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(day=ts.dt.strftime("%Y-%m-%d"))
    jobs = [(day, g.drop(columns=["day"]).to_dict("records"), lookback)
            for day, g in trigs.groupby("day", sort=True)]
    rows = []
    if procs <= 1:
        for j in jobs:
            rows.extend(day_outcomes(j))
            print(f"  {j[0]}: {len(j[1])} candidates", flush=True)
    else:
        with Pool(procs) as p:
            for day_rows in p.imap(day_outcomes, jobs):
                rows.extend(day_rows)
                if day_rows:
                    print(f"  {day_rows[0]['day']}: {len(day_rows)} candidates", flush=True)
    return pd.DataFrame(rows)


def gate(lb: int = LOOKBACK_DAYS) -> None:
    """Outcome invariance of lookback `lb` vs 30 days, on days with real fills. Any
    difference in fill/exit/dollars fails — a lookback that changes outcomes would corrupt
    every number downstream of L2. Reuses the L0 census when it exists (the gate days are
    parity-verified against it); regenerates only as a fallback."""
    days = ["2025-06-10", "2025-09-17"]
    census = ROOT / "output/l0_triggers_fit.parquet"
    if census.exists():
        T = pd.read_parquet(census)
        tday = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
        trigs = T[tday.dt.strftime("%Y-%m-%d").isin(days)].reset_index(drop=True)
    else:
        from scripts.build_l0_triggers import run_days
        raw = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet").drop(
            columns=["roll"], errors="ignore")
        trigs = run_days(raw, days)
    a = run(trigs, procs=2, lookback=lb)
    b = run(trigs, procs=2, lookback=30)
    cols = ["ts", "status", "fill_ts", "exit_ts"]
    fa, fb = a[a.status == "outcome"], b[b.status == "outcome"]
    same = (a[cols].reset_index(drop=True).equals(b[cols].reset_index(drop=True))
            and len(fa) == len(fb)
            and (fa.dollars_1lot.to_numpy() == fb.dollars_1lot.to_numpy()).all())
    print(f"candidates {len(a)} | outcomes {len(fa)} vs {len(fb)} (30d) | "
          f"1-lot ${fa.dollars_1lot.sum():+,.0f} vs ${fb.dollars_1lot.sum():+,.0f}")
    if not same:
        m = a[cols].compare(b[cols]) if len(a) == len(b) else None
        print(m)
        raise SystemExit(f"GATE FAILED — {lb}d lookback is not outcome-invariant")
    if len(fa) == 0:
        raise SystemExit("GATE INCONCLUSIVE — no filled outcomes on the sample days")
    print(f"gate OK — {lb}d lookback outcome-identical to 30d on "
          f"{len(fa)} real outcomes")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--lb", type=int, default=LOOKBACK_DAYS,
                    help="lookback days: gated variant for --gate, override for full runs")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--mgmt", default="V8", help="management/exit variant (V8 shipped; V5/V6 = partial at first structure, runner to deeper structural level)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.gate:
        return gate(a.lb)
    if not a.span:
        raise SystemExit("--span or --gate required")
    global _MGMT
    _MGMT = a.mgmt
    trigs = pd.read_parquet(ROOT / f"output/l0_triggers_{a.span}.parquet")
    F = run(trigs, procs=a.procs, lookback=a.lb)
    suffix = "" if a.mgmt == "V8" else f"_{a.mgmt.lower()}"
    out = Path(a.out) if a.out else ROOT / f"output/l2_outcomes_{a.span}{suffix}.parquet"
    F.to_parquet(out, index=False)
    oc = F[F.status == "outcome"]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} candidates, {len(oc)} outcomes")
    print(f"status: {F.status.value_counts().to_dict()}")
    if len(oc):
        print(f"1-lot: ${oc.dollars_1lot.sum():+,.0f} | WR {(oc.dollars_1lot > 0).mean() * 100:.0f}%"
              f" | mean R {oc.R.mean():+.3f} | median risk {oc.risk.median():.1f}pt")


if __name__ == "__main__":
    main()
