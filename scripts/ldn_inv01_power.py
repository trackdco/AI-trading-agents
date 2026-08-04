#!/usr/bin/env python3
"""LDN-INV-01 — can the 2026 sample decide kill criterion 2 at all? A POWER analysis.

WHY. Trial 1's L0 census (research/candidates/london-inventory-fade.md) shows the
inventory signature in 2025 (q0 +20.7 pts, q4 -3.8 — asymmetric) and no asymmetry in
2026 (q0 +17.9, q4 +42.0). Kill criterion 2 is armed. But 2026 carries ~28 days per
quintile cell — BELOW the >=30/era-cell floor the prereg itself cites (VALIDATION-PROCESS
§2.2). Adjudicating an asymmetry by comparing two underpowered cells can return "absent"
almost regardless of the truth.

So before the candidate is killed OR refined, one question has to be answered:

    if 2025's asymmetry were reproduced EXACTLY in 2026, would this sample see it?

If the answer is no, then criterion 2 firing is a sample-size artifact, and a refinement
that "restores" asymmetry there is fitting noise. The honest verdict becomes INCONCLUSIVE
ON POWER (VALIDATION-PROCESS §5) — which blocks like FAIL but points at "get more data",
not "redesign the strategy".

This is measurement of the TEST, not a new search. It ledgers as diagnostic, not as a
trial: no threshold is tuned and no new rule is proposed.

SEALED-SPAN GUARD. The substrate spans 2023-01→2026-07 and the 2023/24 years are the
sealed holdout. `fit_only()` drops them and asserts they are gone. There is no override.

    python -m scripts.ldn_inv01_power
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SUB = ROOT / "output/london_day_features.parquet"
BARS = ROOT / "data/reference/nq_1m_master.parquet"
NY = "America/New_York"
PHI = NormalDist()
# the prereg's authorised windows, ET minute-of-day (close-to-close of boundary minutes)
WINDOWS = {"02:00->03:00": (120, 180), "03:00->04:00": (180, 240),
           "04:00->06:00": (240, 360), "02:00->06:00": (120, 360)}
MIN_N_CELL = 30          # VALIDATION-PROCESS §2.2 proposed floor for a direction claim


def fit_only(d: pd.DataFrame) -> pd.DataFrame:
    """The sealed-span guard. 2023/24 are the holdout; they never enter this analysis."""
    yr = pd.to_datetime(d.day).dt.year
    out = d[yr.isin([2025, 2026])].copy()
    left = sorted(set(pd.to_datetime(out.day).dt.year))
    if set(left) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: years {left}")
    return out


def window_returns() -> pd.DataFrame:
    """Per day, NQ point change close-to-close across each authorised ET window."""
    b = pd.read_parquet(BARS)
    ts = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b = b.assign(day=ts.dt.strftime("%Y-%m-%d"), mod=ts.dt.hour * 60 + ts.dt.minute)
    b = b[b["mod"].between(120, 360)]
    piv = b.pivot_table(index="day", columns="mod", values="close", aggfunc="last")
    out = {}
    for name, (a, z) in WINDOWS.items():
        lo = piv.reindex(columns=range(a, a + 6)).bfill(axis=1).iloc[:, 0]
        hi = piv.reindex(columns=range(z - 5, z + 1)).ffill(axis=1).iloc[:, -1]
        out[name] = hi - lo
    return pd.DataFrame(out).reset_index()


def two_sample_power(delta: float, sd: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Power of a two-sided two-sample test to detect a true mean difference `delta`."""
    se = sd * math.sqrt(1 / n1 + 1 / n2)
    if se == 0:
        return 1.0
    crit = PHI.inv_cdf(1 - alpha / 2)
    lam = abs(delta) / se
    return (1 - PHI.cdf(crit - lam)) + PHI.cdf(-crit - lam)


