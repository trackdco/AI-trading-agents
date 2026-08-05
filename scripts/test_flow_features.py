#!/usr/bin/env python3
"""UNIT TESTS + LOOK-AHEAD PROOFS for the at-entry flow feature library.

Two independent things are checked, and both must pass before any feature is used:

  A. UNIT TESTS on SYNTHETIC sequences with hand-computable answers. These catch a feature that
     is internally wrong — a real-data proof cannot, because a wrong feature computed from
     pre-entry data still passes a look-ahead test.

  B. LOOK-AHEAD PROOFS on EVERY REAL HISTORICAL EVENT in the repo. Each feature is recomputed
     with every row from the entry minute onward physically deleted; the value must be identical.

  A ⟂ B. A feature can pass one and fail the other. Both are required.

    python -m scripts.test_flow_features
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.flow_features import REGISTRY, FeatureInput, compute, prove_no_lookahead  # noqa

NY = "America/New_York"
FAILS: list[str] = []


def _synth(n=60, start="2026-01-05 09:00", vol=100.0, delta=0.0, px=20000.0, step=0.0):
    idx = pd.date_range(start, periods=n, freq="1min", tz=NY)
    close = px + step * np.arange(n)
    bars = pd.DataFrame({"open": close, "high": close + 2, "low": close - 2, "close": close},
                        index=idx)
    fpm = pd.DataFrame({"vol": np.full(n, vol), "delta": np.full(n, delta)}, index=idx)
    fpp = pd.DataFrame({"price": np.round(close * 4) / 4, "volume": np.full(n, vol),
                        "side": "B"}, index=idx)
    return idx, bars, fpm, fpp


def _mk(idx, bars, fpm, fpp, entry_i, side=1, disp=(None, None), sess_i=0):
    entry = idx[entry_i]
    return FeatureInput(day=str(idx[0].date()), entry_ts=entry,
                        cut=entry - pd.Timedelta(minutes=1), side=side,
                        sess_start=idx[sess_i],
                        disp_start=disp[0], disp_end=disp[1],
                        bars=bars, fpm=fpm, fpp=fpp)


def check(label, got, want, tol=1e-6):
    ok = (got != got and want != want) or abs(got - want) < tol
    print(f"    {'PASS' if ok else 'FAIL'}  {label:<58} got {got!r:>12}  want {want!r}")
    if not ok:
        FAILS.append(label)


# ------------------------------------------------------------------ A. unit tests
def unit_tests():
    print("A. UNIT TESTS ON SYNTHETIC SEQUENCES (hand-computable)\n")
    idx, bars, fpm, fpp = _synth(n=60, vol=100.0, delta=10.0)

    print("  participation_to_touch")
    # disp = minutes 10..14 (5 min x 100 = 500). entry at 20 -> cut 19 -> ret = 15..19 = 5 x 100.
    x = _mk(idx, bars, fpm, fpp, 20, disp=(idx[10], idx[14]))
    check("5-min retrace over 5-min displacement = 1.0", compute("participation_to_touch", x), 1.0)
    # entry at 15 -> cut 14 -> ret window (14, 14] is EMPTY -> UNDEFINED, not 0.
    x = _mk(idx, bars, fpm, fpp, 15, disp=(idx[10], idx[14]))
    check("retracement shorter than a minute -> NaN, not 0", compute("participation_to_touch", x),
          float("nan"))
    # entry at 25, disp 10..14 -> ret 15..24 = 10 x 100 / 500 = 2.0
    x = _mk(idx, bars, fpm, fpp, 25, disp=(idx[10], idx[14]))
    check("10-min retrace over 5-min displacement = 2.0", compute("participation_to_touch", x), 2.0)

    print("\n  disp_delta_magnitude")
    # disp 10..14 -> |sum delta| = |5 x 10| = 50; session median vol = 100 -> 0.5
    x = _mk(idx, bars, fpm, fpp, 20, disp=(idx[10], idx[14]))
    check("|5x10| / median vol 100 = 0.5", compute("disp_delta_magnitude", x), 0.5)
    # sign must not matter: flip delta to -10, magnitude identical
    _, _, fneg, _ = _synth(n=60, vol=100.0, delta=-10.0)
    x2 = _mk(idx, bars, fneg, fpp, 20, disp=(idx[10], idx[14]))
    check("UNSIGNED: delta -10 gives the same value", compute("disp_delta_magnitude", x2), 0.5)

    print("\n  volume_pace_at_entry")
    fp2 = fpm.copy(); fp2.loc[idx[15:20], "vol"] = 300.0     # last 5 completed before entry@20
    x = _mk(idx, bars, fp2, fpp, 20)
    check("last-5 mean 300 / session median 100 = 3.0", compute("volume_pace_at_entry", x), 3.0)

    print("\n  cvd_slope_pre_15")
    # constant delta d per minute -> cumsum is linear with slope d; /median vol
    x = _mk(idx, bars, fpm, fpp, 30)
    check("constant delta 10, median vol 100 -> slope 0.1", compute("cvd_slope_pre_15", x), 0.1)
    flat = fpm.copy(); flat["delta"] = 0.0
    x = _mk(idx, bars, flat, fpp, 30)
    check("zero delta -> slope 0.0", compute("cvd_slope_pre_15", x), 0.0)

    print("\n  absorption_pre_5")
    # vol 100x5=500, range: closes flat at 20000 -> high 20002 low 19998 -> range 4
    # delta 0 -> (500/4) * (1 - 0) = 125
    x = _mk(idx, bars, flat, fpp, 20)
    check("500 vol / 4pt range, zero net delta = 125", compute("absorption_pre_5", x), 125.0)
    # fully one-sided: |delta| == vol -> multiplier 0 -> absorption 0
    onesided = fpm.copy(); onesided["delta"] = onesided["vol"]
    x = _mk(idx, bars, onesided, fpp, 20)
    check("fully one-sided -> 0 (no absorption)", compute("absorption_pre_5", x), 0.0)

    print("\n  vpoc_distance_at_entry  (roll-clean dependent)")
    i2, b2, f2, p2 = _synth(n=60, vol=100.0, px=20000.0, step=0.0)
    p2 = p2.copy(); p2.loc[i2[0:10], "price"] = 19990.0      # heaviest cluster away from price
    p2.loc[i2[0:10], "volume"] = 1000.0
    x = _mk(i2, b2, f2, p2, 30)
    # vpoc 19990, last close 20000, range = high-low over [<=cut] = 20002-19998 = 4
    check("(20000 - 19990) * side / 4 = 2.5", compute("vpoc_distance_at_entry", x), 2.5)
    x = _mk(i2, b2, f2, p2, 30, side=-1)
    check("side = -1 flips the sign", compute("vpoc_distance_at_entry", x), -2.5)

    print("\n  cvd_price_divergence_pre")
    i3 = pd.date_range("2026-01-05 09:00", periods=60, freq="1min", tz=NY)
    close = np.full(60, 20000.0); close[10] = 19980.0; close[30] = 19970.0   # lower low at 30
    b3 = pd.DataFrame({"open": close, "high": close + 1, "low": close, "close": close}, index=i3)
    d3 = np.zeros(60); d3[11:31] = 5.0                       # CVD rises between the two lows
    f3 = pd.DataFrame({"vol": np.full(60, 100.0), "delta": d3}, index=i3)
    x = _mk(i3, b3, f3, fpp, 45, side=1)
    got = compute("cvd_price_divergence_pre", x)
    check("lower low + higher CVD -> positive divergence", got > 0, True)
    d4 = np.zeros(60); d4[11:31] = -5.0                      # CVD falls with price -> no divergence
    f4 = pd.DataFrame({"vol": np.full(60, 100.0), "delta": d4}, index=i3)
    x = _mk(i3, b3, f4, fpp, 45, side=1)
    check("lower low + lower CVD -> negative (confirmation)",
          compute("cvd_price_divergence_pre", x) < 0, True)

    print("\n  BOUNDARY ENFORCEMENT — the library masks, the feature is not trusted")
    # Put a huge spike AT and AFTER the entry minute. Nothing may change.
    spike = fpm.copy(); spike.loc[idx[20:], "vol"] = 1e6; spike.loc[idx[20:], "delta"] = 1e6
    a = compute("volume_pace_at_entry", _mk(idx, bars, fpm, fpp, 20))
    b_ = compute("volume_pace_at_entry", _mk(idx, bars, spike, fpp, 20))
    check("1e6 spike at/after entry cannot move the value", b_, a)


# ------------------------------------------------------------------ B. real-event proofs
def _real_events():
    """Every historical event in the repo that carries a logged entry timestamp."""
    from scripts.footprint_clean import minute_frame, price_frame
    from scripts.nya_sb01_feasibility import load_bars

    fpm = minute_frame(clean=True)
    fpp = price_frame().set_index("ts")[["price", "volume", "side"]]
    bars = load_bars().set_index("ts")[["open", "high", "low", "close"]]

    rows = []
    ash = ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-orderflow-trades.csv"
    if ash.exists():
        d = pd.read_csv(ash)
        for c in ("disp_start", "disp_end", "entry_ts"):
            d[c] = pd.to_datetime(d[c], utc=True).dt.tz_convert(NY)
        for r in d.itertuples():
            rows.append(("ash-unicorn-sb", r.date, r.entry_ts, r.disp_start, r.disp_end,
                         1 if r.direction == "long" else -1))
    for p in sorted((ROOT / "research/_shared/sweep-logs").glob("*.csv")):
        d = pd.read_csv(p)
        d["ts"] = pd.to_datetime(d.date + " " + d.time).dt.tz_localize(NY, ambiguous="NaT",
                                                                      nonexistent="NaT")
        d = d.dropna(subset=["ts"])
        for r in d.itertuples():
            rows.append((p.stem, r.date, r.ts, None, None,
                         1 if r.direction == "long" else -1))
    return rows, bars, fpm, fpp


def lookahead_proofs():
    print("\n\nB. LOOK-AHEAD PROOFS ON EVERY REAL HISTORICAL EVENT")
    print("   (recompute with all rows from the entry minute onward DELETED; must be identical)\n")
    rows, bars, fpm, fpp = _real_events()
    print(f"   events found: {len(rows)}   sources: {len(set(r[0] for r in rows))}\n")
    tally = {n: {"n": 0, "same": 0, "defined": 0} for n in REGISTRY}
    for src, day, ets, ds, de, side in rows:
        s0 = ets.normalize() + pd.Timedelta(hours=8)
        cut = ets - pd.Timedelta(minutes=1)
        lo = ets.normalize()
        hi = ets + pd.Timedelta(hours=4)
        x = FeatureInput(day=day, entry_ts=ets, cut=cut, side=side, sess_start=s0,
                         disp_start=ds, disp_end=de,
                         bars=bars[(bars.index >= lo) & (bars.index <= hi)],
                         fpm=fpm[(fpm.index >= lo) & (fpm.index <= hi)],
                         fpp=fpp[(fpp.index >= lo) & (fpp.index <= hi)])
        for name in REGISTRY:
            full, masked, same = prove_no_lookahead(name, x)
            t = tally[name]
            t["n"] += 1; t["same"] += int(same); t["defined"] += int(full == full)
    print(f"   {'feature':<30}{'events':>8}{'identical':>11}{'defined':>9}  verdict")
    print("   " + "-" * 72)
    for name, t in tally.items():
        ok = t["same"] == t["n"]
        if not ok:
            FAILS.append(f"lookahead:{name}")
        print(f"   {name:<30}{t['n']:>8}{t['same']:>11}{t['defined']:>9}"
              f"  {'PROOF PASSES' if ok else 'LOOK-AHEAD DETECTED'}")
    und = [n for n, t in tally.items() if t["defined"] < 0.5 * t["n"]]
    if und:
        print(f"\n   ⚠️ mostly UNDEFINED on real events (a property, not a bug): {', '.join(und)}")


if __name__ == "__main__":
    unit_tests()
    lookahead_proofs()
    print("\n" + "=" * 78)
    if FAILS:
        print(f"❌ {len(FAILS)} FAILURE(S): {FAILS}")
        sys.exit(1)
    print("✅ ALL UNIT TESTS AND ALL LOOK-AHEAD PROOFS PASS.")
