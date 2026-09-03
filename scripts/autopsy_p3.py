"""AUTOPSY PART 3 — the control the headline needs, and what a loser actually IS.

Part 2 found prior-session volatility 'survives' with a 6-10R day spread. But
day-R = trades x EV/trade, and a wide prior day makes more signals. If EV/trade
is FLAT across volatility buckets then the whole effect is opportunity count,
not quality: nothing to filter, and no bearing on losing days at all. This
separates the two. It also asks what a losing day looks like from INSIDE
(same-session features - diagnostic only, unusable as a filter, and labelled).
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad")
import loser_autopsy as LA   # noqa: E402  (runs parts 1-2, then we reuse its DATA)

print("\n" + "=" * 92)
print("PART 3a — DECOMPOSITION: is 'high prior vol pays' quality, or just more trades?")
print("=" * 92)
for era in LA.ERAS:
    days, R, kept, feat = LA.DATA[(era, False)]
    ds = [d for d in days if d in feat and np.isfinite(feat[d]["vol_ratio"])]
    xs = np.array([feat[d]["vol_ratio"] for d in ds])
    e = LA.buckets(xs, 4)
    idx = np.clip(np.digitize(xs, e[1:-1]), 0, 3)
    print(f"\n{era}")
    print(f"  {'prior vol ratio':<18}{'days':>7}{'day R':>9}{'trades/day':>12}"
          f"{'EV/trade':>11}{'WR':>8}{'red days':>10}")
    for k in range(4):
        sel = [d for d, i in zip(ds, idx) if i == k]
        ts = [t for d in sel for t in kept[d]]
        dr = np.array([R[d] for d in sel])
        print(f"  {e[k]:.2f}–{e[k+1]:<13.2f}{len(sel):>7}{dr.mean():>+9.1f}"
              f"{len(ts)/len(sel):>12.1f}"
              f"{sum(LA.net(t) for t in ts)/len(ts):>+11.4f}{LA.wr(ts) if hasattr(LA,'wr') else 0:>8.1%}"
              f"{(dr<0).mean():>10.0%}")

print("\n" + "=" * 92)
print("PART 3b — WHAT A LOSING DAY IS, FROM INSIDE (same-session; DIAGNOSTIC ONLY,")
print("          these are not knowable at the open and can never be a filter)")
print("=" * 92)
for era, path in (("2020-22", LA.ERAS["2020-22"]["bars"]), ("2023-26", None)):
    bars = LA.load_bars(path)
    days, R, kept, feat = LA.DATA[(era, False)]
    rows = []
    for d in days:
        t0 = pd.Timestamp(f"{d} 18:00", tz=LA.OB.NY)
        s = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if len(s) < 300:
            continue
        rng = float(s.high.max() - s.low.min())
        push = abs(float(s.close.iloc[-1]) - float(s.open.iloc[0])) / rng if rng else np.nan
        rows.append((d, R[d], rng, push, len(kept[d])))
    rows.sort(key=lambda x: x[1])
    n = len(rows)
    print(f"\n{era}  ({n} days)")
    print(f"  {'group':<14}{'days':>6}{'mean R':>9}{'sess range':>12}"
          f"{'push |C-O|/rng':>16}{'trades':>8}")
    for lbl, sl in (("worst 5%", rows[:n // 20]), ("worst 20%", rows[:n // 5]),
                    ("all", rows), ("best 20%", rows[-(n // 5):])):
        print(f"  {lbl:<14}{len(sl):>6}{np.mean([x[1] for x in sl]):>+9.1f}"
              f"{np.mean([x[2] for x in sl]):>12.1f}"
              f"{np.nanmean([x[3] for x in sl]):>16.3f}{np.mean([x[4] for x in sl]):>8.1f}")
