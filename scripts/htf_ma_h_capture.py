#!/usr/bin/env python3
"""H-capture battery (prereg §H-capture). Frame persisted this time.

    python -m scripts.htf_ma_h_capture
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
MIN_CL = 30


def rho_rank(a, b) -> float:
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def build_frame() -> pd.DataFrame:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    R = F[(F.kind == "reject") & (F.target_defined == True)].copy()   # noqa: E712
    R = R.reset_index(drop=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    netR = np.full(len(R), np.nan)
    arr = np.full(len(R), np.nan)
    cnt = np.full(len(R), np.nan)
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
        prof = profile_at_minutes(hist, sorted({pd.Timestamp(r.t) - pd.Timedelta(minutes=1)
                                                for r in g.itertuples()}))
        for i, r in g.iterrows():
            d = -1 if r.side == "below" else 1
            entry = r.event_px
            stop = (r.trig_high + TICK) if d < 0 else (r.trig_low - TICK)
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            e_t = pd.Timestamp(r.t)
            j0 = int(np.searchsorted(idx.values, e_t.to_datetime64()))
            if j0 >= len(idx):
                continue
            exit_px = cl[-1]
            for j in range(j0, len(idx)):
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    exit_px = stop
                    break
            netR[i] = (d * (exit_px - entry) - COST_PTS) / risk
            arr[i] = float(r.target_before_extreme_20)
            pm = e_t - pd.Timedelta(minutes=1)
            p = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lv = [p.poc, p.vah, p.val]
            if vrow is not None:
                lv += [vrow.vwap, vrow.vwap_p1, vrow.vwap_m1,
                       vrow.vwap_p2, vrow.vwap_m2]
            cnt[i] = sum(1 for v in lv if np.isfinite(v)
                         and 0 < d * (v - entry) <= 1.0 * r.w15)
            wl = w15_f.iloc[j0]
            j_back = int(np.searchsorted(idx.values,
                                         (e_t - pd.Timedelta(minutes=60)).to_datetime64()))
            wb = w15_f.iloc[j_back] if 0 <= j_back < len(w15_f) else np.nan
            if np.isfinite(wl) and np.isfinite(wb) and wb > 0:
                bwx[i] = wl / wb
    R["netR"], R["arrival"], R["cnt_ahead"], R["bwx"] = netR, arr, cnt, bwx
    R["month"] = R.sess_day.str[:7]
    R = R[R.netR.notna() & R.cnt_ahead.notna()]
    R.to_parquet(ROOT / "output/htf_ma_census/h_capture_frame.parquet", index=False)
    return R


def main() -> None:
    R = build_frame()
    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("H-CAPTURE BATTERY (prereg §H-capture), reject arm, frame persisted")
    emit("\n== queries reported with the result ==")
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        emit(f"  {era}: corr(H1 dist, H2 emptiness=-cnt) = "
             f"{rho_rank(d.next_level_dist_W, -d.cnt_ahead):+.3f} | "
             f"corr(H2, H3 bwx) = {rho_rank(-d.cnt_ahead, d.bwx.fillna(d.bwx.median())):+.3f}")

    emit("\n== count-ahead bins in netR (two-part bar, both eras) ==")
    verdicts = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        means, top = [], None
        row = []
        for name, m in (("0", d.cnt_ahead == 0), ("1", d.cnt_ahead == 1),
                        ("2", d.cnt_ahead == 2), ("3+", d.cnt_ahead >= 3)):
            b = d[m]
            cm = b.groupby("cluster_id").netR.mean()
            am = b.groupby("cluster_id").arrival.mean()
            if len(cm) < MIN_CL:
                row.append(f"{name}:UNDERPWR(n{len(cm)})")
                continue
            mu, se = cm.mean(), cm.std(ddof=1) / np.sqrt(len(cm))
            means.append(mu)
            if name == "0":
                top = (mu, mu - 1.96 * se)
            row.append(f"{name}:{mu:+.3f}[{mu-1.96*se:+.3f},{mu+1.96*se:+.3f}]"
                       f"arr{am.mean()*100:.0f}%(n{len(cm)})")
        mono = all(means[k] >= means[k + 1] - 1e-12 for k in range(len(means) - 1))
        top_ok = top is not None and top[0] > 0 and top[1] > 0
        verdicts += [mono, top_ok]
        emit(f"  {era}: " + " ".join(row))
        emit(f"          monotone-decreasing={'Y' if mono else 'N'} | "
             f"count0>0 CI clear={'Y' if top_ok else 'N'}")

    emit("\n== MONTHLY LODO (14 folds): H2 netR rho sign per fold ==")
    for var, name in ((-R.cnt_ahead, "H2"), (R.bwx, "H3")):
        R["_v"] = var
        fails = []
        for m in sorted(R.month.unique()):
            d = R[R.month != m].dropna(subset=["_v"])
            r_ = rho_rank(d._v, d.netR)
            if r_ <= 0:
                fails.append(f"{m}({r_:+.3f})")
        emit(f"  {name}: {14 - len(fails)}/{len(sorted(R.month.unique()))} folds keep sign"
             + (f" | FAILING: {' '.join(fails)}" if fails else " | ALL FOLDS HOLD"))
    d25 = R[R.era == "H2-2025"].dropna(subset=["bwx"])
    d26 = R[R.era == "H1-2026"].dropna(subset=["bwx"])
    dc25 = d25.groupby("sess_day").apply(lambda x: rho_rank(x.bwx, x.netR)
                                         if len(x) >= 5 else np.nan).dropna()
    dc26 = d26.groupby("sess_day").apply(lambda x: rho_rank(x.bwx, x.netR)
                                         if len(x) >= 5 else np.nan).dropna()
    emit(f"\n  H3 day-clustered (mean of within-day rhos): "
         f"H2-2025 {dc25.mean():+.3f} (n={len(dc25)} days) | "
         f"H1-2026 {dc26.mean():+.3f} (n={len(dc26)} days)")

    final = all(verdicts)
    emit(f"\nBIN BAR: {'PASS' if final else 'FAIL'} | LODO read above | "
         "SPEC A-1 clause 5 resolves per the H2xH3 corr vs 0.4.")
    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## H-capture — RESULT (run 2026-08-08)\n\n```\n"
                 + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
