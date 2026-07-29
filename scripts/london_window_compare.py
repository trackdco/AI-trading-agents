#!/usr/bin/env python3
"""Raw-structure comparison: London 08:00-10:00 vs 10:00-12:00 — is the second slot worth
buying depth data for?

THE QUESTION. The 08:00-10:00 canon's entire edge comes from ONE order-flow signal (W/FAR,
r=0.834 — the same structural fact scored twice). Depth data exists for 08:00-09:59 only: the
295 fit / 129 sealed MBP-10 files are exactly that window. So 10:00-12:00 cannot be scored, and
the only honest comparison is RAW STRUCTURE — the L2 outcome population before any check.

WHAT "RAW" MEANS HERE. Identical pipeline, identical engine config, identical rr_floor/V8/
v8_be_at_open=False, identical 30d->7d lookback discipline. The ONLY difference is the two
hours the detector looks at. Both are reported at three depths:

  all candidates        every L2 outcome (the unfiltered base)
  risk >= LON_RISK_MIN  the tradeable population — L2 proved sub-9.5pt loses in every band
                        and era in the 08-10 window, so this is the fair like-for-like
  by era                2025 vs 2026, because one era is an anecdote

HOW TO READ IT FOR THE BUY DECISION. Depth is worth buying for 10-12 if its raw base is
comparable to 08-10's. In 08-10 the risk-gated base is roughly breakeven (meanR +0.045 in
2025, +0.069 in 2026) and the wall signal lifts the taken population to +0.4/+0.6. Depth did
not rescue a losing base — it selected within a neutral one. If 10-12's gated base is also
~breakeven, the same lever plausibly exists. If it is materially negative, depth has to
overcome a deficit rather than sort a neutral pool, and the prior is much weaker.

This script asserts nothing about 10-12's order flow. It cannot — there is no data. It sizes
the prior.

    python -m scripts.london_window_compare
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.scorer import LON_RISK_MIN  # noqa: E402

WINDOWS = {"08:00-10:00 (canon, has depth)": "output/l2_outcomes_london_fit.parquet",
           "10:00-12:00 (no depth)": "output/l2_outcomes_london_1000-1200_fit.parquet"}


def line(lab: str, d: pd.DataFrame) -> str:
    if not len(d):
        return f"    {lab:>22}: (none)"
    return (f"    {lab:>22}: n={len(d):>5}  WR {(d.dollars_1lot > 0).mean() * 100:>3.0f}%  "
            f"meanR {d.R.mean():>+7.3f}  1-lot ${d.dollars_1lot.sum():>+10,.0f}  "
            f"medRisk {d.risk.median():>4.1f}pt")


def main() -> None:
    frames = {}
    for lab, path in WINDOWS.items():
        p = ROOT / path
        if not p.exists():
            print(f"missing: {path} — build it first")
            continue
        F = pd.read_parquet(p)
        F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
        frames[lab] = F

    for lab, F in frames.items():
        oc = F[F.status == "outcome"]
        print(f"\n{'=' * 96}\n{lab}\n{'=' * 96}")
        print(f"  candidates {len(F)} on {F.day.nunique()} days -> {len(oc)} outcomes")
        print(f"  status: {F.status.value_counts().to_dict()}")

        print("\n  ALL candidates (unfiltered base):")
        print(line("all eras", oc))
        for e in sorted(oc.era.unique()):
            print(line(e, oc[oc.era == e]))

        big = oc[oc.risk >= LON_RISK_MIN]
        print(f"\n  risk >= {LON_RISK_MIN} (the tradeable population — like-for-like):")
        print(line("all eras", big))
        for e in sorted(big.era.unique()):
            print(line(e, big[big.era == e]))

        print("\n  by risk band (does the same monotonic WR-vs-risk structure exist?):")
        for lo, hi in [(0, 4), (4, 7), (7, 9.5), (9.5, 15), (15, 25), (25, 1e9)]:
            s = oc[(oc.risk >= lo) & (oc.risk < hi)]
            if not len(s):
                continue
            lab2 = f"{lo:g}-{hi:g}pt" if hi < 1e9 else f">{lo:g}pt"
            print(f"    {lab2:>10} n={len(s):>5} WR {(s.dollars_1lot > 0).mean() * 100:>3.0f}% "
                  f"meanR {s.R.mean():>+7.3f}")

    if len(frames) == 2:
        a, b = (f[f.status == "outcome"] for f in frames.values())
        ga, gb = a[a.risk >= LON_RISK_MIN], b[b.risk >= LON_RISK_MIN]
        print(f"\n{'=' * 96}\nHEAD TO HEAD — risk-gated base, the number the buy decision "
              f"turns on\n{'=' * 96}")
        for lab, g in zip(WINDOWS, (ga, gb)):
            print(f"  {lab:>32}: n={len(g):>5}  meanR {g.R.mean():>+7.3f}  "
                  f"${g.dollars_1lot.sum():>+10,.0f}  "
                  f"per-day {len(g) / max(g.day.nunique(), 1):.1f}")


if __name__ == "__main__":
    main()
