#!/usr/bin/env python3
"""
PREREGISTRATION-3 §4 — conviction sizing on the TEST half, run only for features that HELD.

usage: sizing_test.py --features F.parquet --config C1a_C3a --held F11:against:with [F10:best:worst ...]
Score = (#held features in best bucket) − (#held features in worst bucket).
Reading A: {≤−1: 0.5×, 0: 1×, ≥+1: 1.5×}; reading B: {0.75×, 1×, 1.25×}.
PASS if under BOTH readings net $ per unit risk improves vs flat AND max DD (in $) is not worse by >10%.
"""
import argparse
from datetime import date

import pandas as pd
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def curve(pnl):
    cum = peak = dd = 0.0
    for x in pnl:
        cum += x; peak = max(peak, cum); dd = max(dd, peak - cum)
    return cum, dd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/features/features.parquet")
    ap.add_argument("--config", default="C1a_C3a")
    ap.add_argument("--held", nargs="+", required=True, help="FEATURE:best_bucket:worst_bucket")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    df = pd.read_parquet(a.features)
    df = df[df["config"] == a.config].copy()
    df["ed"] = pd.to_datetime(df["entry_ts"], utc=True).dt.tz_convert(ET).dt.date
    df = df[(df["ed"] >= date(2025, 1, 1)) & (df["ed"] <= date(2026, 9, 2))].sort_values("entry_ts")
    score = pd.Series(0, index=df.index)
    for spec in a.held:
        f, best, worst = spec.split(":")
        score += (df[f] == best).astype(int) - (df[f] == worst).astype(int)
    df["score"] = score
    lines = [f"# Conviction sizing — test half, {a.config}, held features {a.held}, n={len(df)}\n",
             "| reading | multipliers | net $ | $ per unit risk | max DD $ | vs flat: return/risk | vs flat: DD | trades ×0.5/0.75 | ×1 | ×1.5/1.25 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    risk_unit = df["stop"] * 2 * 2.0          # stop pts × 2 contracts × $2/pt = dollars at risk at 1×
    flat_net, flat_dd = curve(df["pnl"]); flat_rr = flat_net / risk_unit.sum()
    lines.append(f"| flat | 1× | {flat_net:+,.0f} | {flat_rr:+.4f} | {flat_dd:,.0f} | — | — | — | {len(df)} | — |")
    verdicts = []
    for name, (lo, hi) in (("A", (0.5, 1.5)), ("B", (0.75, 1.25))):
        mult = df["score"].map(lambda s: lo if s <= -1 else (hi if s >= 1 else 1.0))
        net, dd = curve(df["pnl"] * mult); rr = net / (risk_unit * mult).sum()
        ok = (rr > flat_rr) and (dd <= flat_dd * 1.10)
        verdicts.append(ok)
        lines.append(f"| {name} | {lo}/1/{hi} | {net:+,.0f} | {rr:+.4f} | {dd:,.0f} | {'better' if rr > flat_rr else 'worse'} ({100*(rr/flat_rr-1):+.1f}%) | {'ok' if dd <= flat_dd*1.10 else 'WORSE'} ({100*(dd/flat_dd-1):+.1f}%) | {(mult==lo).sum()} | {(mult==1).sum()} | {(mult==hi).sum()} |")
    by = df.groupby("score")["pnl"].agg(["count", "mean"])
    lines.append("\nby score: " + ", ".join(f"score {int(s)}: n={int(r['count'])}, mean {r['mean']:+.2f}" for s, r in by.iterrows()))
    lines.append(f"\n**Sizing verdict (minimum across readings): {'PASS' if all(verdicts) else 'NOT DEMONSTRATED'}**")
    text = "\n".join(lines); print(text)
    if a.md:
        open(a.md, "w").write(text + "\n")


if __name__ == "__main__":
    main()
