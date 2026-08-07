#!/usr/bin/env python3
"""PAIRWISE OVERLAP — the same-session redundancy detector (ANGUS 2026-08-04).

The question this answers, in Angus's words: two strategies in the same session are
both profitable, but "if you look at the entry times across the days, they're all
basically entering at the same time (just off of different things firing)" — so a
move against one is a move against both, and the account is double-sized on ONE idea.
Day-level P&L correlation is too blunt for this; the tell is at the trade level.

Consumes any two emission files (docs/CONTRACT-strategy-emission.md — signal ts,
fill_ts, exit_ts, direction, day, pl are exactly the needed fields) and measures:

  1. ENTRY CLUSTERING — for each trade of A on a both-active day, the minute gap to
     the nearest SAME-direction entry of B (and vice versa). Reported as the share of
     trades with a same-direction twin within 5 / 15 / 30 minutes. This is the
     "different trigger, same trade" detector.
  2. CO-ENTRY DAYS — share of both-active days with at least one same-direction pair
     inside 15 minutes.
  3. CONCURRENT OPEN RISK — minutes both books are in-market simultaneously (same
     clock, one budget accumulator), total and by day.
  4. DIRECTION AGREEMENT — on both-active days, how often the day's net direction
     matches (long-heavy vs short-heavy by risk-weighted count).
  5. DAY-LEVEL P&L — Pearson + Spearman on both-active days (the blunt instrument,
     kept for continuity with the battery), plus same-red-day co-occurrence.

REDUNDANCY FLAGS — thresholds [PROPOSED — Angus to ratify], stated with every run:
  * EFFECTIVELY ONE STRATEGY: >= 50% of either book's entries have a same-direction
    twin within 15 min. Candidates that trip this are ONE strategy for portfolio
    purposes — validate the better one, tombstone the other as a duplicate
    (supersession pointer, docs/VAULT-SCHEMA.md §6), or explicitly waive.
  * STACKED RISK: concurrent open-risk minutes on >= 30% of both-active days. Both
    can ship only if the combined book passes the funded-shell MC at combined sizing.
  * SAME-DAY BLEED: same-red-day rate >= 2x the independence expectation.

The cross-session battery (scripts/correlation_battery.py) answers "do these books
hedge or stack ACROSS the portfolio"; this answers "are these two candidates the
same trade" WITHIN a session. Both consume the same emissions; run this one first —
a duplicate should die before it ever reaches the portfolio question.

    python -m scripts.pairwise_overlap output/emission_A.parquet output/emission_B.parquet
    python -m scripts.pairwise_overlap --demo   # London pattern-B vs pattern-B2 split
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY_TZ = "America/New_York"
WINDOWS_MIN = (5, 15, 30)
# [PROPOSED — Angus to ratify]
TWIN_SHARE_FLAG = 0.50       # >= this share of entries twinned within 15 min -> ONE STRATEGY
CONCURRENT_DAYS_FLAG = 0.30  # >= this share of both-active days with overlap -> STACKED RISK
RED_RATIO_FLAG = 2.0         # same-red-day rate vs independence -> SAME-DAY BLEED


def _load(path: str | Path) -> pd.DataFrame:
    E = pd.read_parquet(path)
    for c in ("ts", "fill_ts", "exit_ts"):
        E[c + "_dt"] = pd.to_datetime(E[c], format="mixed", utc=True)
    return E


def _twin_shares(A: pd.DataFrame, B: pd.DataFrame, days: set) -> dict[int, float]:
    """Share of A's entries (on both-active days) with a same-direction B entry
    within each window. Entry stamp = fill_ts (risk opening, comparable across books)."""
    gaps = []
    for r in A.itertuples():
        if r.day not in days:
            continue
        cand = B[(B.day == r.day) & (B.direction == r.direction)]
        if len(cand) == 0:
            gaps.append(np.inf)
            continue
        gaps.append((cand.fill_ts_dt - r.fill_ts_dt).abs().min().total_seconds() / 60.0)
    g = np.array(gaps)
    return {w: float((g <= w).mean()) if len(g) else np.nan for w in WINDOWS_MIN}, len(g)


def _minutes(df: pd.DataFrame, days: set) -> dict[str, set]:
    out: dict[str, set] = {}
    for r in df.itertuples():
        if r.day not in days:
            continue
        rng = pd.date_range(r.fill_ts_dt.floor("min"), r.exit_ts_dt.floor("min"), freq="min")
        out.setdefault(r.day, set()).update(rng)
    return out


def report(path_a: str | Path, path_b: str | Path, name_a: str | None = None,
           name_b: str | None = None) -> dict:
    A, B = _load(path_a), _load(path_b)
    na = name_a or A.strategy.iloc[0]
    nb = name_b or B.strategy.iloc[0]
    days_a, days_b = set(A.day), set(B.day)
    both = days_a & days_b
    print(f"PAIRWISE OVERLAP — {na} ({len(A)} trades, {len(days_a)} days) vs "
          f"{nb} ({len(B)} trades, {len(days_b)} days)")
    print(f"both-active days: {len(both)} "
          f"({len(both) / max(len(days_a | days_b), 1):.0%} of union)")
    if not both:
        print("no common days — nothing to measure at trade level")
        return {"both_days": 0, "flags": []}

    ta, n_ta = _twin_shares(A, B, both)
    tb, n_tb = _twin_shares(B, A, both)
    print(f"\n1. ENTRY CLUSTERING (same-direction twin within N minutes)")
    print(f"   {na} -> {nb}: " + "  ".join(f"±{w}m {ta[w]:.0%}" for w in WINDOWS_MIN)
          + f"   ({n_ta} trades on common days)")
    print(f"   {nb} -> {na}: " + "  ".join(f"±{w}m {tb[w]:.0%}" for w in WINDOWS_MIN)
          + f"   ({n_tb} trades on common days)")

    co_days = 0
    for d in both:
        ad = A[A.day == d]
        bd = B[B.day == d]
        hit = any(((bd.direction == r.direction)
                   & ((bd.fill_ts_dt - r.fill_ts_dt).abs()
                      <= pd.Timedelta(minutes=15))).any() for r in ad.itertuples())
        co_days += hit
    print(f"\n2. CO-ENTRY DAYS: {co_days}/{len(both)} both-active days "
          f"({co_days / len(both):.0%}) have a same-direction pair inside 15 min")

    ma, mb = _minutes(A, both), _minutes(B, both)
    ov = {d: len(ma.get(d, set()) & mb.get(d, set())) for d in both}
    ov_days = sum(v > 0 for v in ov.values())
    print(f"\n3. CONCURRENT OPEN RISK: {sum(ov.values())} total minutes; "
          f"{ov_days}/{len(both)} days ({ov_days / len(both):.0%})")

    def day_dir(df: pd.DataFrame, d: str) -> int:
        g = df[df.day == d]
        w = np.where(g.direction == "long", 1, -1) * g.risk_dollars
        return int(np.sign(w.sum()))
    agree = [day_dir(A, d) == day_dir(B, d) for d in sorted(both)]
    print(f"\n4. DIRECTION AGREEMENT (risk-weighted day direction): "
          f"{np.mean(agree):.0%} of both-active days (coin flip: 50%)")

    pa = A.groupby("day").pl.sum().loc[sorted(both)]
    pb = B.groupby("day").pl.sum().loc[sorted(both)]
    pear = float(np.corrcoef(pa, pb)[0, 1]) if pa.std() > 0 and pb.std() > 0 else np.nan
    spear = float(np.corrcoef(pa.rank(), pb.rank())[0, 1]) if len(pa) > 2 else np.nan
    red_a, red_b = pa < 0, pb < 0
    both_red = (red_a & red_b).mean()
    indep = red_a.mean() * red_b.mean()
    ratio = both_red / indep if indep > 0 else np.nan
    print(f"\n5. DAY-LEVEL P&L (both-active, n={len(pa)}): Pearson {pear:+.3f}, "
          f"Spearman {spear:+.3f}")
    print(f"   same-red days: {both_red:.0%} observed vs {indep:.0%} under "
          f"independence (ratio {ratio:.1f}x)")

    flags = []
    if max(ta[15], tb[15]) >= TWIN_SHARE_FLAG:
        flags.append(f"EFFECTIVELY ONE STRATEGY — {max(ta[15], tb[15]):.0%} of one "
                     f"book's entries have a same-direction twin within 15 min "
                     f"(flag at {TWIN_SHARE_FLAG:.0%})")
    if ov_days / len(both) >= CONCURRENT_DAYS_FLAG:
        flags.append(f"STACKED RISK — concurrent open risk on {ov_days / len(both):.0%} "
                     f"of both-active days (flag at {CONCURRENT_DAYS_FLAG:.0%})")
    if ratio == ratio and ratio >= RED_RATIO_FLAG:
        flags.append(f"SAME-DAY BLEED — same-red-day rate {ratio:.1f}x independence "
                     f"(flag at {RED_RATIO_FLAG:.1f}x)")
    print("\nFLAGS [thresholds PROPOSED — Angus to ratify]:")
    print("   " + ("\n   ".join(flags) if flags else "none — no redundancy signal at "
                   "the proposed thresholds"))
    return {"both_days": len(both), "twin_15": {na: ta[15], nb: tb[15]},
            "concurrent_day_share": ov_days / len(both), "pearson": pear,
            "red_ratio": ratio, "flags": flags}


def demo() -> None:
    """Split the old London book by pattern — two same-session books entering off
    different triggers, on real data: exactly the scenario the detector exists for.
    A DEMONSTRATION of the instrument, not a candidate evaluation."""
    src = ROOT / "output/emission_london_old_fit.parquet"
    E = pd.read_parquet(src)
    tmp = []
    for pat, name in (("B2", "london_patB2"), ("B", "london_patB")):
        S = E[E.pattern == pat].copy()
        S["strategy"] = name
        p = ROOT / f"output/_demo_emission_{name}.parquet"
        S.to_parquet(p, index=False)
        tmp.append(p)
    print(f"[demo] {src.name} split by pattern: B2 vs B — same session, different "
          f"triggers, real data\n")
    report(*tmp)
    for p in tmp:
        p.unlink()


def self_test() -> None:
    """Positive control: a book against itself is the perfect duplicate — every flag
    must fire. If this ever prints PASS with no flags, the instrument is broken."""
    p = ROOT / "output/emission_ny_canon_fit.parquet"
    print("[self-test] ny_canon vs itself — the perfect duplicate; all flags must fire\n")
    r = report(p, p, "ny_canon", "ny_canon(copy)")
    need = ("EFFECTIVELY ONE STRATEGY", "STACKED RISK", "SAME-DAY BLEED")
    fired = all(any(f.startswith(n) for f in r["flags"]) for n in need)
    print(f"\nself-test: {'PASS — all three flags fired' if fired else 'FAIL — instrument broken'}")
    sys.exit(0 if fired else 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("emissions", nargs="*", help="two emission parquet paths")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif a.demo:
        demo()
    elif len(a.emissions) == 2:
        report(a.emissions[0], a.emissions[1])
    else:
        ap.error("give two emission files, --demo, or --self-test")


if __name__ == "__main__":
    main()
