#!/usr/bin/env python3
"""DOES THE LONDON 10-13 BOOK COLLIDE WITH THE CANON?

Canon trades two windows, both New-York anchored:
  pre    08:00-09:30 ET
  golden 09:30+      ET
The London book is Europe/London anchored, 10:00-13:00 UK.

Normally the offset is 5h (UK BST + US EDT, or UK GMT + US EST), so 08:00 ET == 13:00 UK
and the two books are exactly adjacent -- London stops at the minute canon starts.

BUT the UK and US switch DST on DIFFERENT dates:
  UK  BST->GMT last Sunday of October ; GMT->BST last Sunday of March
  US  EDT->EST first Sunday of November ; EST->EDT second Sunday of March
For the weeks in between, the offset is 4h and canon's pre-market opens at 12:00 UK --
INSIDE the London window. This script finds those days exactly and prices the collision
against the actual trade book.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_canon_overlap.py
"""
import os
from datetime import time as dtime

import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")

LON_START, LON_END = dtime(10, 0), dtime(13, 0)
CANON_PRE_ET = dtime(8, 0)

days = pd.date_range("2025-07-01", "2026-07-15", freq="D")
rows = []
for d in days:
    if d.dayofweek >= 5:
        continue
    # 08:00 ET on this date, expressed in London wall clock
    et = pd.Timestamp(d.date()).tz_localize("America/New_York") + pd.Timedelta(hours=8)
    uk = et.tz_convert("Europe/London")
    rows.append(dict(day=d.strftime("%Y-%m-%d"), canon_pre_uk=uk.time(),
                     offset_h=int((uk.utcoffset() - et.utcoffset()).total_seconds() // 3600)))
O = pd.DataFrame(rows)
O["collides"] = O.canon_pre_uk < LON_END

if __name__ == "__main__":
    print(f"weekdays examined: {len(O)}")
    print(f"\noffset distribution (UK hours ahead of New York):")
    print(O.offset_h.value_counts().to_string())
    print(f"\ncanon pre-market start in UK time:")
    print(O.canon_pre_uk.astype(str).value_counts().to_string())

    C = O[O.collides]
    print(f"\n=== COLLISION DAYS: {len(C)} of {len(O)} ({len(C)/len(O)*100:.1f}%) ===")
    if len(C):
        # contiguous runs
        C = C.reset_index(drop=True)
        runs, cur = [], [C.day.iloc[0]]
        for a, b in zip(C.day[:-1], C.day[1:]):
            if (pd.Timestamp(b) - pd.Timestamp(a)).days <= 3:
                cur.append(b)
            else:
                runs.append(cur); cur = [b]
        runs.append(cur)
        for r in runs:
            print(f"  {r[0]} -> {r[-1]}  ({len(r)} weekdays)  canon pre-market opens "
                  f"{C[C.day==r[0]].canon_pre_uk.iloc[0]} UK")
        print(f"\n  On these days canon's pre-market window (opens 12:00 UK) overlaps the LAST HOUR"
              f"\n  of the London window (12:00-13:00 UK). On every other day the two are adjacent"
              f"\n  and never overlap.")

    # price it against the real book
    bk = f"{S}/london_book_C.csv"
    if os.path.exists(bk):
        D = pd.read_csv(bk)
        D["collides"] = D.day.isin(set(C.day))
        D["late"] = D.ent >= "12:00:00"
        print(f"\n=== AGAINST THE ACTUAL BOOK (leakage-clean, {len(D)} trades) ===")
        hit = D[D.collides & D.late]
        print(f"  trades on a collision day        : {int(D.collides.sum())}")
        print(f"  ...AND entered at/after 12:00 UK : {len(hit)}   <- the only genuinely conflicted ones")
        if len(hit):
            print(hit[["day", "ent", "R"]].to_string(index=False))
        print(f"  trades still OPEN at 12:00 UK on a collision day: "
              f"{int((D.collides & (D.ent < '12:00:00')).sum())} entered earlier "
              f"(some will still be running)")
    else:
        print(f"\n(book not found at {bk} -- run london_conviction_c.py first to price the overlap)")
