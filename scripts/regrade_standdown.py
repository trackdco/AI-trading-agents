#!/usr/bin/env python3
"""FREE re-grade: swap the stand-down gate on EXISTING v0.7 agent verdicts (no rerun).

The agent's raw book choice + raw risk_off request are stored per day in the ledgers.
This applies different stand-down gates on top of those fixed book choices and re-grades
per year -- testing "does the inventory gate beat the health gate in the live stack"
without spending a single new agent call.

Gates tested:
  baseline_v07   flat iff agent asked risk_off AND health<=0   (current shipped logic)
  inventory      flat iff walk-forward inventory gate says flat (REPLACES agent stand-down)
  inv_or_agent   flat iff inventory says flat OR agent asked risk_off
  inv_or_health  flat iff inventory says flat OR health<0

    python -m scripts.regrade_standdown
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BOOKS = "output/allyears_daily_books_r1r2.csv"


def champ_series():
    """Chronological champion (imbalance-switch) floored P&L for the walk-forward gate."""
    b = pd.read_csv(BOOKS)
    v = pd.read_csv("output/regime_vector.csv")
    d = b.merge(v, on="day", how="left").sort_values("day").reset_index(drop=True)
    d["champ_pl"] = np.where(d.imbal_share_20 >= 0.5, d.E4, d.E3)
    return d


def wf_inventory_flat(d, min_n=20, fb=60):
    """day -> True if pre-open inventory bucket's trailing champ expectancy < 0. Walk-forward:
    tercile edges + expectancy from prior days only."""
    vals = d.inventory_pts.values
    cpl = d.champ_pl.values
    flat = {}
    for i in range(len(d)):
        if pd.isna(vals[i]) or i < 40:
            prior = cpl[max(0, i - fb):i]
        else:
            past = vals[:i]
            past = past[~np.isnan(past)]
            q1, q2 = np.nanquantile(past, [1/3, 2/3])
            x = vals[i]
            mask = past <= q1 if x <= q1 else ((past > q1) & (past <= q2) if x <= q2 else past > q2)
            pb = cpl[:i][~np.isnan(vals[:i])][mask]
            prior = pb if len(pb) >= min_n else cpl[max(0, i - fb):i]
        prior = prior[~np.isnan(prior)]
        flat[d.day.iloc[i]] = bool(len(prior) >= 10 and prior.mean() < 0)
    return flat


def health_neg(d, window=20):
    h = pd.Series(d.champ_pl.values).rolling(window).sum().shift(1)
    return {d.day.iloc[i]: bool(h.iloc[i] < 0) if pd.notna(h.iloc[i]) else False for i in range(len(d))}


def champ_pick(day, vec):
    r = vec[vec.day == day]
    if r.empty or pd.isna(r.iloc[0].imbal_share_20):
        return "ROTATION"
    return "MOMENTUM" if r.iloc[0].imbal_share_20 >= 0.5 else "ROTATION"


def regrade(ledger_path, label, inv_flat, hneg, vec):
    L = pd.read_csv(ledger_path)
    L["y"] = L.day.str[:4]
    gates = {}
    for _, r in L.iterrows():
        day = r.day
        agent_riskoff = (r.stance_asked == "risk_off")
        inv = inv_flat.get(day, False)
        hn = hneg.get(day, False)
        # book resolution on TRADE days = agent's raw book (CHAMPION -> imbalance switch)
        book = champ_pick(day, vec) if r.book == "CHAMPION" else r.book
        book_pl = r.e3 if book == "ROTATION" else r.e4
        for g, is_flat in [
            ("baseline_v07", agent_riskoff and hn),
            ("inventory", inv),
            ("inv_or_agent", inv or agent_riskoff),
            ("inv_or_health", inv or hn),
            # CONDITIONAL: inventory gate active ONLY in bad regimes (health<0), keep the
            # agent's own health-gated stand-down everywhere (protects green years).
            ("cond_add", (agent_riskoff and hn) or (hn and inv)),
            # inventory in bad regime, agent's risk_off in good regime
            ("cond_replace", (hn and inv) or (not hn and agent_riskoff)),
        ]:
            gates.setdefault(g, []).append(0.0 if is_flat else book_pl)
    print(f"\n=== {label} (n={len(L)}, ceiling ${L.orc.sum():,.0f}) ===")
    out = {}
    for g, pls in gates.items():
        L[g] = pls
        per = L.groupby("y")[g].sum()
        flatrate = (np.array(pls) == 0).mean()
        line = "  ".join(f"{y}:${per[y]:+,.0f}" for y in sorted(per.index))
        cap = sum(pls) / L.orc.sum() * 100
        print(f"  {g:16s} ALL ${sum(pls):+8,.0f} ({cap:+.0f}%) flat {flatrate*100:.0f}%  | {line}")
        out[g] = sum(pls)
    return out


def main():
    d = champ_series()
    inv_flat = wf_inventory_flat(d)
    hneg = health_neg(d)
    vec = pd.read_csv("output/regime_vector.csv")[["day", "imbal_share_20"]]
    print(f"inventory gate flats {np.mean(list(inv_flat.values()))*100:.0f}% of all days")
    regrade("output/v07/walk_v07/ledger.csv", "FRESH-EYES 2023-2026 (agent books, swapped gate)", inv_flat, hneg, vec)
    regrade("output/v07/chained2026/ledger.csv", "CHAINED 2026 (agent books, swapped gate)", inv_flat, hneg, vec)


if __name__ == "__main__":
    main()
