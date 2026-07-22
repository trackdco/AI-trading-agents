#!/usr/bin/env python3
"""Dollar-evaluate the VERIFIED stand-down gates (Angus 23-Jul, ultracode synthesis).

All 26 findings survived adversarial recompute + 3-4/4 subperiod stress. Here we convert the
stand-down predictors into $ on top of the no-forecast portfolio, with thresholds fit on 2025
ONLY, frozen on 2026. Two layers:

  DAY gate  (skip whole day)  : composite onflow-magnitude high  -> both_red risk
  WINDOW gates (skip a window): pre_red gate from pre-8:00 flow; gold_red gate from the
                                09:40-known signals (pre_traded, choppy pm/open, stalling accel)

Baseline = the no-forecast portfolio (both books, every day, verified trade rules).

    python -m scripts.standdown_eval
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def zdir(train, col, y):
    """AUC-signed z-score of col using train stats; returns (mu, sd, sign)."""
    mu, sd = train[col].mean(), train[col].std()
    d = pd.DataFrame({"x": train[col], "y": train[y]}).dropna()
    r = d.x.rank(); n1 = int(d.y.sum()); n0 = len(d) - n1
    a = (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return mu, sd, (1.0 if a >= 0.5 else -1.0)


def main():
    F = pd.read_parquet("output/dayflow_v2.parquet")
    S = pd.read_parquet("output/trade_angles.parquet")
    S["win_"] = np.where(S.fillmi.dt.hour * 60 + S.fillmi.dt.minute < 570, "pre", "gold")

    # ---- the verified no-forecast portfolio trade set (from earlier) ----
    q1 = S[(S.pattern == "B2") & (S.yr == 2025) & (S.conf_PM == 1)].cvd_PM.abs().quantile(0.25)
    keep = (((S.pattern == "B2") & (S.conf_PM == 1) & (S.cvd_PM.abs() >= q1) & (S.path_lo == 0)) |
            ((S.pattern == "B") & (S.conf_last15 == 1) & (S.div15 == 0)) |
            ((S.pattern == "A") & (S.conf_PM == 1)))
    K = S[keep].copy()

    tr = F[F.yr == 2025]

    # ---- DAY gate: composite of abs_cvd_ASIA, absz_cvd_ON, abs(eff_ASIA); high => both_red ----
    day_feats = ["cvd_ASIA", "cvd_ON", "eff_ASIA"]
    comp = {}
    for yr, d in (("2025", F[F.yr == 2025]), ("2026", F[F.yr == 2026])):
        s = pd.Series(0.0, index=d.index)
        for c in day_feats:
            v = d[c].abs()
            mu, sd = tr[c].abs().mean(), tr[c].abs().std()
            s = s.add((v - mu) / sd, fill_value=0.0)
        comp[yr] = s / len(day_feats)
    COMP = pd.concat(comp.values())
    day_thr = comp["2025"].quantile(0.80)                 # skip the top-quintile onflow-mag days

    # ---- WINDOW gates ----
    # pre_red gate: same onflow composite (pre-8:00) high  -> skip PRE window
    pre_thr = comp["2025"].quantile(0.70)
    # gold_red gate: pre_traded OR choppy pm/open OR stalling accel  (all 09:40-known)
    def gold_flags(d):
        pm_lo = d.pm_eff_path < tr.pm_eff_path.quantile(0.40)
        op_lo = d.op_eff_path < tr.op_eff_path.quantile(0.40)
        accel_lo = d.cvd_accel_PM.abs() < tr.cvd_accel_PM.abs().quantile(0.40)
        crosses_hi = d.pm_crosses > tr.pm_crosses.quantile(0.60)
        return (pm_lo.astype(int) + op_lo.astype(int) + accel_lo.astype(int) + crosses_hi.astype(int))

    gflag = gold_flags(F)
    gold_gate_thr = 2                                       # skip gold if >=2 chop/stall flags

    dd = COMP.rename("comp")
    F2 = F.join(dd)
    F2["gflag"] = gflag
    day_skip = F2.comp >= day_thr
    pre_skip = F2.comp >= pre_thr
    gold_skip = F2.gflag >= gold_gate_thr

    def evalyr(yr):
        d = K[K.yr == yr].copy()
        days = F2[F2.yr == yr]
        dskip = set(days.index[day_skip.reindex(days.index, fill_value=False)])
        pskip = set(days.index[pre_skip.reindex(days.index, fill_value=False)])
        gskip = set(days.index[gold_skip.reindex(days.index, fill_value=False)])
        base = d.dollars.sum()
        # apply: drop trade if its day is day-skipped, or (its window is skipped)
        def kept(row):
            if row.day in dskip:
                return False
            if row.win_ == "pre" and row.day in pskip:
                return False
            if row.win_ == "gold" and row.day in gskip:
                return False
            return True
        g = d[d.apply(kept, axis=1)]
        ceil = days.oracle_sd.sum()
        dailypl = g.groupby("day").dollars.sum(); cum = dailypl.cumsum()
        mdd = (cum.cummax() - cum).max() if len(cum) else 0
        return base, g.dollars.sum(), len(d), len(g), ceil, g.win.mean() * 100 if len(g) else 0, mdd

    S["win"] = S.dollars > 0; K["win"] = K.dollars > 0
    print("           portfolio ->  +stand-down gates (day + window)")
    for yr in (2025, 2026):
        base, gated, nb, ng, ceil, wr, mdd = evalyr(yr)
        print(f"  {yr}: ${base:+8,.0f} ({nb} tr)  ->  ${gated:+8,.0f} ({ng} tr, {wr:.0f}% win, maxDD ${mdd:,.0f})  "
              f"| capture {gated/ceil*100:.0f}% of ${ceil:+,.0f}")

    # monthly consistency of the gated book
    d = K.copy()
    days = F2
    dskip = set(days.index[day_skip]); pskip = set(days.index[pre_skip]); gskip = set(days.index[gold_skip])
    def kept(row):
        return not (row.day in dskip or (row.win_ == "pre" and row.day in pskip)
                    or (row.win_ == "gold" and row.day in gskip))
    g = d[d.apply(kept, axis=1)].copy()
    g["mo"] = g.day.str[:7]
    m = g.groupby("mo").dollars.agg(["sum", "count"])
    print(f"\n  gated book months green: {int((m['sum']>0).sum())}/{len(m)}")
    for mo, r in m.iterrows():
        print(f"    {mo} n={int(r['count']):3d}  ${r['sum']:+8,.0f}")
    g.to_parquet("output/gated_portfolio.parquet")
    print(f"\n  total gated: ${g.dollars.sum():+,.0f} over {len(g)} trades")


if __name__ == "__main__":
    main()
