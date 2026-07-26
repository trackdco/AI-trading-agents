#!/usr/bin/env python3
"""DAY-STOP LOOKAHEAD AUDIT for the London 10-13 UK book.

The book's day-stop is implemented as: sort the day's signals by entry time, walk them in
order, and stop taking further trades once a trade's FINAL NET is negative.

That is not executable. Signals fire every 15 minutes, but a trade takes a median of ~2 hours
to resolve. When a second signal fires while the first is STILL OPEN, its final net is not yet
knowable -- so the backtest is using information from the future to decline a trade.

This script quantifies the bias by rebuilding the book under three day-stop rules:

  A  as-written      block on a prior trade's final net, regardless of whether it has closed
                     (the published 55-trade book -- contains lookahead)
  B  realtime        block only once a losing trade has actually CLOSED at or before the
                     signal bar; stacking otherwise permitted
  C  realtime+single realtime day-stop AND never more than one position open at a time

B is what the rule as written in the trade plan actually does live. C is what most traders
assume they are doing.

Also reports concurrency and correlated stop-out clusters -- several positions can share one
stop level and die in the same minute, which the as-written book structurally cannot contain.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_daystop_lookahead.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
RISK = 300.0                                   # $ per 1R, flat, for the dollar view

print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukt"] = b.uk.dt.time

m = (b.set_index("ts").resample("15min", label="right", closed="right")
     .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
          close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"]))
_uk = m.index.tz_convert("Europe/London")
m["ukt"] = _uk.time
m["ukday"] = _uk.strftime("%Y-%m-%d")
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["v10"] = m.volume.rolling(10).mean().shift(1)
m["slo"] = m.low.rolling(5).min()
m["shi"] = m.high.rolling(5).max()
M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= "2025-07-01") & (M.ukday <= "2026-07-15")].reset_index(drop=True)
a = {c: M[c].values for c in
     ["uts", "open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "v10", "slo", "shi"]}
ud, utt = M.ukday.values, M.ukt.values


def all_signals():
    """Every qualifying signal, resolved, BEFORE any day-stop is applied."""
    rows = []
    for i in range(1, len(M) - 1):
        d = ud[i]
        if d in ("2025-11-28", "2026-04-03") or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
            continue
        up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
        dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
        dr = 1 if (up and a["low"][i] <= a["ma50"][i]) else (-1 if (dn and a["high"][i] >= a["ma50"][i]) else 0)
        if dr == 0 or not (a["v10"][i] > 0 and a["volume"][i] < a["v10"][i]):
            continue
        en = a["open"][i + 1] + dr * TICK
        rf = min(a["slo"][i], a["ma50"][i]) if dr > 0 else max(a["shi"][i], a["ma50"][i])
        rk = abs(en - rf) + TICK
        if rk < 5 or rk > 70:
            continue
        st, tg = en - dr * rk, en + dr * 3 * rk
        gg, j, how = None, i + 1, None
        while j < len(M) and ud[j] == d:
            if utt[j] >= dtime(16, 30):
                gg = dr * (a["close"][j] - en); how = "time"; break
            hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
            ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
            if hs:
                gg = -rk - TICK; how = "stop"; break
            if ht:
                gg = 3 * rk - TICK; how = "target"; break
            j += 1
        if gg is None:
            j = min(j, len(M) - 1); gg = dr * (a["close"][j] - en); how = "dayend"
        net = gg * PV - COMM
        rows.append(dict(day=d, sig=i, res=j, ent=str(utt[i]), ext=str(utt[j]), dr=dr,
                         rk=rk, net=net, R=net / (rk * PV), how=how, mins=(j - i) * 15))
    return pd.DataFrame(rows).sort_values(["day", "sig"]).reset_index(drop=True)


SIG = all_signals()


def apply_daystop(mode):
    """mode: 'aswritten' | 'realtime' | 'realtime_single'"""
    keep = []
    for d, g in SIG.groupby("day"):
        taken = []                                  # (res_bar, net) of trades actually taken
        stopped = False                             # as-written latch
        for _, r in g.iterrows():
            if mode == "aswritten":
                if stopped:
                    continue
                keep.append(r.name)
                if r.net < 0:
                    stopped = True
                continue
            # --- executable variants: entry happens at the OPEN of bar sig+1, so only
            #     trades that resolved at or before bar sig are known at decision time.
            known_loss = any(res <= r.sig and nt < 0 for res, nt in taken)
            if known_loss:
                continue
            if mode == "realtime_single":
                open_now = any(res > r.sig for res, _ in taken)   # still holding
                if open_now:
                    continue
            keep.append(r.name)
            taken.append((r.res, r.net))
    return SIG.loc[keep].copy().reset_index(drop=True)


def stats(D, label):
    S_ = D.sort_values(["day", "sig"])
    eq = (S_.R * RISK).cumsum().values
    peak = np.maximum.accumulate(np.concatenate([[0.0], eq]))
    dd = float((peak[1:] - eq).max())
    print(f"  {label:<26} {len(D):>3} trades  netR {D.R.sum():>+7.2f}  "
          f"WR {(D.R>0).mean()*100:>3.0f}%  ${eq[-1]:>+9,.0f}  maxDD ${dd:>7,.0f}"
          + ("   <-- BREACHES $2,000" if dd > 2000 else ""))
    return dd


if __name__ == "__main__":
    print(f"\nraw qualifying signals (no day-stop): {len(SIG)}  netR {SIG.R.sum():+.2f}\n")

    print(f"=== DAY-STOP VARIANTS (flat ${RISK:.0f} per 1R) ===")
    books = {}
    for mode, lab in (("aswritten", "A as-written (published)"),
                      ("realtime", "B realtime day-stop"),
                      ("realtime_single", "C realtime + one-at-a-time")):
        books[mode] = apply_daystop(mode)
        stats(books[mode], lab)

    A, B_, C = books["aswritten"], books["realtime"], books["realtime_single"]
    ka = set(zip(A.day, A.ent))
    extra = B_[[k not in ka for k in zip(B_.day, B_.ent)]]
    print(f"\n=== WHAT THE LOOKAHEAD HIDES ===")
    print(f"  B takes {len(extra)} trades that A declines using information it could not have had.")
    print(f"  those trades: {int((extra.R>0).sum())} winners / {int((extra.R<=0).sum())} losers, "
          f"netR {extra.R.sum():+.2f}  (${extra.R.sum()*RISK:+,.0f})")
    if len(extra):
        print(f"\n{'day':<11} {'entry':<9} {'exit':<9} {'dir':>5} {'mins':>5} {'R':>7} {'why A skipped it':<40}")
        for _, r in extra.sort_values(["day", "ent"]).iterrows():
            prior = A[(A.day == r.day)]
            pl = prior[prior.net < 0]
            why = (f"prior loss entered {pl.iloc[0].ent} still OPEN until {pl.iloc[0].ext}"
                   if len(pl) else "n/a")
            print(f"{r.day:<11} {r.ent:<9} {r.ext:<9} {'long' if r.dr>0 else 'short':>5} "
                  f"{int(r.mins):>5} {r.R:>+7.2f} {why:<40}")

    print(f"\n=== CONCURRENCY (in the executable book B) ===")
    conc = []
    for d, g in B_.groupby("day"):
        for _, r in g.iterrows():
            n = int(((g.sig <= r.sig) & (g.res > r.sig)).sum())
            conc.append((d, r.ent, n))
    cdf = pd.DataFrame(conc, columns=["day", "ent", "open_at_entry"])
    print(f"  max simultaneous open positions: {cdf.open_at_entry.max()}")
    top = cdf.sort_values("open_at_entry", ascending=False).head(5)
    for _, r in top.iterrows():
        print(f"    {r.day}  entry {r.ent}  ->  {r.open_at_entry} position(s) open")
    print(f"  days with any stacking: "
          f"{int((cdf.groupby('day').open_at_entry.max() > 1).sum())} / {cdf.day.nunique()}")

    print(f"\n=== CORRELATED STOP-OUT CLUSTERS (same day, same resolution bar, all stops) ===")
    cl = (B_[B_.how == "stop"].groupby(["day", "res", "ext"])
          .agg(n=("R", "size"), lossR=("R", "sum")).reset_index())
    cl = cl[cl.n > 1].sort_values("lossR")
    if len(cl):
        print(f"{'day':<11} {'exit bar':<9} {'stops':>6} {'total R':>9} "
              f"{'$@300':>9} {'$@500':>9} {'$@700':>9}")
        for _, r in cl.iterrows():
            print(f"{r.day:<11} {r.ext:<9} {int(r.n):>6} {r.lossR:>+9.2f} "
                  f"{r.lossR*300:>+9,.0f} {r.lossR*500:>+9,.0f} {r.lossR*700:>+9,.0f}")
        w = cl.iloc[0]
        print(f"\n  worst single instant: {w.lossR:+.2f}R in one bar. Against a $2,000 trailing DD "
              f"that is\n  ${abs(w.lossR)*500:,.0f} at the $500 rung and ${abs(w.lossR)*700:,.0f} "
              f"at the $700 rung -- account-ending in one minute.")
        print(f"  the as-written book A contains {int((A[A.how=='stop'].groupby(['day','res']).size()>1).sum())} "
              f"such clusters, by construction.")
    else:
        print("  none")
