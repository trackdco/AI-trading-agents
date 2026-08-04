#!/usr/bin/env python3
"""LDN-SWP-01 — CORRECTED re-run on the true London session window.

WHY THIS EXISTS. The first run (scripts/ldn_swp01_census.py, per
docs/PREREG-london-asia-sweep-pair.md) hardcoded the outcome window as 03:00-06:00 ET.
That is wrong on two counts:

  1. The London session is 08:00-10:00 Europe/London — 03:00-05:00 ET in normal weeks.
     03:00-06:00 ET is 08:00-11:00 London: a THREE-hour window an hour past the close.
  2. Hardcoding ET hours is explicitly on the burn list (docs/HANDOFF-london-rebuild.md
     §7 item 1) — the two zones' DST offsets do not move together. The authority is
     `scripts/run_triggers_london.london_window_et(day)`.

This is a SPECIFICATION CORRECTION, not a new hypothesis. Same claim, same groups, same
decision rule; the session boundary is fixed. The first run's numbers are superseded.

Two things improve as a side effect:
  - the 35 dst_mismatch days no longer need excluding — the converter handles them, so
    they re-enter the sample;
  - the "dead hour" (pre-open sweep) is derived per day as [00:00 ET, london_open) rather
    than the substrate's hardcoded 00:00-03:00, which is itself wrong on mismatch days.

CAUSALITY, the defect that killed the first run: group P's direction was set by a breach
INSIDE the outcome window, making the outcome partly definitional. Here group P is
measured strictly from the breach forward, so nothing that defines the event is drawn from
the interval being measured.

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_swp01_london_only
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_census import welch

NY, LON = "America/New_York", "Europe/London"
PHI = NormalDist()
MIN_N_GROUP = 30


def london_window_et(day: str):
    """08:00-10:00 Europe/London for `day`, in ET. Mirrors run_triggers_london."""
    return (pd.Timestamp(f"{day} 08:00", tz=LON).tz_convert(NY),
            pd.Timestamp(f"{day} 10:00", tz=LON).tz_convert(NY))


def build() -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g for d, g in bars.groupby("day", sort=False)}

    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None or not len(g):
            continue
        start, end = london_window_et(r.day)
        pre = g[(g.ts >= start.normalize()) & (g.ts < start)]      # 00:00 ET -> London open
        win = g[(g.ts >= start) & (g.ts <= end)]
        if len(win) < 30 or not len(pre):
            continue

        # pre-open (dead) sweep, derived per day — not the substrate's hardcoded 00:00-03:00
        pre_hi = bool((pre.high > r.asia_hi).any())
        pre_lo = bool((pre.low < r.asia_lo).any())
        # in-session sweep, and WHEN it first happens (needed for the causal measurement)
        hi_hits = win.index[win.high > r.asia_hi]
        lo_hits = win.index[win.low < r.asia_lo]

        if pre_hi ^ pre_lo:                       # group D — settled before the open
            grp, direction, entry_px = "D", (1.0 if pre_hi else -1.0), win.close.iloc[0]
        elif (not pre_hi) and (not pre_lo) and (len(hi_hits) > 0) ^ (len(lo_hits) > 0):
            grp = "P"                             # group P — first breach is in-session
            direction = 1.0 if len(hi_hits) else -1.0
            i = (hi_hits if len(hi_hits) else lo_hits)[0]
            entry_px = win.loc[i, "close"]        # measure FROM the breach: causal
        else:
            continue                              # both sides, or no event

        rows.append({"day": r.day, "era": r.day[:4], "group": grp,
                     "signed_ret": (win.close.iloc[-1] - entry_px) * direction,
                     "asia_rng_pctl20": r.asia_rng_pctl20,
                     "mismatch": bool(r.dst_mismatch),
                     "win_et": f"{start:%H:%M}-{end:%H:%M}"})
    return pd.DataFrame(rows)


def delta_for(f: pd.DataFrame) -> float:
    a = f[f.group == "D"].signed_ret.to_numpy(float)
    b = f[f.group == "P"].signed_ret.to_numpy(float)
    return float(a.mean() - b.mean()) if len(a) > 1 and len(b) > 1 else float("nan")


def main() -> None:
    d = build()
    print("LONDON SESSION ONLY — 08:00-10:00 Europe/London, converted per day")
    print(f"windows seen in ET: {dict(d.win_et.value_counts())}")
    print(f"  (mismatch days now INCLUDED: {int(d.mismatch.sum())} — the converter "
          f"handles them)\n")
    print(f"events: {len(d)}   "
          f"{', '.join(f'{e}: {(d.era == e).sum()}' for e in ('2025', '2026'))}\n")
    print(f"{'era':>6} {'n(D)':>6} {'n(P)':>6} {'mean D':>9} {'mean P':>9} {'delta':>9}")
    for era in ("2025", "2026"):
        e = d[d.era == era]
        a, b = e[e.group == "D"].signed_ret, e[e.group == "P"].signed_ret
        print(f"{era:>6} {len(a):>6} {len(b):>6} {a.mean():>+9.2f} {b.mean():>+9.2f} "
              f"{a.mean() - b.mean():>+9.2f}")

    print("\n" + "=" * 84)
    print("FRAGILITY GATE (prereg §6) — first, before the primary is read")
    print("=" * 84)
    fired = []
    for era in ("2025", "2026"):
        e = d[d.era == era]
        full = delta_for(e)
        order = e.signed_ret.abs().sort_values().index
        parts = [f"full {full:+.2f}"]
        for k in (1, 3, 5, 10):
            t = delta_for(e.loc[order].iloc[:-k])
            parts.append(f"drop{k} {t:+.2f}")
            if k <= 3 and np.isfinite(t) and np.sign(t) != np.sign(full):
                fired.append(f"{era}@drop{k}")
        print(f"  {era}: " + " | ".join(parts))
    print(f"\n  GATE {'FIRES' if fired else 'CLEAR'}")

    print("\n" + "=" * 84)
    print("PRIMARY — delta = mean signed_ret(D) - mean signed_ret(P)")
    print("=" * 84)
    res = {}
    for era in ("2025", "2026"):
        e = d[d.era == era]
        a = e[e.group == "D"].signed_ret.to_numpy(float)
        b = e[e.group == "P"].signed_ret.to_numpy(float)
        diff, se, p = welch(a, b)
        res[era] = (diff, se, p, len(a), len(b))
        print(f"  {era}: delta {diff:>+8.2f}  se {se:>6.2f}  p {p:.3f}  n {len(a)}/{len(b)}"
              f"{'' if min(len(a), len(b)) >= MIN_N_GROUP else '  BELOW n>=30'}")
        print(f"         D mean {a.mean():+.2f} (continuation reads >0)  |  "
              f"P mean {b.mean():+.2f} (reversal reads <0)")

    d25, _, p25, *_ = res["2025"]
    d26, se26, p26, na, nb = res["2026"]
    lo, hi = d26 - 1.96 * se26, d26 + 1.96 * se26
    npass = (p25 <= 0.05 and p26 <= 0.05 and d25 > 0 and d26 > 0
             and min(res["2025"][3], res["2025"][4], na, nb) >= MIN_N_GROUP)
    fail = (not (lo <= d25 <= hi)) and (lo <= 0 <= hi or d26 < 0)
    verdict = ("FAIL (fragility)" if fired else "PASS" if npass
               else "FAIL" if fail else "INCONCLUSIVE ON POWER")
    print(f"\n  2026 95% CI on delta [{lo:+.2f}, {hi:+.2f}]  "
          f"contains 0: {'YES' if lo <= 0 <= hi else 'no'}")
    print("\n" + "=" * 84)
    print(f"VERDICT (London-only window): {verdict}")
    print("=" * 84)
    print("\n  Both group means are the numbers that matter — they test the two theses")
    print("  directly. A thesis needs its group mean to be materially non-zero.")


if __name__ == "__main__":
    main()
