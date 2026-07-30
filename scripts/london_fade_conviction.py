#!/usr/bin/env python3
"""LONDON deep fades — does order flow tell you WHICH one reverses? FIT ONLY. Holdout sealed.

The deep counter-VWAP fades (long well below the day's VWAP, short well above) are a near coin
flip: n=73, 44% win, but net POSITIVE because the winners snap back hard. Angus's question: is
there a confluence — order-flow strength AT the extreme — that separates the fades that reverse
from the ones that keep going? The mechanism: a long stabbed in far below value should be more
likely to bounce if someone is actually DEFENDING the low (thick bid, positive delta, buyers
absorbing) rather than if it is falling into a vacuum.

So every confluence here is DIRECTION-ADJUSTED to mean "strength in the trade's favour at entry":
  imb_dir      book imbalance toward the trade side (bids for a long, asks for a short)
  supmres_dir  support-minus-resist depth, already dir-adjusted in london_depth
  support_sz   raw support-side depth at entry
  thick_build  book thickening over the last 5 min (dep_thick_d5m) — defence arriving
  wall_behind  size of the wall BEHIND the entry (the level being defended)
  cvd_dir      session cumulative delta in the trade direction (net buying for a long)
  filldelta_dir  signed delta right at the fill minute — immediate absorption
  d15_dir/d30_dir  signed delta over the last 15 / 30 min

POWER WARNING, up front and non-negotiable. This is a subset of a subset (73 trades), mined
in-sample, across ~10 flow features. Bonferroni here is p<0.005 and almost nothing will clear it;
that is EXPECTED and is not a reason to relax the bar. The output is a ranked list of leads with
honest p-values and a conviction composite, to be CONFIRMED on the sealed holdout — not a filter
to switch on. A composite built and evaluated on the same 73 trades is the most overfit object in
this whole project; it is shown with that label attached.

    python -m scripts.london_fade_conviction
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, lon_pop, write  # noqa: E402

SEED = 20260730
N_PERM = 5000
DEEP = -0.25            # "deep fade" = dir-adj entry-vs-VWAP below this
MIN_COV = 40            # a feature needs this many non-null rows in the subset to be readable
DOCS = ROOT / "docs"


def auc(x: np.ndarray, win: np.ndarray) -> float:
    s = pd.Series(x)
    ranks = s.rank(method="average").values
    nw, nl = int(win.sum()), int((~win).sum())
    if nw == 0 or nl == 0:
        return float("nan")
    return float((ranks[win].sum() - nw * (nw + 1) / 2) / (nw * nl))


def sep(x: np.ndarray, win: np.ndarray, rng) -> tuple:
    m = ~np.isnan(x)
    x, win = x[m], win[m]
    a = auc(x, win)
    obs = abs(a - 0.5)
    null = np.array([abs(auc(x, rng.permutation(win)) - 0.5) for _ in range(N_PERM)])
    return a, float((null >= obs).mean()), int(m.sum())


def build_flow(t: pd.DataFrame) -> pd.DataFrame:
    sgn = np.where(t.direction.values == "long", 1.0, -1.0)
    long = t.direction.values == "long"
    f = pd.DataFrame(index=t.index)
    f["imb_dir"] = t.dep_imb.values * sgn
    f["supmres_dir"] = t.dep_sup_m_res.values.astype(float)     # already dir-adjusted
    f["support_sz"] = t.dep_support.values.astype(float)
    f["thick_build"] = t.dep_thick_d5m.values.astype(float)
    f["wall_behind"] = np.where(long, t.dep_wall_below_sz.values, t.dep_wall_above_sz.values)
    f["cvd_dir"] = t.cvd_ON_sofar.values * sgn
    f["filldelta_dir"] = t.fill_delta.values * sgn
    f["d15_dir"] = t.d15.values * sgn
    f["d30_dir"] = t.d30.values * sgn
    return f


NAMES = {
    "imb_dir": "book imbalance toward trade",
    "supmres_dir": "support - resist depth",
    "support_sz": "support-side depth (raw)",
    "thick_build": "book thickening, 5-min",
    "wall_behind": "wall size behind entry",
    "cvd_dir": "session CVD in trade dir",
    "filldelta_dir": "delta at fill (absorption)",
    "d15_dir": "signed delta, 15-min",
    "d30_dir": "signed delta, 30-min",
}
# pre-declared composite: three DISTINCT lenses on 'strength in my favour', not nine correlated
# ones. Depth (imbalance), session flow (CVD), immediate absorption (fill delta).
COMPOSITE = ["imb_dir", "cvd_dir", "filldelta_dir"]


def main() -> None:
    P = lon_pop()
    t = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).copy()
    t["dir"] = t.ent_vs_vwap_sd_dir
    t["era"] = pd.to_datetime(t.day).dt.year.astype(str)
    t["win"] = t.R > 0
    d = t[t.dir < DEEP].copy().reset_index(drop=True)
    F = build_flow(d)
    win = d.win.values
    rng = np.random.default_rng(SEED)
    # COVERAGE GATE, applied BEFORE the Bonferroni bar is quoted so the bar matches the tests
    # actually run. `wall_behind` is non-null on only 2 of these 73 trades and returned a
    # degenerate AUC of 1.000 off one winner and one loser — an artifact, and a structural one:
    # London's W check IS "no wall behind the entry", so a taken trade almost never has one and
    # scoring its size would be circular.
    covn = {c: int(F[c].notna().sum()) for c in NAMES}
    usable = [c for c in NAMES if covn[c] >= MIN_COV]
    excluded = [c for c in NAMES if covn[c] < MIN_COV]
    bonf = len(usable)

    L = ["# London deep fades — can order flow give conviction on which reverses?\n",
         "\n**Fit only. Sealed 2023/24 never loaded. Subset-of-a-subset mining — "
         "hypothesis generation, not a filter.**\n",
         f"\nDeep fade = direction-adjusted entry-vs-VWAP below {DEEP:g} (long well below the "
         f"day's VWAP, short well above). **{len(d)} trades, {win.mean() * 100:.0f}% win, "
         f"${d.dollars.sum():+,.0f}, mean R {d.R.mean():+.3f}** — the near-coin-flip bucket the "
         f"VWAP filter would drop. The question is whether flow strength at the extreme sorts the "
         f"reversals from the continuations.\n",
         f"\n**How to read it.** AUC = P(the confluence ranks higher on a reverting/winning fade "
         f"than a losing one); 0.5 is nothing, >0.5 means MORE strength predicts the reversal "
         f"(the hypothesis). {N_PERM:,}-shuffle permutation p. With {bonf} features the Bonferroni "
         f"bar is p<{0.05 / bonf:.4f}. **n is ~{int(win.sum())} winners / {int((~win).sum())} "
         f"losers, so power is low by construction** — expect few or zero survivors, and read a "
         f"clean p as a lead to test on the holdout, never as a switch to flip.\n"]

    if excluded:
        L.append("\n**Excluded for coverage** (fewer than "
                 f"{MIN_COV} of {len(d)} rows carry the feature, so no honest read is possible): "
                 + ", ".join(f"`{c}` ({covn[c]}/{len(d)})" for c in excluded)
                 + ". `wall_behind` in particular is structural, not bad luck — London's W check "
                   "IS 'no wall behind the entry', so a taken trade almost never has one, and "
                   "scoring its size would be circular.\n")

    # per-feature separation within the deep-fade subset
    L.append("\n## Does strength-at-the-extreme separate the reversals?\n\n"
             "| confluence (dir-adjusted) | n | loser med | winner med | AUC | perm p | "
             "Bonferroni | reverse-rate low / high |\n|---|---|---|---|---|---|---|---|\n")
    rows = []
    for c in usable:
        x = F[c].values.astype(float)
        a, p, n = sep(x, win, rng)
        m = ~np.isnan(x)
        xl, xw = x[m & ~win], x[m & win]
        # median split within the subset -> reversal (win) rate in the low vs high half
        med = np.nanmedian(x)
        lo = win[m & (x <= med)]
        hi = win[m & (x > med)]
        rows.append(dict(c=c, a=a, p=p, n=n,
                         lmed=float(np.median(xl)) if len(xl) else float("nan"),
                         wmed=float(np.median(xw)) if len(xw) else float("nan"),
                         lo=float(lo.mean()) if len(lo) else float("nan"),
                         hi=float(hi.mean()) if len(hi) else float("nan")))
    for r in sorted(rows, key=lambda r: abs(r["a"] - 0.5), reverse=True):
        passb = "**yes**" if r["p"] < 0.05 / bonf else ("borderline" if r["p"] < 0.05 else "no")
        arrow = "strength->reversal" if r["a"] > 0.5 else "strength->continuation"
        L.append(f"| {NAMES[r['c']]} | {r['n']} | {r['lmed']:.2f} | {r['wmed']:.2f} | "
                 f"{r['a']:.3f} ({arrow}) | {r['p']:.3f} | {passb} | "
                 f"{r['lo'] * 100:.0f}% / {r['hi'] * 100:.0f}% |\n")

    # composite conviction score
    comp = [c for c in COMPOSITE if c in usable]
    Z = pd.DataFrame({c: (F[c] - F[c].mean()) / F[c].std(ddof=0) for c in comp})
    conv = Z.mean(axis=1, skipna=True).values     # mean of available z-scores
    cov = ~np.isnan(conv)
    a_c, p_c, _ = sep(conv, win, rng)
    L.append(f"\n## Conviction composite (the most overfit object in the project — labelled as "
             f"such)\n\n"
             f"Mean z-score of three DISTINCT strength lenses — "
             f"{', '.join(NAMES[c] for c in comp)} — built AND scored on the same {len(d)} "
             f"trades. AUC {a_c:.3f}, perm p {p_c:.3f}. Reversal rate and net by composite "
             f"tercile:\n\n"
             "| conviction | trades | reverse rate | mean R | net $ |\n|---|---|---|---|---|\n")
    dd = d[cov].copy()
    dd["conv"] = conv[cov]
    dd["q"] = pd.qcut(dd.conv, 3, labels=["low", "mid", "high"], duplicates="drop")
    for k, g in dd.groupby("q", observed=True):
        L.append(f"| {k} | {len(g)} | {(g.R > 0).mean() * 100:.0f}% | {g.R.mean():+.3f} | "
                 f"${g.dollars.sum():+,.0f} |\n")

    # conditional filter: keep only the high-conviction half of the deep fades. Guard vs random.
    hi_mask = cov & (conv > np.nanmedian(conv))
    kept, drop = d[hi_mask], d[cov & ~(conv > np.nanmedian(conv))]
    Khi = int(hi_mask.sum())
    # random guard: pick Khi random deep fades, how often does the random half's net beat this?
    idx = np.flatnonzero(cov)
    obs_net = float(kept.dollars.sum())
    null = np.array([d.dollars.values[rng.choice(idx, Khi, replace=False)].sum()
                     for _ in range(N_PERM)])
    p_net = float((null >= obs_net).mean())
    L.append(f"\n### If you took only the high-conviction half of the deep fades\n\n"
             f"| | trades | reverse rate | mean R | net $ |\n|---|---|---|---|---|\n"
             f"| high-conviction half (kept) | {len(kept)} | {(kept.R > 0).mean() * 100:.0f}% | "
             f"{kept.R.mean():+.3f} | ${kept.dollars.sum():+,.0f} |\n"
             f"| low-conviction half (dropped) | {len(drop)} | {(drop.R > 0).mean() * 100:.0f}% | "
             f"{drop.R.mean():+.3f} | ${drop.dollars.sum():+,.0f} |\n"
             f"\nRandom-half guard ({N_PERM:,} draws): the high-conviction half nets "
             f"${obs_net:+,.0f} vs a random half's median ${np.median(null):+,.0f} "
             f"(p={p_net:.4f}). "
             + ("Beats a random split — the composite is sorting something real on THIS data.\n"
                if p_net < 0.05 else
                "Does not clearly beat a random split of the same size — the composite is not "
                "demonstrably sorting the fades on this data.\n"))

    # per-era stability of the best single lead
    best = max(rows, key=lambda r: abs(r["a"] - 0.5))
    L.append(f"\n## Per-era check on the strongest single lead ({NAMES[best['c']]})\n\n")
    for e in ("2025", "2026"):
        ge = d[d.era == e]
        xe = build_flow(ge)[best["c"]].values.astype(float)
        we = ge.win.values
        m = ~np.isnan(xe)
        if m.sum() >= 10:
            L.append(f"- **{e}**: n={int(m.sum())}, AUC {auc(xe[m], we[m]):.3f}\n")
        else:
            L.append(f"- **{e}**: n={int(m.sum())} — too few to read\n")

    L.append("\n## Verdict\n\n")
    passed = [r for r in rows if r["p"] < 0.05 / bonf]
    borderl = [r for r in rows if 0.05 / bonf <= r["p"] < 0.05]
    if passed:
        L.append("Clears Bonferroni even at this small n (a strong lead): "
                 + ", ".join(f"**{NAMES[r['c']]}** (AUC {r['a']:.2f}, p {r['p']:.3f})"
                             for r in passed) + ".\n")
    else:
        L.append(f"**Nothing clears Bonferroni** — expected at n={len(d)}. ")
    if borderl:
        L.append("Directional leads worth carrying to the holdout (p<0.05 raw, not corrected): "
                 + ", ".join(f"{NAMES[r['c']]} (AUC {r['a']:.2f}, {'strength->reversal' if r['a']>0.5 else 'strength->continuation'}, p {r['p']:.3f})"
                             for r in borderl) + ".\n")
    L.append(f"\n**On the mechanism:** the direction of the tilt is what matters more than any one "
             f"p-value here. If the strength lenses point 'more strength -> higher reversal rate' "
             f"(AUC>0.5), Angus's intuition is at least consistent with the fit data and deserves "
             f"a pre-registered holdout test: a deep-fade is only taken when flow confirms someone "
             f"is defending the extreme. If they point the other way, the deep fades that reverse "
             f"are the ones flow had ALREADY given up on — a squeeze, not absorption — and the "
             f"conviction story is wrong. Read the AUC arrows above for which world we are in.\n")
    write("LONDON-FADE-CONVICTION.md", "".join(L))
    print(f"deep fades n={len(d)}, win {win.mean():.0%}; best lead "
          f"{best['c']} AUC {best['a']:.3f} p {best['p']:.3f}; "
          f"composite AUC {a_c:.3f} p {p_c:.3f}; hi-half net-guard p {p_net:.4f}")


if __name__ == "__main__":
    main()
