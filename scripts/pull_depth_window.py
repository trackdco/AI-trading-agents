#!/usr/bin/env python3
"""Pull WINDOWED mbp-10 depth (heatmap) from Databento — cost-checked, per-day intraday slices.

Why windowed: raw full-session NQ mbp-10 is ~144 GB/month and Databento bills for what you REQUEST.
Slicing to the 07:55-10:20 ET entry window per day is ~10x smaller/cheaper and still covers every
champion entry (08:01-10:12) + a 5-min approach. This is what turns the magnet/absorption test from
n=5 (April only) into a real Feb-Jul sample.

SAFETY: dry-run by default — it only cost-checks (free) and prints the estimate. It downloads NOTHING
until you pass --confirm, and aborts if the estimate exceeds --max-cost. Needs DATABENTO_API_KEY
(Angus/Brake account) and Angus's cost sign-off (data-lane buy).

  pip install databento pandas
  python scripts/pull_depth_window.py                        # cost-check only (dry run)
  python scripts/pull_depth_window.py --confirm --max-cost 30   # actually download

Output: raw per-day <outdir>/nq_mbp10_YYYY-MM-DD.dbn.zst (DO NOT COMMIT — gitignored).
Then condense to the committable format (script lives on claude/getting-started-6lwnvs):
  python scripts/condense_depth.py <outdir>/*.dbn.zst --outdir data/reference/depth_out

NOTE (OOS guard): Jun/Jul 2026 are the reserved out-of-sample block. Pull them if you want, but do
NOT fit/tune the magnet on them — hold them out for final validation, or the OOS check is worthless.
"""
import argparse, os, sys
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import pandas as pd

NY, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")
DATASET, SCHEMA = "GLBX.MDP3", "mbp-10"
SYMBOLS, STYPE = ["NQ.v.0"], "continuous"   # continuous front-month by volume = single instrument = smallest pull


def hhmm(x):
    h, m = x.split(":"); return dtime(int(h), int(m))


def window_utc(day, ws, we):
    # tz-aware -> DST handled by zoneinfo (Feb/early-Mar EST -05:00, after 2026-03-08 EDT -04:00)
    s = datetime.combine(day, ws, tzinfo=NY).astimezone(UTC)
    e = datetime.combine(day, we, tzinfo=NY).astimezone(UTC)
    return s, e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-02-01")
    ap.add_argument("--end", default="2026-07-31")
    ap.add_argument("--win-start", default="07:55")
    ap.add_argument("--win-end", default="10:20")
    ap.add_argument("--outdir", default="data/raw/depth")
    ap.add_argument("--max-cost", type=float, default=30.0, help="USD ceiling; abort if estimate exceeds")
    ap.add_argument("--confirm", action="store_true", help="actually download (default: cost-check only)")
    a = ap.parse_args()

    try:
        import databento as db
    except ImportError:
        sys.exit("pip install databento")
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        sys.exit("set DATABENTO_API_KEY (Angus/Brake account) — not present in this environment")
    client = db.Historical(key)

    ws, we = hhmm(a.win_start), hhmm(a.win_end)
    days = pd.bdate_range(a.start, a.end)   # business days; holidays return 0 records (0 cost)
    os.makedirs(a.outdir, exist_ok=True)

    print(f"cost-checking {len(days)} sessions | {DATASET} {SCHEMA} {SYMBOLS} "
          f"{a.win_start}-{a.win_end} ET | {a.start}..{a.end}")
    total_cost, total_rec, plan = 0.0, 0, []
    for d in days:
        s, e = window_utc(d.date(), ws, we)
        try:
            c = client.metadata.get_cost(dataset=DATASET, symbols=SYMBOLS, schema=SCHEMA,
                                         start=s, end=e, stype_in=STYPE)
            n = client.metadata.get_record_count(dataset=DATASET, symbols=SYMBOLS, schema=SCHEMA,
                                                 start=s, end=e, stype_in=STYPE)
        except Exception as ex:
            print(f"  {d.date()}  cost-check failed: {ex}"); continue
        total_cost += float(c); total_rec += int(n)
        plan.append((str(d.date()), s, e, int(n)))

    print(f"\nESTIMATE: ${total_cost:,.2f} | {total_rec:,} records | {len(plan)} sessions")
    print("OOS guard: Jun/Jul are the reserved out-of-sample block — do NOT tune the magnet on them.")
    if not a.confirm:
        print("\nDRY-RUN (cost-check only, no download). Re-run with --confirm to pull.")
        return
    if total_cost > a.max_cost:
        sys.exit(f"\nABORT: estimate ${total_cost:,.2f} exceeds --max-cost ${a.max_cost:,.2f}. "
                 f"Raise the ceiling only with Angus's sign-off.")

    print(f"\nDownloading -> {a.outdir}")
    for d, s, e, n in plan:
        if n == 0:
            continue
        out = os.path.join(a.outdir, f"nq_mbp10_{d}.dbn.zst")
        if os.path.exists(out):
            print(f"  {d}  exists, skip"); continue
        client.timeseries.get_range(dataset=DATASET, symbols=SYMBOLS, schema=SCHEMA,
                                    start=s, end=e, stype_in=STYPE).to_file(out)
        print(f"  {d}  {n:,} rec -> {out}")
    print(f"\nDone. Raw in {a.outdir} (DO NOT COMMIT). Next, on getting-started-6lwnvs:")
    print(f"  python scripts/condense_depth.py {a.outdir}/*.dbn.zst --outdir data/reference/depth_out")


if __name__ == "__main__":
    main()
