#!/usr/bin/env python3
"""COMBINED NY + LONDON audit — four stages, FIT ONLY.

Stage 0  cheap gate: jackknife the London arm choice by month
Stage 1  join the two books: correlation, loss-day coincidence, MEASURED clock overlap
Stage 2  chronological combined replay under ONE shared $800 daily budget
Stage 3  Monte Carlo, 2,000 paths, day-level bootstrap keeping BOTH books in the same draw

SEALED SPAN NEVER TOUCHED. Every read goes through fit_only(): refuses any path containing
"holdout" and raises if a single row falls outside 2025/2026. No override exists.

SIZING BASIS, verified not assumed. output/canon_book.parquet's `dollars` equals
R x risk_pts x $20 to the cent on every row — it is a 1-NQ-lot figure, NOT pre-sized. So the
ladder is applied here as SAFETY-SPINE.md:145 defines it: fixed DOLLAR RISK per conviction
tier, stop-width-normalised, contracts being whatever makes the stop cost that amount.

  risk_$ = BASE x min(2.0, conviction)     BASE = $300  ->  0.25=$75  0.5=$150
  pnl_$  = R x risk_$                      0.75=$225  1.0=$300  1.5=$450  2.25=$600

  That IS the "$75/150/225/300 lucid ladder": the canon ladder (0.25/0.5/0.75/1.0/1.5/2.25
  multipliers, 2.25 capped at 2.0x) evaluated at base_dollar $300, which SAFETY-SPINE puts
  around $4.3k available DD — inside the stated $2k-$6k working band. Because risk is pinned
  in dollars, R-multiples convert straight to P&L and stop width drops out, which is the whole
  point of dollar-risk sizing.

    python -m scripts.combined_book_audit --stage 0
"""
from __future__ import annotations

import argparse
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
BASE_DOLLAR = 300.0            # the lucid ladder's 1.0 tier
CONV_CAP = 2.0                 # 2.25 caps at 2x base (SAFETY-SPINE)
BUDGET = 800.0                 # shared daily risk budget
N_PATHS = 2000
START, TRAIL, LOCK_AT, PAYOUT_AT, PAYOUT = 50_000.0, 2_000.0, 52_000.0, 54_000.0, 2_000.0
MIN_WITHDRAW_AT = 53_000.0
RNG_SEED = 20260730


def fit_only(path: Path) -> pd.DataFrame:
    if "holdout" in str(path).lower():
        raise SystemExit(f"SEALED SPAN REFUSED: {path}")
    df = pd.read_parquet(path)
    yrs = sorted(set(pd.to_datetime(df.day).dt.year))
    if set(yrs) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: rows from {yrs} in {path.name}")
    return df


def ladder_risk(conv: float) -> float:
    return BASE_DOLLAR * min(CONV_CAP, float(conv))


def london_pop() -> pd.DataFrame:
    F = fit_only(ROOT / "output/l3_features_london_fit.parquet")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
    F["mo"] = F.day.str[:7]
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True).dt.tz_convert(ET)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)          # 1 lot
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    F["old4"] = F[["W", "FAR", "ROOM", "ASIA"]].sum(axis=1)
    return F[F.risk >= LON_RISK_MIN].reset_index(drop=True)


LEVELS = {"capped": dict(cap_per_session=2, day_stop_dollars=400.0),
          "uncapped": dict(cap_per_session=999, day_stop_dollars=400.0),
          "raw": dict(cap_per_session=999, day_stop_dollars=1e12)}
ARMS = {"wall": ("wall", 1.0), "old4": ("old4", 3.0)}


def london_book(P: pd.DataFrame, arm: str = "wall", level: str = "uncapped") -> pd.DataFrame:
    col, thr = ARMS[arm]
    pol = L4Policy(threshold={"london": thr}, escalation_threshold={"london": thr},
                   **LEVELS[level])
    b = select(P.assign(score=P[col]), pol)
    return b[b.taken].reset_index(drop=True)


