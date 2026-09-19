#!/usr/bin/env python3
"""E3 — SWEEP-CONDITIONED RE-ENTRY (DECLARATIONS-level-family-census.md §E3).

The first variable in the programme sourced from the trader's GRAMMAR
rather than from the table's columns, and logged as such.

Plain re-entry is dead (A2), so the sweep condition carries all the work.
Sweep definition, DECLARED BEFORE MEASUREMENT and never swept:

  reference extreme  lowest low (long-side reclaim) / highest high (short)
                     of the 8 completed 15m bars preceding the STOPPED attempt
  penetration        a later bar trades >= 4 ticks (1.00pt) beyond it
  reclaim            a completed 15m bar closes back INSIDE the reference
                     extreme within 3 bars of the penetration

All three must hold on bars strictly between the stopped attempt and the
re-entry trigger. Law 7 arithmetic is printed FIRST, before any sweep is
evaluated.

    python -m scripts.htf_ma_sweep_reentry
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_restate import boot_ci                          # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

LOOKBACK, PEN_TICKS, RECLAIM_BARS, TICK = 8, 4, 3, 0.25


def f15_for(bars: pd.DataFrame, day: str) -> pd.DataFrame:
    t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    f = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return f[(f.index > t0) & (f.index <= t1)]


def swept(f15: pd.DataFrame, t_stop: pd.Timestamp, t_re: pd.Timestamp,
          d: int) -> bool:
    """Declared sweep+reclaim between the stopped attempt and the re-entry."""
    idx = list(f15.index)
    try:
        i_s = idx.index(t_stop)
        i_r = idx.index(t_re)
    except ValueError:
        return False
    if i_r <= i_s or i_s < LOOKBACK:
        return False
    win = f15.iloc[i_s - LOOKBACK:i_s]
    if len(win) < LOOKBACK:
        return False
    between = f15.iloc[i_s + 1:i_r + 1]
    if between.empty:
        return False
    pen = PEN_TICKS * TICK
    if d > 0:                                   # long: sweep a LOW, reclaim up
        ref = float(win.low.min())
        for k in range(len(between)):
            if between.low.iloc[k] <= ref - pen:
                nxt = between.iloc[k:k + RECLAIM_BARS + 1]
                if (nxt.close > ref).any():
                    return True
    else:                                       # short: sweep a HIGH
        ref = float(win.high.max())
        for k in range(len(between)):
            if between.high.iloc[k] >= ref + pen:
                nxt = between.iloc[k:k + RECLAIM_BARS + 1]
                if (nxt.close < ref).any():
                    return True
    return False


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    M = pd.read_parquet(ROOT /
                        "output/htf_ma_census/mtable_fit_structclust.parquet")
    F = F.merge(M, on=["sess_day", "t", "arm", "side", "n_attempts"],
                how="left")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    R = F[(F.arm == "reject") & F.out_ship.notna()
          & (F.risk > 0)].sort_values("t")
    R["stopped"] = (R.out_hold <= -1.0) & (R.mfe_r < 3.0)
    bk = R.groupby("structural_cluster_id", as_index=False).first()
    nA, E = len(bk), bk.out_ship.mean()

    print("== E3 LAW 7 ARITHMETIC (published before any sweep evaluated) ==")
    print(f"  book A: n_A={nA} fights, E={E:+.3f}R. Re-entries are ADDED:")
    print("  EV_new = (n_A*E + n_s*mu_s)/(n_A + n_s)")
    for ns in (100, 200, 400, 600):
        mu2 = ((E + 0.02) * (nA + ns) - nA * E) / ns
        mu5 = ((E + 0.05) * (nA + ns) - nA * E) / ns
        print(f"    n_s={ns:4d} -> mu_s >= {mu2:+.3f}R for +0.02R book, "
              f"{mu5:+.3f}R for +0.05R")

    # candidate re-entries: next trigger after a stopped one, same fight
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    cands = []
    for cid, g in R.groupby("structural_cluster_id", sort=False):
        g = g.sort_values("t")
        rows = list(g.itertuples())
        for i in range(len(rows) - 1):
            if rows[i].stopped:
                cands.append((rows[i], rows[i + 1]))
    print(f"\n  CEILING: {len(cands)} stopped-then-retriggered pairs exist. "
          f"The sweep condition can only shrink this.")

    f15cache: dict[str, pd.DataFrame] = {}
    recs = []
    for prev, re_ in cands:
        day = re_.sess_day
        if day not in f15cache:
            f15cache[day] = f15_for(bars, day)
        ok = swept(f15cache[day], pd.Timestamp(prev.t), pd.Timestamp(re_.t),
                   int(re_.direction))
        recs.append({"sess_day": day, "t": re_.t, "era": re_.era,
                     "out_ship": re_.out_ship, "sweep": ok,
                     "scid": re_.structural_cluster_id})
    C = pd.DataFrame(recs)
    S = C[C.sweep]
    print(f"\n== declared sweep (lookback {LOOKBACK} bars, penetration "
          f"{PEN_TICKS} ticks, reclaim within {RECLAIM_BARS} bars) ==")
    print(f"  qualifying re-entries n_s = {len(S)} of {len(C)} candidates "
          f"({len(S)/max(len(C),1)*100:.0f}%)")
    if len(S):
        mu = S.out_ship.mean()
        need = ((E + 0.02) * (nA + len(S)) - nA * E) / len(S)
        print(f"  mu_s = {mu:+.3f}R   (needed for +0.02R book: {need:+.3f}R)")
        lo, hi = boot_ci(S, "out_ship", lambda s: s.out_ship.mean())
        print(f"  day-boot 95% CI: [{lo:+.3f},{hi:+.3f}]  "
              f"{'CLEAR OF ZERO' if lo > 0 else 'includes zero'}")
        nonS = C[~C.sweep]
        print(f"  non-sweep re-entries: n={len(nonS)} mu={nonS.out_ship.mean():+.3f}R")
        new_ev = (nA * E + len(S) * mu) / (nA + len(S))
        print(f"  book with sweep re-entries added: {E:+.3f} -> {new_ev:+.3f}R "
              f"({new_ev - E:+.3f})")
        print("\n  by era:")
        for era, g in S.groupby("era"):
            print(f"    {era}: n={len(g):4d} mu={g.out_ship.mean():+.3f}R")
        sp = pd.read_csv(ROOT / "output/htf_ma_census/cutstudy_split.csv",
                         dtype=str)
        print("\n  frozen split-half (explore H1 / confirm H2):")
        for half in ("1", "2"):
            days = set(sp[sp.half == half].sess_day)
            g = S[S.sess_day.isin(days)]
            if len(g) < 10:
                print(f"    half {half}: n={len(g)} UNDERPOWERED")
                continue
            lo2, hi2 = boot_ci(g, "out_ship", lambda s: s.out_ship.mean())
            print(f"    half {half}: n={len(g):4d} mu={g.out_ship.mean():+.3f}R "
                  f"[{lo2:+.3f},{hi2:+.3f}]")
        print(f"\n  VERDICT vs declared bar (mu_s>0 with CI clear of zero AND "
              f">= +0.02R book improvement):")
        print(f"    mu_s>0 CI-clear: {lo > 0} | book improvement "
              f"{new_ev - E:+.3f}R >= +0.02R: {new_ev - E >= 0.02}")


if __name__ == "__main__":
    main()
