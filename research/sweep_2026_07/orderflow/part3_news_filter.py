#!/usr/bin/env python3
"""PART 3 — the news filter: register it and run the test that can kill it.

WHY IT IS THE STRONGEST LEAD. It improved the sized pre-market slice in the leaky arm AND in
the partially-remediated arm independently; it is NOT fitted to this book (the veto is a
published economic calendar, so it is knowable at fill time by construction); and it needs no
threshold estimated from outcomes.

THE TEST THAT CAN KILL IT (Brake, required). It drops trades in a window where a handful of
trades carry nearly all the P&L. If the entire benefit is one bad day in fourteen months, it is
an anecdote, not a rule. So: recompute the benefit with the single largest avoided trade
removed, then jackknife over EVERY avoided trade and count how many single removals flip the
sign. Reported whichever way it goes.

Both arms are run independently. Both halves of the split are reported: the filter is not
fitted to either, so neither half is privileged by construction — but the OOS half is the
headline, consistent with the rest of the study.

BASELINE CAVEAT: the C arm is PARTIALLY REMEDIATED (C only). W and the dep_* family remain
leaky in the selection path of every book here.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
BOOKS = f"{OUT}/job2_books"
SPLIT, NBOOT = "2025-12-23", 4000
rng = np.random.default_rng(20260729)
REP = {"split": SPLIT, "baseline_caveat": "C arm is PARTIALLY REMEDIATED (C only); "
                                          "W and dep_* remain leaky in all books here"}

def pm(name):
    b = pd.read_parquet(f"{BOOKS}/sized_{name}.parquet")
    b["ft"] = pd.to_datetime(b.fill, utc=True)
    et = b.ft.dt.tz_convert("America/New_York")
    b["hm"] = et.dt.hour * 60 + et.dt.minute
    b = b[(b.session == "NY") & (b.hm >= 480) & (b.hm < 570)].copy()
    b["rk"] = b.risk_pts.round(4)
    b["key"] = (b.day.astype(str) + "|" + b.ft.astype(str) + "|" + b.direction + "|"
                + b["rk"].astype(str))
    return b

def dayboot(a_by_day, b_by_day, days):
    out = []
    for _ in range(NBOOT):
        pick = rng.choice(days, size=len(days), replace=True)
        out.append(sum(b_by_day.get(d, 0.0) - a_by_day.get(d, 0.0) for d in pick))
    o = np.array(out)
    return (float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5)),
            float(min(2 * min((o <= 0).mean(), (o >= 0).mean()), 1.0)))

print("=" * 100)
print("NEWS FILTER — sized pre-market slice, both arms")
print("=" * 100)
for arm, lab in (("L", "LEAKY arm (conf_PM)"), ("C", "PARTIALLY-REMEDIATED arm (C only)")):
    A, Bk = pm(f"{arm}_nonews"), pm(f"{arm}_news")
    avoided = A[~A.key.isin(set(Bk.key))]
    added = Bk[~Bk.key.isin(set(A.key))]
    delta = Bk.pl.sum() - A.pl.sum()
    days = sorted(set(A.day) | set(Bk.day))
    abd = A.groupby("day").pl.sum().to_dict()
    bbd = Bk.groupby("day").pl.sum().to_dict()
    lo, hi, p = dayboot(abd, bbd, days)
    print(f"\n--- {lab} ---")
    print(f"  no-news : {len(A):>3} trades  ${A.pl.sum():+,.2f}")
    print(f"  news    : {len(Bk):>3} trades  ${Bk.pl.sum():+,.2f}")
    print(f"  DELTA   : {len(Bk)-len(A):+d} trades  ${delta:+,.2f}   "
          f"day-clustered 95% CI [${lo:+,.0f}, ${hi:+,.0f}]  p={p:.3f}")
    print(f"  avoided {len(avoided)} trades (sum ${avoided.pl.sum():+,.2f}), "
          f"{len(added)} newly appear from freed nth slots (sum ${added.pl.sum():+,.2f})")
    R = dict(n_nonews=len(A), pl_nonews=float(A.pl.sum()), n_news=len(Bk),
             pl_news=float(Bk.pl.sum()), delta=float(delta), ci=[lo, hi], p=p,
             n_avoided=len(avoided), pl_avoided=float(avoided.pl.sum()),
             n_added=len(added), pl_added=float(added.pl.sum()))

    # ---- THE KILL TEST: remove the single largest avoided trade
    if len(avoided):
        av = avoided.reindex(avoided.pl.abs().sort_values(ascending=False).index)
        biggest = av.iloc[0]
        print(f"\n  largest avoided trade: {biggest.day} {biggest.ft}  ${biggest.pl:+,.2f} "
              f"({abs(biggest.pl)/max(abs(delta),1e-9)*100:.0f}% of the delta's magnitude)")
        d_excl = delta - (-biggest.pl)      # removing it from the no-news book
        print(f"  DELTA with that one trade removed from the no-news book: ${d_excl:+,.2f} "
              f"-> {'STILL POSITIVE' if d_excl > 0 else 'SIGN FLIPS: the benefit was that one day'}")
        jack = [delta - (-t.pl) for t in av.itertuples()]
        flips = sum(1 for j in jack if (j > 0) != (delta > 0))
        print(f"  jackknife over all {len(av)} avoided trades: {flips} single removals flip the "
              f"sign; delta range [${min(jack):+,.0f}, ${max(jack):+,.0f}]")
        top5 = av.head(5)[["day", "pl"]].values.tolist()
        print(f"  five largest avoided: " + ", ".join(f"{d} ${v:+,.0f}" for d, v in top5))
        R.update(largest_avoided=dict(day=str(biggest.day), pl=float(biggest.pl)),
                 delta_excl_largest=float(d_excl), jackknife_flips=int(flips),
                 jackknife_range=[float(min(jack)), float(max(jack))],
                 survives_kill_test=bool(d_excl > 0), top5_avoided=top5)

    # ---- by half
    for half, sel in (("IS  (< split)", lambda d: d < SPLIT), ("OOS (>= split)", lambda d: d >= SPLIT)):
        a2, b2 = A[A.day.map(sel)], Bk[Bk.day.map(sel)]
        dd = b2.pl.sum() - a2.pl.sum()
        n_av = len(a2[~a2.key.isin(set(b2.key))])
        print(f"  {half}: no-news ${a2.pl.sum():+,.2f} ({len(a2)}) -> news ${b2.pl.sum():+,.2f} "
              f"({len(b2)})  delta ${dd:+,.2f}  [{n_av} avoided]")
        R[f"half_{half.split()[0]}"] = dict(pl_nonews=float(a2.pl.sum()), pl_news=float(b2.pl.sum()),
                                            delta=float(dd), n_avoided=n_av)
    REP[arm] = R

print("\n" + "=" * 100)
print("READING: the filter is not fitted to this book, so a positive delta in BOTH arms is")
print("evidence of a real, knowable-at-fill effect. The kill test is what decides whether it is")
print("a RULE or an ANECDOTE: if removing one avoided trade flips the sign, it is an anecdote.")
json.dump(REP, open(f"{OUT}/part3_results.json", "w"), indent=1, default=float)
print(f"wrote {OUT}/part3_results.json")
