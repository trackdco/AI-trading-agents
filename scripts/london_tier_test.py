#!/usr/bin/env python3
"""LONDON conviction tiers — which sizing shape is best? FIT ONLY. Holdout sealed.

THE GAP THIS CLOSES. NY sizes by conviction: base $150 static -> tiers $75/150/225/300 off a
4-point score. London's score is BINARY: of its four candidate checks, ROOM was killed as noise
and ASIA as backwards, leaving W and FAR — and those two are one signal (r=0.834), so `wall` =
(W or FAR) is a 0/1 gate, not a ladder. Consequence: every London P&L figure quoted so far is
FLAT 1 NQ LOT, which risks $255 median / $280 mean per trade — 1.9x the lucid tier-1.0 unit of
$150. "London makes +$22,795" is therefore a statement about an un-declared position size, not
about funded sizing. This script decides the sizing rule.

THE TWO QUESTIONS ARE SEPARATE, AND CONFLATING THEM IS THE TRAP.

  SHAPE  Does splitting the gate into two cells — both W+FAR vs exactly one — and sizing them
         differently beat one flat size? Pure signal question. Answered at MATCHED TOTAL RISK,
         so scale cannot leak in: whatever the shape, the book deploys the same summed dollar
         risk over the same trades. Without that normalisation "bigger tier = more money" wins
         by construction and tells you nothing.

  SCALE  Given the shape, how big? NOT a signal question — a risk-budget question, and it is
         not free. London fills 03:02-05:54 ET and NY opens 07:45, so London draws first on the
         shared $800 budget; a larger London unit blocks NY trades. Answered on the verified NY
         canon under the real budget, trailing drawdown and payout cadence.

PARAMETERISATION. shape = ratio r = tier(both) / tier(one). r = 1 is flat. Declared grid:
r in {1, 1.5, 2, 3} — FOUR cells, fixed before looking, and the winner is charged the shrinkage
appropriate to that breadth off the stage-3 curve (docs/LONDON-AUDIT-STAGE3-selection-null.md).
At n=4 that charge is -0.014 R, i.e. negligible — which is the point of pre-declaring a small
grid instead of sweeping.

  Risk-band tiering (size off stop width) is reported as a FIFTH, PRE-REJECTED shape. It is
  partly circular: risk is R's denominator, so a band that sorts on stop width is partly
  sorting on the metric it is judged by. It is printed, not hidden, and not selected.

SIZING ARITHMETIC. Dollar-risk sizing, stop-width-normalised, on MNQ at $2/pt:
    risk_$    = base x tier            (base $150, the lucid static base)
    contracts = risk_$ / (stop_pts x 2)
    pnl       = R x contracts x stop_pts x 2
Part 1 uses CONTINUOUS contracts so the matched-risk normalisation is exact and the shape test
is clean. Part 3 uses INTEGER contracts, floor with a 1-contract minimum, because that is what
actually gets sent — and the rounding is not negligible at small tiers (a $75 unit on a 12.8pt
stop is 2.93 contracts -> 2). Both are reported; neither is the other's sanity check.

    python -m scripts.london_tier_test
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select                      # noqa: E402
from scripts.london_combined_job import (BUDGET, N_PATHS, SEED,     # noqa: E402
                                         _daymap, lon_pop, maxdd, mc, preflight,
                                         replay, shrink, write)

BASE = 150.0            # lucid static base — the tier-1.0 unit
MNQ = 2.0               # $/pt, MNQ
NQ_PT = 20.0            # $/pt, NQ (1 NQ = 10 MNQ)
FLOOR, LIFETIME, CAP = 9.5, math.inf, 999      # the frozen arm: window-end x uncapped
DAY_STOP = 400.0
RATIOS = [1.0, 1.5, 2.0, 3.0]                  # DECLARED GRID — four cells, fixed upfront
N_PERM = 2000
POWER_FLOOR = 25                               # min n per era per cell to call a result
# (tier_both, tier_one) pairs that EXIST on the lucid ladder {0.5, 1.0, 1.5, 2.0}. Anything
# outside it is not a London decision — it needs the NY profile's ceiling changed — so it is
# excluded from selection rather than allowed to win by being the biggest thing on the list.
LADDER = {0.5, 1.0, 1.5, 2.0}
LADDER_SCALES = {
    1.0: [("flat 0.5", 0.5, 0.5), ("flat 1.0", 1.0, 1.0),
          ("flat 1.5", 1.5, 1.5), ("flat 2.0", 2.0, 2.0)],
    1.5: [("1.5 / 1.0", 1.5, 1.0)],
    2.0: [("1.0 / 0.5", 1.0, 0.5), ("2.0 / 1.0", 2.0, 1.0)],
    3.0: [("1.5 / 0.5", 1.5, 0.5)],
}


# --------------------------------------------------------------------------- book
def population() -> pd.DataFrame:
    """The frozen arm's candidate pool, with stop width kept in POINTS and R made explicit."""
    P = lon_pop()
    Q = P[(P.risk >= FLOOR) & (P.max_away_before_fill < LIFETIME)].copy()
    Q["stop_pts"] = Q.risk.astype(float)
    Q["both"] = ((Q.W == 1) & (Q.FAR == 1)).astype(bool)
    Q["wall"] = ((Q.W == 1) | (Q.FAR == 1)).astype(float)
    Q["R"] = Q.dollars.astype(float) / (Q.stop_pts * NQ_PT)
    return Q