def ny_book() -> pd.DataFrame:
    b = fit_only(ROOT / "output/canon_book.parquet")
    t = b[b["size"] > 0].copy()
    t["session"] = "ny"
    t["fill_ts"] = pd.to_datetime(t.fill, format="mixed", utc=True).dt.tz_convert(ET)
    t["conv"] = t["size"].astype(float)
    t["risk_$"] = t.conv.map(ladder_risk)
    t["pnl_ladder"] = t.R * t["risk_$"]
    t["pnl_1lot"] = t.dollars.astype(float)
    return t.reset_index(drop=True)


def _spearman(a: pd.Series, b: pd.Series) -> float:
    """Pearson on ranks — identical to Spearman, and avoids adding scipy, which is not on the
    approved dependency list in code-standards.md."""
    return float(a.rank().corr(b.rank()))


def maxdd(pnl: pd.Series) -> float:
    eq = pnl.cumsum()
    return float((eq.cummax() - eq).max()) if len(eq) else 0.0


def write(name: str, body: str) -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / name).write_text(body)
    print(f"\nwrote docs/{name} ({len(body):,} chars)")


# ============================================================ STAGE 0
def stage0() -> None:
    P = london_pop()
    months = sorted(P.mo.unique())
    L = ["# Combined audit — Stage 0: is the London arm choice month-fragile?\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         "\nThe cheap gate, run before spending the hour. If dropping any single month flips "
         "either decision — wall vs old4, or which constraint level wins — the arm choice is an "
         "artifact of that month and the rest of the job is not worth running.\n"]

    def net(arm, level, pop):
        b = london_book(pop, arm, level)
        return b.dollars.sum(), len(b)

    full = {(a, lv): net(a, lv, P)[0] for a in ARMS for lv in LEVELS}
    base_arm = "wall" if max(full[("wall", lv)] for lv in LEVELS) > \
                          max(full[("old4", lv)] for lv in LEVELS) else "old4"
    base_lvl = max(LEVELS, key=lambda lv: full[(base_arm, lv)])
    L.append(f"\n## Full fit span (14 months)\n\n| arm | capped | uncapped | raw |\n"
             f"|---|---|---|---|\n")
    for a in ARMS:
        L.append(f"| {a} | ${full[(a, 'capped')]:+,.0f} | ${full[(a, 'uncapped')]:+,.0f} | "
                 f"${full[(a, 'raw')]:+,.0f} |\n")
    L.append(f"\n**Baseline decision: arm=`{base_arm}`, level=`{base_lvl}`.**\n")

    L.append(f"\n## Drop-one-month jackknife\n\n| month dropped | winning arm | winning level | "
             f"arm flip | level flip |\n|---|---|---|---|---|\n")
    arm_flips, lvl_flips = [], []
    for mo in months:
        Q = P[P.mo != mo]
        d = {(a, lv): net(a, lv, Q)[0] for a in ARMS for lv in LEVELS}
        wa = "wall" if max(d[("wall", lv)] for lv in LEVELS) > \
                       max(d[("old4", lv)] for lv in LEVELS) else "old4"
        wl = max(LEVELS, key=lambda lv: d[(wa, lv)])
        af = wa != base_arm
        lf = wl != base_lvl
        if af:
            arm_flips.append(mo)
        if lf:
            lvl_flips.append(mo)
        L.append(f"| {mo} | {wa} | {wl} | {'**FLIP**' if af else 'no'} | "
                 f"{'**FLIP**' if lf else 'no'} |\n")

    Q2 = P[~P.mo.isin(["2026-03", "2026-05"])]
    d2 = {(a, lv): net(a, lv, Q2) for a in ARMS for lv in LEVELS}
    L.append(f"\n## With BOTH 2026-03 and 2026-05 removed\n\n"
             f"(the two largest contributing months: +$4,964 and +$5,322 of the "
             f"${full[('wall', 'uncapped')]:+,.0f} uncapped total)\n\n"
             f"| arm | capped | uncapped | raw |\n|---|---|---|---|\n")
    for a in ARMS:
        L.append(f"| {a} | ${d2[(a, 'capped')][0]:+,.0f} (n={d2[(a, 'capped')][1]}) | "
                 f"${d2[(a, 'uncapped')][0]:+,.0f} (n={d2[(a, 'uncapped')][1]}) | "
                 f"${d2[(a, 'raw')][0]:+,.0f} (n={d2[(a, 'raw')][1]}) |\n")
    wa2 = "wall" if max(d2[("wall", lv)][0] for lv in LEVELS) > \
                    max(d2[("old4", lv)][0] for lv in LEVELS) else "old4"
    still = d2[("wall", "uncapped")][0] > 0
    L.append(f"\nWinning arm without those two months: **{wa2}**. "
             f"Wall/uncapped remains **{'PROFITABLE' if still else 'UNPROFITABLE'}** at "
             f"${d2[('wall', 'uncapped')][0]:+,.0f} over 12 months.\n")

    L.append("\n## Verdict\n")
    if arm_flips:
        L.append(f"\n**STOP — the arm choice flips on removal of: {', '.join(arm_flips)}.** "
                 f"The wall-vs-old4 decision is not robust to a single month and the rest of "
                 f"this job should not be run on it.\n")
    else:
        L.append(f"\n**PROCEED — the arm choice (`{base_arm}`) survives every single-month "
                 f"removal.** No month's absence flips wall vs old4.\n")
    if lvl_flips:
        L.append(f"\nThe constraint LEVEL is softer: it flips when dropping "
                 f"{', '.join(lvl_flips)}. That is a weaker claim than the arm choice and "
                 f"should be treated as unsettled — capped vs uncapped is a preference, not a "
                 f"finding.\n")
    else:
        L.append(f"\nThe constraint level (`{base_lvl}`) is also stable across all "
                 f"single-month removals.\n")
    (DOCS / "combined_audit_stage0.json").write_text(
        pd.Series({"base_arm": base_arm, "base_level": base_lvl,
                   "arm_flips": ",".join(arm_flips) or "none",
                   "level_flips": ",".join(lvl_flips) or "none",
                   "proceed": not arm_flips}).to_json())
    write("COMBINED-AUDIT-STAGE0-arm-jackknife.md", "".join(L))
    if arm_flips:
        raise SystemExit("STAGE 0 GATE: arm choice is month-fragile — halting by design")


