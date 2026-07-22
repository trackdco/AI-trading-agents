#!/usr/bin/env python3
"""BIAS LAB — screen ~20 daily-directional-bias concepts + a walk-forward learning ensemble.
NQ, Jan 2023 -> Jul 2026. No trading; the target is the NY session's DIRECTION.

Each concept -> a daily signal {+1 bull, -1 bear, 0 neutral} from data available at 08:00 ET
(prior days complete + this day's overnight/premarket through 08:00). Graded: the NY session
(09:30->16:00) net move beyond +/-0.10% of the open. Reported overall, per-year, and
TRAIN(2023-24) vs TEST(2025-26). Edge = accuracy - base rate (P(up)) for that period.

Concepts span trend/momentum, ICT/session (incl. the documented overnight/daytime reversal
anomaly), indicators, and stat/seasonal/external (VIX). True CVD is 2026-only, so order flow
uses a 1m up/down-volume proxy for the full span (flagged).

LEARNER (the journaling agent, deterministic + walk-forward): each concept keeps a trailing-60
record; each day it votes with signed weight = signal*(trailing_acc - base_rate) once it has
>=15 graded fires -> concepts beating the base rate push their direction, concepts below it get
FADED (voted opposite). Ensemble = sign of the weighted sum (NEUTRAL if weak). Only prior days
feed the weights (no lookahead). We journal the trusted/faded concept set over time and test
whether the learned bias beats the best single concept and the base rate out of sample.
"""
import io
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
START, END = "2023-01-01", "2026-07-15"
THR = 0.0010
TRAIN_END = "2024-12-31"

bars = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
bars["t"] = bars["ts"].dt.time
by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day")}
daylist = sorted(by_day)

vix = pd.read_csv("/home/user/gs/data/reference/vix_daily.csv")
vix["date"] = vix["date"].astype(str)
vix = vix.set_index("date")["vix"].to_dict()

# ---------------- per-day feature frame (all values known by 08:00 ET on the day) --------------
def sess(g, a, b):
    return g[(g.t >= a) & (g.t < b)]

rows = []
for i, day in enumerate(daylist):
    if day < "2022-11-01":
        continue
    g = by_day[day]
    ny = sess(g, dtime(9, 30), dtime(16, 0))
    if len(ny) < 100:
        continue
    rows.append(dict(
        day=day, dow=pd.Timestamp(day).dayofweek, dom=pd.Timestamp(day).day,
        d_o=float(g.open.iloc[0]), d_h=float(g.high.max()), d_l=float(g.low.min()), d_c=float(g.close.iloc[-1]),
        rth_o=float(ny.open.iloc[0]), rth_c=float(ny.close.iloc[-1]),
        rth_h=float(ny.high.max()), rth_l=float(ny.low.min()),
        t_hi=ny.ts[ny.high.idxmax()].value, t_lo=ny.ts[ny.low.idxmin()].value,
        pm_c=float(sess(g, dtime(0, 0), dtime(8, 0)).close.iloc[-1]) if len(sess(g, dtime(0, 0), dtime(8, 0))) else np.nan,
        pm_o=float(sess(g, dtime(0, 0), dtime(8, 0)).open.iloc[0]) if len(sess(g, dtime(0, 0), dtime(8, 0))) else np.nan,
        asia_c=float(sess(g, dtime(0, 0), dtime(3, 0)).close.iloc[-1]) if len(sess(g, dtime(0, 0), dtime(3, 0))) else np.nan,
        asia_o=float(sess(g, dtime(0, 0), dtime(3, 0)).open.iloc[0]) if len(sess(g, dtime(0, 0), dtime(3, 0))) else np.nan,
        lon_o=float(sess(g, dtime(3, 0), dtime(8, 0)).open.iloc[0]) if len(sess(g, dtime(3, 0), dtime(8, 0))) else np.nan,
        lon_c=float(sess(g, dtime(3, 0), dtime(8, 0)).close.iloc[-1]) if len(sess(g, dtime(3, 0), dtime(8, 0))) else np.nan,
        lon_h=float(sess(g, dtime(3, 0), dtime(8, 0)).high.max()) if len(sess(g, dtime(3, 0), dtime(8, 0))) else np.nan,
        lon_l=float(sess(g, dtime(3, 0), dtime(8, 0)).low.min()) if len(sess(g, dtime(3, 0), dtime(8, 0))) else np.nan,
        vix=vix.get(day, np.nan),
    ))
F = pd.DataFrame(rows).set_index("day").sort_index()

# prior-day RTH close (16:00) for overnight gap
rth_close = {}
for day in F.index:
    ny = sess(by_day[day], dtime(9, 30), dtime(16, 0))
    rth_close[day] = float(ny.close.iloc[-1])
