#!/usr/bin/env python3
"""VERDICT — Census B (M2 rejection/continuation). Reads FIT rows only.

Per SPEC §6/§8 + the ANGUS steers (2026-08-07): headline = STRUCTURAL target
before S-past-the-trigger-candle-EXTREME (the actual stated stop rule); the
travel_max_W tail quantiles carry the skew; the persistence null (BR-5) stands
accepted — magnitude and conditioning columns are read ONCE, reported never
filtered, no encoding search. Placebo pair on the reject headline.

    python -m scripts.htf_ma_verdict_b
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars               # noqa: E402
from scripts.htf_ma_verdict_a import wilson                   # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, profile_at_minutes  # noqa: E402

TICK = 0.25
N_DRAWS, N_DAYS_PER_ERA = 100, 50
HEADLINE_S = 20


def cell(d: pd.DataFrame, col: str) -> str:
    cm = d.groupby("cluster_id")[col].mean()
    p, lo, hi = wilson(int(round(cm.sum())), len(cm))
    tag = " UNDERPOWERED" if len(cm) < 30 else ""
    return f"{cm.mean()*100:5.1f}% [{lo*100:4.1f},{hi*100:4.1f}] n={len(cm)}{tag}"


def era_of(day: str) -> str:
    return "H2-2025" if day < "2026-01-01" else "H1-2026"


def light_b(seg_f15, ma_at, hi, lo, idx, lvl_lookup, w_at):
    """Placebo machine: failed attempts vs a line; race = nearest REAL level in
    the away direction before HEADLINE_S ticks past the failing bar's extreme."""
    ev = win = 0
    ma = ma_at
    o, h, l, c = (seg_f15[k].to_numpy() for k in ("open", "high", "low", "close"))
    for side, away in (("below", -1), ("above", 1)):
        for bi in range(len(seg_f15)):
            m = ma[bi]
            if not np.isfinite(m):
                continue
            fail = ((c[bi] < m) and (h[bi] >= m) and (o[bi] < m)) if side == "below" \
                else ((c[bi] > m) and (l[bi] <= m) and (o[bi] > m))
            if not fail:
                continue
            tgt = lvl_lookup(seg_f15.index[bi], c[bi], away)
            if not np.isfinite(tgt):
                continue
            ev += 1
            stop_ref = h[bi] if away < 0 else l[bi]
            j0 = int(np.searchsorted(idx.values, seg_f15.index[bi].to_datetime64()))
            for j in range(j0, len(idx)):
                adv = ((hi[j] - stop_ref) if away < 0 else (stop_ref - lo[j])) / TICK
                if adv >= HEADLINE_S:
                    break
                if away * ((hi[j] if away > 0 else lo[j]) - tgt) >= 0:
                    win += 1
                    break
    return ev, win


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/censusB_fit.parquet")
    F["era"] = F.sess_day.map(era_of)
    R = F[(F.kind == "reject") & (F.target_defined == True)]        # noqa: E712
    B = F[(F.kind == "break") & (F.retraced_ma == True)             # noqa: E712
          & (F.target_defined == True)]                             # noqa: E712
    lines: list[str] = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("CENSUS B — M2 REJECTION/CONTINUATION, fit only, 15m reference")
    emit(f"reject events w/ target: {len(R):,} | break-retest w/ target: {len(B):,} "
         f"| days {F.sess_day.nunique()}")

    emit("\n== HEADLINE: structural target before S past the trigger-candle "
         "extreme (cluster-collapsed, Wilson 95) ==")
    for name, D in (("REJECT", R), ("BREAK-RETEST (retest-referenced)", B)):
        emit(f"[{name}]")
        for S in (10, 20, 40):
            for side in ("below", "above"):
                r25 = cell(D[(D.side == side) & (D.era == "H2-2025")],
                           f"target_before_extreme_{S}")
                r26 = cell(D[(D.side == side) & (D.era == "H1-2026")],
                           f"target_before_extreme_{S}")
                emit(f"  S={S:>2}t {side:<6} {r25}  |  {r26}")

    emit("\n== the skew (travel_max_W quantiles, reject) ==")
    for era in ("H2-2025", "H1-2026"):
        for side in ("below", "above"):
            t = R[(R.era == era) & (R.side == side)].travel_max_W
            emit(f"  {era} {side:<6} p50 {t.median():.2f}W p75 {t.quantile(.75):.2f} "
                 f"p90 {t.quantile(.9):.2f} p95 {t.quantile(.95):.2f} max {t.max():.1f}")

    emit("\n== geometry (reject): target dist / stop dist, W units ==")
    risk_w = np.where(R.side == "below", R.trig_high - R.event_px,
                      R.event_px - R.trig_low) / R.w15
    emit(f"  target p25/50/75: {R.next_level_dist_W.quantile(.25):.2f}/"
         f"{R.next_level_dist_W.median():.2f}/{R.next_level_dist_W.quantile(.75):.2f}W"
         f" | stop p25/50/75: {np.percentile(risk_w,25):.2f}/"
         f"{np.percentile(risk_w,50):.2f}/{np.percentile(risk_w,75):.2f}W")

    emit("\n== magnitude, read ONCE as declared (quartiles vs headline S=20) ==")
    for var in ("pen_bw", "body_atr", "close_dist_bw"):
        for era in ("H2-2025", "H1-2026"):
            d = R[(R.era == era) & R[var].notna()].copy()
            try:
                d["q"] = pd.qcut(d[var], 4, labels=False, duplicates="drop")
            except ValueError:
                continue
            rates = d.groupby("q")[f"target_before_extreme_{HEADLINE_S}"].mean()
            emit(f"  {var:<14} {era}: Q1..Q4 " +
                 " ".join(f"{v*100:.0f}%" for v in rates))

    emit("\n== conditioning columns, REPORTED never filtered (headline S=20) ==")
    for var, cuts in (("confluence_count", [0, 1, 2, 99]),
                      ("mtf_reject_count", [0, 1, 2, 3, 99])):
        for era in ("H2-2025", "H1-2026"):
            d = R[R.era == era]
            parts = []
            for k in range(len(cuts) - 1):
                m = (d[var] >= cuts[k]) & (d[var] < cuts[k + 1])
                if m.sum() >= 15:
                    parts.append(f"{cuts[k]}{'+' if cuts[k+1]==99 else ''}:"
                                 f"{d[m][f'target_before_extreme_{HEADLINE_S}'].mean()*100:.0f}%"
                                 f"(n{m.sum()})")
            emit(f"  {var:<18} {era}: " + " ".join(parts))
    for era in ("H2-2025", "H1-2026"):
        d = R[R.era == era]
        a = d[d.admissible_snapshot == True]                        # noqa: E712
        b = d[d.admissible_snapshot == False]                       # noqa: E712
        emit(f"  admissible_snapshot {era}: ADMISSIBLE "
             f"{a[f'target_before_extreme_{HEADLINE_S}'].mean()*100:.0f}%(n{len(a)}) vs "
             f"BLOCKED {b[f'target_before_extreme_{HEADLINE_S}'].mean()*100:.0f}%(n{len(b)})")

    emit("\n== sessions (reject, S=20, eras pooled; reported never filtered) ==")
    for s in ("asia", "london", "ny_pre", "ny_rth_am", "ny_pm"):
        for side in ("below", "above"):
            d = R[(R.session == s) & (R.side == side)]
            if len(d) >= 15:
                emit(f"  {s:<10} {side:<6} {cell(d, f'target_before_extreme_{HEADLINE_S}')}")

    # ---- placebos on the reject headline ---------------------------------
    emit(f"\n== placebos (headline: target before {HEADLINE_S}t past extreme) ==")
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    rng = np.random.default_rng(31)
    for era, lo_d, hi_d in (("H2-2025", "2025-06-01", "2025-12-31"),
                            ("H1-2026", "2026-01-01", "2026-07-31")):
        days = sorted(d for d in F.sess_day.unique() if lo_d <= d <= hi_d)
        samp = list(rng.choice(days, size=min(N_DAYS_PER_ERA, len(days)), replace=False))
        prep = {}
        for d in samp:
            t0 = pd.Timestamp(f"{d} 18:00", tz=NY)
            hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) &
                        (bars.index < t0 + pd.Timedelta(hours=23))]
            ma, w = bb_ma_asof(hist, 15)
            f15 = hist.resample("15min", label="right", closed="left").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
            f15 = f15[f15.index > t0]
            ma_at = ma.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
            seg = hist[hist.index >= t0]
            prof = profile_at_minutes(hist, [t - pd.Timedelta(minutes=1)
                                             for t in f15.index])
            def mk_lookup(prof=prof):
                def lookup(t, px, away):
                    p = prof.loc[t - pd.Timedelta(minutes=1)]
                    cands = [v for v in (p.poc, p.vah, p.val)
                             if np.isfinite(v) and away * (v - px) > 0]
                    return min(cands, key=lambda v: abs(v - px)) if cands else np.nan
                return lookup
            prep[d] = (f15, ma_at, seg.high.to_numpy(), seg.low.to_numpy(),
                       seg.index, mk_lookup(),
                       np.abs(seg.close.to_numpy() - ma.loc[seg.index].to_numpy()))
        ev = win = 0
        for d in samp:
            f15, ma_at, hi_, lo_, idx, lk, _ = prep[d]
            e, k = light_b(f15, ma_at, hi_, lo_, idx, lk, None)
            ev += e; win += k
        real = win / ev if ev else np.nan
        draws = []
        for _ in range(N_DRAWS):
            ep = kp = 0
            for d in samp:
                f15, ma_at, hi_, lo_, idx, lk, dist = prep[d]
                off = rng.choice(dist[np.isfinite(dist)]) * rng.choice([-1, 1])
                e, k = light_b(f15, ma_at + off, hi_, lo_, idx, lk, None)
                ep += e; kp += k
            draws.append(kp / ep if ep else np.nan)
        draws = np.array([x for x in draws if np.isfinite(x)])
        pct = (draws < real).mean() * 100
        emit(f"  {era}: real {real*100:.1f}% (events {ev}) | placebo mean "
             f"{draws.mean()*100:.1f}% p95 {np.percentile(draws,95)*100:.1f}% "
             f"| real at {pct:.0f}th pct")

    with open(ROOT / "docs/VERDICT-htf-ma-census.md", "a") as fh:
        fh.write("\n## Census B — M2 REJECTION/CONTINUATION (run 2026-08-07, "
                 "fit only, 15m reference)\n\n```\n" + "\n".join(lines) + "\n```\n")
    print("\nappended -> docs/VERDICT-htf-ma-census.md")


if __name__ == "__main__":
    main()
