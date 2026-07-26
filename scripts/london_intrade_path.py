#!/usr/bin/env python3
"""IN-TRADE PATH MATRIX for the London 10:00-13:00 UK book — substrate for time-based cuts.

Angus's NY canon carries a 3-minute in-trade cut: if the trade is underwater past a threshold
AND net delta is against the position at +3 min, exit. On the NY book that combination ran an
18% win rate, so cutting it was free money. Our trades hold a median of 120 minutes rather than
minutes, so the equivalent checkpoint has to be much later — this builds every checkpoint so the
right one can be found rather than assumed.

BUILT ON THE BROAD DATASET. All 275 qualifying signals 2023-01 -> 2026-07, not the 70-signal
window the book was tuned on. That matters twice over: it is the larger sample, and it splits
into 205 holdout signals (2023-01 -> 2025-06) against 70 in-sample, so a cut rule can actually
be validated out-of-sample. Nothing else in this project has had that.

PER-CHECKPOINT COLUMNS, from 1-minute bars, for t in {3,5,10,15,20,30,45,60,90,120} minutes:
  r_t      unrealised R at t, marked at the 1-minute CLOSE
  mae_t    worst adverse excursion in R at any point up to t (on bar lows/highs)
  mfe_t    best favourable excursion in R up to t
  done_t   1 if the trade already resolved (stop or target) at or before t
  fw_t     signed aggressor delta from entry to t, in contracts, positive = with the trade
           (CVD exists only from 2025-06-02, so NaN before that -- reported, never imputed)

The eventual outcome (R, how, mins) is carried alongside so cut rules can be priced.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_intrade_path.py
"""
import os
import glob
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
CKPT = [3, 5, 10, 15, 20, 30, 45, 60, 90, 120]
IS_START = "2025-07-01"

print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b = b.sort_values("ts").reset_index(drop=True)
TS = b.ts.values
BO, BH, BL, BC = (b.open.values.astype(float), b.high.values.astype(float),
                  b.low.values.astype(float), b.close.values.astype(float))
POS1 = pd.Series(np.arange(len(b)), index=b.ts)

