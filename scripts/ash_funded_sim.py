#!/usr/bin/env python3
"""Mock $50k funded-account run of ash-unicorn-sb (AM1), with split risk.

    A-arm  F2_retrace_ratio < 1.0  (the 73.3% WR filtered set)  -> risk 1.5x = $375
    B-arm  everything else, incl. the 8 trades with no flow data -> risk $250

Sized in MICROS (MNQ, $2/pt). NQ is unusable here: $250 on the median 25.5pt stop is 0.49
NQ contracts. Every trade sizes to >= 1 MNQ, so no setup is dropped for sizing.

*** THIS IS NOT A VALIDATION. *** The A-arm is a filter found IN-SAMPLE on 15 trades and is
currently under pre-registered forward test (ash-unicorn-sb-forward-protocol.md). Sizing up
1.5x on it is a bet that the filter is real. This script therefore ALSO runs the null:
arm labels reshuffled 20,000 times, which is what the account does if F2 carries no
information. Read that section before the headline.

    python -m scripts.ash_funded_sim
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STRAT = ROOT / "research/ash10hazard/strategies"

# ---------------------------------------------------------------- assumptions, all stated
BALANCE = 50_000.0
RISK_B = 250.0            # normal setup
RISK_MULT = 1.5           # A-arm multiplier -> $375
PT = 2.0                  # MNQ $/point
TICK = 0.25               # MNQ tick, points
# cost: the desk's NQ convention ($25/round turn = $5 commission + 1 tick slip each way)
# scaled by 10 for the micro. Per CONTRACT, per round turn.
COST_PER_CONTRACT = 2.50

# Prop-firm rules vary by firm and none of these are quoted from a contract. Two generic
# $50k profiles are run so the answer does not hinge on one firm's numbers.
PROFILES = {
    "trailing $2,000 + $1,000 daily": dict(trail=2_000.0, daily=1_000.0, target=3_000.0),
    "trailing $2,500, no daily cap": dict(trail=2_500.0, daily=None, target=3_000.0),
}


def load() -> pd.DataFrame:
    raw = pd.read_csv(STRAT / "ash-unicorn-sb-raw-trades.csv")
    fl = pd.read_csv(STRAT / "ash-unicorn-sb-orderflow-trades.csv")
    d = raw.merge(fl[["date", "F1_disp_delta", "F2_retrace_ratio"]], on="date", how="left")
    d = d.sort_values("date").reset_index(drop=True)
    # A-arm requires flow data AND F2 < 1. NaN flow (pre-2025-06-01) is NOT high-conviction:
    # we could not have known at the time, so it sizes as normal.
    d["arm"] = np.where(d.F2_retrace_ratio < 1.0, "A", "B")
    return d


def size_trades(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["risk_budget"] = np.where(d.arm == "A", RISK_B * RISK_MULT, RISK_B)
    # floor so the budget is a CAP, never exceeded; every trade still gets >= 1 contract
    d["contracts"] = np.maximum(1, np.floor(d.risk_budget / (d.risk_pts * PT))).astype(int)
    d["risk_actual"] = d.contracts * d.risk_pts * PT
    d["cost"] = d.contracts * COST_PER_CONTRACT
    d["pnl"] = d.R * d.risk_actual - d.cost
    return d


def walk(d: pd.DataFrame, trail: float, daily: float | None, target: float) -> dict:
    """Equity walk with a trailing threshold that locks at the starting balance."""
    eq = BALANCE
    peak = BALANCE
    floor_ = BALANCE - trail
    blown = None
    hit_target_on = None
    curve, day_pnl = [], {}
    for r in d.itertuples():
        if blown:
            break
        pnl = r.pnl
        # daily cap: AM1 is one trade/day, so this binds only if a single trade breaches it
        capped = False
        if daily is not None and pnl < -daily:
            pnl, capped = -daily, True
        eq += pnl
        day_pnl[r.date] = day_pnl.get(r.date, 0.0) + pnl
        peak = max(peak, eq)
        # threshold trails the high-water mark, then locks once it reaches the start balance
        floor_ = max(floor_, min(peak - trail, BALANCE))
        curve.append(dict(date=r.date, arm=r.arm, contracts=r.contracts,
                          risk=r.risk_actual, R=r.R, pnl=pnl, equity=eq,
                          threshold=floor_, capped=capped))
        if eq <= floor_:
            blown = r.date
        if hit_target_on is None and eq - BALANCE >= target:
            hit_target_on = r.date
    c = pd.DataFrame(curve)
    best_day = max(day_pnl.values()) if day_pnl else 0.0
    profit = c.equity.iloc[-1] - BALANCE if len(c) else 0.0
    return dict(curve=c, blown=blown, target_on=hit_target_on, profit=profit,
                best_day=best_day, trades_taken=len(c),
                min_buffer=float((c.equity - c.threshold).min()) if len(c) else np.nan,
                consistency=(best_day / profit if profit > 0 else np.nan))


def report(tag: str, res: dict, target: float) -> None:
    c = res["curve"]
    print(f"\n--- {tag} ---")
    if res["blown"]:
        print(f"  ACCOUNT BLOWN on {res['blown']} after {res['trades_taken']} trades")
    print(f"  trades taken        {res['trades_taken']}")
    print(f"  net P&L             ${res['profit']:+,.0f}   "
          f"(final equity ${BALANCE + res['profit']:,.0f})")
    print(f"  closest to the line  ${res['min_buffer']:,.0f} of buffer at the worst point")
    print(f"  best single day     ${res['best_day']:+,.0f}", end="")
    if res["consistency"] == res["consistency"]:
        flag = "  <- FAILS a 50% consistency rule" if res["consistency"] > 0.5 else ""
        print(f"  = {100*res['consistency']:.0f}% of total profit{flag}")
    else:
        print()
    print(f"  ${target:,.0f} target      "
          f"{'reached ' + res['target_on'] if res['target_on'] else 'NOT reached'}")


def main() -> None:
    d = size_trades(load())
    A, B = d[d.arm == "A"], d[d.arm == "B"]
    print("MOCK $50k FUNDED ACCOUNT — ash-unicorn-sb (AM1 09:45-10:15 ET), MNQ micros")
    print(f"span {d.date.min()} -> {d.date.max()}   {len(d)} setups over "
          f"{len(d.date.unique())} sessions\n")
    print(f"  A-arm (F2 < 1.0)  n={len(A):2d}  risk ${RISK_B*RISK_MULT:.0f}   "
          f"WR {100*(A.R>=2).mean():.1f}%   avg {A.R.mean():+.2f}R")
    print(f"  B-arm (all else)  n={len(B):2d}  risk ${RISK_B:.0f}   "
          f"WR {100*(B.R>=2).mean():.1f}%   avg {B.R.mean():+.2f}R")
    print(f"    of which no flow data (sized normal by necessity): "
          f"{int(B.F2_retrace_ratio.isna().sum())}")
    print(f"\nsizing: MNQ ${PT:.0f}/pt, contracts = floor(budget / (stop_pts x $2)), min 1")
    print(f"  contracts {d.contracts.min()}-{d.contracts.max()} (median "
          f"{int(d.contracts.median())})   actual risk ${d.risk_actual.min():.0f}-"
          f"${d.risk_actual.max():.0f}   cost ${COST_PER_CONTRACT:.2f}/contract/round turn")

    for name, p in PROFILES.items():
        print("\n" + "=" * 74)
        print(f"PROFILE: {name}")
        print("=" * 74)
        report("SPLIT RISK ($375 A / $250 B) — as asked", walk(d, **p), p["target"])
        flat = size_trades(load().assign(arm="B"))
        report("FLAT $250 everywhere — the comparator", walk(flat, **p), p["target"])
        # the obvious follow-up: the B-arm is a losing arm. What if you only take A?
        a_only = size_trades(load().pipe(lambda x: x[x.arm == "A"]).reset_index(drop=True))
        report(f"A-ARM ONLY ($375, skip the other {len(d)-len(a_only)}) — for reference",
               walk(a_only, **p),
               p["target"])

    # ------------------------------------------------------------------ the null
    print("\n" + "=" * 74)
    print("IF THE FILTER IS NOISE — arm labels reshuffled 20,000 times")
    print("=" * 74)
    p = PROFILES["trailing $2,000 + $1,000 daily"]
    real = walk(d, **p)
    base = load()
    n_a = int((base.arm == "A").sum())
    # Precompute each trade's P&L under BOTH sizings once, then the null only permutes
    # which sizing each trade gets. Identical arithmetic to walk(), just without rebuilding
    # a DataFrame 20,000 times.
    pnl = {}
    for arm in ("A", "B"):
        s = size_trades(base.assign(arm=arm))
        pnl[arm] = s.pnl.to_numpy(float)
    profits, blows = np.empty(20_000), 0
    rng = np.random.default_rng(11)
    for i in range(20_000):
        pick = np.zeros(len(base), bool)
        pick[rng.permutation(len(base))[:n_a]] = True
        v = np.where(pick, pnl["A"], pnl["B"])
        v = np.maximum(v, -p["daily"]) if p["daily"] is not None else v
        eq, peak, fl_ = BALANCE, BALANCE, BALANCE - p["trail"]
        for x in v:
            eq += x
            peak = max(peak, eq)
            fl_ = max(fl_, min(peak - p["trail"], BALANCE))
            if eq <= fl_:
                blows += 1
                break
        profits[i] = eq - BALANCE
    print(f"  actual (F2-labelled)      ${real['profit']:+,.0f}")
    print(f"  random labels, median     ${np.median(profits):+,.0f}")
    print(f"  random labels, 5th-95th   ${np.percentile(profits,5):+,.0f} to "
          f"${np.percentile(profits,95):+,.0f}")
    print(f"  P(random >= actual)       {(profits >= real['profit']).mean():.4f}")
    print(f"  blow-up rate, random      {100*blows/20_000:.1f}%")

    # --------------------------------------------- the risk question the null can't answer
    # The permutation above holds the observed outcomes fixed and only moves the labels. It
    # cannot say what a WORSE RUN OF THE SAME EDGE does to the account. Bootstrap does: resample
    # trades with replacement, so streaks form and break differently each run.
    print("\n" + "=" * 74)
    print(f"SAME EDGE, DIFFERENT LUCK — 20,000 bootstrap runs of {len(d)} trades")
    print("=" * 74)
    print(f"{'scenario':<34}{'P(blow up)':>12}{'P(hit $3k)':>12}{'median P&L':>14}"
          f"{'5th pct':>11}")
    for label, shuffle_arms in (("as observed (filter works)", False),
                                ("filter is NOISE (labels random)", True)):
        prof = np.empty(20_000)
        blow = tgt = 0
        for i in range(20_000):
            idx = rng.integers(0, len(base), len(base))
            if shuffle_arms:
                pick = np.zeros(len(base), bool)
                pick[rng.permutation(len(base))[:n_a]] = True
                v = np.where(pick, pnl["A"][idx], pnl["B"][idx])
            else:
                v = np.where((base.arm == "A").to_numpy()[idx],
                             pnl["A"][idx], pnl["B"][idx])
            eq, peak, fl_, hit = BALANCE, BALANCE, BALANCE - p["trail"], False
            for x in v:
                eq += x
                peak = max(peak, eq)
                fl_ = max(fl_, min(peak - p["trail"], BALANCE))
                if eq - BALANCE >= p["target"]:
                    hit = True
                if eq <= fl_:
                    blow += 1
                    break
            tgt += hit
            prof[i] = eq - BALANCE
        print(f"{label:<34}{100*blow/20_000:>11.1f}%{100*tgt/20_000:>11.1f}%"
              f"{np.median(prof):>+14,.0f}{np.percentile(prof,5):>+11,.0f}")

    # what actually constrains this account
    d2 = walk(d, **p)["curve"]
    streak = mx = 0
    for r in d2.R:
        streak = streak + 1 if r <= -1 else 0
        mx = max(mx, streak)
    print(f"\nlongest losing streak observed: {mx}   "
          f"largest single loss: ${-d2.pnl.min():,.0f}   "
          f"daily cap ${p['daily']:,.0f} was hit {int(d2.capped.sum())} times")
    print(f"trade frequency: {len(d)/16.3:.1f}/month over 16.3 months")

    out = STRAT / "ash-unicorn-sb-funded-sim.csv"
    walk(d, **p)["curve"].to_csv(out, index=False)
    print(f"\nequity curve -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
