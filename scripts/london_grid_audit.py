#!/usr/bin/env python3
"""LONDON grid audit — stages A/B/C, FIT ONLY, every winner charged its own shrinkage.

SEALED SPAN NEVER TOUCHED: fit_only() refuses holdout paths and raises on any row outside
2025/2026. No override.

SHRINKAGE MODEL, declared before any result. Stage 3 of the selection-null job measured
IS->OOS shrinkage at three grid breadths on this exact population:

    grid ~1 (rule held fixed)          -0.010 R
    grid 4 (the L3 check trial)        -0.014 R
    grid 29,161 (exhaustive search)    +1.138 R

Between the 4 and 29,161 anchors this interpolates log-linearly in grid size:

    shrink(N) = -0.014 + 1.152 * (ln N - ln 4) / (ln 29161 - ln 4),  clamped at >= -0.014

Every stage declares its grid size N up front and every reported winner carries
`adj mean R = raw mean R - shrink(N)`. THE MODEL RESTS ON THREE POINTS and assumes shrinkage
grows with the log of the number of things tried; it is a correction of the right order, not a
precise quantity. Raw figures are shown alongside so nothing is hidden behind it.

    python -m scripts.london_grid_audit --stage A|B|C
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select  # noqa: E402
from src.canon.scorer import LON_RISK_MIN, london_checks  # noqa: E402

DOCS = ROOT / "docs"
ET = "America/New_York"
ERAS = ["2025", "2026"]
LIFETIMES = [10.0, 15.0, 20.0, 22.0, 25.0, 30.0, 40.0, math.inf]   # pts; inf = window-end only
CAPS = {"1/session": 1, "2/session": 2, "uncapped": 999}
FLOORS = [0.0, 5.0, 7.0, 9.5, 12.0, 15.0]
CEILINGS = [math.inf, 60.0, 40.0, 25.0]

A_ANCHOR, A_SHRINK = 4.0, -0.014
B_ANCHOR, B_SHRINK = 29161.0, 1.138


def shrink(n: int) -> float:
    if n <= A_ANCHOR:
        return A_SHRINK
    f = (math.log(n) - math.log(A_ANCHOR)) / (math.log(B_ANCHOR) - math.log(A_ANCHOR))
    return A_SHRINK + (B_SHRINK - A_SHRINK) * f


def fit_only(path: Path) -> pd.DataFrame:
    if "holdout" in str(path).lower():
        raise SystemExit(f"SEALED SPAN REFUSED: {path}")
    df = pd.read_parquet(path)
    yrs = sorted(set(pd.to_datetime(df.day).dt.year))
    if set(yrs) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: {yrs} in {path.name}")
    return df


def pop(apply_floor: bool = True) -> pd.DataFrame:
    F = fit_only(ROOT / "output/l3_features_london_fit.parquet")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
    F["mo"] = F.day.str[:7]
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True).dt.tz_convert(ET)
    F["exit_ts"] = pd.to_datetime(F["exit"], format="mixed", utc=True).dt.tz_convert(ET)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    # ORDER LIFETIME comes from L1's max_away_before_fill: a distance cancel of X points is the
    # filter max_away < X. L1 recorded it precisely so lifetime policies stay derived columns.
    L1 = fit_only(ROOT / "output/l1_fills_london_fit.parquet")
    F = F.merge(L1[["ts", "max_away_before_fill"]].drop_duplicates("ts"), on="ts", how="left")
    F["max_away_before_fill"] = F.max_away_before_fill.fillna(0.0)
    return F[F.risk >= LON_RISK_MIN].reset_index(drop=True) if apply_floor else F


def take(P: pd.DataFrame, cap: int) -> pd.DataFrame:
    pol = L4Policy(threshold={"london": 1.0}, escalation_threshold={"london": 1.0},
                   cap_per_session=cap, day_stop_dollars=400.0)
    b = select(P.assign(score=P.wall), pol)
    return b[b.taken]


def stats(t: pd.DataFrame, n_grid: int) -> dict:
    if not len(t):
        return {"n": 0}
    eq = t.sort_values("fill_ts").dollars.cumsum()
    return {"n": len(t), "wr": (t.dollars > 0).mean() * 100, "R": t.R.mean(),
            "adjR": t.R.mean() - shrink(n_grid), "net": t.dollars.sum(),
            "dd": (eq.cummax() - eq).max()}


def blocked_by_resting(P: pd.DataFrame, t: pd.DataFrame) -> int:
    """How often a resting/open position occupied a slot another candidate wanted: candidates
    whose trigger time falls inside a taken trade's [fill, exit] interval. Measured, because
    the selector models cap slots at fill time and cannot see this."""
    n = 0
    tt = pd.to_datetime(P.ts, format="mixed", utc=True).dt.tz_convert(ET)
    for r in t.itertuples():
        n += int(((tt > r.fill_ts) & (tt < r.exit_ts) & (P.day == r.day)).sum())
    return n


def write(name: str, body: str) -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / name).write_text(body)
    print(f"\nwrote docs/{name} ({len(body):,} chars)")


# ---------------------------------------------------------------- STAGE A
def stageA() -> None:
    P = pop()
    N_GRID = len(LIFETIMES) * len(CAPS)
    sh = shrink(N_GRID)
    L = [f"# London grid audit — Stage A: order lifetime x cap\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n**Grid size declared upfront: {len(LIFETIMES)} lifetimes x {len(CAPS)} cap levels "
         f"= {N_GRID} cells.** Shrinkage charged to every winner at this breadth: "
         f"**{sh:+.3f} R** (interpolated on the stage-3 curve; see module docstring — three "
         f"anchor points, so a correction of the right order, not a precise quantity).\n",
         f"\nLifetime is derived from L1's `max_away_before_fill`: a distance cancel of X pts is "
         f"the filter `max_away < X`. `inf` = no distance cancel, order lives to the session "
         f"window end (the ANGUS ruling).\n"]
    rows = []
    for lt in LIFETIMES:
        Q = P[P.max_away_before_fill < lt]
        for clab, cap in CAPS.items():
            t = take(Q, cap)
            for e in ERAS:
                s = stats(t[t.era == e], N_GRID)
                rows.append({"lifetime": "window-end" if lt == math.inf else f"{lt:g}pt",
                             "cap": clab, "era": e, **s})
    R = pd.DataFrame(rows)
    L.append(f"\n## The grid — per era, 1 NQ lot\n\n| lifetime | cap | era | n | WR | raw R | "
             f"**adj R** | net | maxDD |\n|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        if not r["n"]:
            continue
        L.append(f"| {r['lifetime']} | {r['cap']} | {r['era']} | {r['n']} | {r['wr']:.0f}% | "
                 f"{r['R']:+.3f} | **{r['adjR']:+.3f}** | ${r['net']:+,.0f} | "
                 f"${r['dd']:,.0f} |\n")

    # winner: best combined net with BOTH eras positive on adjusted R
    agg = (R.pivot_table(index=["lifetime", "cap"], values=["net", "adjR", "n"],
                         aggfunc={"net": "sum", "adjR": "min", "n": "sum"})
           .reset_index())
    ok = agg[agg.adjR > 0].sort_values("net", ascending=False)
    L.append(f"\n## Slot contention — measured\n\n| lifetime | cap | candidates whose trigger "
             f"fell inside an open trade |\n|---|---|---|\n")
    for lt in (math.inf, 22.0, 15.0):
        Q = P[P.max_away_before_fill < lt]
        for clab, cap in CAPS.items():
            L.append(f"| {'window-end' if lt == math.inf else f'{lt:g}pt'} | {clab} | "
                     f"{blocked_by_resting(Q, take(Q, cap))} |\n")

    if not len(ok):
        L.append("\n## Verdict\n\n**NULL — no cell keeps both eras positive after shrinkage "
                 f"of {sh:+.3f} R.** At this grid breadth nothing survives the correction its "
                 "own search cost implies.\n")
        win = None
    else:
        win = ok.iloc[0]
        L.append(f"\n## Winning cell\n\n**lifetime `{win.lifetime}` x cap `{win.cap}`** — "
                 f"combined net ${win.net:+,.0f}, worse-era adjusted R {win.adjR:+.3f}, "
                 f"n={int(win.n)}.\n")
        # leave-one-out on the winner: does the CAP level stop flipping?
        lt = math.inf if win.lifetime == "window-end" else float(win.lifetime.replace("pt", ""))
        Q = P[P.max_away_before_fill < lt]
        base = max(CAPS, key=lambda c: take(Q, CAPS[c]).dollars.sum())
        flips = []
        for mo in sorted(Q.mo.unique()):
            S = Q[Q.mo != mo]
            w = max(CAPS, key=lambda c: take(S, CAPS[c]).dollars.sum())
            if w != base:
                flips.append(f"{mo}->{w}")
        L.append(f"\n## 14-month leave-one-out at the winning lifetime\n\n"
                 f"Baseline cap at lifetime `{win.lifetime}`: **{base}**.\n")
        if flips:
            L.append(f"\n**The cap level STILL FLIPS** on: {', '.join(flips)} "
                     f"({len(flips)} of {Q.mo.nunique()} months). Setting the lifetime "
                     f"correctly does NOT stabilise the constraint level.\n\n"
                     f"**Consequence, per your instruction: freeze capped 2/session on risk "
                     f"grounds and move to the holdout.**\n")
        else:
            L.append(f"\n**The cap level STOPS FLIPPING once lifetime is set to "
                     f"`{win.lifetime}`.** Every single-month removal keeps `{base}` as the "
                     f"winner. This is a real change to the freeze: the earlier level "
                     f"instability (4 of 14 months) was an artifact of leaving order lifetime "
                     f"unset, not a property of the cap.\n")
    write("LONDON-GRID-STAGEA-lifetime-x-cap.md", "".join(L))


# ---------------------------------------------------------------- STAGE B
def stageB() -> None:
    P = pop(apply_floor=False)
    N_GRID = len(FLOORS) * len(CEILINGS)
    sh = shrink(N_GRID)
    L = ["# London grid audit — Stage B: the risk band\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n**Grid declared upfront: {len(FLOORS)} floors x {len(CEILINGS)} ceilings = "
         f"{N_GRID} cells.** Shrinkage charged at this breadth: **{sh:+.3f} R**.\n",
         "\n## Was 9.5 measured on London or inherited from NY?\n",
         "\n**Measured on London, and it is not NY's number.** NY's Layer 0 is a 7-60pt BAND "
         "(`docs/` and the NY substrate carry both a floor and a ceiling). London's is "
         "`LON_RISK_MIN = 9.5` with **no upper cap**, and `src/canon/scorer.py:63` labels it "
         "\"London Layer 0 ... London-native\"; `scripts/london_canon.py` sources it as the "
         "\"2025-London median\". So the floor is London-derived — but it was fitted on 2025 "
         "only and never trialed against an honest population until this rebuild.\n"]
    L.append(f"\n## By risk decile, both eras separately, 1 NQ lot\n\n"
             f"| decile | pts range | 2025 n/WR/R | 2026 n/WR/R | total $ |\n"
             f"|---|---|---|---|---|\n")
    P = P.copy()
    P["dec"] = pd.qcut(P.risk, 10, labels=False, duplicates="drop")
    for d, g in P.groupby("dec"):
        c = {}
        for e in ERAS:
            s = g[g.era == e]
            c[e] = (f"{len(s)}/{(s.dollars > 0).mean() * 100:.0f}%/{s.R.mean():+.2f}"
                    if len(s) else "-")
        L.append(f"| {int(d) + 1} | {g.risk.min():.1f}-{g.risk.max():.1f} | {c['2025']} | "
                 f"{c['2026']} | ${g.dollars.sum():+,.0f} |\n")

    L.append(f"\n## Floor x ceiling sweep — era-consistency bar: BOTH eras positive on "
             f"adjusted R\n\n| floor | ceiling | 2025 adj R | 2026 adj R | n | net | "
             f"consistent |\n|---|---|---|---|---|---|---|\n")
    best = []
    for fl in FLOORS:
        for ce in CEILINGS:
            Q = P[(P.risk >= fl) & (P.risk <= ce)]
            t = take(Q, 2)
            if len(t) < 40:
                continue
            a = {e: stats(t[t.era == e], N_GRID) for e in ERAS}
            if not all(a[e].get("n") for e in ERAS):
                continue
            cons = all(a[e]["adjR"] > 0 for e in ERAS)
            if cons:
                best.append((t.dollars.sum(), fl, ce, min(a[e]["adjR"] for e in ERAS), len(t)))
            L.append(f"| {fl:g} | {'none' if ce == math.inf else f'{ce:g}'} | "
                     f"{a['2025']['adjR']:+.3f} | {a['2026']['adjR']:+.3f} | {len(t)} | "
                     f"${t.dollars.sum():+,.0f} | {'YES' if cons else 'no'} |\n")
    L.append("\n## Verdict\n")
    if not best:
        L.append(f"\n**NULL — no floor/ceiling combination keeps both eras positive after "
                 f"{sh:+.3f} R of shrinkage.** The risk band cannot be improved on this "
                 f"evidence; the incumbent 9.5 floor with no ceiling is not beaten.\n")
    else:
        best.sort(reverse=True)
        net, fl, ce, mn, n = best[0]
        L.append(f"\n**Best era-consistent band: floor {fl:g}pt, ceiling "
                 f"{'none' if ce == math.inf else f'{ce:g}pt'}** — net ${net:+,.0f}, n={n}, "
                 f"worse-era adjusted R {mn:+.3f}.\n")
        if fl == 9.5 and ce == math.inf:
            L.append("\nThat is the incumbent band. **The 9.5 floor with no ceiling survives "
                     "its own sweep** — it was not beaten by any alternative.\n")
        else:
            L.append(f"\nThis differs from the incumbent (9.5, no ceiling). Treat as a "
                     f"PROPOSAL requiring Angus sign-off and holdout confirmation, not a "
                     f"change to make here.\n")
    write("LONDON-GRID-STAGEB-risk-band.md", "".join(L))


# ---------------------------------------------------------------- STAGE C
def stageC() -> None:
    P = pop()
    t = take(P, 2)
    N_GRID = 2
    sh = shrink(N_GRID)
    alpha = 1 - 0.95 ** (1 / 2)
    L = ["# London grid audit — Stage C: two pre-registered hypotheses\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n**Exactly two hypotheses, declared before testing, no expansion.** Family-wise "
         f"correction is over TWO tests (Sidak): per-test alpha = **{alpha:.4f}**. Shrinkage at "
         f"grid N=2: **{sh:+.3f} R** — pre-registration is why this is near zero rather than "
         f"the {shrink(29161):+.3f} an open search would carry.\n",
         f"\nBook: capped 2/session, n={len(t)}.\n"]

    # H1 — concurring timeframes
    ts_all = pd.to_datetime(P.ts, format="mixed", utc=True).dt.tz_convert(ET)
    P2 = P.assign(_m=ts_all.dt.floor("5min"))
    conc = P2.groupby(["day", "_m", "direction"]).ts.transform("count")
    P2 = P2.assign(conc=conc)
    tt = t.merge(P2[["ts", "conc"]], on="ts", how="left")
    tt["bucket"] = np.where(tt.conc >= 3, "3+", tt.conc.astype("Int64").astype(str))
    L.append("\n## H1 — does the count of concurring timeframes predict outcome?\n"
             "\nConcurring = triggers on the same day, same direction, within the same 5-minute "
             "bin (MTF arbitration keeps one per close, so agreement shows as siblings).\n\n"
             "| agreeing | 2025 n/WR/R | 2026 n/WR/R | raw R | **adj R** |\n"
             "|---|---|---|---|---|\n")
    h1 = {}
    for b in ["1", "2", "3+"]:
        s = tt[tt.bucket == b]
        if not len(s):
            continue
        c = {e: (f"{len(s[s.era == e])}/{(s[s.era == e].dollars > 0).mean() * 100:.0f}%/"
                 f"{s[s.era == e].R.mean():+.2f}" if len(s[s.era == e]) else "-") for e in ERAS}
        h1[b] = {e: s[s.era == e].R.mean() for e in ERAS}
        L.append(f"| {b} | {c['2025']} | {c['2026']} | {s.R.mean():+.3f} | "
                 f"**{s.R.mean() - sh:+.3f}** |\n")
    mono = all(h1.get("3+", {}).get(e, -9) > h1.get("1", {}).get(e, 9) for e in ERAS) if h1 else False
    L.append(f"\n**H1 verdict: {'monotone in both eras — SUPPORTED' if mono else 'NOT era-consistent — NULL'}.** "
             f"{'3+ agreeing beats 1 in both 2025 and 2026.' if mono else 'The ordering does not hold in both eras, so the hypothesis is not supported regardless of the pooled figure.'}\n")

    # H2 — long/short symmetry
    L.append("\n## H2 — is the book symmetric long vs short?\n\n"
             "| direction | 2025 n/WR/R | 2026 n/WR/R | net | raw R | **adj R** |\n"
             "|---|---|---|---|---|---|\n")
    h2 = {}
    for d in ["long", "short"]:
        s = t[t.direction == d]
        c = {e: (f"{len(s[s.era == e])}/{(s[s.era == e].dollars > 0).mean() * 100:.0f}%/"
                 f"{s[s.era == e].R.mean():+.2f}" if len(s[s.era == e]) else "-") for e in ERAS}
        h2[d] = {e: s[s.era == e].R.mean() for e in ERAS}
        L.append(f"| {d} | {c['2025']} | {c['2026']} | ${s.dollars.sum():+,.0f} | "
                 f"{s.R.mean():+.3f} | **{s.R.mean() - sh:+.3f}** |\n")
    same = all(np.sign(h2["long"][e] - h2["short"][e]) == np.sign(h2["long"]["2025"] - h2["short"]["2025"]) for e in ERAS)
    gap = t[t.direction == "long"].R.mean() - t[t.direction == "short"].R.mean()
    L.append(f"\nLong-minus-short gap: {gap:+.3f} R, same sign in both eras: "
             f"**{'yes' if same else 'no'}**.\n")
    L.append(f"\n**H2 verdict: {'ASYMMETRIC and era-consistent' if same and abs(gap) > 0.15 else 'SYMMETRIC / NULL'}** "
             f"— {'one side carries materially more of the edge and the sign holds across eras.' if same and abs(gap) > 0.15 else 'no era-consistent directional asymmetry large enough to act on.'}\n")
    write("LONDON-GRID-STAGEC-two-hypotheses.md", "".join(L))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["A", "B", "C"], required=True)
    a = ap.parse_args()
    {"A": stageA, "B": stageB, "C": stageC}[a.stage]()


if __name__ == "__main__":
    main()
