#!/usr/bin/env python3
"""The iFVG book with a STRUCTURAL target instead of a fixed 2R.

Two questions, one run.

1. BLAST RADIUS of CORRECTION 2. `require_revisit` was inert (the flag was read after
   being set from the breaking bar), so the published book is the require_revisit=False
   population. Running both arms prices what the fix changed.

2. THE EXIT. He does not target a fixed multiple -- "95% of my targets are always highs
   and lows" (r43i9rRIjoQ 08:25:54), and "do you think the market sees your little
   riskreward position tool on the screen? No" (08:27:20). The incumbent test targets a
   flat 2R. That is an exit mismatch, not a filter, so it is run as its own arm.

DRAW SET. Only levels that already exist with no-lookahead semantics in
src/engine/sessions.py, plus completed same-day session extremes:
  prior-day H/L, prior-week H/L, completed Asia H/L, completed London H/L.
L1 equal-highs and L9 intermediate-term are NOT here -- they need swing clustering that
does not exist yet. L2 trend line is dropped as unfalsifiable.

LAW 2. A structural target sets reward from the same geometry as risk, so R is a moving
denominator between arms. Median stop, cost in R, and dollars per trade are reported on
every row; an EV-in-R lift that is not also a dollar lift is cost arithmetic.

    python scripts/dodgy_structural_target.py [--days N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import (
    COST_PTS,
    MAX_HOLD,
    load_nq,
    report,
    signals,
)
from src.research.tomtrades import autopsy as AU

NY = "America/New_York"
PT = 20.0                       # NQ $/point
SESSIONS = {"asia": (20, 0, 24, 0), "london": (2, 0, 5, 0)}


def session_day(ts: pd.DatetimeIndex) -> np.ndarray:
    return (ts - pd.Timedelta(hours=18)).date


def draw_levels(bars: pd.DataFrame) -> pd.DataFrame:
    """As-of draw levels per bar. Every column is NaN until the level is COMPLETE.

    Prior-day and prior-week come from completed prior periods, so they are valid all
    session. Same-day Asia and London become valid only after their window closes --
    that is the whole no-lookahead question here, and it is enforced by construction.
    """
    ts = bars.index
    sd = session_day(ts)
    df = pd.DataFrame(index=ts)
    df["_sd"] = sd

    # prior completed session day / week
    hl = bars.groupby(sd).agg(hi=("high", "max"), lo=("low", "min"))
    prior = hl.shift(1)
    df["pdh"] = pd.Series(sd, index=ts).map(prior["hi"]).to_numpy()
    df["pdl"] = pd.Series(sd, index=ts).map(prior["lo"]).to_numpy()

    wk = pd.DatetimeIndex(pd.to_datetime(hl.index)).isocalendar()
    wkkey = (wk["year"].astype(int) * 100 + wk["week"].astype(int)).to_numpy()
    whl = hl.assign(_wk=wkkey).groupby("_wk").agg(hi=("hi", "max"), lo=("lo", "min"))
    pw = whl.shift(1)
    sd2wk = pd.Series(wkkey, index=hl.index)
    df["pwh"] = pd.Series(sd, index=ts).map(sd2wk).map(pw["hi"]).to_numpy()
    df["pwl"] = pd.Series(sd, index=ts).map(sd2wk).map(pw["lo"]).to_numpy()

    # Same-day completed session boxes, measured in HOURS ELAPSED SINCE THE 18:00 OPEN.
    # Clock hour is wrong here: the session spans midnight, so "hour < 20" also matches
    # 00:00-18:00, which is AFTER Asia rather than before it, and silently voids the level
    # for the whole part of the session where it is actually tradeable.
    start = (pd.to_datetime(pd.Series(sd, index=ts).astype("string"))
             .dt.tz_localize(NY) + pd.Timedelta(hours=18))
    elapsed = (ts - pd.DatetimeIndex(start)).total_seconds() / 3600.0
    elapsed = pd.Series(elapsed, index=ts)
    for name, (h0, m0, h1, m1) in SESSIONS.items():
        a = (h0 + m0 / 60.0 - 18) % 24
        b = (h1 + m1 / 60.0 - 18) % 24
        inwin = (elapsed >= a) & (elapsed < b)
        w = bars[inwin.to_numpy()]
        g = w.groupby(session_day(w.index)).agg(hi=("high", "max"), lo=("low", "min"))
        df[f"{name}_h"] = pd.Series(sd, index=ts).map(g["hi"]).to_numpy()
        df[f"{name}_l"] = pd.Series(sd, index=ts).map(g["lo"]).to_numpy()
        df.loc[(elapsed < b).to_numpy(), [f"{name}_h", f"{name}_l"]] = np.nan  # not closed yet
    return df.drop(columns="_sd")


HI_COLS = ["pdh", "pwh", "asia_h", "london_h"]
LO_COLS = ["pdl", "pwl", "asia_l", "london_l"]


def attach_target(sig: pd.DataFrame, bars: pd.DataFrame, lv: pd.DataFrame) -> pd.DataFrame:
    """Nearest UNSWEPT draw level ahead of entry, in the trade direction."""
    hi = lv[HI_COLS].to_numpy()
    lo = lv[LO_COLS].to_numpy()
    c = bars["close"].to_numpy()
    tgt, name = [], []
    for r in sig.itertuples(index=False):
        i, d = int(r.i), int(r.direction)
        cand = list(hi[i]) if d > 0 else list(lo[i])
        cols = list(HI_COLS if d > 0 else LO_COLS)
        cand.append(float(r.t1)); cols.append("swing")   # nearest confirmed swing pool
        ahead = [(v, cols[k]) for k, v in enumerate(cand)
                 if np.isfinite(v) and (v > c[i] if d > 0 else v < c[i])]
        if ahead:
            v, nm = min(ahead, key=lambda x: abs(x[0] - c[i]))
            tgt.append(v); name.append(nm)
        else:
            tgt.append(np.nan); name.append("")
    out = sig.copy()
    out["struct_t"] = tgt
    out["struct_name"] = name
    return out


def simulate(bars: pd.DataFrame, sig: pd.DataFrame, mode: str,
             min_rr: float = 0.0) -> pd.DataFrame:
    """mode: 'fixed2r' (incumbent) | 'structural' (his stated exit).

    min_rr is his own floor -- "never take a trade below one R" -- and it matters here:
    the nearest unswept pool is frequently closer than 1R, so without the floor the book
    contains trades he would refuse.
    """
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(bars)
    out = []
    for r in sig.itertuples(index=False):
        i0 = int(r.i) + 1
        if i0 >= n:
            continue
        entry, d = o[i0], int(r.direction)
        stop = float(r.stop)
        risk = abs(entry - stop)
        if risk < 2.0:
            continue
        if mode == "fixed2r":
            final = entry + d * 2.0 * risk
        else:
            if not np.isfinite(r.struct_t):
                continue                       # his rule 4: no unswept target -> no trade
            final = float(r.struct_t)
            if (final - entry) * d <= 0:
                continue
        rr = abs(final - entry) / risk
        if rr < min_rr:
            continue
        px, why = np.nan, "timeout"
        for j in range(i0, min(i0 + MAX_HOLD, n)):
            if (h[j] >= stop) if d < 0 else (l_[j] <= stop):
                px, why = stop, "stop"
                break
            if (l_[j] <= final) if d < 0 else (h[j] >= final):
                px, why = final, "target"
                break
        else:
            px = c[min(i0 + MAX_HOLD, n) - 1]
        gross = d * (px - entry)
        out.append({"sid": int(r.sid), "sess_day": r.sess_day, "risk": risk, "rr": rr,
                    "out": gross / risk - COST_PTS / risk,
                    "usd": (gross - COST_PTS) * PT, "reason": why})
    t = pd.DataFrame(out)
    if not t.empty:
        t["win"] = (t["out"] > 0).astype(float)
    return t


def row(t: pd.DataFrame, label: str) -> dict:
    r = report(t, label)
    if "ev" not in r:
        return r
    lo, hi = AU.dboot_mean(t.assign(out=t.usd), "out")
    r |= {"med_stop": t.risk.median(), "cost_r": COST_PTS / t.risk.median(),
          "med_rr": t.rr.median(), "usd": t.usd.mean(), "usd_lo": lo, "usd_hi": hi,
          "usd_day": t.usd.sum() / t.sess_day.nunique()}
    return r


def main() -> None:
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else None
    bars = load_nq()
    if days:
        keep = sorted(set(session_day(bars.index)))[-days:]
        bars = bars[pd.Series(session_day(bars.index), index=bars.index).isin(keep)]
    print(f"NQ {len(bars):,} bars  {bars.index.min()} -> {bars.index.max()}", flush=True)

    lv = draw_levels(bars)
    print("draw levels available (% of bars): " + "  ".join(
        f"{c}={100 * lv[c].notna().mean():.0f}%" for c in HI_COLS + LO_COLS), flush=True)

    res = []
    for rv, lab in ((False, "OLD (revisit inert = published)"), (True, "FIXED (revisit enforced)")):
        s = signals(bars, require_sweep=False, require_revisit=rv)
        s = attach_target(s, bars, lv)
        print(f"\n{lab}: {len(s):,} signals", flush=True)
        arms = (("fixed2r", 0.0, "fixed 2R"),
                ("structural", 0.0, "structural"),
                ("structural", 1.0, "structural rr>=1"))
        for mode, mrr, mlab in arms:
            t = simulate(bars, s, mode, mrr)
            res.append(row(t, f"{lab.split()[0]:5s} · {mlab}"))
            print(f"   {mlab:17s} -> {len(t):,} trades", flush=True)

    d = pd.DataFrame([r for r in res if "ev" in r])
    d["ci"] = d.apply(lambda r: f"[{r.lo:+.3f},{r.hi:+.3f}]", axis=1)
    d["usd_ci"] = d.apply(lambda r: f"[{r.usd_lo:+.0f},{r.usd_hi:+.0f}]", axis=1)
    d["eras"] = np.where(d.both, "BOTH", "-")
    print("\n=== EV in R (Law 3: win% and EV together) ===")
    print(d[["variant", "n", "per_day", "win_pct", "ev", "ci", "h1", "h2", "eras"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n=== Law 2: the denominator moved, so price it in dollars too ===")
    print(d[["variant", "n", "med_stop", "cost_r", "med_rr", "usd", "usd_ci", "usd_day"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    out = ROOT / "output/dodgy_structural_target.csv"
    d.to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
