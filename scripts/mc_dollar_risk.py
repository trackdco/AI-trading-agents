#!/usr/bin/env python3
"""EOD Monte-Carlo under CONVICTION-BASED DOLLAR-RISK sizing (Angus, 24-Jul redirect).

Sizing rule (replaces static micro-count):
  per-trade $ risk = base_dollar(available_dd) * tier_mult(conviction), capped by 40-micro clamp
    tier_mult = min(2.0, conviction)   # 0.25..1.0 linear; 1.5->1.5x; 2.25->2.0x (=$400 at floor)
    base_dollar = $200 at <=$3k available DD; +$75 per $1k of available DD past $3k
  contracts(MNQ,$2/pt) = round( risk_$ / (stop_pts * 2) ), hard-clamped to 40 micros
  => every trade of a given tier risks a CONSTANT dollar amount, stop-width-normalized.

Compared head-to-head with static base-5-floor micro sizing.
Lucid 50k, EOD drawdown (not trailing). Full cycle (eval 3k -> funded 4k max payout)
and 1-yr funded survival, naked and with Tier-1 spine halts.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DD = 2000.0            # 50k drawdown
SEED = 20260724
NSIM = 20000

# ---- build per-day trade sequences from both canon books ----
ny = pd.read_parquet("output/canon_book.parquet")
lo = pd.read_parquet("output/london_canon_book.parquet")
def prep(d):
    t = d[d["size"] > 0].copy()
    return pd.DataFrame({"day": t["day"].astype(str), "fill": pd.to_datetime(t["fill"], utc=True),
                         "conv": t["size"].round(4), "risk": t["risk"].astype(float),
                         "Rm": (t["dollars"] / (t["risk"] * 20.0)).astype(float)})
B = pd.concat([prep(ny), prep(lo)], ignore_index=True).sort_values("fill")
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in B.groupby("day")]
NDAY = len(DAYS)

FLOOR = {0.25: 3, 0.5: 5, 0.75: 6, 1.0: 7, 1.5: 8, 2.25: 11}

def base_dollar(ad):
    # +$75 to the 1.0-base per $1k of available DD past $3k (Angus 24-Jul: MC sweet spot)
    return 200.0 + 75.0 * max(0, int((ad - 3000) // 1000)) if ad > 3000 else 200.0

def micros_dollar_risk(conv, risk, ad):
    rb = base_dollar(ad) * min(2.0, conv)
    return min(40, int(round(rb / (risk * 2.0))))

def micros_static(conv, risk, ad):
    base = 7 + 3 * max(0, int((ad - 3000) // 1000)) if ad > 3000 else 7
    return min(40, int(round(FLOOR[conv] * base / 7.0)))


def sim_year(rng, sizer, spine, ndays=252):
    """One funded-year path. Returns (final_pnl, busted)."""
    bal = 0.0            # profit above 50k start
    line = -DD           # EOD line relative to start (start=0), locks at 0 in funded
    for _ in range(ndays):
        day = DAYS[rng.integers(NDAY)]
        day_start_bal = bal
        avail = bal - line          # available DD, fixed at day open
        day_pl = 0.0
        for conv, risk, Rm in day:
            if spine:
                if (bal - line) + day_pl <= 250:   # available-dd halt
                    break
                if day_pl <= -800:                 # daily-loss halt
                    break
            m = sizer(conv, risk, avail + day_pl if False else avail)
            pl = m * (Rm * risk * 20.0) / 10.0     # micro=$2/pt = dollars/10
            day_pl += pl
            if bal + day_pl <= line:               # intraday-fatal breach
                return bal + day_pl, True
        bal += day_pl
        # EOD line update (trails gains up by DD, locks at 0)
        line = min(0.0, max(line, bal - DD))
    return bal, False


def sim_cycle(rng, sizer, spine):
    """Eval (3k tgt, line locks at 2k bal) then funded (4k tgt, line locks at 0). days to payout."""
    # eval: 3k target, EOD line trails up by DD, locks at 2k balance (line cap +2000)
    bal, line, days = 0.0, -DD, 0
    while bal < 3000 and days < 400:
        days += 1
        day = DAYS[rng.integers(NDAY)]; avail = bal - line; dpl = 0.0
        for conv, risk, Rm in day:
            if spine and ((bal - line) + dpl <= 250 or dpl <= -800): break
            dpl += sizer(conv, risk, avail) * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line: return days, False
        bal += dpl
        line = min(2000.0, max(line, bal - DD))   # locks at +2000 balance
    if bal < 3000: return days, False
    # funded
    bal, line = 0.0, -DD
    while bal < 4000 and days < 800:
        days += 1
        day = DAYS[rng.integers(NDAY)]; avail = bal - line; dpl = 0.0
        for conv, risk, Rm in day:
            if spine and ((bal - line) + dpl <= 250 or dpl <= -800): break
            dpl += sizer(conv, risk, avail) * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line: return days, False
        bal += dpl
        line = min(0.0, max(line, bal - DD))
    return days, bal >= 4000


def run(label, sizer):
    rng = np.random.default_rng(SEED)
    for spine in (False, True):
        finals = np.empty(NSIM); busts = 0
        for i in range(NSIM):
            f, b = sim_year(rng, sizer, spine)
            finals[i] = f; busts += b
        tag = "+spine" if spine else "naked "
        print(f"  {label} {tag}: bust {busts/NSIM*100:5.2f}%   median ${np.median(finals):+,.0f}   "
              f"p10 ${np.percentile(finals,10):+,.0f}   p90 ${np.percentile(finals,90):+,.0f}")
    # full cycle (spine on)
    rng = np.random.default_rng(SEED + 1)
    days = np.empty(NSIM); ok = 0
    for i in range(NSIM):
        d, s = sim_cycle(rng, sizer, True); days[i] = d; ok += s
    print(f"  {label} CYCLE: eval->$4k payout {ok/NSIM*100:5.1f}%   median {np.median(days[days>0]):.0f} days")


if __name__ == "__main__":
    print(f"funded-year survival + full cycle, {NSIM} sims each, EOD drawdown, Lucid 50k\n")
    print("DOLLAR-RISK sizing (1.0=$200, 1.5=$300, 2.25=$400 at floor; +$75/$1k DD past $3k):")
    run("dollar-risk", micros_dollar_risk)
    print("\nSTATIC micro sizing (base-5-floor, +3 micros/$1k DD past $3k):")
    run("static-micro", micros_static)
