#!/usr/bin/env python3
"""T6 — the market-context layer, one row per session.

ANGUS 2026-08-05: *"i guess next thing to look at is market context and shit like that too,
if youre shorting a heavy bull market its probably not gonna go best for you. use your quant
brain and all the info available and see what can help you draw strong, accurate market
context theses behind trades."* And: *"start using weekly volume profile as well... u should
be looking at previous day vps and stuff, price likes those."*

WHAT THIS FIXES. Nothing in this repo currently knows what kind of market it is trading.
The only regime read we own is `htf_flag`, which is the **15-minute** trend -- a read of the
last couple of hours. There is no daily trend state, no volatility regime, no balance /
imbalance classification, and no volume-profile level older than the current session.

THE CAUSALITY RULE, AND IT IS ABSOLUTE. Every column is computed from sessions **strictly
before** the row's own date, by building the per-session table first and then shifting it by
one. That is not a stylistic choice: London trades at 03:00-05:00 ET, hours before the RTH
session opens, so any field touching the same day's cash session would be unusable there and
silently poisonous everywhere. Shifting once, at the end, makes the guarantee structural
rather than something to re-audit column by column.

TWO KINDS OF COLUMN:

  CONTEXT   what regime are we in -- daily trend, volatility, balance vs imbalance, value
            migration. Used to CONDITION trades. All relative (trailing percentiles), never
            an absolute threshold, so it cannot be tuned to the sample.
  LEVELS    prior-session / prior-week / rolling-5 / rolling-20 POC, VAH, VAL. Actual
            tradeable prices, for the level builder to consume.

    python -m scripts.build_daily_context
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine.indicators import volume_profile  # noqa: E402

NY = "America/New_York"
BIN_PTS = 5.0
VA_PCT = 70.0
RTH = (9 * 60 + 30, 16 * 60)
PCT_WIN = 252          # trailing window for every percentile -- one year of sessions
OUT = ROOT / "output/daily_context.parquet"

WINDOWS = {"prev": 1, "week": None, "roll5": 5, "roll20": 20}


def load_bars() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in ("data/reference/nq_1m_master.parquet",
                             "data/reference/nq_1m_feb_jul2026.parquet")], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    iso = t.dt.isocalendar()
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    b["wk"] = iso.year.astype(int) * 100 + iso.week.astype(int)
    return b


def trailing_pct(s: pd.Series, win: int = PCT_WIN) -> pd.Series:
    """Percentile of each value within its own trailing window. No full-sample quantile
    anywhere in this file -- a full-sample cut peeks at the future and would let a regime
    label be fitted to the era it is meant to describe."""
    return s.rolling(win, min_periods=60).apply(
        lambda w: float((w[:-1] < w[-1]).mean()), raw=True)


def overlap(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Fraction of the union of two value areas that the two share. 1.0 = identical value
    (balance, the market agreeing with yesterday); 0.0 = disjoint (value migrated)."""
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    u_lo, u_hi = min(a[0], b[0]), max(a[1], b[1])
    if u_hi <= u_lo:
        return np.nan
    return max(0.0, hi - lo) / (u_hi - u_lo)