F["prth_c"] = [rth_close.get(F.index[i - 1]) if i > 0 else np.nan for i in range(len(F))]

# daily-close indicators computed on CLOSES THROUGH THE PRIOR DAY (shift 1 = no lookahead)
c = F["d_c"]
F["sma20"] = c.rolling(20).mean().shift(1)
F["sma50"] = c.rolling(50).mean().shift(1)
F["pc"] = c.shift(1); F["pc2"] = c.shift(2); F["pc3"] = c.shift(3); F["pc5"] = c.shift(5)
F["ph"] = F["d_h"].shift(1); F["pl"] = F["d_l"].shift(1)
F["ph2"] = F["d_h"].shift(2); F["pl2"] = F["d_l"].shift(2)
delta = c.diff()
gain = delta.clip(lower=0).rolling(14).mean(); loss = (-delta.clip(upper=0)).rolling(14).mean()
F["rsi"] = (100 - 100 / (1 + gain / loss)).shift(1)
sd = c.rolling(20).std(ddof=0)
F["bb_up"] = (c.rolling(20).mean() + 2 * sd).shift(1); F["bb_lo"] = (c.rolling(20).mean() - 2 * sd).shift(1)
ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
macd = ema12 - ema26; F["macd_hist"] = (macd - macd.ewm(span=9, adjust=False).mean()).shift(1)
F["vix_p"] = pd.Series(F["vix"].values, index=F.index).shift(1)   # prior day's VIX close (known at 08:00)
F["vix_p2"] = pd.Series(F["vix"].values, index=F.index).shift(2)
F["vix_chg"] = (F["vix_p"] - F["vix_p2"])   # change over the PRIOR completed day (NO lookahead;
#   today's VIX close reflects today's move -> using it would be circular against the outcome)
# weekly bias (prior completed weeks): higher weekly closes
F["iso"] = pd.to_datetime(F.index).isocalendar().week.values + pd.to_datetime(F.index).isocalendar().year.values * 100
wk = F.groupby("iso").agg(wc=("d_c", "last")).sort_index()
wk["wprev"] = wk["wc"].shift(1); wk["wprev3"] = wk["wc"].shift(3)
wbias = {i: (1 if r.wc > r.wprev and r.wc > r.wprev3 else -1 if r.wc < r.wprev and r.wc < r.wprev3 else 0)
         for i, r in wk.iterrows() if pd.notna(r.wprev3)}
# map each day to its PRIOR week's bias (no lookahead)
isos = sorted(wk.index)
prevw = {isos[k]: isos[k - 1] for k in range(1, len(isos))}
F["wbias"] = [wbias.get(prevw.get(i), 0) for i in F["iso"]]

# up/down volume proxy per prior day (tick-rule net)
udv = {}
for day in F.index:
    g = by_day[day]; ch = g.close.diff()
    up = g.volume[ch > 0].sum(); dn = g.volume[ch < 0].sum()
    udv[day] = np.sign(up - dn)
F["udv_prev"] = [udv.get(F.index[i - 1], 0) if i > 0 else 0 for i in range(len(F))]

F = F[(F.index >= START) & (F.index <= END)].dropna(subset=["sma50", "rsi", "prth_c"])
base_rate_all = float((F["rth_c"] > F["rth_o"]).mean())
print(f"days {len(F)}  base rate P(NY up) = {base_rate_all*100:.1f}%")

# ---------------- concept signal functions (each: row -> -1/0/+1) ----------------
def sgn(x):
    try:
        if x is None or pd.isna(x):
            return 0
        return int(np.sign(float(x)))
    except (TypeError, ValueError):
        return 0

def _num(x, default=np.nan):
    try:
        return float(x) if not pd.isna(x) else default
    except (TypeError, ValueError):
        return default

C = {}   # name -> function
C["daily_trend_20_50"] = lambda r: 1 if (r.pc > r.sma20 and r.sma20 > r.sma50) else (-1 if (r.pc < r.sma20 and r.sma20 < r.sma50) else 0)
C["momentum_1d"] = lambda r: sgn(r.pc - r.pc2)
C["momentum_3d"] = lambda r: sgn(r.pc - r.pc3)
C["momentum_5d"] = lambda r: sgn(r.pc - r.pc5)
C["weekly_bias"] = lambda r: int(r.wbias)
C["daily_hh_hl"] = lambda r: 1 if (r.ph > r.ph2 and r.pl > r.pl2) else (-1 if (r.ph < r.ph2 and r.pl < r.pl2) else 0)
C["overnight_cont"] = lambda r: sgn(r.pm_c - r.prth_c)        # overnight drift continues
C["overnight_reversal"] = lambda r: -sgn(r.pm_c - r.prth_c)   # documented tug-of-war reversal
C["gap_fill"] = lambda r: -sgn(r.pm_c - r.prth_c)             # gaps tend to fill (same as reversal here)
C["london_dir_cont"] = lambda r: sgn(r.lon_c - r.lon_o)
C["london_reversal"] = lambda r: -sgn(r.lon_c - r.lon_o)
C["asia_dir"] = lambda r: sgn(r.asia_c - r.asia_o)
def _sweep(r):
    ll, lh, pl, ph = _num(r.lon_l), _num(r.lon_h), _num(r.pl), _num(r.ph)
    if np.isnan(ll) or np.isnan(lh):
        return 0
    return 1 if ll < pl else (-1 if lh > ph else 0)