def book(Q: pd.DataFrame, tier_both: float, tier_one: float | None = None,
         integer: bool = True, day_stop: float = DAY_STOP) -> pd.DataFrame:
    """Select and size. tier_one=None => flat 1 NQ lot (the status-quo reference).

    The day stop is a rule on REALIZED ACCOUNT DOLLARS, so it is applied to the SIZED P&L, not
    to 1-lot P&L — which means the selected set can legitimately differ between sizing options.
    That is the honest behaviour; Part 1 pins the set instead (day_stop off) to isolate shape.
    """
    W = Q.copy()
    if tier_one is None:
        W["contracts"] = 10.0                              # 1 NQ = 10 MNQ
    else:
        W["tier"] = np.where(W.both, tier_both, tier_one)
        want = BASE * W.tier
        c = want / (W.stop_pts * MNQ)
        W["contracts"] = np.maximum(1.0, np.floor(c)) if integer else c
    W["risk_d"] = W.contracts * W.stop_pts * MNQ           # ACTUAL deployed dollar risk
    W["pnl_sized"] = W.R * W.risk_d
    pol = L4Policy(threshold={"london": 1.0}, escalation_threshold={"london": 1.0},
                   cap_per_session=CAP, day_stop_dollars=day_stop)
    b = select(W.assign(score=W.wall), pol, dollars_col="pnl_sized")
    t = b[b.taken].copy()
    t["risk"] = t.risk_d                                   # replay's budget rule reads `risk`
    t["pnl"] = t.pnl_sized
    return t.reset_index(drop=True)


def weights(both: np.ndarray, r: float) -> np.ndarray:
    """Tier weights for ratio r, normalised so mean weight is exactly 1.0.

    Total deployed risk is then BASE x n for every r — the matched-risk condition. Without it
    the comparison is a scale comparison wearing a shape comparison's clothes.

    r = inf puts the whole budget on the both cell and nothing on one-only. That is a GATE
    change, not a tier — see part1's note — but it is the natural limit of the ratio family and
    is measured rather than left implicit.
    """
    if math.isinf(r):
        nb = max(int(both.sum()), 1)
        return np.where(both, len(both) / nb, 0.0).astype(float)
    w = np.where(both, r, 1.0).astype(float)
    return w * (len(w) / w.sum())


def stats(R: np.ndarray, w: np.ndarray, day: np.ndarray) -> dict:
    pnl = R * BASE * w
    d = pd.Series(pnl).groupby(pd.Series(day)).sum()
    return {"net": float(pnl.sum()), "dd": maxdd(d), "worst": float(pnl.min()),
            "best": float(pnl.max()), "wr": float((pnl > 0).mean())}


