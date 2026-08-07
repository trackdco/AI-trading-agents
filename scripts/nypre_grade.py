#!/usr/bin/env python3
"""GRADING PACK — the two NY pre-market survivors through Brake's DSR/PBO graders,
the funded-shell MC, and the correlation battery, in one run.

Inputs (all committed / reproducible):
  output/emission_nypre_{gap,inv}_fit.parquet   scripts/nypre_book.py (frozen specs)
  output/nypre_arms_{nypre_gap,nypre_inv}.parquet  day-level exit-arm matrices
  output/emission_ny_canon_fit.parquet          scripts/emit_strategy.py (shipped canon)

What runs:
  DSR   src/validation/dsr.py (Brake). Candidate = day-level P&L over the FULL
        flow-span day universe (no-trade days are $0 — that is the return stream
        an account holding the strategy experiences). Three deflation levels:
          a) rebuilt exit arms as trial_sharpes (the search we can reconstruct
             exactly, per Brake's preferred input),
          b) the family ledger count (gap 7 / inv 8 declared arms) with the
             rebuilt arms' Sharpe variance as the null spread,
          c) the whole pre-market program (34 declared arms across 8 families —
             the funnel that SELECTED these two winners) with the same spread.
        (c) is the honest deflation for "best of the program"; (a) is the floor.
  PBO   src/validation/pbo.py CSCV over the exit-arm matrices (n_blocks=16,
        day-level rows). Judges the ARM-SELECTION procedure (A1/G0 chosen
        in-sample on n=22/51 — exactly the flagged worry).
  MC    the correlation battery's funded shell (50k start, $2k EOD trailing,
        lock at 50k): each survivor alone, both paired, canon alone, and
        canon+both paired vs pairing-shuffled — the shuffle gap prices what
        same-day dependence costs. Comparative statistic, not a funding forecast.
  CORR  day-level Pearson/Spearman (union + both-active), worst-decile co-crash,
        in-market minute overlap, input-family audit — scored against the five
        [PROPOSED] thresholds in docs/REPORT-correlation-2026-08-04.md.

Writes output/nypre_grading_report.md and prints the same text.

    python -m scripts.nypre_grade
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.dsr import deflated_sharpe_ratio  # noqa: E402
from src.validation.pbo import pbo_cscv  # noqa: E402

SEED = 7
N_SIMS = 2_000
YEAR_DAYS, HALF_DAYS = 252, 126
START, TRAIL = 50_000.0, 2_000.0

LEDGER_ARMS = {"nypre_gap": 7, "nypre_inv": 8}
PROGRAM_ARMS = 34  # euro 8 + polarity 7 + gap 7 + inv 8 + four census-only families

# Mechanism families each book's entry gates read (manifest input_columns -> family).
FAMILIES = {
    "nypre_gap": {"session-structure", "order-flow"},
    "nypre_inv": {"overnight-structure", "order-flow"},
    "ny_canon": {"depth-walls", "overnight-structure", "order-flow", "vwap",
                 "trigger-density", "structural-events"},
}
VETO_SHARED = 3  # threshold 5: >=3 shared families needs an Angus waiver


def day_universe() -> pd.Index:
    arms = pd.read_parquet(ROOT / "output/nypre_arms_nypre_gap.parquet")
    return arms.index


def series_on(universe: pd.Index, book: pd.DataFrame) -> pd.Series:
    s = book.groupby("day").pl.sum()
    return s.reindex(universe).fillna(0.0)


def pearson(x, y):
    if x.std() == 0 or y.std() == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    return pearson(pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy())


def ruin(day_pl: np.ndarray, rng, n_days: int) -> dict:
    busts, nets = 0, []
    for _ in range(N_SIMS):
        path = day_pl[rng.integers(0, len(day_pl), n_days)]
        bal, line = START, START - TRAIL
        for p in path:
            bal += p
            if bal - line <= 0:
                busts += 1
                break
            line = min(START, max(line, bal - TRAIL))
        nets.append(bal - START)
    return {"p_bust": busts / N_SIMS, "median": float(np.median(nets)),
            "p05": float(np.percentile(nets, 5))}


def minutes_per_day(book: pd.DataFrame) -> dict[str, set]:
    out: dict[str, set] = {}
    for r in book.itertuples():
        f = pd.Timestamp(r.fill_ts).floor("min")
        x = pd.Timestamp(r.exit_ts).floor("min")
        out.setdefault(str(r.day), set()).update(pd.date_range(f, x, freq="min"))
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    L: list[str] = []
    say = lambda s="": (print(s), L.append(s))

    uni = day_universe()
    gap = pd.read_parquet(ROOT / "output/emission_nypre_gap_fit.parquet")
    inv = pd.read_parquet(ROOT / "output/emission_nypre_inv_fit.parquet")
    canon = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet")
    canon = canon[canon.day.isin(set(uni))]
    books = {"nypre_gap": gap, "nypre_inv": inv}
    S = {k: series_on(uni, b) for k, b in books.items()}
    S["ny_canon"] = series_on(uni, canon)

    say("# NY pre-market survivors — grading pack (DSR / PBO / funded-shell MC / correlation)")
    say("")
    say(f"Universe: {len(uni)} flow-span sessions {uni[0]} .. {uni[-1]}. "
        f"Sizing: research-native $160-risk per trade. Canon restricted to the same days "
        f"(fit-span funded accounting, {len(canon)} trades).")
    say("")

    say("## 1. DSR (Brake's grader, src/validation/dsr.py)")
    say("")
    for name in ("nypre_gap", "nypre_inv"):
        arms = pd.read_parquet(ROOT / f"output/nypre_arms_{name}.parquet")
        trial_sharpes = []
        for c in arms.columns:
            col = arms[c].to_numpy(float)
            sd = col.std(ddof=1)
            if sd > 0:
                trial_sharpes.append(col.mean() / sd)
        ts = np.array(trial_sharpes)
        r = S[name].to_numpy(float)
        rows = []
        d_a = deflated_sharpe_ratio(r, trial_sharpes=ts)
        rows.append(("a) rebuilt exit arms", d_a))
        var = float(ts.var(ddof=1))
        d_b = deflated_sharpe_ratio(r, n_trials=LEDGER_ARMS[name], trial_sr_var=var)
        rows.append((f"b) family ledger ({LEDGER_ARMS[name]} arms)", d_b))
        d_c = deflated_sharpe_ratio(r, n_trials=PROGRAM_ARMS, trial_sr_var=var)
        rows.append((f"c) whole program ({PROGRAM_ARMS} arms)", d_c))
        say(f"### {name}  (daily SR {d_a.sr:+.4f}, n={d_a.n_obs} days, "
            f"skew {d_a.skew:+.2f}, kurt {d_a.kurt:.1f})")
        for label, d in rows:
            say(f"  {label:32s} SR0 {d.sr0:+.4f}  PSR(0) {d.psr_zero:.3f}  "
                f"DSR {d.dsr:.3f}  {'PASS >= .95' if d.significant else 'below .95'}")
        say("")

    say("## 2. PBO (Brake's grader, src/validation/pbo.py — CSCV on the exit-arm choice)")
    say("")
    for name in ("nypre_gap", "nypre_inv"):
        arms = pd.read_parquet(ROOT / f"output/nypre_arms_{name}.parquet")
        p = pbo_cscv(arms, n_blocks=16)
        say(f"  {name}: PBO {p.pbo:.2f} over {p.n_combinations} splits "
            f"({p.n_trials} arms, {p.n_obs_used} days used) — "
            f"{'OVERFIT >= .50' if p.overfit else 'selection beats noise'}; "
            f"IS->OOS slope {p.slope:+.2f}, P(OOS loss) {p.prob_oos_loss:.2f}")
    say("")

    say("## 3. Funded-shell MC (comparative; 50k start, $2k EOD trailing, lock at 50k)")
    say("")
    combos = {
        "nypre_gap alone": S["nypre_gap"],
        "nypre_inv alone": S["nypre_inv"],
        "gap + inv (paired days)": S["nypre_gap"] + S["nypre_inv"],
        "ny_canon alone (same span)": S["ny_canon"],
        "canon + both (paired days)": S["ny_canon"] + S["nypre_gap"] + S["nypre_inv"],
    }
    for label, s in combos.items():
        r6 = ruin(s.to_numpy(float), rng, HALF_DAYS)
        r12 = ruin(s.to_numpy(float), rng, YEAR_DAYS)
        say(f"  {label:28s} 6mo: P(bust) {r6['p_bust']:.1%}  median ${r6['median']:+,.0f}  "
            f"p05 ${r6['p05']:+,.0f} | 12mo: P(bust) {r12['p_bust']:.1%}  "
            f"median ${r12['median']:+,.0f}")
    x = (S["ny_canon"] + S["nypre_gap"] + S["nypre_inv"]).to_numpy(float)
    sh_gap = S["nypre_gap"].sample(frac=1, random_state=SEED).to_numpy(float)
    sh_inv = S["nypre_inv"].sample(frac=1, random_state=SEED + 1).to_numpy(float)
    shuffled = S["ny_canon"].to_numpy(float) + sh_gap + sh_inv
    rp = ruin(x, rng, YEAR_DAYS)
    rs = ruin(shuffled, rng, YEAR_DAYS)
    say(f"  pairing cost (canon+both):  paired P(bust) {rp['p_bust']:.1%} vs "
        f"shuffled {rs['p_bust']:.1%} — the gap is what same-day dependence costs")
    say("")

    say("## 4. Correlation battery, scored against the five [PROPOSED] thresholds")
    say("")
    pairs = [("nypre_gap", "nypre_inv"), ("nypre_gap", "ny_canon"), ("nypre_inv", "ny_canon")]
    for a, b in pairs:
        sa, sb = S[a], S[b]
        act_a, act_b = sa != 0, sb != 0
        both = act_a & act_b
        n_both = int(both.sum())
        xu, yu = sa.to_numpy(float), sb.to_numpy(float)
        pe_u, sp_u = pearson(xu, yu), spearman(xu, yu)
        say(f"### {a} vs {b}  (active {int(act_a.sum())}/{int(act_b.sum())} days, "
            f"both-active {n_both})")
        say(f"  union (inactive=$0):  Pearson {pe_u:+.3f}  Spearman {sp_u:+.3f}")
        if n_both >= 3:
            xi, yi = sa[both].to_numpy(float), sb[both].to_numpy(float)
            pe_i, sp_i = pearson(xi, yi), spearman(xi, yi)
            say(f"  both-active:          Pearson {pe_i:+.3f}  Spearman {sp_i:+.3f}")
        t3 = n_both >= 60
        say(f"  T3 min-60-both-active: {'MET — return estimates count' if t3 else 'NOT MET — return estimates untrusted; structural veto + timing rule'}")
        if t3:
            qx, qy = np.quantile(xi, 0.10), np.quantile(yi, 0.10)
            co = float(((xi <= qx) & (yi <= qy)).sum() / max((xi <= qx).sum(), 1))
            say(f"  T1 |rho|<=0.30: {'PASS' if abs(pe_i) <= .3 and abs(sp_i) <= .3 else 'FAIL'}   "
                f"T2 co-crash {co:.2f} <= 0.25: {'PASS' if co <= .25 else 'FAIL'}")
        shared = FAMILIES[a] & FAMILIES[b]
        say(f"  T5 shared families {len(shared)}/{VETO_SHARED} ({', '.join(sorted(shared)) or 'none'}): "
            f"{'VETO — Angus waiver required' if len(shared) >= VETO_SHARED else 'no veto'}")
        say("")

    say("### In-market minute overlap (simultaneous open risk, same account)")
    m = {k: minutes_per_day(b) for k, b in {**books, "ny_canon": canon}.items()}
    for a, b in pairs:
        days = set(m[a]) & set(m[b])
        ov = sum(len(m[a][d] & m[b][d]) for d in days)
        tot = sum(len(m[a][d]) for d in set(m[a]))
        say(f"  {a} vs {b}: {len(days)} shared days, {ov} simultaneous minutes "
            f"({ov / max(tot, 1):.0%} of {a}'s {tot} in-market minutes)")
    say("")
    say("T4 combined P(bust) <= 1.0%: see section 3 — the paired canon+both 12mo number is the input.")

    (ROOT / "output/nypre_grading_report.md").write_text("\n".join(L) + "\n")
    print("\nwrote output/nypre_grading_report.md")


if __name__ == "__main__":
    main()
