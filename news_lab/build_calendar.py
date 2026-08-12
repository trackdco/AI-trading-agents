"""Forward US high-impact release calendar — what to trade, and when.

    FRED_API_KEY=... python news_lab/build_calendar.py --months 6

Writes news_lab/output/us_calendar.{csv,json,parquet}: one row per upcoming
US release, with the release timestamp in ET and in UTC, ready for an agent to
schedule research against.

US ONLY by construction — every source here is a US agency (BLS, BEA, Census,
Federal Reserve, DOL) plus ADP. No foreign releases exist in this pipeline.

Dates come from the official schedules, never a rule, with two flagged
exceptions (ISM, UMich prelim) called out in the `note` column and marked
needs_verification. Nothing is invented; a source that fails raises.
"""
from __future__ import annotations
import sys
import os
import json
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newslab.events import (            # noqa: E402
    scrape_fomc, fred_release_dates, build_ism, assemble,
    scrape_bea_schedule)
from newslab.config import TZ_ET        # noqa: E402

# What "high impact" means here, and why. HIGH = reliably moves NQ on the
# print; MEDIUM = tradeable but second-tier. Ordered by mover size.
IMPACT = {
    "cpi":     ("HIGH",   "Consumer Price Index",
                "#1 NQ mover this cycle; algos read the unrounded 2nd decimal"),
    "nfp":     ("HIGH",   "Employment Situation (Non-Farm Payrolls)",
                "Three surprises (payrolls, unemployment, earnings) can conflict"),
    "fomc":    ("HIGH",   "FOMC rate decision",
                "Two-phase: 14:00 statement, 14:30 presser. sep=True adds dots"),
    "pce":     ("HIGH",   "Personal Income & Outlays (Core PCE)",
                "The Fed's preferred gauge; mostly pre-priced off CPI+PPI"),
    "ppi":     ("HIGH",   "Producer Price Index",
                "Hits hardest when it confirms or contradicts CPI"),
    "retail":  ("MEDIUM", "Advance Retail Sales",
                "Control group is the read-through, not the headline"),
    "ism_mfg": ("MEDIUM", "ISM Manufacturing PMI",
                "Lands INSIDE RTH — different liquidity than an 08:30 print"),
    "ism_svc": ("MEDIUM", "ISM Services PMI",
                "Often the bigger mover of the two ISMs"),
    "claims":  ("MEDIUM", "Initial Jobless Claims",
                "Weekly. Rarely moves alone; matters in a labour-scare regime"),
    "gdp_adv": ("MEDIUM", "GDP (ADVANCE estimate)",
                "The only GDP print that moves; confirmed against BEA's schedule"),
    "jolts":   ("MEDIUM", "JOLTS Job Openings",
                "Lands INSIDE RTH. Fed watches it for labour slack"),
    "adp":     ("MEDIUM", "ADP National Employment",
                "08:15 — the only pre-08:30 print; sets tone into NFP week"),
    "umich_prelim": ("MEDIUM", "UMich Consumer Sentiment (preliminary)",
                "Inflation-expectations sub-index moves more than the headline"),
    "umich":   ("LOW",    "UMich Consumer Sentiment (final)",
                "Final revision — the preliminary two weeks earlier is the mover"),
    "gdp_est": ("LOW",    "GDP (2nd/3rd estimate)",
                "Dead event per SPEC — the ADVANCE is the only GDP that moves"),
}

FRED_FAMILIES = ["cpi", "ppi", "nfp", "pce", "retail", "gdp_adv", "claims",
                 "jolts", "adp", "umich"]


