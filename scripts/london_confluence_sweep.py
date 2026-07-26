#!/usr/bin/env python3
"""CONFLUENCE SWEEP for the London 10-13 UK book: does a different rejection LEVEL
reach the 3R target faster than the 50-MA, without shedding expectancy?

Motivation: hold-time analysis showed the book's edge lives in long holds
(<=1h buckets run -1.05R/-0.03R/-0.22R; >2h runs +2.10R, 49% of trades). So
"shorten the trade" and "keep the edge" pull against each other. The only
interesting question is whether some OTHER level gets to 3R quicker rather than
just selecting the losing short-hold bucket.

METHOD: swap ONLY the trigger level. Everything else is byte-identical to
london_conviction.py -- 10:00-13:00 UK window, MA-stack trend filter, fading
volume, entry at next M15 open +1 tick, structural stop min(swing-5, LEVEL) -1
tick clamped 5-70pt, fixed 3R target, day-stop, 16:30 flat, 2-tick slip + $5 RT.

LEVELS TESTED (all developing / prior-session -> no lookahead):
  ma50            the incumbent (control)
  lvwap           London-session VWAP, 08:00 UK anchor, developing
  lvwap_1s/_2s    London VWAP +/-1sigma, +/-2sigma (side chosen by trade direction)
  pd_poc/vah/val  PRIOR UK day's full-session volume profile (70% value area)
  on_poc/vah/val  overnight profile, 22:00 UK prior day -> 08:00 UK current day

CAVEAT -- MULTIPLE COMPARISONS: this sweeps ~11 level definitions on the SAME
2025-07..2026-07 window the book was frozen on. Any winner here is a HOLDOUT
CANDIDATE, not a result. Validate on 2023-24 (bars are present) before believing it.

RESULT (2026-07-26, in-sample 2025-07-01 -> 2026-07-15):
  level        n   WR     netR   avgR  medHold  meanHold  R/hour  exit mix
  ma50        55  56%   +67.95  +1.24     120m      123m   +0.60  31 tgt / 24 stop   <- control
  lvwap       91  36%   +38.65  +0.42     120m      119m   +0.21  33 tgt / 58 stop
  lvwap_1s    73  34%   +25.27  +0.35      75m       96m   +0.22  25 tgt / 48 stop
  lvwap_2s    25  28%    +2.16  +0.09      60m       83m   +0.06   7 tgt / 18 stop
  pd_poc      13  23%    -1.31  -0.10      60m       98m   -0.06   3 tgt / 10 stop
  pd_vah      20  45%   +15.59  +0.78     112m      128m   +0.36   9 tgt / 11 stop
  pd_val       9  33%    +2.78  +0.31     105m      107m   +0.17   3 tgt /  6 stop
  on_poc      39  46%   +29.30  +0.75     135m      138m   +0.33  17 tgt / 21 stop / 1 time
  on_vah      31  32%    +5.55  +0.18     120m      128m   +0.08   9 tgt / 21 stop / 1 time
  on_val      12  50%   +11.75  +0.98     105m      100m   +0.59   6 tgt /  6 stop

VERDICT: nothing beats the 50-MA. It wins avgR, netR, WR and R/hour simultaneously.
Every level that DID shorten the hold (lvwap_1s 96m, lvwap_2s 83m, pd_poc 98m) paid for
it with expectancy (+0.35R / +0.09R / -0.10R) -- i.e. shortening selects into the losing
short-hold bucket exactly as the hold-time study predicted. on_val ties on R/hour (+0.59)
on n=12, which is noise, not a signal. NO holdout run is warranted: there is no candidate.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_confluence_sweep.py [--start YYYY-MM-DD --end YYYY-MM-DD]
"""
import os
import sys
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
BIN, VA = 1.0, 0.70                      # profile bin (pts) and value-area coverage

START = "2025-07-01"
END = "2026-07-15"
if "--start" in sys.argv:
    START = sys.argv[sys.argv.index("--start") + 1]
if "--end" in sys.argv:
    END = sys.argv[sys.argv.index("--end") + 1]

print(f"load bars  window {START} -> {END} ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukt"] = b.uk.dt.time
b["ukday"] = b.uk.dt.strftime("%Y-%m-%d")


# ---------- volume profile helpers (value-area algorithm as used in canon) ----------
def value_area(hist):
    if not hist:
        return None
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * BIN
    total = arr.sum()
    n = len(arr)
    if total <= 0:
        return None
    poc = int(arr.argmax())
    lo = hi = poc
    cov = arr[poc]
    tgt = VA * total
    while cov < tgt - 1e-9 and (lo > 0 or hi < n - 1):
        bl = arr[lo - 1] if lo > 0 else -np.inf
        ab = arr[hi + 1] if hi < n - 1 else -np.inf
        if ab >= bl:
            hi += 1; cov += arr[hi]
        else:
            lo -= 1; cov += arr[lo]
    return dict(poc=float(centers[poc]), vah=float(centers[hi]), val=float(centers[lo]))


def profile_of(frame):
    """Volume spread evenly across each bar's price bins (standard TPO-ish approximation)."""
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