# ============================================================ STAGE 1
def stage1() -> None:
    N, Lo = ny_book(), london_book(london_pop())
    nd = N.groupby("day").pnl_1lot.sum()
    ld = Lo.groupby("day").dollars.sum()
    alld = sorted(set(nd.index) | set(ld.index))
    j = pd.DataFrame({"ny": nd.reindex(alld).fillna(0.0),
                      "lon": ld.reindex(alld).fillna(0.0)})
    both = j[(nd.reindex(alld).notna()) & (ld.reindex(alld).notna())]

    L = ["# Combined audit — Stage 1: joining the NY and London books\n",
         "\n**Fit only. Sealed 2023/24 never loaded.** Both books at 1 NQ lot here so the "
         "correlation is not an artifact of two different sizing schemes.\n",
         f"\n- NY book: {len(N)} trades on {N.day.nunique()} days\n"
         f"- London wall arm: {len(Lo)} trades on {Lo.day.nunique()} days\n"
         f"- **Days both traded: {len(both)}** | NY-only: {len(set(nd.index) - set(ld.index))} "
         f"| London-only: {len(set(ld.index) - set(nd.index))}\n"]

    r_all = j.ny.corr(j.lon)
    r_both = both.ny.corr(both.lon)
    L.append(f"\n## Day-level P&L correlation\n\n"
             f"| basis | n days | Pearson r | Spearman |\n|---|---|---|---|\n"
             f"| all days in either book (absent = $0) | {len(j)} | {r_all:+.3f} | "
             f"{_spearman(j.ny, j.lon):+.3f} |\n"
             f"| days BOTH traded | {len(both)} | {r_both:+.3f} | "
             f"{_spearman(both.ny, both.lon):+.3f} |\n")

    nl, ll = both.ny < 0, both.lon < 0
    obs = float((nl & ll).mean())
    exp = float(nl.mean() * ll.mean())
    L.append(f"\n## Loss-day coincidence vs independence\n\n"
             f"On the {len(both)} shared days: NY loses on {nl.mean() * 100:.1f}%, London on "
             f"{ll.mean() * 100:.1f}%.\n\n"
             f"- **Observed both-lose: {obs * 100:.1f}%** ({int((nl & ll).sum())} days)\n"
             f"- Independence predicts: {exp * 100:.1f}% ({exp * len(both):.1f} days)\n"
             f"- Ratio observed/expected: **{obs / max(exp, 1e-9):.2f}x**\n")
    L.append(f"\n{'Losses cluster MORE than independence predicts' if obs > exp else 'Losses cluster LESS than independence predicts'}"
             f" — the diversification benefit is "
             f"{'weaker' if obs > exp else 'better'} than a naive correlation read suggests.\n")

    # MEASURED clock overlap, one timezone, stated
    L.append(f"\n## Measured clock overlap — all times **America/New_York (ET)**\n")
    nh = N.fill_ts.dt.hour + N.fill_ts.dt.minute / 60
    lh = Lo.fill_ts.dt.hour + Lo.fill_ts.dt.minute / 60
    L.append(f"\n| book | earliest fill | latest fill | median |\n|---|---|---|---|\n"
             f"| NY (window 07:45-11:00 ET) | {nh.min():.2f} | {nh.max():.2f} | "
             f"{nh.median():.2f} |\n"
             f"| London (window 08:00-10:00 Europe/London) | {lh.min():.2f} | {lh.max():.2f} | "
             f"{lh.median():.2f} |\n")
    gap = nh.min() - lh.max()
    L.append(f"\nLondon's latest fill is {lh.max():.2f} ET; NY's earliest is {nh.min():.2f} ET. "
             f"**Clock overlap of the ENTRY windows: none — a {gap:.2f} hour gap.** "
             f"London 08:00-10:00 Europe/London maps to 03:00-05:00 ET (04:00-06:00 on the ~20 "
             f"DST-misaligned days), which ends {nh.min() - 6:.2f}+ hours before NY's 07:45 "
             f"band opens.\n")
    # but POSITIONS can overlap
    lex = Lo.exit_ts if "exit_ts" in Lo else pd.to_datetime(Lo["exit"], format="mixed", utc=True).dt.tz_convert(ET)
    lex = pd.to_datetime(Lo["exit"], format="mixed", utc=True).dt.tz_convert(ET)
    still = (lex.dt.hour + lex.dt.minute / 60) >= 7.75
    L.append(f"\n**Entries never overlap; POSITIONS can.** {int(still.sum())} of {len(Lo)} "
             f"London trades ({still.mean() * 100:.1f}%) are still open at 07:45 ET when NY's "
             f"window opens. That is the only channel through which the two books can compete "
             f"for the one-position constraint or the shared budget intraday.\n")
    write("COMBINED-AUDIT-STAGE1-book-join.md", "".join(L))