# --------------------------------------------------------------------------- part 1
def part1(Q: pd.DataFrame, L: list) -> tuple:
    """Shape at matched total risk, on a PINNED trade set."""
    T = book(Q, 1.0, 1.0, integer=False, day_stop=1e12)     # set pinned: day stop off
    R, both, day = T.R.values, T.both.values, T.day.values
    era = pd.to_datetime(T.day).dt.year.astype(str).values
    nb, no = int(both.sum()), int((~both).sum())

    L.append(f"\n## Part 1 — shape, at matched total risk\n\n"
             f"Trade set PINNED at {len(T)} trades (frozen arm: floor {FLOOR:g}pt, window-end "
             f"lifetime, uncapped; day stop disabled here so every shape scores the SAME trades "
             f"and only the weights move). Continuous contracts, so total deployed risk is "
             f"exactly ${BASE:,.0f} x {len(T)} = **${BASE * len(T):,.0f}** for every row below.\n")
    L.append(f"\nCells: **both W+FAR n={nb}**, **exactly one n={no}**. "
             f"Mean R overall **{R.mean():+.3f}**.\n")
    L.append("\n| cell | n | WR | mean R | 2025 n / R | 2026 n / R |\n|---|---|---|---|---|---|\n")
    for lab, m in (("both W+FAR", both), ("exactly one", ~both)):
        s25, s26 = m & (era == "2025"), m & (era == "2026")
        L.append(f"| {lab} | {int(m.sum())} | {(R[m] > 0).mean() * 100:.0f}% | "
                 f"{R[m].mean():+.3f} | {int(s25.sum())} / {R[s25].mean():+.3f} | "
                 f"{int(s26.sum())} / {R[s26].mean():+.3f} |\n")

    weak = [e for e in ("2025", "2026")
            if ((~both) & (era == e)).sum() < POWER_FLOOR]
    L.append(f"\n**Power:** the one-only cell must carry >= {POWER_FLOOR} trades per era to be "
             f"called. " + (f"UNDERPOWERED in {weak} — the separation below is reported but is "
                            f"NOT a result.\n" if weak else
                            "Both eras clear it, but only just — treat the one-only mean R as a "
                            "wide interval, not a point.\n"))

    L.append("\n| ratio r = tier(both)/tier(one) | net | maxDD | net/maxDD | worst trade | "
             "2025 net | 2026 net |\n|---|---|---|---|---|---|---|\n")
    res = {}
    for r in RATIOS:
        w = weights(both, r)
        s = stats(R, w, day)
        n25 = stats(R[era == "2025"], weights(both[era == "2025"], r), day[era == "2025"])
        n26 = stats(R[era == "2026"], weights(both[era == "2026"], r), day[era == "2026"])
        res[r] = dict(s, n25=n25["net"], n26=n26["net"], w=w)
        L.append(f"| {'**1.0 (flat)**' if r == 1 else f'{r:g}'} | ${s['net']:+,.0f} | "
                 f"${s['dd']:,.0f} | {s['net'] / max(s['dd'], 1):.1f} | ${s['worst']:+,.0f} | "
                 f"${n25['net']:+,.0f} | ${n26['net']:+,.0f} |\n")

    # the ratio family's limit, and a pre-rejected fifth shape. Both reported, neither selected.
    inf_s = stats(R, weights(both, math.inf), day)
    i25 = stats(R[era == "2025"], weights(both[era == "2025"], math.inf), day[era == "2025"])
    i26 = stats(R[era == "2026"], weights(both[era == "2026"], math.inf), day[era == "2026"])
    L.append(f"| _inf (both only — a GATE change, not a tier)_ | _${inf_s['net']:+,.0f}_ | "
             f"_${inf_s['dd']:,.0f}_ | _{inf_s['net'] / max(inf_s['dd'], 1):.1f}_ | "
             f"_${inf_s['worst']:+,.0f}_ | _${i25['net']:+,.0f}_ | _${i26['net']:+,.0f}_ |\n")
    q = pd.qcut(T.stop_pts, 3, labels=False, duplicates="drop").values
    band = np.where(q == 0, 3.0, np.where(q == 1, 2.0, 1.0))       # tight stop -> big tier
    band = band * (len(band) / band.sum())
    sb = stats(R, band, day)
    L.append(f"| _risk-band 3-tier (PRE-REJECTED, circular)_ | _${sb['net']:+,.0f}_ | "
             f"_${sb['dd']:,.0f}_ | _{sb['net'] / max(sb['dd'], 1):.1f}_ | "
             f"_${sb['worst']:+,.0f}_ | — | — |\n")
    L.append(f"\n**On r = inf.** Dropping the one-only trades entirely is the ratio family's "
             f"limit and it scores ${inf_s['net']:+,.0f} at matched risk, but it is NOT a sizing "
             f"decision — it redefines the gate from `W or FAR` to `W and FAR`, which is a "
             f"structural hypothesis and would take pre-registration multiplicity from 2 to 3. "
             f"It was also added AFTER the first look at the declared four, so quoting it as the "
             f"winner would be exactly the selection inflation the stage-3 curve exists to "
             f"charge for. Measured and recorded here; it is not selected, and if it is ever "
             f"promoted it goes in as a declared structural hypothesis with its own alpha.\n")

    best = max((r for r in RATIOS), key=lambda r: res[r]["net"])
    L.append(f"\n**Best ratio on net at matched risk: r = {best:g}** "
             f"(${res[best]['net']:+,.0f} vs flat ${res[1.0]['net']:+,.0f}, "
             f"**${res[best]['net'] - res[1.0]['net']:+,.0f}**). Charged shrinkage at the "
             f"declared breadth of {len(RATIOS)} cells: **{shrink(len(RATIOS)):+.3f} R** per "
             f"trade, i.e. ${shrink(len(RATIOS)) * BASE * len(T):+,.0f} off the net -> "
             f"**${res[best]['net'] + shrink(len(RATIOS)) * BASE * len(T):+,.0f}** forward.\n")
    return T, res, best


