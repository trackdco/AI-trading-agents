"""The 2020-2022 EMPIRE — the full 2023-26 stack replicated on the older tape.

Not a holdout. The 2020-22 value-area result was already read (docs/
FINDINGS-holdout-2020-2022.md), so this cannot be evidence against
overfitting. It is a REPLICATION CHECK, and it answers one question:

    do the four extra level families, the two VWAP books, the rails and
    ARMING still behave the way they do in 2023-26, in a crash year and a
    bear market?

Frozen constants throughout (Run A): floor 5.0, depth 3.0, cap 30pt,
bin 1.0 - the certified NQ values, unscaled, exactly as the holdout's
winning arm used them.

DIFFERENCE FROM THE 2023-26 EMPIRE, stated up front: no news gate. The
repo's news_archive.csv starts 2023-01-04, so G8 cannot be applied to
2020-22 at all. On 2023-26 the gate is a wash on totals (S19: +1,131R ->
+1,133R) so this is worth ~nothing in R, but it is not like-for-like and
every table below is labelled ng0.

Everything else - honest fills (one tick through), 0.5pt round-trip cost
in R, ambiguity scored as a loss, G3 first-in-wins, G5 cap 4, G6
same-direction cap 3, roll days excluded - is the same code path the
2023-26 empire runs.

    python3 hold_empire.py
"""
import sys
from collections import defaultdict

import numpy as np

QL = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0, QL)
import scripts.conviction_sizing as CS          # noqa: E402

COST = CS.COST_PTS


def books(arm=False):
    am = "_arm1" if arm else ""
    lv = CS.load(f"pd_va_trades_nq20a_lvall_xr30_sar_through_tf1{am}.jsonl.gz")
    sv = CS.load(f"vwap_rev_tf1_retest_nq20a_ng0_xr30_dd{am}.jsonl.gz", champ_cell=True)
    nv = CS.load(f"vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd{am}.jsonl.gz", champ_cell=True)
    return lv, sv, nv


def net(t):
    return t["r"] - COST / t["risk"]


def wr(ts):
    tp = sum(1 for t in ts if t["res"] == "TARGET")
    st = sum(1 for t in ts if t["res"] == "STOP")
    return tp / max(tp + st, 1)


def metrics(kept):
    days = sorted(kept)
    v = np.array([sum(net(t) for t in kept[d]) for d in days])
    flat = [t for d in days for t in kept[d]]
    eq = np.cumsum(v)
    return dict(n=len(flat), per_day=len(flat) / len(days), wr=wr(flat),
                ev=sum(net(t) for t in flat) / len(flat), total=float(v.sum()),
                rday=float(v.mean()), maxdd=float((eq - np.maximum.accumulate(eq)).min()),
                sharpe=float(v.mean() / v.std()), green=float((v > 0).mean()),
                worst=float(v.min()), days=len(days), v=v, dd=days)


def row(lbl, m):
    return (f"{lbl:<22}{m['n']:>8,}{m['per_day']:>8.1f}{m['wr']:>8.1%}"
            f"{m['ev']:>+10.4f}{m['total']:>+10.0f}{m['rday']:>+9.2f}"
            f"{m['maxdd']:>+8.1f}{m['sharpe']:>8.3f}{m['green']:>7.0%}")


HDR = (f"{'':<22}{'trades':>8}{'/day':>8}{'WR':>8}{'EV/trade':>10}"
       f"{'net R':>10}{'R/day':>9}{'maxDD':>8}{'Sharpe':>8}{'green':>7}")

print(__doc__.split("\n\n")[1].strip().replace("\n", " "))
print("\n" + "=" * 96)
print("2020-2022 EMPIRE — frozen constants, no news gate (ng0)")
print("=" * 96)

res = {}
for arm in (False, True):
    lv, sv, nv = books(arm)
    tag = "armed 1R" if arm else "flat (frozen spec)"
    print(f"\nbooks, {tag}: 8-level {len(lv):,} + vwap-session {len(sv):,} "
          f"+ vwap-ny {len(nv):,} = {len(lv)+len(sv)+len(nv):,}")
    kept = CS.rail_pass([lv, sv, nv])
    res[arm] = metrics(kept)
    res[("sep", arm)] = (lv, sv, nv)

print("\n" + HDR)
print("-" * 96)
print(row("flat (frozen spec)", res[False]))
print(row("armed 1R", res[True]))

f, a = res[False], res[True]
print(f"\narming vs flat: EV/trade {a['ev']/f['ev']-1:+.1%}   "
      f"total R {a['total']/f['total']-1:+.1%}   "
      f"maxDD {a['maxdd']-f['maxdd']:+.1f}R ({a['maxdd']/f['maxdd']-1:+.1%})   "
      f"Sharpe {f['sharpe']:.3f} -> {a['sharpe']:.3f}")

# per-book standalone, unrailed
print("\n" + "=" * 96)
print("PER BOOK, STANDALONE (no rails) — flat")
print("=" * 96)
print(f"{'':<22}{'trades':>8}{'WR':>10}{'EV/trade':>12}{'net R':>10}")
for nm, b in zip(("8-level", "vwap-session", "vwap-ny"), res[("sep", False)]):
    print(f"{nm:<22}{len(b):>8,}{wr(b):>10.1%}{sum(net(t) for t in b)/len(b):>+12.4f}"
          f"{sum(net(t) for t in b):>+10.0f}")

# yearly + monthly on the railed books
for arm in (False, True):
    m = res[arm]
    tag = "ARMED" if arm else "FLAT"
    yr = defaultdict(float); mo = defaultdict(float)
    for d, x in zip(m["dd"], m["v"]):
        yr[d[:4]] += x; mo[d[:7]] += x
    print(f"\n{tag} by year:  " + "   ".join(f"{k} {v:+.0f}R" for k, v in sorted(yr.items())))
    pos = sum(1 for v in mo.values() if v > 0)
    print(f"{tag} months: {pos}/{len(mo)} positive   worst {min(mo.values()):+.1f}R   "
          f"median {np.median(list(mo.values())):+.1f}R   best {max(mo.values()):+.1f}R")
