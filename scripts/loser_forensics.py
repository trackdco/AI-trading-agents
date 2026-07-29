#!/usr/bin/env python3
"""Loser forensics (ANGUS 2026-07-26): "id like to see where the flagged loss evens out,
and also look at the orderflow when the trade is in drawdown... i still think we can
prevent a lot of losers from fully losing."

PART A — the cut frontier. Sweep the in-trade cut over horizon h in {3,5,10} min,
mark-depth r_thr, and flow fw_thr, on BOTH books (rr 2.0 and 1.5): net dR of exiting
flagged trades at the +h mark, winners sacrificed, and the HALF-EXIT variant (de-risk 50%
instead of kill). A cell "evens out" when dR >= 0 with the same sign in 2025 AND 2026.

PART B — what the flow says while underwater. For trades in drawdown at h (r_h <= -0.10),
split eventual winners vs losers and table the in-trade flow/book features (canon
intrade_matrix vocabulary): fw_h, adverse-minute fraction, adverse pressing, absorption,
relative volume, book thickness/imbalance shift, wall-behind. Both-years verdicts.

Exit-at-mark approximation: a cut fills at the +h minute close (same convention both
variants). EXPLORATORY: final thresholds must be re-derived with intrade_matrix's own
conventions inside the adoption package (docs/RULING-mechanical-only.md).

    python -m scripts.loser_forensics
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.canon.features import load_depth_day                         # noqa: E402

NY = "America/New_York"
HORIZONS = [3, 5, 10]
R_THRS = [-0.05, -0.11, -0.20, -0.30, -0.45]
FW_THRS = [None, -13.0, -60.0, -150.0]


def paths(tag: str) -> pd.DataFrame:
    out = Path(f"output/forensics_rr{tag}.parquet")
    if out.exists():
        return pd.read_parquet(out)
    X = pd.read_parquet(f"output/mgmt_rr{tag}.parquet")
    fill = pd.to_datetime(X.fill_ts.str.replace("T", " "), utc=True, format="mixed").dt.tz_convert(NY)
    ex = pd.to_datetime(X.exit_ts.str.replace("T", " "), utc=True, format="mixed").dt.tz_convert(NY)
    X["hold_min"] = (ex - fill).dt.total_seconds() / 60
    X["yr"] = X.month.str[:4]
    X["win"] = X.dollars > 0

    bars = pd.read_parquet("data/reference/nq_1m_master.parquet")
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(mi=bt.dt.floor("min"))
    byday = {d: g for d, g in bars.groupby(bt.dt.strftime("%Y-%m-%d"))}
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    daymed = M.groupby("sday").vol.median()
    dep_cache: dict = {}

    rows = []
    for i, t in X.iterrows():
        f0 = fill[i].floor("min")
        day = fill[i].strftime("%Y-%m-%d")
        sgn = 1 if t.direction == "long" else -1
        g = byday.get(day)
        m = M[(M.index > f0) & (M.index <= f0 + pd.Timedelta(minutes=max(HORIZONS)))]
        f: dict = {}
        for h in HORIZONS:
            if t.hold_min <= h:                    # only trades still alive at h
                continue
            b = g[(g.mi >= f0) & (g.mi <= f0 + pd.Timedelta(minutes=h))]
            if not len(b):
                continue
            f[f"r_{h}"] = sgn * (b.close.iloc[-1] - t.entry) / t.risk_pts
            f[f"mae_{h}"] = max(0.0, ((t.entry - b.low.min()) if sgn == 1
                                      else (b.high.max() - t.entry))) / t.risk_pts
            mh = m[m.index <= f0 + pd.Timedelta(minutes=h)]
            if len(mh):
                f[f"fw_{h}"] = sgn * mh.delta.sum()
                f[f"fafrac_{h}"] = (np.sign(mh.delta) != sgn).mean()
                px = mh.vwp
                adverse = (sgn * (px - t.entry)) < 0
                f[f"advpress_{h}"] = sgn * mh.delta[adverse].sum() if adverse.any() else 0.0
                f[f"absorb_{h}"] = float((adverse & (np.sign(mh.delta) == sgn)).sum())
                f[f"relvol_{h}"] = mh.vol.mean() / max(daymed.get(day, np.nan), 1)
        if day not in dep_cache:
            dep_cache[day] = load_depth_day(day)
        dep = dep_cache[day]
        if dep is not None:
            for h in HORIZONS:
                if t.hold_min <= h:
                    continue
                b0 = dep[dep.ts <= f0]
                bh = dep[dep.ts <= f0 + pd.Timedelta(minutes=h)]
                if b0.empty or bh.empty:
                    continue
                s0 = b0[b0.ts == b0.ts.max()]
                sh = bh[bh.ts == bh.ts.max()]
                th0, thh = s0["size"].sum(), sh["size"].sum()
                f[f"dthick_{h}"] = thh - th0
                def imb(s):
                    tb = s[s.side == "bid"]["size"].sum()
                    ta = s[s.side == "ask"]["size"].sum()
                    return sgn * (tb - ta) / max(tb + ta, 1)
                f[f"dimb_{h}"] = imb(sh) - imb(s0)
                behind = sh[sh.price < t.entry] if sgn == 1 else sh[sh.price > t.entry]
                f[f"wallb_{h}"] = behind["size"].max() if len(behind) else 0.0
        rows.append(f)
    F = pd.concat([X.reset_index(drop=True),
                   pd.DataFrame(rows).reset_index(drop=True)], axis=1)
    F.to_parquet(out)
    return F


def part_a(F: pd.DataFrame, tag: str) -> None:
    print(f"\n######## PART A — cut frontier, rr{tag} "
          f"(dR = exit flagged at the +h mark; positive = cut helps) ########")
    print(f"{'h':>3} {'r_thr':>7} {'fw_thr':>8} | {'n_flag':>6} {'lose%':>6} "
          f"{'winsac':>7} | {'dR full':>8} {'25':>6} {'26':>6} | {'dR half':>8} {'EVENS':>6}")
    for h in HORIZONS:
        v = F[F[f"r_{h}"].notna()]
        for rt in R_THRS:
            for ft in FW_THRS:
                flag = v[f"r_{h}"] <= rt
                if ft is not None:
                    flag &= v[f"fw_{h}"].fillna(0) <= ft
                if flag.sum() < 12:
                    continue
                d = (v[f"r_{h}"] - v.r_multiple)[flag]
                dr = d.sum()
                dry = {yr: d[v.yr[flag & (v.yr == yr)].index].sum() for yr in ("2025", "2026")}
                both = np.sign(dry["2025"]) == np.sign(dry["2026"])
                evens = dr >= 0 and both and min(abs(dry["2025"]), abs(dry["2026"])) > 0
                winsac = int((flag & v.win).sum())
                print(f"{h:>3} {rt:>7.2f} {'off' if ft is None else f'{ft:.0f}':>8} | "
                      f"{flag.sum():>6} {(~v.win[flag]).mean()*100:>5.0f}% {winsac:>7} | "
                      f"{dr:>+8.1f} {dry['2025']:>+6.1f} {dry['2026']:>+6.1f} | "
                      f"{dr/2:>+8.1f} {'YES' if evens else '':>6}")


def part_b(F: pd.DataFrame, tag: str) -> None:
    print(f"\n######## PART B — flow while underwater, rr{tag} "
          f"(in DD at h: r_h <= -0.10; eventual winners vs losers) ########")
    for h in HORIZONS:
        v = F[(F[f"r_{h}"].notna()) & (F[f"r_{h}"] <= -0.10)]
        if len(v) < 30:
            continue
        W, L = v[v.win], v[~v.win]
        print(f"\n-- h={h}min: {len(v)} underwater ({len(W)} recover, {len(L)} die; "
              f"recover rate {len(W)/len(v)*100:.0f}%)")
        print(f"{'feature':<14}{'recover p50':>13}{'die p50':>10}{'gap dir 25':>12}{'26':>5}{'SIG':>6}")
        for c in (f"fw_{h}", f"fafrac_{h}", f"advpress_{h}", f"absorb_{h}",
                  f"relvol_{h}", f"mae_{h}", f"dthick_{h}", f"dimb_{h}", f"wallb_{h}"):
            if c not in v or v[c].notna().sum() < 30:
                continue
            oks = []
            for yr in ("2025", "2026"):
                w = W[W.yr == yr][c].dropna()
                l = L[L.yr == yr][c].dropna()
                oks.append("?" if (len(w) < 10 or len(l) < 10) else
                           ("+" if w.median() > l.median() else "-"))
            sig = oks[0] == oks[1] and oks[0] in "+-"
            print(f"{c:<14}{W[c].median():>13.2f}{L[c].median():>10.2f}"
                  f"{oks[0]:>12}{oks[1]:>5}{'YES' if sig else '':>6}")


def main() -> None:
    for tag in ("2_0", "1_5"):
        F = paths(tag)
        part_a(F, tag.replace("_", "."))
        part_b(F, tag.replace("_", "."))


if __name__ == "__main__":
    main()
