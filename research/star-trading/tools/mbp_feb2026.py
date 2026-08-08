#!/usr/bin/env python3
"""What the MBP-10 condensed snapshots actually support, and the two things they
can measure that nothing else in this repo can:

  1. the realised top-of-book SPREAD  (the cost assumption is currently UNVERIFIED)
  2. a minute-resolution mid path over the hand-log month

HOLDOUT GUARD. The sealed holdout is 2025-02-01 .. 2026-01-30. Every MBP file
dated inside it is REFUSED here. Only 2026-02-01 onward is read — that range is
after the holdout ends and is not part of the workbench either; it is currently
UNCLASSIFIED in config/data_split.yaml and needs a ruling.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOLDOUT_START, HOLDOUT_END = "2025-02-01", "2026-01-30"
POST_HOLDOUT = "2026-02-01"


class HoldoutBreach(RuntimeError):
    pass


def et_offset(dt):
    y = dt.year
    m = datetime(y, 3, 8, tzinfo=timezone.utc)
    while m.weekday() != 6:
        m += timedelta(days=1)
    n = datetime(y, 11, 1, tzinfo=timezone.utc)
    while n.weekday() != 6:
        n += timedelta(days=1)
    return -4 if m.replace(hour=7) <= dt < n.replace(hour=6) else -5


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def read_file(p):
    """-> list of (et_minute_of_day, date, bid, ask, bidsz, asksz). Refuses holdout."""
    out = []
    with p.open(newline="") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
            ts = datetime.fromisoformat(row["ts_event"].replace(" ", "T"))
            et = ts + timedelta(hours=et_offset(ts))
            d = et.strftime("%Y-%m-%d")
            if HOLDOUT_START <= d <= HOLDOUT_END:
                raise HoldoutBreach(f"REFUSING {p.name}: session {d} is inside the "
                                    f"SEALED holdout {HOLDOUT_START}..{HOLDOUT_END}")
            b, a = float(row["bid_px_00"]), float(row["ask_px_00"])
            if b > 1e6:
                b, a = b / 1e9, a / 1e9
            out.append((et.hour * 60 + et.minute, d, b, a,
                        float(row["bid_sz_00"]), float(row["ask_sz_00"])))
    return out


def handlog():
    rows = []
    hl = ROOT / "data" / "reference" / "feb2026_hand_log.csv"
    for row in csv.DictReader(hl.read_text().splitlines()):
        k = {kk.strip(): (vv or "").strip() for kk, vv in row.items() if kk}
        t = k["Entry Time"]
        h, m = t.split(":")[:2]
        rows.append({
            "date": datetime.strptime(k["Date"], "%B %d, %Y").strftime("%Y-%m-%d"),
            "min": int(h) * 60 + int(m), "hhmm": f"{int(h):02d}:{int(m):02d}",
            "dir": k["Direction"].lower(), "tf": k["Entry TF"],
            "stop": float(k["Stop pts"]), "R": float(k["R Multiple"] or 0),
            "mfe": float(k["MFE (R)"] or 0), "res": k["Result"],
            "reason": k["Exit Reason"], "pattern": k["Pattern"],
        })
    return rows


def main():
    files = sorted(p for p in ROOT.glob("*.csv")
                   if "mbp" in p.name.lower() or p.name.startswith("condensed_GLBX-"))

    # classify by first timestamp WITHOUT reading book content
    usable, refused = [], 0
    for p in files:
        with p.open(newline="") as fh:
            fh.readline()
            ts = datetime.fromisoformat(fh.readline().split(",")[0].replace(" ", "T"))
        d = (ts + timedelta(hours=et_offset(ts))).strftime("%Y-%m-%d")
        if d < POST_HOLDOUT:
            refused += 1
        else:
            usable.append((d, p))
    print(f"MBP files total {len(files)}   REFUSED as holdout-dated {refused}   "
          f"readable (>= {POST_HOLDOUT}) {len(usable)}\n")

    # ---- only files whose window overlaps RTH are useful for the strategy ----
    by_date = collections.defaultdict(list)
    for d, p in usable:
        by_date[d].append(p)

    spread_pts, spread_by_bucket = [], collections.defaultdict(list)
    depth, mids = [], collections.defaultdict(dict)
    rth_days = set()
    for d, ps in sorted(by_date.items()):
        for p in ps:
            rows = read_file(p)
            if not rows:
                continue
            if max(r[0] for r in rows) < 9 * 60 + 31:
                continue                                    # overnight-only file
            rth_days.add(d)
            for mm, dd, b, a, bs, asz in rows:
                s = a - b
                if not (0 < s < 20):
                    continue
                mids[dd][mm] = (b + a) / 2
                if mm >= 9 * 60 + 31:
                    spread_pts.append(s)
                    spread_by_bucket[f"{mm//60:02d}:{(mm%60)//15*15:02d}"].append(s)
                    depth.append(bs + asz)
                else:
                    spread_by_bucket[f"pre {mm//60:02d}:{(mm%60)//15*15:02d}"].append(s)

    print("=" * 96)
    print("1. REALISED TOP-OF-BOOK SPREAD — first measurement of a cost input in this project")
    print("=" * 96)
    print(f"sessions with RTH-overlapping snapshots: {len(rth_days)}  "
          f"({min(rth_days)} .. {max(rth_days)})")
    print(f"RTH snapshots (>= 09:31 ET): {len(spread_pts)}\n")
    print(f"   spread, points: min {min(spread_pts):.2f}  p25 {pct(spread_pts,.25):.2f}  "
          f"median {pct(spread_pts,.5):.2f}  p75 {pct(spread_pts,.75):.2f}  "
          f"p95 {pct(spread_pts,.95):.2f}  max {max(spread_pts):.2f}")
    c = collections.Counter(round(s / 0.25) for s in spread_pts)
    tot = sum(c.values())
    print("   spread in ticks: " + "  ".join(
        f"{k}t: {c[k]/tot*100:.1f}%" for k in sorted(c) if c[k] / tot > 0.005))
    print(f"   top-of-book size (bid+ask): median {pct(depth,.5):.0f} contracts, "
          f"p10 {pct(depth,.10):.0f}, p90 {pct(depth,.90):.0f}")
    print("\n   by 15-min bucket (ET):")
    for k in sorted(spread_by_bucket):
        g = spread_by_bucket[k]
        if len(g) < 30:
            continue
        print(f"      {k}  n={len(g):>5}  median {pct(g,.5):.3f}  p90 {pct(g,.9):.3f}")

    print(f"\n   IMPLIED ROUND-TRIP COST FLOOR (cross the spread once on the stop exit):")
    print(f"      median spread {pct(spread_pts,.5):.2f} pt + commission 0.225 pt "
          f"= {pct(spread_pts,.5)+0.225:.3f} pt")
    print(f"      p90 spread    {pct(spread_pts,.9):.2f} pt + commission 0.225 pt "
          f"= {pct(spread_pts,.9)+0.225:.3f} pt")
    print("      Declared assumption in STATE.md: 0.25 lean / 0.50 base / 1.00 adverse.")

    # ---------------------------------------------------------------- hand log
    print("\n" + "=" * 96)
    print("2. HAND-LOG TRADES vs THE OBSERVED MARKET — what the window can and cannot reach")
    print("=" * 96)
    hl = handlog()
    ins = [h for h in hl if h["min"] >= 9 * 60 + 36]
    print(f"hand-log trades {len(hl)}, in scope (>=09:36) {len(ins)}")
    have = {d for d in mids}
    covered = [h for h in ins if h["date"] in have
               and h["min"] >= min(mids[h["date"]]) and h["min"] <= max(mids[h["date"]])]
    print(f"in-scope trades whose ENTRY MINUTE falls inside an available window: "
          f"{len(covered)} of {len(ins)}")
    lost_date = [h for h in ins if h["date"] not in have]
    lost_time = [h for h in ins if h["date"] in have and h not in covered]
    print(f"   lost — no RTH file for the date : {len(lost_date)} "
          f"({sorted({h['date'] for h in lost_date})})")
    print(f"   lost — entry after window close : {len(lost_time)} "
          f"({[h['date']+' '+h['hhmm'] for h in lost_time]})")

    print("\nEntry proxy = mid at the top of the entry minute. Snapshots are minute")
    print("boundaries, so intra-minute extremes are invisible: an OBSERVED touch is real,")
    print("an unobserved one is not evidence of absence. Excursions are lower bounds.\n")
    print(f"{'date':>12} {'entry':>6} {'dir':>6} {'log':>5} {'stop':>6} "
          f"{'claimed mv':>11} {'obs fav':>8} {'obs adv':>8} "
          f"{'1st stop':>9} {'1st tgt':>8} {'first touch':>13} {'verdict':>18}")
    tally = collections.Counter()
    for h in sorted(covered, key=lambda x: (x["date"], x["min"])):
        m = mids[h["date"]]
        e = m[h["min"]]
        ks = [k for k in sorted(m) if k >= h["min"]]
        claim = h["stop"] * abs(h["mfe"])
        fav = adv = 0.0
        t_stop = t_tgt = None
        for k in ks:
            d_ = (m[k] - e) if h["dir"] == "long" else (e - m[k])
            fav, adv = max(fav, d_), max(adv, -d_)
            if t_stop is None and -d_ >= h["stop"]:
                t_stop = k - h["min"]
            if t_tgt is None and d_ >= claim > 0:
                t_tgt = k - h["min"]
            if t_stop is not None or t_tgt is not None:
                break
        for k in ks:                                    # full-window excursions
            d_ = (m[k] - e) if h["dir"] == "long" else (e - m[k])
            fav, adv = max(fav, d_), max(adv, -d_)
        if t_stop is not None and (t_tgt is None or t_stop < t_tgt):
            first = "STOP"
        elif t_tgt is not None:
            first = "target"
        else:
            first = "neither"
        won = h["res"] == "win"
        if first == "STOP" and won:
            v = "TENSION"
        elif first == "target" and won:
            v = "consistent"
        elif first == "STOP" and not won:
            v = "consistent"
        elif max(m) < 16 * 60:
            v = "window truncates"
        else:
            v = "unresolved"
        tally[v] += 1
        print(f"{h['date']:>12} {h['hhmm']:>6} {h['dir']:>6} {h['res']:>5} "
              f"{h['stop']:>6.1f} {claim:>11.1f} {fav:>8.1f} {adv:>8.1f} "
              f"{str(t_stop)+'m' if t_stop is not None else '—':>9} "
              f"{str(t_tgt)+'m' if t_tgt is not None else '—':>8} "
              f"{first:>13} {v:>18}")
    print("\n   " + "   ".join(f"{k}: {v}" for k, v in tally.most_common()))

    print("\n" + "=" * 96)
    print("3. WHAT THE SNAPSHOTS CANNOT DO")
    print("=" * 96)
    print("""   One book snapshot per minute. Per snapshot: ts, top-10 book, and the price
   and size of the single event that produced it.

   NOT present, and not derivable:
     - intra-minute high / low  -> no OHLC bars, so no wick, no rejection block,
       no displacement test, no trigger candle, no wick-anchored stop
     - traded volume per minute -> no VWAP, no volume profile, no POC
     - anything after 10:29 ET  -> no session high/low, no EOD, no full excursion

   The detector needs VWAP, POC, BB and wick geometry. Three of those four are
   uncomputable from this file. The detector CANNOT be run on the hand-log month,
   so 'was there a candidate near the recorded trade' remains unanswerable.""")


if __name__ == "__main__":
    main()
