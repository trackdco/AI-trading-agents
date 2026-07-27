#!/usr/bin/env python3
"""THE YOUTUBER'S GOLD REVERSAL SETUP — mechanised and tested honestly.

His 3-step spec, as stated across the videos:
  1 CONDITION  identify a middle-timeframe range over the last ~4-5 hours
  2 AREA       only trade the EXTREMES: sells in the upper portion, buys in the lower portion
               ("price stretches like an elastic band"); never the middle of the range
  3 ENTRY      wait for a 1-minute "type 3" shift = break a low then break a high (or mirror),
               i.e. a change in the sequence of highs/lows; enter on the pullback; stop beyond
               the extreme; target back toward the mean (~50% of the range / of the extension)
  TIME         "second hour of Asia", ~11:00 AEST, which is a fresh 4H candle open
  CLAIM        80%+ win rate at ~1-1.5R, boosted to 83% by DXY correlation

WHAT THIS TESTS AND WHAT IT CANNOT
  tested   the price-action core: range -> overextension -> 1-min structure shift -> mean-revert
  NOT tested  the DXY inverse-correlation filter. DXY is an ICE product; the Databento GLBX pull
              is CME only, so there are no dollar-index bars in this repo. His single biggest
              claimed edge (+16-19pp win rate) is therefore UNTESTED here, not disproven.
  NOT tested  his discretion: which range "counts", which shift is valid, closing losers early,
              adding to winners. A mechanical encoding is necessarily one interpretation.

DATA  data/reference/gc_1m_master.parquet, Jul 2025 -> Jul 2026 (377,920 1-min bars).
      ONE REGIME (gold 3290 -> 5623). Split-half train/test is possible; a cross-regime holdout
      is NOT. Anything positive here is provisional until 2021-22 data exists.

THE NULL  the honest question is not "is it profitable" but "does the ENTRY LOGIC beat random
      entries with the identical bracket geometry?". For every real signal we draw a random bar
      in the same session window and run the same stop/target machinery. If the setup cannot beat
      its own random-entry twin, the pattern is decoration and the results are bracket geometry.

COSTS  MGC: $10/point, 0.10 tick. Default 2 ticks round-trip slippage + $1.50 commission.
      Asia-session gold spreads are wider than RTH, so a cost-sensitivity row is printed.

    python3 scripts/gold_reversal_test.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PQ = os.path.join(HERE, "data/reference/gc_1m_master.parquet")
PV, TICK, COMM = 10.0, 0.10, 1.50          # MGC
SLIP_TICKS = 2.0                            # round-trip, default
SPLIT = "2026-01-15"
rng = np.random.default_rng(11)

# --- spec parameters (his numbers where he gave them) -----------------------------------------
RANGE_BARS = 300          # ~5 hours of 1-min bars for the middle-timeframe range
EXT_ZONE = 0.85           # "upper/lower portion" of the range for the overextension
SHIFT_LOOK = 20           # bars used to define the recent swing for the structure shift
PULLBACK = 0.50           # enter on the 50% pullback of the breaking move
MIN_RANGE_PT = 8.0        # a range smaller than this is noise on gold
MAX_RANGE_PT = 150.0
MIN_RISK_PT = 1.5         # skip degenerate sub-tick stops
MAX_RISK_PT = 25.0
MAX_HOLD = 120            # scalp: abandon after 2h

print("load gold ...", flush=True)
b = pd.read_parquet(PQ)
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b = b.sort_values("ts").reset_index(drop=True)
b["day"] = b.ts.dt.strftime("%Y-%m-%d")
O, H, L, C = b.open.values, b.high.values, b.low.values, b.close.values
TS = b.ts.values
hour = b.ts.dt.hour.values
day_arr = b.day.values
n = len(b)
print(f"  {n:,} bars  {b.ts.min()} -> {b.ts.max()}", flush=True)

# rolling range over the prior RANGE_BARS (strictly prior: shift by 1)
roll_hi = pd.Series(H).rolling(RANGE_BARS).max().shift(1).values
roll_lo = pd.Series(L).rolling(RANGE_BARS).min().shift(1).values
# recent swing extremes for the shift test (strictly prior)
sw_hi = pd.Series(H).rolling(SHIFT_LOOK).max().shift(1).values
sw_lo = pd.Series(L).rolling(SHIFT_LOOK).min().shift(1).values


def signals(hours=None):
    """Return list of (index, direction, stop_price, range_hi, range_lo).

    SELL logic (BUY mirrors):
      - a valid 5h range exists
      - within the last SHIFT_LOOK bars price OVEREXTENDED into the top EXT_ZONE of that range
      - the current bar CLOSES BELOW the prior swing low  -> the 'type 3' shift down
      - stop goes above the extension high; entry is the pullback toward 50% of the break
    """
    out = []
    for i in range(RANGE_BARS + SHIFT_LOOK, n - MAX_HOLD - 2):
        if hours is not None and hour[i] not in hours:
            continue
        rh, rl = roll_hi[i], roll_lo[i]
        if not (np.isfinite(rh) and np.isfinite(rl)):
            continue
        rsize = rh - rl
        if not (MIN_RANGE_PT <= rsize <= MAX_RANGE_PT):
            continue
        lookback = slice(i - SHIFT_LOOK, i)
        ext_hi = H[lookback].max()
        ext_lo = L[lookback].min()
        # SELL: overextended into the top of the range, then breaks the recent swing low
        if (ext_hi - rl) / rsize >= EXT_ZONE and C[i] < sw_lo[i]:
            out.append((i, -1, ext_hi, rh, rl))
        # BUY: overextended into the bottom, then breaks the recent swing high
        elif (ext_lo - rl) / rsize <= (1 - EXT_ZONE) and C[i] > sw_hi[i]:
            out.append((i, +1, ext_lo, rh, rl))
    return out


def resolve(i, d, stop_px, rh, rl, r_mult, target_mode="R", entry_mode="pullback"):
    """Walk forward from the shift bar. Returns dict or None."""
    brk_from = H[i - SHIFT_LOOK:i].max() if d < 0 else L[i - SHIFT_LOOK:i].min()
    brk_to = C[i]
    if entry_mode == "pullback":
        entry_px = brk_to + (brk_from - brk_to) * PULLBACK
    else:
        entry_px = C[i]
    slip = SLIP_TICKS * TICK
    # find the fill: price must retrace to entry_px within a few bars
    fill = None
    for k in range(i + 1, min(i + 31, n)):
        if (d < 0 and H[k] >= entry_px) or (d > 0 and L[k] <= entry_px):
            fill = k
            break
        # invalidate if the stop is breached before we ever fill
        if (d < 0 and H[k] > stop_px) or (d > 0 and L[k] < stop_px):
            return None
    if fill is None:
        return None
    entry = entry_px - d * slip / 2          # slippage against us on entry
    risk = abs(entry - stop_px)
    if not (MIN_RISK_PT <= risk <= MAX_RISK_PT):
        return None
    if target_mode == "R":
        tgt = entry + d * r_mult * risk
    else:                                     # mean of the range
        tgt = (rh + rl) / 2.0
        if (d < 0 and tgt >= entry) or (d > 0 and tgt <= entry):
            return None
    gross = None
    for k in range(fill + 1, min(fill + MAX_HOLD + 1, n)):
        hit_s = (H[k] >= stop_px) if d < 0 else (L[k] <= stop_px)
        hit_t = (L[k] <= tgt) if d < 0 else (H[k] >= tgt)
        if hit_s:                             # stop checked first (pessimistic)
            gross = -risk; break
        if hit_t:
            gross = abs(tgt - entry); break
    if gross is None:
        k = min(fill + MAX_HOLD, n - 1)
        gross = d * (C[k] - entry)
    net = gross * PV - COMM - (SLIP_TICKS / 2 * TICK) * PV
    return dict(i=fill, day=day_arr[fill], d=d, risk=risk,
                R=net / (risk * PV), net=net)


def build(sigs, r_mult, target_mode="R", entry_mode="pullback"):
    rows = []
    for (i, d, sp, rh, rl) in sigs:
        r = resolve(i, d, sp, rh, rl, r_mult, target_mode, entry_mode)
        if r:
            rows.append(r)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["train"] = df.day < SPLIT
    return df


def randomised(sigs, r_mult, target_mode="R"):
    """Same count, same session hours, same bracket machinery -- random bars."""
    pool = [s[0] for s in sigs]
    if not pool:
        return pd.DataFrame()
    rows = []
    for (i, d, sp, rh, rl) in sigs:
        j = int(rng.choice(pool))             # a random bar from the same signal-hour pool
        rhj, rlj = roll_hi[j], roll_lo[j]
        if not (np.isfinite(rhj) and np.isfinite(rlj)):
            continue
        # same geometry: stop a comparable distance away, same direction
        dist = abs(sp - C[i])
        spj = C[j] + (-d) * dist if dist > 0 else C[j] + (-d) * 3.0
        r = resolve(j, d, spj, rhj, rlj, r_mult, target_mode, entry_mode="market")
        if r:
            rows.append(r)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["train"] = df.day < SPLIT
    return df


def line(df, lab):
    if len(df) < 5:
        print(f"    {lab:24s} n={len(df):4d}   (too few)"); return
    wr = 100 * (df.R > 0).mean()
    eq = df.sort_values("day").net.cumsum().values
    ddn = float((np.maximum.accumulate(eq) - eq).max())
    print(f"    {lab:24s} n={len(df):4d}  WR {wr:3.0f}%  E[R] {df.R.mean():+.3f}  "
          f"net ${df.net.sum():+8,.0f}  maxDD ${ddn:7,.0f}")


if __name__ == "__main__":
    # Asia 2nd hour: 11:00 AEST = 01:00 UTC (AEDT -> 00:00 UTC). Test the window and a wide one.
    WINDOWS = {"asia 2nd hr (00-02 UTC)": {0, 1},
               "asia block (22-04 UTC)": {22, 23, 0, 1, 2, 3},
               "all hours": None}
    for wname, hrs in WINDOWS.items():
        sigs = signals(hrs)
        print(f"\n{'='*96}\n{wname}   raw signals: {len(sigs)}\n{'='*96}")
        if len(sigs) < 20:
            print("  too few signals to evaluate"); continue
        for rm in (1.0, 1.5, 2.0):
            df = build(sigs, rm)
            if not len(df):
                continue
            print(f"  --- target {rm:g}R ---")
            line(df, "ALL")
            line(df[df.train], "train (to 2026-01-15)")
            line(df[~df.train], "TEST (after)")
            line(df[df.d > 0], "buys only")
            line(df[df.d < 0], "sells only")
            rnd = randomised(sigs, rm)
            line(rnd, "RANDOM-ENTRY NULL")
        dfm = build(sigs, 0, target_mode="mean")
        if len(dfm):
            print("  --- target = mean of range (his 'back to 50%') ---")
            line(dfm, "ALL")
            line(dfm[dfm.train], "train")
            line(dfm[~dfm.train], "TEST")
            line(randomised(sigs, 0, target_mode="mean"), "RANDOM-ENTRY NULL")

    # cost sensitivity on the headline window
    print(f"\n{'='*96}\nCOST SENSITIVITY (asia 2nd hr, 1.5R) — scalping lives or dies here\n{'='*96}")
    sigs = signals({0, 1})
    for st in (0.0, 1.0, 2.0, 4.0):
        globals()["SLIP_TICKS"] = st
        df = build(sigs, 1.5)
        if len(df):
            line(df, f"slip {st:g} ticks RT")
    print("\nDXY inverse-correlation filter is NOT tested — no dollar-index bars in this repo.")