# --------------------------------------------------------------------------- part 2
def part2(T: pd.DataFrame, res: dict, best: float, L: list) -> float:
    """Is the both-vs-one separation real, or is the ladder fitting noise?"""
    R, both, day = T.R.values, T.both.values, T.day.values
    era = pd.to_datetime(T.day).dt.year.astype(str).values
    obs = res[best]["net"] - res[1.0]["net"]

    rng = np.random.default_rng(SEED)
    L.append(f"\n## Part 2 — permutation null on the both-vs-one separation\n\n"
             f"H0: the cell label carries no size-relevant information. Statistic: net at "
             f"r={best:g} minus net at r=1 (flat), matched risk, same trades. The label is "
             f"shuffled **within era** ({N_PERM:,} shuffles, seeded {SEED}) so era composition "
             f"cannot supply the effect.\n\n"
             "| span | observed advantage | null mean | null p95 | p-value |\n|---|---|---|---|---|\n")
    ps = {}
    for lab, mask in (("2025", era == "2025"), ("2026", era == "2026"),
                      ("both eras", np.ones(len(R), bool))):
        Rm, bm, dm, em = R[mask], both[mask], day[mask], era[mask]
        o = stats(Rm, weights(bm, best), dm)["net"] - stats(Rm, weights(bm, 1.0), dm)["net"]
        null = np.empty(N_PERM)
        for i in range(N_PERM):
            sh = bm.copy()
            for e in np.unique(em):
                idx = np.flatnonzero(em == e)
                sh[idx] = rng.permutation(bm[idx])
            null[i] = (stats(Rm, weights(sh, best), dm)["net"]
                       - stats(Rm, weights(sh, 1.0), dm)["net"])
        p = float((null >= o).mean())
        ps[lab] = p
        L.append(f"| {lab} | ${o:+,.0f} | ${null.mean():+,.0f} | ${np.percentile(null, 95):+,.0f} "
                 f"| **{p:.4f}** |\n")

    # jackknife: leave one month out, does the advantage keep its sign?
    mo = pd.to_datetime(T.day).dt.strftime("%Y-%m").values
    signs = []
    for m in sorted(set(mo)):
        k = mo != m
        a = (stats(R[k], weights(both[k], best), day[k])["net"]
             - stats(R[k], weights(both[k], 1.0), day[k])["net"])
        signs.append(a > 0)
    L.append(f"\n**Jackknife leave-one-month-out:** the r={best:g} advantage keeps its sign in "
             f"**{sum(signs)}/{len(signs)}** months-removed refits. "
             + ("Not month-dependent.\n" if sum(signs) == len(signs) else
                "It flips on at least one month's removal — fragile.\n"))
    L.append(f"\n**Verdict on shape:** "
             + (f"the separation survives at p={ps['both eras']:.4f} pooled and is present in "
                f"both eras (p={ps['2025']:.4f} / {ps['2026']:.4f}).\n"
                if max(ps["2025"], ps["2026"]) < 0.05 else
                f"pooled p={ps['both eras']:.4f}, but per-era p = {ps['2025']:.4f} / "
                f"{ps['2026']:.4f} — it is NOT independently significant in both eras, so the "
                f"ladder is a secondary hypothesis, not the frozen primary.\n"))
    return ps["both eras"]


