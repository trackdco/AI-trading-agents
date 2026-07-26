#!/usr/bin/env python3
"""LONDON Trend Pullback — FULL per-trade log + session-volatility columns.

Instruments scripts/london_trend_pullback.py. The trade logic (setup, trigger window, entry,
stop/target bracket, 09:25 ET flatten, costs, clamp) is copied BYTE-IDENTICAL so the aggregate
numbers reproduce the committed test exactly -- this only records more fields and adds two
no-lookahead volatility measures. It changes nothing about which trades are taken or how they exit.

Setup (long; mirror short), unchanged from the original:
  trend 20MA>50MA>200MA, close on the trend side of all three (M15)
  trigger: bar wicks the 50MA and closes back, with FADING volume (vol < mean prior 10)
  bracket: stop = min(swing-low-5, 50MA) - 1 tick, clamp 5-70pt; target = 3R
  entry: next M15 bar open +1 tick slip; flatten unresolved at 09:25 ET
  window: fills in [03:00, 07:45) ET; NET of costs (2 ticks slip + $5 RT)
  train 2023-24 / test 2025->now

VOLATILITY COLUMNS (per trade, strictly pre-entry -> no lookahead):
  on_range_pt   overnight/Asia range: high-low of 1-min bars in [prev 18:00 ET, 03:00 ET) on the
                trade day -- the whole Globex overnight INTO the London open, known at 03:00.
  atr14_pt      M15 ATR14 through the SIGNAL bar (its range is known at signal close, before the
                next-bar fill). Causal.
  pdr_pt        prior calendar trading day's high-low range (points), known before the session.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_tp_tradelog.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
NY = "America/New_York"
LON = "Europe/London"
TICK, PV, COMM = 0.25, 20.0, 5.0
TRAIN_END = "2024-12-31"
LON_START, LON_END, FLAT = dtime(3, 0), dtime(7, 45), dtime(9, 25)
TG = 3.0

print("load bars ...", flush=True)
bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)

# ---- per-day volatility context from the 1-minute frame (all strictly pre-London-open) -------
bts = bars.ts
b_et = bts.dt.time
b_day = bts.dt.strftime("%Y-%m-%d")
# overnight/Asia range: [prev 18:00 ET, 03:00 ET) mapped to the London calendar day it precedes.
# a bar at 20:00 ET on D-1 belongs to session D; a bar at 02:00 ET on D belongs to session D.
sess_day = np.where(b_et >= dtime(18, 0),
                    (bts + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d"),
                    b_day)
on_mask = ((b_et >= dtime(18, 0)) | (b_et < dtime(3, 0))).values
onf = pd.DataFrame({"d": np.where(on_mask, sess_day, None),
                    "hi": bars.high.values, "lo": bars.low.values})[on_mask]
ON_RANGE = (onf.groupby("d").hi.max() - onf.groupby("d").lo.min()).to_dict()
# prior calendar trading day range
day_hi = bars.groupby(b_day).high.max()
day_lo = bars.groupby(b_day).low.min()
day_rng = (day_hi - day_lo)
PDR = day_rng.shift(1).to_dict()

# ---- M15 frame + indicators, identical to the original ---------------------------------------
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["day"] = m.index.strftime("%Y-%m-%d")
m["t"] = m.index.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol_maN"] = m.volume.rolling(10).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min()
m["swing_hi5"] = m.high.rolling(5).max()
_tr = np.maximum(m.high - m.low, np.maximum((m.high - m.close.shift(1)).abs(),
                                            (m.low - m.close.shift(1)).abs()))
m["atr14"] = _tr.rolling(14).mean()                       # value at bar i is known at i's close
M = m.reset_index().rename(columns={"index": "ts"}).dropna(subset=["ma200"]).reset_index(drop=True)
a = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200",
                              "vol_maN", "volume", "swing_lo5", "swing_hi5", "atr14"]}
ts_a = M.ts.values
day_a = M.day.values
t_a = M.t.values

trg = np.array([LON_START <= t < LON_END for t in t_a])
trigs = []
for i in range(1, len(M)):
    if not trg[i] or np.isnan(a["vol_maN"][i]) or a["vol_maN"][i] <= 0:
        continue
    if a["volume"][i] >= a["vol_maN"][i]:
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    if up and a["low"][i] <= a["ma50"][i] and a["close"][i] > a["ma50"][i]:
        trigs.append((i, 1))
    elif dn and a["high"][i] >= a["ma50"][i] and a["close"][i] < a["ma50"][i]:
        trigs.append((i, -1))


def resolve(i, dr, invert=False, record=False):
    if i + 1 >= len(M) or day_a[i + 1] != day_a[i]:
        return None
    ed = -dr if invert else dr
    entry = a["open"][i + 1] + ed * TICK
    if invert:
        ref = a["swing_hi5"][i] if dr > 0 else a["swing_lo5"][i]
        risk = abs(ref - entry)
    else:
        ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i])
        risk = abs(entry - ref) + TICK
    if risk < 5 or risk > 70:
        return None
    stop = entry - ed * risk
    tgt = entry + ed * TG * risk
    gross, reason, exitpx, j = None, None, None, i + 1
    while j < len(M) and day_a[j] == day_a[i]:
        if t_a[j] >= FLAT:
            gross = ed * (a["close"][j] - entry); reason = "flat"; exitpx = a["close"][j]; break
        hit_stop = (a["low"][j] <= stop) if ed > 0 else (a["high"][j] >= stop)
        hit_tgt = (a["high"][j] >= tgt) if ed > 0 else (a["low"][j] <= tgt)
        if hit_stop:
            gross = -risk - TICK; reason = "stop"; exitpx = stop; break
        if hit_tgt:
            gross = TG * risk - TICK; reason = "target"; exitpx = tgt; break
        j += 1
    if gross is None:
        jj = min(j, len(M) - 1)
        gross = ed * (a["close"][jj] - entry); reason = "eod"; exitpx = a["close"][jj]
    net = gross * PV - COMM
    if not record:
        return net, net / (risk * PV), risk
    fill = pd.Timestamp(ts_a[i + 1]).tz_localize("UTC")   # .values gave UTC-naive instants
    fill_et = fill.tz_convert(NY)
    fill_uk = fill.tz_convert(LON)
    return dict(net=net, R=net / (risk * PV), risk=risk, entry=entry, stop=stop, tgt=tgt,
                reason=reason, exitpx=exitpx, exit_bar=j,
                fill_et=fill_et, fill_uk=fill_uk)


rows = []
for i, dr in trigs:
    r = resolve(i, dr, record=True)
    rc = resolve(i, dr, invert=True)
    if r is None:
        continue
    d = day_a[i]
    rows.append(dict(
        date=d, weekday=pd.Timestamp(d).strftime("%a"),
        sig_et=str(t_a[i]), entry_et=r["fill_et"].strftime("%H:%M"),
        entry_uk=r["fill_uk"].strftime("%H:%M"),
        dir="long" if dr > 0 else "short",
        entry=round(r["entry"], 2), stop=round(r["stop"], 2), target=round(r["tgt"], 2),
        stop_pt=round(r["risk"], 2), exit_reason=r["reason"], exit_px=round(r["exitpx"], 2),
        netR=round(r["R"], 3), net=round(r["net"], 0),
        on_range_pt=round(ON_RANGE.get(d, np.nan), 1),
        atr14_pt=round(a["atr14"][i], 1) if np.isfinite(a["atr14"][i]) else np.nan,
        pdr_pt=round(PDR.get(d, np.nan), 1),
        year=d[:4], train=d <= TRAIN_END,
        ctrR=rc[1] if rc else np.nan))

T = pd.DataFrame(rows).sort_values(["date", "entry_et"]).reset_index(drop=True)
T.insert(0, "n", range(1, len(T) + 1))
T["cum_net"] = T.net.cumsum().round(0)
out = f"{S}/london_tp_tradelog.csv"
T.to_csv(out, index=False)


def blk(sub, lab):
    if not len(sub):
        print(f"  {lab:14s} n=0"); return
    n = len(sub); wr = 100 * (sub.netR > 0).mean()
    eq = sub.sort_values("date").net.cumsum().values
    dd = float((np.maximum.accumulate(eq) - eq).max())
    gp = sub.netR[sub.netR > 0].sum(); gl = -sub.netR[sub.netR < 0].sum()
    pf = gp / gl if gl > 0 else float("inf")
    print(f"  {lab:14s} n={n:4d}  WR {wr:4.0f}%  E[R] {sub.netR.mean():+.3f}  "
          f"PF {pf:4.2f}  net ${sub.net.sum():+,.0f}  maxDD ${dd:,.0f}")


if __name__ == "__main__":
    print("=" * 92)
    print(f"REPRODUCTION CHECK — {len(T)} trades, {T.date.nunique()} days, "
          f"{int(T.train.sum())} train / {int((~T.train).sum())} test")
    print("=" * 92)
    for lab, sub in (("ALL", T), ("TRAIN 23-24", T[T.train]), ("TEST 25-26", T[~T.train])):
        blk(sub, lab)
    print("\n  counter-baseline (mirror dir), TEST:",
          f"E[R] {T[~T.train].ctrR.mean():+.3f}")
    print("\n  by year:")
    for yr in ("2023", "2024", "2025", "2026"):
        blk(T[T.year == yr], yr)
    print(f"\nwrote {out}  ({len(T)} rows, {len(T.columns)} cols)")
