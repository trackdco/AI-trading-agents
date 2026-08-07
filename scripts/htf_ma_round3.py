#!/usr/bin/env python3
"""ROUND 3 (prereg §Round 3) — ablation, structural partial, H2 re-priced,
Job 3 discharged. Reject arm, shipped exit P75_3.0_trail, frame WITH KEYS.

    python -m scripts.htf_ma_round3
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
P = 0.75


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

    cols = {k: np.full(len(R), np.nan) for k in
            ("ship", "trail_only", "struct", "cnt_ahead", "bwx", "struct_T")}
    for day, g in R.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                    (bars.index < t0 + pd.Timedelta(hours=23))]
        if hist.empty:
            continue
        seg = hist[hist.index >= t0]
        idx = seg.index
        hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
        ma15, w15 = bb_ma_asof(hist, 15)
        w15_f = w15.reindex(idx)
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"high": "max", "low": "min", "close": "last"}).dropna()
        ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
        ma_f15.index = f15.index
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
            cost_r = COST_PTS / risk
            # walk: stop bar, touches at 3R and struct target, trail leg
            pm = e_t - pd.Timedelta(minutes=1)
            p_ = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lv = [p_.poc, p_.vah, p_.val]
            if vrow is not None:
                lv += [vrow.vwap, vrow.vwap_p1, vrow.vwap_m1,
                       vrow.vwap_p2, vrow.vwap_m2]
            beyond = [v for v in lv if np.isfinite(v)
                      and d * (v - entry) / risk >= 2.0]
            struct_px = min(beyond, key=lambda v: d * (v - entry)) if beyond \
                else entry + d * 3.0 * risk
            struct_T = d * (struct_px - entry) / risk
            cols["struct_T"][i] = struct_T
            cols["cnt_ahead"][i] = sum(1 for v in lv if np.isfinite(v)
                                       and 0 < d * (v - entry) <= 1.0 * r.w15)
            wl = w15_f.iloc[j0]
            j_back = int(np.searchsorted(idx.values,
                                         (e_t - pd.Timedelta(minutes=60)).to_datetime64()))
            wb = w15_f.iloc[j_back] if 0 <= j_back < len(w15_f) else np.nan
            if np.isfinite(wl) and np.isfinite(wb) and wb > 0:
                cols["bwx"][i] = wl / wb
            stop_j, t3, ts_ = None, None, None
            for j in range(j0, len(idx)):
                if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                    stop_j = j
                    break
                fav = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
                if t3 is None and fav >= 3.0:
                    t3 = j
                if ts_ is None and fav >= struct_T:
                    ts_ = j
            eod_r = d * (cl[-1] - entry) / risk
            hold_r = -1.0 if stop_j is not None else eod_r
            tstop, trail_r = stop, None
            fbars = f15[f15.index > idx[j0]]
            fi = list(fbars.index)
            pos = 0
            for j in range(j0, len(idx)):
                if (lo[j] <= tstop) if d > 0 else (hi[j] >= tstop):
                    trail_r = d * (tstop - entry) / risk
                    break
                while pos < len(fi) and fi[pos] <= idx[j]:
                    fb = fbars.iloc[pos]
                    m = ma_f15.get(fi[pos], np.nan)
                    if np.isfinite(m) and d * (fb.close - m) > 0:
                        cand = (fb.low - TICK) if d > 0 else (fb.high + TICK)
                        if d * (cand - tstop) > 0:
                            tstop = cand
                    pos += 1
            if trail_r is None:
                trail_r = eod_r
            leg3 = (3.0 * risk - TICK) / risk if t3 is not None else None
            legS = (struct_T * risk - TICK) / risk if ts_ is not None else None
            cols["ship"][i] = (P * leg3 + (1 - P) * trail_r if leg3 is not None
                               else trail_r) - cost_r
            cols["trail_only"][i] = trail_r - cost_r
            cols["struct"][i] = (P * legS + (1 - P) * trail_r if legS is not None
                                 else trail_r) - cost_r
    for k, v in cols.items():
        R[k] = v
    R["month"] = R.sess_day.str[:7]
    R = R[R.ship.notna()]
    R.to_parquet(ROOT / "output/htf_ma_census/round3_frame.parquet", index=False)

    lines = []
    def emit(s=""):
        print(s)
        lines.append(s)

    emit("ROUND 3 (prereg): ablation | structural partial | H2 re-priced | Job 3")
    emit("\n== 1. ABLATION: shipped vs TRAIL_ONLY ==")
    simpler = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        s_ = d.groupby("cluster_id").ship.mean().mean()
        t_ = d.groupby("cluster_id").trail_only.mean().mean()
        simpler.append(t_ >= s_)
        emit(f"  {era}: shipped {s_:+.3f} | trail-only {t_:+.3f} | "
             f"partial earns {'NOTHING' if t_ >= s_ else f'{s_-t_:+.3f}'}")
    fails = []
    for m in sorted(R.month.unique()):
        f_ = R[R.month != m]
        if f_.groupby("cluster_id").ship.mean().mean() <= \
           f_.groupby("cluster_id").trail_only.mean().mean():
            fails.append(m)
    emit(f"  LODO on the margin: {14-len(fails)}/14 folds shipped>trail-only"
         + (f" | FAILING {fails}" if fails else ""))
    emit(f"  DECLARED CONSEQUENCE: {'TRAIL-ONLY SHIPS (simpler rule wins/ties both eras)' if all(simpler) else 'partial EARNS ITS PLACE — two-part rule stands'}")

    emit("\n== 2. STRUCTURAL vs FIXED partial ==")
    struct_wins = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        s_ = d.groupby("cluster_id").ship.mean().mean()
        st = d.groupby("cluster_id")["struct"].mean().mean()
        struct_wins.append(st > s_)
        emit(f"  {era}: fixed-3R {s_:+.3f} | structural>=2R {st:+.3f} "
             f"(median struct T {d.struct_T.median():.2f}R)")
    emit(f"  {'STRUCTURAL becomes a declared candidate (wins both eras)' if all(struct_wins) else 'fixed-3R stands (structural does not win both eras)'}")

    emit("\n== 3. H2 RE-PRICED under shipped exit (three gates) ==")
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era].dropna(subset=["cnt_ahead"])
        c = d.groupby("cluster_id").agg(x=("cnt_ahead", lambda v: -v.mean()),
                                        y=("ship", "mean"))
        emit(f"  {era}: row rho {rho_rank(-d.cnt_ahead, d.ship):+.3f} | "
             f"episode rho {rho_rank(c.x, c.y):+.3f} (n_ep={len(c)})")
    fails = []
    for m in sorted(R.month.unique()):
        f_ = R[R.month != m].dropna(subset=["cnt_ahead"])
        if rho_rank(-f_.cnt_ahead, f_.ship) <= 0:
            fails.append(m)
    emit(f"  period gate: {14-len(fails)}/14 folds keep sign"
         + (f" | FAILING {fails}" if fails else ""))

    emit("\n== 4. JOB 3 — H3 solo bar under shipped exit ==")
    verdicts = []
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era].dropna(subset=["bwx"]).copy()
        d["q"] = pd.qcut(d.bwx.rank(pct=True), 4, labels=False)
        means, top = [], None
        row = []
        for q in range(4):
            b = d[d.q == q]
            cm = b.groupby("cluster_id").ship.mean()
            if len(cm) < 30:
                row.append(f"Q{q+1}:UNDERPWR")
                continue
            mu, se = cm.mean(), cm.std(ddof=1) / np.sqrt(len(cm))
            means.append(mu)
            top = (mu, mu - 1.96 * se)
            row.append(f"Q{q+1}:{mu:+.3f}[{mu-1.96*se:+.3f},{mu+1.96*se:+.3f}](n{len(cm)})")
        mono = all(means[k] <= means[k + 1] + 1e-12 for k in range(len(means) - 1))
        top_ok = top is not None and top[0] > 0 and top[1] > 0
        verdicts += [mono, top_ok]
        emit(f"  {era}: " + " ".join(row))
        emit(f"          monotone={'Y' if mono else 'N'} | topQ>0 CI clear={'Y' if top_ok else 'N'}")
    fails = []
    for m in sorted(R.month.unique()):
        f_ = R[R.month != m].dropna(subset=["bwx"])
        if rho_rank(f_.bwx, f_.ship) <= 0:
            fails.append(m)
    emit(f"  period gate: {14-len(fails)}/14 folds"
         + (f" | FAILING {fails}" if fails else ""))
    emit(f"  JOB 3 BAR: {'PASS' if all(verdicts) and not fails else 'FAIL'}")

    with open(ROOT / "docs/PREREG-htf-ma.md", "a") as fh:
        fh.write("\n## Round 3 — RESULT (run 2026-08-08)\n\n```\n"
                 + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/PREREG-htf-ma.md")


if __name__ == "__main__":
    main()
