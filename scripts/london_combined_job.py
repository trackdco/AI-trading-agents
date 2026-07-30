#!/usr/bin/env python3
"""COMBINED NY+LONDON overnight job — preflight + stages 0,2,3,4. FIT ONLY.

Stages 1 (determinism) and 5 (pre-registration) are already complete and committed:
  docs/LONDON-AUDIT-DETERMINISM.md   docs/LONDON-PREREGISTRATION.md
They are not re-run here; the driver references them.

SEALED SPAN NEVER TOUCHED. fit_only() refuses any path containing "holdout" and raises on any
row outside 2025/2026. No override.

NY BOOK: output/funded_book_lucid_fit.parquet — the VERIFIED canon (920 trades, 230 days,
+$90,015, worst day -$762, maxDD $1,603, 13/13 green). `pl` is already sized by the real spine
(lucid base $150 static -> tiers $75/150/225/300, soft de-risk to half at -$280 realized, ramp
under $1k buffer, elite 2.0x capped 1/day), and `risk_d` is the per-trade dollar risk that spine
allocated. So this job CONSUMES the spine rather than re-deriving it — the earlier attempt
re-derived it from SAFETY-SPINE and got base $300, doubling every tier and manufacturing 14
phantom budget breaches against 0 real ones.

    python -m scripts.london_combined_job --stage preflight|0|2|3|4
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
from src.canon.scorer import london_checks  # noqa: E402

DOCS = ROOT / "docs"
ET = "America/New_York"
ERAS = ["2025", "2026"]
BUDGET = 800.0
N_PATHS = 2000
START, TRAIL, LOCK_AT, PAYOUT_AT, PAYOUT = 50_000.0, 2_000.0, 52_000.0, 54_000.0, 2_000.0
SEED = 20260730
ELIG_DAYS, ELIG_MIN = 5, 100.0   # ANGUS: 5 trading days of +$100 before a payout
RETAIN = 4_000.0                  # lucid optimum from docs/PAYOUT-BUFFER-SWEEP.md
EXPECT = dict(trades=920, days=230, net=90015, worst=-762, dd=1603, green=13)

FLOORS = [7.0, 9.5, 12.0]
LIFETIMES = [15.0, 22.0, math.inf]
CAPS = {"1/session": 1, "2/session": 2, "uncapped": 999}
# shrinkage curve anchors (measured, docs/LONDON-AUDIT-STAGE3-selection-null.md)
A_N, A_S, B_N, B_S = 4.0, -0.014, 29161.0, 1.138


def shrink(n: float) -> float:
    if n <= A_N:
        return A_S
    return A_S + (B_S - A_S) * (math.log(n) - math.log(A_N)) / (math.log(B_N) - math.log(A_N))


def fit_only(p: Path) -> pd.DataFrame:
    if "holdout" in str(p).lower():
        raise SystemExit(f"SEALED SPAN REFUSED: {p}")
    d = pd.read_parquet(p)
    yrs = sorted(set(pd.to_datetime(d.day).dt.year))
    if set(yrs) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: {yrs} in {p.name}")
    return d


def ny() -> pd.DataFrame:
    b = fit_only(ROOT / "output/funded_book_lucid_fit.parquet").copy()
    b["fill_ts"] = pd.to_datetime(b.ts, format="mixed", utc=True).dt.tz_convert(ET)
    b["session"] = "ny"
    b["risk"] = b.risk_d.astype(float)
    b["pnl"] = b.pl.astype(float)
    return b.sort_values(["day", "fill_ts"], kind="mergesort").reset_index(drop=True)


def lon_pop() -> pd.DataFrame:
    F = fit_only(ROOT / "output/l3_features_london_fit.parquet")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True).dt.tz_convert(ET)
    F["exit_ts"] = pd.to_datetime(F["exit"], format="mixed", utc=True).dt.tz_convert(ET)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    L1 = fit_only(ROOT / "output/l1_fills_london_fit.parquet")
    F = F.merge(L1[["ts", "max_away_before_fill"]].drop_duplicates("ts"), on="ts", how="left")
    F["max_away_before_fill"] = F.max_away_before_fill.fillna(0.0)
    return F


def lon_book(P: pd.DataFrame, floor=9.5, lifetime=math.inf, cap=999) -> pd.DataFrame:
    Q = P[(P.risk >= floor) & (P.max_away_before_fill < lifetime)]
    pol = L4Policy(threshold={"london": 1.0}, escalation_threshold={"london": 1.0},
                   cap_per_session=cap, day_stop_dollars=400.0)
    b = select(Q.assign(score=Q.wall), pol)
    t = b[b.taken].copy()
    t["risk"] = t.risk.astype(float) * 20.0      # 1 NQ lot dollar risk
    t["pnl"] = t.dollars.astype(float)
    return t.reset_index(drop=True)


def maxdd(s: pd.Series) -> float:
    eq = s.cumsum()
    return float((eq.cummax() - eq).max()) if len(eq) else 0.0


def write(name: str, body: str) -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / name).write_text(body)
    print(f"\nwrote docs/{name} ({len(body):,} chars)")


# ------------------------------------------------------------------ PREFLIGHT
def preflight(strict=True) -> pd.DataFrame:
    N = ny()
    d = N.groupby("day").pnl.sum()
    mo = N.groupby("month").pnl.sum()
    got = dict(trades=len(N), days=N.day.nunique(), net=round(N.pnl.sum()),
               worst=round(d.min()), dd=round(maxdd(d)), green=int((mo > 0).sum()))
    print("PREFLIGHT NY-alone (lucid, fit)")
    ok = True
    for k, v in EXPECT.items():
        good = got[k] == v
        ok &= good
        print(f"  {k:>7}: {got[k]:>8}  expected {v:>8}  {'OK' if good else 'MISMATCH'}")
    if not ok and strict:
        raise SystemExit("PREFLIGHT FAILED — wrong NY book loaded; nothing downstream is valid")
    print("  -> PREFLIGHT PASS" if ok else "  -> PREFLIGHT FAIL")
    return N


# ------------------------------------------------------------------ STAGE 0
def stage0() -> None:
    P = lon_pop()
    cells = [(f, lt, cl, c) for f in FLOORS for lt in LIFETIMES for cl, c in CAPS.items()]
    N_NOM = len(cells)
    # EFFECTIVE breadth: cells are highly redundant (nested filters of one population), so the
    # nominal count overstates how many independent questions were asked. Estimate via the
    # eigenvalue spectrum of the cell-outcome correlation matrix: the number of components
    # needed for 95% of variance is the effective number of independent tests.
    series, labels = [], []
    for f, lt, cl, c in cells:
        t = lon_book(P, f, lt, c)
        s = t.groupby("day").pnl.sum()
        series.append(s)
        labels.append((f, lt, cl))
    M = pd.concat(series, axis=1).fillna(0.0)
    C = np.corrcoef(M.values.T)
    ev = np.sort(np.linalg.eigvalsh(np.nan_to_num(C, nan=0.0)))[::-1]
    ev = ev[ev > 0]
    N_EFF = int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.95) + 1)
    sh_nom, sh_eff = shrink(N_NOM), shrink(N_EFF)

    L = ["# Combined job — Stage 0: joint risk floor x order lifetime x cap\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n**Grid declared upfront: {len(FLOORS)} floors x {len(LIFETIMES)} lifetimes x "
         f"{len(CAPS)} caps = {N_NOM} cells.**\n",
         f"\n**Effective independent tests: {N_EFF}** (components for 95% of variance in the "
         f"cell-outcome correlation matrix; top eigenvalue {ev[0]:.1f} of {len(ev)}). The cells "
         f"are nested filters of one population, so they are near-duplicates — the nominal count "
         f"badly overstates how many independent questions were asked.\n",
         f"\n| charge | nominal N={N_NOM} | effective N={N_EFF} |\n|---|---|---|\n"
         f"| shrinkage | {sh_nom:+.3f} R | **{sh_eff:+.3f} R** |\n",
         "\nBoth are reported; the effective charge is the defensible one.\n"]

    rows = []
    for (f, lt, cl), s in zip(labels, series):
        t = lon_book(P, f, lt, CAPS[cl])
        r = {"floor": f, "lifetime": "window-end" if lt == math.inf else f"{lt:g}pt", "cap": cl}
        for e in ERAS:
            g = t[t.era == e]
            r[f"n{e}"] = len(g)
            r[f"net{e}"] = g.pnl.sum()
            r[f"R{e}"] = g.R.mean() if len(g) else np.nan
            r[f"adj{e}"] = (g.R.mean() - sh_eff) if len(g) else np.nan
        rows.append(r)
    L.append("\n## The grid — per era, 1 NQ lot, adjusted at the EFFECTIVE charge\n\n"
             "| floor | lifetime | cap | 2025 n/net/adjR | 2026 n/net/adjR | both adj>0 |\n"
             "|---|---|---|---|---|---|\n")
    for r in rows:
        both = (r["adj2025"] > 0) and (r["adj2026"] > 0)
        L.append(f"| {r['floor']:g} | {r['lifetime']} | {r['cap']} | "
                 f"{r['n2025']}/${r['net2025']:+,.0f}/{r['adj2025']:+.3f} | "
                 f"{r['n2026']}/${r['net2026']:+,.0f}/{r['adj2026']:+.3f} | "
                 f"{'YES' if both else 'no'} |\n")

    # Q1: does window-end x uncapped hold at floor 9.5?
    inc = [r for r in rows if r["floor"] == 9.5 and r["lifetime"] == "window-end"
           and r["cap"] == "uncapped"][0]
    at95 = [r for r in rows if r["floor"] == 9.5]
    best95 = max(at95, key=lambda r: r["net2025"] + r["net2026"])
    L.append(f"\n## Q1 — does window-end x uncapped hold at floor 9.5?\n\n"
             f"Incumbent cell: n={inc['n2025'] + inc['n2026']}, net "
             f"${inc['net2025'] + inc['net2026']:+,.0f}, adjusted R "
             f"{inc['adj2025']:+.3f}/{inc['adj2026']:+.3f}.\n\n"
             f"Best cell at floor 9.5: lifetime `{best95['lifetime']}` x cap `{best95['cap']}` "
             f"at ${best95['net2025'] + best95['net2026']:+,.0f}.\n")
    holds = (best95["lifetime"] == "window-end" and best95["cap"] == "uncapped")
    L.append(f"\n**{'HOLDS' if holds else 'DOES NOT HOLD'}** — "
             f"{'window-end x uncapped is the best cell at the incumbent floor.' if holds else 'another cell beats it at floor 9.5; the frozen level is not the fit-optimum there.'}\n")

    # Q2: is the floor-5 era crossing an artifact of the capped comparator?
    L.append("\n## Q2 — does the floor era-crossing persist across cap/lifetime settings?\n\n"
             "Floor 5 was rejected on an era crossing (better 2025, worse 2026) measured against "
             "a CAPPED comparator. If the crossing appears at every cap/lifetime it is a property "
             "of the floor; if only under capping it was a comparator artifact.\n\n"
             "| lifetime | cap | floor 7 vs 12: sign(2025 delta) | sign(2026 delta) | crossing |\n"
             "|---|---|---|---|---|\n")
    cross = 0
    tot = 0
    for lt in LIFETIMES:
        ltl = "window-end" if lt == math.inf else f"{lt:g}pt"
        for cl in CAPS:
            a = [r for r in rows if r["floor"] == 7.0 and r["lifetime"] == ltl and r["cap"] == cl][0]
            b = [r for r in rows if r["floor"] == 12.0 and r["lifetime"] == ltl and r["cap"] == cl][0]
            d25 = np.sign(a["R2025"] - b["R2025"])
            d26 = np.sign(a["R2026"] - b["R2026"])
            x = d25 != d26
            cross += bool(x)
            tot += 1
            L.append(f"| {ltl} | {cl} | {d25:+.0f} | {d26:+.0f} | {'YES' if x else 'no'} |\n")
    L.append(f"\n**Crossing present in {cross} of {tot} cap/lifetime settings.** "
             f"{'It is a property of the floor, not the capped comparator — the floor-5 rejection stands on general grounds.' if cross >= tot * 0.6 else 'It is NOT general — the crossing depends on the cap/lifetime setting, so the original rejection rested partly on the capped comparator. Reported; the rejection is not relitigated here per instruction.'}\n")
    write("COMBINED-JOB-STAGE0-joint-grid.md", "".join(L))


# ------------------------------------------------------------------ shared replay
def replay(N: pd.DataFrame, Lo: pd.DataFrame, rule: str, reserve: float = 0.0):
    """In-flight-inclusive shared budget. rule: 'clock' | 'reserve'.
    London may draw at most `reserve` before NY's window opens when rule='reserve'."""
    ev = pd.concat([
        N[["day", "fill_ts", "session", "risk", "pnl"]],
        Lo[["day", "fill_ts", "session", "risk", "pnl"]]], ignore_index=True)
    ev = ev.sort_values(["day", "fill_ts"], kind="mergesort")
    taken, blocked = [], {"ny": 0, "london": 0}
    for _d, g in ev.groupby("day", sort=True):
        realized, lon_used = 0.0, 0.0
        for r in g.itertuples():
            cap_here = BUDGET
            if rule == "reserve" and r.session == "london":
                cap_here = min(BUDGET, reserve)
                if lon_used + r.risk > cap_here:
                    blocked["london"] += 1
                    continue
            if realized + r.risk > BUDGET:
                blocked[r.session] += 1
                continue
            taken.append({"day": r.day, "fill_ts": r.fill_ts, "session": r.session,
                          "risk": r.risk, "pnl": r.pnl})
            if r.session == "london":
                lon_used += r.risk
            if r.pnl < 0:
                realized += -r.pnl
    return pd.DataFrame(taken), blocked


