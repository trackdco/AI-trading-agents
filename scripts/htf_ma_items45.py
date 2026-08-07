#!/usr/bin/env python3
"""Items 4 + 5 + the final H2 sizing test (prereg: six-items block + item-3
diagnosis). Reject arm, shipped exit. Seventh-law arithmetic printed FIRST.

    python -m scripts.htf_ma_items45
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, vwap_bands, profile_at_minutes    # noqa: E402


def rho_rank(a, b) -> float:
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    R = pd.read_parquet(ROOT / "output/htf_ma_census/round3_frame.parquet")
    R = R[R.ship.notna() & R.trail_only.notna()].copy().reset_index(drop=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    beyond = np.full(len(R), np.nan)
    for day, g in R.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        if hist.empty:
            continue
        vw = vwap_bands(hist)
        prof = profile_at_minutes(hist, sorted({pd.Timestamp(r.t) - pd.Timedelta(minutes=1)
                                                for r in g.itertuples()}))
        for i, r in g.iterrows():
            d = -1 if r.side == "below" else 1
            entry = r.event_px
            stop = (r.trig_high + 0.25) if d < 0 else (r.trig_low - 0.25)
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            pm = pd.Timestamp(r.t) - pd.Timedelta(minutes=1)
            p_ = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lv = [p_.poc, p_.vah, p_.val]
            if vrow is not None:
                lv += [vrow.vwap, vrow.vwap_p1, vrow.vwap_m1,
                       vrow.vwap_p2, vrow.vwap_m2]
            beyond[i] = sum(1 for v in lv if np.isfinite(v)
                            and 3.0 < d * (v - entry) / risk <= 8.0)
    R["cnt_beyond"] = beyond
    R = R[R.cnt_beyond.notna()]
    R.to_parquet(ROOT / "output/htf_ma_census/items45_frame.parquet", index=False)

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("ITEMS 4+5 + FINAL H2 TEST (prereg six-items + item-3 diagnosis)")
    emit("\n== SEVENTH LAW FIRST (before any gate is read) ==")
    emit("  Ladder weights 0.5-2.0 bound the achievable gain: with any rho <=")
    emit("  0.25, weighted-minus-unweighted <= ~0.02R. The 2025 gap is 0.047R.")
    emit("  EXPECTATION SET: even a full pass closes AT MOST ~half the gap.")

    emit("\n== ITEM 4: obstacles beyond the partial (count in (3R,8R]) ==")
    emit(f"  distribution: {R.cnt_beyond.value_counts().sort_index().to_dict()}")
    era_ok = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        c = d.groupby("cluster_id").agg(x=("cnt_beyond", lambda v: -v.mean()),
                                        y=("ship", "mean"))
        r_ep = rho_rank(c.x, c.y)
        era_ok.append(r_ep > 0)
        emit(f"  {era}: row rho {rho_rank(-d.cnt_beyond, d.ship):+.3f} | "
             f"episode rho {r_ep:+.3f} (n_ep={len(c)})")
    fails = []
    for m in sorted(R.month.unique()):
        f_ = R[R.month != m]
        if rho_rank(-f_.cnt_beyond, f_.ship) <= 0:
            fails.append(m)
    emit(f"  period gate: {14-len(fails)}/14"
         + (f" FAILING {fails}" if fails else ""))
    emit(f"  ITEM 4 GATES: {'PASS' if all(era_ok) and not fails else 'FAIL'}")

    emit("\n== FINAL H2 TEST: direct count thresholds (declared encoding) ==")
    wmap = np.select([R.cnt_ahead <= 1, R.cnt_ahead == 2, R.cnt_ahead == 3],
                     [2.0, 1.5, 1.0], 0.5)
    R["wt"] = wmap
    legs = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        cu = d.groupby("cluster_id").ship.mean().mean()
        cw = ((d.ship * d.wt).groupby(d.cluster_id).sum()
              / d.wt.groupby(d.cluster_id).sum()).mean()
        legs += [cw > cu, cw > 0]
        emit(f"  {era}: unweighted {cu:+.4f} | count-ladder {cw:+.4f} | margin {cw-cu:+.4f}")
    fails = []
    for m in sorted(R.month.unique()):
        f_ = R[R.month != m]
        cu = f_.groupby("cluster_id").ship.mean().mean()
        cw = ((f_.ship * f_.wt).groupby(f_.cluster_id).sum()
              / f_.wt.groupby(f_.cluster_id).sum()).mean()
        if cw <= cu:
            fails.append(m)
    emit(f"  LODO: {14-len(fails)}/14"
         + (f" FAILING {fails}" if fails else ""))
    emit(f"  FINAL H2 VERDICT (three legs): "
         f"{'PASS' if all(legs) and not fails else 'FAIL — H2-as-sizing is CLOSED permanently'}")

    emit("\n== ITEM 5: joint 2x2 — exit x selection (selection-on = cnt_ahead<=2) ==")
    for era in ("H2-2025", "H1-2026"):
        for sel, name in ((R.cnt_ahead.notna(), "ALL"), (R.cnt_ahead <= 2, "SELECTED")):
            d = R[(R.era == era) & sel]
            ps = d.groupby("cluster_id").ship.mean().mean()
            tt = d.groupby("cluster_id").trail_only.mean().mean()
            emit(f"  {era} {name:<9}: partial {ps:+.4f} | trail-only {tt:+.4f} "
                 f"| partial-earns {ps-tt:+.4f} (n_cl={d.cluster_id.nunique()})")
    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## Items 4+5 + final H2 — RESULT (run 2026-08-08)\n\n```\n"
                 + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
