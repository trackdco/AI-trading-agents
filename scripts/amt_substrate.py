#!/usr/bin/env python3
"""AMT / PROFILE SUBSTRATE — session structures for the auction-market toolkit.

Infrastructure, not a strategy: one row per RTH session with the objects every
auction-market-theory / TPO / volume-profile / VWAP candidate reads. Built once
from data/reference/nq_1m_master.parquet (full 2023-2026 span); candidates then
census against this table under their own preregs. No trading claims are tested
here — building features is not a trial and appears in no ledger.

Definitions (mechanical, so every later prereg can cite them):
  TPO           30-minute brackets (A=09:30-10:00 ... M=15:30-16:00), price bins
                of BIN pts; a bin's TPO count = # brackets whose bracket range
                covers the bin.
  POC           bin with the max TPO count (tie -> closest to session midpoint).
  Value area    70% of total TPOs, grown outward from the POC (classic method).
  Poor high/low session extreme whose extreme bin holds >= 2 TPOs (no
                single-print taper at the end of the auction).
  Single prints interior bins with TPO count == 1 (excluding the extremes'
                natural taper) — unfinished business inside the profile.
  Naked POC     a prior session's POC never TOUCHED (session low <= poc <=
                session high) by any later session, as of each day. This table
                stores each day's own POC + the nearest naked POC above/below
                at that day's open, with its age in sessions.
  Open type     first-30-min classification vs the open price:
                  drive     price never re-crosses the open after the first
                            5 minutes (one-sided conviction)
                  test_drive  crosses once within the first 15 min, then
                            one-sided (test, reject, go)
                  rejection_reverse  travels >= 0.5 x prior session range one
                            way then closes the bracket beyond the open on the
                            other side
                  auction   everything else (two-sided, no conviction)
  Day type      by range-extension vs the initial balance (IB = first hour):
                  trend     close in the extreme 20% of range AND range >= 2xIB
                  normal_var  range extension one side >= 1xIB beyond IB
                  normal    range extension < 0.5xIB beyond IB either side
                  neutral   extension BOTH sides of the IB
  VWAP          RTH session vwap from 1-min (close x volume), sigma = vwap-
                weighted stdev; bands at +/-1 and +/-2 sigma.
  Value relation  today's open vs PRIOR session's value area:
                  above / inside / below  (the 80%-rule precondition).

    python -m scripts.amt_substrate            # writes output/amt_days.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BIN = 5.0          # TPO price bin, points
VA_FRAC = 0.70     # value-area fraction
BRACKETS = [(f"{h:02d}:{m:02d}", f"{h + (m + 30) // 60:02d}:{(m + 30) % 60:02d}")
            for h, m in [(9, 30), (10, 0), (10, 30), (11, 0), (11, 30), (12, 0),
                         (12, 30), (13, 0), (13, 30), (14, 0), (14, 30), (15, 0),
                         (15, 30)]]


def tpo_profile(r: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(bin_prices, tpo_counts) for one session's RTH 1-min rows."""
    lo = np.floor(r.low.min() / BIN) * BIN
    hi = np.ceil(r.high.max() / BIN) * BIN
    bins = np.arange(lo, hi + BIN, BIN)
    counts = np.zeros(len(bins), dtype=int)
    for b0, b1 in BRACKETS:
        w = r[(r.clock >= b0) & (r.clock < b1)]
        if not len(w):
            continue
        blo, bhi = w.low.min(), w.high.max()
        counts += ((bins >= blo - BIN / 2) & (bins <= bhi + BIN / 2)).astype(int)
    return bins, counts


def value_area(bins: np.ndarray, counts: np.ndarray, mid: float) -> tuple[float, float, float]:
    """POC, VAL, VAH by the classic grow-outward-from-POC method."""
    top = counts.max()
    cands = bins[counts == top]
    poc = float(cands[np.abs(cands - mid).argmin()])
    i = int(np.where(bins == poc)[0][0])
    need = VA_FRAC * counts.sum()
    got, lo_i, hi_i = counts[i], i, i
    while got < need and (lo_i > 0 or hi_i < len(bins) - 1):
        up = counts[hi_i + 1] if hi_i < len(bins) - 1 else -1
        dn = counts[lo_i - 1] if lo_i > 0 else -1
        if up >= dn:
            hi_i += 1; got += max(up, 0)
        else:
            lo_i -= 1; got += max(dn, 0)
    return poc, float(bins[lo_i]), float(bins[hi_i])


