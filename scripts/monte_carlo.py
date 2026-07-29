#!/usr/bin/env python3
"""MONTE CARLO — funded eval (Angus 21 Jul). Conservative micro sizing on the conviction
tiers: HIGH = 6 MNQ, MID/LOW = 3 MNQ. Eval: +$3,000 target, $2,000 trailing drawdown that
LOCKS at the starting balance once peak profit reaches +$2,000 (Apex-standard).

Resamples our actual trade pool two ways -- trade-by-trade (iid) and day-blocks (keeps
losing days clustered, more realistic for DD). Reports pass / bust / incomplete and how long
it takes. NQ->MNQ: micro $ = 1-NQ $ * micros / 10 (NQ=$20/pt, MNQ=$2/pt).

    python -m scripts.monte_carlo
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
TARGET = 3000.0
DD = 2000.0
MICROS = {"HIGH": 6, "MID": 3, "LOW": 3}
SIMS = 50000
SEED = 12345


def sim_path(pnls):
    """Walk a P&L sequence; return ('pass'|'bust'|'incomplete', steps). Trailing DD locks at
    breakeven (start) once peak >= DD."""
    eq = 0.0; peak = 0.0
    for i, p in enumerate(pnls, 1):
        eq += p
        peak = max(peak, eq)
        floor = min(peak - DD, 0.0)          # locks at 0 (start) once peak >= DD
        if eq >= TARGET:
            return "pass", i
        if eq <= floor:
            return "bust", i
    return "incomplete", len(pnls)


def main():
    W = pd.read_csv("output/conviction_trades.csv")
    W["micros"] = W.tier.map(MICROS)
    W["mpnl"] = W.dollars * W.micros / 10.0        # micro dollars per trade
    pool = W.mpnl.to_numpy()
    # daily blocks in chronological fill order
    W["fillkey"] = W.date + " " + W.fill_t
    days = [g.sort_values("fillkey").mpnl.to_numpy() for _, g in W.groupby("date")]

    print("### MONTE CARLO — funded eval ($3k target / $2k trailing, locks at breakeven) ###\n")
    print(f"sizing: HIGH 6 micros, MID/LOW 3 micros  ({W.tier.value_counts().to_dict()})")
    print(f"pool: {len(W)} trades   micro $/trade: mean ${pool.mean():+.0f}  "
          f"win ${W[W.win].mpnl.mean():+.0f}  loss ${W[~W.win].mpnl.mean():+.0f}   "
          f"expectancy ${pool.mean():+.0f}/trade")
    print(f"trading days: {len(days)}   avg trades/day {len(W)/len(days):.1f}\n")

    rng = np.random.default_rng(SEED)

    # actual chronological sequence, once (deterministic)
    act = W.sort_values("fillkey").mpnl.to_numpy()
    print(f"actual 2026 sequence (as it happened): {sim_path(act)[0].upper()}  "
          f"(final ${act.sum():+,.0f} over {len(act)} trades)\n")

    def run(mode, cap_units):
        res = {"pass": 0, "bust": 0, "incomplete": 0}; steps = []
        for _ in range(SIMS):
            if mode == "trade":
                seq = pool[rng.integers(0, len(pool), cap_units)]
            else:
                seq = np.concatenate([days[i] for i in rng.integers(0, len(days), cap_units)])
            out, n = sim_path(seq)
            res[out] += 1
            if out == "pass":
                steps.append(n)
        p = {k: v / SIMS * 100 for k, v in res.items()}
        med = int(np.median(steps)) if steps else 0
        return p, med

    print(f"{SIMS:,} sims each:\n")
    for mode, cap, unit in (("trade", 200, "trades"), ("day", 120, "days")):
        p, med = run(mode, cap)
        print(f"  {mode+'-level bootstrap':22s}  PASS {p['pass']:4.1f}%   BUST {p['bust']:4.1f}%   "
              f"incomplete {p['incomplete']:4.1f}%   median {unit} to pass: {med}")

    # sensitivity: sizing variants + DD size, trade-level
    print("\n  sensitivity (trade-level, pass%):")
    def pass_rate(micros, dd, target, cap=200):
        mp = (W.dollars * W.tier.map(micros) / 10.0).to_numpy()
        c = 0
        for _ in range(SIMS):
            seq = mp[rng.integers(0, len(mp), cap)]
            eq = 0.0; peak = 0.0; done = False
            for x in seq:
                eq += x; peak = max(peak, eq); fl = min(peak - dd, 0.0)
                if eq >= target: c += 1; done = True; break
                if eq <= fl: done = True; break
            # incomplete counts as not-pass
        return c / SIMS * 100
    for label, mic in (("HIGH6 / MID3 / LOW3 (this)", {"HIGH":6,"MID":3,"LOW":3}),
                       ("flat 3 micros", {"HIGH":3,"MID":3,"LOW":3}),
                       ("HIGH4 / MID2 / LOW2 (lighter)", {"HIGH":4,"MID":2,"LOW":2}),
                       ("HIGH8 / MID4 / LOW4 (heavier)", {"HIGH":8,"MID":4,"LOW":4})):
        print(f"    {label:32s}  pass {pass_rate(mic, DD, TARGET):4.1f}%")


if __name__ == "__main__":
    main()
