#!/usr/bin/env python3
"""CURRENCY-PROS 15m STRATEGY — independent test on NQ, New York hours. RESEARCH ONLY.

Canon and the live path are untouched. This tests a third-party strategy described in a
YouTube video, coded from the transcript.

################ PARAMETERS FROZEN BEFORE THE FIRST RUN. NOT TUNED. ################
The video leaves ~7 parameters unspecified. Each is fixed here at the most standard
textbook default, chosen BEFORE seeing any result, and never changed afterwards. Anything
else would reproduce the selection error the video already commits.

  SWING_N        = 2      fractal swing: extreme of the 2 bars each side. A swing is only
                          USABLE at i+2 (confirmation lag) — no lookahead anywhere.
  BOS            = CLOSE beyond the prior confirmed swing extreme (not a wick).
  SWEEP_LOOKBACK = 20     bars before the BOS in which a sweep must appear.
  SWEEP          = a bar whose HIGH exceeds a prior confirmed swing high but whose CLOSE is
                   back below it (bearish; mirrored for bullish).
  FVG            = 3-bar gap: low[i-1] > high[i+1] (bearish). Any non-zero gap counts.
  FVG_NEAR       = 0.10   the FVG must contain the entry level, or sit within 10% of the leg
                          range of it, to score.
  HTF_LOOKBACK   = 60     4-hour bars defining the higher-timeframe range (~10 trading days).
  HTF            = premium/discount vs the 50% mark. Sell only in premium, buy only in discount.
  MIN_SCORE      = 3 of 4 — what the video actually demonstrates (takes 3/4 twice, calls 4/4
                   a "no-brainer"). He never states a minimum.
  ENTRY          = 75% retracement (primary), 71% reported alongside.
                   E = low + f*(high-low) for a short, giving exactly f/(1-f) R:R:
                   0.75 -> 3.00R, 0.71 -> 2.45R. The "1:3" is arithmetic, not a result.
  STOP / TARGET  = range extreme / opposite extreme.
  VALID_HOURS    = 48     limit order expires; also invalidated if the stop level trades
                          before the entry fills.
####################################################################################

FILL AND OUTCOME RESOLUTION USE 1-MINUTE BARS, not 15-minute. Resolving stop-vs-target inside a
15-minute bar that contains both is the classic ambiguity that flatters backtests; this walks
the minute series so the sequence is real.

NEW YORK ONLY: a trade counts when its ENTRY FILLS between 09:30 and 16:00 ET (primary). The
08:00-16:00 window is reported alongside, since the rest of this project uses it.

THE NULL THAT MATTERS: the geometry forces a fixed 3.00R payoff, so under a driftless random
walk the breakeven win rate is exactly 1/(1+3) = 25%. The claim is therefore testable as "win
rate materially above 25%", with a binomial p and a day-clustered bootstrap CI. A second test
asks whether 4/4 actually beats 3/4 — his central claim that stacking confluences means
something.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/thirdparty"
os.makedirs(OUT, exist_ok=True)

SWING_N, SWEEP_LOOKBACK, FVG_NEAR, HTF_LOOKBACK = 2, 20, 0.10, 60
MIN_SCORE, VALID_HOURS = 3, 48
FIBS = (0.75, 0.71)
NY = "America/New_York"

m1 = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                     columns=["ts_event", "open", "high", "low", "close"])
m1["ts"] = pd.to_datetime(m1.ts_event, utc=True)
m1 = m1.drop_duplicates("ts").set_index("ts").sort_index()
print(f"1-minute bars: {len(m1):,}  {m1.index[0]} -> {m1.index[-1]}")


def resample(df, rule):
    o = df.resample(rule, label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"))
    return o.dropna()


m15, h4 = resample(m1, "15min"), resample(m1, "4h")
print(f"15-minute bars: {len(m15):,} | 4-hour bars: {len(h4):,}")
H, L, C = m15.high.values, m15.low.values, m15.close.values
IDX, n = m15.index, len(m15)

sw_hi, sw_lo = np.zeros(n, bool), np.zeros(n, bool)
for i in range(SWING_N, n - SWING_N):
    if (H[i] > H[i - SWING_N:i]).all() and (H[i] > H[i + 1:i + SWING_N + 1]).all():
        sw_hi[i] = True
    if (L[i] < L[i - SWING_N:i]).all() and (L[i] < L[i + 1:i + SWING_N + 1]).all():
        sw_lo[i] = True
conf_hi = np.flatnonzero(sw_hi)
conf_lo = np.flatnonzero(sw_lo)
print(f"swings: {len(conf_hi):,} highs, {len(conf_lo):,} lows")


def last_confirmed(arr, before_bar):
    """Most recent swing whose CONFIRMATION (idx+SWING_N) is <= before_bar."""
    k = np.searchsorted(arr, before_bar - SWING_N, side="right") - 1
    return int(arr[k]) if k >= 0 else None


h4h, h4l, h4c, h4_idx = h4.high.values, h4.low.values, h4.close.values, h4.index


def htf_state(ts):
    k = int(h4_idx.searchsorted(ts, side="right")) - 1
    if k < HTF_LOOKBACK:
        return None
    hi = h4h[k - HTF_LOOKBACK + 1:k + 1].max()
    lo = h4l[k - HTF_LOOKBACK + 1:k + 1].min()
    if hi <= lo:
        return None
    return "premium" if h4c[k] > lo + 0.5 * (hi - lo) else "discount"


print("detecting setups ...", flush=True)
setups = []
for j in range(SWING_N + 1, n):
    for side in ("short", "long"):
        arr = conf_lo if side == "short" else conf_hi
        ref = last_confirmed(arr, j - 1)
        if ref is None:
            continue
        lvl = L[ref] if side == "short" else H[ref]
        if not ((C[j] < lvl) if side == "short" else (C[j] > lvl)):
            continue
        prev = last_confirmed(arr, j - 2)
        if prev is not None and ((C[j - 1] < L[prev]) if side == "short" else (C[j - 1] > H[prev])):
            continue                                    # only the FIRST break of a level
        lo_b = max(0, j - SWEEP_LOOKBACK)
        sweep_bar = sweep_px = None
        for b in range(j - 1, lo_b - 1, -1):
            s = last_confirmed(conf_hi if side == "short" else conf_lo, b - 1)
            if s is None:
                continue
            sl = H[s] if side == "short" else L[s]
            if (H[b] > sl and C[b] < sl) if side == "short" else (L[b] < sl and C[b] > sl):
                sweep_bar, sweep_px = b, (H[b] if side == "short" else L[b])
                break
        nxt = conf_lo if side == "short" else conf_hi
        k = np.searchsorted(nxt, j, side="right")
        if k >= len(nxt):
            continue
        end = int(nxt[k])
        confirm = end + SWING_N
        if confirm >= n:
            continue
        if side == "short":
            rng_hi = sweep_px if sweep_px is not None else float(H[lo_b:end + 1].max())
            rng_lo = float(L[j:end + 1].min())
        else:
            rng_lo = sweep_px if sweep_px is not None else float(L[lo_b:end + 1].min())
            rng_hi = float(H[j:end + 1].max())
        if rng_hi <= rng_lo:
            continue
        fvg = []
        for b in range(max(lo_b, 1), min(end, n - 1)):
            if side == "short" and L[b - 1] > H[b + 1]:
                fvg.append((float(H[b + 1]), float(L[b - 1])))
            if side == "long" and H[b - 1] < L[b + 1]:
                fvg.append((float(H[b - 1]), float(L[b + 1])))
        st = htf_state(IDX[confirm])
        setups.append(dict(side=side, confirm=confirm, rng_hi=rng_hi, rng_lo=rng_lo,
                           span=rng_hi - rng_lo, fvg=fvg, has_sweep=sweep_bar is not None,
                           htf=st, aligned=(st == "premium") if side == "short"
                           else (st == "discount")))
print(f"raw setups detected: {len(setups):,}")

M1H, M1L, M1I = m1.high.values, m1.low.values, m1.index


def simulate(s, fib):
    hi, lo, span = s["rng_hi"], s["rng_lo"], s["span"]
    if s["side"] == "short":
        entry, stop, target = lo + fib * span, hi, lo
    else:
        entry, stop, target = hi - fib * span, lo, hi
    near = any(min(a, b) - FVG_NEAR * span <= entry <= max(a, b) + FVG_NEAR * span
               for a, b in s["fvg"])
    score = int(s["has_sweep"]) + 1 + int(near) + int(s["aligned"])
    t0 = IDX[s["confirm"]] + pd.Timedelta(minutes=15)
    k0 = int(M1I.searchsorted(t0, side="left"))
    kmax = min(int(M1I.searchsorted(t0 + pd.Timedelta(hours=VALID_HOURS), side="right")),
               len(M1I) - 1)
    if k0 >= kmax:
        return None
    fill = None
    for k in range(k0, kmax):
        if s["side"] == "short":
            if M1H[k] >= stop:
                break
            if M1H[k] >= entry:
                fill = k
                break
        else:
            if M1L[k] <= stop:
                break
            if M1L[k] <= entry:
                fill = k
                break
    if fill is None:
        return None
    for k in range(fill, min(fill + 60 * 24 * 5, len(M1I) - 1)):
        if s["side"] == "short":
            if M1H[k] >= stop:
                return dict(score=score, R=-1.0, fill_k=fill, exit_k=k)
            if M1L[k] <= target:
                return dict(score=score, R=fib / (1 - fib), fill_k=fill, exit_k=k)
        else:
            if M1L[k] <= stop:
                return dict(score=score, R=-1.0, fill_k=fill, exit_k=k)
            if M1H[k] >= target:
                return dict(score=score, R=fib / (1 - fib), fill_k=fill, exit_k=k)
    return None


print("simulating on 1-minute bars ...", flush=True)
rows = []
for s in setups:
    for fib in FIBS:
        r = simulate(s, fib)
        if r is None:
            continue
        ts = M1I[r["fill_k"]].tz_convert(NY)
        rows.append(dict(fib=fib, side=s["side"], score=r["score"], R=r["R"],
                         fill=str(ts), day=ts.strftime("%Y-%m-%d"),
                         hm=ts.hour * 60 + ts.minute,
                         hold_min=int(r["exit_k"] - r["fill_k"]),
                         htf=s["htf"], has_sweep=s["has_sweep"], span=s["span"]))
T = pd.DataFrame(rows)
T.to_csv(f"{OUT}/cp_trades_all.csv", index=False)
print(f"filled + resolved trades (all hours, both fib levels): {len(T):,}")
json.dump(dict(n_setups=len(setups), n_trades=int(len(T)),
               params=dict(SWING_N=SWING_N, SWEEP_LOOKBACK=SWEEP_LOOKBACK, FVG_NEAR=FVG_NEAR,
                           HTF_LOOKBACK=HTF_LOOKBACK, MIN_SCORE=MIN_SCORE,
                           VALID_HOURS=VALID_HOURS, FIBS=list(FIBS))),
          open(f"{OUT}/cp_raw.json", "w"), indent=1)
print(f"wrote {OUT}/cp_trades_all.csv")