def mde(sd: float, n1: int, n2: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Minimum detectable difference at the given sample sizes."""
    return (PHI.inv_cdf(1 - alpha / 2) + PHI.inv_cdf(power)) * sd * math.sqrt(1 / n1 + 1 / n2)


def n_needed(delta: float, sd: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Days PER CELL required to detect `delta` at the target power."""
    return 2 * ((PHI.inv_cdf(1 - alpha / 2) + PHI.inv_cdf(power)) * sd / abs(delta)) ** 2


def main() -> None:
    sub = fit_only(pd.read_parquet(SUB))
    W = window_returns()
    d = sub.merge(W, on="day", how="inner")
    d["era"] = pd.to_datetime(d.day).dt.year.astype(str)
    print(f"census days after sealed-span guard: {len(d)} "
          f"({', '.join(f'{e}: {(d.era == e).sum()}' for e in ('2025', '2026'))})\n")

    # era-local quintiles on the conditioning variable, exactly as the prereg specifies
    d["q"] = d.groupby("era").prior_rth_ret.transform(
        lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))

    # ---- parity: reproduce the ledger's trial-1 numbers before trusting anything else
    print("PARITY vs the trial-1 ledger (mean NQ points by prior-RTH quintile)")
    print(f"{'era':>6} {'window':>14} {'q0':>9} {'q4':>9} {'spread':>9} {'n/cell':>7}")
    print("-" * 60)
    cells = {}
    for era in ("2025", "2026"):
        e = d[d.era == era]
        for win in WINDOWS:
            q0, q4 = e[e.q == 0][win].dropna(), e[e.q == 4][win].dropna()
            cells[(era, win)] = (q0, q4)
            print(f"{era:>6} {win:>14} {q0.mean():>+9.1f} {q4.mean():>+9.1f} "
                  f"{q0.mean() - q4.mean():>+9.1f} {min(len(q0), len(q4)):>7}")
    print()

    # ---- the power question, on the window the thesis actually lives in
    print("=" * 78)
    print("POWER: can 2026 detect the asymmetry 2025 showed?")
    print("=" * 78)
    for win in ("03:00->04:00", "02:00->06:00"):
        q0_25, q4_25 = cells[("2025", win)]
        q0_26, q4_26 = cells[("2026", win)]
        delta25 = q0_25.mean() - q4_25.mean()            # the 2025 asymmetry, in points
        # pooled within-cell sd in 2026 — the noise the 2026 test actually fights
        sd26 = math.sqrt(((len(q0_26) - 1) * q0_26.var(ddof=1)
                          + (len(q4_26) - 1) * q4_26.var(ddof=1))
                         / (len(q0_26) + len(q4_26) - 2))
        n1, n2 = len(q0_26), len(q4_26)
        pw = two_sample_power(delta25, sd26, n1, n2)
        print(f"\n--- window {win}")
        print(f"  2025 asymmetry (q0-q4)           {delta25:+.1f} pts")
        print(f"  2026 within-cell sd (pooled)     {sd26:.1f} pts")
        print(f"  2026 cell sizes                  n={n1} / n={n2}   "
              f"(floor is {MIN_N_CELL})")
        print(f"  POWER to detect the 2025 effect  {pw * 100:.0f}%")
        print(f"  min detectable spread @80% power {mde(sd26, n1, n2):+.1f} pts "
              f"({mde(sd26, n1, n2) / abs(delta25):.1f}x the 2025 effect)")
        print(f"  days/cell needed @80% power      {n_needed(delta25, sd26):,.0f} "
              f"(=> ~{n_needed(delta25, sd26) * 5:,.0f} census days/era)")
        obs26 = q0_26.mean() - q4_26.mean()
        print(f"  2026 observed spread             {obs26:+.1f} pts")
        # is the 2026 observation even distinguishable from the 2025 effect?
        se = sd26 * math.sqrt(1 / n1 + 1 / n2)
        z = (obs26 - delta25) / se
        print(f"  2026 obs vs 2025 effect          z={z:+.2f}, "
              f"p={2 * (1 - PHI.cdf(abs(z))):.3f}  "
              f"-> {'DISTINGUISHABLE' if abs(z) > 1.96 else 'NOT distinguishable'}")

    # ---- criterion 2 AS LITERALLY WORDED: is q0 indistinguishable from q4 within 2026?
    print("\n" + "=" * 78)
    print('CRITERION 2 AS WORDED: "top-quintile drift statistically indistinguishable')
    print('from bottom-quintile" — tested WITHIN each era')
    print("=" * 78)
    for era in ("2025", "2026"):
        for win in ("03:00->04:00", "02:00->06:00"):
            q0, q4 = cells[(era, win)]
            sd = math.sqrt(((len(q0) - 1) * q0.var(ddof=1) + (len(q4) - 1) * q4.var(ddof=1))
                           / (len(q0) + len(q4) - 2))
            se = sd * math.sqrt(1 / len(q0) + 1 / len(q4))
            z = (q0.mean() - q4.mean()) / se
            p = 2 * (1 - PHI.cdf(abs(z)))
            print(f"  {era} {win:>14}  spread {q0.mean() - q4.mean():>+7.1f}  "
                  f"z={z:>+5.2f} p={p:.3f}  -> "
                  f"{'DISTINGUISHABLE' if p <= 0.05 else 'indistinguishable (criterion 2 fires)'}")

    print("\n  NOTE: at n=28/cell with this variance, almost NOTHING is distinguishable.")
    print("  A criterion that fires whenever the sample is small is not a test of the")
    print("  strategy — it is a test of the sample. See the verdict note.")

    # ---- how much validate-era data would actually settle this
    q0_25, q4_25 = cells[("2025", "03:00->04:00")]
    q0_26, q4_26 = cells[("2026", "03:00->04:00")]
    sd26 = math.sqrt(((len(q0_26) - 1) * q0_26.var(ddof=1)
                      + (len(q4_26) - 1) * q4_26.var(ddof=1))
                     / (len(q0_26) + len(q4_26) - 2))
    need_cell = n_needed(q0_25.mean() - q4_25.mean(), sd26)
    have_days = int((d.era == "2026").sum())
    need_days = need_cell * 5
    print("\n" + "=" * 78)
    print("WHAT WOULD SETTLE IT (03:00->04:00, the window the thesis claims)")
    print("=" * 78)
    print(f"  validate-era days needed @80% power   ~{need_days:,.0f}")
    print(f"  validate-era days available now        {have_days:,}")
    print(f"  shortfall                             ~{max(0, need_days - have_days):,.0f} "
          f"days (~{max(0, need_days - have_days) / 21:.0f} more trading months)")
    print("\n" + "=" * 78)
    print("READ THIS AS: if power is low, criterion 2 cannot fire on evidence — the")
    print("sample cannot tell 'asymmetry absent' from 'asymmetry present but unmeasurable'.")
    print("=" * 78)


if __name__ == "__main__":
    main()