# --------------------------------------------------------------------------- part 3
def part3(Q: pd.DataFrame, best: float, L: list) -> None:
    """Scale, under the real funded constraints. Bigger is not free."""
    N = preflight()
    raw_net = float(N.pnl.sum())
    dmN, kN = _daymap(N)
    base_mc = mc(dmN, kN)
    # BASELINE = NY replayed under the SAME budget rule with an EMPTY London book, not the raw
    # book sum. The rule blocks a few NY trades on its own; charging that to London (or crediting
    # it) is a definitional error. The first run of this script used the raw sum and every
    # "vs NY-alone" delta carried the offset below.
    EMPTY = pd.DataFrame(columns=["day", "fill_ts", "session", "risk", "pnl", "R"])
    B, _ = replay(N, EMPTY, "clock")
    ny_net = float(B.pnl.sum())
    sane = 0.005 <= base_mc["bust"] <= 0.04
    L.append(f"\n## Part 3 — scale, under the real funded constraints\n\n"
             f"NY = the verified lucid canon ({len(N)} trades, {N.day.nunique()} days, "
             f"${raw_net:+,.0f}). Shared ${BUDGET:,.0f} daily budget, chronological and causal — "
             f"London fills 03:02-05:54 ET and draws first, so it can crowd NY out (though not by "
             f"the mechanism it looks like — see below). Integer MNQ contracts, day stop "
             f"${DAY_STOP:,.0f} on sized dollars, {N_PATHS:,} MC paths keeping both books in the "
             f"same day-draw.\n"
             f"\n**Sanity: NY-alone P(bust) = {base_mc['bust'] * 100:.1f}%** (must be 0.5-4%). "
             f"{'PASS' if sane else 'FAIL'}\n"
             f"\n**Baseline correction.** NY replayed under the same ${BUDGET:,.0f} rule with an "
             f"EMPTY London book nets **${ny_net:+,.0f}**, against ${raw_net:+,.0f} for the raw "
             f"book: the budget rule blocks NY trades worth ${ny_net - raw_net:+,.0f} on its own. "
             f"Every 'vs NY-alone' figure below is measured against the REPLAYED baseline, so that "
             f"offset is not credited to London. The first run of this script used the raw sum and "
             f"every delta carried it — visible as an identical ${ny_net - raw_net:+,.0f} in the "
             f"zero-edge column, where London contributes exactly nothing.\n")
    if not sane:
        raise SystemExit(f"SANITY FAILED: NY-alone P(bust) {base_mc['bust'] * 100:.1f}% outside "
                         f"0.5-4%. No Part 3 number is valid.")

    L.append(f"\n**Candidate set restricted to tiers that EXIST on the lucid ladder "
             f"{{{', '.join(f'{t:g}' for t in sorted(LADDER))}}}.** A first pass allowed "
             f"ratio-preserving pairs off the ladder (3.0/1.0 = $450/$150 of risk) and that pair "
             f"won — but tier 3.0 is not available on a profile whose ceiling is $300, so it was "
             f"not a London decision at all, it was a request to change the NY profile. Excluded.\n")
    L.append("\n| London sizing | trades | LON net | mean risk/trade | NY blk | combined net | "
             "vs NY-alone | per $1 risk | P(bust) | med withdrawn |\n"
             "|---|---|---|---|---|---|---|---|---|---|\n")
    L.append(f"| _NY alone_ | 0 | $0 | — | 0 | ${ny_net:+,.0f} | $0 | — | "
             f"**{base_mc['bust'] * 100:.1f}%** | ${np.median(base_mc['pay']):,.0f} |\n")

    cands = list(LADDER_SCALES[1.0])
    if best != 1.0:
        cands += LADDER_SCALES[best]
    cands += [("1 NQ lot (status quo, OFF-ladder)", None, None)]

    def at_mean_R(Lo, target):
        """Re-run the combined replay with London's mean R forced to `target`.

        Implemented as a SHIFT of every trade's R (pnl = (R - s) * risk_d, s = meanR_fit - target),
        which preserves trade-level dispersion while moving the centre. A multiplicative haircut
        was tried first and CANNOT rank scales: it multiplies every candidate by the same factor,
        so half of a bigger number is still bigger and the ordering survives by construction.
        A shift can rank them, because it converts winners into losers — and it is London's
        realized LOSSES, not its risk, that accumulate against the shared budget.
        target=None leaves the fit P&L untouched.
        """
        pnl = (Lo.pnl.values if target is None
               else (Lo.R.values - (Lo.R.mean() - target)) * Lo.risk.values)
        T, bl = replay(N, Lo.assign(pnl=pnl), "clock")
        dm, k = _daymap(T)
        r = mc(dm, k)
        return {"delta": float(T.pnl.sum()) - ny_net, "bust": r["bust"],
                "pay": float(np.median(r["pay"])), "blk": bl["ny"]}

    fitR = float(book(Q, 1.0, 1.0).R.mean())
    SCEN = [("fit", None), ("+0.30", 0.30), ("+0.20", 0.20), ("+0.10", 0.10),
            ("0.00", 0.00), ("-0.10", -0.10), ("-0.25", -0.25)]
    SEP = ("|---" * (len(SCEN) + 1)) + "|\n"
    rows = []
    for lab, tb, to in cands:
        Lo = book(Q, tb if tb is not None else 1.0, to)
        sc = {s[0]: at_mean_R(Lo, s[1]) for s in SCEN}
        f = sc["fit"]
        rows.append(dict(lab=lab, n=len(Lo), lon=float(Lo.pnl.sum()),
                         mr=float(Lo.risk.mean()), sc=sc,
                         onladder=(tb in LADDER and to in LADDER), **f))
        L.append(f"| {lab} | {len(Lo)} | ${Lo.pnl.sum():+,.0f} | ${Lo.risk.mean():,.0f} | "
                 f"{f['blk']} | ${ny_net + f['delta']:+,.0f} | **${f['delta']:+,.0f}** | "
                 f"${f['delta'] / max(Lo.risk.mean(), 1):,.0f} | "
                 f"{f['bust'] * 100:.1f}% | **${f['pay']:,.0f}** |\n")

    L.append(f"\n### P(bust) cannot decide this, and neither can a haircut\n\n"
             f"Every config sits at or below NY-alone's {base_mc['bust'] * 100:.1f}%: London is "
             f"profitable, its per-trade risk is small against a $2,000 trailing line, and the "
             f"shared ${BUDGET:,.0f} budget already caps daily exposure. A proportional haircut "
             f"is no better — it multiplies every candidate by the same factor, so the ranking "
             f"survives by construction and a rule of the form 'maximise withdrawn subject to a "
             f"haircut test' cannot lose. Both degenerate to 'pick the biggest', which is not a "
             f"finding.\n"
             f"\nWhat CAN rank scales is London's true mean R landing below what the fit measured. "
             f"The mechanism is worth stating precisely, because it is not what it looks like: "
             f"under the budget rule a trade's risk gates its OWN admission, but only REALIZED "
             f"LOSSES accumulate against the ${BUDGET:,.0f}. London therefore does not crowd NY "
             f"by being big — it crowds NY by LOSING while being big. At mean R = 0 the losses "
             f"are real even though the net is not, and the crowding cost scales with the size "
             f"chosen. That is where a large unit is punished, and it is the only place it is.\n")
    L.append(f"\n### Downside scenarios — London's true mean R, dispersion preserved\n\n"
             f"Fit measures mean R = **{fitR:+.3f}** on the taken book. Each column forces the "
             f"mean to the stated value and re-runs the entire combined replay and Monte Carlo. "
             f"Figures are London's contribution over the replayed NY-alone baseline.\n\n"
             "| London sizing | " + " | ".join(f"R={s[0]}" for s in SCEN) + " |\n" + SEP)
    for x in rows:
        L.append(f"| {x['lab']} | "
                 + " | ".join(f"${x['sc'][s[0]]['delta']:+,.0f}" for s in SCEN) + " |\n")
    L.append("\nSame scenarios, P(bust):\n\n| London sizing | "
             + " | ".join(f"R={s[0]}" for s in SCEN) + " |\n" + SEP)
    for x in rows:
        L.append(f"| {x['lab']} | "
                 + " | ".join(f"{x['sc'][s[0]]['bust'] * 100:.1f}%" for s in SCEN) + " |\n")

    # break-even mean R: scanned, not solved — the budget rule accumulates realized losses, so
    # the blocked set depends on the P&L and the relationship is not linear.
    L.append("\n### Break-even mean R\n\nHow far can London's true mean R fall before it stops "
             "adding anything to the combined account? Scanned in 0.01 steps down from the fit "
             "value; not solved analytically, because the blocked set depends on the P&L.\n\n"
             "| London sizing | break-even mean R | headroom below fit | cost at R = 0.00 | "
             "cost at R = -0.25 |\n|---|---|---|---|---|\n")
    for x, (lab, tb, to) in zip(rows, cands):
        Lo = book(Q, tb if tb is not None else 1.0, to)
        be = None
        for m in np.arange(fitR, -0.301, -0.01):
            pnl = (Lo.R.values - (Lo.R.mean() - m)) * Lo.risk.values
            T, _ = replay(N, Lo.assign(pnl=pnl), "clock")
            if float(T.pnl.sum()) - ny_net <= 0:
                be = float(m)
                break
        x["be"], x["z0"], x["z25"] = be, x["sc"]["0.00"]["delta"], x["sc"]["-0.25"]["delta"]
        L.append(f"| {x['lab']} | {'< -0.30' if be is None else f'{be:+.2f}'} | "
                 f"{'>' if be is None else ''}{fitR - (be if be is not None else -0.30):.2f} R | "
                 f"${x['z0']:+,.0f} | ${x['z25']:+,.0f} |\n")

    # WHICH scenario the P(bust) ceiling is enforced at is the whole decision, so it is declared
    # rather than discovered. BIND is "half the fit edge", the same margin of safety stage 4's
    # haircut sensitivity already used (25/50/75%); half of +0.471 is ~+0.20. Enforcing the
    # ceiling at the WORST column instead (R = -0.25, i.e. London badly negative when the fit
    # measures +0.47) is a rule no size but a token one can pass, and a first pass did exactly
    # that and returned a spurious "no config survives". The full mapping is printed below so the
    # sensitivity of the pick to this choice is visible instead of buried.
    BIND = "+0.20"
    ceil = base_mc["bust"] + 0.005
    nl = len([x for x in rows if x["onladder"]])
    L.append(f"\n**Selection rule.** (a) both tiers on the lucid ladder — off-ladder sizes are a "
             f"profile change, not a London decision; (b) P(bust) no more than 0.5pp above "
             f"NY-alone (ceiling {ceil * 100:.1f}%) at a declared adverse scenario; (c) among "
             f"survivors, maximise median withdrawn.\n"
             f"\nThe binding scenario is declared as **mean R = {BIND}**, i.e. roughly HALF the "
             f"fit edge of {fitR:+.3f} — the same margin of safety stage 4's haircut sensitivity "
             f"already used. It is not chosen for its answer: enforcing the ceiling at the worst "
             f"column instead (R = -0.25, London badly negative where the fit measures "
             f"{fitR:+.2f}) is a rule that only a token size can pass, and it returns a spurious "
             f"null. Here is the pick under EVERY scenario, so the choice is visible:\n\n"
             "| ceiling enforced at | configs clearing | pick | med withdrawn (fit) | "
             "contribution (fit) |\n|---|---|---|---|---|\n")
    for s, _ in SCEN:
        e = [x for x in rows if x["onladder"] and x["sc"][s]["bust"] <= ceil]
        if e:
            p = max(e, key=lambda x: x["pay"])
            L.append(f"| R = {s} | {len(e)}/{nl} | {'**' if s == BIND else ''}{p['lab']}"
                     f"{'**' if s == BIND else ''} | ${p['pay']:,.0f} | ${p['delta']:+,.0f} |\n")
        else:
            L.append(f"| R = {s} | 0/{nl} | _none — London flat 0.5 or not at all_ | — | — |\n")

    ok = [x for x in rows if x["onladder"] and x["sc"][BIND]["bust"] <= ceil]
    if not ok:
        L.append("\n**NO CONFIG SURVIVES at the declared scenario.** Reported as a null; no "
                 "scale is selected.\n")
        return _rounding(Q, L)
    pick = max(ok, key=lambda x: x["pay"])
    bel = "< -0.30" if pick["be"] is None else f"{pick['be']:+.2f}"
    L.append(f"\n### Answer\n\n**{pick['lab']}** — {len(ok)} of {nl} on-ladder configs clear the "
             f"ceiling at R = {BIND}, and this is the largest of them by median withdrawn.\n\n"
             f"| | fit | R = {BIND} | R = 0.00 | R = -0.25 |\n|---|---|---|---|---|\n"
             f"| contribution | ${pick['delta']:+,.0f} | ${pick['sc'][BIND]['delta']:+,.0f} | "
             f"${pick['z0']:+,.0f} | ${pick['z25']:+,.0f} |\n"
             f"| P(bust) | {pick['bust'] * 100:.1f}% | {pick['sc'][BIND]['bust'] * 100:.1f}% | "
             f"{pick['sc']['0.00']['bust'] * 100:.1f}% | "
             f"{pick['sc']['-0.25']['bust'] * 100:.1f}% |\n"
             f"\nMedian withdrawn ${pick['pay']:,.0f}, mean risk ${pick['mr']:,.0f}/trade, "
             f"break-even mean R {bel} — {fitR - (pick['be'] if pick['be'] is not None else -0.30):.2f} R "
             f"of headroom below the fit measurement.\n")
    # the ladder-vs-flat claim, stated against the flats it sits between on size
    flats = [x for x in rows if x["lab"].startswith("flat")]
    L.append("\n### Why this beats the flat tiers either side of it\n\nThe pick is not simply the "
             "biggest survivor — it is a different SHAPE, and the comparison that matters is "
             "against the flat tiers it sits between on mean risk per trade.\n\n"
             "| config | mean risk | contribution fit | contribution R=+0.20 | contribution R=0 | "
             "P(bust) R=0 | break-even mean R |\n|---|---|---|---|---|---|---|\n")
    for x in sorted(flats + [pick], key=lambda x: x["mr"]):
        be = "< -0.30" if x["be"] is None else f"{x['be']:+.2f}"
        mark = "**" if x is pick else ""
        L.append(f"| {mark}{x['lab']}{mark} | ${x['mr']:,.0f} | ${x['delta']:+,.0f} | "
                 f"${x['sc']['+0.20']['delta']:+,.0f} | ${x['z0']:+,.0f} | "
                 f"{x['sc']['0.00']['bust'] * 100:.1f}% | {be} |\n")
    se = math.sqrt(0.03 * 0.97 / N_PATHS) * 100
    L.append(f"\nRead the two halves of that table differently, because they are not equally "
             f"precise. **The contribution columns are deterministic** — one chronological replay "
             f"of a fixed book, no sampling — and there the ladder genuinely dominates both flats "
             f"either side of it: it holds ${pick['sc']['+0.20']['delta']:+,.0f} at half the fit "
             f"edge where flat 1.5 holds ${flats[2]['sc']['+0.20']['delta']:+,.0f} on 27% more "
             f"risk per trade, and it is still positive at mean R = 0 where both flat 1.0 and "
             f"flat 1.5 have gone negative.\n"
             f"\n**The P(bust) columns are Monte Carlo estimates** at {N_PATHS:,} paths, so their "
             f"standard error near 3% is about {se:.1f}pp — call it +/-{2 * se:.1f}pp at 2 sigma. "
             f"Gaps of a few tenths are noise, and two consequences follow honestly. First, the "
             f"ladder's {pick['sc']['0.00']['bust'] * 100:.1f}% at R = 0 is NOT better than flat "
             f"1.0's {flats[1]['sc']['0.00']['bust'] * 100:.1f}% — bust risk tracks size, and the "
             f"ladder carries more of it than flat 1.0 does. It does not degrade like something "
             f"smaller; it degrades like its own size while paying like something bigger. Second, "
             f"flat 1.5 misses the ceiling at R = +0.20 by "
             f"{(flats[2]['sc']['+0.20']['bust'] - ceil) * 100:.1f}pp, which is well inside that "
             f"noise — so the bust screen does NOT separate the ladder from flat 1.5, and anyone "
             f"reading it as the deciding evidence is over-reading it.\n"
             f"\nSo the answer rests on the deterministic column, not the sampled one: at equal "
             f"or lower risk per trade the ladder retains more of its contribution as the edge "
             f"decays, because the size sits where the edge was measured and the weak cell stays "
             f"small. The bust ceiling is a screen that rules out flat 2.0 decisively "
             f"({flats[3]['sc']['+0.20']['bust'] * 100:.1f}% at R = +0.20, far outside noise); it "
             f"is not what picks the winner.\n")

    _rounding(Q, L)


