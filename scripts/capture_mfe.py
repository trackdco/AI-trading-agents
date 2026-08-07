#!/usr/bin/env python3
"""Capture ceiling for the CANON book (agents-capture test, HANDOFF-agents-capture §3.2).

Same walk as scripts/l2_mfe_walk.py but over `funded_book.load_book(span)` — the canonical
wall-cut book the agents will manage — and for BOTH spans, so the capture ratio
(realized R / MFE R) has a holdout-confirmable denominator built from bar data that exists
in 2023/24 as well (no fp_minutes dependency).

Per trade: in-trade MFE/MAE (fill -> engine exit), MFE to 15:55, minutes to peak, giveback,
and the hold-to-close reference (original stop, no target, stop-first same-bar — the
"doing nothing" fact, never a proposal).

    python -m scripts.capture_mfe --span fit
    python -m scripts.capture_mfe --span holdout
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars  # noqa: E402
from scripts import funded_book as fb  # noqa: E402

NY = "America/New_York"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", required=True, choices=["fit", "holdout"])
    a = ap.parse_args()

    V = fb.load_book(a.span)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    B = bars.set_index("mi").sort_index()
    bday = B.index.strftime("%Y-%m-%d")

    rows = []
    for day, g in V.groupby("day", sort=True):
        db = B[bday == day]
        if not len(db):
            print(f"  {day}: NO BARS", flush=True)
            continue
        h, lo, cl = db.high.to_numpy(), db.low.to_numpy(), db.close.to_numpy()
        mi = db.index
        eod_i = int(np.searchsorted(mi, pd.Timestamp(f"{day} 15:55", tz=NY), side="right"))
        for r in g.itertuples():
            s = 1 if r.direction == "long" else -1
            fill = r.fill                       # load_book already parsed (mixed-DST safe)
            exit_ts = r.exit
            i0 = int(np.searchsorted(mi, fill, side="left"))
            iex = int(np.searchsorted(mi, exit_ts, side="right"))
            risk = float(r.risk)                # ENGINE bracket |limit - stop_initial|
            if risk <= 0 or i0 >= eod_i:
                continue
            fav = s * (h[i0:eod_i] - r.entry) if s == 1 else s * (lo[i0:eod_i] - r.entry)
            adv = s * (lo[i0:eod_i] - r.entry) if s == 1 else s * (h[i0:eod_i] - r.entry)
            fav_in = fav[: max(iex - i0, 1)]
            adv_in = adv[: max(iex - i0, 1)]
            R_real = float(r.dollars_1lot) / (risk * 20.0)
            stop_hit = np.nonzero(adv <= -risk)[0]
            if len(stop_hit):
                hold_R = -1.0
                peak_eod = float(fav[: stop_hit[0] + 1].max()) / risk
            else:
                hold_R = float(s * (cl[eod_i - 1] - r.entry)) / risk
                peak_eod = float(fav.max()) / risk
            ipk = int(np.argmax(fav_in))
            rows.append({
                "day": day, "ts": r.ts, "direction": r.direction, "sess": r.sess,
                "tier": float(r.tier), "elite": bool(r.elite), "era": r.era,
                "struct_event": r.struct_event, "fill_ts": str(r.fill_ts), "risk": risk,
                "R_v8": round(R_real, 4),
                "mfe_R": round(float(fav_in.max()) / risk, 3),
                "mae_R": round(float(adv_in.min()) / risk, 3),
                "mfe_R_eod": round(peak_eod, 3),
                "mins_to_peak": ipk,
                "giveback_R": round(float(fav_in.max()) / risk - R_real, 3),
                "hold_R": round(hold_R, 3)})
    F = pd.DataFrame(rows)
    out = ROOT / f"output/capture_mfe_{a.span}.parquet"
    F.to_parquet(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} of {len(V)} canon trades")
    print(f"mean realized R {F.R_v8.mean():+.3f} | in-trade MFE {F.mfe_R.mean():.3f} | "
          f"MFE-to-EOD {F.mfe_R_eod.mean():.3f} | hold-to-close {F.hold_R.mean():+.3f}")
    for (era, sess), g in F.groupby(["era", "sess"]):
        print(f"  {era}·{sess}: n={len(g)} realized {g.R_v8.mean():+.2f} "
              f"MFE {g.mfe_R.mean():.2f} eodMFE {g.mfe_R_eod.mean():.2f}")


if __name__ == "__main__":
    main()
