#!/usr/bin/env python3
"""RECLAIM trigger prototype (detector v2 candidate) — FIT ONLY, census first.

Born from the 2026-04-27 fidelity forensics: ANGUS's documented 09:33-09:36 long
(8pt stop, ~8R) does not exist in the census; the detector fired five SHORT
rejections into the flush he bought. The missing grammar:

    SWEEP-AND-RECLAIM: price trades >=1 tick beyond a REFERENCE EXTREME, and the
    TF candle CLOSES back through it. Direction = with the reclaim. The sweep's
    own extreme is the stop.

v0 reference extremes, bars-only (no new data): overnight high/low (18:00 prev
-> 08:00), prior-day high/low, opening-range high/low (the 09:30 1m bar).
TFs 1/2/3/5min, close-labeled; detection 07:45-11:00 ET; dedup one trigger per
(T, tf, ref_name, direction). Entry/stop/walk: identical displacement machinery
(next 1m open, sweep extreme -/+1 tick, stop-first to 15:55).

VALIDATION ANCHOR: must fire LONG on 2026-04-27 around 09:34-09:37 with a tight
stop, given nothing about that day. Anchor checked in output, never coded in.

    python -m scripts.l0_reclaim_prototype [--census-only]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_displacement_entry import NY, TICK, walk  # noqa: E402
from scripts.build_l2_outcomes import load_bars              # noqa: E402

TFS = [1, 2, 3, 5]
COST1 = 0.5


def day_refs(all_bars: pd.DataFrame, day: str) -> dict:
    d0 = pd.Timestamp(f"{day} 00:00", tz=NY)
    on = all_bars[(all_bars.mi >= d0 - pd.Timedelta(hours=6)) &
                  (all_bars.mi < d0 + pd.Timedelta(hours=8))]
    prev = all_bars[(all_bars.mi >= d0 - pd.Timedelta(hours=30)) &
                    (all_bars.mi < d0 - pd.Timedelta(hours=6))]
    o = all_bars[(all_bars.mi >= d0 + pd.Timedelta(hours=9, minutes=30)) &
                 (all_bars.mi < d0 + pd.Timedelta(hours=9, minutes=31))]
    refs = {}
    if len(on):
        refs["on_high"], refs["on_low"] = float(on.high.max()), float(on.low.min())
    if len(prev):
        refs["pd_high"], refs["pd_low"] = float(prev.high.max()), float(prev.low.min())
    if len(o):
        refs["or_high"], refs["or_low"] = float(o.high.max()), float(o.low.min())
    return refs


def main() -> None:
    census_only = "--census-only" in sys.argv
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars["day"] = bars.mi.dt.strftime("%Y-%m-%d")
    # HARD FIT GUARD (incident 2026-08-06, prereg §8a): load_bars() covers
    # 2023-2026 INCLUDING the sealed holdout. Detection days are restricted to
    # the fit span; prior-day/overnight refs may reach into earlier bars
    # (causal), but no trigger outside fit is scanned, walked, or saved.
    FIT_START, FIT_END = "2025-06-01", "2026-07-31"
    days = sorted(d for d in bars.day.unique()
                  if FIT_START <= d <= FIT_END
                  and bars[bars.day == d].mi.dt.hour.max() >= 10)

    rows = []
    for day in days:
        db = bars[bars.day == day]
        refs = day_refs(bars, day)
        if not refs:
            continue
        t0 = pd.Timestamp(f"{day} 07:45", tz=NY)
        t1 = pd.Timestamp(f"{day} 11:00", tz=NY)
        intr = db[(db.mi >= t0 - pd.Timedelta(minutes=6)) & (db.mi <= t1)]
        for tf in TFS:
            g = intr.set_index("mi").resample(f"{tf}min", label="right", closed="left").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
            g = g[(g.index > t0) & (g.index <= t1)]
            for name, ref in refs.items():
                if name.endswith("low"):
                    hit = (g.low <= ref - TICK) & (g.close > ref)
                    direction, stop_col = "long", "low"
                else:
                    hit = (g.high >= ref + TICK) & (g.close < ref)
                    direction, stop_col = "short", "high"
                # or_* refs only meaningful after 09:31
                sel = g[hit]
                for T, r in sel.iterrows():
                    if name.startswith("or_") and T <= pd.Timestamp(f"{day} 09:31", tz=NY):
                        continue
                    rows.append({"day": day, "T": T, "tf": tf, "ref_name": name,
                                 "ref": ref, "direction": direction,
                                 "sweep_ext": float(r[stop_col]),
                                 "close": float(r.close)})
    C = pd.DataFrame(rows).drop_duplicates(["day", "T", "tf", "ref_name", "direction"])
    assert C.day.min() >= FIT_START and C.day.max() <= FIT_END, "fit-guard violated"
    C["era"] = np.where(C.day.str[:4] == "2025", "2025", "2026")
    print(f"RECLAIM census: {len(C):,} triggers over {C.day.nunique()} days "
          f"({(C.era=='2025').sum():,} in 2025 / {(C.era=='2026').sum():,} in 2026)")
    print("by ref:", C.ref_name.value_counts().to_dict())

    a = C[(C.day == "2026-04-27") & (C.direction == "long")
          & (C["T"].dt.strftime("%H:%M") >= "09:30") & (C["T"].dt.strftime("%H:%M") <= "09:45")]
    print(f"\nVALIDATION ANCHOR 2026-04-27 09:30-09:45 longs: {len(a)} triggers")
    for r in a.itertuples():
        print(f"  {r.T:%H:%M} {r.tf}min reclaim of {r.ref_name} @ {r.ref:.2f} "
              f"(sweep ext {r.sweep_ext:.2f}, close {r.close:.2f}, "
              f"risk-to-sweep {abs(r.close - r.sweep_ext):.1f}pt)")
    C.to_parquet(ROOT / "output/l0_reclaim_census.parquet", index=False)
    if census_only:
        return

    bars_by_day = {d: g for d, g in bars.groupby("day")}
    out = []
    for r in C.itertuples():
        db = bars_by_day[r.day]
        sgn = 1 if r.direction == "long" else -1
        stop = r.sweep_ext - TICK if sgn > 0 else r.sweep_ext + TICK
        nxt = db[db.mi >= r.T]
        if nxt.empty:
            continue
        entry = float(nxt.iloc[0].open)
        w = walk(db, nxt.iloc[0].mi, entry, stop, sgn, r.day)
        if w is None:
            out.append({"day": r.day, "era": r.era, "tf": r.tf, "ref_name": r.ref_name,
                        "direction": r.direction, "risk": np.nan, "r_hold": -1.0,
                        "max_r": 0.0, "stopped_ever": True, "gap_loss": True})
            continue
        hm = nxt.iloc[0].mi.hour * 60 + nxt.iloc[0].mi.minute
        sess = "pre" if 480 <= hm < 570 else ("gold" if 580 <= hm < 630 else "other")
        out.append({"day": r.day, "era": r.era, "tf": r.tf, "ref_name": r.ref_name,
                    "direction": r.direction, "sess": sess, "gap_loss": False, **w})
    W = pd.DataFrame(out)
    W = W[W.risk >= 2.0]
    W["net"] = W.r_hold - COST1 / W.risk
    W.to_parquet(ROOT / "output/l0_reclaim_walked.parquet", index=False)
    print(f"\nwalked {len(W):,} (risk>=2pt), hold-to-close with sweep stop:")
    hdr = f"{'':<16}{'n':>6}{'stop%':>7}{'WR':>7}{'avg win':>9}{'R/tr net':>10}{'tot R':>8}"
    for key, G in (("BY YEAR", W.groupby("era")),
                   ("BY REF", W.groupby("ref_name")),
                   ("BY SESSION", W.groupby("sess"))):
        print(f"\n{key}\n{hdr}")
        for k, d in G:
            wn = d[d.r_hold > 0]
            print(f"{str(k):<16}{len(d):>6,}{d.stopped_ever.mean()*100:>6.0f}%"
                  f"{(d.r_hold>0).mean()*100:>6.1f}%{wn.r_hold.mean() if len(wn) else 0:>+9.2f}"
                  f"{d.net.mean():>+10.3f}{d.net.sum():>+8.0f}")
    print("\nFIT ONLY. New trigger family -> full meat grinder before anything "
          "is believed. HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
