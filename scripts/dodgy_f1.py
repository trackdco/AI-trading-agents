#!/usr/bin/env python3
"""F1 — "big overnight move equals choppy or sideways New York AM session".

Run against DECLARATIONS-dodgy-f1.md, committed before this script was run.

His claim, quantified: "anything above like 300 points is pretty substantial". It needs no
entry model, which is why it outlived the refutation of everything else in the lecture.

THE MEASURE IS THE TEST. Overnight range and NY-AM range are both driven by the day's
volatility, and volatility clusters, so any raw-range measure would find that big overnight
moves precede big NY-AM ranges -- autocorrelation, not chop. The pre-declared primary is the
EFFICIENCY RATIO, |last-first| / sum|dclose|, which is scale-free and is what "choppy"
actually means: distance covered divided by ground travelled. Raw range is reported only to
make the confound visible.

    .venv/bin/python scripts/dodgy_f1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED = 20260819
NBOOT = 4000
THRESH = 300.0          # [A] his number
ON = (0.0, 14.5)        # 18:00 -> 08:30, hours elapsed since the session open
AM = (14.5, 17.0)       # 08:30 -> 11:00


def elapsed_hours(idx: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    sd = (idx - pd.Timedelta(hours=18)).date
    naive = pd.to_datetime(pd.Series(sd, index=idx).astype("string")) + pd.Timedelta(hours=18)
    start = naive.dt.tz_localize(idx.tz, nonexistent="shift_forward", ambiguous=True)
    return sd, (idx - pd.DatetimeIndex(start)).total_seconds().to_numpy() / 3600.0


def per_day(bars: pd.DataFrame) -> pd.DataFrame:
    sd, el = elapsed_hours(bars.index)
    h, l_, c = (bars[x].to_numpy() for x in ("high", "low", "close"))
    on = (el >= ON[0]) & (el < ON[1])
    am = (el >= AM[0]) & (el < AM[1])
    rows = []
    for day, g in pd.DataFrame({"sd": sd, "on": on, "am": am, "h": h, "l": l_,
                                "c": c}).groupby("sd", sort=True):
        o, a = g[g.on], g[g.am]
        if len(o) < 300 or len(a) < 120:          # truncated / holiday sessions
            continue
        ac = a.c.to_numpy()
        travel = np.abs(np.diff(ac)).sum()
        disp = abs(ac[-1] - ac[0])
        amrange = a.h.max() - a.l.min()
        rows.append({"sess_day": day,
                     "on_range": o.h.max() - o.l.min(),
                     "on_pct": 100 * (o.h.max() - o.l.min()) / o.c.iloc[0],
                     "eff": disp / travel if travel > 0 else np.nan,
                     "realise": disp / amrange if amrange > 0 else np.nan,
                     "am_range": amrange,
                     "am_disp": disp,
                     "px": o.c.iloc[0]})
    return pd.DataFrame(rows).dropna().reset_index(drop=True)


def boot_diff(a: np.ndarray, b: np.ndarray, rng) -> tuple[float, float]:
    """Bootstrap CI on mean(a) - mean(b). Each observation is one day, so resampling
    days IS the day-clustered bootstrap BR-42 requires -- no nesting needed."""
    d = np.empty(NBOOT)
    for k in range(NBOOT):
        d[k] = rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean()
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Rank correlation = Pearson on ranks. Implemented rather than pulled in, to avoid
    adding scipy to the venv for one function; average ranks handle ties."""
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def boot_spearman(x: np.ndarray, y: np.ndarray, rng) -> tuple[float, float, float]:
    r = spearman(x, y)
    n = len(x)
    s = np.empty(NBOOT)
    for k in range(NBOOT):
        i = rng.integers(0, n, n)
        s[k] = spearman(x[i], y[i])
    return float(r), float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def split(d: pd.DataFrame, mask: np.ndarray, label: str, rng) -> dict:
    hi, lo = d[mask], d[~mask]
    if min(len(hi), len(lo)) < 30:
        return {"arm": label, "n_hi": len(hi), "n_lo": len(lo)}
    clo, chi = boot_diff(hi.eff.to_numpy(), lo.eff.to_numpy(), rng)
    rlo, rhi = boot_diff(hi.realise.to_numpy(), lo.realise.to_numpy(), rng)
    return {"arm": label, "n_hi": len(hi), "n_lo": len(lo),
            "eff_hi": hi.eff.mean(), "eff_lo": lo.eff.mean(),
            "eff_diff": hi.eff.mean() - lo.eff.mean(), "lo": clo, "hi": chi,
            "real_diff": hi.realise.mean() - lo.realise.mean(), "rlo": rlo, "rhi": rhi,
            "amrange_hi": hi.am_range.mean(), "amrange_lo": lo.am_range.mean()}


