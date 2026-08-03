#!/usr/bin/env python3
"""L2 — LONDON: the outcome of every L0 candidate, walked independently through the REAL engine.

Mirrors scripts/build_l2_outcomes.py with the London window rule. Answers the base strategy's
honest London performance before any selection — the number the old pipeline never produced,
because selection (the 2-cap, serialization, stop gates) was fused into the same simulate()
pass that produced outcomes.

NO RE-IMPLEMENTATION. Each trigger runs through `simulate()` itself, one trigger per call, so
entry vetoes, V8 management, partials, target resolution and EOD flatten are the engine's own
code path. What changes is only the config:

  window = the DAY'S OWN London window   03:00-05:00 ET, or 04:00-06:00 on DST-shifted days
  cap 99                                 the 2-cap is L4 policy, not physics
  min_stop/post_open_min_stop 0          LON_RISK_MIN 9.5 is L3/L4 policy, not physics
  max_stop_points None                   same
  t_cancel effectively off               cancel rules are L1-derived columns; an outcome
                                         depends only on the fill, not on which cancel rule
                                         permitted it, so ONE outcome serves all three arms
  v8_be_at_open FALSE                    ANGUS 29-Jul: "don't do break even at 9:30"

THE v8_be_at_open RULING. V8 carries a "premarket fills -> BE at 09:29" belt written for NY
premarket entries. Every London fill is 03:00-06:00 ET, so it qualifies by construction and
forces BE on any London trade still alive ~4.5 hours later. Measured on the old book before
asking: it touches 8 of 445 trades (1.8%) — but those 8 averaged $216 against $12 for
everything else, i.e. it lands on the tail. Angus ruled it off for London. The flag defaults
True in engine.py so NY stays byte-identical; only this script sets it False. NOTE: the old
london_canon_book.parquet was built WITH the belt on, so L2 outcomes will not reproduce it —
that is an intended difference, not a gate failure.

WHAT SURVIVES INSIDE THE ENGINE, DELIBERATELY: tick rounding, bad-geometry veto, the §6 target
menu with `rr_floor = 2.0` at order time (ANGUS: "HARD 2R minimum every trade" — base strategy,
not selection), V8 partial + 5m-swing runner trail. A candidate the engine refuses to order is
recorded with that veto as its status, so the census stays complete.

INDEPENDENT WALKS: one trigger per simulate() call kills one-order-at-a-time serialization the
same way L1 does. This matters more for London than NY — L1 showed that with the distance
cancel off, "an order is already working" blocks 28 of 42 triggers on a sample day. L4
re-imposes capacity at selection time and will have to price that.

LOOKBACK: bars start LOOKBACK_DAYS before the day. --gate proves outcome invariance against a
30-day lookback on sample days with real fills. NY's 2d attempt failed this honestly (the
target menu lost far levels); 7d is the tested starting point.

    python -m scripts.build_l2_outcomes_london --gate        # run FIRST
    python -m scripts.build_l2_outcomes_london --span fit [--procs 3]
    python -m scripts.build_l2_outcomes_london --span holdout
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

import scripts.build_l0_triggers_london as L0M  # noqa: E402
from scripts.build_l0_triggers_london import window_et  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
LOOKBACK_DAYS = 7
MASTER = "data/reference/nq_1m_master.parquet"

_BARS: pd.DataFrame | None = None       # per-process cache (fork inherits the parent's copy)
_MGMT = "V8"                            # module-level so Pool workers inherit it

# One normal-window day and one DST-shifted day, both with real fills at L1.
GATE_DAYS = ["2025-09-17", "2025-10-28"]


def l2_cfg(day: str, t_cancel: float = 100000.0):
    """Config for ONE day. win_start/win_end are wall-clock times and cannot express a window
    that shifts with DST, so the window is resolved per day rather than hardcoded."""
    start, end = window_et(day)
    return load_backtest_config().model_copy(update={
        "win_start": dtime(start.hour, start.minute),
        "win_end": dtime(end.hour, end.minute),
        "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None, "t_cancel": t_cancel,
        "mgmt_variant": _MGMT,
        "v8_be_at_open": False})        # ANGUS 29-Jul


def load_bars() -> pd.DataFrame:
    """Master alone — verified byte-identical to nq_1m_feb_jul2026 across all 161,525
    overlapping 2026 rows at L0, so the concat+dedup the NY loader does is a no-op here."""
    return (pd.read_parquet(ROOT / MASTER).drop(columns=["roll"], errors="ignore")
            .sort_values("ts_event").reset_index(drop=True))


def day_outcomes(args) -> list[dict]:
    """All of one day's triggers, one simulate() each. Module-level for Pool pickling."""
    day, recs, lookback = args
    global _BARS
    if _BARS is None:
        _BARS = load_bars()
    seg = _BARS[(_BARS.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                 - pd.Timedelta(days=lookback))
                & (_BARS.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))].reset_index(drop=True)
    cfg = l2_cfg(day)
    _, win_end = window_et(day)
    out = []
    for rec in recs:
        t = Trigger(**{k: v for k, v in rec.items() if k in Trigger.model_fields})
        trades, verdicts, _ = simulate(seg, [t], cfg)
        row = {"day": day, "ts": t.ts, "tf": t.tf, "direction": t.direction,
               "kind": t.kind, "pattern": t.pattern, "htf_flag": t.htf_flag,
               "confluence_count": t.confluence_count,
               "dst_shifted": win_end.hour == 6,
               "cluster_members": rec.get("cluster_members", ""),
               "level_stack": rec.get("level_stack", "")}
        if trades:
            r = trades[0]
            risk = round(abs(float(r.limit_price) - float(r.stop_initial)), 4)
            row |= {"status": "outcome", "fill_ts": str(r.fill_ts), "entry": float(r.entry),
                    "stop": float(r.stop_initial), "risk": risk,
                    "exit_ts": str(r.exit_ts), "exit_price": float(r.exit_price),
                    "exit_reason": str(r.exit_reason), "target": str(r.target_name),
                    "target_level": float(r.target_level),
                    "working_target": float(r.working_target),
                    "pts": float(r.points), "R": float(r.r_multiple),
                    "size_engine": float(r.size), "dollars_1lot": float(r.dollars),
                    "fill_hm": pd.Timestamp(r.fill_ts).hour * 60
                    + pd.Timestamp(r.fill_ts).minute}
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
    """GATE — outcome invariance of lookback `lb` vs 30 days, on days with real fills.

    Any difference in fill/exit/dollars fails: a lookback that changes outcomes corrupts every
    number downstream of L2. The gate days are L0-parity-verified and include a DST-shifted
    day, so the per-day window config is exercised too.
    """
    census = ROOT / "output/l0_triggers_london_fit.parquet"
    if not census.exists():
        raise SystemExit(f"{census.relative_to(ROOT)} missing — build the L0 census first")
    T = pd.read_parquet(census)
    tday = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = T[tday.dt.strftime("%Y-%m-%d").isin(GATE_DAYS)].reset_index(drop=True)
    print(f"gate days {GATE_DAYS}: {len(trigs)} candidates "
          f"(DST-shifted: {[d for d in GATE_DAYS if window_et(d)[0].hour != 3]})\n")

    a = run(trigs, procs=2, lookback=lb)
    b = run(trigs, procs=2, lookback=30)
    cols = ["ts", "status", "fill_ts", "exit_ts"]
    fa, fb = a[a.status == "outcome"], b[b.status == "outcome"]
    same = (a[cols].reset_index(drop=True).equals(b[cols].reset_index(drop=True))
            and len(fa) == len(fb)
            and (fa.dollars_1lot.to_numpy() == fb.dollars_1lot.to_numpy()).all())
    print(f"\ncandidates {len(a)} | outcomes {len(fa)} vs {len(fb)} (30d) | "
          f"1-lot ${fa.dollars_1lot.sum():+,.0f} vs ${fb.dollars_1lot.sum():+,.0f}")
    if not same:
        if len(a) == len(b):
            print(a[cols].compare(b[cols]))
        raise SystemExit(f"GATE FAILED — {lb}d lookback is not outcome-invariant for London")
    if len(fa) == 0:
        raise SystemExit("GATE INCONCLUSIVE — no filled outcomes on the sample days")
    print(f"gate OK — {lb}d lookback outcome-identical to 30d on {len(fa)} real London outcomes")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout", "forward"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--lb", type=int, default=LOOKBACK_DAYS)
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--mgmt", default="V8")
    ap.add_argument("--win", default="08:00-10:00",
                    help="London-local window HH:MM-HH:MM. Must match the census being read.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    L0M.WINDOW = tuple(a.win.split("-"))          # set before any Pool fork
    tag = "" if L0M.WINDOW == ("08:00", "10:00") else "_" + a.win.replace(":", "")
    if a.gate:
        return gate(a.lb)
    if not a.span:
        raise SystemExit("--span or --gate required")
    global _MGMT
    _MGMT = a.mgmt

    trigs = pd.read_parquet(ROOT / f"output/l0_triggers_london{tag}_{a.span}.parquet")
    F = run(trigs, procs=a.procs, lookback=a.lb)
    suffix = "" if a.mgmt == "V8" else f"_{a.mgmt.lower()}"
    out = Path(a.out) if a.out else \
        ROOT / f"output/l2_outcomes_london{tag}_{a.span}{suffix}.parquet"
    F.to_parquet(out, index=False)

    oc = F[F.status == "outcome"]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} candidates, {len(oc)} outcomes")
    print(f"status: {F.status.value_counts().to_dict()}")
    if not len(oc):
        return
    print(f"1-lot: ${oc.dollars_1lot.sum():+,.0f} | WR {(oc.dollars_1lot > 0).mean() * 100:.0f}%"
          f" | mean R {oc.R.mean():+.3f} | median risk {oc.risk.median():.1f}pt")
    print(f"exit_reason: {oc.exit_reason.value_counts().to_dict()}")

    # THE LON_RISK_MIN TEST (handoff §2: "TEST the London gate on the honest population the way
    # we tested NY's (L2 by risk band) before trusting it"). This is that table.
    bands = [(0, 4), (4, 7), (7, 9.5), (9.5, 15), (15, 25), (25, 1e9)]
    print("\nby risk band — the LON_RISK_MIN = 9.5pt test on the honest population:")
    print(f"  {'band':>12} {'n':>6} {'WR':>6} {'meanR':>8} {'$1lot':>12}")
    for lo, hi in bands:
        s = oc[(oc.risk >= lo) & (oc.risk < hi)]
        if not len(s):
            continue
        lab = f"{lo:g}-{hi:g}pt" if hi < 1e9 else f">{lo:g}pt"
        mark = "  <- gate cuts" if hi <= 9.5 else ""
        print(f"  {lab:>12} {len(s):>6} {(s.dollars_1lot > 0).mean() * 100:>5.0f}% "
              f"{s.R.mean():>+8.3f} {s.dollars_1lot.sum():>+12,.0f}{mark}")
    below = oc[oc.risk < 9.5]
    above = oc[oc.risk >= 9.5]
    print(f"  BELOW 9.5: n={len(below)} WR {(below.dollars_1lot > 0).mean() * 100:.0f}% "
          f"meanR {below.R.mean():+.3f} ${below.dollars_1lot.sum():+,.0f}")
    print(f"  AT/ABOVE : n={len(above)} WR {(above.dollars_1lot > 0).mean() * 100:.0f}% "
          f"meanR {above.R.mean():+.3f} ${above.dollars_1lot.sum():+,.0f}")


if __name__ == "__main__":
    main()
