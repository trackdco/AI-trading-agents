#!/usr/bin/env python3
"""Funded-account PAYOUT-CYCLE Monte Carlo (Angus 24-Jul: model real withdrawals).

Lucid 50k funded reality (not a one-shot target):
  - EOD drawdown $2,000; line locks at start balance (50k) once +$2k banked; bust if
    balance <= line intraday.
  - Max payout = $2,000 cash per withdrawal. Withdrawing needs balance >= a trigger AND
    >= 5 winning days since the last payout. Withdrawal REDUCES balance (and thus available
    DD), which mechanically de-risks the dollar-risk sizer.
  - Up to 5 funded accounts per Lucid login (copy-traded, identical book).

Two withdrawal strategies (Angus):
  HARVEST-MIN : withdraw $2k as soon as balance >= $4k  -> balance back to $2k (min buffer)
  BUILD-6     : build to $6k first, then withdraw $2k    -> balance back to $4k (fat buffer,
                sizer runs a higher base, next payout comes faster)
  BUILD-8     : build to $8k, withdraw $2k -> $6k        (even fatter, for comparison)

Sizing: conviction dollar-risk, base $200 (1.0 tier), +$75 per $1k available DD past $3k,
40-micro clamp. The real KPI is ANNUAL CASH WITHDRAWN per account, then x5 accounts.

    python -m scripts.mc_payout_cycles
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DD = 2000.0
INC = 75.0            # +$ per $1k available DD past $3k (Angus sweet spot)
BASE0 = 200.0
PAYOUT = 2000.0       # max payout per withdrawal
MIN_WIN_DAYS = 5      # winning days required between payouts
MIN_WIN_PL = 150.0    # a "winning day" must clear >= +$150 (Lucid consistency rule)
NSIM = 20000
NDAYS = 252
SEED = 20260724

ny = pd.read_parquet("output/canon_book.parquet")
lo = pd.read_parquet("output/london_canon_book.parquet")
def prep(d):
    t = d[d["size"] > 0].copy()
    return pd.DataFrame({"day": t["day"].astype(str), "fill": pd.to_datetime(t["fill"], utc=True),
                         "conv": t["size"].round(4), "risk": t["risk"].astype(float),
                         "Rm": (t["dollars"] / (t["risk"] * 20.0)).astype(float)})
B = pd.concat([prep(ny), prep(lo)], ignore_index=True).sort_values("fill")
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in B.groupby("day")]
ND = len(DAYS)


def base_dollar(ad):
    return BASE0 + INC * max(0, int((ad - 3000) // 1000)) if ad > 3000 else BASE0

def micros(conv, risk, ad):
    return min(40, int(round(min(2.0, conv) * base_dollar(ad) / (risk * 2.0))))


def sim_account(rng, trigger):
    """One funded account over NDAYS. Returns (cash_withdrawn, n_payouts, day_first_payout, busted)."""
    bal, line = 0.0, -DD
    withdrawn = 0.0
    payouts = 0
    win_days = 0
    first = 0
    for d in range(1, NDAYS + 1):
        day = DAYS[rng.integers(ND)]
        avail = bal - line             # fixed at day open
        dpl = 0.0
        for conv, risk, Rm in day:
            dpl += micros(conv, risk, avail) * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:      # intraday bust
                return withdrawn, payouts, first, True
        bal += dpl
        if dpl >= MIN_WIN_PL:          # counts toward the payout gate only if >= +$150
            win_days += 1
        line = min(0.0, max(line, bal - DD))         # EOD line update, locks at 0
        # end-of-day withdrawal
        if bal >= trigger and win_days >= MIN_WIN_DAYS:
            bal -= PAYOUT
            withdrawn += PAYOUT
            payouts += 1
            win_days = 0
            if first == 0:
                first = d
    return withdrawn, payouts, first, False


def run(label, trigger):
    rng = np.random.default_rng(SEED)
    cash = np.empty(NSIM); pays = np.empty(NSIM); firsts = []; busts = 0
    for i in range(NSIM):
        w, p, f, b = sim_account(rng, trigger)
        cash[i] = w; pays[i] = p; busts += b
        if f: firsts.append(f)
    fr = np.array(firsts)
    print(f"  {label:11s} (trigger ${trigger:,.0f}): "
          f"cash/acct med ${np.median(cash):,.0f} (p25 ${np.percentile(cash,25):,.0f} / "
          f"p75 ${np.percentile(cash,75):,.0f})  payouts med {np.median(pays):.0f}  "
          f"1st payout ~{np.median(fr):.0f}d  bust {busts/NSIM*100:.2f}%")
    print(f"  {'':11s}  x5 accounts: median ${np.median(cash)*5:,.0f}/yr cash withdrawn "
          f"(p25 ${np.percentile(cash,25)*5:,.0f})")
    return np.median(cash)


if __name__ == "__main__":
    print(f"Lucid 50k funded, payout cycles, {NSIM} sims x {NDAYS} days, dollar-risk +${INC:.0f}/$1k\n")
    print(f"Max payout ${PAYOUT:,.0f}/withdrawal, {MIN_WIN_DAYS} winning days between payouts:\n")
    m1 = run("HARVEST-MIN", 4000)
    m2 = run("BUILD-6", 6000)
    m3 = run("BUILD-8", 8000)
    print(f"\n  BUILD-6 vs HARVEST-MIN: {(m2/m1-1)*100:+.0f}% annual cash/acct")
    print(f"  BUILD-8 vs HARVEST-MIN: {(m3/m1-1)*100:+.0f}% annual cash/acct")
