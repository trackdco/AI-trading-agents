#!/usr/bin/env python3
"""Part B — order-flow filters on ash-unicorn-sb (AM1 only).

Two filters, both declared in ash-unicorn-sb-orderflow.md BEFORE running:

  F1 DISPLACEMENT DELTA — signed delta over the MSS displacement leg, normalised by the
     session's median minute volume. Substitute for the ES confirmation we cannot compute.
     CONFIRM = strongly with the trade. Threshold: > 0 (the least-searched cut that exists).

  F2 RETRACEMENT PARTICIPATION — volume during the FVG fill relative to the displacement
     leg. A healthy pullback into a gap is PASSIVE. CONFIRM = fill volume BELOW displacement
     volume. Threshold: ratio < 1.0 (again, the natural cut, not a searched one).

Both read only minutes AT OR BEFORE the entry bar. Asserted at runtime.

Flow span 2025-06-01+ covers 19 of the 24 baseline trades, so the honest comparator is the raw
baseline RESTRICTED TO THE SAME 19. Both are reported. (Was 29 of 37 before the 2026-08-07
sweep-gate fix; the counts below are computed, not written down.)

    python -m scripts.ash_orderflow_test
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ash_raw_baseline import SESSIONS, daily_bias  # noqa: E402
from scripts.nya_sb01_feasibility import (  # noqa: E402
    MSS_LOOKBACK, find_fvg, load_bars, order_block, session_extremes, swing_levels,
)

NY = "America/New_York"
RTH_END = 16 * 60
COST_USD, PT = 25.0, 20.0


def flow_frame() -> pd.DataFrame:
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp.index = pd.to_datetime(fp.index)
    return fp[["vol", "delta"]].sort_index()


def run(bars: pd.DataFrame, fp: pd.DataFrame) -> pd.DataFrame:
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    trades = []
    for k, day in enumerate(days):
        g, prev = by_day[day], by_day[days[k - 1]] if k else None
        if prev is None:
            continue
        bias = daily_bias(bars, day)
        for name, m0, m1 in SESSIONS["NY"]:
            w = g[(g.mins >= m0) & (g.mins <= m1)].reset_index(drop=True)
            if len(w) < 20:
                continue
            hs, ls = swing_levels(g, m0)
            ext = session_extremes(g, prev)
            cands = ([(x, -1) for x in hs + [ext.get("asia_hi"), ext.get("lon_hi")] if x]
                     + [(x, +1) for x in ls + [ext.get("asia_lo"), ext.get("lon_lo")] if x])
            for lv, side in cands:
                if bias != side:
                    continue
                # ⚠️ SWEEP GATE, fixed 2026-08-07 — same defect as ash_raw_baseline.py, which
                # this file duplicates. The test used to ask WHERE PRICE IS, not WHETHER IT
                # CROSSED, so a level already breached before 09:45 scored a sweep on bar 0.
                o0 = float(w.open.iloc[0])
                if (o0 > lv) if side < 0 else (o0 < lv):
                    continue
                hit = (w.high > lv) if side < 0 else (w.low < lv)
                if not hit.any():
                    continue
                s = int(hit.idxmax())
                seg, post = w.iloc[max(0, s - MSS_LOOKBACK):s + 1], w.iloc[s + 1:]
                if not len(seg) or not len(post):
                    continue
                ref = float(seg.low.min()) if side < 0 else float(seg.high.max())
                brk = (post.close < ref) if side < 0 else (post.close > ref)
                if not brk.any():
                    continue
                m = int(brk.idxmax())
                fv = find_fvg(w, m, side)
                if fv is None:
                    continue
                edge, _far, fstart = fv
                ob, _ = order_block(w, fstart, side)
                if ob is None:
                    continue
                fwd = w.iloc[m + 1:]
                fill = (fwd.high >= edge) if side < 0 else (fwd.low <= edge)
                if not len(fwd) or not fill.any():
                    continue
                t = int(fill.idxmax())
                entry, stop = float(edge), float(ob)
                risk = abs(entry - stop)
                if risk <= 0:
                    continue

                # ---------- FLOW, read only over minutes <= entry ----------
                ts_disp0, ts_disp1 = w.ts.iloc[fstart], w.ts.iloc[m]
                ts_entry = w.ts.iloc[t]
                disp = fp[(fp.index >= ts_disp0) & (fp.index <= ts_disp1)]
                ret = fp[(fp.index > ts_disp1) & (fp.index <= ts_entry)]
                sess_vol = fp[(fp.index >= w.ts.iloc[0]) & (fp.index <= ts_entry)].vol
                assert disp.index.max() <= ts_entry if len(disp) else True
                assert ret.index.max() <= ts_entry if len(ret) else True
                med = float(sess_vol.median()) if len(sess_vol) else np.nan
                f1 = (float(disp.delta.sum()) * side / med) if (len(disp) and med) else np.nan
                dv = float(disp.vol.sum()); rv = float(ret.vol.sum())
                f2 = (rv / dv) if dv > 0 and len(ret) else np.nan

                target = entry - 2 * risk if side < 0 else entry + 2 * risk
                half = entry - risk if side < 0 else entry + risk
                # SAME-BAR FILL-AND-STOP (fixed 2026-08-07, mirrors ash_raw_baseline.py).
                fb = w.iloc[t]
                same_bar_stop = (fb.high >= stop) if side < 0 else (fb.low <= stop)
                tail = pd.concat([w.iloc[t + 1:], g[(g.mins > m1) & (g.mins <= RTH_END)]])
                cur, be, out = stop, False, None
                if same_bar_stop:
                    out = -1.0
                for _, bar in (tail.iterrows() if out is None else iter([])):
                    if side < 0:
                        if bar.high >= cur:
                            out = 0.0 if be else -1.0; break
                        if bar.low <= target:
                            out = 2.0; break
                        if not be and bar.low <= half:
                            cur, be = entry, True
                    else:
                        if bar.low <= cur:
                            out = 0.0 if be else -1.0; break
                        if bar.high >= target:
                            out = 2.0; break
                        if not be and bar.high >= half:
                            cur, be = entry, True
                if out is None:
                    last = float(tail.close.iloc[-1]) if len(tail) else entry
                    out = float(((entry - last) if side < 0 else (last - entry)) / risk)
                trades.append({"date": day, "time": f"{ts_entry:%H:%M}", "session": "NY",
                               # flow-window PROVENANCE, logged so the boundaries are auditable
                               "disp_start": ts_disp0, "disp_end": ts_disp1, "entry_ts": ts_entry,
                               "window": name, "direction": "short" if side < 0 else "long",
                               "entry": round(entry, 2), "stop": round(stop, 2),
                               "target": round(target, 2), "risk_pts": round(risk, 2),
                               "R": round(out, 3),
                               "outcome": "win" if out >= 2 else ("BE" if out == 0 else
                                          ("loss" if out <= -1 else "timeout")),
                               "F1_disp_delta": round(f1, 3) if f1 == f1 else np.nan,
                               "F2_retrace_ratio": round(f2, 3) if f2 == f2 else np.nan})
                break
    return pd.DataFrame(trades)


def summarise(d: pd.DataFrame, label: str) -> dict:
    if not len(d):
        return {"filter": label, "n": 0}
    c = float((COST_USD / (d.risk_pts * PT)).mean())
    eq = d.R.cumsum()
    return {"filter": label, "n": len(d), "win_rate": (d.R >= 2).mean(),
            "avg_R": d.R.mean(), "expectancy": d.R.mean() - c,
            "total_R": d.R.sum(), "maxDD": float((eq.cummax() - eq).max())}


def main() -> None:
    bars, fp = load_bars(), flow_frame()
    d = run(bars, fp)
    d.to_csv(ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-orderflow-trades.csv",
             index=False)
    cov = d.dropna(subset=["F1_disp_delta", "F2_retrace_ratio"])
    print("ORDER-FLOW FILTERS on ash-unicorn-sb (AM1 09:45-10:15 ET)")
    print(f"baseline trades {len(d)}   with flow data {len(cov)}   "
          f"(flow starts 2025-06-01)\n")
    rows = [summarise(d, f"RAW baseline (all {len(d)})"),
            summarise(cov, f"RAW baseline ({len(cov)} flow-covered) <- comparator"),
            summarise(cov[cov.F1_disp_delta > 0], "F1 displacement delta > 0"),
            summarise(cov[cov.F2_retrace_ratio < 1.0], "F2 retrace vol < displacement vol"),
            summarise(cov[(cov.F1_disp_delta > 0) & (cov.F2_retrace_ratio < 1.0)],
                      "F1 + F2 combined")]
    t = pd.DataFrame(rows)
    t["kept_%"] = (100 * t.n / len(cov)).round(0)
    print(t.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    print(f"\nF1 distribution: median {cov.F1_disp_delta.median():+.2f}, "
          f"share >0 {100*(cov.F1_disp_delta > 0).mean():.0f}%")
    print(f"F2 distribution: median {cov.F2_retrace_ratio.median():.2f}, "
          f"share <1 {100*(cov.F2_retrace_ratio < 1).mean():.0f}%")


if __name__ == "__main__":
    main()
