#!/usr/bin/env python3
"""LDN-FLOW-01 event rebuild — the SAME events as the published censuses, but carrying
the timestamps needed to join order flow.

WHY THIS FILE EXISTS. ldn_trap01_census and ldn_vwap01_census return day/era/signed_ret
only. To ask anything about flow AT ENTRY we need the entry minute itself, and the push
that preceded it. This file re-runs the identical event logic and records:

    ts_entry       the minute t at which the event fires (the entry minute)
    ts_push_start  the minute the push into the extreme began (break bar / touch bar)

NOTHING ABOUT THE EVENT DEFINITION IS CHANGED. `verify()` asserts that the rebuilt event
counts and mean signed_ret match the published verdicts to 2dp, per era, per candidate.
If the event set drifts, the assert fires and the numbers below are not comparable to
anything already signed off.

The push window is [ts_push_start, ts_entry] — event-defined, not a free parameter, and
strictly at or before t. The outcome is measured over (t, window close]. No flow measure
may read a minute after t.

SEALED-SPAN GUARD: inherited from fit_only(). 2023/24 dropped. No holdout look.

    python -m scripts.ldn_flow01_events
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
BREAK_TICKS, TICK = 4, 0.25          # LDN-TRAP-01, declared
RECLAIM_MIN = 15                     # LDN-TRAP-01, declared
SIGMA_MULT = 2.0                     # LDN-VWAP-01, declared

# Published in docs/VERDICT-LDN-TRAP-01.md and docs/VERDICT-LDN-VWAP-01.md.
PUBLISHED = {
    ("trap", "2025"): (161, -2.30), ("trap", "2026"): (89, -2.64),
    ("vwap", "2025"): (77, -3.81), ("vwap", "2026"): (38, -12.15),
}


def _load():
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    prev = {d: days[i - 1] for i, d in enumerate(days) if i}
    return sub, by_day, prev


def build_trap() -> pd.DataFrame:
    """Verbatim LDN-TRAP-01 event logic, plus ts_entry / ts_push_start."""
    sub, by_day, prev = _load()
    rows = []
    for r in sub.itertuples():
        g, pg = by_day.get(r.day), by_day.get(prev.get(r.day, ""))
        if g is None or pg is None:
            continue
        start, end = london_window_et(r.day)
        on = pd.concat([pg[pg.ts >= pg.ts.dt.normalize() + pd.Timedelta(hours=18)],
                        g[g.ts < start]])
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30 or not len(on):
            continue
        levels = [("ONH", float(on.high.max()), +1), ("ONL", float(on.low.min()), -1),
                  ("PDH", r.prior_rth_hi, +1), ("PDL", r.prior_rth_lo, -1)]

        best = None
        for name, lvl, side in levels:
            if lvl is None or pd.isna(lvl):
                continue
            buf = BREAK_TICKS * TICK
            brk = w.index[(w.high > lvl + buf) if side > 0 else (w.low < lvl - buf)]
            if not len(brk):
                continue
            b = int(brk[0])
            seg = w.iloc[b: b + RECLAIM_MIN + 1]
            back = seg.index[(seg.close < lvl) if side > 0 else (seg.close > lvl)]
            if not len(back):
                continue
            t = int(back[0])
            if best is None or t < best["t"]:
                best = {"day": r.day, "era": r.day[:4], "cand": "trap", "t": t,
                        "direction": -side,
                        "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * (-side),
                        "ts_entry": w.ts.iloc[t], "ts_push_start": w.ts.iloc[b]}
        if best:
            best.pop("t")
            rows.append(best)
    return pd.DataFrame(rows)


def build_vwap() -> pd.DataFrame:
    """Verbatim LDN-VWAP-01 event logic (gated arm), plus ts_entry / ts_push_start."""
    sub, by_day, prev = _load()
    rows = []
    for r in sub.itertuples():
        g, pg = by_day.get(r.day), by_day.get(prev.get(r.day, ""))
        if g is None or pg is None:
            continue
        start, end = london_window_et(r.day)
        on = pd.concat([pg[pg.ts >= pg.ts.dt.normalize() + pd.Timedelta(hours=18)],
                        g[g.ts < start]])
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30 or len(on) < 60 or on.volume.sum() <= 0:
            continue
        vwap = float((on.close * on.volume).sum() / on.volume.sum())
        sigma = float(np.sqrt((((on.close - vwap) ** 2) * on.volume).sum()
                              / on.volume.sum()))
        if sigma <= 0:
            continue
        up, dn = vwap + SIGMA_MULT * sigma, vwap - SIGMA_MULT * sigma
        drive = bool(w.close.iloc[0] > r.asia_hi or w.close.iloc[0] < r.asia_lo)

        hit_up = w.index[w.high >= up]
        hit_dn = w.index[w.low <= dn]
        if not len(hit_up) and not len(hit_dn):
            continue
        i_up = hit_up[0] if len(hit_up) else len(w)
        i_dn = hit_dn[0] if len(hit_dn) else len(w)
        i, side = (int(i_up), +1) if i_up <= i_dn else (int(i_dn), -1)

        t, run = None, 0
        for j in range(i, len(w)):
            c = w.close.iloc[j]
            beyond = (c > up) if side > 0 else (c < dn)
            if beyond:
                run += 1
                if run >= 2:
                    break
            else:
                t = j
                break
        if t is None:
            continue
        rows.append({"day": r.day, "era": r.day[:4], "cand": "vwap",
                     "gated": not drive, "direction": -side,
                     "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * (-side),
                     "ts_entry": w.ts.iloc[t], "ts_push_start": w.ts.iloc[i]})
    d = pd.DataFrame(rows)
    return d[d.gated].drop(columns=["gated"]).reset_index(drop=True)


def verify(d: pd.DataFrame) -> None:
    """Assert the rebuild reproduces the signed-off verdicts. Non-negotiable."""
    for (cand, era), (n_exp, m_exp) in PUBLISHED.items():
        s = d[(d.cand == cand) & (d.era == era)].signed_ret
        assert len(s) == n_exp, f"{cand} {era}: n {len(s)} != published {n_exp}"
        assert abs(s.mean() - m_exp) < 0.005, (
            f"{cand} {era}: mean {s.mean():.4f} != published {m_exp}")
    print("VERIFIED — rebuilt event sets match the published verdicts exactly.")


def events() -> pd.DataFrame:
    d = pd.concat([build_trap(), build_vwap()], ignore_index=True)
    verify(d)
    assert (d.ts_push_start <= d.ts_entry).all(), "push window must end at or before t"
    return d


def main() -> None:
    d = events()
    print(f"\npooled events: {len(d)}")
    for cand in ("trap", "vwap"):
        for era in ("2025", "2026"):
            s = d[(d.cand == cand) & (d.era == era)]
            push = (s.ts_entry - s.ts_push_start).dt.total_seconds() / 60
            print(f"  {cand} {era}: n {len(s):>4}  mean {s.signed_ret.mean():>+7.2f}  "
                  f"push length min/med/max {push.min():.0f}/{push.median():.0f}/"
                  f"{push.max():.0f} min")


if __name__ == "__main__":
    main()
