#!/usr/bin/env python3
"""Regenerate every London arm's per-day outcome series — the missing artifact.

WHY. docs/CONFORMANCE-trial-ledger-vs-2.4.md identified one root cause behind three
§2.4 gaps: the ledger recorded summary statistics but not per-trial return series. So
effective-N could not be clustered on co-movement, PBO/CSCV had no T x N matrix, and no
SPA family audit was possible. This script produces that matrix by re-running the
committed censuses.

NO NEW TRIAL. Every arm here was already declared, run and recorded. This re-derives the
per-day vector behind numbers that are already on the record; it tests no new hypothesis
and adds nothing to the ledger count.

ONE SERIES PER (family, arm) OVER THE WHOLE FIT SPAN. The era split is a validation
device, not a separate strategy, so both era rows of an arm point at one series. Days an
arm did not fire are 0 — a strategy that does not trade earns nothing that day.

FILTER ARMS. LDN-FLOW-01 and LDN-DEF-01 arms are correlation tests, not return series.
Their strategy analogue is the declared median split: take the events in the upper half
of the measure, which is exactly the "would this filter remove losers" reading those
verdicts reported. That construction is stated here rather than chosen quietly.

SEALED-SPAN GUARD: inherited from fit_only() in every census. No holdout look.

    python -m scripts.backfill_trial_series
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.trial_ledger import LEDGER, load, series_file, write_series


def day_series(d: pd.DataFrame, value: str = "signed_ret") -> pd.Series:
    return d.groupby("day")[value].sum()


def upper_half(d: pd.DataFrame, measure: str) -> pd.Series:
    """The declared median split: events in the top half of `measure` by era."""
    keep = d.groupby("era")[measure].transform("median")
    return day_series(d[d[measure] > keep])


def main() -> None:
    written: dict[tuple[str, str], Path] = {}

    print("LDN-TRAP-01 ...")
    from scripts.ldn_trap01_census import build as trap
    t = trap()
    written[("LDN-TRAP-01", "primary")] = write_series(
        "LDN-TRAP-01", "primary", day_series(t))
    written[("LDN-TRAP-01", "secondary:first-revisit")] = write_series(
        "LDN-TRAP-01", "secondary-first-revisit", day_series(t[t.first_revisit]))

    print("LDN-VWAP-01 ...")
    from scripts.ldn_vwap01_census import build as vwap
    v, _ = vwap()
    written[("LDN-VWAP-01", "primary")] = write_series(
        "LDN-VWAP-01", "primary", day_series(v[v.gated]))
    written[("LDN-VWAP-01", "secondary:gate")] = write_series(
        "LDN-VWAP-01", "secondary-gate", day_series(v))          # ungated arm

    print("LDN-VT-01 ...")
    from scripts.ldn_vt01_census import build as vt
    w = vt()
    written[("LDN-VT-01", "primary")] = write_series(
        "LDN-VT-01", "primary", day_series(w))
    written[("LDN-VT-01", "secondary:placebo-diff")] = write_series(
        "LDN-VT-01", "secondary-placebo-diff",
        w.assign(d=w.touched.astype(float) - w.placebo_touched.astype(float))
         .groupby("day").d.sum())

    print("LDN-FLOW-01 ...")
    from scripts.ldn_flow01_events import events as flow_events
    from scripts.ldn_flow01_test import measure as flow_measure, minute_frame
    fe, mf = flow_events(), minute_frame()
    fd = flow_measure(fe, mf, 5)
    for m in ("CONFIRM", "ABSORB", "EFFORT", "TRAPPED"):
        written[("LDN-FLOW-01", m)] = write_series("LDN-FLOW-01", m, upper_half(fd, m))

    print("LDN-DEF-01 ...")
    from scripts.ldn_def01_census import footprint, measure as def_measure, trap_events
    de = trap_events()
    fp = footprint()
    de = de[(de.ts_entry >= fp.ts.min()) & (de.ts_entry <= fp.ts.max())]
    dd = def_measure(de, fp, 3, 2)
    for m in ("ABSORB", "PIN", "ICEBERG"):
        written[("LDN-DEF-01", m)] = write_series("LDN-DEF-01", m, upper_half(dd, m))

    # ---- attach paths to the ledger rows (LDN-INV-01 / LDN-SWP-01 have no rerunnable
    # census in this branch; they stay NaN and are reported as such, not silently blank)
    led = load()
    if "series_path" not in led.columns:
        led["series_path"] = pd.NA
    for (fam, arm), path in written.items():
        mask = (led.family == fam) & (led.trial == arm)
        led.loc[mask, "series_path"] = str(path)
        if not mask.any():
            print(f"  WARNING no ledger row matched {fam} / {arm}")
    led.to_parquet(LEDGER, index=False)

    covered = int(led.series_path.notna().sum())
    print(f"\nwrote {len(written)} arm series -> {series_file('X', 'Y').parent}")
    print(f"ledger rows now carrying a series: {covered} / {len(led)}")
    missing = sorted(set(led[led.series_path.isna()].family))
    if missing:
        print(f"still without series: {', '.join(missing)} "
              "(no rerunnable census on this branch — counted, not clustered)")


if __name__ == "__main__":
    main()
