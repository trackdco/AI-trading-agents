#!/usr/bin/env python3
"""Winner/loser autopsy for ash-unicorn-sb (AM1). DESCRIPTIVE — not a test.

Enriches the Stage-3 trade log with context features and compares winners against losers.

⚠️ THIS IS A SEARCH. 15 winners vs 12 losers across ~9 features. Under the null, the chance
of at least one feature separating at p<0.05 is ~1-(0.95^9) = 37%. Every p below is reported
BOTH raw and Holm-adjusted, and any filter derived here is CIRCULAR on this sample by
construction — it must be validated on data not used to find it.

    python -m scripts.ash_autopsy
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import load_bars  # noqa: E402

PHI = NormalDist()
NY = "America/New_York"


def enrich(tr: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    bars = bars.copy()
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    # daily ATR(14) from 1-min bars, computed on days STRICTLY BEFORE each trade
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1)   # prior 14 days only
    atr_pct = atr.rank(pct=True)                              # keyed by 'YYYY-MM-DD' str

    # news calendar (US red folder), ET
    cal = pd.concat([pd.read_csv(ROOT / f, comment="#")
                     for f in ("config/news_calendar_hist.csv", "config/news_calendar.csv")])
    cal["dt"] = pd.to_datetime(cal.datetime_ET, errors="coerce")
    cal = cal.dropna(subset=["dt"])

    rows = []
    for r in tr.itertuples():
        d = r.date
        g = by_day.get(d)
        if g is None:
            continue
        entry_min = int(r.time.split(":")[0]) * 60 + int(r.time.split(":")[1])
        ts = pd.Timestamp(f"{d} {r.time}", tz=NY)
        key = pd.Timestamp(d)
        # HTF alignment: is the 1H trend (last 4h close vs 4h prior) with the trade?
        pre = g[g.mins < 585]
        h1 = np.nan
        if len(pre) > 120:
            h1 = float(pre.close.iloc[-1] - pre.close.iloc[-120])
        aligned = np.nan
        if h1 == h1:
            aligned = int((h1 > 0) == (r.direction == "long"))
        # distance to nearest pre-window swing extreme, in R units
        prev_hi = float(pre.high.max()) if len(pre) else np.nan
        prev_lo = float(pre.low.min()) if len(pre) else np.nan
        dist = np.nan
        if prev_hi == prev_hi:
            dist = min(abs(r.entry - prev_hi), abs(r.entry - prev_lo)) / r.risk_pts
        # news inside or near the window
        day_news = cal[cal.dt.dt.date == key.date()]
        news_in = int(((day_news.dt.dt.hour * 60 + day_news.dt.dt.minute)
                       .between(585, 615)).any()) if len(day_news) else 0
        news_day = int(len(day_news) > 0)
        rows.append({**r._asdict(),
                     "dow": key.day_name()[:3],
                     "entry_min_into_window": entry_min - 585,
                     "atr_pct": float(atr_pct.get(d, np.nan)),
                     "htf_aligned": aligned,
                     "dist_to_level_R": dist,
                     "news_in_window": news_in,
                     "news_day": news_day,
                     "risk_pts_v": r.risk_pts})
    return pd.DataFrame(rows).drop(columns=["Index"], errors="ignore")


def two_prop(a: int, na: int, b: int, nb: int) -> float:
    if min(na, nb) == 0:
        return float("nan")
    p = (a + b) / (na + nb)
    se = np.sqrt(p * (1 - p) * (1 / na + 1 / nb))
    if se == 0:
        return float("nan")
    return 2 * (1 - PHI.cdf(abs(a / na - b / nb) / se))


def mannwhitney_p(x: np.ndarray, y: np.ndarray) -> float:
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x) < 3 or len(y) < 3:
        return float("nan")
    allv = np.concatenate([x, y])
    r = pd.Series(allv).rank().to_numpy()
    r1 = r[:len(x)].sum()
    u1 = r1 - len(x) * (len(x) + 1) / 2
    mu = len(x) * len(y) / 2
    sd = np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
    return float(2 * (1 - PHI.cdf(abs(u1 - mu) / sd))) if sd > 0 else float("nan")


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x) < 2 or len(y) < 2:
        return float("nan")
    gt = sum(int((xi > y).sum()) for xi in x)
    lt = sum(int((xi < y).sum()) for xi in x)
    return (gt - lt) / (len(x) * len(y))


def null_best_of(m: int, nw: int, nl: int, reps: int = 20000, seed: int = 7) -> tuple:
    """What does the BEST of m tests look like when there is nothing there?

    Answers the only question that matters for a search: is our smallest p-value
    smaller than what pure noise hands back at this sample size?
    """
    rng = np.random.default_rng(seed)
    mu, sd = nw * nl / 2, np.sqrt(nw * nl * (nw + nl + 1) / 12)
    best = np.empty(reps)
    for i in range(reps):
        ps = []
        for _ in range(m):
            a, b = rng.normal(size=nw), rng.normal(size=nl)
            r = pd.Series(np.concatenate([a, b])).rank().to_numpy()
            u1 = r[:nw].sum() - nw * (nw + 1) / 2
            ps.append(2 * (1 - PHI.cdf(abs(u1 - mu) / sd)))
        best[i] = min(ps)
    return best, float(np.median(best))


def power_floor(nw: int, nl: int, base: float = 0.33) -> tuple:
    """Smallest effect this sample could have detected at 80% power, alpha .05."""
    za, zb = PHI.inv_cdf(0.975), PHI.inv_cdf(0.80)
    d_min = (za + zb) * np.sqrt(1 / nw + 1 / nl)
    p2_min = float("nan")
    for p2 in np.arange(base + 0.01, 1.0, 0.01):
        p = (base * nw + p2 * nl) / (nw + nl)
        se = np.sqrt(p * (1 - p) * (1 / nw + 1 / nl))
        if 1 - PHI.cdf(za - abs(p2 - base) / se) >= 0.80:
            p2_min = p2
            break
    return d_min, p2_min


def main() -> None:
    tr = pd.read_csv(ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-raw-trades.csv")
    fl = pd.read_csv(ROOT / "research/ash10hazard/strategies/"
                     "ash-unicorn-sb-orderflow-trades.csv")
    tr = tr.merge(fl[["date", "F1_disp_delta", "F2_retrace_ratio"]], on="date", how="left")
    d = enrich(tr, load_bars())
    W = d[d.R >= 2]; L = d[d.R <= -1]; BE = d[d.R == 0]
    print("AUTOPSY — ash-unicorn-sb (AM1 09:45-10:15 ET)")
    print(f"n={len(d)}   winners={len(W)}  losers={len(L)}  break-even={len(BE)}")
    print("⚠️ SEARCH over ~9 features on 15v12. P(>=1 false positive at .05) = 37%.\n")

    tests = []
    # categorical / binary
    for f in ("htf_aligned", "news_in_window", "news_day"):
        a, b = W[f].dropna(), L[f].dropna()
        if len(a) and len(b):
            tests.append((f, f"{100*a.mean():.0f}% vs {100*b.mean():.0f}%",
                          two_prop(int(a.sum()), len(a), int(b.sum()), len(b)), len(a), len(b)))
    # continuous
    for f in ("atr_pct", "dist_to_level_R", "entry_min_into_window", "risk_pts_v",
              "F1_disp_delta", "F2_retrace_ratio"):
        a, b = W[f].to_numpy(float), L[f].to_numpy(float)
        av, bv = np.nanmedian(a), np.nanmedian(b)
        tests.append((f, f"med {av:.2f} vs {bv:.2f}", mannwhitney_p(a, b),
                      int((~np.isnan(a)).sum()), int((~np.isnan(b)).sum())))
    # direction
    tests.append(("direction_long", f"{100*(W.direction=='long').mean():.0f}% vs "
                  f"{100*(L.direction=='long').mean():.0f}%",
                  two_prop(int((W.direction=='long').sum()), len(W),
                           int((L.direction=='long').sum()), len(L)), len(W), len(L)))

    t = pd.DataFrame(tests, columns=["feature", "winners vs losers", "p_raw", "nW", "nL"])
    t = t.sort_values("p_raw")
    m = len(t)
    t["p_holm"] = [min(1.0, p * (m - i)) if p == p else np.nan
                   for i, p in enumerate(t.p_raw)]
    delt = {f: cliffs_delta(W[f].to_numpy(float), L[f].to_numpy(float))
            for f in ("atr_pct", "dist_to_level_R", "entry_min_into_window", "risk_pts_v",
                      "F1_disp_delta", "F2_retrace_ratio")}
    t["cliff_d"] = t.feature.map(delt)
    t["survives"] = np.where(t.p_holm <= 0.05, "YES", "no")
    t["thin"] = np.where(t[["nW", "nL"]].min(axis=1) < 15, "<15 FLAG", "")
    print(t.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    # --- is the best p smaller than what noise gives us at this size? ---
    best_p = float(t.p_raw.min())
    best, med = null_best_of(m, len(W), len(L))
    print(f"\nNULL CHECK — best-of-{m} tests on {len(W)}v{len(L)} random data (20k reps):")
    print(f"  P(min p <= our {best_p:.3f}) = {(best <= best_p).mean():.3f}   "
          f"median min-p under the null = {med:.3f}")
    d_min, p2_min = power_floor(len(W), len(L))
    print(f"POWER FLOOR at 80%/alpha.05 — smallest detectable Cohen's d = {d_min:.2f} "
          f"(Cohen 'large' = 0.80);")
    print(f"  a binary feature at a 33% base would need to reach {100*p2_min:.0f}% to be seen.")
    print("  => 'nothing separated' means NO HUGE EFFECT, not 'no useful effect'.")

    print("\nDAY OF WEEK (descriptive only):")
    print(d.groupby("dow").R.agg(n="size", mean="mean").to_string())
    print("\nBE trades — where do they sit?")
    for f in ("atr_pct", "F2_retrace_ratio"):
        print(f"  {f}: W {np.nanmedian(W[f]):.2f} | BE {np.nanmedian(BE[f]):.2f} "
              f"| L {np.nanmedian(L[f]):.2f}")
    d.to_csv(ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-autopsy-features.csv",
             index=False)


if __name__ == "__main__":
    main()
