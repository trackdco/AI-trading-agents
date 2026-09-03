#!/usr/bin/env python3
"""PD VA LOSS ANATOMY, ROUND 2 — the heavy-machinery pre-entry screen.

    python -m scripts.pd_va_features2

His ask (2026-09-03): test MORE pre-entry features on the final spec,
using the full toolkit. Population: news-gated champion trades (1m,
>=3pt, 1R, SAR, all sessions), n≈7.6k. All features as-of signal time.

PREREGISTERED VERDICT RULE (set before results were read): a feature is
a SURVIVOR only if (a) extreme-bucket ordering matches in both split
halves, (b) EV spread between extreme buckets >= 0.05R in BOTH halves,
(c) each extreme bucket has n >= 400 per half. Same direction but
smaller = WATCH. Anything else = NULL. ~30 cells are screened; ~1 false
"consistent" cell is expected by chance — the rule exists for that.

Features:
  vwap_rel    trade direction vs the level's side of session VWAP
              (fade_to_vwap = entering back toward vwap; extend = away)
  vwap_z      how stretched the level sits vs vwap in band-sigma units
  ma15_align  direction vs 15m BB MA slope (30-min lookback)
  wk_va       level vs the anchored weekly value area x direction
  sess_pos    level's position in the session's range so far
  chop        chop_state v2 at signal (window-local regime)
  touches     prior touches of the level this session (freshness)
  last_touch  minutes since price last traded at the level
  density     trades already taken today (tape pace)
  drift       direction vs the trailing-2h drift
  open_gap    session open vs PD value area x direction
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import anchored_weekly_profile         # noqa: E402
from scripts.chop_state import state_at                           # noqa: E402
from src.htf_ma.levels import bb_ma_asof, vwap_bands              # noqa: E402

MID = "2024-10-21"


def day_features(bars, day, trades):
    t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
    sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
    if len(sess) < 300:
        return
    ts = sess.index.view("int64")
    hi = sess.high.to_numpy()
    lo = sess.low.to_numpy()
    cl = sess.close.to_numpy()
    run_hi = np.maximum.accumulate(hi)
    run_lo = np.minimum.accumulate(lo)
    vw = vwap_bands(sess)
    vwap = vw["vwap"].to_numpy()
    sig1 = (vw["vwap_p1"].to_numpy() - vwap)
    ma15, _ = bb_ma_asof(sess, 15)
    ma15 = ma15.to_numpy()
    try:
        aw = anchored_weekly_profile(bars, day, upto=t0 + pd.Timedelta(hours=1))
        wvah, wval = float(aw["awVAH"]), float(aw["awVAL"])
    except Exception:
        wvah = wval = np.nan
    sess_open = float(sess.open.iloc[0])
    m = META.get(day, {})
    og = None
    if m:
        og = "above" if sess_open > m["vah"] else \
             "below" if sess_open < m["val"] else "inside"

    trades.sort(key=lambda t: t["t_sig_hrs"])
    for k, t in enumerate(trades):
        i = min(int(np.searchsorted(ts, int(t0.value + t["t_sig_hrs"] * 3.6e12))),
                len(ts) - 1)
        j = max(i - 1, 0)                      # last CLOSED bar at signal
        L, d = t["entry"], t["dir"]
        f = {}
        z = (L - vwap[j]) / sig1[j] if sig1[j] > 0 else 0.0
        f["vwap_rel"] = "fade_to_vwap" if z * d < 0 else "extend_away"
        f["vwap_z"] = "z<1" if abs(z) < 1 else ("z1-2" if abs(z) < 2 else "z2+")
        j30 = max(j - 30, 0)
        slope = ma15[j] - ma15[j30]
        f["ma15_align"] = "with_ma" if slope * d > 0 else "against_ma"
        if np.isfinite(wvah):
            side = "above" if L > wvah else ("below" if L < wval else "inside")
            f["wk_va"] = "inside_wk" if side == "inside" else (
                "toward_wk" if (side == "above") == (d == -1) else "away_wk")
        rng = run_hi[j] - run_lo[j]
        if rng > 0:
            p = (L - run_lo[j]) / rng
            f["sess_pos"] = "at_low" if p < 0.2 else ("at_high" if p > 0.8 else "mid")
        try:
            hm = (t0 + pd.Timedelta(hours=t["t_sig_hrs"])).strftime("%H:%M")
            f["chop"] = (state_at(bars, day, hm) or {}).get("state") or "NA"
        except Exception:
            f["chop"] = "NA"
        touched = (lo[:j + 1] <= L) & (hi[:j + 1] >= L)
        ntouch = int(touched.sum())
        f["touches"] = "0-5" if ntouch <= 5 else ("6-20" if ntouch <= 20 else "21+")
        nz = np.flatnonzero(touched)
        f["last_touch"] = ("<10m" if (j - nz[-1]) < 10 else
                           "10-60m" if (j - nz[-1]) < 60 else ">60m") if len(nz) else "never"
        f["density"] = "1st-2nd" if k < 2 else ("3rd-6th" if k < 6 else "7th+")
        j120 = max(j - 120, 0)
        dr = cl[j] - cl[j120]
        f["drift"] = "with_drift" if dr * d > 0 else "against_drift"
        if og:
            f["open_gap"] = "open_in_va" if og == "inside" else (
                "toward_va" if (og == "above") == (d == -1) else "away_va")
        yield t, f


def main() -> int:
    rows = [json.loads(l) for l in gzip.open(
        ROOT / "output/analysis/pd_va_trades_sar_through_tf1_ng.jsonl.gz", "rt")]
    pop = [t for t in rows if t["depth"] == 3.0 and t["target_r"] == 1.0]
    global META
    META = json.loads((ROOT / "output/analysis/pd_va_days.json").read_text())
    bars = OB.get_bars()
    byday = defaultdict(list)
    for t in pop:
        byday[t["day"]].append(t)

    agg = defaultdict(lambda: defaultdict(lambda: [[], []]))
    for idx, (day, trades) in enumerate(sorted(byday.items())):
        for t, f in day_features(bars, day, trades) or []:
            half = 0 if day < MID else 1
            for name, b in f.items():
                agg[name][b][half].append(t["r"] - 0.5 / t["risk"])
        if idx % 100 == 0:
            print(f"[{idx}/{len(byday)}] {day}", flush=True)

    print("\nPREREG RULE: SURVIVOR = same extreme ordering both halves, "
          "spread >=0.05R both, extreme n>=400/half\n")
    for name, buckets in agg.items():
        print(f"-- {name}")
        stats = {}
        for b, (i_, o_) in sorted(buckets.items()):
            ei = np.mean(i_) if i_ else 0
            eo = np.mean(o_) if o_ else 0
            stats[b] = (ei, eo, len(i_), len(o_))
            print(f"   {b:14} IS EV {ei:+.3f} (n={len(i_):4})   "
                  f"OOS EV {eo:+.3f} (n={len(o_):4})")
        bs = list(stats)
        if len(bs) >= 2:
            hi_i = max(bs, key=lambda b: stats[b][0])
            lo_i = min(bs, key=lambda b: stats[b][0])
            hi_o = max(bs, key=lambda b: stats[b][1])
            lo_o = min(bs, key=lambda b: stats[b][1])
            sp_i = stats[hi_i][0] - stats[lo_i][0]
            sp_o = stats[hi_o][1] - stats[lo_o][1]
            same = (hi_i == hi_o and lo_i == lo_o)
            nmin = min(stats[hi_i][2], stats[lo_i][2],
                       stats[hi_i][3], stats[lo_i][3])
            v = ("SURVIVOR" if same and sp_i >= 0.05 and sp_o >= 0.05
                 and nmin >= 400 else
                 "watch" if same and min(sp_i, sp_o) >= 0.03 else "null")
            print(f"   -> {v} (spread IS {sp_i:+.3f} / OOS {sp_o:+.3f}, "
                  f"best={hi_i}/{hi_o}, worst={lo_i}/{lo_o})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
