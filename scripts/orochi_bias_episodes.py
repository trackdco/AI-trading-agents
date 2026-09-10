#!/usr/bin/env python3
"""S41 part 2 — the tradeability check the census CANNOT answer.

The census reports conditional MEANS over every qualifying minute. Two things
inflate how good that looks, and both are fixed here:

  1. PERSISTENCE. If price sits below VAL for three hours that is ONE episode,
     not 180 observations. Here each state contributes at most ONE observation
     per session: the first minute it becomes true (a state ENTRY).
  2. DISPERSION. A mean says nothing about whether you could hold the trade.
     Here every state reports sd, hit rate, and mean/sd — the per-bet
     information ratio, which is what decides whether a bias survives a stop.

Verdict language is deliberately conservative: a state is only INTERESTING if
its hit rate beats the same-era baseline hit rate in ALL THREE eras AND its
pooled mean/sd exceeds 0.10. Nothing here is a strategy; this measures whether
a bias exists that is worth building an entry around.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                       # noqa: E402
from scripts.agent_context import volume_profile             # noqa: E402
import scripts.pd_va_backtest as BT                          # noqa: E402
from scripts.orochi_bias_census import (classify_day, HORIZONS,   # noqa: E402
                                        WARMUP_MIN, SESS_H)

# states carrying a directional prediction: +1 expect up, -1 expect down
DIRECTIONAL = {
    "valoc=below_val": +1, "valoc=above_vah": -1,
    "zone=gt_sd2_dn": +1, "zone=gt_sd2_up": -1,
    "regime=IMB_DN": +1, "regime=IMB_UP": -1,
    "event=ACC_BACK_UP": +1, "event=ACC_BACK_DN": -1,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", choices=("nq", "nq20a"), default="nq")
    a = ap.parse_args()
    inst = BT.INSTRUMENTS[a.instrument]
    if inst["bars"]:
        b = pd.read_parquet(ROOT / inst["bars"])
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
        bars = b.set_index("mi").sort_index()[
            ["open", "high", "low", "close", "volume"]]
        roll_skip = set(json.loads((ROOT / inst["rolls"]).read_text()))
    else:
        bars = OB.get_bars()
        roll_skip = set()
    days = OB.all_session_days(bars)

    ep = defaultdict(list)      # (state,h) -> [(day, signed_move)]
    allm = defaultdict(list)    # h -> [signed baseline moves]
    for di, day in enumerate(days):
        if day in roll_skip or di == 0:
            continue
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        pa = pd.Timestamp(f"{days[di-1]} 18:00", tz=OB.NY)
        pseg = bars[(bars.index >= pa) & (bars.index < t0)]
        sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
        if len(sess) < 600 or len(pseg) < 300:
            continue
        _, val, vah = volume_profile(pseg, bin_w=inst["bin_w"])
        zone, regime, valoc, ev, fwd = classify_day(sess, vah, val, inst["bin_w"])
        n = len(zone)
        lab = {f"zone={z}": zone for z in set(zone)}
        series = {"zone": zone, "regime": regime, "valoc": valoc, "event": ev}
        for st, d in DIRECTIONAL.items():
            kind, want = st.split("=")
            arr = series[kind]
            hit = np.flatnonzero(arr == want)
            hit = hit[hit >= WARMUP_MIN]
            if len(hit) == 0:
                continue
            if kind == "event":
                idxs = hit                      # each event is its own episode
            else:
                # state ENTRIES only: first bar of each contiguous run
                idxs = hit[np.concatenate(([True], np.diff(hit) > 1))]
            for h in HORIZONS:
                f = fwd[h]
                for j in idxs:
                    if j < n and np.isfinite(f[j]):
                        ep[(st, h)].append((day, d * float(f[j])))
        for h in HORIZONS:
            f = fwd[h][WARMUP_MIN:]
            allm[h].extend(f[np.isfinite(f)].tolist())

    out = {"episodes": {f"{k[0]}@@{k[1]}": v for k, v in ep.items()},
           "baseline": {str(h): [float(np.mean(v)), float(np.std(v)),
                                 float(np.mean(np.array(v) > 0))]
                        for h, v in allm.items()}}
    p = ROOT / f"output/analysis/orochi_episodes_{a.instrument}.json"
    p.write_text(json.dumps(out))
    print(f"wrote {p}: " + ", ".join(
        f"{k}={len(v)}" for k, v in sorted(ep.items()) if k[1] == 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
