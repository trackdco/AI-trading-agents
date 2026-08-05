#!/usr/bin/env python3
"""SHARED DATA LAYER — roll-clean footprint. Fixes the day-level band defect.

⚠️ THE DEFECT THIS FIXES

`data/reference/cvd/README.md` documents the shipped clean as:

    "removed by keeping only ticks inside each DAY's ground-truth [low, high] band
     from nq_1m_*.parquet (+/-1 tick)"

A DAY-level band cannot separate contracts during a quarterly roll. The continuous 1-minute
master series switches contract *inside* the day, so the day's [low, high] spans BOTH the
front and the back month, and every back-month tick sits comfortably inside it.

Measured across the FULL owned span, before this fix:

    4.14% of footprint ROWS and 2.32% of VOLUME lie outside their own MINUTE's bar range.
    45 of 352 sessions exceed 1% of volume; the worst are quarterly roll dates:
      2025-09-15  62.0% of volume   2025-12-14  61.6%   2025-12-15  56.9%
      2025-06-16  53.2%             2025-06-15  53.2%   2026-03-16  38.6%

⚠️ IT IS NOT MERELY BACK-MONTH CONTAMINATION. On 2025-09-15 the raw price range is
234.40 -> 26,300.00 while the session's own bar range is 24,139.50 -> 24,183.00. The low
cluster is CALENDAR-SPREAD ticks, which print at a few hundred points rather than at index
level. The raw 08:00-09:29 VPOC for that session is **239.90** — not a wrong price, not a
price at all. Cleaned, it is 24,172.75, inside the session's bar range.

THE FIX — MINUTE-LEVEL BANDING, not day-level.

A tick is kept only if its price lies inside the [low, high] of the SAME MINUTE's bar, with a
one-tick tolerance. This provably zeroes off-band volume BY CONSTRUCTION: after the filter, the
predicate that defines "off-band" is false on every surviving row. That is a stronger guarantee
than "we measured it and it looked small", and it is asserted at runtime.

Why not roll-week masking instead? Masking discards whole sessions — including their front-month
volume — and requires knowing the roll dates, which this repo cannot derive: `nq_1m_master.parquet`
carries NO contract identifier. Minute banding needs no roll calendar and keeps the good ticks.

WHAT THIS DOES NOT CLAIM. Minute banding removes ticks priced outside the front month's own
traded range that minute. A back-month tick that happens to print inside the front month's
minute range is NOT removable by any price-based method, and no contract id exists to catch it.
That residual is bounded by the overlap of the two contracts' ranges and is not measurable here.
Stated so the clean is not over-trusted.

    python -m scripts.footprint_clean          # runs the validation, prints the before/after
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TICK = 0.25
NY = "America/New_York"
_CACHE: dict = {}


def _bars() -> pd.DataFrame:
    from scripts.nya_sb01_feasibility import load_bars
    b = load_bars()
    return b.set_index("ts")[["low", "high"]]


def load_footprint_raw(include_holdout: bool = False) -> pd.DataFrame:
    """Every non-sealed footprint file, concatenated. NY-local ts. No cleaning."""
    parts = []
    for p in sorted(glob.glob(str(ROOT / "data/reference/cvd/footprint_*.parquet"))):
        if "holdout" in p and not include_holdout:
            continue                                  # sealed 2023/24 — never opened
        d = pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume", "trades"])
        d["ts"] = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
        parts.append(d[["ts", "price", "side", "volume", "trades"]])
    out = pd.concat(parts, ignore_index=True)
    return out.astype({"volume": "int64", "trades": "int64"})


def load_footprint_clean(verbose: bool = False) -> pd.DataFrame:
    """Minute-banded footprint. Off-band volume is zero by construction and asserted.

    Rows whose minute has no master bar (the 3 tail days after 2026-07-15) are DROPPED, not
    kept on a looser band — a row we cannot band is a row we cannot vouch for.
    """
    if "clean" in _CACHE:
        return _CACHE["clean"]
    fp = load_footprint_raw()
    bars = _bars()
    n0, v0 = len(fp), int(fp.volume.sum())
    fp = fp.join(bars, on="ts", how="inner")           # inner: unbandable minutes are dropped
    keep = (fp.price >= fp.low - TICK) & (fp.price <= fp.high + TICK)
    out = fp[keep].drop(columns=["low", "high"]).reset_index(drop=True)

    # PROOF, not a spot-check: re-derive the predicate on the survivors. Must be empty.
    chk = out.join(bars, on="ts", how="inner")
    bad = (chk.price < chk.low - TICK) | (chk.price > chk.high + TICK)
    assert not bad.any(), f"minute-band clean failed: {int(bad.sum())} rows still off-band"

    if verbose:
        print(f"  raw rows {n0:,} vol {v0:,}")
        print(f"  banded   {len(out):,} vol {int(out.volume.sum()):,}"
              f"   dropped {100*(1-len(out)/n0):.2f}% rows / "
              f"{100*(1-out.volume.sum()/v0):.2f}% volume")
    _CACHE["clean"] = out
    return out


def minute_frame(clean: bool = True) -> pd.DataFrame:
    """Per-minute (vol, delta) from the CLEANED footprint. delta = B - A, buy-positive.

    Sign convention verified empirically in this repo: fp.delta correlates +0.645 with the
    minute's (close-open) over 369,045 minutes. scripts/build_cvd_minute.py's docstring says the
    opposite and is wrong.
    """
    key = f"min_{clean}"
    if key in _CACHE:
        return _CACHE[key]
    fp = load_footprint_clean() if clean else load_footprint_raw()
    g = fp.groupby(["ts", "side"]).volume.sum().unstack("side").fillna(0.0)
    for c in ("A", "B"):
        if c not in g:
            g[c] = 0.0
    out = pd.DataFrame({"vol": g.A + g.B, "delta": g.B - g.A}, index=g.index).sort_index()
    _CACHE[key] = out
    return out


def price_frame() -> pd.DataFrame:
    """Cleaned (minute x price x side) — the substrate for any volume-at-price feature."""
    return load_footprint_clean()


# ------------------------------------------------------------------ validation
def validate() -> None:
    bars = _bars()
    raw = load_footprint_raw()
    j = raw.join(bars, on="ts", how="inner")
    off = (j.price < j.low - TICK) | (j.price > j.high + TICK)
    j = j.assign(off=off, day=j.ts.dt.strftime("%Y-%m-%d"))

    print("ROLL CONTAMINATION — BEFORE the minute-level clean (full owned span)\n")
    print(f"  rows {len(j):,}   off-band rows {int(off.sum()):,} ({100*off.mean():.2f}%)")
    print(f"  volume off-band: {100*j.volume[off].sum()/j.volume.sum():.2f}%")
    by = j.groupby("day").apply(
        lambda x: pd.Series({"rows_pct": 100 * x.off.mean(),
                             "vol_pct": 100 * x.volume[x.off].sum() / max(x.volume.sum(), 1)}),
        include_groups=False).sort_values("vol_pct", ascending=False)
    print("\n  worst 10 sessions by off-band VOLUME share:")
    print(by.head(10).round(2).to_string())
    print(f"\n  sessions >1% off-band volume: {int((by.vol_pct > 1).sum())} of {len(by)}")

    print("\n" + "=" * 78)
    print("VALIDATION ON 2025-09-15 — the worst roll session")
    print("=" * 78)
    d = j[j.day == "2025-09-15"]
    print(f"  raw rows {len(d):,}   off-band {int(d.off.sum()):,} ({100*d.off.mean():.1f}%)"
          f"   off-band volume {100*d.volume[d.off].sum()/d.volume.sum():.1f}%")
    band = d[~d.off]
    print(f"  raw price range   {d.price.min():.2f} -> {d.price.max():.2f}"
          f"   (spread {d.price.max()-d.price.min():.0f} pt)")
    print(f"  clean price range {band.price.min():.2f} -> {band.price.max():.2f}"
          f"   (spread {band.price.max()-band.price.min():.0f} pt)")
    w = d[(d.ts.dt.hour * 60 + d.ts.dt.minute >= 480) &
          (d.ts.dt.hour * 60 + d.ts.dt.minute < 570)]
    for lab, x in (("RAW", w), ("CLEAN", w[~w.off])):
        if len(x):
            v = x.groupby("price").volume.sum()
            print(f"  08:00-09:29 VPOC {lab:<6} {v.idxmax():>10.2f}"
                  f"   (session bar range {bars.loc[x.ts].low.min():.2f}"
                  f" -> {bars.loc[x.ts].high.max():.2f})")

    print("\n" + "=" * 78)
    print("AFTER the clean — the guarantee")
    print("=" * 78)
    c = load_footprint_clean(verbose=True)
    chk = c.join(bars, on="ts", how="inner")
    bad = (chk.price < chk.low - TICK) | (chk.price > chk.high + TICK)
    print(f"  off-band rows remaining: {int(bad.sum())}   off-band volume remaining: "
          f"{int(chk.volume[bad].sum())}")
    print("  ^ zero BY CONSTRUCTION, and asserted inside load_footprint_clean().")

    print("\nIMPACT ON THE AGGREGATE PER-MINUTE FRAME (what non-price features read)")
    a, b = minute_frame(clean=False), minute_frame(clean=True)
    both = a.join(b, lsuffix="_raw", rsuffix="_cln", how="inner")
    dv = (both.vol_raw - both.vol_cln) / both.vol_raw.replace(0, np.nan)
    print(f"  minutes compared {len(both):,}")
    print(f"  volume differs on {100*(dv.fillna(0) > 1e-9).mean():.1f}% of minutes; "
          f"median |diff| {100*dv.median():.3f}%, p99 {100*dv.quantile(0.99):.2f}%")
    print(f"  total volume removed: {100*(1 - b.vol.sum()/a.vol.sum()):.2f}%")
    print("\n  -> f2_oos_test.flow_frame() reads the UNCLEANED tape and therefore carries this")
    print("     contamination. It is NOT changed retroactively — that would silently alter")
    print("     already-committed results — but every result computed from it inherits the")
    print("     caveat, and any NEW work must use minute_frame()/price_frame() from here.")


if __name__ == "__main__":
    validate()
