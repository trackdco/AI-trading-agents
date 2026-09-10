#!/usr/bin/env python3
"""OROCHI BIAS CENSUS — does the framework predict direction? (2026-09-10)

His ask: use Orochi's auction framework as a MECHANICAL BIAS engine — classify
what the market is doing, and use that to say where price goes next — rather
than as a set of trade triggers.

WHY THIS TEST IS STRUCTURALLY IMMUNE TO THE S40 LEAK. The fill-bar look-ahead
lived entirely in exit/fill accounting. This census places NO orders. It
classifies the state using only bars up to and including minute t's close,
then measures what price actually did from close(t) to close(t+h). There is
no limit fill, no intrabar path, no stop/target race — nothing a look-ahead
can hide inside. If the framework carries directional information, it must
show up here; if it does not show up here, no entry grammar can rescue it.

PRE-REGISTERED, written before any number was read:

  MEASURE. For every minute of every session (after VWAP warm-up), record
  the Orochi state, then forward close-to-close moves at h = 5/15/30/60 min.
  Report EVERY state, not a selected subset. Census, not strategy.

  SIGNIFICANCE. Overlapping windows autocorrelate, so t-stats on raw minutes
  are inflated. Every state's returns are collapsed to ONE mean per session
  day first, then t-tested across days (day-clustered). Reported as t_day.

  ERAS. 2020-22 (the sealed holdout tape), 2023-24, 2025-26. Reported
  separately, always.

  VERDICT RULE.
    SIGNAL  = mean forward move has the SAME SIGN in all three eras
              AND |t_day| >= 2 in the pooled sample
              AND the pooled mean move exceeds 2.0 pts, the published
              MNQ bar-level friction ceiling cited in the intake dossier.
    WEAK    = same sign in all three eras, but under the 2.0pt bar.
              Real information, not tradeable alone.
    NULL    = anything else.
  A WEAK result is the expected outcome and is NOT a failure: a bias that
  is real but sub-friction is still usable as a FILTER on some other entry,
  which is exactly what "framework, not trigger" means.

  BASELINE. NQ drifts up. Every state is reported against the unconditional
  mean move for the same era and horizon, and long/short states are read
  symmetrically. Edge is measured vs baseline, never vs zero.

STATE DEFINITIONS (all causal, all mechanical, his doctrine):
  zone   position of close vs DEVELOPING session VWAP bands (+-1sd = his
         "value", +-2sd = his "rotational extreme").
  regime his hard gate. ROT = no acceptance established beyond either +-1sd
         edge so far this session. IMB_UP/IMB_DN = acceptance (3 consecutive
         closes) was established beyond an edge and price is still beyond it.
         DEV = outside an edge but not yet accepted ("just barely deviating").
  vaLoc  position vs PRIOR-DAY value area (VAH/VAL from the prior session's
         volume profile) — above / inside / below.
  event  ACC_BACK_UP/DN = his flagship failed auction: price accepted outside
         the prior-day VA, then closed back inside. Bias is toward traversal.

    python -m scripts.orochi_bias_census --instrument nq
    python -m scripts.orochi_bias_census --instrument nq20a
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                       # noqa: E402
from scripts.agent_context import volume_profile             # noqa: E402
from src.htf_ma.levels import vwap_bands                     # noqa: E402
import scripts.pd_va_backtest as BT                          # noqa: E402

SESS_H = 23.0
WARMUP_MIN = 15          # his "useless for the first 10-15 minutes"
ACCEPT_N = 3             # his negative definition: a bare poke is not acceptance
HORIZONS = (5, 15, 30, 60)


def classify_day(sess, vah, val, bin_w):
    """Per-minute causal state + forward moves for one session."""
    cl = sess.close.to_numpy(float)
    n = len(cl)
    vw = vwap_bands(sess)
    v0 = vw.vwap.to_numpy(float)
    p1, m1 = vw.vwap_p1.to_numpy(float), vw.vwap_m1.to_numpy(float)
    p2, m2 = vw.vwap_p2.to_numpy(float), vw.vwap_m2.to_numpy(float)

    zone = np.full(n, "na", dtype=object)
    above2, above1 = cl > p2, cl > p1
    below2, below1 = cl < m2, cl < m1
    zone[above1 & ~above2] = "sd1_2_up"
    zone[above2] = "gt_sd2_up"
    zone[below1 & ~below2] = "sd1_2_dn"
    zone[below2] = "gt_sd2_dn"
    zone[~above1 & ~below1 & (cl >= v0)] = "in_val_up"
    zone[~above1 & ~below1 & (cl < v0)] = "in_val_dn"

    # acceptance beyond a value edge: ACCEPT_N consecutive closes beyond it
    def runs(mask):
        out = np.zeros(n, bool)
        c = 0
        for i in range(n):
            c = c + 1 if mask[i] else 0
            out[i] = c >= ACCEPT_N
        return out
    acc_up_now, acc_dn_now = runs(above1), runs(below1)
    ever_up = np.maximum.accumulate(acc_up_now.astype(int)).astype(bool)
    ever_dn = np.maximum.accumulate(acc_dn_now.astype(int)).astype(bool)

    regime = np.full(n, "ROT", dtype=object)
    regime[above1 & ~ever_up] = "DEV_UP"
    regime[below1 & ~ever_dn] = "DEV_DN"
    regime[above1 & ever_up] = "IMB_UP"
    regime[below1 & ever_dn] = "IMB_DN"

    # prior-day value area location + his flagship acceptance-back-inside
    valoc = np.full(n, "in_va", dtype=object)
    if np.isfinite(vah):
        valoc[cl > vah] = "above_vah"
    if np.isfinite(val):
        valoc[cl < val] = "below_val"
    ev = np.full(n, "", dtype=object)
    if np.isfinite(vah) and np.isfinite(val):
        acc_out_up = runs(cl > vah)
        acc_out_dn = runs(cl < val)
        seen_up = seen_dn = False
        for i in range(n):
            if acc_out_up[i]:
                seen_up = True
            elif seen_up and cl[i] <= vah:
                ev[i] = "ACC_BACK_DN"      # failed upside auction -> traverse down
                seen_up = False
            if acc_out_dn[i]:
                seen_dn = True
            elif seen_dn and cl[i] >= val:
                ev[i] = "ACC_BACK_UP"      # failed downside auction -> traverse up
                seen_dn = False

    fwd = {h: np.full(n, np.nan) for h in HORIZONS}
    for h in HORIZONS:
        fwd[h][:n - h] = cl[h:] - cl[:n - h]
    return zone, regime, valoc, ev, fwd


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
    print(f"{a.instrument}: {len(bars):,} bars, {len(days)} session days", flush=True)

    # rows: (day, state_key, horizon) -> list of forward moves
    acc = defaultdict(lambda: defaultdict(list))
    for di, day in enumerate(days):
        if day in roll_skip:
            continue
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        i = days.index(day) if di == 0 else di
        if i == 0:
            continue
        pa = pd.Timestamp(f"{days[i-1]} 18:00", tz=OB.NY)
        pseg = bars[(bars.index >= pa) & (bars.index < t0)]
        sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
        if len(sess) < 600 or len(pseg) < 300:
            continue
        _, val, vah = volume_profile(pseg, bin_w=inst["bin_w"])
        zone, regime, valoc, ev, fwd = classify_day(sess, vah, val, inst["bin_w"])
        for h in HORIZONS:
            f = fwd[h]
            ok = np.isfinite(f)
            ok[:WARMUP_MIN] = False
            idx = np.flatnonzero(ok)
            acc[day][("ALL", h)].extend(f[idx])
            for j in idx:
                acc[day][(f"zone={zone[j]}", h)].append(f[j])
                acc[day][(f"regime={regime[j]}", h)].append(f[j])
                acc[day][(f"valoc={valoc[j]}", h)].append(f[j])
                acc[day][(f"{regime[j]}|{zone[j]}", h)].append(f[j])
                if ev[j]:
                    acc[day][(f"event={ev[j]}", h)].append(f[j])
        if di % 200 == 0:
            print(f"  [{di}/{len(days)}] {day}", flush=True)

    out = ROOT / f"output/analysis/orochi_bias_{a.instrument}.json"
    ser = {d: {f"{k[0]}@@{k[1]}": [float(np.mean(v)), len(v)]
               for k, v in dd.items()} for d, dd in acc.items()}
    out.write_text(json.dumps(ser))
    print(f"wrote {out} ({len(ser)} days)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