def main() -> int:
    b = load_bars()
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]
    byday = {d: g for d, g in rth.groupby("day")}
    idx = sorted(byday)
    wk = {d: int(g.wk.iloc[0]) for d, g in byday.items()}

    # ---- per-session facts, each describing ITS OWN session ------------------------
    recs = []
    for d in idx:
        g = byday[d]
        try:
            vp = volume_profile(g, BIN_PTS, VA_PCT)
        except Exception:
            continue
        recs.append({"day": d, "wk": wk[d], "open": float(g.open.iloc[0]),
                     "high": float(g.high.max()), "low": float(g.low.min()),
                     "close": float(g.close.iloc[-1]),
                     "poc": vp.poc, "vah": vp.vah, "val": vp.val,
                     "vol": float(g.volume.sum())})
    S = pd.DataFrame(recs).set_index("day")
    print(f"{len(S)} sessions {S.index[0]} -> {S.index[-1]}", flush=True)

    # ---- multi-session profiles, each describing the window ENDING at that session ---
    for name, n in WINDOWS.items():
        if name == "prev":
            continue                                   # the session's own profile
        poc, vah, val = [], [], []
        for i, d in enumerate(S.index):
            if name == "week":
                hist = [x for x in S.index[:i + 1] if wk[x] == wk[d]]
            else:
                hist = list(S.index[max(0, i + 1 - n): i + 1])
            if len(hist) < (2 if name == "week" else n):
                poc.append(np.nan); vah.append(np.nan); val.append(np.nan)
                continue
            vp = volume_profile(pd.concat([byday[x] for x in hist]), BIN_PTS, VA_PCT)
            poc.append(vp.poc); vah.append(vp.vah); val.append(vp.val)
        S[f"poc_{name}"], S[f"vah_{name}"], S[f"val_{name}"] = poc, vah, val
    S["poc_prev"], S["vah_prev"], S["val_prev"] = S.poc, S.vah, S.val

    # ---- CONTEXT, still stamped on the session that produced it ---------------------
    tr = pd.concat([S.high - S.low,
                    (S.high - S.close.shift()).abs(),
                    (S.low - S.close.shift()).abs()], axis=1).max(axis=1)
    S["atr20"] = tr.rolling(20).mean()
    S["range_atr"] = (S.high - S.low) / S.atr20
    S["atr_pct"] = trailing_pct(S.atr20)

    # daily trend: distance from the 20-session mean, in ATR units (scale-free across eras)
    S["trend_atr"] = (S.close - S.close.rolling(20).mean()) / S.atr20
    S["ret5_atr"] = (S.close - S.close.shift(5)) / S.atr20
    S["trend_pct"] = trailing_pct(S.trend_atr)
    S["close_pos"] = (S.close - S.low) / (S.high - S.low)      # 1 = closed on the high

    # value migration (T6): POC over POC is the market restating fair value
    step = np.sign(S.poc.diff())
    S["poc_dir3"] = np.sign(S.poc - S.poc.shift(3))
    S["poc_dir5"] = np.sign(S.poc - S.poc.shift(5))
    streak, run = [], 0
    prev = 0.0
    for v in step.to_numpy():
        run = (run + 1) if (v == prev and v != 0) else (1 if v != 0 else 0)
        streak.append(run * (v if v != 0 else 0))
        prev = v
    S["poc_streak"] = streak

    # balance vs imbalance: does today's value area still sit on yesterday's?
    S["va_overlap"] = [overlap((lo, hi), (plo, phi)) for lo, hi, plo, phi in
                       zip(S.val, S.vah, S.val.shift(), S.vah.shift())]
    S["va_overlap_3"] = S.va_overlap.rolling(3).mean()

    # ---- VIX, prior close ------------------------------------------------------------
    V = pd.read_csv(ROOT / "data/reference/vix_daily.csv")
    S["vix"] = S.index.map(dict(zip(V.date, V.vix)))
    S["vix"] = S.vix.ffill()
    S["vix_pct"] = trailing_pct(S.vix)

    # ---- THE SHIFT. Everything above describes a completed session; move it forward one
    # so the row for day D carries only what was knowable before D began. -------------
    C = S.shift(1)
    C.insert(0, "day", S.index)
    C = C.drop(columns=["wk", "open", "high", "low", "close", "poc", "vah", "val", "vol"])
    C = C.reset_index(drop=True)

    # ---- readable buckets, from trailing percentiles only ---------------------------
    def bucket(p):
        if not np.isfinite(p):
            return "na"
        return ("strong_bear" if p < 0.15 else "bear" if p < 0.35 else
                "neutral" if p < 0.65 else "bull" if p < 0.85 else "strong_bull")
    C["trend_state"] = [bucket(p) for p in C.trend_pct]
    C["vol_state"] = ["na" if not np.isfinite(p) else
                      "low" if p < 0.33 else "normal" if p < 0.67 else "high"
                      for p in C.vix_pct]
    # balance = value sat still; imbalance = value moved off yesterday's
    C["balance_state"] = ["na" if not np.isfinite(v) else
                          "balance" if v >= 0.60 else "edge" if v >= 0.30 else "imbalance"
                          for v in C.va_overlap]
    # trend direction as a tradeable sign: agree with it or fade it
    C["trend_sign"] = np.where(C.trend_pct > 0.65, 1,
                               np.where(C.trend_pct < 0.35, -1, 0)).astype(int)

    C.to_parquet(OUT, index=False)
    ok = C[C.trend_state != "na"]
    print(f"\nwrote {OUT.relative_to(ROOT)} — {len(C)} sessions, {len(ok)} labelled")
    print("\ntrend_state:", ok.trend_state.value_counts().to_dict())
    print("vol_state:  ", ok.vol_state.value_counts().to_dict())
    print("balance:    ", ok.balance_state.value_counts().to_dict())
    print(f"\nva_overlap  median {C.va_overlap.median():.2f}  "
          f"poc_streak |median| {C.poc_streak.abs().median():.0f}")
    print("\ntail:")
    print(C[["day", "trend_state", "vol_state", "balance_state", "poc_prev",
             "poc_week", "vah_prev", "val_prev"]].tail(5).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
