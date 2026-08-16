#!/usr/bin/env python3
"""STUDY H — travel regression (prereg §H). The DV changed, not the candidates.

Reject arm, fit, shipped exit (hold-with-stop), netR = money DV (barred);
travel_max_W and arrival reported alongside. Candidates with DECLARED signs:
H1 next_level_dist_W (+), H2 path_emptiness (+ = fewer levels within 1.0W
ahead), H3 bw_expansion (+ = w15 now / w15 4 completed bars ago > 1).
Bar per candidate: declared-sign Spearman in BOTH eras; family >=1 of 3 with
|rho|>=0.05 both eras. One run.

    python -m scripts.htf_ma_study_h
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands, profile_at_minutes  # noqa: E402

TICK = 0.25
COST_PTS = 0.5


def rho_rank(a, b) -> float:
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    R = F[(F.kind == "reject") & (F.target_defined == True)].copy()   # noqa: E712
    R = R.reset_index(drop=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]

    netR = np.full(len(R), np.nan)
    trav = np.full(len(R), np.nan)
    empt = np.full(len(R), np.nan)
    bwx = np.full(len(R), np.nan)
    for day, g in R.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        if hist.empty:
            continue
        seg = hist[hist.index >= t0]
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
        _, w15 = bb_ma_asof(hist, 15)
        w15_f = w15.reindex(idx)
        vw = vwap_bands(hist)
        pm_minutes = sorted({pd.Timestamp(r.t) - pd.Timedelta(minutes=1)
                             for r in g.itertuples()})
        prof = profile_at_minutes(hist, pm_minutes)
        for i, r in g.iterrows():
            d = -1 if r.side == "below" else 1
            entry, risk_ref = r.event_px, None
            stop = (r.trig_high + TICK) if d < 0 else (r.trig_low - TICK)
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            e_t = pd.Timestamp(r.t)
            j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
            if j0 >= len(idx):
                continue
            exit_px, ext = cl[-1], 0.0
            for j in range(j0, len(idx)):
                ext = max(ext, d * ((hi[j] if d > 0 else lo[j]) - entry))
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    exit_px = stop
                    break
            netR[i] = (d * (exit_px - entry) - COST_PTS) / risk
            trav[i] = max(ext, 0.0) / r.w15
            # H2 path emptiness: count of levels within 1.0W AHEAD of entry
            pm = e_t - pd.Timedelta(minutes=1)
            p = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lv = [p.poc, p.vah, p.val]
            if vrow is not None:
                lv += [vrow.vwap, vrow.vwap_p1, vrow.vwap_m1,
                       vrow.vwap_p2, vrow.vwap_m2]
            ahead = [v for v in lv if np.isfinite(v)
                     and 0 < d * (v - entry) <= 1.0 * r.w15]
            empt[i] = -len(ahead)               # MORE empty = HIGHER value
            # H3 band-width expansion: w15 at event vs 60m (4 bars) earlier
            wl = w15_f.iloc[j0] if j0 < len(w15_f) else np.nan
            j_back = int(np.searchsorted(idx.values,
                                         (e_t - pd.Timedelta(minutes=60)).to_datetime64()))
            wb = w15_f.iloc[j_back] if 0 <= j_back < len(w15_f) else np.nan
            if np.isfinite(wl) and np.isfinite(wb) and wb > 0:
                bwx[i] = wl / wb
    R["netR"], R["trav"], R["empt"], R["bwx"] = netR, trav, empt, bwx
    R = R[R.netR.notna()]

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("STUDY H — travel regression (prereg §H), reject arm, shipped exit")
    cands = [("H1 next_level_dist_W", "next_level_dist_W", +1),
             ("H2 path_emptiness", "empt", +1),
             ("H3 bw_expansion", "bwx", +1)]
    family = []
    for name, col, sign in cands:
        oks = []
        for era in ("H2-2025", "H1-2026"):
            d = R[(R.era == era)].dropna(subset=[col])
            r_money = rho_rank(d[col], d.netR)
            r_trav = rho_rank(d[col], d.trav)
            r_arr = rho_rank(d[col], d["target_before_extreme_20"].astype(float))
            ok = (np.sign(r_money) == sign) and abs(r_money) >= 0.05
            oks.append(ok)
            emit(f"  {name:<22} {era}: netR rho {r_money:+.3f} "
                 f"{'OK ' if ok else 'MISS'} | travel {r_trav:+.3f} | "
                 f"arrival {r_arr:+.3f} (n={len(d):,})")
        family.append(all(oks))
        emit(f"    -> {'PASS' if all(oks) else 'FAIL'} (declared sign, both eras, |rho|>=0.05)")
    emit(f"\nFAMILY VERDICT (>=1 of 3): "
         f"{'PASS — the travel direction has at least one live candidate' if any(family) else 'FAIL — the reorientation reading weakens; the discretion-not-in-features reading strengthens'}")
    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## H — RESULT (run 2026-08-07)\n\n```\n" + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