print("build prior-day + overnight profiles ...", flush=True)
# pre-split once: filtering the whole frame inside a per-day loop is O(days*rows)
by_day = {d: g for d, g in b.groupby("ukday", sort=True)}
days = sorted(by_day)
late = {d: g[g.ukt >= dtime(22, 0)] for d, g in by_day.items()}
early = {d: g[g.ukt < dtime(8, 0)] for d, g in by_day.items()}
PD, ON = {}, {}
for k, d in enumerate(days):
    if k > 0:                                    # PRIOR full UK day -> no lookahead
        PD[d] = profile_of(by_day[days[k - 1]])
    segs = [early[d]]
    if k > 0:
        segs.insert(0, late[days[k - 1]])
    seg = pd.concat(segs) if segs else None
    ON[d] = profile_of(seg) if seg is not None and len(seg) else None

# ---------- M15 frame + indicators ----------
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

# London-session developing VWAP + sigma bands (08:00 UK anchor, no lookahead)
tp = (m.high + m.low + m.close) / 3.0
inl = m.ukt >= dtime(8, 0)
gd = m.ukday.where(inl)
cv = m.volume.where(inl).groupby(gd).cumsum()
cvp = (tp * m.volume).where(inl).groupby(gd).cumsum()
cvp2 = (tp * tp * m.volume).where(inl).groupby(gd).cumsum()
m["lvwap"] = cvp / cv
m["lvwap_sd"] = np.sqrt(((cvp2 / cv) - m.lvwap ** 2).clip(lower=0))

M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= START) & (M.ukday <= END)].reset_index(drop=True)
a = {c: M[c].values for c in ["uts", "open", "high", "low", "close", "volume",
                              "ma20", "ma50", "ma200", "v10", "slo", "shi", "lvwap", "lvwap_sd"]}
ud, utt = M.ukday.values, M.ukt.values


def level_at(name, i, dr):
    """The rejection level for bar i given trade direction dr. NaN -> no trade."""
    if name == "ma50":
        return a["ma50"][i]
    if name == "lvwap":
        return a["lvwap"][i]
    if name in ("lvwap_1s", "lvwap_2s"):
        k = 1.0 if name.endswith("1s") else 2.0
        v, sd = a["lvwap"][i], a["lvwap_sd"][i]
        # longs pull back to the LOWER band; shorts rally to the UPPER band
        return v - dr * k * sd
    d = ud[i]
    src = PD if name.startswith("pd_") else ON
    p = src.get(d)
    if p is None:
        return np.nan
    return p[name.split("_")[1]]


LEVELS = ["ma50", "lvwap", "lvwap_1s", "lvwap_2s",
          "pd_poc", "pd_vah", "pd_val", "on_poc", "on_vah", "on_val"]


def run(level):
    rows = []
    for i in range(1, len(M) - 1):
        d = ud[i]
        if d in ("2025-11-28", "2026-04-03") or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
            continue
        up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
        dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
        if not (up or dn):
            continue
        dr = 1 if up else -1
        L = level_at(level, i, dr)
        if not np.isfinite(L):
            continue
        # rejection: wick through the level, close back on the trend side
        wick = (a["low"][i] <= L and a["close"][i] > L) if dr > 0 else (a["high"][i] >= L and a["close"][i] < L)
        if not wick:
            continue
        if not (a["v10"][i] > 0 and a["volume"][i] < a["v10"][i]):
            continue
        en = a["open"][i + 1] + dr * TICK
        rf = min(a["slo"][i], L) if dr > 0 else max(a["shi"][i], L)
        rk = abs(en - rf) + TICK
        if rk < 5 or rk > 70:
            continue
        st, tg = en - dr * rk, en + dr * 3 * rk
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
            gg = dr * (a["close"][min(j, len(M) - 1)] - en); how = "dayend"
        rows.append(dict(day=d, ent=str(utt[i]), net=gg * PV - COMM,
                         R=(gg * PV - COMM) / (rk * PV), bars=j - i, how=how, rk=rk))
    if not rows:
        return pd.DataFrame()
    A = pd.DataFrame(rows).sort_values(["day", "ent"]).reset_index(drop=True)
    keep = []
    for d, g in A.groupby("day"):
        stp = False
        for _, r in g.iterrows():
            if stp:
                continue
            keep.append(r.name)
            if r.net < 0:
                stp = True
    D = A.loc[keep].copy().reset_index(drop=True)
    D["mins"] = D.bars * 15
    return D


if __name__ == "__main__":
    print(f"\n{'level':<10} {'n':>3} {'WR':>4} {'netR':>8} {'avgR':>6} "
          f"{'medHold':>8} {'meanHold':>9} {'R/hour':>7}  exit mix")
    print("-" * 82)
    res = {}
    for lv in LEVELS:
        D = run(lv)
        if not len(D):
            print(f"{lv:<10}   0   --       --     --       --        --       --  (no trades)")
            continue
        res[lv] = D
        rh = D.R.sum() / (D.mins.sum() / 60.0)
        mark = "  <- control" if lv == "ma50" else ""
        print(f"{lv:<10} {len(D):>3} {(D.R>0).mean()*100:>3.0f}% {D.R.sum():>+8.2f} {D.R.mean():>+6.2f} "
              f"{D.mins.median():>7.0f}m {D.mins.mean():>8.0f}m {rh:>+7.2f}  "
              f"{dict(D.how.value_counts())}{mark}")

    print("\nR/hour = total R divided by total hours in market (capital-efficiency view).")
    print("MULTIPLE COMPARISONS: ~10 level definitions on the frozen 2025-26 window.")
    print("Anything that beats ma50 here is a HOLDOUT CANDIDATE -- rerun on 2023-24 before believing it.")
