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
    scrape_dol_claims, fred_release_dates, apply_time_overrides)
from newslab.config import SEAL_FROM, RELEASES   # noqa: E402

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

# Why a family's EVENT count differs from its naive cadence. An event is a NEWS
# RELEASE, not a data point: when two reference months are published in one
# release, that is one event, not two. Each entry subtracts exactly one expected
# event and names the evidence. Verified via FRED output_type=4 (which release
# date first printed which reference period) plus the official notices.
# Sources: bls.gov/bls/2025-lapse-revised-release-dates.htm (BLS cancellations),
#          bea.gov release-schedule-update blog 2025-11-24 (BEA),
#          oui.doleta.gov 404s across the whole span (DOL).
ADJUSTMENTS = {
    "cpi": [("folded", "Oct+Nov 2025 both first-printed on 2025-12-18 — the "
                       "Oct-2025 CPI news release was CANCELLED outright "
                       "(data never collected), its index published with Nov")],
    "ppi": [("folded", "Oct+Nov 2025 both first-printed on 2026-01-14 — the "
                       "Oct-2025 PPI release was cancelled and folded in")],
    "nfp": [("folded", "Oct+Nov 2025 both first-printed on 2025-12-16 — the "
                       "Oct-2025 Employment Situation was CANCELLED; the "
                       "household survey was never collected at all")],
    "pce": [("folded", "Oct+Nov 2025 both first-printed on 2026-01-22"),
            ("window_edge", "Dec-2025 PCE fell after 2026-01-31; BEA's "
                            "post-shutdown backlog pushed it past the window")],
    "retail": [("window_edge", "Dec-2025 retail fell after 2026-01-31 — the "
                               "last in-window release, 2026-01-14, covers "
                               "Nov-2025")],
    "gdp_adv": [("window_edge", "Q4-2025 advance fell after 2026-01-31. BEA "
                                "CANCELLED the Q3-2025 advance outright and "
                                "issued an initial estimate on 2025-12-23 "
                                "instead, shifting the whole cadence right")],
    "claims": [("suspended", "7 weeks, 2025-10-02..2025-11-13 — DOL suspended "
                             "the national claims release for the 43-day "
                             "shutdown; resumed 2025-11-20")] ,
}
ADJ_COUNT = {"claims": 7}   # the single claims entry stands for 7 lost weeks


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
            if fam == "gdp_adv":
                # the family IS the advance estimate; 2nd/3rd estimates share
                # the release id but are dead events (SPEC), so they are not
                # gdp_adv rows at all.
                df = df[df["release_kind"] == "print"]
            n_rev = int((df["release_kind"] == "revision_only").sum())
            print(f"         {len(df)} releases"
                  + (f" ({n_rev} revision-only)" if n_rev else ""))
            frames.append(df)
    else:
        print("[fred]   SKIPPED (--no-fred): cpi/ppi/nfp/pce/retail/gdp_adv "
              "absent from this table")

    ev = apply_time_overrides(assemble(frames))
    ev["release_kind"] = ev["release_kind"].fillna("print")
    return ev[(ev["date"] >= WINDOW_START) & (ev["date"] <= WINDOW_END)
              ].reset_index(drop=True)


def report(ev: pd.DataFrame) -> pd.DataFrame:
    """Per-family counts vs expected — the GATE L0 table.

    The gate counts PRINTS. A revision-only release (February CPI/PPI seasonal
    recalculation, late-April Census retail benchmark) is a real release but
    not a red-folder event, and inflating coverage with them would be lying to
    the gate.
    """
    rows = []
    for fam, exp in sorted(EXPECTED.items()):
        g = ev[ev["family"] == fam]
        prints = int((g["release_kind"] == "print").sum())
        susp = ADJ_COUNT.get(fam, len(ADJUSTMENTS.get(fam, [])))
        adj = exp - susp
        rows.append(dict(
            family=fam, tier=RELEASES[fam]["tier"], expected=exp,
            adjust=susp, adj_expected=adj, prints=prints,
            revision_only=int((g["release_kind"] == "revision_only").sum()),
            pct_adj=round(100.0 * prints / adj, 1) if adj else None,
            needs_verification=int(g["needs_verification"].sum()),
            gate_95=("PASS" if adj and prints >= 0.95 * adj else "FAIL")))
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
