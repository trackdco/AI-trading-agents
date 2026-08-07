#!/usr/bin/env python3
"""LDN-ATC-01 L1 STAGE 1 — full reporting per docs/PREREG-london-atc-L1.md §10.

Runs ONLY after scripts.ldn_atc01_l1 has passed its census-reproduction gate.
Fit span, bars only, in-sample. Can only KILL, never confirm.

    python -m scripts.ldn_atc01_l1_report
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_atc01_l1 import (  # noqa: E402
    FIT_END, FIT_START, classify, load_bars, rs, sessions, simulate, win)

SEED = 20260806


def chain_stripped_trigger(d: pd.DataFrame, bias: str):
    """Same bias, same clock, NO pullback and NO LTA requirement."""
    m15, m30 = rs(d, "15min"), rs(d, "30min")
    t15, t30 = win(m15, "07:00", "09:00"), win(m30, "07:00", "09:00")
    for ts in t30.index:
        if ts not in t15.index:
            continue
        a, b = t15.loc[ts], t30.loc[ts]
        ok = (a.close < a.open and b.close < b.open) if bias == "short" \
            else (a.close > a.open and b.close > b.open)
        if ok:
            return ts
    return None


def build(S: dict, C: pd.DataFrame, cost: float, target_mode="structural") -> pd.DataFrame:
    """The declared ATC population."""
    out = []
    for _, r in C[C.status == "triggered"].iterrows():
        res = simulate(S[r.day], r.bias, r.trig_ts, r.ref, cost, target_mode)
        if res is None:
            continue
        res.update(day=r.day, era=r.era, bias=r.bias, trig=r.trig_ts,
                   clock=r.trig_ts.strftime("%H:%M"))
        out.append(res)
    return pd.DataFrame(out)


def build_control(S: dict, C: pd.DataFrame, cost: float, kind: str) -> pd.DataFrame:
    out = []
    rng = np.random.default_rng(SEED)
    for _, r in C.iterrows():
        if r.bias is None or (isinstance(r.bias, float) and np.isnan(r.bias)):
            continue
        if kind == "randomised_bias":
            if r.status != "triggered":
                continue
            bias = "short" if rng.random() < 0.5 else "long"
            ts = r.trig_ts
        else:                                   # chain_stripped
            bias = r.bias
            ts = chain_stripped_trigger(S[r.day], bias)
            if ts is None:
                continue
        res = simulate(S[r.day], bias, ts, r.ref, cost, "structural")
        if res is None:
            continue
        res.update(day=r.day, era=r.era, chained=(r.status == "triggered"))
        out.append(res)
    return pd.DataFrame(out)


def stat(x: pd.DataFrame) -> dict:
    f = x[x.skip.isna()]
    if f.empty:
        return dict(n=0, mean=np.nan, wr=np.nan, pf=np.nan)
    w, l = f[f.r_net > 0].r_net.sum(), -f[f.r_net < 0].r_net.sum()
    return dict(n=len(f), mean=f.r_net.mean(), wr=(f.r_net > 0).mean(),
                pf=(w / l if l > 0 else np.inf))


def line(lbl, s):
    return (f"{lbl:<34}{s['n']:>6}{s['mean']:>+10.3f}{s['wr']:>9.1%}"
            f"{s['pf']:>8.2f}") if s["n"] else f"{lbl:<34}{0:>6}{'—':>10}{'—':>9}{'—':>8}"


def main() -> None:
    b = load_bars()
    S = {d: v for d, v in sessions(b).items() if FIT_START <= str(d) <= FIT_END}
    rows = []
    for day, d in S.items():
        r = classify(d)
        r.update(day=day, era="2025" if str(day) < "2026-01-01" else "2026",
                 half=("2025H1" if str(day) < "2025-07-01" else "2025H2")
                 if str(day) < "2026-01-01" else
                 ("2026H1" if str(day) < "2026-07-01" else "2026H2"))
        rows.append(r)
    C = pd.DataFrame(rows)
    print(f"GATE: triggered={int((C.status=='triggered').sum())} (published 108) | "
          f"2025={int(((C.status=='triggered')&(C.era=='2025')).sum())} (69) | "
          f"2026={int(((C.status=='triggered')&(C.era=='2026')).sum())} (39)")

    P = {c: build(S, C, c) for c in (1.0, 2.0)}
    A = P[2.0]
    print("\n" + "=" * 78)
    print("1. EVENT COUNTS AND FILL RATE")
    print("=" * 78)
    print(f"  triggered sessions (chain complete)   {len(A)}")
    for k, v in A.skip.value_counts(dropna=False).items():
        print(f"    {'FILLED / usable' if pd.isna(k) else 'skipped: '+str(k):<36}{v}")
    filled = A[A.skip.isna()]
    print(f"  FILL RATE (of triggers with a valid target): "
          f"{len(filled)}/{int((A.skip!='target_not_beyond_entry').sum())} = "
          f"{len(filled)/max(int((A.skip!='target_not_beyond_entry').sum()),1):.1%}")

    print("\n" + "=" * 78)
    print("2. HEADLINE — strict 2pt stack (1pt shown alongside)")
    print("=" * 78)
    print(f"{'cell':<34}{'n':>6}{'meanR':>10}{'WR':>9}{'PF':>8}")
    for c in (2.0, 1.0):
        print(f"-- cost {c:.0f}pt --")
        print(line("  pooled", stat(P[c])))
        for era in ("2025", "2026"):
            print(line(f"    {era}", stat(P[c][P[c].era == era])))
    print("\n  by half-year (2pt):")
    for h in ("2025H1", "2025H2", "2026H1", "2026H2"):
        days = set(C[C.half == h].day)
        print(line(f"    {h}", stat(A[A.day.isin(days)])))

    print("\n  07:30 vs 08:00-and-later (2pt):")
    print(line("    07:30 (pre-open)", stat(A[A.clock == "07:30"])))
    print(line("    08:00 and later", stat(A[A.clock != "07:30"])))

    print("\n" + "=" * 78)
    print("3. k DISTRIBUTION (prereg 10.2) — structural target")
    print("=" * 78)
    kk = filled.k
    print(f"  mean {kk.mean():.2f} | median {kk.median():.2f} | "
          f"FRACTION k<1.0R = {(kk<1.0).mean():.1%}")
    print("  left tail: min {:.2f} | p5 {:.2f} | p10 {:.2f} | p25 {:.2f}".format(
        kk.min(), kk.quantile(.05), kk.quantile(.10), kk.quantile(.25)))
    print("  deciles: " + " ".join(f"{kk.quantile(q):.2f}" for q in np.arange(.1, 1.0, .1)))
    p_req = (0.4804 + 1) / (kk.mean() + 1)
    print(f"  -> Stage 2 required WR at the realised mean k: {p_req:.1%}")

    print("\n" + "=" * 78)
    print("4. RISK BANDS on ATC's own population (2pt) — is 9.5pt native here?")
    print("=" * 78)
    bands = [(0, 3), (3, 5), (5, 7), (7, 9.5), (9.5, 15), (15, 25), (25, 1e9)]
    print(f"{'band (pts)':<34}{'n':>6}{'meanR':>10}{'WR':>9}{'PF':>8}")
    for lo, hi in bands:
        print(line(f"    {lo}-{hi if hi<1e8 else '+'}", stat(filled[(filled.risk >= lo) & (filled.risk < hi)])))
    print(line("  below 9.5", stat(filled[filled.risk < 9.5])))
    print(line("  at/above 9.5", stat(filled[filled.risk >= 9.5])))

    print("\n" + "=" * 78)
    print("5. EXITS, MFE/MAE, BOUND-BOTH-ORDERINGS")
    print("=" * 78)
    for k, v in filled.exit.value_counts().items():
        print(f"    {k:<34}{v:>5}  {v/len(filled):>6.1%}")
    print(f"    BOUND-both-orderings cases        {int(filled.both_orderings.sum()):>5}"
          f"  {filled.both_orderings.mean():>6.1%}  (stop taken first, declared)")
    print(f"    MFE median {filled.mfe_r.median():.2f}R | MAE median {filled.mae_r.median():.2f}R")

    print("\n" + "=" * 78)
    print("6. CONTROLS")
    print("=" * 78)
    RB = build_control(S, C, 2.0, "randomised_bias")
    CS = build_control(S, C, 2.0, "chain_stripped")
    print(line("  ATC (declared)", stat(A)))
    print(line("  control: randomised bias", stat(RB)))
    print("\n  10.1 TEST A — SELECTION (disjoint populations):")
    print(line("    ATC, chain complete", stat(A)))
    print(line("    bias but chain NOT complete", stat(CS[~CS.chained])))
    print("\n  10.1 TEST B — ENTRY (paired, sessions where both fire):")
    both = set(A[A.skip.isna()].day) & set(CS[CS.skip.isna()].day)
    a_p = A[A.day.isin(both) & A.skip.isna()].set_index("day").r_net.sort_index()
    c_p = CS[CS.day.isin(both) & CS.skip.isna()].set_index("day").r_net.sort_index()
    c_p = c_p[~c_p.index.duplicated()]
    a_p, c_p = a_p.align(c_p, join="inner")
    dlt = a_p - c_p
    print(f"    paired sessions {len(dlt)} | ATC {a_p.mean():+.3f}R vs stripped "
          f"{c_p.mean():+.3f}R | diff {dlt.mean():+.3f}R")
    if len(dlt) > 2 and dlt.std() > 0:
        print(f"    paired t = {dlt.mean()/(dlt.std()/np.sqrt(len(dlt))):+.2f}")

    filled.to_parquet(ROOT / "output/ldn_atc01_l1_trades.parquet")
    print("\ntrades -> output/ldn_atc01_l1_trades.parquet")


if __name__ == "__main__":
    main()