def main() -> None:
    rng = np.random.default_rng(SEED)
    bars = pd.read_parquet(ROOT / "output/_nq_bars.parquet")
    d = per_day(bars)
    d["era"] = np.where(d.index < len(d) // 2, "H1", "H2")
    print(f"NQ {len(bars):,} bars -> {len(d):,} usable session days "
          f"({d.sess_day.min()} .. {d.sess_day.max()})", flush=True)

    # --- §4: his fixed threshold on an index that doubled
    print("\n=== his 300pt threshold across the sample (declaration §4) ===")
    print(f"NQ level: H1 median {d[d.era=='H1'].px.median():,.0f} · "
          f"H2 median {d[d.era=='H2'].px.median():,.0f}")
    for e in ("H1", "H2"):
        s = d[d.era == e]
        print(f"  {e}: {100 * (s.on_range >= THRESH).mean():5.1f}% of days clear 300pt · "
              f"median overnight range {s.on_range.median():6.1f}pt "
              f"({s.on_pct.median():.2f}% of price)")

    # --- arm 1: the threshold-free statistic
    print("\n=== ARM 1 · Spearman(overnight range, NY-AM efficiency) ===")
    for name, x in (("overnight range, pts", d.on_range.to_numpy()),
                    ("overnight range, % of price", d.on_pct.to_numpy())):
        r, lo, hi = boot_spearman(x, d.eff.to_numpy(), rng)
        v = "NEGATIVE (his claim)" if hi < 0 else ("POSITIVE (reversed)" if lo > 0 else "spans zero")
        print(f"  {name:28s} rho={r:+.4f} [{lo:+.4f},{hi:+.4f}]  {v}")
    r, lo, hi = boot_spearman(d.on_range.to_numpy(), d.am_range.to_numpy(), rng)
    print(f"  {'DIAGNOSTIC vs raw AM range':28s} rho={r:+.4f} [{lo:+.4f},{hi:+.4f}]"
          "  <- the volatility confound, not evidence")

    # --- arms 2-4: threshold splits
    rows = [split(d, (d.on_range >= THRESH).to_numpy(), "his 300pt [A]", rng),
            split(d, (d.on_range >= d.on_range.quantile(0.75)).to_numpy(),
                  "top quartile, pts", rng),
            split(d, (d.on_pct >= d.on_pct.quantile(0.75)).to_numpy(),
                  "top quartile, % of price", rng)]
    for e in ("H1", "H2"):
        s = d[d.era == e].reset_index(drop=True)
        rows.append(split(s, (s.on_range >= THRESH).to_numpy(), f"his 300pt · {e}", rng))
    t = pd.DataFrame([r for r in rows if "eff_diff" in r])
    t["ci"] = t.apply(lambda r: f"[{r.lo:+.4f},{r.hi:+.4f}]", axis=1)
    t["verdict"] = np.where(t.hi < 0, "CHOPPIER (his claim)",
                            np.where(t.lo > 0, "MORE DIRECTIONAL (reversed)", "spans zero"))
    print("\n=== ARMS 2-4 · efficiency, big-overnight days minus the rest ===")
    print(t[["arm", "n_hi", "n_lo", "eff_hi", "eff_lo", "eff_diff", "ci", "verdict"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n  secondary (range realisation) and the diagnostic raw range:")
    print(t[["arm", "real_diff", "rlo", "rhi", "amrange_hi", "amrange_lo"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # --- decile gradient
    d["dec"] = pd.qcut(d.on_range, 10, labels=False, duplicates="drop")
    g = d.groupby("dec").agg(n=("eff", "size"), on_med=("on_range", "median"),
                             eff=("eff", "mean"), realise=("realise", "mean"),
                             am_range=("am_range", "mean"))
    print("\n=== DECILE GRADIENT of overnight range ===")
    print(g.to_string(float_format=lambda v: f"{v:.4f}"))
    d.to_csv(ROOT / "output/dodgy_f1_days.csv", index=False)
    t.to_csv(ROOT / "output/dodgy_f1.csv", index=False)
    print(f"\nseed={SEED} NBOOT={NBOOT} · wrote output/dodgy_f1*.csv")


if __name__ == "__main__":
    main()
