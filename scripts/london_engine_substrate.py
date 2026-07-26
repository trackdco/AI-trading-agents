#!/usr/bin/env python3
"""LONDON 10:00-13:00 UK SUBSTRATE via the full trigger engine — the way Angus built 08:00-10:00.

Everything before this ran ONE hand-coded pattern (MA-stack + 50-MA wick + fading volume) and
got 70 fills over the in-sample year. That is far too few to mine an Angus-style check ladder --
his London 08:00-10:00 canon was mined on ~750 fills. This rebuilds the substrate his way:

  detect_triggers  over the 10:00-13:00 UK window (rejection blocks + displacements against the
                   confluence clusters: BB MA, daily-VWAP dev bands, POC), A/B/B2 classified,
                   MTF-arbitrated -- i.e. the whole mechanical universe, not one setup
  simulate         each classified trigger under BOTH management books, no book choosing:
                     E3 = V8 rotation/trail management
                     E4 = momentum entry
  no pre-filtering: every classified trigger is taken under both books

WINDOW is Europe/London 10:00-13:00, converted to ET per day, so the ~5 weeks/year of UK/US DST
misalignment shift correctly (10:00 UK is normally 05:00 ET; 04:00 ET when clocks disagree).

FULL SPAN 2023-01 -> 2026-07. The engine needs only bars, which exist back to 2023, so the
substrate spans the whole history. Rows are tagged:
    oos   = 1 for 2023-01..2025-06 (holdout), 0 for 2025-07..2026-07 (the tuned window)
    cvd   = 1 for fills on/after 2025-06-02 (order-flow data exists), 0 before
Geometry/price checks can be mined and validated across the whole span; order-flow checks are
limited to cvd==1, exactly as before.

TWO DELIBERATE ENGINE SETTINGS, both documented rather than silent:
  * calendar = EMPTY.  The engine's NY pre-market news rule blocks all trades before 09:30 ET on
    any US-high-impact day. Our window is 05:00-08:00 ET, so that rule vetoes the ENTIRE London
    window on every release day (verified: 41/41 triggers vetoed on 2026-06-05 / NFP). The
    08:30 ET release is 13:30 UK -- AFTER our window closes -- so the rule is a NY artefact
    misapplied to a London book. Disabling it honours "no pre-filtering". News-as-a-check was
    separately tested earlier and was noise.
  * max_trades_per_day = 2, matching Angus's london_substrate.py (his was 2, engine default 3).

PER-DAY SLICE for speed: detect_triggers resamples and indicator-scans its whole input, so
passing the full 1.25M-bar frame per day is O(days x history). Each day is sliced to
[window_start - 1.5d, window_end + 9h]: 1.5 days of lookback warms the daily-VWAP (18:00 ET
anchor), POC and BB-MA indicators; +9h forward carries every trade to its exit (engine flattens
at 15:55 ET = 20:55 UK at the latest). Verified to give identical triggers to the full-frame call.

    LONDON_WT=<worktree> LONDON_SCRATCH=<dir> python3 scripts/london_engine_substrate.py \
        [--start 2023-01-02 --end 2026-07-15] [--workers N]

Output: $LONDON_SCRATCH/london_engine_substrate.parquet  (one row per fill)
"""
import os
import sys
import time
from datetime import time as dtime
from multiprocessing import Pool
from zoneinfo import ZoneInfo

import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
sys.path.insert(0, WT)

# the engine loads config/*.yaml relative to CWD, so run from the worktree root
os.chdir(WT)

NY = ZoneInfo("America/New_York")
LON = ZoneInfo("Europe/London")
IS_START = "2025-07-01"      # in-sample window start (book was tuned on 2025-07 onward)
CVD_START = "2025-06-02"     # order-flow data availability

START = "2023-01-02"
END = "2026-07-15"
WORKERS = 4
if "--start" in sys.argv:
    START = sys.argv[sys.argv.index("--start") + 1]
if "--end" in sys.argv:
    END = sys.argv[sys.argv.index("--end") + 1]
if "--workers" in sys.argv:
    WORKERS = int(sys.argv[sys.argv.index("--workers") + 1])

# ---- load engine + bars once in the parent; workers inherit via fork -------------------------
from src.engine.triggers import detect_triggers                       # noqa: E402
from src.backtest.engine import load_backtest_config, simulate        # noqa: E402