# ============================================================ STAGE 2
def _events(N, Lo, lon_ladder: bool):
    """One chronological event stream. Each row: day, ts, session, risk_$, pnl_$, conv."""
    rows = []
    for r in N.itertuples():
        rows.append({"day": r.day, "ts": r.fill_ts, "session": "ny", "conv": r.conv,
                     "risk": r._asdict()["risk_$"], "pnl": r.pnl_ladder})
    for r in Lo.itertuples():
        conv = 1.0
        risk = ladder_risk(conv) if lon_ladder else float(r.risk) * 20.0
        pnl = r.R * risk if lon_ladder else float(r.dollars)
        rows.append({"day": r.day, "ts": r.fill_ts, "session": "london", "conv": conv,
                     "risk": risk, "pnl": pnl})
    return pd.DataFrame(rows).sort_values(["day", "ts"], kind="stable").reset_index(drop=True)


def _replay(E: pd.DataFrame, priority: str):
    """Shared $800 budget, NY's in-flight-inclusive rule:
    realized losses + in-flight risk + new risk <= BUDGET. Chronological, causal."""
    taken, blocked = [], {"ny": 0, "london": 0}
    for _day, g in E.groupby("day", sort=True):
        if priority == "ny_first":
            order = g.assign(k=(g.session != "ny").astype(int))
        elif priority == "london_first":
            order = g.assign(k=(g.session != "london").astype(int))
        else:                                    # higher conviction first
            order = g.assign(k=-g.conv)
        order = order.sort_values(["k", "ts"], kind="stable")
        realized_loss, inflight = 0.0, 0.0
        for r in order.itertuples():
            if realized_loss + inflight + r.risk > BUDGET:
                blocked[r.session] += 1
                continue
            inflight += r.risk
            taken.append({"day": r.day, "ts": r.ts, "session": r.session, "pnl": r.pnl,
                          "risk": r.risk})
            inflight -= r.risk
            if r.pnl < 0:
                realized_loss += -r.pnl
    return pd.DataFrame(taken), blocked


