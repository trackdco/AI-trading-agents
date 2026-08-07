#!/usr/bin/env python3
"""L3 LONDON — order flow ON THE ENTRY CANDLE, timeframe-aware.

ANGUS 2026-08-05:

    "we have to run the order flow variables at entry with market displacement through
     levels. Full winner vs loser separation study again... If we can capture the ones that
     win and dismiss the losers, it's profitable. The entry mechanism is the core but
     there's so many layers we validate against"

AND HE IS RIGHT THAT THIS HAD NOT BEEN RUN. The L3 battery carried `fill_delta` (the one
minute before the fill), `d5`, `d15`, `d30` — fixed windows ending before the fill. NONE of
them is the flow ON the trigger candle. For a 3-minute displacement closing at T, the candle
being entered off spans (T-3, T]; the battery measured the minute before it and the half
hour around it, and never the thing itself. The null that failed on the displacement half
did not test this class.

WHY THIS IS ONLY ASKABLE NOW. Under EC the displacement is a MARKET entry at that candle's
close, so the candle's own flow is information held AT the decision, in full, with nothing
after it. Under the old retest entry the same measurement would have been a lookahead
dressed as a feature.

EVERY WINDOW IS TIMEFRAME-AWARE. A 1-minute trigger gets 1 minute of tape, a 5-minute
trigger gets 5. Using a fixed window would compare a 5-minute candle's flow against a
1-minute candle's flow and call the difference a signal.

FEATURES (all direction-signed, all strictly at-or-before the trigger close):

  trig_delta        signed delta over the trigger candle's own minutes
  trig_delta_conf   does that delta agree with the trade direction
  trig_delta_frac   |delta| / volume on the candle -- conviction, not size
  trig_vol_rel      candle volume vs the session's per-minute median x TF
  trig_accel        candle delta vs the immediately preceding equal-length window
  trig_absorb       high volume AND low delta fraction -- size absorbed, move not confirmed
  prev_delta_conf   the preceding equal-length window's delta vs direction (context)

    python -m scripts.l3_london_trigger_flow --entry EC
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.score_canon_span import minute_tape  # noqa: E402

NY = "America/New_York"
TF_MIN = {"1min": 1, "2min": 2, "3min": 3, "5min": 5}


def add(F: pd.DataFrame, M: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(F["ts"], utc=True, format="mixed").dt.tz_convert(NY)
    out = []
    for i, (t, tf, d) in enumerate(zip(ts, F["tf"], F["direction"])):
        n = TF_MIN.get(tf, 1)
        sgn = 1.0 if d == "long" else -1.0
        # the trigger candle is CLOSE-labeled: bar stamped t covers (t - n*1min, t]
        cur = M.loc[t - pd.Timedelta(minutes=n - 1): t]
        prv = M.loc[t - pd.Timedelta(minutes=2 * n - 1): t - pd.Timedelta(minutes=n)]
        r: dict = {}
        if len(cur):
            dl, vol = float(cur.delta.sum()), float(cur.vol.sum())
            r["trig_delta"] = dl * sgn
            r["trig_delta_conf"] = float(np.sign(dl) == sgn)
            r["trig_delta_frac"] = abs(dl) / max(vol, 1.0)
            sess = M.loc[: t].tail(240)
            med = float(sess.vol.median()) if len(sess) else np.nan
            r["trig_vol_rel"] = vol / max(med * n, 1.0) if med == med else np.nan
            if len(prv):
                pd_ = float(prv.delta.sum())
                r["trig_accel"] = (dl - pd_) * sgn
                r["prev_delta_conf"] = float(np.sign(pd_) == sgn)
            # absorption: heavy volume, weak directional conviction
            r["trig_absorb"] = float((r.get("trig_vol_rel", 0) or 0) > 1.5
                                     and r["trig_delta_frac"] < 0.10)
        out.append(r)
        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{len(F)}", flush=True)
    X = pd.DataFrame(out, index=F.index)
    return pd.concat([F, X], axis=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="EC")
    a = ap.parse_args()
    p = ROOT / (f"output/l3_features_london_fit_{a.entry}.parquet" if a.entry != "E3"
                else "output/l3_features_london_fit.parquet")
    F = pd.read_parquet(p)
    F = F.drop(columns=[c for c in F.columns
                        if c.startswith(("trig_delta", "trig_vol", "trig_accel",
                                         "trig_absorb", "prev_delta"))], errors="ignore")
    M = minute_tape({"tape": "output/fp_minutes.parquet"})
    print(f"adding trigger-candle flow to {len(F):,} rows", flush=True)
    F = add(F, M)
    F.to_parquet(p, index=False)
    new = [c for c in F.columns if c.startswith(("trig_", "prev_"))]
    print(f"\nwrote {p.relative_to(ROOT)} — {len(new)} new columns: {new}")
    for c in new:
        print(f"  {c:<18} resolved {F[c].notna().mean():.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