print("load bars ...", flush=True)
DF = (pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
      .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
EMPTY_CAL = pd.DataFrame(columns=["datetime_ET", "event", "impact"])
BASE = load_backtest_config().model_copy(update={"max_trades_per_day": 2})
BOOKS = (("E3", {"mgmt_variant": "V8"}), ("E4", {"entry_variant": "E4"}))


def win_et(day: str):
    return (pd.Timestamp(f"{day} 10:00", tz=LON).tz_convert(NY),
            pd.Timestamp(f"{day} 13:00", tz=LON).tz_convert(NY))


def one_day(day: str):
    """All fills for one UK date, both books. Returns list[dict] (empty on no-trade / error)."""
    try:
        s, e = win_et(day)
        sl = DF[(DF.ts_event >= s - pd.Timedelta(days=1, hours=12))
                & (DF.ts_event <= e + pd.Timedelta(hours=9))].reset_index(drop=True)
        if len(sl) < 200:
            return []
        trigs = [t for t in detect_triggers(sl, start=s, end=e) if t.pattern != "unclassified"]
        if not trigs:
            return []
        cfg0 = BASE.model_copy(update={"win_start": s.time(), "win_end": e.time()})
        out = []
        for bk, upd in BOOKS:
            tr, _, _ = simulate(sl, list(trigs), cfg0.model_copy(update=upd), calendar=EMPTY_CAL)
            for r in tr:
                out.append(dict(
                    day=r.trade_date, book=bk, fill=str(r.fill_ts), exit=str(r.exit_ts),
                    direction=r.direction, entry=float(r.entry), stop=float(r.stop_initial),
                    exit_price=float(r.exit_price), exit_reason=r.exit_reason,
                    dollars=float(r.dollars), pattern=r.pattern, tf=getattr(r, "tf", ""),
                    n_trig=len(trigs)))
        return out
    except Exception as ex:                       # one bad day must not kill the run
        return [dict(day=day, book="ERR", fill="", exit="", direction="", entry=0.0, stop=0.0,
                     exit_price=0.0, exit_reason=f"ERR:{type(ex).__name__}:{ex}"[:120],
                     dollars=0.0, pattern="", tf="", n_trig=-1)]


def main():
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(START, END)]
    print(f"window 10:00-13:00 UK | span {START} -> {END} | {len(days)} weekdays | "
          f"{WORKERS} workers", flush=True)
    t0 = time.time()
    rows, done = [], 0
    with Pool(WORKERS) as pool:
        for res in pool.imap_unordered(one_day, days, chunksize=1):
            rows.extend(res)
            done += 1
            if done % 40 == 0:
                el = time.time() - t0
                print(f"  {done}/{len(days)} days  {el/60:.1f}m  "
                      f"eta {el/done*(len(days)-done)/60:.0f}m  fills {len([r for r in rows if r['book']!='ERR'])}",
                      flush=True)

    A = pd.DataFrame(rows)
    errs = A[A.book == "ERR"]
    if len(errs):
        print(f"\n{len(errs)} day-level errors, e.g.: {errs.exit_reason.iloc[0]}")
    A = A[A.book != "ERR"].reset_index(drop=True)
    A["yr"] = A.day.str[:4].astype(int)
    A["risk"] = (A.entry - A.stop).abs()
    A["oos"] = (A.day < IS_START).astype(int)
    A["cvd"] = (A.day >= CVD_START).astype(int)
    A = A.sort_values("fill").reset_index(drop=True)
    A.to_parquet(f"{S}/london_engine_substrate.parquet")

    w = A.dollars > 0
    print(f"\n{'='*70}\nSUBSTRATE: {len(A)} fills over {A.day.nunique()} days "
          f"({time.time()-t0:.0f}s)\n{'='*70}")
    print(f"  overall  WR {w.mean()*100:.0f}%  raw ${A.dollars.sum():+,.0f}  "
          f"per book {dict(A.book.value_counts())}")
    print(f"  in-sample (2025-07+): {int((A.oos==0).sum())} fills  "
          f"holdout (pre): {int((A.oos==1).sum())}  cvd-covered: {int((A.cvd==1).sum())}")
    print(f"\n  {'year':>6} {'fills':>6} {'WR':>5} {'raw$':>12}")
    for yr in sorted(A.yr.unique()):
        d = A[A.yr == yr]
        print(f"  {yr:>6} {len(d):>6} {(d.dollars>0).mean()*100:>4.0f}% {d.dollars.sum():>+12,.0f}")
    print(f"\n  patterns {dict(A.pattern.value_counts())}")
    print(f"  exits    {dict(A.exit_reason.value_counts())}")
    print(f"\nwrote {S}/london_engine_substrate.parquet")


if __name__ == "__main__":
    main()
