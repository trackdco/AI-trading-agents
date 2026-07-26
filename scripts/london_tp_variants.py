#!/usr/bin/env python3
"""LONDON Trend Pullback — VARIANT GRID. Goal: fix TRAIN (especially 2024) without gutting TEST.

Base book (london_trend_pullback.py, reproduced bit-exact by london_tp_tradelog.py):
365 trades 2023->2026-07, TRAIN 23-24 -$23,530 (2024 alone -$28,320 at 15% WR),
TEST 25-26 +$55,975 at +0.425 E[R].

WHAT THE 2024 TAPE ACTUALLY SHOWS (from the per-trade log): the bleed is CLUSTERED —
same-day, same-direction re-triggers stopping in sequence (2024-01-25 five longs, 2024-05-16
four longs, 2024-09-04 four shorts, etc.). The MA stack stays stacked while price fails through
the level, so the setup re-arms every 15 minutes into the same losing move. That points at
overtrading mechanics (first-touch-only, one-position, day-stop) more than at entry filters.

VARIANTS (all strictly no-lookahead, net of the same costs, same 03:00-07:45 ET signal window,
same 09:25 flat; TRAIN 2023-24 is the fitting ground, TEST 2025-26 is the holdout):
  baselines      trend-filter-alone (fading-volume rule REMOVED, so the extra rules have to
                 earn their place) and V0 as committed
  overtrading    first-touch of the 50 (no touch on prior 1 / prior 3 bars), one-position-
                 at-a-time, realtime day-stop (first CLOSED loss ends the day -- the honest
                 form, not the lookahead form found in the 10-13 book)
  brackets       2R target; fixed ATR14-based stops (friend's spec) at 1.5x, with 3R and 2R
  friend spec    20>50>200 + first touch + fading volume + ATR bracket, exactly as proposed
  context        session VWAP side (18:00 ET anchor), overnight-range gate, room to the
                 prior-session extreme >= 3R (target reachable without a breakout),
                 prior-day value-area position
  stacks         the mechanism trio (ft3 + day-stop) combined with the context filters

MULTIPLICITY: ~18 variants are evaluated. The guard is the train/test split plus per-year
positivity as the bar -- but anything promoted from this grid is a HOLDOUT CANDIDATE fitted on
2023-24, not a ship. Everything is reported, not just winners.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_tp_variants.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
NY = "America/New_York"
TICK, PV, COMM = 0.25, 20.0, 5.0
TRAIN_END = "2024-12-31"
LON_START, LON_END, FLAT = dtime(3, 0), dtime(7, 45), dtime(9, 25)
BIN, VA = 1.0, 0.70

print("load bars ...", flush=True)
bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
# CME session id: 18:00 ET boundary (a bar at 18:00+ belongs to the NEXT calendar session)
bars["sess"] = (bars.ts + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
b_t = bars.ts.dt.time

# ---------------- per-session context (all knowable before the London window) ----------------
print("session context ...", flush=True)
g = bars.groupby("sess")
SESS_HI = g.high.max()
SESS_LO = g.low.min()
PD_HI = SESS_HI.shift(1).to_dict()
PD_LO = SESS_LO.shift(1).to_dict()

on_mask = ((b_t >= dtime(18, 0)) | (b_t < dtime(3, 0))).values
onb = bars[on_mask]
og = onb.groupby("sess")
ON_HI, ON_LO = og.high.max().to_dict(), og.low.min().to_dict()
ON_RANGE = (og.high.max() - og.low.min()).to_dict()
_ov = og.volume.sum()
ON_VOL_REL = (_ov / _ov.shift(1).rolling(20, min_periods=10).median()).to_dict()


def value_area(hist):
    if not hist:
        return None
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * BIN
    total = arr.sum()
    if total <= 0:
        return None
    poc = int(arr.argmax())
    lo = hi = poc
    cov = arr[poc]
    tgt = VA * total
    n = len(arr)
    while cov < tgt - 1e-9 and (lo > 0 or hi < n - 1):
        bl = arr[lo - 1] if lo > 0 else -np.inf
        ab = arr[hi + 1] if hi < n - 1 else -np.inf
        if ab >= bl:
            hi += 1; cov += arr[hi]
        else:
            lo -= 1; cov += arr[lo]
    return dict(poc=float(centers[poc]), vah=float(centers[hi]), val=float(centers[lo]))


def profile_of(frame):
    lo_i = np.floor(frame.low.values / BIN).astype(np.int64)
    hi_i = np.floor(frame.high.values / BIN).astype(np.int64)
    vol = frame.volume.values.astype(float)
    span = (hi_i - lo_i + 1).clip(min=1)
    share = vol / span
    idx = np.repeat(np.arange(len(lo_i)), span)
    offs = np.concatenate([np.arange(s) for s in span]) if len(span) else np.array([], dtype=np.int64)
    bins = lo_i[idx] + offs
    w = share[idx]
    if not len(bins):
        return None
    order = np.argsort(bins, kind="stable")
    bs, ws = bins[order], w[order]
    uniq, start = np.unique(bs, return_index=True)
    sums = np.add.reduceat(ws, start)
    return value_area(dict(zip(uniq.tolist(), sums.tolist())))


print("prior-session profiles ...", flush=True)
by_sess = {d: fr for d, fr in bars.groupby("sess")}
sess_days = sorted(by_sess)
PD_PROF = {}
for k, d in enumerate(sess_days):
    if k > 0:
        PD_PROF[d] = profile_of(by_sess[sess_days[k - 1]])

# ---------------- M15 frame + indicators (identical to the committed book) --------------------
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["day"] = m.index.strftime("%Y-%m-%d")
m["sess"] = ((m.index - pd.Timedelta(minutes=1)) + pd.Timedelta(hours=6)).strftime("%Y-%m-%d")
m["t"] = m.index.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol_maN"] = m.volume.rolling(10).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min()
m["swing_hi5"] = m.high.rolling(5).max()
_tr = np.maximum(m.high - m.low, np.maximum((m.high - m.close.shift(1)).abs(),
                                            (m.low - m.close.shift(1)).abs()))
m["atr14"] = _tr.rolling(14).mean()
# session VWAP (18:00 ET anchor), developing, M15 typical price
tp = (m.high + m.low + m.close) / 3.0
cv = m.volume.groupby(m.sess).cumsum()
cvp = (tp * m.volume).groupby(m.sess).cumsum()
m["vwap"] = cvp / cv
M = m.reset_index().rename(columns={"index": "ts"}).dropna(subset=["ma200"]).reset_index(drop=True)
a = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200",
                              "vol_maN", "volume", "swing_lo5", "swing_hi5", "atr14", "vwap"]}
day_a, sess_a, t_a = M.day.values, M.sess.values, M.t.values

# ---------------- candidates (V0 trigger, fading-volume recorded as a FLAG) -------------------
trg = np.array([LON_START <= t < LON_END for t in t_a])
CAND = []
for i in range(4, len(M)):
    if not trg[i] or np.isnan(a["vol_maN"][i]) or a["vol_maN"][i] <= 0:
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    dr = 0
    if up and a["low"][i] <= a["ma50"][i] and a["close"][i] > a["ma50"][i]:
        dr = 1
    elif dn and a["high"][i] >= a["ma50"][i] and a["close"][i] < a["ma50"][i]:
        dr = -1
    if dr == 0:
        continue

    def touched(k):
        return (a["low"][k] <= a["ma50"][k]) if dr > 0 else (a["high"][k] >= a["ma50"][k])
    d = day_a[i]
    sd = sess_a[i]
    prof = PD_PROF.get(sd)
    pdh, pdl = PD_HI.get(sd, np.nan), PD_LO.get(sd, np.nan)
    CAND.append(dict(
        i=i, dr=dr, day=d, sess=sd,
        fading=a["volume"][i] < a["vol_maN"][i],
        ft1=not touched(i - 1),
        ft3=not (touched(i - 1) or touched(i - 2) or touched(i - 3)),
        vwap_ok=(a["close"][i] > a["vwap"][i]) if dr > 0 else (a["close"][i] < a["vwap"][i]),
        onrange=ON_RANGE.get(sd, np.nan),
        onvol=ON_VOL_REL.get(sd, np.nan),
        pd_room=((pdh - a["close"][i]) if dr > 0 else (a["close"][i] - pdl)),
        in_value=(prof is not None and prof["val"] <= a["close"][i] <= prof["vah"]),
        beyond_pd=(a["close"][i] > pdh) if dr > 0 else (a["close"][i] < pdl),
    ))
print(f"candidates (any 50-MA touch in stacked trend, window): {len(CAND)}  "
      f"of which fading-volume: {sum(c['fading'] for c in CAND)}", flush=True)


def resolve(i, dr, stop_mode="struct", tg=3.0):
    if i + 1 >= len(M) or day_a[i + 1] != day_a[i]:
        return None
    entry = a["open"][i + 1] + dr * TICK
    if stop_mode == "struct":
        ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i])
        risk = abs(entry - ref) + TICK
    else:                                            # fixed ATR bracket, e.g. "atr1.5"
        k = float(stop_mode[3:])
        if not np.isfinite(a["atr14"][i]):
            return None
        risk = k * a["atr14"][i]
    if risk < 5 or risk > 70:
        return None
    stop = entry - dr * risk
    tgt = entry + dr * tg * risk
    gross, j = None, i + 1
    while j < len(M) and day_a[j] == day_a[i]:
        if t_a[j] >= FLAT:
            gross = dr * (a["close"][j] - entry); break
        hit_stop = (a["low"][j] <= stop) if dr > 0 else (a["high"][j] >= stop)
        hit_tgt = (a["high"][j] >= tgt) if dr > 0 else (a["low"][j] <= tgt)
        if hit_stop:
            gross = -risk - TICK; break
        if hit_tgt:
            gross = tg * risk - TICK; break
        j += 1
    if gross is None:
        j = min(j, len(M) - 1)
        gross = dr * (a["close"][j] - entry)
    net = gross * PV - COMM
    return dict(net=net, R=net / (risk * PV), risk=risk, res=j)


def run(filt=None, stop_mode="struct", tg=3.0, need_fading=True, one_pos=False, daystop=False):
    rows = []
    for c in CAND:
        if need_fading and not c["fading"]:
            continue
        if filt and not filt(c):
            continue
        r = resolve(c["i"], c["dr"], stop_mode, tg)
        if r is None:
            continue
        rows.append({**c, **r})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values(["day", "i"]).reset_index(drop=True)
    if one_pos or daystop:
        keep = []
        for d, gd in df.groupby("day", sort=True):
            taken = []
            for ix, r in gd.iterrows():
                if daystop and any(res <= r.i and nt < 0 for res, nt in taken):
                    continue
                if (one_pos or daystop) and any(res > r.i for res, _ in taken):
                    continue
                keep.append(ix)
                taken.append((r.res, r.net))
        df = df.loc[keep].reset_index(drop=True)
    return df


def block(df, name):
    print(f"\n### {name}")
    if not len(df):
        print("    no trades"); return {}
    out = {}
    rows = [("2023", df[df.day.str[:4] == "2023"]), ("2024", df[df.day.str[:4] == "2024"]),
            ("2025", df[df.day.str[:4] == "2025"]), ("2026", df[df.day.str[:4] == "2026"]),
            ("TRAIN", df[df.day <= TRAIN_END]), ("TEST", df[df.day > TRAIN_END])]
    for lab, s in rows:
        if not len(s):
            print(f"    {lab:5s}  n=  0"); continue
        eq = s.net.cumsum().values
        dd = float((np.maximum.accumulate(eq) - eq).max())
        gp, gl = s.R[s.R > 0].sum(), -s.R[s.R < 0].sum()
        print(f"    {lab:5s}  n={len(s):4d}  WR {100*(s.R>0).mean():3.0f}%  "
              f"E[R] {s.R.mean():+.3f}  PF {gp/gl if gl>0 else float('inf'):4.2f}  "
              f"net ${s.net.sum():+9,.0f}  maxDD ${dd:8,.0f}")
        out[lab] = (len(s), s.net.sum(), s.R.mean())
    return out


VARIANTS = [
    ("1 trend-alone (no volume rule)",      dict(need_fading=False)),
    ("2 V0 as committed",                   dict()),
    ("3 V0 + first-touch(1)",               dict(filt=lambda c: c["ft1"])),
    ("4 V0 + first-touch(3)",               dict(filt=lambda c: c["ft3"])),
    ("5 V0 + one-position-at-a-time",       dict(one_pos=True)),
    ("6 V0 + day-stop (realtime, 1-pos)",   dict(daystop=True)),
    ("7 V0 + ft3 + day-stop",               dict(filt=lambda c: c["ft3"], daystop=True)),
    ("8 V0, target 2R",                     dict(tg=2.0)),
    ("9 V0, ATR1.5 stop / 3R",              dict(stop_mode="atr1.5")),
    ("10 V0, ATR1.5 stop / 2R",             dict(stop_mode="atr1.5", tg=2.0)),
    ("11 FRIEND SPEC: ft1 + ATR1.5 / 3R",   dict(filt=lambda c: c["ft1"], stop_mode="atr1.5")),
    ("12 friend spec + day-stop",           dict(filt=lambda c: c["ft1"], stop_mode="atr1.5", daystop=True)),
    ("13 V0 + VWAP side",                   dict(filt=lambda c: c["vwap_ok"])),
    ("14 V0 + overnight range >= 100",      dict(filt=lambda c: np.isfinite(c["onrange"]) and c["onrange"] >= 100)),
    ("15 V0 + room to PD extreme >= 3R*",   dict(filt=lambda c: np.isfinite(c["pd_room"]) and c["pd_room"] >= 3 * 25)),
    ("16 V0 + ft3 + day-stop + VWAP",       dict(filt=lambda c: c["ft3"] and c["vwap_ok"], daystop=True)),
    ("17 V0 + ft3 + day-stop + onr>=100",   dict(filt=lambda c: c["ft3"] and np.isfinite(c["onrange"]) and c["onrange"] >= 100, daystop=True)),
    ("18 ft3 + day-stop + VWAP + onr>=100", dict(filt=lambda c: c["ft3"] and c["vwap_ok"] and np.isfinite(c["onrange"]) and c["onrange"] >= 100, daystop=True)),
]

if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("VARIANT GRID — per-year, TRAIN 23-24 (fitting ground) / TEST 25-26 (holdout)")
    print("=" * 100)
    summary = []
    for name, kw in VARIANTS:
        df = run(**kw)
        st = block(df, name)
        summary.append(dict(
            variant=name,
            n=st.get("TRAIN", (0, 0, 0))[0] + st.get("TEST", (0, 0, 0))[0],
            y2024=st.get("2024", (0, 0.0, 0.0))[1],
            train=st.get("TRAIN", (0, 0.0, 0.0))[1],
            test=st.get("TEST", (0, 0.0, 0.0))[1],
            testER=st.get("TEST", (0, 0.0, np.nan))[2]))
    R = pd.DataFrame(summary)
    print("\n" + "=" * 100)
    print("RANKING — the bar: 2024 toward flat AND TEST not gutted")
    print("=" * 100)
    print(f"{'variant':<38} {'n':>5} {'2024$':>10} {'TRAIN$':>10} {'TEST$':>10} {'TEST E[R]':>10}")
    for _, r in R.sort_values("y2024", ascending=False).iterrows():
        print(f"{r.variant:<38} {r.n:>5} {r.y2024:>+10,.0f} {r.train:>+10,.0f} "
              f"{r.test:>+10,.0f} {r.testER:>+10.3f}")
    R.to_csv(f"{S}/london_tp_variants.csv", index=False)
    print(f"\n* variant 15 uses a 75pt proxy for 3R (median struct risk ~25pt) so the filter "
          f"stays independent of the stop model.")
    print(f"wrote {S}/london_tp_variants.csv")
