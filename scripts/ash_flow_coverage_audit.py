#!/usr/bin/env python3
"""Flow-coverage audit for ash-unicorn-sb (AM1). AUDIT ONLY — no outcome measured.

Answers one question: are there trades sitting inside the aggressor-tagged data we
actually own that have never had flow derivations built for them?

It checks coverage from BOTH ends so a stale assumption cannot hide a gap:
  - the raw footprint files on disk (data/reference/cvd/footprint_*.parquet), which is
    where the owned span is really defined
  - the derived per-minute frame (output/fp_minutes.parquet) actually consumed by
    scripts/ash_orderflow_test.py

A trade is only "recoverable" if it falls inside the raw span AND lacks derivations.
Anything before the raw span cannot be recovered from data we hold, and is reported as
such rather than interpolated.

Sealed 2023/24 holdout footprint files are EXCLUDED by name and never opened.

    python -m scripts.ash_flow_coverage_audit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
STRAT = ROOT / "research/ash10hazard/strategies"


def raw_footprint_span() -> tuple[str, str, list]:
    """Owned aggressor span from the raw files. Sealed holdout files are skipped."""
    files = sorted(p for p in (ROOT / "data/reference/cvd").glob("footprint_*.parquet")
                   if "holdout" not in p.name)
    spans = []
    for p in files:
        t = pd.to_datetime(pd.read_parquet(p, columns=["ts_minute"]).ts_minute, utc=True)
        spans.append((p.name, t.min().tz_convert(NY), t.max().tz_convert(NY)))
    lo = min(s[1] for s in spans).strftime("%Y-%m-%d")
    hi = max(s[2] for s in spans).strftime("%Y-%m-%d")
    return lo, hi, spans


def main() -> None:
    lo, hi, spans = raw_footprint_span()
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp.index = pd.to_datetime(fp.index)
    fp_days = set(fp.index.strftime("%Y-%m-%d"))

    raw = pd.read_csv(STRAT / "ash-unicorn-sb-raw-trades.csv")
    fl = pd.read_csv(STRAT / "ash-unicorn-sb-orderflow-trades.csv")
    m = raw.merge(fl[["date", "F1_disp_delta", "F2_retrace_ratio"]], on="date", how="left")
    m["in_owned"] = m.date.between(lo, hi)
    m["day_in_fp"] = m.date.isin(fp_days)
    m["has_flow"] = m.F1_disp_delta.notna() & m.F2_retrace_ratio.notna()

    print("FLOW-COVERAGE AUDIT — ash-unicorn-sb (AM1 09:45-10:15 ET). No outcomes measured.\n")
    print("owned aggressor-tagged files (sealed holdout excluded):")
    for n, a, b in spans:
        print(f"  {n:<34} {a:%Y-%m-%d} -> {b:%Y-%m-%d}")
    print(f"\nOWNED SPAN (union)     : {lo} -> {hi}")
    print(f"derived fp_minutes span: {min(fp_days)} -> {max(fp_days)}  ({len(fp_days)} days)")
    print(f"trade log span         : {m.date.min()} -> {m.date.max()}  ({len(m)} trades)\n")

    print(m[["date", "time", "direction", "R", "outcome",
             "in_owned", "day_in_fp", "has_flow"]].to_string(index=False))

    gap = m[m.in_owned & ~m.has_flow]
    unrec = m[~m.in_owned]
    print(f"\ntrades total                        {len(m)}")
    print(f"inside owned span                   {int(m.in_owned.sum())}")
    print(f"  of which already derived          {int((m.in_owned & m.has_flow).sum())}")
    print(f"  RECOVERABLE (in span, no flow)    {len(gap)}")
    print(f"before owned span (unrecoverable)   {len(unrec)}")
    if len(gap):
        print("\nRECOVERABLE TRADES — build derivations for these:")
        print(gap[["date", "time", "outcome"]].to_string(index=False))
    else:
        print(f"\nSAMPLE TERMINAL WITHIN OWNED DATA — {int((m.in_owned & m.has_flow).sum())} "
              "flow-covered is the ceiling;")
        print("only forward accumulation grows it. No Stage 4/5 re-run is warranted.")
    if len(unrec):
        print(f"\nUnrecoverable window needed: {unrec.date.min()} -> {unrec.date.max()} "
              f"({len(unrec)} trades). Requires a Databento GLBX.MDP3 trades pull for a span")
        print("that PREDATES every footprint file we hold. Not attempted.")


if __name__ == "__main__":
    main()
