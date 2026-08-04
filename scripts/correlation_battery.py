#!/usr/bin/env python3
"""CORRELATION BATTERY — NY canon vs old London book (ANGUS brief 2026-08-04 §3).

Correlation is not one number. Six measurements, run as a battery, on the two books
that already exist:

  NY:     output/funded_book_lucid_fit.parquet — the shipped funded accounting
          (scripts/funded_book.py: rules J/K/L, conviction tiers, $160 base, budget
          $853.33, regenerate with `python -m scripts.funded_book --span fit`).
  London: output/london_canon_book.parquet — the old London book at its native
          research sizing (scripts/london_canon.py Layer-2 multipliers; NOT
          budget-governed, NOT funded-accounted). Rows with size 0 never traded.

  1. INPUT-FAMILY OVERLAP — a veto, not a score. Computed from the two entry specs
     (src/canon/scorer_ny.py::checks/score_of; scripts/london_canon.py::build_london),
     not from returns. Structural overlap leads; return correlation lags.
  2. DAY-LEVEL P&L CORRELATION — Pearson AND Spearman, on two day universes:
     union of active days (inactive book = $0) and intersection (both active).
     Where they disagree, that is information.
  3. TAIL DEPENDENCE — correlation is an average-case statistic; what kills a funded
     account is both books red on the same day. Conditional co-crash rates on each
     book's worst-decile days, both directions, against the 10% independence floor.
  4. TIMING OVERLAP — in-market minute intervals per day per book; simultaneous
     open-risk minutes against one budget accumulator is a different problem from
     correlated daily returns.
  5. SAMPLE ADEQUACY — n common days and a bootstrap CI (10k resamples) on every
     correlation estimate. An estimate without a CI certifies nothing.
  6. COMBINED RUIN — whole-day paired bootstrap (2,000 sims x 252 days) under the
     funded shell (50k start, $2k EOD trailing, line locks at 50k): NY alone,
     London alone, combined as-paired, combined with pairing shuffled (dependence
     broken). The paired-vs-shuffled gap is what same-day dependence costs. This is
     the decision statistic — the one that connects to money.

All estimates are measurements of the PAST co-movement of these two specific books;
thresholds for "uncorrelated enough to both ship" are Angus's to set and live in
docs/REPORT-correlation-2026-08-04.md, not here.

Writes: output/correlation_daily_ny_london.parquet (joined day series)
        output/correlation_battery_report.md      (this run's numbers)

    python -m scripts.correlation_battery
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED = 7
N_BOOT = 10_000
N_SIMS = 2_000
YEAR_DAYS = 252
START, TRAIL = 50_000.0, 2_000.0

# Input families per entry spec. NY: src/canon/scorer_ny.py (checks/score_of + elite);
# London: scripts/london_canon.py (build_london). A family is "read" if any entry gate,
# score bit, or sizing input draws on it.
FAMILIES = {
    "depth walls (dep_wall_*)":            {"NY": "W, D, WALLSZ, wall-quality cut", "LDN": "W, FAR"},
    "overnight structure (on_range/age)":  {"NY": "AGE",                            "LDN": "ROOM"},
    "order flow / CVD / delta":            {"NY": "F_, Tc, T2, LONSLOPE",           "LDN": "ASIA, opp5"},
    "VWAP geometry":                       {"NY": "G",                              "LDN": "—"},
    "trigger density (trigdens_30)":       {"NY": "TRIG",                           "LDN": "—"},
    "structural events (broke)":           {"NY": "elite gate",                     "LDN": "—"},
    "pattern taxonomy (B/B2/A)":           {"NY": "—",                              "LDN": "Layer 2p"},
}


def day_series() -> tuple[pd.Series, pd.Series]:
    ny = pd.read_parquet(ROOT / "output/funded_book_lucid_fit.parquet")
    ldn = pd.read_parquet(ROOT / "output/london_canon_book.parquet")
    ldn = ldn[ldn["size"] > 0]
    a = ny.groupby("day").pl.sum()
    b = ldn.groupby("day").pl.sum()
    lo = max(a.index.min(), b.index.min())
    hi = min(a.index.max(), b.index.max())
    return a.loc[lo:hi], b.loc[lo:hi]


def boot_ci(x: np.ndarray, y: np.ndarray, stat, rng) -> tuple[float, float, float]:
    """stat(x, y) with a 95% percentile bootstrap CI over day pairs."""
    n = len(x)
    est = stat(x, y)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    vals = np.array([stat(x[i], y[i]) for i in idx])
    vals = vals[~np.isnan(vals)]
    return est, *np.percentile(vals, [2.5, 97.5])


def pearson(x, y):
    if x.std() == 0 or y.std() == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    return pearson(pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy())


def in_market_minutes() -> pd.DataFrame:
    """Per-day in-market minute sets for each book; overlap = simultaneous open risk."""
    from scripts.funded_book import load_book, run
    V = load_book("fit")
    B = run(V, "lucid")
    V = V.set_index(["ts"])
    ny = pd.DataFrame({"fill": V.loc[B.ts, "fill"].to_numpy(),
                       "exit": V.loc[B.ts, "exit"].to_numpy(),
                       "day": B.day.to_numpy()})
    ldn = pd.read_parquet(ROOT / "output/london_canon_book.parquet")
    ldn = ldn[ldn["size"] > 0].copy()
    ldn["fill"] = pd.to_datetime(ldn.fill, format="mixed", utc=True)
    ldn["exit"] = pd.to_datetime(ldn.exit, format="mixed", utc=True)

    def minutes(df):
        out = {}
        for r in df.itertuples():
            mins = pd.date_range(pd.Timestamp(r.fill).floor("min"),
                                 pd.Timestamp(r.exit).floor("min"), freq="min")
            out.setdefault(r.day, set()).update(mins)
        return out

    ldn["day"] = ldn.day.astype(str)
    m_ny, m_ldn = minutes(ny), minutes(ldn)
    rows = []
    for day in sorted(set(m_ny) | set(m_ldn)):
        a, b = m_ny.get(day, set()), m_ldn.get(day, set())
        rows.append({"day": day, "ny_min": len(a), "ldn_min": len(b),
                     "overlap_min": len(a & b)})
    return pd.DataFrame(rows)


def ruin(day_pl: np.ndarray, rng) -> dict:
    """Whole-day bootstrap under the funded shell: 50k start, $2k EOD trailing, lock at 50k.
    Bust = EOD buffer <= 0. No payout withdrawals (mc_funded_lab owns that knob), so P(bust)
    here is a comparison statistic between books, not an absolute funding forecast."""
    n = len(day_pl)
    busts, nets, dds, worsts = 0, [], [], []
    for _ in range(N_SIMS):
        path = day_pl[rng.integers(0, n, YEAR_DAYS)]
        bal, line, mb, peak, dd = START, START - TRAIL, 1e9, START, 0.0
        for p in path:
            bal += p
            mb = min(mb, bal - line)
            if bal - line <= 0:
                busts += 1
                break
            line = min(START, max(line, bal - TRAIL))
            peak = max(peak, bal)
            dd = max(dd, peak - bal)
        nets.append(bal - START)
        dds.append(dd)
        worsts.append(path.min())
    return {"P(bust)": busts / N_SIMS, "median net/yr": float(np.median(nets)),
            "median maxDD": float(np.median(dds)), "p95 maxDD": float(np.percentile(dds, 95)),
            "median worst day": float(np.median(worsts))}


def main() -> None:
    rng = np.random.default_rng(SEED)
    L: list[str] = []
    say = lambda s="": (print(s), L.append(s))

    a, b = day_series()
    lo, hi = a.index.min(), min(a.index.max(), b.index.max())
    say(f"CORRELATION BATTERY — NY canon (funded, lucid fit) vs old London book (native sizing)")
    say(f"common span {lo} .. {hi} | NY active days {len(a)} | London active days {len(b)}")
    say("")

    say("1. INPUT-FAMILY OVERLAP (from the entry specs — a veto input, not a score)")
    shared = 0
    for fam, r in FAMILIES.items():
        both = r["NY"] != "—" and r["LDN"] != "—"
        shared += both
        say(f"   {'SHARED ' if both else '       '}{fam:38s} NY: {r['NY']:34s} LDN: {r['LDN']}")
    say(f"   -> {shared}/{len(FAMILIES)} families shared. Depth walls, overnight structure and")
    say(f"      order-flow are read by BOTH books: structurally, these are cousins.")
    say("")

    U = pd.DataFrame({"ny": a, "ldn": b}).fillna(0.0)          # union of active days
    I = pd.DataFrame({"ny": a, "ldn": b}).dropna()             # both active
    for name, df in (("union (inactive book = $0)", U), ("intersection (both active)", I)):
        x, y = df.ny.to_numpy(float), df.ldn.to_numpy(float)
        pe, plo, phi = boot_ci(x, y, pearson, rng)
        sp, slo, shi = boot_ci(x, y, spearman, rng)
        say(f"2. DAY-LEVEL P&L — {name}: n={len(df)}")
        say(f"   Pearson  {pe:+.3f}  [95% CI {plo:+.3f} .. {phi:+.3f}]")
        say(f"   Spearman {sp:+.3f}  [95% CI {slo:+.3f} .. {shi:+.3f}]")
    say("")

    x, y = I.ny.to_numpy(float), I.ldn.to_numpy(float)
    qx, qy = np.quantile(x, 0.10), np.quantile(y, 0.10)
    n = len(I)
    ny_bad, ldn_bad = x <= qx, y <= qy
    both = ny_bad & ldn_bad
    say(f"3. TAIL DEPENDENCE (worst-decile days, both-active universe, n={n})")
    say(f"   NY worst-decile cut ${qx:+,.0f} ({ny_bad.sum()} days) | London ${qy:+,.0f} ({ldn_bad.sum()} days)")
    say(f"   P(LDN in worst decile | NY in worst decile) = {both.sum() / max(ny_bad.sum(), 1):.2f}  (independence: 0.10)")
    say(f"   P(NY in worst decile | LDN in worst decile) = {both.sum() / max(ldn_bad.sum(), 1):.2f}  (independence: 0.10)")
    say(f"   both-red-decile days: {both.sum()} (independence expects {0.10 * ny_bad.sum():.1f})")
    tail = ny_bad | ldn_bad
    if tail.sum() >= 8:
        tp = pearson(x[tail], y[tail])
        say(f"   Pearson conditioned on either-in-worst-decile (n={tail.sum()}): {tp:+.3f}")
    say(f"   [small-n warning: decile conditioning leaves ~{ny_bad.sum()} days; treat point")
    say(f"    estimates as direction, not precision — this is battery item 5's whole point]")
    say("")

    T = in_market_minutes()
    say(f"4. TIMING OVERLAP (in-market minutes, taken trades only)")
    say(f"   days with any simultaneous open risk: {(T.overlap_min > 0).sum()}/{len(T)}"
        f" | total overlapping minutes: {T.overlap_min.sum()}")
    say("")

    say(f"5. SAMPLE ADEQUACY")
    say(f"   both-active days n={len(I)}; London trades {len(b)}/{len(a)} of NY's active days.")
    say(f"   CIs above are 10k-resample percentile bootstraps; any threshold Angus sets")
    say(f"   should name the minimum n at which an estimate counts at all.")
    say("")

    say(f"6. COMBINED RUIN (paired whole-day bootstrap, {N_SIMS} sims x {YEAR_DAYS} days,")
    say(f"   50k start, $2k EOD trailing locking at 50k; London at NATIVE sizing — see caveat)")
    u = U.ny.to_numpy(float), U.ldn.to_numpy(float)
    combined = u[0] + u[1]
    shuffled = u[0] + rng.permutation(u[1])
    for name, series in (("NY alone", u[0]), ("London alone", u[1]),
                         ("combined (as paired)", combined),
                         ("combined (pairing shuffled)", shuffled)):
        r = ruin(series, rng)
        say(f"   {name:28s} P(bust) {r['P(bust)']:.1%} | median net/yr ${r['median net/yr']:+,.0f}"
            f" | maxDD med ${r['median maxDD']:,.0f} p95 ${r['p95 maxDD']:,.0f}"
            f" | median worst day ${r['median worst day']:+,.0f}")
    say("")
    say("   CAVEAT: London runs its research sizing (multiplier ~1 NQ lot), un-governed by")
    say("   the shared $853.33 budget; the combined rows measure dependence shape, not a")
    say("   shippable book. A funded-profile London book is the data contract's first job.")

    out = pd.DataFrame({"ny": a, "ldn": b})
    out.to_parquet(ROOT / "output/correlation_daily_ny_london.parquet")
    (ROOT / "output/correlation_battery_report.md").write_text(
        "# Correlation battery — raw run output\n\n```\n" + "\n".join(L) + "\n```\n")
    print("\nwrote output/correlation_daily_ny_london.parquet, output/correlation_battery_report.md")


if __name__ == "__main__":
    main()
