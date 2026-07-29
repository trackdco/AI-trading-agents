#!/usr/bin/env python3
"""The RAW ORDER-FLOW-VALIDATED BOOK — standard 1-lot, deliberately unconfigured.

ANGUS 30-Jul: *"i dont want to build stop loss metrics and stuff until we have the
conclusive volume of order flow validated trades... standard 1 lot sizing before we refine
any of that."* This is that deliverable: every validated trade over the fit span at 1-lot,
V8 exits (winner of the exit study), shown BOTH uncapped (the full validated stream) and
under the 2-per-session causal walk. No conviction sizing, no day stop, no escalation, no
DD ramp — those get DESIGNED from this data, not imposed on it.

Validation gates (L3 verdicts, survivor architecture):
  pre  = W==1                    (load-bearing; all pre edge lives inside it)
  gold = D==1                    (hard gate, unrescuable off-side)
Score tiers displayed on top (gold survivor-weighted 2D+Tc+AGE+T2[+TRIG], pre W*2+G+F_)
so the volume/quality tradeoff is visible — the tier choice is ANGUS's, made from this
table, not made here.

    python -m scripts.raw_validated_book
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select  # noqa: E402


def load() -> pd.DataFrame:
    S = pd.read_parquet(ROOT / "output/l3_scored_fit.parquet")
    S = S[(S.risk >= 7) & (S.risk <= 60) & S.sess.isin(["pre", "gold"])].copy()
    S["valid"] = np.where(S.sess == "pre", S.W == 1, S.D == 1)
    S["month"] = S.day.str[:7]
    return S


def table(d: pd.DataFrame, weeks: float, label: str) -> None:
    if not len(d):
        return
    print(f"  {label:<26} n={len(d):>4}  {len(d) / weeks:>4.1f}/wk  "
          f"WR {(d.dollars_1lot > 0).mean() * 100:>3.0f}%  meanR {d.R.mean():+.3f}  "
          f"totR {d.R.sum():+7.1f}  ${d.dollars_1lot.sum():+10,.0f}")


def monthly(d: pd.DataFrame, label: str) -> None:
    m = d.groupby("month").dollars_1lot.sum()
    green = (m > 0).sum()
    print(f"\n  {label} monthly (1-lot): {green}/{len(m)} green")
    for k, v in m.items():
        print(f"    {k}  ${v:+9,.0f}  ({(d[d.month == k].dollars_1lot > 0).mean() * 100:.0f}% WR, "
              f"n={len(d[d.month == k])})")


def maxdd(d: pd.DataFrame) -> float:
    cum = d.sort_values("fill_ts").groupby("day").dollars_1lot.sum().cumsum()
    return float((cum.cummax() - cum).max()) if len(cum) else 0.0


def main() -> None:
    S = load()
    weeks = S.day.nunique() / 5.0
    V = S[S.valid]
    print(f"span: {S.day.nunique()} days ({weeks:.1f} wk) | candidates in-band {len(S)} "
          f"| VALIDATED {len(V)}\n")

    print("UNCAPPED validated stream (1-lot, V8 exits):")
    pre, gold = V[V.sess == "pre"], V[V.sess == "gold"]
    table(pre, weeks, "pre  W==1")
    table(pre[pre.G == 1], weeks, "pre  W==1 & G==1")
    table(gold, weeks, "gold D==1 (score>=2)")
    table(gold[gold.gold_score >= 4], weeks, "gold score>=4")
    table(gold[gold.gold_score >= 5], weeks, "gold score>=5")
    table(V, weeks, "TOTAL validated")

    print("\nCAPPED 2/session, causal first-clearing walk (no escalation, no day stop):")
    C = V.copy().rename(columns={"sess": "session"})
    C["score"] = np.where(C.session == "pre", 10.0, C.gold_score)   # pre: W is the gate
    for gate, lbl in [(2.0, "gold gate>=2 (D alone)"), (4.0, "gold gate>=4"),
                      (5.0, "gold gate>=5")]:
        pol2 = L4Policy(cap_per_session=2,
                        threshold={"pre": 0.0, "gold": gate},
                        escalation_threshold={"pre": 0.0, "gold": gate},
                        day_stop_dollars=1e12)
        B = select(C, pol2, dollars_col="dollars_1lot")
        t = B[B.taken]
        zero_days = S.day.nunique() - t.day.nunique()
        print(f"\n  == {lbl} ==   taken {len(t)} ({len(t) / weeks:.1f}/wk) | "
              f"zero-trade days {zero_days}/{S.day.nunique()} | maxDD(1-lot) ${maxdd(t):,.0f}")
        for sess in ["pre", "gold"]:
            table(t[t.session == sess], weeks, f"   {sess}")
        m = t.groupby("month").dollars_1lot.sum()
        print(f"   months green: {(m > 0).sum()}/{len(m)} | total ${t.dollars_1lot.sum():+,.0f}")

    pol = L4Policy(cap_per_session=2, threshold={"pre": 0.0, "gold": 4.0},
                   escalation_threshold={"pre": 0.0, "gold": 4.0}, day_stop_dollars=1e12)
    B = select(C, pol, dollars_col="dollars_1lot")
    t = B[B.taken]
    monthly(t, "CAPPED gold>=4 book")
    out = ROOT / "output/raw_validated_book.parquet"
    B.to_parquet(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
