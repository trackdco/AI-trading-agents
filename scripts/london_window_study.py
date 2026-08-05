#!/usr/bin/env python3
"""LDN-WIN-01 — London session window study.

Authorised by docs/PREREG-london-window-study.md, filed 2026-08-05 before this
ran. Measurement only: no entries, no exits, no P&L.

Question: is the NQ London opportunity concentrated 1h before the European open
to 1h after (~02:00-05:00 ET, the Tradesharpe claim), or in our substrate's
03:00-06:00 ET window?

    python -m scripts.london_window_study            # report to stdout + output/
    python -m scripts.london_window_study --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BARS = REPO / "data/reference/nq_1m_master.parquet"
FEATURES = REPO / "output/london_day_features.parquet"
OUT = REPO / "output/london_window_study.md"

BUCKET_MIN = 30
DAY_START, DAY_END = "00:00", "07:00"


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    bars = pd.read_parquet(BARS)
    bars["ts_event"] = pd.to_datetime(bars["ts_event"])
    bars["day"] = bars["ts_event"].dt.strftime("%Y-%m-%d")
    bars["minute"] = bars["ts_event"].dt.hour * 60 + bars["ts_event"].dt.minute
    feats = pd.read_parquet(FEATURES)
    return bars, feats


def era_of(day: str) -> str | None:
    """Declared eras only. 2023/24 is untouched — it is the sealed holdout."""
    if day.startswith("2025"):
        return "2025"
    if day.startswith("2026"):
        return "2026"
    return None


def bucket_stats(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    """Realised range, displacement, efficiency and volume per bucket."""
    grouped = frame.groupby(["day", key])
    agg = grouped.agg(
        hi=("high", "max"),
        lo=("low", "min"),
        first=("open", "first"),
        last=("close", "last"),
        vol=("volume", "sum"),
    ).reset_index()
    agg["range_pts"] = agg["hi"] - agg["lo"]
    agg["disp_pts"] = (agg["last"] - agg["first"]).abs()
    # Direction-agnostic: how much of the travel actually went somewhere.
    agg["efficiency"] = (agg["disp_pts"] / agg["range_pts"]).where(agg["range_pts"] > 0)
    return agg


def summarise(agg: pd.DataFrame, key: str) -> pd.DataFrame:
    agg = agg.copy()
    agg["era"] = agg["day"].map(era_of)
    agg = agg[agg["era"].notna()]
    out = (
        agg.groupby(["era", key])
        .agg(
            days=("day", "nunique"),
            range_med=("range_pts", "median"),
            disp_med=("disp_pts", "median"),
            eff_med=("efficiency", "median"),
            vol_med=("vol", "median"),
        )
        .reset_index()
    )
    return out


def hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    bars, feats = load()
    start = int(DAY_START[:2]) * 60
    end = int(DAY_END[:2]) * 60
    window = bars[(bars["minute"] >= start) & (bars["minute"] < end)].copy()

    # ---- clock-anchored -------------------------------------------------
    window["clock_bucket"] = (window["minute"] // BUCKET_MIN) * BUCKET_MIN
    clock = summarise(bucket_stats(window, "clock_bucket"), "clock_bucket")

    # ---- event-anchored (relative to that day's measured European open) --
    euro = feats[["day", "euro_open_det", "euro_open_clock", "dst_mismatch"]].copy()
    euro = euro[euro["euro_open_det"].notna() & (euro["euro_open_det"] != "")]
    euro["euro_min"] = euro["euro_open_det"].str.slice(0, 2).astype(int) * 60 + euro[
        "euro_open_det"
    ].str.slice(3, 5).astype(int)
    merged = window.merge(euro[["day", "euro_min", "dst_mismatch"]], on="day", how="inner")
    merged["offset"] = merged["minute"] - merged["euro_min"]
    merged = merged[(merged["offset"] >= -120) & (merged["offset"] < 180)]
    # Floor-divide keeps negative offsets in the correct bucket.
    merged["event_bucket"] = (merged["offset"] // BUCKET_MIN) * BUCKET_MIN
    event = summarise(bucket_stats(merged, "event_bucket"), "event_bucket")

    # ---- the declared comparison ----------------------------------------
    def band(frame: pd.DataFrame, era: str, lo: int, hi: int) -> dict:
        sel = frame[(frame["era"] == era) & (frame["clock_bucket"] >= lo)
                    & (frame["clock_bucket"] < hi)]
        return {
            "range_med": round(float(sel["range_med"].median()), 2),
            "eff_med": round(float(sel["eff_med"].median()), 4),
            "vol_med": int(sel["vol_med"].median()) if len(sel) else 0,
        }

    verdict = {}
    for era in ("2025", "2026"):
        his = band(clock, era, 2 * 60, 5 * 60)      # 02:00-05:00 — Tradesharpe
        ours_tail = band(clock, era, 5 * 60, 6 * 60)  # 05:00-06:00 — ours only
        early = band(clock, era, 2 * 60, 3 * 60)      # 02:00-03:00 — his only
        verdict[era] = {"his_window_0200_0500": his,
                        "our_tail_0500_0600": ours_tail,
                        "his_extra_0200_0300": early,
                        "H1_range": his["range_med"] > ours_tail["range_med"],
                        "H1_efficiency": his["eff_med"] > ours_tail["eff_med"]}

    def spread(frame: pd.DataFrame, key: str, era: str) -> float:
        sel = frame[frame["era"] == era]
        return round(float(sel["range_med"].max() / sel["range_med"].min()), 3) if len(sel) else 0.0

    h2 = {era: {"clock_peak_ratio": spread(clock, "clock_bucket", era),
                "event_peak_ratio": spread(event, "event_bucket", era)}
          for era in ("2025", "2026")}
    for era in h2:
        h2[era]["H2_event_tighter"] = h2[era]["event_peak_ratio"] > h2[era]["clock_peak_ratio"]

    report = {"verdict_H1": verdict, "verdict_H2": h2,
              "clock": clock.to_dict("records"), "event": event.to_dict("records")}

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    lines = ["# LDN-WIN-01 — London window study (NQ)", "",
             "Authorised by `docs/PREREG-london-window-study.md`. Measurement only.",
             "Eras: discover 2025 / validate 2026. 2023/24 untouched.", "",
             "## Clock-anchored, 30-min buckets (median per bucket)", "",
             "| era | ET | days | range pts | displacement | efficiency | volume |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for r in clock.itertuples():
        lines.append(f"| {r.era} | {hhmm(int(r.clock_bucket))} | {r.days} | "
                     f"{r.range_med:.1f} | {r.disp_med:.1f} | {r.eff_med:.3f} | {int(r.vol_med):,} |")
    lines += ["", "## Event-anchored to measured European open (minutes offset)", "",
              "| era | offset | days | range pts | displacement | efficiency | volume |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for r in event.itertuples():
        lines.append(f"| {r.era} | {int(r.event_bucket):+d}m | {r.days} | "
                     f"{r.range_med:.1f} | {r.disp_med:.1f} | {r.eff_med:.3f} | {int(r.vol_med):,} |")
    lines += ["", "## Declared verdict", "", "```", json.dumps(
        {"H1": verdict, "H2": h2}, indent=2), "```"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwritten -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
