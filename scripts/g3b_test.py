"""G3b — widen first-in-wins from one stop-floor to ANY distance.

Current G3: no book opens a same-direction position within one stop floor
(5pt) of any open position. G3b: skip a same-direction entry while any
other book holds a same-direction position, regardless of price gap.

Receipt behind it (conviction audit): a same-direction position held by
another book MORE than 5pt away — outside what G3 bans — ran -0.070 net
EV, negative in all four half-cells (level book -0.05/-0.08, vwap
-0.02/-0.10), n = 552 + 455, which was under the audit's 400/half bar.

PREREGISTERED, written before this run:
  ADOPT if total R improves AND drawdown-matched R/day improves in BOTH
  halves. Removing negative-EV trades raises total R almost by
  construction, so the binding condition is the risk-adjusted one and
  the split-half consistency.
  Tested on the flat empire AND the armed empire, since arming is the
  adopted layer and a rail must earn its place on the book that ships.

Same standing caveat as G3 itself: the rail pass is post-hoc
chronological; the exact joint simulation is executor-stage work.
"""
import sys
import numpy as np
from collections import defaultdict
sys.path.insert(0, ".")
import scripts.conviction_sizing as CS

FLOOR = 5.0


def rail(books, any_distance=False):
    byday = defaultdict(list)
    for b in books:
        for t in b:
            byday[t["day"]].append(t)
    kept, g3n = defaultdict(list), 0
    for d, ts in byday.items():
        ts.sort(key=lambda t: (t["fill_hrs"], t["t_sig_hrs"]))
        open_pos = []
        for t in ts:
            f, en = t["fill_hrs"], t["fill_hrs"] + t["hold_min"] / 60
            open_pos = [p for p in open_pos if p[1] > f]
            block = any(dr == t["dir"] and (any_distance or abs(px - t["entry"]) <= FLOOR)
                        for _, _, dr, px in open_pos)
            if block:
                g3n += 1
                continue
            if len(open_pos) >= 4:
                continue
            if sum(1 for *_, dr, _ in open_pos if dr == t["dir"]) >= 3:
                continue
            open_pos.append((f, en, t["dir"], t["entry"]))
            kept[d].append(t)
    return kept, g3n


def series(kept, grid):
    d = defaultdict(float)
    for day, ts in kept.items():
        for t in ts:
            d[day] += t["r"] - 0.5 / t["risk"]
    return np.array([d.get(k, 0.0) for k in grid])


def show(tag, suffix):
    lv = CS.load(f"pd_va_trades_lvall_xr30_sar_through_tf1_ng{suffix}.jsonl.gz")
    sv = CS.load(f"vwap_rev_tf1_retest_xr30_dd{suffix}.jsonl.gz", champ_cell=True)
    nv = CS.load(f"vwap_rev_tf1_retest_xr30_nyanc_dd{suffix}.jsonl.gz", champ_cell=True)
    books = [lv, sv, nv]
    grid = sorted({t["day"] for b in books for t in b})
    MID = grid[len(grid) // 2]
    is_m = np.array([g < MID for g in grid])
    print(f"\n{tag}")
    print(f"  {'rail':<28}{'trades':>8}{'blocked':>9}{'total R':>9}{'R/day':>8}"
          f"{'maxDD':>8}{'Sharpe':>8}{'IS R/d':>8}{'OOS R/d':>9}")
    res = {}
    for lab, anyd in (("G3  (within one floor)", False), ("G3b (any distance)", True)):
        kept, blocked = rail(books, anyd)
        v = series(kept, grid)
        n = sum(len(x) for x in kept.values())
        res[lab] = (v, n)
        print(f"  {lab:<28}{n:>8,}{blocked:>9,}{v.sum():>+9.0f}{v.mean():>+8.2f}"
              f"{CS.maxdd(v):>8.1f}{v.mean()/v.std():>8.3f}"
              f"{v[is_m].mean():>+8.2f}{v[~is_m].mean():>+9.2f}")
    (a, na), (b, nb) = res["G3  (within one floor)"], res["G3b (any distance)"]
    sc = CS.maxdd(a) / CS.maxdd(b)
    dm = (b * sc)
    di = dm[is_m].mean() / a[is_m].mean() - 1
    do = dm[~is_m].mean() / a[~is_m].mean() - 1
    print(f"  -> G3b removes {na - nb:,} more trades ({(na-nb)/na:.1%}), "
          f"total R {b.sum() - a.sum():+.0f}")
    print(f"  -> drawdown-matched (scale {sc:.3f}): IS {di:+.1%}  OOS {do:+.1%}")
    ok = b.sum() > a.sum() and di > 0 and do > 0
    print(f"  -> VERDICT: {'ADOPT' if ok else 'not adopted'} "
          f"(needs total R up AND drawdown-matched R/day up in both halves)")


show("FLAT EMPIRE (frozen spec)", "")
show("ARMED EMPIRE (the adopted layer)", "_arm1")
