#!/usr/bin/env python3
"""PORTFOLIO LAB — B2-redux item 4: N accounts on ONE signal stream.

The per-account bust rate is not the portfolio risk. N accounts trading
identical signals at the same size are PERFECTLY CORRELATED: they are not
N independent draws, they are one strategy's bad month replicated N times
-- N x the P&L and N x the drawdown at the same moment.

Model: one bootstrapped market year (the SAME day sequence for every
account, calendar-aligned). Account i begins trading on calendar day
offset_i. Simultaneous = all offsets 0. Staggered = offsets spread across
the first `spread` days, which is the trader's hypothesis: since breach
risk concentrates in the pre-lock phase, staggering should de-synchronise
the vulnerable windows.

Reports, per configuration:
  P(>=50% / 100% of accounts take a FUNDED breach in the same month)
  monthly portfolio cashflow: mean, sd, CV, P(a month pays zero)
  annual portfolio net, and its 5th percentile (the bad-year tail)

    python -m scripts.htf_ma_portfolio_lab [--draws N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ma_account_lab import (EVAL_COST, YEAR,      # noqa: E402
                                        load_days, run_account)

SEED, DRAWS = 20260807, 600
MONTH = 21                      # trading days per month bucket


def portfolio(day_r, seqs, n_acct: int, policy: dict, stagger: int,
              payout_cap, payout_at) -> dict:
    """EQUAL EXPOSURE (fix, 2026-08-07): every account trades exactly YEAR
    days. Staggering SHIFTS the window along a longer shared calendar; it
    does not truncate it. The earlier version gave staggered accounts up
    to 24% fewer trading days, so their whole net penalty was an exposure
    artifact rather than a cost of staggering."""
    offs = (np.linspace(0, stagger, n_acct).astype(int) if stagger
            else np.zeros(n_acct, dtype=int))
    cal = YEAR + stagger                      # shared calendar length
    n_month = int(np.ceil(cal / MONTH))
    p_half, p_all, zero_m = [], [], []
    m_flow_all, ann_net = [], []
    for seq in seqs:
        # distinct ACCOUNTS dying per month (not breach events)
        month_dead = [set() for _ in range(n_month)]
        month_flow = np.zeros(n_month)
        net = 0.0
        for i in range(n_acct):
            r = run_account(day_r, seq, policy, start=int(offs[i]),
                            payout_cap=payout_cap, payout_at=payout_at,
                            n_days=YEAR)
            net += sum(w for _, w in r["wd"]) - r["fees"]
            for d in r["funded_deaths"]:   # account DEATHS, not eval resets
                month_dead[min(d // MONTH, n_month - 1)].add(i)
            for d, w in r["wd"]:
                month_flow[min(d // MONTH, n_month - 1)] += w
        counts = np.array([len(s) for s in month_dead])
        p_half.append(float((counts >= 0.5 * n_acct).any()))
        p_all.append(float((counts >= n_acct).any()))
        zero_m.append(float((month_flow == 0).mean()))
        m_flow_all.append(month_flow)
        ann_net.append(net)
    mf = np.concatenate(m_flow_all)
    return {"p_half": float(np.mean(p_half)), "p_all": float(np.mean(p_all)),
            "zero_m": float(np.mean(zero_m)),
            "m_mean": float(mf.mean()), "m_sd": float(mf.std()),
            "cv": float(mf.std() / mf.mean()) if mf.mean() else np.nan,
            "net": float(np.mean(ann_net)),
            "net_p05": float(np.percentile(ann_net, 5)),
            "net_med": float(np.median(ann_net))}


def show(tag: str, s: dict) -> None:
    print(f"{tag:34s} net ${s['net']:9,.0f} (med ${s['net_med']:9,.0f}, "
          f"p05 ${s['net_p05']:9,.0f}) | month ${s['m_mean']:7,.0f} "
          f"+-{s['m_sd']:7,.0f} CV {s['cv']:4.2f} | zero-mo "
          f"{s['zero_m']*100:4.1f}% | >=50% breach/mo {s['p_half']*100:5.1f}% "
          f"| all {s['p_all']*100:4.1f}%")


def main() -> None:
    draws = DRAWS
    if "--draws" in sys.argv:
        draws = int(sys.argv[sys.argv.index("--draws") + 1])
    rng = np.random.default_rng(SEED)
    base = load_days()
    hair20 = load_days(0.2 * 0.257)
    MAXSTAG = 60
    # the shared calendar must be long enough that a staggered account
    # still gets its full YEAR of trading days (equal-exposure fix)
    seqs = [rng.integers(0, len(base), YEAR + MAXSTAG) for _ in range(draws)]
    POL = {"s_pre": 150., "s_post": 300.}
    CUSH = {"s_pre": 150., "mode": "cushion", "k": 0.05,
            "s_min": 75., "s_max": 300.}
    print(f"wd@$6k, {draws} bootstrapped years. N=5 is the VERIFIED "
          f"household funded-account cap; N=10/33 shown as NON-COMPLIANT "
          f"reference only.\n")

    for cap, cap_tag in ((5, "payouts capped(5) — THE VERIFIED RULE"),
                         (None, "payouts uncapped — counterfactual")):
        print(f"== {cap_tag} ==")
        for n in (1, 5, 10, 33):
            for stag, stag_tag in ((0, "simultaneous"), (60, "staggered60")):
                if n == 1 and stag:
                    continue
                s = portfolio(base, seqs, n, POL, stag, cap, 6000.)
                show(f"N={n:2d} {stag_tag} 150->300", s)
        print()

    print("== N=5 (compliant fleet): flat vs cushion sizing ==")
    for cap, ctag in ((5, "capped"), (None, "uncapped")):
        for pol, ptag in ((POL, "150->300"), (CUSH, "cushion k=.05")):
            for stag, stag_tag in ((0, "simult"), (60, "stagger60")):
                s = portfolio(base, seqs, 5, pol, stag, cap, 6000.)
                show(f"N=5 {ptag} {stag_tag} [{ctag}]", s)
    print()

    print("== correlation check: N=33 INDEPENDENT streams (what the "
          "per-account rate would imply) vs shared ==")
    s_shared = portfolio(base, seqs, 33, POL, 0, None, 6000.)
    # independent: give each account its own sequence within a draw
    p_half, mflow, ann = [], [], []
    n_month = int(np.ceil(YEAR / MONTH))
    for k in range(draws):
        month_dead = [set() for _ in range(n_month)]
        month_flow = np.zeros(n_month)
        net = 0.0
        for i in range(33):
            seq = rng.integers(0, len(base), YEAR)
            r = run_account(base, seq, POL, payout_cap=None,
                            payout_at=6000., n_days=YEAR)
            net += sum(w for _, w in r["wd"]) - r["fees"]
            for d in r["funded_deaths"]:
                month_dead[min(d // MONTH, n_month - 1)].add(i)
            for d, w in r["wd"]:
                month_flow[min(d // MONTH, n_month - 1)] += w
        p_half.append(float((np.array([len(x) for x in month_dead])
                             >= 16.5).any()))
        mflow.append(month_flow)
        ann.append(net)
    mf = np.concatenate(mflow)
    show("N=33 shared stream", s_shared)
    print(f"{'N=33 independent streams':34s} net ${np.mean(ann):9,.0f} "
          f"(med ${np.median(ann):9,.0f}, p05 ${np.percentile(ann,5):9,.0f}) "
          f"| month ${mf.mean():7,.0f} +-{mf.std():7,.0f} "
          f"CV {mf.std()/mf.mean():4.2f} | zero-mo "
          f"{(mf==0).mean()*100:4.1f}% | >=50% breach/mo "
          f"{np.mean(p_half)*100:5.1f}%")

    print("\n== N=33 shared, EV haircut -20% (uncapped, 150->300 wd@$6k) ==")
    show("N=33 simultaneous [-20%]",
         portfolio(hair20, seqs, 33, POL, 0, None, 6000.))
    show("N=33 staggered60 [-20%]",
         portfolio(hair20, seqs, 33, POL, 60, None, 6000.))


if __name__ == "__main__":
    main()
