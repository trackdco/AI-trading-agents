"""AUTOPSY PART 4 — same-session trendiness, and whether the day tips its hand EARLY.

Part 3 said losing days are not preceded by anything. Part 3b hinted at what
they ARE: normal-to-narrow range, above-average one-way push, fewer signals.
This quantifies push properly, then asks the only question that could still
become a rule: does the FIRST PART of the session predict the rest? An early
gate is knowable in-flight, so unlike the pre-open features it could be acted
on - but it changes occupancy WITHIN the day, so a bucket here is NOT a rule
effect (the G3b lesson) and it would need its own engine run. Flagged, not
adopted.
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad")
import loser_autopsy as LA   # noqa: E402

def tab(era, path, key, desc, k=4):
    bars = LA.load_bars(path)
    days, R, kept, feat = LA.DATA[(era, False)]
    rows = []
    for d in days:
        t0 = pd.Timestamp(f"{d} 18:00", tz=LA.OB.NY)
        s = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if len(s) < 300 or not kept[d]:
            continue
        rng = float(s.high.max() - s.low.min())
        if not rng:
            continue
        e6 = s[s.index < t0 + pd.Timedelta(hours=6)]          # 18:00-24:00, Asia
        r6 = float(e6.high.max() - e6.low.min()) if len(e6) > 100 else np.nan
        v = dict(push=abs(float(s.close.iloc[-1]) - float(s.open.iloc[0])) / rng,
                 early_push=(abs(float(e6.close.iloc[-1]) - float(e6.open.iloc[0])) / r6
                             if r6 and np.isfinite(r6) and r6 > 0 else np.nan),
                 early_R=sum(LA.net(t) for t in kept[d] if t["fill_hrs"] < 6.0))[key]
        if np.isfinite(v):
            rows.append((v, R[d], kept[d]))
    xs = np.array([r[0] for r in rows])
    e = LA.buckets(xs, k)
    idx = np.clip(np.digitize(xs, e[1:-1]), 0, k - 1)
    print(f"\n{era} — {desc}")
    print(f"  {'bucket':<18}{'days':>7}{'day R':>9}{'trades/d':>10}{'EV/trade':>11}{'red days':>10}")
    for j in range(k):
        sel = [r for r, i in zip(rows, idx) if i == j]
        ts = [t for r in sel for t in r[2]]
        dr = np.array([r[1] for r in sel])
        print(f"  {e[j]:>7.2f}–{e[j+1]:<10.2f}{len(sel):>7}{dr.mean():>+9.1f}"
              f"{len(ts)/len(sel):>10.1f}{sum(LA.net(t) for t in ts)/len(ts):>+11.4f}"
              f"{(dr<0).mean():>10.0%}")

print("\n" + "=" * 92)
print("PART 4a — SAME-SESSION one-way push (diagnostic: what a loser IS)")
print("=" * 92)
for era, p in (("2020-22", LA.ERAS["2020-22"]["bars"]), ("2023-26", None)):
    tab(era, p, "push", "|close-open| / session range, whole session")

print("\n" + "=" * 92)
print("PART 4b — does the FIRST 6 HOURS tip the day off?  (18:00-24:00 ET, Asia)")
print("=" * 92)
for era, p in (("2020-22", LA.ERAS["2020-22"]["bars"]), ("2023-26", None)):
    tab(era, p, "early_R", "book's own P&L in the first 6 hours -> rest of day")
