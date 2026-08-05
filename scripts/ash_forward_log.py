#!/usr/bin/env python3
"""FORWARD LOG for ash-unicorn-sb (AM1). Pre-registered out-of-sample accumulation.

Plan locked in research/ash10hazard/strategies/ash-unicorn-sb-forward-protocol.md.
THIS SCRIPT RUNS NO TEST. It cannot report on H1 or H2 — by design, so it cannot be used
to peek between the pre-planned looks.

  append   scan forward dates with the IDENTICAL AM1 gate stack and append one row per
           qualifying setup (taken or not), hashing the frozen entry-time fields
  verify   recompute every hash, flag CONTAMINATED rows, report progress toward the looks

Feature definitions are not re-implemented here. They are imported from the same modules
that produced the in-sample numbers, so forward rows pool with
ash-unicorn-sb-autopsy-features.csv without a rename or a redefinition:

    F1_disp_delta, F2_retrace_ratio  <- scripts.ash_orderflow_test.run
    the ten context features         <- scripts.ash_autopsy.enrich

HARD GUARD: dates on or before FORWARD_START are refused. The forward set cannot be
back-filled from data that already existed when the protocol was written.

    python -m scripts.ash_forward_log verify
    python -m scripts.ash_forward_log append [--taken y|n] [--logged-by mechanical|manual]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ash_autopsy import enrich  # noqa: E402
from scripts.ash_orderflow_test import flow_frame  # noqa: E402
from scripts.ash_orderflow_test import run as scan_setups  # noqa: E402
from scripts.nya_sb01_feasibility import load_bars  # noqa: E402

# Day the protocol was committed. Forward means STRICTLY AFTER this date — no exceptions,
# no override flag. An override is the only thing that could turn this log back into a
# back-fill, so one is not provided.
FORWARD_START = "2026-08-07"

LOG = ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-forward.csv"
LOOK_1, LOOK_2 = 20, 46

IDENTITY = ["date", "time", "session", "window", "direction", "taken"]
TRADE = ["entry", "stop", "target", "exit", "exit_time", "risk_pts", "R", "outcome",
         "be_moved"]
ON_TRIAL = ["F1_disp_delta", "F2_retrace_ratio"]
CONTEXT = ["htf_aligned", "atr_pct", "dist_to_level_R", "news_in_window", "news_day",
           "entry_min_into_window", "risk_pts_v", "dow", "direction_long"]
PROVENANCE = ["flow_source", "logged_by", "logged_at_utc", "entry_hash", "notes"]
COLUMNS = IDENTITY + TRADE + ON_TRIAL + CONTEXT + PROVENANCE

# Frozen at entry and hashed. Outcome fields are deliberately EXCLUDED — they are filled
# after the close and filling them must not read as contamination.
FROZEN = (["date", "time", "direction", "entry", "stop", "target", "risk_pts"]
          + ON_TRIAL + CONTEXT)


def row_hash(r: pd.Series) -> str:
    blob = "|".join(f"{c}={'' if pd.isna(r.get(c)) else r.get(c)}" for c in FROZEN)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def empty_log() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def read_log() -> pd.DataFrame:
    if not LOG.exists():
        return empty_log()
    return pd.read_csv(LOG, dtype={"date": str, "time": str, "entry_hash": str})


def cmd_append(args: argparse.Namespace) -> None:
    bars = load_bars()
    fwd_days = sorted(d for d in bars.day.unique() if d > FORWARD_START)
    if not fwd_days:
        print(f"No bar data after {FORWARD_START}. Nothing to log — the clock is running "
              f"but no forward session exists yet.")
        print(f"bar data currently ends {bars.day.max()}.")
        return

    setups = scan_setups(bars, flow_frame())
    setups = setups[setups.date > FORWARD_START].copy()
    if setups.empty:
        print(f"{len(fwd_days)} forward session(s) present, 0 qualifying setups. "
              f"Nothing to append.")
        return

    d = enrich(setups, bars)
    d["direction_long"] = (d.direction == "long").astype(int)
    d["taken"] = args.taken
    d["logged_by"] = args.logged_by
    d["logged_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    d["flow_source"] = "output/fp_minutes.parquet"
    d["notes"] = ""
    for c in COLUMNS:
        if c not in d.columns:
            d[c] = pd.NA
    d = d[COLUMNS]
    d["entry_hash"] = d.apply(row_hash, axis=1)

    old = read_log()
    seen = set(zip(old.date, old.time)) if len(old) else set()
    new = d[~d.apply(lambda r: (r.date, r.time) in seen, axis=1)]
    if new.empty:
        print(f"All {len(d)} forward setup(s) already logged. Append-only: nothing written.")
        return
    pd.concat([old, new], ignore_index=True).to_csv(LOG, index=False)
    print(f"appended {len(new)} row(s) -> {LOG.relative_to(ROOT)}")
    print(new[["date", "time", "direction", "taken", "F1_disp_delta",
               "F2_retrace_ratio"]].to_string(index=False))


def cmd_verify(_: argparse.Namespace) -> None:
    d = read_log()
    print("FORWARD LOG — ash-unicorn-sb (AM1). Integrity + progress. NO TEST IS RUN.\n")
    print(f"protocol : research/ash10hazard/strategies/ash-unicorn-sb-forward-protocol.md")
    print(f"forward span begins: strictly after {FORWARD_START}\n")

    if len(d):
        bad_date = d[d.date <= FORWARD_START]
        d = d.assign(_h=d.apply(row_hash, axis=1))
        tampered = d[d.entry_hash.notna() & (d._h != d.entry_hash)]
        print(f"rows                     {len(d)}")
        print(f"hash OK                  {int((d._h == d.entry_hash).sum())}")
        print(f"CONTAMINATED             {len(tampered)}")
        print(f"pre-forward dates (BAD)  {len(bad_date)}")
        if len(tampered):
            print("\n!! frozen fields changed after logging — these rows are CONTAMINATED "
                  "and must be excluded:")
            print(tampered[["date", "time", "entry_hash", "_h"]].to_string(index=False))
        if len(bad_date):
            print("\n!! rows dated on or before the protocol commit — not out-of-sample:")
            print(bad_date[["date", "time"]].to_string(index=False))
    else:
        print("rows                     0   (header-only — the clock has started, "
              "no forward setup has occurred yet)")

    n = len(d)
    cov = int(d[ON_TRIAL].notna().all(axis=1).sum()) if n else 0
    resolved = int(d.outcome.notna().sum()) if n else 0
    print(f"\nPROGRESS")
    print(f"  forward setups logged  {n}")
    print(f"  outcome resolved       {resolved}")
    print(f"  flow-covered           {cov}")
    print(f"  toward LOOK 1 (n=20)   {cov}/{LOOK_1}   need +{max(0, LOOK_1 - cov)}")
    print(f"  toward LOOK 2 (n=46)   {cov}/{LOOK_2}   need +{max(0, LOOK_2 - cov)}")
    if cov >= LOOK_1:
        print("\n>>> LOOK 1 TRIGGER REACHED. Run the pre-registered analysis in the "
              "protocol. Not before.")
    else:
        print("\nNo look triggered. H1 and H2 remain untested — do not run them early.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append", help="scan forward dates and append qualifying setups")
    a.add_argument("--taken", choices=["y", "n"], default="n",
                   help="was the setup actually traded (default n — logged for base rate)")
    a.add_argument("--logged-by", choices=["mechanical", "manual"], default="mechanical")
    a.set_defaults(fn=cmd_append)
    v = sub.add_parser("verify", help="hash check + progress; runs no test")
    v.set_defaults(fn=cmd_verify)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