def build(months: int = 6, today: str | None = None) -> pd.DataFrame:
    start = today or pd.Timestamp.today().strftime("%Y-%m-%d")
    end = (pd.Timestamp(start) + pd.DateOffset(months=months)
           ).strftime("%Y-%m-%d")
    frames = []

    print(f"window {start} → {end}", flush=True)
    print("[fomc]  federalreserve.gov …", flush=True)
    f = scrape_fomc()
    frames.append(f[(f["date"] >= start) & (f["date"] <= end)])

    for fam in FRED_FAMILIES:
        print(f"[{fam}] FRED …", flush=True)
        # classify=False: a future release has no first print yet, so the
        # print/revision test cannot run and must not be faked.
        df = fred_release_dates(fam, start, end, classify=False,
                                include_no_data=True)
        frames.append(df)

    print("[ism]   1st/3rd federal business day rule …", flush=True)
    ism = build_ism(start, end)
    frames.append(ism[(ism["date"] >= start) & (ism["date"] <= end)])

    # UMich publishes TWICE a month and FRED lists only the final. The
    # PRELIMINARY (2nd Friday) is the mover, so derive it and flag it as a rule.
    # Validated against sca.isr.umich.edu, which shows the next release on the
    # 2nd Friday; FRED's date for the same month is the 4th Friday.
    fridays = pd.date_range(start, end, freq="W-FRI")
    prelim = [d for d in fridays if 8 <= d.day <= 14]
    frames.append(pd.DataFrame([
        dict(family="umich_prelim", date=d.strftime("%Y-%m-%d"),
             time_et="10:00", sep=False, source="rule_2nd_friday",
             needs_verification=True) for d in prelim]))

    ev = assemble(frames)
    ev = ev[(ev["date"] >= start) & (ev["date"] <= end)].copy()

    # FRED bundles GDP advance/2nd/3rd under one release id. BEA's own schedule
    # names the advance explicitly, so use it; past BEA's coverage fall back to
    # the published cadence (advance lands in Jan/Apr/Jul/Oct) and flag it.
    try:
        bea = scrape_bea_schedule()
        adv = set(bea.loc[bea["family"] == "gdp_adv", "date"])
        bea_max = max(bea["date"]) if len(bea) else ""
    except Exception as e:                          # noqa: BLE001
        print(f"[gdp]   BEA schedule unavailable ({e}); month-rule only")
        adv, bea_max = set(), ""
    g = ev["family"] == "gdp_adv"
    month = pd.to_datetime(ev["date"]).dt.month
    is_adv = ev["date"].isin(adv) | (~ev["date"].le(bea_max)
                                     & month.isin([1, 4, 7, 10]))
    ev.loc[g & ~is_adv, "family"] = "gdp_est"       # 2nd/3rd — dead events
    ev.loc[g & is_adv & ~ev["date"].isin(adv), "needs_verification"] = True

    ev["impact"] = ev["family"].map(lambda f: IMPACT[f][0])
    ev["name"] = ev["family"].map(lambda f: IMPACT[f][1])
    ev["note"] = ev["family"].map(lambda f: IMPACT[f][2])
    ev["ts_utc"] = ev["ts_release_et"].dt.tz_convert("UTC")
    ev["weekday"] = ev["ts_release_et"].dt.day_name()

    # Honest flags on the two families whose dates are not from an official
    # schedule, so an agent never treats them as confirmed.
    ism_m = ev["family"].isin(["ism_mfg", "ism_svc"])
    ev.loc[ism_m, "note"] += (" | DATE IS RULE-DERIVED: ISM is behind a login "
                              "wall, confirm on ismworld.org before trading")
    up = ev["family"] == "umich_prelim"
    ev.loc[up, "note"] += (" | DATE IS RULE-DERIVED (2nd Friday): UMich "
                           "publishes no machine-readable schedule")

    cols = ["ts_release_et", "ts_utc", "date", "weekday", "time_et", "family",
            "name", "impact", "sep", "needs_verification", "source", "note"]
    return ev[cols].sort_values("ts_release_et").reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--today", default=None, help="override 'now' (YYYY-MM-DD)")
    ap.add_argument("--outdir", default="news_lab/output")
    ap.add_argument("--high-only", action="store_true")
    a = ap.parse_args()

    cal = build(a.months, a.today)
    if a.high_only:
        cal = cal[cal["impact"] == "HIGH"].reset_index(drop=True)
    os.makedirs(a.outdir, exist_ok=True)
    base = os.path.join(a.outdir, "us_calendar")
    cal.to_parquet(f"{base}.parquet", index=False)
    out = cal.copy()
    out["ts_release_et"] = out["ts_release_et"].astype(str)
    out["ts_utc"] = out["ts_utc"].astype(str)
    out.to_csv(f"{base}.csv", index=False)
    json.dump(out.to_dict("records"), open(f"{base}.json", "w"), indent=2)

    print(f"\nwrote {base}.{{parquet,csv,json}} — {len(cal)} events\n")
    print(cal.groupby(["impact", "family"]).size().to_string())

    # An agency only publishes its schedule so far ahead. Saying nothing here
    # would let an agent read "no CPI in January" as fact rather than as "not
    # announced yet", which is the difference between a quiet week and a
    # missed print.
    window_end = cal["date"].max()
    short = []
    for fam, g in cal.groupby("family"):
        last = g["date"].max()
        if last < window_end and fam not in ("gdp_adv",):
            short.append((fam, last))
    if short:
        print("\nCOVERAGE HORIZON — these families are confirmed only to the "
              "date shown;\nlater dates are NOT YET PUBLISHED by the agency, "
              "not absent:")
        for fam, last in sorted(short, key=lambda x: x[1]):
            print(f"   {fam:14s} confirmed through {last}")
        print("   Re-run this script when the agencies post next year's "
              "schedules.")
    print("\nNEXT 15:")
    nxt = cal.head(15)[["date", "weekday", "time_et", "impact", "name"]]
    print(nxt.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
