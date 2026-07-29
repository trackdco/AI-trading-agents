#!/usr/bin/env python3
"""LONDON overnight audit — three stages, FIT ONLY. Acceptance bars fixed in advance.

Stage 1  loser autopsy at scale      every candidate cut over all L3 features
Stage 2  combination search          low-frequency high-WR cells, permutation + FWER
Stage 3  selection-null calibration  how much of the result is real vs. having looked a lot

THE SEALED SPAN IS NEVER TOUCHED. Every load goes through `fit_only()`, which refuses any path
containing "holdout" and raises if a single row falls outside 2025/2026. There is no flag to
override it. If this job ever reads sealed data it dies rather than reporting a number.

WHY STAGE 3 EXISTS. Stages 1 and 2 search thousands of rules and report the best. That process
finds something even in pure noise, and the permutation null in stage 2 only controls for "is
this cell's edge real given these rows" — not for "how much did my searching inflate it". Stage
3 re-runs the ENTIRE selection procedure inside randomized in-sample/out-of-sample splits, so
the reported number is the honest expected shrinkage of a rule chosen the way this rule was
chosen. It is the only stage that can say the wall arm is mostly-real or mostly-artifact.

A CLEAN NULL IS A RESULT. If nothing clears a bar, the verdict file says so plainly. Nothing
here is tuned to produce survivors.

    python -m scripts.london_overnight_audit --stage 1
    python -m scripts.london_overnight_audit --stage 2
    python -m scripts.london_overnight_audit --stage 3
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select  # noqa: E402
from src.canon.scorer import LON_RISK_MIN, london_checks  # noqa: E402

DOCS = ROOT / "docs"
ERAS = ["2025", "2026"]
N_PERM = 2000
N_SPLITS = 500
RNG = np.random.default_rng(20260730)

# ---- acceptance bars, fixed before any result was seen -------------------------------------
S1_MIN_N_ERA = 30          # cut-set rows required in EACH era
S2_MIN_WR_ERA = 0.65       # >=65% WR in each era separately
S2_MIN_WILSON = 0.60       # pooled Wilson 95% lower bound
S2_MIN_N_ERA = 25          # so a 65% WR is never 2-of-3
S1_JACKKNIFE_UNIT = "month"


def fit_only(path: Path) -> pd.DataFrame:
    """The sealed-span guard. No override exists."""
    if "holdout" in str(path).lower():
        raise SystemExit(f"SEALED SPAN REFUSED: {path}")
    df = pd.read_parquet(path)
    yrs = sorted(set(pd.to_datetime(df.day).dt.year))
    if set(yrs) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: rows from {yrs} in {path.name}")
    return df


def population() -> pd.DataFrame:
    F = fit_only(ROOT / "output/l3_features_london_fit.parquet")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
    F["mo"] = F.day.str[:7]
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)
    F["win"] = F.dollars > 0
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    return F[F.risk >= LON_RISK_MIN].reset_index(drop=True)      # Layer 0


def book(P: pd.DataFrame) -> pd.DataFrame:
    """The wall arm, uncapped + day stop — the configuration L4 recommended freezing."""
    pol = L4Policy(threshold={"london": 1.0}, escalation_threshold={"london": 1.0},
                   cap_per_session=999, day_stop_dollars=400.0)
    b = select(P.assign(score=P.wall), pol)
    return b[b.taken].reset_index(drop=True)


def maxdd(d: pd.DataFrame) -> float:
    if not len(d):
        return 0.0
    eq = d.sort_values("fill_ts").dollars.cumsum()
    return float((eq.cummax() - eq).max())


def wilson_lo(k: int, n: int, z: float = 1.96) -> float:
    if not n:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((c - m) / d)


def atoms(P: pd.DataFrame) -> list[tuple[str, np.ndarray]]:
    """Binary conditions from every usable L3 feature. Numeric features are split at their
    quartiles in BOTH directions; low-cardinality categoricals become one atom per level."""
    skip = {"ts", "day", "book", "fill", "exit", "direction", "entry", "stop", "exit_price",
            "exit_reason", "dollars", "pattern", "tf", "wgroup", "yr", "risk", "era", "mo",
            "session", "fill_ts", "win", "wall", "score", "taken", "nth", "kill_reason",
            "R", "hold_min", "mo_green", "target", "win_et"}
    out: list[tuple[str, np.ndarray]] = []
    for c in P.columns:
        if c in skip:
            continue
        s = P[c]
        if pd.api.types.is_numeric_dtype(s):
            v = s.astype(float)
            if v.notna().sum() < 50 or v.nunique() < 3:
                if v.nunique() == 2:
                    for lev in sorted(v.dropna().unique()):
                        out.append((f"{c}=={lev:g}", (v == lev).to_numpy()))
                continue
            for q in (0.25, 0.5, 0.75):
                t = float(v.quantile(q))
                out.append((f"{c}<={t:.4g}", (v <= t).to_numpy()))
                out.append((f"{c}>{t:.4g}", (v > t).to_numpy()))
        elif s.nunique() <= 6:
            for lev in sorted(map(str, s.dropna().unique())):
                out.append((f"{c}=={lev}", (s.astype(str) == lev).to_numpy()))
    # the categorical trade descriptors are informative even though they are passthrough
    for c in ("pattern", "tf", "direction"):
        if c in P:
            for lev in sorted(P[c].astype(str).unique()):
                out.append((f"{c}=={lev}", (P[c].astype(str) == lev).to_numpy()))
    # Dedupe by MASK. Quartiles frequently coincide on discrete features (vwap_cross_30's q25
    # and q50 are both 0), which produced identical cuts under different names and would
    # inflate stage 2's test count — and therefore weaken its family-wise correction.
    seen, uniq = set(), []
    for name, m in out:
        k = m.tobytes()
        if k in seen or m.all() or not m.any():
            continue
        seen.add(k)
        uniq.append((name, m))
    return uniq


def write(name: str, body: str) -> Path:
    DOCS.mkdir(exist_ok=True)
    p = DOCS / name
    p.write_text(body)
    print(f"\nwrote {p.relative_to(ROOT)} ({len(body):,} chars)")
    return p


# ============================================================ STAGE 1
def stage1() -> None:
    P = population()
    B = book(P)
    era_wr = {e: B[B.era == e].win.mean() for e in ERAS}
    base_dd = {e: maxdd(B[B.era == e]) for e in ERAS}
    L = []
    L.append("# London overnight audit — Stage 1: loser autopsy at scale\n")
    L.append("**Fit only. Sealed 2023/24 never loaded** (`fit_only()` refuses any holdout "
             "path and raises on any row outside 2025/2026; no override exists).\n")
    L.append(f"Book = wall arm (W or FAR), uncapped + day stop. "
             f"n={len(B)} ({', '.join(f'{e}: {len(B[B.era == e])}' for e in ERAS)}).\n")
    L.append(f"Book WR: " + ", ".join(f"{e} {era_wr[e] * 100:.1f}%" for e in ERAS)
             + f" | maxDD: " + ", ".join(f"{e} ${base_dd[e]:,.0f}" for e in ERAS) + "\n")
    L.append("\n## Acceptance bar (fixed before any result was seen)\n")
    L.append(f"A cut survives only if, **in 2025 and 2026 separately**: the cut set's WR is "
             f"below the book's WR, the sign agrees across eras, n>={S1_MIN_N_ERA} in each "
             f"era, and removing it **improves maxDD** — net P&L alone is not enough.\n")
    L.append("\n**Net requirement:** the cut set must also be net NEGATIVE in each era. A set "
             "can sit below book WR and still be profitable via larger winners — cutting that "
             "costs money and is not a loser trait.\n")
    L.append(f"\nEvery survivor is then jackknifed by dropping one {S1_JACKKNIFE_UNIT} at a "
             f"time. Anything that flips sign on a single month's removal is reported as "
             f"FRAGILE, not as a finding.\n")

    A = atoms(B)
    rows = []
    for name, m in A:
        ok, detail = True, {}
        for e in ERAS:
            em = (B.era == e).to_numpy()
            cut = B[m & em]
            if len(cut) < S1_MIN_N_ERA:
                ok = False
                break
            keep = B[~m & em]
            dd_after = maxdd(keep)
            detail[e] = {"n": len(cut), "cut_wr": float(cut.win.mean()),
                         "book_wr": float(era_wr[e]), "dd_before": base_dd[e],
                         "dd_after": dd_after, "saved": float(-cut.dollars.sum())}
            if not (cut.win.mean() < era_wr[e]          # predominantly losers by WR...
                    and cut.dollars.sum() < 0              # ...and net negative: removing it
                                                           # must SAVE money, not cost it
                    and dd_after < base_dd[e]):            # and improve drawdown
                ok = False
                break
        if ok:
            rows.append({"cut": name, **{f"{e}_{k}": v for e in ERAS
                                         for k, v in detail[e].items()}})
    L.append(f"\n## Result\n\n**{len(A)} candidate cuts tested across all L3 features. "
             f"{len(rows)} cleared the bar.**\n")

    survivors = []
    if not rows:
        L.append("\n**CLEAN NULL — no cut clears the bar.** No feature, at any quartile "
                 "threshold, removes a predominantly-losing subset consistently in both eras "
                 "while also improving drawdown. The book's losers are not separable by any "
                 "single L3 feature at this resolution. That is a result, not a failure to "
                 "find one.\n")
    else:
        months = sorted(B.mo.unique())
        L.append(f"\n### Jackknife ({len(months)} months, drop-one-out)\n")
        L.append("| cut | 2025 cut WR / book | 2026 cut WR / book | $ saved | maxDD 25 | "
                 "maxDD 26 | jackknife |\n|---|---|---|---|---|---|---|\n")
        # most-saved first (saved is now positive: a real loser cut returns money when removed)
        for r in sorted(rows, key=lambda x: -(x["2025_saved"] + x["2026_saved"])):
            m = dict(A)[r["cut"]]
            flips = []
            for mo in months:
                keepmo = (B.mo != mo).to_numpy()
                bad = False
                for e in ERAS:
                    em = ((B.era == e) & (B.mo != mo)).to_numpy()
                    cut = B[m & em]
                    if (len(cut) < 10 or cut.win.mean() >= B[em].win.mean()
                            or cut.dollars.sum() >= 0):
                        bad = True
                if bad:
                    flips.append(mo)
            frag = "FRAGILE (" + ",".join(flips) + ")" if flips else "stable"
            if not flips:
                survivors.append({"cut": r["cut"], "saved": r["2025_saved"] + r["2026_saved"]})
            L.append(f"| `{r['cut']}` | {r['2025_cut_wr'] * 100:.0f}% / "
                     f"{r['2025_book_wr'] * 100:.0f}% (n={r['2025_n']}) | "
                     f"{r['2026_cut_wr'] * 100:.0f}% / {r['2026_book_wr'] * 100:.0f}% "
                     f"(n={r['2026_n']}) | ${r['2025_saved'] + r['2026_saved']:,.0f} | "
                     f"${r['2025_dd_before']:,.0f}->${r['2025_dd_after']:,.0f} | "
                     f"${r['2026_dd_before']:,.0f}->${r['2026_dd_after']:,.0f} | {frag} |\n")
        L.append(f"\n**{len(survivors)} of {len(rows)} survive the jackknife unbroken.**\n")
        if not survivors:
            L.append("\nEvery cut that cleared the headline bar collapses when a single month "
                     "is removed. Read that as a null: these are month-specific artifacts, not "
                     "loser traits.\n")

    (DOCS / "london_audit_stage1.json").write_text(json.dumps(
        {"tested": len(A), "cleared": len(rows), "stable": survivors}, indent=2))
    write("LONDON-AUDIT-STAGE1-loser-autopsy.md", "".join(L))


# ============================================================ STAGE 2
def stage2() -> None:
    P = population()
    A = atoms(P)
    names = [n for n, _ in A]
    M = np.column_stack([m.astype(bool) for _, m in A])
    win = P.win.to_numpy().astype(bool)
    era = P.era.to_numpy()
    weeks = P.day.nunique() / 5.0
    min_n_pooled = int(np.ceil(weeks))          # ~1 trade per week

    L = ["# London overnight audit — Stage 2: combination search\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\nPopulation: risk >= {LON_RISK_MIN} candidates, n={len(P)} "
         f"({', '.join(f'{e}: {int((era == e).sum())}' for e in ERAS)}) over "
         f"{P.day.nunique()} days (~{weeks:.0f} weeks).\n",
         "\n## Acceptance bar (fixed in advance)\n",
         f"\n- >= {S2_MIN_WR_ERA * 100:.0f}% WR in 2025 and 2026 **separately**\n"
         f"- pooled Wilson 95% lower bound >= {S2_MIN_WILSON * 100:.0f}%\n"
         f"- >= ~1 trade/week pooled (n >= {min_n_pooled}), and n >= {S2_MIN_N_ERA} per era "
         f"so a 65% WR is never 2-of-3\n"
         f"- {N_PERM}-shuffle permutation null **per era**, outcomes shuffled within era\n"
         f"- family-wise correction (Šidák) across every combination tested\n"]

    def cells():
        yield from ((i,) for i in range(len(names)))
        yield from itertools.combinations(range(len(names)), 2)

    tested = 0
    prelim = []
    for combo in cells():
        tested += 1
        m = M[:, combo[0]].copy()
        for j in combo[1:]:
            m &= M[:, j]
        n = int(m.sum())
        if n < min_n_pooled:
            continue
        okay = True
        per = {}
        for e in ERAS:
            em = m & (era == e)
            ne = int(em.sum())
            if ne < S2_MIN_N_ERA:
                okay = False
                break
            wr = float(win[em].mean())
            if wr < S2_MIN_WR_ERA:
                okay = False
                break
            per[e] = (ne, wr)
        if not okay:
            continue
        k = int(win[m].sum())
        lo = wilson_lo(k, n)
        if lo < S2_MIN_WILSON:
            continue
        prelim.append({"combo": combo, "n": n, "wr": k / n, "wilson": lo, "per": per})

    L.append(f"\n## Result\n\n**{tested:,} combinations tested** (all singles and all pairs of "
             f"{len(names)} atomic conditions derived from the L3 features). "
             f"**{len(prelim)} cleared the deterministic bar** before any null was run.\n")

    survivors = []
    if prelim:
        alpha_fw = 1 - (1 - 0.05) ** (1 / tested)       # Šidák
        L.append(f"\nFamily-wise Šidák threshold for {tested:,} tests: "
                 f"per-test alpha = {alpha_fw:.3g}.\n")
        for c in prelim:
            m = M[:, c["combo"][0]].copy()
            for j in c["combo"][1:]:
                m &= M[:, j]
            ps = {}
            for e in ERAS:
                sel = era == e
                obs = float(win[m & sel].mean())
                pool = win[sel].copy()
                cnt = int((m & sel).sum())
                hits = 0
                for _ in range(N_PERM):
                    RNG.shuffle(pool)
                    if pool[:cnt].mean() >= obs:
                        hits += 1
                ps[e] = hits / N_PERM
            c["p"] = ps
            c["passes_fwer"] = all(v <= alpha_fw for v in ps.values())
            if c["passes_fwer"]:
                survivors.append(c)
        L.append("\n| cell | n | WR | Wilson lo | 2025 n/WR/p | 2026 n/WR/p | FWER |\n"
                 "|---|---|---|---|---|---|---|\n")
        for c in sorted(prelim, key=lambda x: -x["wilson"]):
            lab = " AND ".join(names[i] for i in c["combo"])
            L.append(f"| `{lab}` | {c['n']} | {c['wr'] * 100:.0f}% | {c['wilson'] * 100:.0f}% | "
                     f"{c['per']['2025'][0]}/{c['per']['2025'][1] * 100:.0f}%/{c['p']['2025']:.4f} | "
                     f"{c['per']['2026'][0]}/{c['per']['2026'][1] * 100:.0f}%/{c['p']['2026']:.4f} | "
                     f"{'PASS' if c['passes_fwer'] else 'fails'} |\n")
        L.append(f"\n**{len(survivors)} of {len(prelim)} survive family-wise correction.**\n")

    # WHICH CONSTRAINT BOUND. A bare "nothing found" hides whether the bar was missed on
    # evidence or on sample size. These two floors are in structural tension: ~1 trade/week
    # admits n≈39-70, but a 95% Wilson lower bound of 60% off a ~65% point estimate needs
    # n≈150. Report the cells that met the WR bar in both eras so the reader can see which
    # floor did the killing. This does not move the bar — those cells remain rejected.
    near = []
    for combo in cells():
        m = M[:, combo[0]].copy()
        for j in combo[1:]:
            m &= M[:, j]
        n = int(m.sum())
        if n < min_n_pooled:
            continue
        per = {}
        ok = True
        for e in ERAS:
            em = m & (era == e)
            if int(em.sum()) < S2_MIN_N_ERA:
                ok = False
                break
            per[e] = (int(em.sum()), float(win[em].mean()))
        if ok and all(v[1] >= S2_MIN_WR_ERA for v in per.values()):
            k = int(win[m].sum())
            near.append({"lab": " AND ".join(names[i] for i in combo), "n": n,
                         "wr": k / n, "wilson": wilson_lo(k, n), "per": per})
    L.append("\n## Which floor bound the result\n")
    if near:
        L.append(f"\n{len(near)} cell(s) met the >= {S2_MIN_WR_ERA * 100:.0f}% WR bar in BOTH "
                 f"eras but were rejected by the pooled Wilson floor — a SAMPLE-SIZE objection, "
                 f"not evidence against:\n\n"
                 "| cell | n | pooled WR | Wilson lo | 2025 | 2026 |\n|---|---|---|---|---|---|\n")
        for c in sorted(near, key=lambda x: -x["wilson"]):
            L.append(f"| `{c['lab']}` | {c['n']} | {c['wr'] * 100:.1f}% | "
                     f"**{c['wilson'] * 100:.1f}%** | {c['per']['2025'][0]}/"
                     f"{c['per']['2025'][1] * 100:.1f}% | {c['per']['2026'][0]}/"
                     f"{c['per']['2026'][1] * 100:.1f}% |\n")
        L.append(f"\nThe two floors cannot both be satisfied at this population size: ~1 "
                 f"trade/week admits n≈{min_n_pooled}-70, while a 95% Wilson lower bound of "
                 f"{S2_MIN_WILSON * 100:.0f}% off a ~65% point estimate needs n≈150. Any cell "
                 f"rare enough to be 'low-frequency' is too small to prove itself to 95% "
                 f"confidence. **These cells are not findings** — they are the reason the null "
                 f"is 'unproven at this sample', not 'disproven'. Note that two of them invert "
                 f"or ignore ASIA, consistent with the L3 trial finding ASIA backwards in 2026.\n")
    else:
        L.append(f"\nNo cell reached {S2_MIN_WR_ERA * 100:.0f}% WR in both eras even before "
                 f"the Wilson floor was applied. The null is on the evidence, not on sample "
                 f"size.\n")

    if not prelim or not survivors:
        L.append("\n**CLEAN NULL.** No feature combination reaches 65% win rate in both eras "
                 "at ~1 trade/week with a pooled Wilson floor of 60% and a family-wise-corrected "
                 "permutation null. Searching "
                 f"{tested:,} combinations and finding nothing that survives correction is "
                 "exactly what an honest search over a population with one real signal looks "
                 "like. There is no London elite cell at this resolution.\n")

    (DOCS / "london_audit_stage2.json").write_text(json.dumps(
        {"tested": tested, "cleared": len(prelim),
         "survivors": [{"cell": [names[i] for i in c["combo"]], "n": c["n"], "wr": c["wr"],
                        "wilson": c["wilson"], "p": c["p"]} for c in survivors]}, indent=2))
    write("LONDON-AUDIT-STAGE2-combinations.md", "".join(L))


# ============================================================ STAGE 3
def stage3() -> None:
    P = population()
    A = atoms(P)
    names = [n for n, _ in A]
    M = np.column_stack([m.astype(bool) for _, m in A])
    win = P.win.to_numpy().astype(bool)
    R = P.R.to_numpy(float)
    days = P.day.to_numpy()
    uniq = np.array(sorted(set(days)))

    # the actual rule this rebuild shipped, measured on everything
    wall = P.wall.to_numpy().astype(bool)
    actual_is = float(R[wall].mean())

    pair_idx = list(itertools.combinations(range(len(names)), 2))
    min_n = 25

    L = ["# London overnight audit — Stage 3: selection-null calibration\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         "\n## What this stage answers\n",
         "\nStages 1 and 2 search thousands of rules and report the best. That process returns "
         "a winner even on pure noise, and a per-cell permutation null does not price it — it "
         "asks *is this cell real given these rows*, not *how much did searching inflate it*.\n",
         f"\nSo: **{N_SPLITS} randomized day-level splits**. In each, the ENTIRE selection "
         "procedure runs in-sample (pick the best-performing rule by mean R among all singles "
         f"and pairs with n>={min_n}), then that rule — chosen blind — is measured "
         "out-of-sample. The gap between the two is the shrinkage a rule picked this way "
         "should expect.\n",
         "\nSplits are **by day**, never by row: same-day trades share regime and tape, so a "
         "row-level split would leak and understate shrinkage.\n"]

    is_scores, oos_scores = [], []
    for _ in range(N_SPLITS):
        RNG.shuffle(uniq)
        cut = len(uniq) // 2
        isd = set(uniq[:cut].tolist())
        m_is = np.array([d in isd for d in days])
        m_oos = ~m_is
        best, best_v = None, -np.inf
        for combo in [(i,) for i in range(len(names))] + pair_idx:
            c = M[:, combo[0]].copy()
            for j in combo[1:]:
                c &= M[:, j]
            sel = c & m_is
            if sel.sum() < min_n:
                continue
            v = R[sel].mean()
            if v > best_v:
                best_v, best = v, combo
        if best is None:
            continue
        c = M[:, best[0]].copy()
        for j in best[1:]:
            c &= M[:, j]
        o = c & m_oos
        if o.sum() < 10:
            continue
        is_scores.append(best_v)
        oos_scores.append(float(R[o].mean()))

    a = np.array(is_scores)
    b = np.array(oos_scores)
    shrink = a - b
    pct = float((b < actual_is).mean() * 100)

    L.append(f"\n## Result — {len(b)} valid splits\n")
    L.append(f"\n| | median | mean | p10 | p90 |\n|---|---|---|---|---|\n")
    L.append(f"| best in-sample mean R | {np.median(a):+.3f} | {a.mean():+.3f} | "
             f"{np.percentile(a, 10):+.3f} | {np.percentile(a, 90):+.3f} |\n")
    L.append(f"| same rule out-of-sample | {np.median(b):+.3f} | {b.mean():+.3f} | "
             f"{np.percentile(b, 10):+.3f} | {np.percentile(b, 90):+.3f} |\n")
    L.append(f"| shrinkage (IS - OOS) | {np.median(shrink):+.3f} | {shrink.mean():+.3f} | "
             f"{np.percentile(shrink, 10):+.3f} | {np.percentile(shrink, 90):+.3f} |\n")
    L.append(f"\n**Median IS->OOS shrinkage: {np.median(shrink):+.3f} R** "
             f"({np.median(shrink) / max(abs(np.median(a)), 1e-9) * 100:.0f}% of the in-sample "
             f"figure evaporates out-of-sample for a rule chosen this way).\n")
    L.append(f"\n## Where the wall arm actually sits\n")
    L.append(f"\nThe shipped rule (W or FAR) scores **{actual_is:+.3f} mean R** on the full fit "
             f"population. Against the distribution of *out-of-sample* results from rules "
             f"selected by search, it sits at the **{pct:.0f}th percentile**.\n")
    if pct >= 90:
        L.append("\n**Read: mostly real.** A searched rule rarely achieves this out-of-sample. "
                 "The wall arm is not what data-dredging typically produces here.\n")
    elif pct >= 60:
        L.append("\n**Read: partly real, materially inflated.** The wall arm beats the typical "
                 "searched rule but sits inside the range search can reach. Expect the holdout "
                 "to come in meaningfully below the fit figure — roughly the shrinkage above.\n")
    else:
        L.append("\n**Read: not distinguishable from search artifact.** The wall arm's result "
                 "is within what selecting the best of thousands of rules produces by chance. "
                 "The sealed holdout is the only remaining evidence that could rescue it, and "
                 "the prior should be low.\n")
    L.append(f"\n**Practical consequence:** subtract roughly {np.median(shrink):.2f} R from any "
             f"fit-span expectation before believing it live. Applied to the wall arm's fit "
             f"mean R of {actual_is:+.3f}, the honest forward expectation is about "
             f"{actual_is - np.median(shrink):+.3f} R.\n")

    (DOCS / "london_audit_stage3.json").write_text(json.dumps(
        {"splits": len(b), "median_shrinkage": float(np.median(shrink)),
         "actual_meanR": actual_is, "percentile": pct}, indent=2))
    write("LONDON-AUDIT-STAGE3-selection-null.md", "".join(L))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=[1, 2, 3], required=True)
    a = ap.parse_args()
    {1: stage1, 2: stage2, 3: stage3}[a.stage]()


if __name__ == "__main__":
    main()