C["sweep_pdl_bull"] = _sweep   # turtle soup
C["premarket_judas"] = lambda r: -sgn(r.pm_c - r.pm_o)        # premarket move = manipulation, reverse
C["rsi_meanrev"] = lambda r: 1 if _num(r.rsi, 50) < 35 else (-1 if _num(r.rsi, 50) > 65 else 0)
C["rsi_momentum"] = lambda r: 1 if _num(r.rsi, 50) > 55 else (-1 if _num(r.rsi, 50) < 45 else 0)
C["bb_meanrev"] = lambda r: 1 if _num(r.pc) < _num(r.bb_lo) else (-1 if _num(r.pc) > _num(r.bb_up) else 0)
C["bb_momentum"] = lambda r: 1 if _num(r.pc) > _num(r.bb_up) else (-1 if _num(r.pc) < _num(r.bb_lo) else 0)
C["macd"] = lambda r: sgn(r.macd_hist)
C["udv"] = lambda r: int(r.udv_prev)
C["vix_low_bull"] = lambda r: (1 if _num(r.vix_p, 20) < 16 else (-1 if _num(r.vix_p, 20) > 24 else 0))
C["vix_rising_bear"] = lambda r: (-sgn(r.vix_chg) if abs(_num(r.vix_chg, 0)) > 0.5 else 0)
C["dow_seasonal"] = lambda r: 1 if r.dow in (1, 2, 3) else 0   # Tue-Thu drift (tested)
C["turn_of_month"] = lambda r: 1 if (r.dom >= 28 or r.dom <= 3) else 0
C["prev_rth_cont"] = lambda r: sgn(r.pc - r.d_o if False else r.pc - r.pc2)  # placeholder alias -> drop dup

del C["prev_rth_cont"]

# ---------------- grade each concept ----------------
def outcome(r):
    thr = THR * r.rth_o; net = r.rth_c - r.rth_o
    return 1 if net > thr else (-1 if net < -thr else 0)

F["out"] = F.apply(outcome, axis=1)
recs = F.to_dict("index"); order = list(F.index)
SIG = {name: np.array([fn(F.loc[d]) for d in order]) for name, fn in C.items()}
OUT = F["out"].values
yr = np.array([d[:4] for d in order])
is_train = np.array([d <= TRAIN_END for d in order])

def score(sig, mask):
    m = mask & (sig != 0) & (OUT[:len(sig)] if False else True)
    fire = (sig != 0) & mask
    if fire.sum() == 0:
        return 0, 0.0
    correct = ((sig == OUT) & fire).sum()
    return int(fire.sum()), round(100 * correct / fire.sum(), 1)

def base(mask):
    o = OUT[mask]
    return round(100 * (o == 1).mean(), 1)   # base = predict up always

results = []
for name, sig in SIG.items():
    n_all, a_all = score(sig, np.ones(len(order), bool))
    n_tr, a_tr = score(sig, is_train)
    n_te, a_te = score(sig, ~is_train)
    edge_te = round(a_te - base(~is_train), 1)
    results.append(dict(concept=name, n=n_all, acc=a_all, train_acc=a_tr, test_acc=a_te,
                        test_n=n_te, test_edge=edge_te))
R = pd.DataFrame(results).sort_values("test_edge", ascending=False)
R.to_csv(f"{S}/bias_lab_concepts.csv", index=False)
print(f"\nbase rate all {base_rate_all*100:.1f}%  train {base(is_train)}%  test {base(~is_train)}%")
print("\n=== CONCEPTS ranked by OOS edge (test 2025-26) ===")
print(R.to_string(index=False))
np.save(f"{S}/_sig.npy", np.array([SIG[n] for n in C]))
import json
json.dump({"names": list(C), "order": order, "out": OUT.tolist(),
           "is_train": is_train.tolist(), "yr": yr.tolist(),
           "base_all": base_rate_all}, open(f"{S}/_lab.json", "w"))
print("\nsaved bias_lab_concepts.csv + _lab.json")
