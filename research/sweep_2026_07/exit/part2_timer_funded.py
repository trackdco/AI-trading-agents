#!/usr/bin/env python3
"""EXIT-TIMING STUDY — PART 2: the N-minute timer, measured completely.

######################################################################################
# THIS RULE CANNOT BE CONFIRMED ON THIS BOOK. Stated first, and repeated on the       #
# dashboard:                                                                          #
#   * It was found POST-HOC, after the pre-registered select-on-IS procedure had      #
#     already rejected it.                                                            #
#   * It LOST in-sample (-$575 at 45 min) and gained everything out-of-sample         #
#     (+$9,075) — a sign flip across the one regime boundary this book contains.      #
#   * 15 of 68 configurations in that sweep flip negative-to-positive by chance.      #
# Measuring it completely is not the same as validating it. Only Part 4's forward     #
# shadow log can ever do that.                                                        #
######################################################################################

WHAT IS MEASURED (no selection, no sweep — a fixed grid reported as a SHAPE):
  horizons 30 / 45 / 60 / 90 minutes, plus canon as the reference
  full funded-risk suite for each: terminal P&L, max drawdown, minimum available drawdown,
  daily-loss-limit breach days, and bust probability by day-block bootstrap, NAKED and with
  the full safety spine (Tier-1 proximity halt + DD-scaling ramp)
  split by year and by segment

THE RULE. Original stop stays fixed and live for the whole hold. If price touches the stop the
trade exits there at -1R. Otherwise, at the close of bar N, the position is closed at market.
No trailing at any point — that is the source of the variance cost being quantified here.

COSTS: $1.24/micro round trip; $0.50/micro slippage on marketable exits (stop and timer are
both marketable). The canon reference carries its OWN cost convention from its own book — that
difference is stated, not merged.

BASELINE: partially remediated (C only) + news filter. W and dep_* leaky in the selection path.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/exit"
COMM_RT, SLIP_MKT = 1.24, 0.50
START_EQ, DD_AMT, DAY_HALT, NBOOT = 50_000.0, 2_000.0, -800.0, 5_000
HOR = (30, 45, 60, 90)
rng = np.random.default_rng(20260729)

F = pd.read_csv(f"{OUT}/part1_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")
assert len(F) == 182 and abs(F.pl.sum() - 21097.875) < 1e-6
print(f"anchor OK: {len(F)} PM trades ${F.pl.sum():+,.2f}")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values

FULL = pd.read_parquet(f"{REPO}/research/sweep_2026_07/orderflow/job2_books/sized_C_news.parquet")
FULL["ft"] = pd.to_datetime(FULL.fill, utc=True)
_et = FULL.ft.dt.tz_convert("America/New_York")
FULL["hm"] = _et.dt.hour * 60 + _et.dt.minute
FULL["rk"] = FULL.risk_pts.round(4)
FULL["key"] = FULL.day.astype(str) + "|" + FULL.ft.astype(str) + "|" + FULL.direction + "|" + FULL["rk"].astype(str)
F["key"] = F.day.astype(str) + "|" + F.ft.astype(str) + "|" + F.direction + "|" + F.risk_pts.round(4).astype(str)
assert F.key.isin(set(FULL.key)).all(), "PM trades must all be in the full sized book"
print(f"full sized book: {len(FULL)} trades ${FULL.pl.sum():+,.2f} "
      f"(NY {int((FULL.session=='NY').sum())} / LONDON {int((FULL.session=='LONDON').sum())})")


def timer_pl(h):
    """Per-trade dollar P&L for the PM trades under an h-minute timer."""
    out, how = np.empty(len(F)), []
    for i, r in enumerate(F.itertuples(index=False)):
        d = 1 if r.direction == "long" else -1
        k0 = int(r.k0)
        ce = r.et.replace(hour=15, minute=55, second=0, microsecond=0)
        kend = min(int(BI.searchsorted(ce.tz_convert("UTC"), side="right")), len(BI) - 1)
        kh = min(k0 + h, kend, len(BI) - 1)
        lo = ((BL[k0:kh + 1] - r.entry) if d > 0 else (r.entry - BH[k0:kh + 1])) / r.risk_pts
        hit = np.nonzero(lo <= -1.0)[0]
        if len(hit):
            R_, why = -1.0, "stop"
        else:
            R_ = float((((BC[kh] - r.entry) if d > 0 else (r.entry - BC[kh])) / r.risk_pts))
            why = "timer"
        out[i] = r.micros * (R_ * r.risk_pts * 2.0 - COMM_RT - SLIP_MKT)
        how.append(why)
    return out, np.array(how)


def funded(df, ddscale=False):
    df = df.sort_values("fill")
    eq, line, cur, daypl = START_EQ, START_EQ - DD_AMT, None, 0.0
    busted, minav, breaches, peak, mdd = False, 1e9, 0, START_EQ, 0.0
    for day_, pl in zip(df.day.values, df.pl.values):
        if day_ != cur:
            if cur is not None:
                line = min(max(line, eq - DD_AMT), START_EQ)
                if daypl <= DAY_HALT:
                    breaches += 1
            cur, daypl = day_, 0.0
        avail = eq - line
        if daypl <= DAY_HALT or avail <= 100.0:
            continue
        eq += pl
        daypl += pl
        minav = min(minav, eq - line)
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
        if eq <= line:
            busted = True
    if daypl <= DAY_HALT:
        breaches += 1
    return dict(pl=eq - START_EQ, busted=busted, min_available=minav, max_dd=mdd,
                breach_days=breaches)


def bust_prob(df, ddscale=False):
    days = df.day.unique()
    by = {d: df[df.day == d].pl.values for d in days}
    busts = 0
    for _ in range(NBOOT):
        order = rng.choice(days, size=len(days), replace=True)
        eq, line, dead = START_EQ, START_EQ - DD_AMT, False
        for d in order:
            avail = eq - line
            scale = 1.0
            if ddscale:
                if avail > 3000:
                    scale = (200 + 75 * np.floor((avail - 3000) / 1000)) / 200.0
                if avail < 1500:
                    scale = min(scale, max(0.0, (avail - 100.0) / 1400.0))
                if avail <= 100.0:
                    continue
            daypl = 0.0
            for pl in by[d]:
                if daypl <= DAY_HALT * scale:
                    continue
                daypl += pl * scale
            eq += daypl
            line = min(max(line, eq - DD_AMT), START_EQ)
            if eq <= line:
                dead = True
                break
        busts += dead
    return 100.0 * busts / NBOOT


def swap(pl_new):
    B = FULL.copy()
    m = dict(zip(F.key.values, pl_new))
    B["pl"] = [m.get(k, p) for k, p in zip(B.key.values, B.pl.values)]
    return B


print("\n" + "=" * 112)
print("PART 2 — FUNDED-RISK SUITE, FULL SIZED BOOK (NY + London), timer applied to PM only")
print("=" * 112)
print(f"{'variant':16s} {'PM P&L':>11} {'book P&L':>11} {'maxDD':>9} {'min avail':>10} "
      f"{'breach d':>9} {'bust naked':>11} {'bust spine':>11} {'stop%':>7}")
res = {}
base_full = funded(FULL)
base_bn, base_bs = bust_prob(FULL, False), bust_prob(FULL, True)
print(f"{'canon (ref)':16s} {F.pl.sum():>+11,.0f} {FULL.pl.sum():>+11,.0f} "
      f"{base_full['max_dd']:>9,.0f} {base_full['min_available']:>10,.0f} "
      f"{base_full['breach_days']:>9} {base_bn:>10.2f}% {base_bs:>10.2f}% {'—':>7}")
res["canon"] = dict(pm_pl=float(F.pl.sum()), book_pl=float(FULL.pl.sum()),
                    **{k: float(v) if not isinstance(v, bool) else v
                       for k, v in base_full.items()},
                    bust_naked=base_bn, bust_spine=base_bs, stop_share=None)
for h in HOR:
    pl_new, how = timer_pl(h)
    B = swap(pl_new)
    f_ = funded(B)
    bn, bs = bust_prob(B, False), bust_prob(B, True)
    sshare = float((how == "stop").mean())
    res[f"timer{h}"] = dict(pm_pl=float(pl_new.sum()), book_pl=float(B.pl.sum()),
                            **{k: float(v) if not isinstance(v, bool) else v
                               for k, v in f_.items()},
                            bust_naked=bn, bust_spine=bs, stop_share=sshare)
    print(f"{'timer '+str(h)+'m':16s} {pl_new.sum():>+11,.0f} {B.pl.sum():>+11,.0f} "
          f"{f_['max_dd']:>9,.0f} {f_['min_available']:>10,.0f} {f_['breach_days']:>9} "
          f"{bn:>10.2f}% {bs:>10.2f}% {sshare*100:>6.0f}%")

print(f"\nSHAPE CHECK — is the benefit a spike at one horizon (fitting) or a plateau (structure)?")
pm = [res[f"timer{h}"]["pm_pl"] for h in HOR]
print(f"  PM P&L across 30/45/60/90: " + "  ".join(f"${v:+,.0f}" for v in pm))
print(f"  spread across the grid: ${max(pm)-min(pm):,.0f} on a mean of ${np.mean(pm):,.0f} "
      f"({(max(pm)-min(pm))/abs(np.mean(pm))*100:.0f}% of the level)")
print(f"  all four above canon (${F.pl.sum():+,.0f})? "
      f"{all(v > F.pl.sum() for v in pm)}")
res["shape"] = dict(values=pm, spread=float(max(pm) - min(pm)), mean=float(np.mean(pm)),
                    all_above_canon=bool(all(v > F.pl.sum() for v in pm)))

print(f"\nWHERE THE MONEY IS — by year and by segment (timer 45m vs canon, PM slice)")
pl45, how45 = timer_pl(45)
F["pl_t45"] = pl45
F["yr"] = F.day.str[:4]
print(f"{'cut':26s} {'n':>4} {'canon':>11} {'timer45':>11} {'delta':>11}")
for nm, g in list(F.groupby("yr")) + [(s, F[F.seg == s]) for s in
                                      ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29")] \
        + [("IS half", F[~F.oos]), ("OOS half", F[F.oos])]:
    flag = "  INSUFFICIENT" if len(g) < 10 else ""
    print(f"{str(nm):26s} {len(g):>4} {g.pl.sum():>+11,.0f} {g.pl_t45.sum():>+11,.0f} "
          f"{g.pl_t45.sum()-g.pl.sum():>+11,.0f}{flag}")
    res.setdefault("where", {})[str(nm)] = dict(n=len(g), canon=float(g.pl.sum()),
                                                timer=float(g.pl_t45.sum()),
                                                delta=float(g.pl_t45.sum() - g.pl.sum()),
                                                insufficient=bool(len(g) < 10))
res["provenance"] = dict(
    warning="POST-HOC. Rejected by the pre-registered selection. Lost in-sample (-$575), "
            "gained out-of-sample (+$9,075). 15/68 sweep configs flip negative-to-positive by "
            "chance. CANNOT BE CONFIRMED ON THIS BOOK.",
    costs="$1.24/micro RT + $0.50/micro slippage on marketable exits; canon reference carries "
          "its own cost convention",
    engine="$50k start, $2,000 EOD-trailing DD locked at the floor, Tier-1 daily halt -$800 "
           "plus $100 proximity halt; spine adds the DD-scaling ramp",
    nboot=NBOOT)
F[["day", "ft", "seg", "oos", "pl", "pl_t45"]].to_csv(f"{OUT}/part2_timer_trades.csv", index=False)
json.dump(res, open(f"{OUT}/part2_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part2_report.json + part2_timer_trades.csv")
