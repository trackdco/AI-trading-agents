"""AUTOPSY PART 5 — the early-session read, decontaminated.

Part 4b conditioned REST-OF-DAY on FIRST-6-HOURS but reported whole-day R,
which contains the first 6 hours - so a good start scored itself. This splits
them: the conditioning variable is the book's P&L on fills before hour 6, and
the outcome is R and EV/trade on fills from hour 6 onward, which the
conditioning variable cannot contain.

Note what this is NOT: a daily loss cutoff. That was built and killed (it made
max drawdown worse at -20, -30 and -40pt alike). This asks the narrower
question of whether the rest of the day is WORTH LESS after a bad start -
which is a statement about EV, not a stop rule - and any rule from it changes
occupancy within the day, so it would need its own engine run (the G3b lesson).
"""
import sys
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad")
import loser_autopsy as LA   # noqa: E402

CUT = 6.0
print("\n" + "=" * 96)
print(f"PART 5 — first {CUT:g}h of the session vs THE REST OF THE DAY ONLY (no overlap)")
print("=" * 96)
for era in LA.ERAS:
    days, R, kept, feat = LA.DATA[(era, False)]
    rows = []
    for d in days:
        early = [t for t in kept[d] if t["fill_hrs"] < CUT]
        late = [t for t in kept[d] if t["fill_hrs"] >= CUT]
        if not early or not late:
            continue
        rows.append((sum(LA.net(t) for t in early), late))
    xs = np.array([r[0] for r in rows])
    e = LA.buckets(xs, 4)
    idx = np.clip(np.digitize(xs, e[1:-1]), 0, 3)
    print(f"\n{era}   ({len(rows)} days with trades on both sides of the cut)")
    print(f"  {'first 6h P&L':<18}{'days':>7}{'REST-of-day R':>16}{'trades':>9}"
          f"{'EV/trade':>11}{'WR':>8}{'red':>7}")
    for j in range(4):
        sel = [r for r, i in zip(rows, idx) if i == j]
        ts = [t for r in sel for t in r[1]]
        dr = np.array([sum(LA.net(t) for t in r[1]) for r in sel])
        tp = sum(1 for t in ts if t["res"] == "TARGET")
        st = sum(1 for t in ts if t["res"] == "STOP")
        print(f"  {e[j]:>7.1f}–{e[j+1]:<10.1f}{len(sel):>7}{dr.mean():>+16.2f}"
              f"{len(ts)/len(sel):>9.1f}{sum(LA.net(t) for t in ts)/len(ts):>+11.4f}"
              f"{tp/max(tp+st,1):>8.1%}{(dr<0).mean():>7.0%}")
    lo = [r for r, i in zip(rows, idx) if i == 0]
    hi = [r for r, i in zip(rows, idx) if i == 3]
    f = lambda s: sum(LA.net(t) for r in s for t in r[1]) / sum(len(r[1]) for r in s)
    print(f"  -> rest-of-day EV worst vs best start: {f(lo):+.4f} vs {f(hi):+.4f}  "
          f"(spread {f(hi)-f(lo):+.4f}R/trade)")