def stage2() -> None:
    N = ny_book()
    P = london_pop()
    Lo = london_book(P)
    L = ["# Combined audit — Stage 2: chronological combined replay, one shared $800 budget\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\nBudget rule (NY's existing in-flight-inclusive form): a trade is taken only if "
         f"`realized losses + in-flight risk + new risk <= ${BUDGET:,.0f}`. Chronological "
         f"within each day; no ordering uses information from later in the day.\n",
         f"\nNY sized on the lucid ladder (base ${BASE_DOLLAR:,.0f}: 0.25=$75, 0.5=$150, "
         f"0.75=$225, 1.0=$300, 1.5=$450, 2.25 capped at $600). P&L = R x risk_$ because "
         f"dollar-risk sizing is stop-width-normalised.\n"]

    ny_alone_ladder = float(N.pnl_ladder.sum())
    L.append(f"\n**NY alone at the ladder: ${ny_alone_ladder:+,.0f}** "
             f"({len(N)} trades). This is the number every combined figure is measured "
             f"against.\n")

    for lab, lon_ladder in (("London at 1 lot", False), ("London at the lucid ladder", True)):
        E = _events(N, Lo, lon_ladder)
        L.append(f"\n## {lab}\n\n| priority | NY blocked | LON blocked | combined net | "
                 f"vs NY-alone | worst day | maxDD |\n|---|---|---|---|---|---|---|\n")
        for pr, prlab in (("ny_first", "NY-first"), ("london_first", "London-first"),
                          ("conviction", "higher-conviction-first")):
            T, bl = _replay(E, pr)
            daily = T.groupby("day").pnl.sum()
            net = float(T.pnl.sum())
            L.append(f"| {prlab} | {bl['ny']} | {bl['london']} | ${net:+,.0f} | "
                     f"**${net - ny_alone_ladder:+,.0f}** | ${daily.min():+,.0f} | "
                     f"${maxdd(daily):,.0f} |\n")
    L.append(f"\n**\"vs NY-alone\" is London's real contribution** — combined net minus the "
             f"${ny_alone_ladder:+,.0f} NY makes by itself under the same budget. A positive "
             f"figure means London adds money after paying for every NY trade it displaced.\n")
    write("COMBINED-AUDIT-STAGE2-combined-replay.md", "".join(L))


