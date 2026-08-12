"""L0 build — assemble the event table for 2023-01-01 → 2026-01-31.

Run:  python news_lab/build_l0.py            (needs FRED_API_KEY for BLS/BEA)
      python news_lab/build_l0.py --no-fred  (keyless subset, for smoke tests)

Source of truth per family, in the order the SPEC trusts them:
  fomc              federalreserve.gov calendar   (statement URL = the date)
  claims            oui.doleta.gov press probe    (filename = the date)
  cpi/ppi/nfp       FRED release dates            (BLS schedule, machine-readable)
  pce/retail/gdp    FRED release dates            (BEA/Census schedule)
  ism_mfg/ism_svc   1st/3rd federal business day  (rule — stays flagged)

Nothing here invents a date. Every scraper raises rather than filling a gap.
"""
from __future__ import annotations
import sys
import os
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newslab.events import (            # noqa: E402
    WINDOW_START, WINDOW_END, assemble, build_ism, scrape_fomc,
    scrape_dol_claims, fred_release_dates)
from newslab.config import SEAL_FROM    # noqa: E402

FRED_FAMILIES = ["cpi", "ppi", "nfp", "pce", "retail", "gdp_adv"]

# Expected counts over the window, and WHY. Monthly families: 37 months.
MONTHS = len(pd.period_range(WINDOW_START, WINDOW_END, freq="M"))
EXPECTED = {
    "cpi": MONTHS, "ppi": MONTHS, "nfp": MONTHS, "pce": MONTHS,
    "retail": MONTHS, "ism_mfg": MONTHS, "ism_svc": MONTHS,
    "gdp_adv": len(pd.period_range(WINDOW_START, WINDOW_END, freq="Q")),
    "fomc": 25,      # 8/yr 2023-25 + the 2026-01-28 decision
    "claims": len(pd.date_range(WINDOW_START, WINDOW_END, freq="W-THU")),
}


def in_window(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["date"] >= WINDOW_START) & (df["date"] <= WINDOW_END)]


def build(use_fred: bool = True) -> pd.DataFrame:
    frames = []

    print("[fomc]   federalreserve.gov …", flush=True)
    frames.append(in_window(scrape_fomc()))
    print(f"         {len(frames[-1])} decisions")

    print("[claims] probing oui.doleta.gov (this walks every weekday) …",
          flush=True)
    frames.append(in_window(scrape_dol_claims(WINDOW_START, WINDOW_END)))
    print(f"         {len(frames[-1])} releases confirmed")

    print("[ism]    1st/3rd federal business day rule …", flush=True)
    frames.append(in_window(build_ism(WINDOW_START, WINDOW_END)))
    print(f"         {len(frames[-1])} rows (needs_verification=True)")

    if use_fred:
        for fam in FRED_FAMILIES:
            print(f"[{fam}] FRED release dates …", flush=True)
            df = in_window(fred_release_dates(fam, WINDOW_START, WINDOW_END))
            print(f"         {len(df)} releases")
            frames.append(df)
    else:
        print("[fred]   SKIPPED (--no-fred): cpi/ppi/nfp/pce/retail/gdp_adv "
              "absent from this table")

    ev = assemble(frames)
    return ev[(ev["date"] >= WINDOW_START) & (ev["date"] <= WINDOW_END)
              ].reset_index(drop=True)


def report(ev: pd.DataFrame) -> pd.DataFrame:
    """Per-family counts vs expected — the GATE L0 table."""
    rows = []
    for fam, exp in sorted(EXPECTED.items()):
        got = int((ev["family"] == fam).sum())
        rows.append(dict(
            family=fam, expected=exp, got=got,
            pct=round(100.0 * got / exp, 1) if exp else None,
            needs_verification=int(
                ev.loc[ev["family"] == fam, "needs_verification"].sum()),
            gate_95=("PASS" if exp and got >= 0.95 * exp else "FAIL")))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fred", action="store_true")
    ap.add_argument("--out", default="output/events.parquet")
    a = ap.parse_args()

    ev = build(use_fred=not a.no_fred)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    ev.to_parquet(a.out, index=False)

    print(f"\nwrote {a.out}: {len(ev)} events, "
          f"{ev['date'].min()} → {ev['date'].max()}")
    print(f"seal boundary (NEWSLAB_SEAL_FROM) = {SEAL_FROM}\n")
    rep = report(ev)
    print(rep.to_string(index=False))
    dup = ev[ev.duplicated(["family", "date"], keep=False)]
    print(f"\nduplicate (family,date) rows: {len(dup)}")
    if len(dup):
        print(dup[["family", "date", "source"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