ARMS = {"window-end x uncapped": dict(lifetime=math.inf, cap=999),
        "22pt x 2/session": dict(lifetime=22.0, cap=2)}


# ------------------------------------------------------------------ STAGE 2
def stage2() -> None:
    N = preflight()
    P = lon_pop()
    ny_net = float(N.pnl.sum())
    nd = N.groupby("day").pnl.sum()

    L = ["# Combined job — Stage 2: chronological combined replay, shared $800 budget\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\nNY = the VERIFIED lucid canon: {len(N)} trades, {N.day.nunique()} days, "
         f"**${ny_net:+,.0f}**. `pl` already carries the real spine (base $150 static -> tiers "
         f"$75/150/225/300, soft de-risk to half at -$280, ramp under $1k buffer, elite 2.0x "
         f"capped 1/day); `risk_d` is the dollar risk that spine allocated. This job CONSUMES "
         f"the spine rather than re-deriving it.\n",
         "\nLondon flat 1 NQ lot. Budget rule: `realized losses + new risk <= $800`, "
         "chronological, causal — no ordering uses information from later in the day.\n",
         "\n**Causally implementable rules only.** London fills 03:02-05:54 ET; NY opens 07:45 "
         "ET. Anything requiring foreknowledge of NY's setups is excluded. So: (a) clock order, "
         "(b) a reserved London sub-budget swept $0-$400 in $50 steps.\n"]

    for arm, kw in ARMS.items():
        Lo = lon_book(P, 9.5, **kw)
        L.append(f"\n## Arm: {arm}\n\nLondon standalone: {len(Lo)} trades, "
                 f"${Lo.pnl.sum():+,.0f}\n\n"
                 "| rule | NY blk | LON blk | combined net | vs NY-alone | worst day | maxDD | "
                 "months green |\n|---|---|---|---|---|---|---|---|\n")
        for lab, rule, res in ([("clock order", "clock", 0.0)]
                               + [(f"reserve ${r:.0f}", "reserve", float(r))
                                  for r in range(0, 401, 50)]):
            T, bl = replay(N, Lo, rule, res)
            d = T.groupby("day").pnl.sum()
            mo = T.groupby(T.fill_ts.dt.strftime("%Y-%m")).pnl.sum()
            net = float(T.pnl.sum())
            L.append(f"| {lab} | {bl['ny']} | {bl['london']} | ${net:+,.0f} | "
                     f"**${net - ny_net:+,.0f}** | ${d.min():+,.0f} | ${maxdd(d):,.0f} | "
                     f"{int((mo > 0).sum())}/{len(mo)} |\n")

    # correlation on the CORRECT NY daily series
    Lo = lon_book(P, 9.5, **ARMS["window-end x uncapped"])
    ld = Lo.groupby("day").pnl.sum()
    alld = sorted(set(nd.index) | set(ld.index))
    j = pd.DataFrame({"ny": nd.reindex(alld).fillna(0.0), "lon": ld.reindex(alld).fillna(0.0)})
    both = j.loc[sorted(set(nd.index) & set(ld.index))]
    nl, ll = both.ny < 0, both.lon < 0
    obs, exp = float((nl & ll).mean()), float(nl.mean() * ll.mean())
    L.append(f"\n## Day-level correlation on the CORRECT NY series\n\n"
             f"(the earlier ~0 was measured on the deleted pre-rebuild book)\n\n"
             f"| basis | n days | Pearson | Spearman |\n|---|---|---|---|\n"
             f"| all days either book | {len(j)} | {j.ny.corr(j.lon):+.3f} | "
             f"{j.ny.rank().corr(j.lon.rank()):+.3f} |\n"
             f"| days both traded | {len(both)} | {both.ny.corr(both.lon):+.3f} | "
             f"{both.ny.rank().corr(both.lon.rank()):+.3f} |\n"
             f"\n**Loss-day coincidence** on {len(both)} shared days: NY loses "
             f"{nl.mean() * 100:.1f}%, London {ll.mean() * 100:.1f}%. Observed both-lose "
             f"**{obs * 100:.1f}%** vs independence {exp * 100:.1f}% "
             f"(ratio **{obs / max(exp, 1e-9):.2f}x**).\n")
    write("COMBINED-JOB-STAGE2-replay.md", "".join(L))


