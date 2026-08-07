#!/usr/bin/env python3
"""Exit-study companion — MFE/MAE and the hold-to-close reference for every L2 fill.

ANGUS 30-Jul: *"based off of the old canon, the mean r was 2.1 but mean MFE was 7.1 so
massive gap there, which id rely on agents to fill rather than mechanics."* This measures
that gap ON THIS population, per fill:

  mfe_R / mae_R      best/worst excursion (vs original stop risk) between fill and exit
  mfe_R_eod, mins_to_peak, giveback_R (peak minus realized, the honest cost of the gap)
  hold_R             full position, ORIGINAL stop, no target, flatten 15:55 — the naive
                     ceiling reference (a fact about doing nothing, not a proposal)

Same-bar convention mirrors the engine's conservatism: when a bar touches both stop and
favorable ground, the stop counts first. 1-minute bars; excursions are bar extremes.

    python -m scripts.l2_mfe_walk
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars  # noqa: E402

NY = "America/New_York"


def main() -> None:
    O = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet")
    oc = O[O.status == "outcome"].copy()
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    B = bars.set_index("mi").sort_index()
    bday = B.index.strftime("%Y-%m-%d")

    rows = []
    for day, g in oc.groupby("day", sort=True):
        db = B[bday == day]
        h, lo, cl = db.high.to_numpy(), db.low.to_numpy(), db.close.to_numpy()
        mi = db.index
        eod_i = int(np.searchsorted(mi, pd.Timestamp(f"{day} 15:55", tz=NY), side="right"))
        for r in g.itertuples():
            s = 1 if r.direction == "long" else -1
            fill = pd.Timestamp(r.fill_ts)
            exit_ts = pd.Timestamp(r.exit_ts)
            i0 = int(np.searchsorted(mi, fill, side="left"))
            iex = int(np.searchsorted(mi, exit_ts, side="right"))
            risk = float(r.risk)
            if risk <= 0 or i0 >= eod_i:
                continue
            fav = s * (h[i0:eod_i] - r.entry) if s == 1 else s * (lo[i0:eod_i] - r.entry)
            adv = s * (lo[i0:eod_i] - r.entry) if s == 1 else s * (h[i0:eod_i] - r.entry)
            # in-trade (fill -> engine exit) excursions
            fav_in = fav[: max(iex - i0, 1)]
            adv_in = adv[: max(iex - i0, 1)]
            # hold arm: original stop, no target, flatten 15:55 — stop-first same-bar
            stop_hit = np.nonzero(adv <= -risk)[0]
            if len(stop_hit):
                hold_R = -1.0
                peak_eod = float(fav[: stop_hit[0] + 1].max()) / risk if stop_hit[0] >= 0 else 0.0
            else:
                hold_R = float(s * (cl[eod_i - 1] - r.entry)) / risk
                peak_eod = float(fav.max()) / risk
            ipk = int(np.argmax(fav_in))
            rows.append({
                "day": day, "ts": r.ts, "direction": r.direction, "fill_hm": r.fill_hm,
                "risk": risk, "R_v8": float(r.R),
                "mfe_R": round(float(fav_in.max()) / risk, 3),
                "mae_R": round(float(adv_in.min()) / risk, 3),
                "mfe_R_eod": round(peak_eod, 3),
                "mins_to_peak": ipk,
                "giveback_R": round(float(fav_in.max()) / risk - float(r.R), 3),
                "hold_R": round(hold_R, 3)})
        print(f"  {day}: {len(g)} fills", flush=True)
    F = pd.DataFrame(rows)
    F.to_parquet(ROOT / "output/l2_mfe_fit.parquet", index=False)
    print(f"\nwrote output/l2_mfe_fit.parquet — {len(F)} rows")
    print(f"mean realized R {F.R_v8.mean():+.2f} | mean in-trade MFE {F.mfe_R.mean():.2f} | "
          f"mean MFE-to-EOD {F.mfe_R_eod.mean():.2f} | mean hold-to-close {F.hold_R.mean():+.2f}")


if __name__ == "__main__":
    main()
