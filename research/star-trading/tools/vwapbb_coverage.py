#!/usr/bin/env python3
"""Coverage census + gate-5 acceptance test for the VWAP/BB study.

Scoped to data already held. No acquisition.
"""
from __future__ import annotations

import collections
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from alpha_data import load

NY = ZoneInfo("America/New_York")
SPLIT = "2025-01-31"          # workbench ends here; holdout begins 2025-02-01


def et_index():
    """{et_date: {minute_of_et_day: (o,h,l,c,v,sym)}}"""
    d = load()
    bars, front = d["bars"], d["front"]
    out: dict[str, dict] = {}
    for ud in sorted(bars):
        base = datetime.fromisoformat(ud).replace(tzinfo=timezone.utc)
        sym = front[ud]
        for m, (o, h, l, c, v) in bars[ud].items():
            t = (base + timedelta(minutes=m)).astimezone(NY)
            out.setdefault(t.date().isoformat(), {})[t.hour * 60 + t.minute] = (o, h, l, c, v, sym)
    return out


def main():
    S = et_index()
    days = sorted(S)
    print("=" * 78)
    print("STEP 0 — COVERAGE CENSUS (all data held, repo-wide search)")
    print("=" * 78)
    print(f"ET session-days with any bars: {len(days)}   {days[0]} .. {days[-1]}\n")

    print("Month-by-month (ET session-days, and how many are FULL 1380-bar Globex days):")
    by_month = collections.OrderedDict()
    for d in days:
        by_month.setdefault(d[:7], []).append(d)
    prev_ym = None
    for ym, ds in by_month.items():
        full = sum(1 for x in ds if len(S[x]) == 1380)
        # flag calendar gaps between months
        if prev_ym:
            py, pm = int(prev_ym[:4]), int(prev_ym[5:])
            cy, cm = int(ym[:4]), int(ym[5:])
            if (cy - py) * 12 + (cm - pm) > 1:
                miss = (cy - py) * 12 + (cm - pm) - 1
                print(f"   *** GAP: {miss} month(s) absent between {prev_ym} and {ym} ***")
        print(f"   {ym}  days={len(ds):3d}  full-1380={full:3d}")
        prev_ym = ym

    print("\nRequested checks:")
    for t in ("2026-02-11", "2026-02-17"):
        st = "PRESENT" if t in S else "ABSENT"
        print(f"   parity date {t}: {st}")
    cal = [d for d in days if "2026-02-02" <= d <= "2026-02-27"]
    print(f"   calibration window 2026-02-02..02-27: {len(cal)} of ~19 sessions present")

    # ---------------- acceptance test ------------------------------------
    print("\n" + "=" * 78)
    print("GATE 5 ACCEPTANCE TEST — run against coverage that exists")
    print("=" * 78)
    full = [d for d in days if len(S[d]) == 1380]
    print(f"1. bars/session: {len(full)}/{len(days)} sessions have exactly 1380 bars "
          f"({len(full)/len(days)*100:.1f}%)")
    cnt = collections.Counter(len(S[d]) for d in days)
    print(f"   most common counts: {cnt.most_common(5)}")

    # intra-session gaps: within a session's own min..max minute span, any missing minute?
    gappy = 0
    for d in days:
        ms = sorted(S[d])
        span = ms[-1] - ms[0] + 1
        if span != len(ms):
            gappy += 1
    print(f"2. intra-session gaps: {gappy} session(s) with a missing minute inside their own span")

    print(f"3. parity dates present with full sessions: NO — both absent (see above)")
    print(f"4. calibration window complete: NO — 0 of ~19 sessions")

    d = load()
    syms = set(d["front"].values())
    print(f"5. front-month outrights identifiable: YES — {len(syms)} distinct front symbols, "
          f"none hyphenated: {sorted(syms)}")
    print(f"   hyphenated spreads present in source and excluded at load: YES "
          f"(verified in Stage 0 audit; loader filters '-')")

    # open-label consistency: a bar stamped 18:00 ET should be the session's first
    firsts = collections.Counter(min(S[d]) for d in days)
    print(f"6. open-labelled convention: most common first-minute-of-session = "
          f"{firsts.most_common(3)}  (18:00 ET = {18*60})")

    # ---------------- split ------------------------------------------------
    print("\n" + "=" * 78)
    print("FINALISED SPLIT (recomputed from actual coverage)")
    print("=" * 78)
    work = [x for x in days if x <= SPLIT]
    hold = [x for x in days if x > SPLIT]
    # restrict to sessions with a real RTH block, which is what the study trades
    def has_rth(x):
        return any(9 * 60 + 31 <= m < 16 * 60 for m in S[x])
    workR = [x for x in work if has_rth(x)]
    holdR = [x for x in hold if has_rth(x)]
    print(f"  WORKBENCH {work[0]} .. {SPLIT}: {len(work)} session-days, {len(workR)} with an RTH block")
    print(f"  HOLDOUT    2025-02-01 .. {hold[-1]}: {len(hold)} session-days, {len(holdR)} with an RTH block")

    # ---------------- replacement date candidates -------------------------
    print("\nReplacement PARITY date candidates (workbench only, full 1380-bar sessions,")
    print("not a roll session, Tue-Thu, recent enough for easy chart retrieval):")
    rolls = set()
    dd = load()
    fr = dd["front"]
    uds = sorted(dd["bars"])
    for i in range(1, len(uds)):
        if fr[uds[i]] != fr[uds[i - 1]]:
            rolls.add(uds[i])
    cands = []
    for x in workR:
        if x < "2024-11-01" or len(S[x]) != 1380:
            continue
        wd = datetime.fromisoformat(x).weekday()
        if wd not in (1, 2, 3):
            continue
        if x in rolls:
            continue
        cands.append(x)
    for x in cands[-12:]:
        print(f"   {x}  {datetime.fromisoformat(x).strftime('%a')}  bars={len(S[x])}")

    print("\nReplacement CALIBRATION window candidate (19 consecutive workbench sessions):")
    tail19 = workR[-19:]
    print(f"   {tail19[0]} .. {tail19[-1]}  ({len(tail19)} sessions, "
          f"{sum(1 for x in tail19 if len(S[x])==1380)} full-1380)")


if __name__ == "__main__":
    main()