# ------------------------------------------------------------------ MC engine
def mc(daymap: dict, keys: list, seed=SEED, block=1, retain=RETAIN) -> dict:
    """CORRECTED payout model. The first attempt withdrew on every touch of $54k, which pinned
    the account $2k above a locked floor permanently and inflated NY-alone P(bust) to 11.8%
    against an expected ~1%. Two fixes, both measured in docs/PAYOUT-BUFFER-SWEEP.md:

      cadence  a withdrawal requires ELIG_DAYS trading days of +$ELIG_MIN or better since the
               last one (ANGUS 2026-07-30). Not "whenever eligible".
      retain   withdraw down to a RETAINED BUFFER, not to $2k. The sweep showed $2k is the
               worst choice available on both profiles (18.4% / 14.3% bust vs ~2% at $4k+):
               retaining only $2k above a locked floor means one bad cluster ends the account.
    """
    rng = np.random.default_rng(seed)
    busts, cycles, payouts = 0, [], []
    K = np.array(keys, dtype=object)
    nblocks = max(1, 252 // block)
    for _ in range(N_PATHS):
        eq, floor, locked, paid, cyc, good = START, START - TRAIL, False, 0.0, 0, 0
        starts = rng.integers(0, max(1, len(K) - block + 1), size=nblocks)
        seq = [K[i + o] for i in starts for o in range(block) if i + o < len(K)]
        for k in seq:
            dpl = 0.0
            for p in daymap[k]:
                eq += p
                dpl += p
            if dpl >= ELIG_MIN:
                good += 1
            if not locked:
                floor = max(floor, eq - TRAIL)
                if floor >= START:
                    floor, locked = START, True
            if eq <= floor:
                busts += 1
                break
            if good >= ELIG_DAYS and eq - floor > retain:
                w = eq - floor - retain
                eq -= w
                paid += w
                cyc += 1
                good = 0
        cycles.append(cyc)
        payouts.append(paid)
    return {"bust": busts / N_PATHS, "cyc": np.array(cycles), "pay": np.array(payouts)}


def _daymap(T: pd.DataFrame) -> tuple:
    dm = {d: g.sort_values("fill_ts", kind="mergesort").pnl.tolist()
          for d, g in T.groupby("day")}
    return dm, sorted(dm)


# ------------------------------------------------------------------ STAGE 3
def stage3() -> None:
    P = lon_pop()
    L = ["# Combined job — Stage 3: London on its own funded account\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         "\nZero contention with NY, but a second set of account rules and its own bust risk: "
         f"own ${BUDGET:,.0f} daily budget, own ${TRAIL:,.0f} trailing EOD drawdown, own "
         f"${PAYOUT_AT - START + START:,.0f} target.\n"]
    L.append("\n| arm | trades | net | worst day | maxDD | P(bust) | payout cycles med | "
             "net payout med |\n|---|---|---|---|---|---|---|---|\n")
    for arm, kw in ARMS.items():
        Lo = lon_book(P, 9.5, **kw)
        d = Lo.groupby("day").pnl.sum()
        dm, keys = _daymap(Lo)
        r = mc(dm, keys)
        L.append(f"| {arm} | {len(Lo)} | ${Lo.pnl.sum():+,.0f} | ${d.min():+,.0f} | "
                 f"${maxdd(d):,.0f} | **{r['bust'] * 100:.1f}%** | "
                 f"{np.median(r['cyc']):.0f} | ${np.median(r['pay']):,.0f} |\n")
    L.append("\nCompare against the best sub-budget allocation in Stage 2: a separate account "
             "buys zero contention at the cost of a second independent bust exposure and a "
             "second account fee. The 1-lot London book's own drawdown is small relative to a "
             "$2k trailing line, so its standalone bust risk is the number that decides it.\n")
    write("COMBINED-JOB-STAGE3-separate-account.md", "".join(L))


# ------------------------------------------------------------------ STAGE 4
def stage4() -> None:
    N = preflight()
    P = lon_pop()
    dmN, kN = _daymap(N.assign(pnl=N.pnl))
    base = mc(dmN, kN)
    L = ["# Combined job — Stage 4: Monte Carlo suite\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n{N_PATHS:,} paths, 252 days, seeded ({SEED}). Day-level bootstrap resampling whole "
         "calendar days with BOTH books' trades in the SAME draw, intraday order preserved. "
         "Resampling the books independently would manufacture diversification and flatter the "
         "combined distribution.\n",
         f"\nFunded rules: start ${START:,.0f}, ${TRAIL:,.0f} trailing EOD DD locking at start "
         f"once equity reaches ${LOCK_AT:,.0f}, full ${PAYOUT:,.0f} payout at ${PAYOUT_AT:,.0f}.\n"]
    sane = 0.005 <= base["bust"] <= 0.04
    L.append(f"\n## Sanity check\n\n**NY-alone P(bust) = {base['bust'] * 100:.1f}%** "
             f"— must land in 0.5%-4%. {'PASS' if sane else 'FAIL'}\n")
    if not sane:
        raise SystemExit(f"SANITY FAILED: NY-alone P(bust) {base['bust'] * 100:.1f}% outside "
                         f"0.5-4%. Wrong book or wrong payout model — no stage-4 number is valid.")
    L.append("\n## Headline\n\n| config | P(bust) | cycles med/p90 | net payout p10/med/p90 |\n"
             "|---|---|---|---|\n")

    def row(lab, r):
        L.append(f"| {lab} | **{r['bust'] * 100:.1f}%** | {np.median(r['cyc']):.0f}/"
                 f"{np.percentile(r['cyc'], 90):.0f} | ${np.percentile(r['pay'], 10):,.0f}/"
                 f"${np.median(r['pay']):,.0f}/${np.percentile(r['pay'], 90):,.0f} |\n")
    row("NY alone", base)
    best = {}
    for arm, kw in ARMS.items():
        Lo = lon_book(P, 9.5, **kw)
        T, _ = replay(N, Lo, "clock")
        dm, k = _daymap(T)
        r = mc(dm, k)
        best[arm] = (Lo, r)
        row(f"NY + London ({arm}, clock)", r)
    for arm, kw in ARMS.items():
        Lo = lon_book(P, 9.5, **kw)
        dm, k = _daymap(Lo)
        row(f"London separate account ({arm})", mc(dm, k))

    # sensitivity 1 — haircut
    L.append("\n## Sensitivity 1 — haircut London's mean R\n\nMargin of safety on an unspent "
             "holdout: at what degradation does London's contribution reach zero?\n\n"
             "| haircut | arm | combined net | vs NY-alone |\n|---|---|---|---|\n")
    ny_net = float(N.pnl.sum())
    for h in (0.0, 0.25, 0.50, 0.75):
        for arm, kw in ARMS.items():
            Lo = lon_book(P, 9.5, **kw)
            Lo = Lo.assign(pnl=Lo.pnl * (1 - h))
            T, _ = replay(N, Lo, "clock")
            net = float(T.pnl.sum())
            L.append(f"| {h * 100:.0f}% | {arm} | ${net:+,.0f} | **${net - ny_net:+,.0f}** |\n")

    # sensitivity 2 — weekly blocks
    L.append("\n## Sensitivity 2 — weekly blocks\n\nDaily blocks assume no week-scale "
             "autocorrelation. Repeat at 5-day blocks.\n\n| config | P(bust) daily | "
             "P(bust) weekly | med payout daily | med payout weekly |\n|---|---|---|---|---|\n")
    wk = mc(dmN, kN, block=5)
    L.append(f"| NY alone | {base['bust'] * 100:.1f}% | {wk['bust'] * 100:.1f}% | "
             f"${np.median(base['pay']):,.0f} | ${np.median(wk['pay']):,.0f} |\n")
    for arm, (Lo, r) in best.items():
        T, _ = replay(N, Lo, "clock")
        dm, k = _daymap(T)
        w = mc(dm, k, block=5)
        L.append(f"| NY+London ({arm}) | {r['bust'] * 100:.1f}% | {w['bust'] * 100:.1f}% | "
                 f"${np.median(r['pay']):,.0f} | ${np.median(w['pay']):,.0f} |\n")

    # sensitivity 3 — scaled600
    p6 = ROOT / "output/funded_book_scaled600_fit.parquet"
    L.append("\n## Sensitivity 3 — second NY profile (scaled600)\n")
    if p6.exists():
        N6 = fit_only(p6).copy()
        N6["fill_ts"] = pd.to_datetime(N6.ts, format="mixed", utc=True).dt.tz_convert(ET)
        N6["session"] = "ny"
        N6["risk"] = N6.risk_d.astype(float)
        N6["pnl"] = N6.pl.astype(float)
        N6 = N6.sort_values(["day", "fill_ts"], kind="mergesort")
        dm6, k6 = _daymap(N6)
        r6 = mc(dm6, k6)
        L.append(f"\nscaled600 NY-alone: {len(N6)} trades, ${N6.pnl.sum():+,.0f}, "
                 f"P(bust) {r6['bust'] * 100:.1f}%, med payout ${np.median(r6['pay']):,.0f}\n\n"
                 "| arm | combined net | vs NY-alone | P(bust) |\n|---|---|---|---|\n")
        for arm, kw in ARMS.items():
            Lo = lon_book(P, 9.5, **kw)
            T, _ = replay(N6, Lo, "clock")
            dm, k = _daymap(T)
            r = mc(dm, k)
            L.append(f"| {arm} | ${T.pnl.sum():+,.0f} | "
                     f"**${T.pnl.sum() - N6.pnl.sum():+,.0f}** | {r['bust'] * 100:.1f}% |\n")
        L.append("\nscaled600's budget scales with buffer, so contention behaves differently — "
                 "a larger NY risk unit crowds London harder under one shared budget.\n")
    else:
        L.append(f"\n**NOT RUN** — {p6.name} absent. Generate with "
                 f"`python -m scripts.funded_book --profile scaled600` and re-run this stage. "
                 f"Reported as not-run rather than silently skipped.\n")
    write("COMBINED-JOB-STAGE4-monte-carlo.md", "".join(L))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["preflight", "0", "2", "3", "4"])
    a = ap.parse_args()
    {"preflight": lambda: preflight(), "0": stage0, "2": stage2, "3": stage3, "4": stage4}[a.stage]()


if __name__ == "__main__":
    main()
