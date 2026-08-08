#!/usr/bin/env python3
"""Census of the MBP-10 condensed files in the repo root. Establish exactly what
they cover before any claim rests on them."""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import csv
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOLDOUT_START, HOLDOUT_END = "2025-02-01", "2026-01-30"


def et_offset(dt):
    """US Eastern offset. DST: second Sunday of March .. first Sunday of November."""
    y = dt.year
    m = datetime(y, 3, 8, tzinfo=timezone.utc)
    while m.weekday() != 6:
        m += timedelta(days=1)
    dst_start = m.replace(hour=7)                       # 02:00 ET = 07:00 UTC
    n = datetime(y, 11, 1, tzinfo=timezone.utc)
    while n.weekday() != 6:
        n += timedelta(days=1)
    dst_end = n.replace(hour=6)
    return -4 if dst_start <= dt < dst_end else -5


def to_et(ts):
    return ts + timedelta(hours=et_offset(ts))


def parse_ts(s):
    return datetime.fromisoformat(s.replace(" ", "T"))


def main():
    files = sorted(p for p in ROOT.glob("*.csv") if "mbp" in p.name.lower()
                   or p.name.startswith("condensed_GLBX-"))
    print(f"files matched: {len(files)}\n")

    recs = []
    for p in files:
        with p.open(newline="") as fh:
            rd = csv.reader(fh)
            hdr = next(rd)
            first = next(rd, None)
            if first is None:
                recs.append({"f": p.name, "n": 0})
                continue
            n = 1
            last = first
            for row in rd:
                last = row
                n += 1
        ci = {k: i for i, k in enumerate(hdr)}
        t0, t1 = parse_ts(first[ci["ts_event"]]), parse_ts(last[ci["ts_event"]])
        et0, et1 = to_et(t0), to_et(t1)
        # HOLDOUT GUARD. Timestamps and symbology are metadata and are kept for the
        # inventory; PRICE fields are book content and are dropped for any session
        # inside the sealed range. An earlier version of this script read them —
        # see target-stop-reconciliation.md section 7.
        sealed = HOLDOUT_START <= et0.strftime("%Y-%m-%d") <= HOLDOUT_END
        px = None if sealed else float(first[ci["price"]])
        recs.append({
            "f": p.name, "n": n, "t0": t0, "t1": t1, "et0": et0, "et1": et1,
            "sym": first[ci["symbol"]], "iid": first[ci["instrument_id"]],
            "sealed": sealed,
            # price scale is a property of the file family (a naming convention),
            # so it is readable from the filename without touching book content
            "scaled": p.name.startswith("condensed_"),
            "px": None if px is None else (px / 1e9 if px > 1e6 else px),
        })
    print(f"holdout-dated files (book content NOT read): "
          f"{sum(1 for r in recs if r.get('sealed'))}\n")

    ok = [r for r in recs if r.get("n")]
    print("=" * 100)
    print("FAMILIES")
    print("=" * 100)
    fam = collections.defaultdict(list)
    for r in ok:
        if r["f"].startswith("condensed_GLBX-"):
            fam["condensed_GLBX-<hash>"].append(r)
        elif r["f"].startswith("condensed_glbx-mdp3-"):
            fam["condensed_glbx-mdp3-<date>"].append(r)
        else:
            fam["glbx-mdp3-<date>_condensed"].append(r)
    for k, g in sorted(fam.items()):
        et_windows = collections.Counter(
            f'{r["et0"]:%H:%M}-{r["et1"]:%H:%M}' for r in g)
        print(f"\n{k}: {len(g)} files")
        print(f"   date span (ET) : {min(r['et0'] for r in g):%Y-%m-%d} .. "
              f"{max(r['et1'] for r in g):%Y-%m-%d}")
        print(f"   rows/file      : min {min(r['n'] for r in g)}  "
              f"median {sorted(r['n'] for r in g)[len(g)//2]}  max {max(r['n'] for r in g)}")
        print(f"   symbols        : {dict(collections.Counter(r['sym'] for r in g))}")
        print(f"   price scaled   : {dict(collections.Counter(r['scaled'] for r in g))}")
        print(f"   ET windows     : {dict(et_windows.most_common(6))}")

    print("\n" + "=" * 100)
    print("RTH COVERAGE — does any file reach the strategy window 09:31-16:00 ET?")
    print("=" * 100)
    rth = [r for r in ok if r["et1"].hour * 60 + r["et1"].minute > 9 * 60 + 31]
    print(f"files whose LAST snapshot is after 09:31 ET : {len(rth)} of {len(ok)}")
    past_936 = [r for r in ok if r["et1"].hour * 60 + r["et1"].minute >= 9 * 60 + 36]
    print(f"files reaching 09:36 ET (first signal bar)  : {len(past_936)}")
    past_10 = [r for r in ok if r["et1"].hour * 60 + r["et1"].minute >= 10 * 60]
    print(f"files reaching 10:00 ET                     : {len(past_10)}")
    past_16 = [r for r in ok if r["et1"].hour * 60 + r["et1"].minute >= 16 * 60]
    print(f"files reaching 16:00 ET (session close)     : {len(past_16)}")

    print("\n" + "=" * 100)
    print("FEBRUARY 2026 — the hand-log month")
    print("=" * 100)
    feb = sorted((r for r in ok if r["et0"].year == 2026 and r["et0"].month == 2),
                 key=lambda r: r["et0"])
    print(f"{len(feb)} files\n")
    print(f"{'file':>46} {'rows':>5} {'ET window':>14} {'symbol':>8} {'min/row':>8}")
    for r in feb:
        span = (r["t1"] - r["t0"]).total_seconds() / 60
        print(f"{r['f']:>46} {r['n']:>5} "
              f"{r['et0']:%H:%M}-{r['et1']:%H:%M}  {r['sym']:>8} "
              f"{span/max(1,r['n']-1):>8.2f}")

    # hand-log dates vs available files
    hl = ROOT / "data" / "reference" / "feb2026_hand_log.csv"
    import csv as _csv
    dates = set()
    for row in _csv.DictReader(hl.read_text().splitlines()):
        k = {kk.strip(): (vv or "").strip() for kk, vv in row.items() if kk}
        dates.add(datetime.strptime(k["Date"], "%B %d, %Y").date())
    have = {r["et0"].date() for r in ok}
    print(f"\nhand-log dates: {len(dates)}   with an mbp file: "
          f"{len(dates & have)}   missing: {sorted(d.isoformat() for d in dates - have)}")

    print("\n" + "=" * 100)
    print("ALL DATES COVERED, by month")
    print("=" * 100)
    bym = collections.Counter(f"{r['et0']:%Y-%m}" for r in ok)
    for k in sorted(bym):
        print(f"   {k}: {bym[k]:>3} files")


if __name__ == "__main__":
    main()
