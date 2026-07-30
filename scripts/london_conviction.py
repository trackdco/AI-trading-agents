#!/usr/bin/env python3
"""LONDON conviction map — which taken trades deserve more size. FIT ONLY. Holdout sealed.

THE ASK (Brake, 2026-07-30): do for London what the NY canon did — distinguish an average
trade from a really good one, using order flow, and propose conviction tiers. NY's ladder is
0.25-2.25 off check-counts; London's book is wall-gated with a binary score, so conviction
has to come from the FEATURE MATRIX on top of taken trades, not from the gate.

BASELINE: the cut@09:30 book (Brake ruling 2026-07-30, recorded in
docs/LONDON-REV3-BASELINE.md — a RISK ruling, adopted knowing the late-bucket guard read
p=0.076). 144 trades / 85 days / +$21,801 / 62% WR / +0.630 mean R. The full 187-trade book
is carried as a robustness column throughout — a conviction signal that only works with the
late bucket in (or out) is fragile, and says so.

THIS IS A SIZING OVERLAY, NOT A GATE. Every cell below contains trades the book TAKES. The
standing ANGUS ruling ("no sizing until the validated volume is visible") means nothing here
ships now: the output is a declared conviction map + a candidate ladder, judged post-holdout
exactly like the tier test's 1.5/0.5 — against numbers written down before the sealed run.

DISCIPLINE (the burn list, applied):
  - Coverage-gate first (#6): features under 95% non-null on the book are excluded from the
    continuous sweep; the wall family enters only through W/FAR/both (wall_behind is
    structurally circular with W and stays out — fade-conviction precedent).
  - Era split before any claim (#1): every cell reports 2025 and 2026 separately; a cell
    whose effect flips sign across eras is dead on arrival whatever its pooled number.
  - Loss rate != expectancy (#2): every cell carries mean R next to WR; nothing is called
    good on WR alone.
  - Search breadth is paid for (#7): univariate p-values are charged worst-of-K across all
    K features tested (max-|lift| permutation null); pair cells are charged worst-of-K
    across all pairs. The two PRIOR cells from the prereg's "explicitly not asked" list
    (dep_resist>33 & ASIA==0; cvd_ASIA>737 & dep_wall_above_sz>5) were declared BEFORE this
    sweep, so they are charged at their own k=2 — that is the entire value of having
    written them down last week.
  - Min-cell floor: 25/era to CALL a result (project standard); cells 10-24/era are
    printed as HYPOTHESIS-GRADE; below 10/era not printed. On a 144-trade book almost
    every pair cell is hypothesis-grade — the doc says so rather than hiding it.

DIRECTION ADJUSTMENT: flow/geometry features are signed into the trade's frame first
(long: +feature; short: -feature) so "with-trade flow" means the same thing in both
directions. Features already direction-adjusted upstream (ent_vs_vwap_sd_dir) or
direction-free (dep_thick, rng_30, risk...) pass through. Wall-ahead uses above for longs,
below for shorts (= FAR's own convention).

LADDER: conviction score = count of surviving (era-consistent, floor-passing) conditions
true per trade. Tiers priced at matched total risk like the tier test, with the zero-edge
column that exposes risk-shuffling masquerading as edge.

    python -m scripts.london_conviction
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd, write  # noqa: F401
from scripts.london_holdout_report import load_pop

LON = "Europe/London"
NQ_PT = 20.0
SEED = 20260730
N_PERM = 5000
FLOOR_CALL, FLOOR_HYP = 25, 10          # per-era n to call / to print as hypothesis
CUT_MIN = 570                            # 09:30 London — Brake ruling, rev 3 baseline

# declared continuous feature set: (column, signed_into_trade_frame?)
FEATURES = [
    ("cvd_ASIA", True), ("cvd_ON_sofar", True),
    ("d5", True), ("d15", True), ("d30", True),
    ("fill_delta", True), ("deltaz_15", True), ("netpath_30", True),
    ("vwap_slope_30", True), ("dep_imb", True), ("dep_sup_m_res", True),
    ("ent_vs_vwap_sd_dir", False),        # already dir-adjusted upstream (loss anatomy)
    ("dep_resist", False), ("dep_support", False), ("dep_thick", False),
    ("dep_thick_d5m", False), ("dep_spread", False),
    ("churn_flow_30", False), ("indec_30", False), ("lvl_churn_30", False),
    ("rng_30", False), ("trigdens_30", False), ("vwap_cross_30", False),
    ("wicky_10", False), ("on_range", False), ("on_extreme_age", False),
    ("bbw_state", False), ("confluence_count", False), ("risk", False),
    ("fill_vol_rel", False), ("room_ahead", False),
]
CATEGORICALS = ["pattern", "kind", "htf_flag", "tf", "direction"]


def lonmins(s: pd.Series) -> pd.Series:
    f = pd.to_datetime(s, format="mixed", utc=True).dt.tz_convert(LON)
    return (f.dt.hour * 60 + f.dt.minute).values


def books() -> tuple[pd.DataFrame, pd.DataFrame]:
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    cut = lon_book(P[P.mins < CUT_MIN], floor=9.5, lifetime=math.inf, cap=999)
    full = lon_book(P, floor=9.5, lifetime=math.inf, cap=999)
    for b in (cut, full):
        long = b.direction.values == "long"
        b["room_ahead"] = np.where(long, 1 - b.ent_on_pos, b.ent_on_pos)
        b["wall_ahead_sz"] = np.where(long, b.dep_wall_above_sz, b.dep_wall_below_sz)
        b["both_wall"] = ((b.W == 1) & (b.FAR == 1)).astype(float)
    return cut, full


def signed(b: pd.DataFrame, col: str, sign_it: bool) -> np.ndarray:
    v = b[col].astype(float).values
    if sign_it:
        v = np.where(b.direction.values == "long", v, -v)
    return v


def cell_row(g: pd.DataFrame) -> dict:
    return {"n": len(g), "wr": float((g.R > 0).mean()) if len(g) else np.nan,
            "r": float(g.R.mean()) if len(g) else np.nan,
            "net": float(g.dollars.sum())}


def wilson_lb(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return np.nan
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    rad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - rad) / denom


def era_cells(b: pd.DataFrame, mask: np.ndarray) -> dict:
    out = {"pool": cell_row(b[mask])}
    for era in ("2025", "2026"):
        out[era] = cell_row(b[mask & (b.era == era).values])
    g = b[mask]
    out["wilson"] = wilson_lb(int((g.R > 0).sum()), len(g))
    return out


def perm_max_null(R: np.ndarray, eras: np.ndarray, masks: np.ndarray,
                  rng: np.random.Generator) -> np.ndarray:
    """For each shuffle (R permuted WITHIN era), the max |mean R in cell - mean R overall|
    across all cells — the worst-of-K distribution every observed lift is charged against."""
    n, k = masks.shape
    counts = masks.sum(axis=0)
    overall = R.mean()
    idx25, idx26 = np.where(eras == "2025")[0], np.where(eras == "2026")[0]
    out = np.empty(N_PERM)
    Rp = R.copy()
    for i in range(N_PERM):
        Rp[idx25] = R[idx25][rng.permutation(len(idx25))]
        Rp[idx26] = R[idx26][rng.permutation(len(idx26))]
        cell_means = (masks.T @ Rp) / np.where(counts > 0, counts, 1)
        out[i] = np.abs(cell_means - Rp.mean()).max() if k else 0.0
    return out


def fmt_cell(c: dict) -> str:
    def one(e):
        d = c[e]
        if d["n"] == 0:
            return "—"
        return f"{d['n']}/{d['wr'] * 100:.0f}%/{d['r']:+.2f}"
    return (f"{c['pool']['n']} | {c['pool']['wr'] * 100:.0f}% | {c['pool']['r']:+.3f} | "
            f"{c['wilson'] * 100:.0f}% | {one('2025')} | {one('2026')}")


def grade(c: dict) -> str:
    n25, n26 = c["2025"]["n"], c["2026"]["n"]
    if min(n25, n26) >= FLOOR_CALL:
        return "CALLABLE"
    if min(n25, n26) >= FLOOR_HYP:
        return "hypothesis"
    return "below-floor"


def main() -> None:
    rng = np.random.default_rng(SEED)
    cut, full = books()
    b = cut.reset_index(drop=True)
    R = b.R.values.astype(float)
    eras = b.era.values
    base = {"pool": cell_row(b), "2025": cell_row(b[b.era == "2025"]),
            "2026": cell_row(b[b.era == "2026"])}

    L = ["# London conviction map — grading the taken trades (cut@09:30 baseline)\n",
         "\n**FIT ONLY. Sealed 2023/24 untouched. Sizing overlay, not a gate — nothing "
         "here ships before the holdout validates the book and Angus lifts the flat-1-lot "
         "ruling.** Full-book (187) robustness column included throughout; a cell that "
         "only works on one baseline is labelled fragile.\n",
         f"\nBaseline: **{base['pool']['n']} trades, WR {base['pool']['wr'] * 100:.0f}%, "
         f"mean R {base['pool']['r']:+.3f}** "
         f"(2025: {base['2025']['n']}/{base['2025']['wr'] * 100:.0f}%/"
         f"{base['2025']['r']:+.2f} · 2026: {base['2026']['n']}/"
         f"{base['2026']['wr'] * 100:.0f}%/{base['2026']['r']:+.2f}). Cell format: "
         "n | WR | mean R | Wilson-95 LB on WR | per-era n/WR/R.\n"]

    # ---------------- 1. prior cells, declared before this sweep (charged at k=2)
    L.append("\n## 1. The two PRIOR cells (declared in prereg §3 before this sweep — "
             "charged at their own k=2, not at today's breadth)\n\n"
             "| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |\n"
             "|---|---|---|---|---|---|---|---|\n")
    priors = {
        "dep_resist>33 & ASIA==0": (b.dep_resist.values > 33) & (b.ASIA.values == 0),
        "cvd_ASIA>737 & wall_above_sz>5":
            (b.cvd_ASIA.values > 737) & (b.dep_wall_above_sz.fillna(0).values > 5),
    }
    for name, m in priors.items():
        c = era_cells(b, m)
        L.append(f"| {name} | {fmt_cell(c)} | {grade(c)} |\n")
    L.append("\n(Thresholds verbatim from the L3 trial via prereg §3 — raw columns, not "
             "direction-adjusted, exactly as originally declared.)\n")

    # ---------------- 2. univariate sweep, worst-of-K charged
    usable = [(f, s) for f, s in FEATURES if b[f].notna().mean() >= 0.95]
    dropped = [f for f, _ in FEATURES if b[f].notna().mean() < 0.95]
    masks, uni = [], []
    for f, s in usable:
        v = signed(b, f, s)
        med = np.nanmedian(v)
        hi = v > med
        masks.append(hi)
        uni.append((f, s, med, hi))
    M = np.column_stack([m.astype(float) for m in masks])
    null_max = perm_max_null(R, eras, M, rng)

    L.append(f"\n## 2. Univariate sweep — {len(usable)} declared features, split at the "
             f"book median, hi-cell vs book\n\nEvery p below is CORRECTED: the observed "
             f"lift is compared to the distribution of the WORST lift across all "
             f"{len(usable)} features under within-era outcome shuffles (N={N_PERM}). "
             f"Coverage-dropped (<95%): {', '.join(dropped)}.\n\n"
             "| feature (hi half) | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | "
             "p(worst-of-K) | era-consistent | grade |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
    rows = []
    for f, s, med, hi in uni:
        c = era_cells(b, hi)
        lift = c["pool"]["r"] - base["pool"]["r"]
        p = float((null_max >= abs(lift)).mean())
        l25 = c["2025"]["r"] - base["2025"]["r"]
        l26 = c["2026"]["r"] - base["2026"]["r"]
        cons = bool(np.sign(l25) == np.sign(l26)) and abs(lift) > 0
        rows.append((f, s, med, hi, c, lift, p, cons))
    rows.sort(key=lambda r: -r[5])
    for f, s, med, hi, c, lift, p, cons in rows:
        L.append(f"| {f}{' (signed)' if s else ''} | {fmt_cell(c)} | {lift:+.3f} | "
                 f"{p:.3f} | {'YES' if cons else 'no'} | {grade(c)} |\n")

    # ---------------- 3. pair cells among era-consistent positive univariates
    elig = [(f, s, med, hi) for f, s, med, hi, c, lift, p, cons in rows
            if cons and lift > 0]
    pair_masks, pair_names = [], []
    for i in range(len(elig)):
        for j in range(i + 1, len(elig)):
            m = elig[i][3] & elig[j][3]
            if m.sum() >= FLOOR_HYP * 2:
                pair_masks.append(m)
                pair_names.append(f"{elig[i][0]} & {elig[j][0]}")
    if pair_masks:
        MP = np.column_stack([m.astype(float) for m in pair_masks])
        null_pair = perm_max_null(R, eras, MP, rng)
    L.append(f"\n## 3. Pair cells — hi&hi among the {len(elig)} era-consistent positive "
             f"features ({len(pair_masks)} pairs with pooled n>={FLOOR_HYP * 2}; charged "
             f"worst-of-{len(pair_masks)})\n\n"
             "| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | p(worst-of-K) | "
             "grade |\n|---|---|---|---|---|---|---|---|---|---|\n")
    pair_rows = []
    for name, m in zip(pair_names, pair_masks):
        c = era_cells(b, m)
        lift = c["pool"]["r"] - base["pool"]["r"]
        p = float((null_pair >= abs(lift)).mean())
        pair_rows.append((name, m, c, lift, p))
    pair_rows.sort(key=lambda r: -r[3])
    for name, m, c, lift, p in pair_rows[:20]:
        L.append(f"| {name} | {fmt_cell(c)} | {lift:+.3f} | {p:.3f} | {grade(c)} |\n")
    if len(pair_rows) > 20:
        L.append(f"\n({len(pair_rows) - 20} further pairs computed and charged in the "
                 "null; only the top 20 by lift printed.)\n")

    # ---------------- 4. categorical splits (descriptive)
    L.append("\n## 4. Categorical splits (descriptive — no inference, tiny cells)\n")
    for cat in CATEGORICALS:
        L.append(f"\n**{cat}**\n\n| value | n | WR | mean R | 2025 | 2026 |\n"
                 "|---|---|---|---|---|---|\n")
        for val, g in b.groupby(cat):
            if len(g) < 5:
                continue
            c = era_cells(b, (b[cat] == val).values)
            L.append(f"| {val} | {c['pool']['n']} | {c['pool']['wr'] * 100:.0f}% | "
                     f"{c['pool']['r']:+.3f} | "
                     f"{c['2025']['n']}/{c['2025']['wr'] * 100:.0f}%/{c['2025']['r']:+.2f} | "
                     f"{c['2026']['n']}/{c['2026']['wr'] * 100:.0f}%/{c['2026']['r']:+.2f} |\n")

    # ---------------- 5. the wall split (the one prior conviction axis already validated)
    L.append("\n## 5. The wall split on this baseline (tier-test axis, re-anchored to "
             "cut@09:30)\n\n| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |\n"
             "|---|---|---|---|---|---|---|---|\n")
    for name, m in [("both W+FAR", (b.both_wall == 1).values),
                    ("exactly one", (b.both_wall == 0).values)]:
        c = era_cells(b, m)
        L.append(f"| {name} | {fmt_cell(c)} | {grade(c)} |\n")

    # ---------------- 6. conviction score + ladder pricing at matched risk
    survivors = [(f, s, med, hi) for f, s, med, hi, c, lift, p, cons in rows
                 if cons and lift > 0 and grade(c) == "CALLABLE"]
    L.append(f"\n## 6. Conviction score — count of surviving conditions "
             f"({len(survivors)} CALLABLE era-consistent positive: "
             f"{', '.join(f for f, *_ in survivors) or 'none'}) + both-wall\n\n")
    score = b.both_wall.values.copy()
    for f, s, med, hi in survivors:
        score = score + hi.astype(float)
    b["conv"] = score
    L.append("| score | n | WR | mean R | net | 2025 | 2026 |\n|---|---|---|---|---|---|---|\n")
    for sc, g in b.groupby("conv"):
        c = era_cells(b, (b.conv == sc).values)
        L.append(f"| {int(sc)} | {c['pool']['n']} | {c['pool']['wr'] * 100:.0f}% | "
                 f"{c['pool']['r']:+.3f} | ${c['pool']['net']:+,.0f} | "
                 f"{c['2025']['n']}/{c['2025']['wr'] * 100:.0f}%/{c['2025']['r']:+.2f} | "
                 f"{c['2026']['n']}/{c['2026']['wr'] * 100:.0f}%/{c['2026']['r']:+.2f} |\n")

    # ladder pricing: weights proportional to tier, scaled to the SAME total risk as flat
    L.append("\n### Ladder pricing at matched total risk (flat book risk = the budget)\n\n"
             "Zero-edge column = same weights applied to outcome-shuffled trades (mean of "
             f"{N_PERM} within-era shuffles): a ladder must beat flat on REAL outcomes by "
             "more than it does on shuffled ones, or it is just risk-shuffling.\n\n"
             "| ladder | net | maxDD (trade) | net/maxDD | zero-edge net |\n"
             "|---|---|---|---|---|\n")
    risk = b.risk.values.astype(float)
    total_risk = risk.sum()
    tiers = sorted(b.conv.unique())
    ladders = {"flat 1.0": np.ones(len(b))}
    if len(tiers) > 1:
        lo, hi_t = tiers[0], tiers[-1]
        w = 0.5 + 1.5 * (b.conv.values - lo) / (hi_t - lo)     # 0.5 .. 2.0 like NY
        ladders["0.5-2.0 by score"] = w
        ladders["1.5/0.5 both-wall only"] = np.where(b.both_wall.values == 1, 1.5, 0.5)
    dollars = b.dollars.values.astype(float)
    idx25 = np.where(eras == "2025")[0]
    idx26 = np.where(eras == "2026")[0]
    order = np.lexsort((b.fill_ts.values, b.day.values))
    for name, w in ladders.items():
        wn = w * total_risk / (w * risk).sum()                 # matched deployed risk
        pnl = dollars * wn
        ze = np.empty(N_PERM)
        dp = dollars.copy()
        rng2 = np.random.default_rng(SEED + 1)
        for i in range(N_PERM):
            dp[idx25] = dollars[idx25][rng2.permutation(len(idx25))]
            dp[idx26] = dollars[idx26][rng2.permutation(len(idx26))]
            ze[i] = (dp * wn).sum()
        eq = pd.Series(pnl[order])
        L.append(f"| {name} | ${pnl.sum():+,.0f} | ${maxdd(eq):,.0f} | "
                 f"{pnl.sum() / max(maxdd(eq), 1):.1f} | ${ze.mean():+,.0f} |\n")

    # ---------------- 7. robustness: does the picture survive on the full 187 book?
    L.append("\n## 7. Robustness — same survivors measured on the FULL 08:00-10:00 book\n\n"
             "| condition | cut book (n/WR/R) | full book (n/WR/R) | fragile? |\n"
             "|---|---|---|---|\n")
    fullb = full.reset_index(drop=True)
    for f, s, med, hi in survivors:
        vf = signed(fullb, f, s)
        hif = vf > med                                          # SAME threshold, not re-fit
        gc, gf = b[hi], fullb[hif]
        frag = "yes" if np.sign(gf.R.mean() - fullb.R.mean()) != np.sign(
            gc.R.mean() - b.R.mean()) else "no"
        L.append(f"| {f} hi | {len(gc)}/{(gc.R > 0).mean() * 100:.0f}%/{gc.R.mean():+.2f} | "
                 f"{len(gf)}/{(gf.R > 0).mean() * 100:.0f}%/{gf.R.mean():+.2f} | {frag} |\n")

    L.append("\n## Read this before quoting any cell\n\n"
             "- 144 trades split four ways is 30-40 per cell POOLED — nearly every pair "
             "cell is hypothesis-grade by the project's own 25/era floor. A 70% WR on n=30 "
             "carries a Wilson-95 lower bound near 52%. The map is for DECLARING priors "
             "the holdout and forward data can judge, not for claiming edges today.\n"
             "- Sizing is frozen at flat 1 lot (ANGUS ruling) until the holdout validates "
             "the book. The ladder above is the declared candidate for the post-holdout "
             "sizing decision, alongside the tier test's 1.5/0.5.\n"
             "- This sweep consumed fit-side search breadth and was charged for it; "
             "worst-of-K nulls on a 144-trade book are brutal, and that is correct.\n")
    write("LONDON-CONVICTION-SWEEP.md", "".join(L))


if __name__ == "__main__":
    main()
