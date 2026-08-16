#!/usr/bin/env python3
"""THE SELECTION EFFECT — his real fills vs the same-day trigger baseline.

This is the one result the whole agent programme rests on, and until now it
lived only in prose in ARCHITECTURE-trading-agent.md with no committed data
and no committed script. Both are fixed here:

  data/trader_fills/fxreplay_2026-01_full.csv   his FX Replay export
  this script                                   the measurement

QUESTION: of the raw triggers available on the days he traded, do the ones
he actually TOOK run further than the ones he passed?

Baseline pool = every in-window 2m/3m raw trigger on a day he traded. His
picks are a subset of that pool by construction (a fill only counts if it
matches a trigger), so the comparison is selection and nothing else — same
days, same mechanism, same market.

TWO CONSTRUCTION CHOICES THAT DECIDE THE ANSWER, both got wrong on the first
pass (see FINDINGS-selection-effect.md):

1. MATCHING IS CAUSAL. A trigger only counts as "the one he took" if it
   CLOSED at or before his fill minute. The original ±5min two-sided window
   let a candle that printed AFTER his entry be credited as his selection —
   lookahead in the matcher itself.
2. THE BASELINE MUST BE IN-WINDOW. His session windows are already a hard
   mechanical constraint, so an all-hours baseline credits judgment for a
   rule the machine enforces for free. Both are reported; in-window is the
   one that speaks to judgment.

Break-even rows (rPnL == 0) are EXCLUDED: "All the trades that get marked as
break-even, I didn't actually take those." Exact duplicate rows are misclicks
and are collapsed.

Triggers are rebuilt here on the CORRECTED VWAP (source=open, BR-106), not
read from the pre-2026-08-10 parquet.

    python -m scripts.trader_selection_effect
    python -m scripts.trader_selection_effect --tol=5 --tf=3 --vwap=hlc3
    python -m scripts.trader_selection_effect --tol=5 --tf=3 --twosided
        ^ the last one reproduces the withdrawn 5.48R reading
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                  # noqa: E402
from scripts.raw_trigger_census import day_rows                  # noqa: E402
from src.htf_ma.levels import NY                                 # noqa: E402

FILLS = ROOT / "data/trader_fills/fxreplay_2026-01_full.csv"
SEED = 20260810
NDRAW = 20_000
TOL_MIN = 3          # trigger closed within TOL_MIN before the fill
WINDOWS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}


def load_fills() -> pd.DataFrame:
    F = pd.read_csv(FILLS)
    n0 = len(F)
    F = F[F.rPnL != 0].copy()
    n_be = n0 - len(F)
    F = F.drop_duplicates(subset=["dateStart", "side", "entryPrice"])
    n_dup = n0 - n_be - len(F)
    # dateStart is UTC and stamped at :59 of the minute BEFORE the entry bar
    t = pd.to_datetime(F.dateStart, format="%Y/%m/%d %H:%M:%S", utc=True)
    F["t_ny"] = (t + pd.Timedelta(seconds=1)).dt.tz_convert(NY)
    F["direction"] = np.where(F.side == "buy", 1, -1)
    F["sess_day"] = [str((x.normalize() if x.hour >= 18
                          else x.normalize() - pd.Timedelta(days=1)).date())
                     for x in F.t_ny]
    F["hm"] = F.t_ny.dt.hour * 60 + F.t_ny.dt.minute
    F["win"] = [next((k for k, (a, b) in WINDOWS.items() if a <= h <= b), None)
                for h in F.hm]
    print(f"fills: {n0} rows -> {n_be} break-even dropped, {n_dup} duplicate "
          f"misclicks collapsed -> {len(F)} real decisions "
          f"over {F.sess_day.nunique()} days ({len(F)/F.sess_day.nunique():.2f}/day)")
    print(f"   net {F.rPnL.sum():+,.0f} USD   win rate "
          f"{(F.rPnL > 0).mean()*100:.0f}%   "
          f"avg win {F.rPnL[F.rPnL>0].mean():+,.0f} / "
          f"avg loss {F.rPnL[F.rPnL<0].mean():+,.0f}")
    print(f"   by window: " + "  ".join(
        f"{k}:{int(v)}" for k, v in F.win.value_counts(dropna=False).items()))
    return F


def build_triggers(bars: pd.DataFrame, days: list[str],
                   tfs=(2, 3)) -> pd.DataFrame:
    """2m+3m by default — his declared grammar is a race across timeframes,
    so scoring 3m alone throws away the entries he took on the 2m closure.
    The two are de-duplicated to one row per (day, direction, 3-min bucket)
    so a single move is not counted twice."""
    rows = []
    for d in days:
        rows.extend(day_rows(bars, d))
    T = pd.DataFrame(rows)
    T["t"] = pd.to_datetime(T.t)
    T = T[T.tf.isin(tfs)].copy()
    T["bucket"] = T.hm // 3
    T = (T.sort_values(["sess_day", "direction", "hm"])
          .drop_duplicates(["sess_day", "direction", "bucket"]))
    T["win"] = [next((k for k, (a, b) in WINDOWS.items() if a <= h <= b), None)
                for h in T.hm]
    return T


def match(F: pd.DataFrame, T: pd.DataFrame, causal: bool = True) -> pd.DataFrame:
    """Nearest same-day same-direction trigger within TOL_MIN of the fill.

    causal=True requires the trigger to have CLOSED at or before the fill
    minute — he cannot have entered on a candle that had not printed yet.
    The two-sided variant exists only to reproduce the earlier reading."""
    out = []
    for _, f in F.iterrows():
        c = T[(T.sess_day == f.sess_day) & (T.direction == f.direction)]
        if causal:
            c = c[(c.hm <= f.hm) & (c.hm >= f.hm - TOL_MIN)]
        else:
            c = c[(c.hm - f.hm).abs() <= TOL_MIN]
        if c.empty:
            out.append(None)
            continue
        gap = (c.hm - f.hm).abs()
        out.append(c.index[int(gap.to_numpy().argmin())])
    F = F.copy()
    F["trig_ix"] = out
    return F


def _perm(sel, pool, rng, day_matched):
    """day_matched=True holds his per-day trade COUNT fixed and randomises
    only the within-day choice. False pools the days — the looser control,
    which also credits him for trading more on the better days."""
    cnt = sel.groupby("sess_day").size()
    by_day = {d: g.run_mfe_r.to_numpy() for d, g in pool.groupby("sess_day")}
    flat = pool.run_mfe_r.to_numpy()
    med = np.empty(NDRAW)
    p2 = np.empty(NDRAW)
    for i in range(NDRAW):
        if day_matched:
            pick = np.concatenate([
                rng.choice(by_day[d], size=min(k, len(by_day[d])),
                           replace=False)
                for d, k in cnt.items() if d in by_day])
        else:
            pick = rng.choice(flat, size=len(sel), replace=False)
        med[i] = np.median(pick)
        p2[i] = (pick >= 2.0).mean()
    return med, p2


def effect(sel: pd.DataFrame, pool: pd.DataFrame, label: str) -> None:
    n = len(sel)
    obs_med = sel.run_mfe_r.median()
    obs_p2 = (sel.run_mfe_r >= 2.0).mean()
    base_med = pool.run_mfe_r.median()
    base_p2 = (pool.run_mfe_r >= 2.0).mean()

    print(f"\n   {label}: his {n} picks from a pool of {len(pool)} "
          f"({len(pool)/pool.sess_day.nunique():.1f}/day over "
          f"{pool.sess_day.nunique()} days)")
    print(f"      median run   HIS {obs_med:5.2f}R   baseline {base_med:5.2f}R")
    print(f"      P(2R)        HIS {obs_p2*100:5.1f}%   baseline "
          f"{base_p2*100:5.1f}%")
    for dm, nm in ((True, "day-matched (strict)"), (False, "pooled (loose)")):
        rng = np.random.default_rng(SEED)
        med, p2 = _perm(sel, pool, rng, dm)
        pm, pp = (med >= obs_med).mean(), (p2 >= obs_p2).mean()
        print(f"      perm {nm:22s} p(median) {pm:.4f}   p(P2R) {pp:.4f}   "
              f"null median-run {med.mean():.2f} [p95 {np.percentile(med,95):.2f}]")


def main() -> None:
    global TOL_MIN
    src = "open"
    tfs = (2, 3)
    for a in sys.argv[1:]:
        if a.startswith("--vwap="):
            src = a.split("=", 1)[1]
        if a.startswith("--tol="):
            TOL_MIN = int(a.split("=", 1)[1])
        if a.startswith("--tf="):
            tfs = tuple(int(x) for x in a.split("=", 1)[1].split(","))
    if src != "open":
        # decomposition only: reproduce what a different band source does to
        # the trigger population, so the effect can be attributed
        import functools

        import scripts.raw_trigger_census as rtc
        from src.htf_ma.levels import vwap_bands as _vb
        rtc.vwap_bands = functools.partial(_vb, source=src)
    print(f"[vwap source = {src}   match tolerance = ±{TOL_MIN} min]")
    F = load_fills()
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    days = sorted(F.sess_day.unique())
    print(f"\nrebuilding {'+'.join(f'{x}m' for x in tfs)} triggers on "
          f"{len(days)} traded days (VWAP source={src}, BR-106)...")
    T = build_triggers(bars, days, tfs)
    print(f"   {len(T)} triggers; in-window "
          f"{T.win.notna().sum()} ({T.win.notna().sum()/len(days):.1f}/day)")

    F = match(F, T, causal=("--twosided" not in sys.argv))
    hit = F.trig_ix.notna()
    print(f"\nMATCHING (same day, same direction, trigger closed within {TOL_MIN} min "
          f"{'BEFORE' if '--twosided' not in sys.argv else 'EITHER SIDE OF'} the fill):")
    print(f"   {hit.sum()} of {len(F)} fills matched a trigger "
          f"({hit.mean()*100:.0f}%) — the {(~hit).sum()} unmatched are the "
          f"known gap in the trigger definition, NOT evidence about them")
    for w in ["LONDON", "NY_PRE", "NY_AM", None]:
        g = F[F.win.isna()] if w is None else F[F.win == w]
        if len(g):
            print(f"      {str(w):8s} {g.trig_ix.notna().sum():2d}/{len(g):2d}")

    print("\n" + "=" * 92)
    print("SELECTION EFFECT — do the triggers he took run further than the "
          "ones he passed, same days?")
    print("=" * 92)

    Tw = T[T.win.notna()]
    sel_ix = F.loc[hit & F.win.notna(), "trig_ix"].astype(int)
    sel = Tw.loc[Tw.index.intersection(sel_ix)]
    pool = Tw[Tw.sess_day.isin(sel.sess_day.unique())]
    if len(sel) >= 5:
        effect(sel, pool, "IN-WINDOW")

    sel_all = T.loc[T.index.intersection(F.loc[hit, "trig_ix"].astype(int))]
    pool_all = T[T.sess_day.isin(sel_all.sess_day.unique())]
    if len(sel_all) >= 5:
        effect(sel_all, pool_all, "ALL HOURS")


if __name__ == "__main__":
    main()
