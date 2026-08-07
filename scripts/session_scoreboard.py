#!/usr/bin/env python3
"""Session-segmented prop scoreboard — displacement entries only.

ANGUS 2026-08-05: *"lets remove b2 entirely... make sure we just section off between
london, pre market and new york am when we optimise shit because the price action
dynamics are just different."*

He is right and the repo already proves it: the NY canon runs two separate books ("pre" and
"gold") with DIFFERENT checks and thresholds for exactly this reason, and the London canon
is a third. Pooling them averages three different markets into one meaningless number.

THREE SEGMENTS, by ET clock at the FILL:

  LONDON      03:00-05:00   (04:00-06:00 on DST-misaligned weeks; from the London census)
  PRE-MARKET  07:45-09:30   (from the NY census, whose band starts 07:45)
  NY AM       09:30-11:00

B2 (rejection blocks) are excluded everywhere. With B2 gone the entry-arm question
collapses — EC and E4 both market-enter displacements, so they are the same book here.

    python -m scripts.session_scoreboard
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.prop_score import HDR, row, score_book  # noqa: E402

NY = "America/New_York"

SOURCES = [
    ("LONDON", "output/l2_outcomes_london_fit_EC.parquet", 0, 24 * 60),
    ("PRE-MARKET", "output/l2_outcomes_fit_EC.parquet", 7 * 60 + 45, 9 * 60 + 30),
    ("NY AM", "output/l2_outcomes_fit_EC.parquet", 9 * 60 + 30, 11 * 60),
]


def load(path: str, lo: int, hi: int) -> pd.DataFrame | None:
    p = ROOT / path
    if not p.exists():
        return None
    O = pd.read_parquet(p)
    O = O[(O.status == "outcome") & (O.kind == "displacement")].copy()
    if "vs_first" in O.columns:                    # dedup where it has been derived
        O = O[O.vs_first]
    ts = pd.to_datetime(O.fill_ts, utc=True, format="mixed").dt.tz_convert(NY)
    hm = ts.dt.hour * 60 + ts.dt.minute
    return O[(hm >= lo) & (hm < hi)]


def main() -> int:
    L = ["# Session-segmented scoreboard — displacement entries, B2 removed", "",
         "Pooling sessions averages three different markets. The canon itself runs `pre`",
         "and `gold` as separate books with different checks; London is a third.", "", HDR]
    for name, path, lo, hi in SOURCES:
        D = load(path, lo, hi)
        if D is None:
            L.append(f"| {name} | — | — | — | — | — | — | — | — | not built yet |")
            continue
        L.append(row(name, score_book(D)))
        for era in ("2025", "2026"):
            E = D[D.day.str[:4] == era]
            if len(E) > 40:
                L.append(row(f"  {name} · {era}", score_book(E)))
    text = "\n".join(L)
    print(text)
    (ROOT / "output/session_scoreboard.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