def open_type(r: pd.DataFrame, prior_range: float) -> str:
    op = r.open.iloc[0]
    w30 = r[r.clock < "10:00"]
    after5 = w30.iloc[5:] if len(w30) > 5 else w30
    crosses = int(((after5.low <= op) & (after5.high >= op)).sum())
    if crosses == 0:
        return "drive"
    w15 = w30[w30.clock < "09:45"]
    c15 = int(((w15.iloc[5:].low <= op) & (w15.iloc[5:].high >= op)).sum()) if len(w15) > 5 else 0
    if 1 <= c15 <= 3 and crosses == c15:
        return "test_drive"
    if prior_range > 0:
        far_up = w30.high.max() - op
        far_dn = op - w30.low.min()
        cl = w30.close.iloc[-1]
        if far_up >= 0.5 * prior_range and cl < op:
            return "rejection_reverse"
        if far_dn >= 0.5 * prior_range and cl > op:
            return "rejection_reverse"
    return "auction"


def day_type(r: pd.DataFrame) -> str:
    ib = r[r.clock < "10:30"]
    ib_hi, ib_lo = ib.high.max(), ib.low.min()
    ib_rng = ib_hi - ib_lo
    hi, lo, cl = r.high.max(), r.low.min(), r.close.iloc[-1]
    rng = hi - lo
    ext_up, ext_dn = hi - ib_hi, ib_lo - lo
    if ib_rng <= 0 or rng <= 0:
        return "normal"
    if ext_up > 0.1 * ib_rng and ext_dn > 0.1 * ib_rng:
        return "neutral"
    pos = (cl - lo) / rng
    if rng >= 2 * ib_rng and (pos >= 0.8 or pos <= 0.2):
        return "trend"
    if max(ext_up, ext_dn) >= 1.0 * ib_rng:
        return "normal_var"
    return "normal"


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    rows = []
    naked: list[dict] = []   # {"poc": price, "day": born} — dies when touched
    prior = None
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts")
        if len(r) < 200:
            continue
        op, hi, lo, cl = r.open.iloc[0], r.high.max(), r.low.min(), r.close.iloc[-1]
        bins, counts = tpo_profile(r)
        poc, val, vah = value_area(bins, counts, (hi + lo) / 2)
        # poor extremes + interior single prints
        poor_hi = counts[-1] >= 2 if len(counts) else False
        poor_lo = counts[0] >= 2 if len(counts) else False
        interior = counts[2:-2]
        singles = int((interior == 1).sum()) if len(interior) else 0
        # naked POCs as of today's open (strictly prior sessions)
        above = [n for n in naked if n["poc"] > op]
        below = [n for n in naked if n["poc"] < op]
        na = min(above, key=lambda n: n["poc"] - op) if above else None
        nb = min(below, key=lambda n: op - n["poc"]) if below else None
        v = None
        w = r[(r.clock >= "09:30") & (r.clock < "16:00")]
        vwap = float((w.close * w.volume).sum() / max(w.volume.sum(), 1))
        sig = float(np.sqrt((w.volume * (w.close - vwap) ** 2).sum() / max(w.volume.sum(), 1)))
        if prior is not None:
            v = ("above" if op > prior["vah"] else "below" if op < prior["val"] else "inside")
        rows.append(dict(
            day=d, open=op, high=hi, low=lo, close=cl,
            poc=poc, val=val, vah=vah,
            poor_high=bool(poor_hi), poor_low=bool(poor_lo), single_prints=singles,
            open_type=open_type(r, (prior["high"] - prior["low"]) if prior else 0.0),
            day_type=day_type(r),
            vwap=vwap, vwap_sigma=sig,
            open_vs_prior_value=v,
            prior_poc=prior["poc"] if prior else np.nan,
            prior_vah=prior["vah"] if prior else np.nan,
            prior_val=prior["val"] if prior else np.nan,
            naked_poc_above=na["poc"] if na else np.nan,
            naked_poc_above_age=(pd.Timestamp(d) - pd.Timestamp(na["day"])).days if na else np.nan,
            naked_poc_below=nb["poc"] if nb else np.nan,
            naked_poc_below_age=(pd.Timestamp(d) - pd.Timestamp(nb["day"])).days if nb else np.nan,
        ))
        naked = [n for n in naked if not (lo <= n["poc"] <= hi)]
        naked.append({"poc": poc, "day": d})
        prior = dict(poc=poc, vah=vah, val=val, high=hi, low=lo)

    out = pd.DataFrame(rows)
    out.to_parquet(ROOT / "output/amt_days.parquet", index=False)
    print(f"{len(out)} sessions {out.day.min()} .. {out.day.max()}")
    print(out.open_type.value_counts().to_string())
    print(out.day_type.value_counts().to_string())
    print(f"poor highs {out.poor_high.mean():.0%} | poor lows {out.poor_low.mean():.0%} | "
          f"open vs prior value: {out.open_vs_prior_value.value_counts(dropna=True).to_dict()}")


if __name__ == "__main__":
    main()
