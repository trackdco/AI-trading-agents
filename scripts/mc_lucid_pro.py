#!/usr/bin/env python3
"""Lucid STANDARD vs PRO (50k) — payout-cycle Monte Carlo under Build-6 (Angus 24-Jul).

Both: 50k, EOD $2k DD (line locks at start once +$2k banked), dollar-risk +$75/$1k,
Build-6 withdrawal (build to $6k, withdraw, keep the cushion). 5 accounts/login.

STANDARD payout gate:
  - $2,000 flat per withdrawal
  - >= 5 positive days of >= +$150 since last payout
  - no daily loss limit (beyond our own spine)

PRO payout gate:
  - $2,000 first withdrawal, $2,500 every one after
  - >= 3 positive days since last payout
  - 40% consistency: the biggest single day in the window must be <= 40% of window net
    profit (a big day BLOCKS the payout until later days dilute it)
  - hard $1,200 DAILY LOSS LIMIT (modeled as lockout: stop trading that day; also reported
    as a would-fail count for the strict interpretation). Our spine's -$800 daily halt sits
    below it, so with the spine the limit is never reached — these are naked numbers.

    python -m scripts.mc_lucid_pro
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DD = 2000.0
INC = 75.0
BASE0 = 200.0
TRIGGER = 6000.0        # Build-6
NSIM = 20000
NDAYS = 252
SEED = 20260724
PRO_DAILY_LIMIT = 1200.0

ny = pd.read_parquet("output/canon_book.parquet")
lo = pd.read_parquet("output/london_canon_book.parquet")
def prep(d):
    t = d[d["size"] > 0].copy()
    return pd.DataFrame({"day": t["day"].astype(str),
                         "conv": t["size"].round(4), "risk": t["risk"].astype(float),
                         "Rm": (t["dollars"] / (t["risk"] * 20.0)).astype(float)})
B = pd.concat([prep(ny), prep(lo)], ignore_index=True)
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in pd.concat([prep(ny), prep(lo)]).groupby("day")]
# rebuild by chronological day using fill order preserved above
B2 = pd.concat([prep(ny).assign(f=pd.to_datetime(ny[ny['size']>0]['fill'].values, utc=True)),
                prep(lo).assign(f=pd.to_datetime(lo[lo['size']>0]['fill'].values, utc=True))],
               ignore_index=True).sort_values("f")
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in B2.groupby("day")]
ND = len(DAYS)


def base_dollar(ad):
    return BASE0 + INC * max(0, int((ad - 3000) // 1000)) if ad > 3000 else BASE0

def micros(conv, risk, ad):
    return min(40, int(round(min(2.0, conv) * base_dollar(ad) / (risk * 2.0))))


def run_day(rng, bal, line, daily_limit=None):
    """Simulate one day. Returns (day_pl, busted). Applies intraday bust + optional daily lockout."""
    day = DAYS[rng.integers(ND)]
    avail = bal - line
    dpl = 0.0
    for conv, risk, Rm in day:
        pl = micros(conv, risk, avail) * (Rm * risk * 20.0) / 10.0
        dpl += pl
        if bal + dpl <= line:
            return dpl, True
        if daily_limit is not None and dpl <= -daily_limit:
            return dpl, False        # daily lockout: stop trading, day closes here
    return dpl, False


def sim_standard(rng):
    bal, line, wd, pays, wdays, first = 0.0, -DD, 0.0, 0, 0, 0
    for d in range(1, NDAYS + 1):
        dpl, bust = run_day(rng, bal, line)
        if bust:
            return wd, pays, first, True
        bal += dpl
        if dpl >= 150.0:
            wdays += 1
        line = min(0.0, max(line, bal - DD))
        if bal >= TRIGGER and wdays >= 5:
            bal -= 2000.0; wd += 2000.0; pays += 1; wdays = 0
            if first == 0: first = d
    return wd, pays, first, False


def sim_pro(rng):
    bal, line, wd, pays, first = 0.0, -DD, 0.0, 0, 0
    window = []          # daily P&Ls since last payout (for 3-day + 40% rule)
    limit_breaches = 0
    for d in range(1, NDAYS + 1):
        dpl, bust = run_day(rng, bal, line, daily_limit=PRO_DAILY_LIMIT)
        if bust:
            return wd, pays, first, True, limit_breaches
        if dpl <= -PRO_DAILY_LIMIT:
            limit_breaches += 1
        bal += dpl
        window.append(dpl)
        line = min(0.0, max(line, bal - DD))
        pos_days = sum(1 for x in window if x > 0)
        net = sum(window)
        maxday = max(window) if window else 0.0
        ok_consistency = (net <= 0) or (maxday <= 0.40 * net)
        if bal >= TRIGGER and pos_days >= 3 and ok_consistency:
            amt = 2000.0 if pays == 0 else 2500.0
            bal -= amt; wd += amt; pays += 1; window = []
            if first == 0: first = d
    return wd, pays, first, False, limit_breaches


def summarize(name, results, extra=None):
    cash = np.array([r[0] for r in results])
    pays = np.array([r[1] for r in results])
    firsts = np.array([r[2] for r in results if r[2]])
    busts = sum(r[3] for r in results)
    print(f"  {name:9s}: cash/acct med ${np.median(cash):,.0f} "
          f"(p25 ${np.percentile(cash,25):,.0f} / p75 ${np.percentile(cash,75):,.0f})  "
          f"payouts med {np.median(pays):.0f}  1st ~{np.median(firsts):.0f}d  bust {busts/len(results)*100:.2f}%")
    print(f"  {'':9s}  x5: median ${np.median(cash)*5:,.0f}/yr  (p25 ${np.percentile(cash,25)*5:,.0f})")
    if extra:
        print(f"  {'':9s}  {extra}")
    return np.median(cash)


if __name__ == "__main__":
    print(f"Lucid 50k STANDARD vs PRO, Build-6, {NSIM} sims x {NDAYS}d, dollar-risk +${INC:.0f}/$1k\n")
    rng = np.random.default_rng(SEED)
    std = [sim_standard(rng) for _ in range(NSIM)]
    rng = np.random.default_rng(SEED)
    pro = [sim_pro(rng) for _ in range(NSIM)]
    ms = summarize("STANDARD", std)
    breach = np.mean([r[4] for r in pro])
    mp = summarize("PRO", [r[:4] for r in pro],
                   extra=f"$1,200 daily-limit lockouts: {breach:.2f}/acct/yr (naked; spine's -$800 halt prevents entirely)")
    print(f"\n  PRO vs STANDARD: {(mp/ms-1)*100:+.0f}% annual cash/acct")