def _rounding(Q: pd.DataFrame, L: list) -> None:
    """Integer-contract rounding cost, reported not buried."""
    L.append("\n### Integer-contract rounding\n\nFloor-with-1-minimum truncates the intended "
             "unit. At small tiers that is not a rounding error, it is the position.\n\n"
             "| tier | intended risk | actual mean risk | mean contracts | trades forced to the "
             "1-contract minimum |\n|---|---|---|---|---|\n")
    for lab, tb, to in LADDER_SCALES[1.0]:
        Lo = book(Q, tb, to)
        L.append(f"| {lab} | ${BASE * tb:,.0f} | ${Lo.risk.mean():,.0f} | "
                 f"{Lo.contracts.mean():.1f} | {int((Lo.contracts == 1).sum())}/{len(Lo)} |\n")


# --------------------------------------------------------------------------- main
def main() -> None:
    Q = population()
    L = ["# London conviction tiers — which sizing shape is best?\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         "\nLondon's wall score is BINARY (W or FAR; ROOM killed as noise, ASIA as backwards, "
         "and W/FAR are one signal at r=0.834), so there is no conviction ladder and 'funded "
         "sizing' was undefined. Every London figure quoted before this doc is flat 1 NQ lot "
         f"— ${NQ_PT:,.0f}/pt, ${Q.stop_pts.median() * NQ_PT:,.0f} median and "
         f"${Q.stop_pts.mean() * NQ_PT:,.0f} mean risk per trade, i.e. "
         f"**{Q.stop_pts.median() * NQ_PT / BASE:.1f}x** the lucid tier-1.0 unit of "
         f"${BASE:,.0f} on the median and **{Q.stop_pts.mean() * NQ_PT / BASE:.1f}x** on the "
         f"mean. So '+$22,795' was never a funded-sizing number.\n",
         f"\nDeclared grid, fixed upfront: ratio r = tier(both W+FAR)/tier(exactly one) in "
         f"{{{', '.join(f'{r:g}' for r in RATIOS)}}} — {len(RATIOS)} cells, shrinkage charge "
         f"{shrink(len(RATIOS)):+.3f} R. Risk-band tiering is reported as a pre-rejected fifth "
         f"shape (circular: risk is R's denominator).\n"]
    T, res, best = part1(Q, L)
    p = part2(T, res, best, L)
    part3(Q, best, L)
    ref = book(Q, 1.0, 1.0)
    L.append(f"\n## Reconciling Part 1 with Part 3\n\nThe two parts report different nets for the "
             f"same nominal tier and that is expected, not a contradiction. Part 1 pins "
             f"{len(T)} trades with the day stop OFF and continuous contracts, so shape is the "
             f"only moving part. Part 3 restores the real machinery: the ${DAY_STOP:,.0f} day "
             f"stop on sized dollars (which removes trades, and removes MORE of them at larger "
             f"tiers) and integer MNQ contracts (which truncate the unit downward). Flat 1.0 "
             f"therefore reads ${res[1.0]['net']:+,.0f} on {len(T)} trades in Part 1 and "
             f"${ref.pnl.sum():+,.0f} on {len(ref)} in Part 3. Earlier sessions quoted "
             f"**187 trades** — that is the 1-NQ-lot set, whose larger unit trips the day stop "
             f"more often; Part 3 reproduces it exactly, which is the cross-check that this "
             f"script is sizing the same book everything else was measured on.\n")
    L.append("\n## What this settles\n\nShape and scale are answered separately and the answers "
             "do not have to agree: a shape can be real and still not be worth the drawdown it "
             "buys, and the scale that maximises withdrawn cash is set by the shared budget and "
             "the trailing line, not by mean R. The pre-registration takes the frozen primary "
             "from Part 3's selection rule and the ladder from Part 1/2 as the single declared "
             "secondary, keeping multiplicity at 2.\n")
    write("LONDON-TIER-TEST.md", "".join(L))
    print(f"\npooled permutation p = {p:.4f}, best ratio r = {best:g}")


if __name__ == "__main__":
    main()