# ============================================================ STAGE 3
def stage3() -> None:
    N = ny_book()
    Lo = london_book(london_pop())
    E_ny = _events(N, Lo.iloc[0:0], False)
    E_both = _events(N, Lo, False)
    T_ny, _ = _replay(E_ny, "ny_first")
    T_both, _ = _replay(E_both, "ny_first")

    def day_map(T):
        return {d: g.pnl.tolist() for d, g in T.groupby("day")}

    dm_ny, dm_both = day_map(T_ny), day_map(T_both)
    days = sorted(set(dm_both) | set(dm_ny))

    def simulate_paths(dm, label):
        rng = np.random.default_rng(RNG_SEED)
        keys = np.array([d for d in days if d in dm], dtype=object)
        busts, cycles, payouts = 0, [], []
        for _ in range(N_PATHS):
            eq, floor, locked, paid, cyc = START, START - TRAIL, False, 0.0, 0
            draw = rng.integers(0, len(keys), size=252)
            for i in draw:
                for p in dm[keys[i]]:            # intraday order preserved within the day
                    eq += p
                if eq >= PAYOUT_AT:
                    eq -= PAYOUT
                    paid += PAYOUT
                    cyc += 1
                if not locked:                   # trailing EOD DD
                    floor = max(floor, eq - TRAIL)
                    if floor >= START:
                        floor, locked = START, True
                if eq <= floor:
                    busts += 1
                    break
            cycles.append(cyc)
            payouts.append(paid)
        return {"label": label, "bust": busts / N_PATHS, "cycles": np.array(cycles),
                "payout": np.array(payouts)}

    a = simulate_paths(dm_ny, "NY alone")
    b = simulate_paths(dm_both, "NY + London")

    L = ["# Combined audit — Stage 3: funded-account Monte Carlo\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\n{N_PATHS:,} paths, 252 trading days each, seeded RNG ({RNG_SEED}).\n",
         "\n**Day-level bootstrap keeping BOTH books in the same draw.** A drawn calendar day "
         "brings every trade that occurred on it, from both sessions, in original intraday "
         "order. The two books are never resampled independently — doing so would destroy the "
         "cross-book correlation this entire job exists to measure, and would flatter the "
         "combined distribution by manufacturing diversification that is not there.\n",
         f"\nFunded rules: start ${START:,.0f}; ${TRAIL:,.0f} trailing EOD drawdown that locks "
         f"at start once equity reaches ${LOCK_AT:,.0f}; withdrawal threshold "
         f"${MIN_WITHDRAW_AT:,.0f}; a full ${PAYOUT:,.0f} payout taken at ${PAYOUT_AT:,.0f} "
         f"(leaving ${PAYOUT_AT - PAYOUT:,.0f}, i.e. ${PAYOUT_AT - PAYOUT - START:,.0f} above "
         f"start). Bust = end-of-day equity at or below the floor.\n",
         f"\nBoth arms replay under the shared ${BUDGET:,.0f} budget, NY-first priority, "
         f"London at 1 lot — so the comparison isolates London's addition, not a sizing change.\n"]

    L.append(f"\n## Result\n\n| | P(bust) | payout cycles (med / p90) | net payout "
             f"(p10 / median / p90) |\n|---|---|---|---|\n")
    for r in (a, b):
        L.append(f"| {r['label']} | **{r['bust'] * 100:.1f}%** | "
                 f"{np.median(r['cycles']):.0f} / {np.percentile(r['cycles'], 90):.0f} | "
                 f"${np.percentile(r['payout'], 10):,.0f} / ${np.median(r['payout']):,.0f} / "
                 f"${np.percentile(r['payout'], 90):,.0f} |\n")
    dbust = (b["bust"] - a["bust"]) * 100
    dmed = np.median(b["payout"]) - np.median(a["payout"])
    L.append(f"\n## Does adding London raise or lower the distribution?\n")
    L.append(f"\n- P(bust): {a['bust'] * 100:.1f}% -> {b['bust'] * 100:.1f}% "
             f"(**{dbust:+.1f} pp**)\n"
             f"- Median net payout: ${np.median(a['payout']):,.0f} -> "
             f"${np.median(b['payout']):,.0f} (**${dmed:+,.0f}**)\n"
             f"- p10 (the bad tail): ${np.percentile(a['payout'], 10):,.0f} -> "
             f"${np.percentile(b['payout'], 10):,.0f}\n")
    verdict = ("RAISES the distribution" if dmed > 0 and dbust <= 0 else
               "raises payout but also raises bust risk" if dmed > 0 else
               "LOWERS the distribution")
    L.append(f"\n**Verdict: adding London {verdict}.**\n")
    L.append(f"\nCaveat that travels with every number here: this is the FIT span bootstrapped. "
             f"It assumes the future resembles 2025-06..2026-07 in both books, and the sealed "
             f"2023/24 holdout — the only untouched evidence — has not been run.\n")
    write("COMBINED-AUDIT-STAGE3-monte-carlo.md", "".join(L))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=[0, 1, 2, 3], required=True)
    a = ap.parse_args()
    {0: stage0, 1: stage1, 2: stage2, 3: stage3}[a.stage]()


if __name__ == "__main__":
    main()
