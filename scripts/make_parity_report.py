#!/usr/bin/env python3
"""Step-4 PARITY GATE report (spec-1 Section 4, Step 4 check).

Loads data/nq_1m.parquet and, for the two gate timestamps

    2026-02-11 09:48 ET  (hand-log trade: SHORT, entry TF 3M)
    2026-02-17 09:50 ET  (hand-log trade: SHORT, entry TF 2M)

computes every gate indicator via ``src.engine.indicators.indicators_asof`` and writes
``output/parity_report.md`` with blank columns for Angus to fill in from the reference
charts. Each |engine − chart| delta must be <= 1.0 NQ point to pass the gate.

Usage:  python3 scripts/make_parity_report.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.engine.indicators import indicators_asof, load_indicators_config  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "nq_1m.parquet"
OUT = REPO / "output" / "parity_report.md"
TZ = "America/New_York"
GATE_TOLERANCE_PTS = 1.0  # spec-1 Step 4 check: within 1.0 NQ point of the chart value

# (timestamp, hand-log context) — spec-1 Step 4; TFs from data/reference/feb2026_hand_log.csv
GATES = [
    (pd.Timestamp("2026-02-11 09:48", tz=TZ),
     "Angus traded the **3M** entry TF this day (short, 09:48) — check the 3min BB row first."),
    (pd.Timestamp("2026-02-17 09:50", tz=TZ),
     "Angus traded the **2M** entry TF for the 09:50 trade (short) — check the 2min BB row first."),
]


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.2f}"


def _rows_for(snap: dict) -> list[tuple[str, float | None]]:
    rows = [(f"BB basis {tf}", snap["tfs"][tf]["bb_basis"])
            for tf in ("1min", "2min", "3min", "5min")]
    rows += [
        ("Daily VWAP mid", snap["daily_vwap"]["mid"]),
        ("Daily VWAP +1σ", snap["daily_vwap"]["upper_1"]),
        ("Daily VWAP −1σ", snap["daily_vwap"]["lower_1"]),
        ("NY VWAP mid", snap["ny_vwap"]["mid"]),
        ("Daily POC (as-of)", None if snap["daily_profile"] is None
         else snap["daily_profile"]["poc"]),
    ]
    return rows


def _table(snap: dict) -> str:
    lines = ["| Level | Engine value | Angus chart value | Δ | within 1.0 pt? |",
             "|---|---|---|---|---|"]
    for name, val in _rows_for(snap):
        lines.append(f"| {name} | {_fmt(val)} | ___ | ___ | ___ |")
    return "\n".join(lines)


def _bar_ts_line(snap: dict) -> str:
    parts = [f"{tf}: {snap['tfs'][tf]['bar_ts'].strftime('%H:%M')}"
             for tf in ("1min", "2min", "3min", "5min")]
    return ", ".join(parts)


def main() -> None:
    cfg = load_indicators_config(REPO / "config" / "strategy.yaml")
    df = pd.read_parquet(PARQUET)

    sections = []
    printed = []
    for ts, tf_note in GATES:
        # Gate value = as of the CLOSE of the named 1m candle (Angus-confirmed convention):
        # the gate bar stamped `ts` is INCLUDED. It closes at ts+1min, so evaluate there.
        # indicators_asof stays a pure "as of instant T" primitive; the +1min lives here.
        asof = ts + pd.Timedelta(minutes=1)
        snap = indicators_asof(df, asof, cfg)
        sections.append(
            f"## {ts.strftime('%A %B %d, %Y — %H:%M ET')}\n\n"
            f"{tf_note}\n\n"
            f"Values are as of the CLOSE of the {ts.strftime('%H:%M')} candle — the gate candle "
            f"is INCLUDED (it closed at {asof.strftime('%H:%M')}). Last CLOSED bar used per TF "
            f"(bar stamp): {_bar_ts_line(snap)}.\n\n"
            f"{_table(snap)}\n")
        printed.append((ts, _rows_for(snap), snap))

    conventions = f"""## Conventions (what the engine computed, so chart comparison is apples-to-apples)

- **Gate-candle-CLOSE semantics (Angus-confirmed):** every value is taken as of the
  CLOSE of the named gate candle — the 09:48 / 09:50 1m bar is INCLUDED (it closes one
  minute later). Resampled 2m/3m/5m frames are close-labeled (built only from
  already-closed 1m bars; trailing partial bins dropped) — the exact bars used are listed
  above each table. On the chart: hover the **named candle** (confirm its close matches
  the gate close) and read that completed candle's indicator values.
- **Bollinger Bands:** BB(20, SMA of close, 2.0σ), population stdev — TradingView
  ``ta.stdev`` — computed per entry TF (§2).
- **VWAP source:** hlc3 = (high+low+close)/3 per 1m bar — standard TradingView VWAP (§2).
- **VWAP band stdev:** VOLUME-WEIGHTED around the running VWAP
  (var = Σ(vol·src²)/Σ(vol) − vwap²), NOT a simple rolling stdev (spec-1 §3).
- **Anchors:** daily VWAP resets at the CME daily session open **18:00 ET**; NY VWAP
  anchors **09:30 ET** and does not exist pre-market (§2/§3).
- **Daily POC:** DEVELOPING (as-of) profile of the current CME session (18:00 boundary),
  built from 1m bars closed at the timestamp, volume spread uniformly across each bar's
  [low, high] range in **0.25-pt bins**; POC = center of the max-volume bin. On the
  chart: use the session volume profile *as of that time* if available; the end-of-day
  profile will differ.
- **Entry TF per the hand log:** Feb 11 = **3M**, Feb 17 09:50 = **2M** — check that BB
  row first; the others are secondary.

## Gate instruction

Angus: fill in the chart value for every row, plus Δ = engine − chart and whether
|Δ| <= {GATE_TOLERANCE_PTS:.1f} NQ point. **Every row must be within {GATE_TOLERANCE_PTS:.1f}
NQ point to pass.** Per spec-1 Step 4: **DO NOT proceed to Step 5 (snapshot builder)
without sign-off on this report.**
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("# Step 4 Parity Report — engine vs reference charts\n\n"
                   "Spec-1 Step 4 PARITY GATE. Engine values below; Angus fills the "
                   "blank columns from the reference charts.\n\n"
                   + "\n".join(sections) + "\n" + conventions)

    for ts, rows, _ in printed:
        print(f"\n{ts}:")
        for name, val in rows:
            print(f"  {name:>18}: {_fmt(val)}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