m = (b.set_index("ts").resample("15min", label="right", closed="right")
     .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
          close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"]))
_uk = m.index.tz_convert("Europe/London")
m["ukt"] = _uk.time
m["ukday"] = _uk.strftime("%Y-%m-%d")
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["v10"] = m.volume.rolling(10).mean().shift(1)
m["slo"] = m.low.rolling(5).min()
m["shi"] = m.high.rolling(5).max()
M = m.reset_index(names="uts").dropna(subset=["ma200"]).reset_index(drop=True)
a = {c: M[c].values for c in
     ["open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "v10", "slo", "shi"]}
ud, utt, uts = M.ukday.values, M.ukt.values, M.uts.values
SKIP = {"2025-11-28", "2026-04-03"}

# ---- CVD (2025-06 onward only) --------------------------------------------
print("load cvd ...", flush=True)
parts = []
for f in sorted(glob.glob(f"{WT}/data/reference/cvd/footprint_*.parquet")):
    d = pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
    d["s"] = np.where(d.side == "B", d.volume.astype(float), -d.volume.astype(float))
    parts.append(d.groupby("ts_minute")["s"].sum())
    del d
delta = pd.concat(parts).groupby(level=0).sum().sort_index()
delta.index = pd.to_datetime(delta.index, utc=True)
CUM = delta.cumsum()
print(f"  cvd minutes {len(delta):,}  {delta.index.min()} -> {delta.index.max()}", flush=True)


def _utc(x):
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def cum_at(t):
    """Cumulative signed delta at or before t; NaN outside CVD coverage."""
    if len(CUM) == 0 or t < CUM.index[0] or t > CUM.index[-1]:
        return np.nan
    k = CUM.index.searchsorted(t, side="right") - 1
    return float(CUM.iloc[k]) if k >= 0 else np.nan


rows = []
for i in range(1, len(M) - 1):
    d = ud[i]
    if d in SKIP or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    dr = 1 if (up and a["low"][i] <= a["ma50"][i]) else (-1 if (dn and a["high"][i] >= a["ma50"][i]) else 0)
    if dr == 0 or not (a["v10"][i] > 0 and a["volume"][i] < a["v10"][i]):
        continue
    en = a["open"][i + 1] + dr * TICK
    rf = min(a["slo"][i], a["ma50"][i]) if dr > 0 else max(a["shi"][i], a["ma50"][i])
    rk = abs(en - rf) + TICK
    if rk < 5 or rk > 70:
        continue
    st, tg = en - dr * rk, en + dr * 3 * rk

    # M15 resolution (the book's own outcome)
    gg, j, how = None, i + 1, None
    while j < len(M) and ud[j] == d:
        if utt[j] >= dtime(16, 30):
            gg = dr * (a["close"][j] - en); how = "time"; break
        hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
        ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
        if hs:
            gg = -rk - TICK; how = "stop"; break
        if ht:
            gg = 3 * rk - TICK; how = "target"; break
        j += 1
    if gg is None:
        j = min(j, len(M) - 1); gg = dr * (a["close"][j] - en); how = "dayend"
    net = gg * PV - COMM

    # ---- 1-minute path from entry -----------------------------------------
    t0 = _utc(uts[i])
    if t0 not in POS1.index:
        continue
    k0 = int(POS1[t0])
    rec = dict(day=d, sig=i, ent=str(utt[i]), dr=dr, entry=en, rk=rk, net=net,
               R=net / (rk * PV), how=how, mins=(j - i) * 15,
               oos=int(d < IS_START))
    c0 = cum_at(t0)
    mx = CKPT[-1]
    lo_run, hi_run, resolved_at = np.inf, -np.inf, None
    vals = {}
    for step in range(1, mx + 1):
        k = k0 + step
        if k >= len(b) or (TS[k] - TS[k0]) / np.timedelta64(1, "m") > step + 0.5:
            break                                    # ran off the tape / session gap
        adv_lo = dr * (BL[k] - en) if dr > 0 else dr * (BH[k] - en)
        adv_hi = dr * (BH[k] - en) if dr > 0 else dr * (BL[k] - en)
        lo_run = min(lo_run, adv_lo)
        hi_run = max(hi_run, adv_hi)
        if resolved_at is None:
            if lo_run <= -rk:
                resolved_at = step
            elif hi_run >= 3 * rk:
                resolved_at = step
        vals[step] = (dr * (BC[k] - en) / rk, lo_run / rk, hi_run / rk,
                      1 if resolved_at is not None else 0)
    for t in CKPT:
        if t in vals:
            r_, mae_, mfe_, dn_ = vals[t]
            rec[f"r_{t}"], rec[f"mae_{t}"], rec[f"mfe_{t}"], rec[f"done_{t}"] = r_, mae_, mfe_, dn_
            ct = cum_at(t0 + pd.Timedelta(minutes=t))
            rec[f"fw_{t}"] = (dr * (ct - c0)) if (np.isfinite(ct) and np.isfinite(c0)) else np.nan
        else:
            for p_ in ("r", "mae", "mfe", "done", "fw"):
                rec[f"{p_}_{t}"] = np.nan
    rows.append(rec)

P = pd.DataFrame(rows)
P.to_csv(f"{S}/london_intrade_path.csv", index=False)

print(f"\nsignals {len(P)}   holdout {int(P.oos.sum())}   in-sample {int((1-P.oos).sum())}")
print(f"outcome: WR {(P.R>0).mean()*100:.0f}%  netR {P.R.sum():+.2f}  "
      f"exits {dict(P.how.value_counts())}")
print(f"\ncheckpoint coverage (trades with a live path at t, and CVD flow at t):")
print(f"  {'t':>4} {'has r_t':>8} {'resolved':>9} {'has fw_t':>9}")
for t in CKPT:
    print(f"  {t:>4} {P[f'r_{t}'].notna().sum():>8} {int(P[f'done_{t}'].fillna(0).sum()):>9} "
          f"{P[f'fw_{t}'].notna().sum():>9}")
print(f"\nwrote {S}/london_intrade_path.csv")
