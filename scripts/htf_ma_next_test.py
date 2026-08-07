#!/usr/bin/env python3
"""The declared NEXT test (VERDICT-htf-ma-census, Census A):

    Proximity placebo on the W-NORMALIZED payoff cell — touch of the line
    before 1.0W of further extension, events at D=0.5W — per era.
    ACCEPTANCE BAR (declared before this run): real >= 95th percentile of 100
    proximity-matched draws in BOTH eras. Pass -> the 15m MA is special and M1
    graduates to entry-timing research. Fail -> 89% enters the base-rate
    library as the null; research pivots to rebalance selection.

Fit days only. Offsets drawn per-day from that day's own |close - ma15|
minute distribution, sign random — the placebo line lives where price
actually was, at matched distances (the §6 fix for unmatched placebos).

    python -m scripts.htf_ma_next_test
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars           # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof              # noqa: E402

N_DRAWS = 100
N_DAYS_PER_ERA = 70
D_FIRE = 0.5
E_CELL = 1.0            # further extension, in TRUE W units at the event


def wcell_machine(seg, line, w_true, records=None, era=None):
    """D=0.5 event machine vs `line`; outcome = line touched before 1.0W of
    further extension (W from the TRUE band width at the event, so the payoff
    yardstick is identical for real and placebo lines).

    When `records` is a list, each event appends the CONVERGENCE DECOMPOSITION:
    at touch minute tau the touch price IS the line value, so
        profit_at_touch = side_toward_MA * (line_tau - px_event)   [W units]
        price_share     = profit_at_touch / gap_at_event
    price_share ~ 1 -> price rebalanced to the line (the trade paid);
    price_share ~ 0 or < 0 -> the line came to price (the touch paid nothing)."""
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    ev = win = 0
    n = len(cl)
    for side in (1, -1):
        armed = True
        for i in range(n):
            m, w = line[i], w_true[i]
            if np.isfinite(m) and lo[i] <= m <= hi[i]:
                armed = True
                continue
            if not (armed and np.isfinite(m) and np.isfinite(w) and w > 0):
                continue
            if side * (cl[i] - m) / w <= D_FIRE:
                continue
            armed = False
            ev += 1
            ref = cl[i]
            gap_w = side * (cl[i] - m) / w          # >0, in W units
            cap_i = E_CELL * w
            run, hit = 0.0, False
            for j in range(i + 1, n):
                adv = (hi[j] - ref) if side > 0 else (ref - lo[j])
                run = max(run, adv)
                if run >= cap_i:
                    break                           # 1.0W further extension first
                if np.isfinite(line[j]) and lo[j] <= line[j] <= hi[j]:
                    win += 1
                    hit = True
                    if records is not None:
                        # trade direction is TOWARD the line = -side
                        prof_w = -side * (line[j] - ref) / w
                        records.append({
                            "era": era, "side": "above" if side > 0 else "below",
                            "gap_w": gap_w, "profit_w": prof_w,
                            "price_share": prof_w / gap_w if gap_w > 0 else np.nan,
                            "t_touch": j - i, "win": True})
                    break
            if records is not None and not hit:
                records.append({"era": era, "side": "above" if side > 0 else "below",
                                "gap_w": gap_w, "profit_w": np.nan,
                                "price_share": np.nan, "t_touch": np.nan,
                                "win": False})
    return ev, win


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusA_fit.parquet")
    rng = np.random.default_rng(23)

    print(f"NEXT TEST — W-cell placebo (touch before {E_CELL}W, D={D_FIRE}) | "
          f"bar: real >= p95 of {N_DRAWS} draws in BOTH eras")
    print("plus CONVERGENCE DECOMPOSITION on ALL fit days (same pass)\n")

    # ---- pass 1: decomposition over every fit day (real line only) -------
    all_days = sorted(F.sess_day.unique())
    prep = {}
    REC: list[dict] = []
    for d in all_days:
        t0 = pd.Timestamp(f"{d} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        ma, w = bb_ma_asof(hist, 15)
        seg = hist[hist.index >= t0]
        prep[d] = (seg, ma.loc[seg.index].to_numpy(), w.loc[seg.index].to_numpy())
        era = "H2-2025" if d < "2026-01-01" else "H1-2026"
        wcell_machine(*prep[d], records=REC, era=era)
    R = pd.DataFrame(REC)
    print(f"== convergence decomposition (all fit days, {len(R):,} events) ==")
    print(f"{'era':<9}{'side':<7}{'n_win':>6}{'price-led':>10}{'mixed':>7}{'ma-led':>8}"
          f"{'med gap':>8}{'med profit':>11}{'profit<=0':>10}")
    for era in ("H2-2025", "H1-2026"):
        for side in ("above", "below"):
            d = R[(R.era == era) & (R.side == side) & R.win]
            if len(d) == 0:
                continue
            pl = (d.price_share >= 0.75).mean()
            ml = (d.price_share <= 0.25).mean()
            print(f"{era:<9}{side:<7}{len(d):>6,}{pl*100:>9.1f}%{(1-pl-ml)*100:>6.1f}%"
                  f"{ml*100:>7.1f}%{d.gap_w.median():>8.2f}{d.profit_w.median():>11.3f}"
                  f"{(d.profit_w <= 0).mean()*100:>9.1f}%")
    w_all = R[R.win]
    print(f"  pooled: median price_share {w_all.price_share.median():.2f} | "
          f"mean profit at touch {w_all.profit_w.mean():+.3f}W vs mean gap "
          f"{w_all.gap_w.mean():.3f}W | true collectable = "
          f"{w_all.profit_w.mean()/w_all.gap_w.mean()*100:.0f}% of the naive gap\n")

    # ---- pass 2: the declared placebo bar, per era -----------------------
    verdicts = []
    for era, lo_d, hi_d in (("H2-2025", "2025-06-01", "2025-12-31"),
                            ("H1-2026", "2026-01-01", "2026-07-31")):
        days = sorted(d for d in F.sess_day.unique() if lo_d <= d <= hi_d)
        samp = list(rng.choice(days, size=min(N_DAYS_PER_ERA, len(days)), replace=False))
        ev = win = 0
        for d in samp:
            seg, ma, w = prep[d]
            e, k = wcell_machine(seg, ma, w)
            ev += e; win += k
        real = win / ev if ev else np.nan
        draws = []
        for _ in range(N_DRAWS):
            ep = kp = 0
            for d in samp:
                seg, ma, w = prep[d]
                dist = np.abs(seg.close.to_numpy() - ma)
                dist = dist[np.isfinite(dist)]
                off = rng.choice(dist) * rng.choice([-1, 1])
                e, k = wcell_machine(seg, ma + off, w)
                ep += e; kp += k
            draws.append(kp / ep if ep else np.nan)
        draws = np.array([x for x in draws if np.isfinite(x)])
        pct = (draws < real).mean() * 100
        p95 = np.percentile(draws, 95)
        ok = real >= p95
        verdicts.append(ok)
        print(f"  {era}: real {real*100:.1f}% (events {ev}) | placebo mean "
              f"{draws.mean()*100:.1f}% p95 {p95*100:.1f}% | real at {pct:.0f}th pct "
              f"-> {'PASS' if ok else 'FAIL'}")
    final = all(verdicts)
    print(f"\nDECLARED BAR: BOTH eras >= p95 -> {'PASS — the 15m MA is special; '
          'M1 graduates to entry-timing research'
          if final else 'FAIL — 89% enters the base-rate library as the null; '
          'research pivots to rebalance SELECTION'}")


if __name__ == "__main__":
    main()
