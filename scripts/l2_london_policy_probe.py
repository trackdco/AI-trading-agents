#!/usr/bin/env python3
"""What do the two POLICY vetoes inside L2 actually cost or save London?

L2 is meant to contain no selection, but two rulebook filters run inside it and remove 25.0%
of the fit census / 16.4% of holdout before any outcome is recorded:

  vetoed_news_preopen   engine.py:871 — on a high-impact PRE-OPEN release day the entire
                        pre-market is blocked until 09:30 ET. Every London entry is before
                        09:30, so a US 8:30 release blacks out the whole London session:
                        1,192 fit candidates over 36 days (26 days blacked out entirely),
                        606 holdout candidates over 12 days.
  vetoed_bb_vwap        §7 v1.2 "cluster must hold BB+VWAP" — 1,146 fit / 357 holdout.

Neither is physics. Both are already config flags (no engine change needed). This script
re-runs ONLY the vetoed candidates with the corresponding flag off and prices what was being
removed, so the ruling rests on numbers rather than on which story sounds better.

READ THE >=9.5pt ROWS, NOT THE HEADLINE. L2 established that risk < 9.5pt loses in every era
(meanR -0.278 fit / -0.291 holdout) regardless of any other rule. If the vetoed candidates are
mostly sub-9.5 they would have lost anyway and the veto is neither saving nor costing anything
real — so every table is also reported conditioned on risk >= 9.5, which is the population the
book will actually trade.

ERA SPLIT, per handoff §3: discover on 2025, validate on 2026, holdout separate. A veto worth
removing points the same way in all three. One era is an anecdote.

EXPOSURE TEST for the news gate specifically: the rule exists to keep positions out of a
pending release, so the direct question is how many of the admitted fills are STILL OPEN at
08:30 ET. If almost none are, the rule is not doing the job it was written to do.

    python -m scripts.l2_london_policy_probe --span fit
    python -m scripts.l2_london_policy_probe --span holdout
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes_london import NY, l2_cfg, run  # noqa: E402

PROBES = {
    "vetoed_news_preopen": ("no_premarket_high_impact", False),
    "vetoed_bb_vwap": ("require_bb_vwap", False),
}
RELEASE_HM = 8 * 60 + 30        # 08:30 ET — the release the pre-open blackout guards


def era(day: str, span: str) -> str:
    return "holdout" if span == "holdout" else day[:4]


def table(oc: pd.DataFrame, label: str) -> None:
    if not len(oc):
        print(f"  {label:>22}: (none)")
        return
    print(f"  {label:>22}: n={len(oc):>5} WR {(oc.dollars_1lot > 0).mean() * 100:>3.0f}% "
          f"meanR {oc.R.mean():>+7.3f}  1-lot ${oc.dollars_1lot.sum():>+10,.0f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout"], required=True)
    ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args()

    L2 = pd.read_parquet(ROOT / f"output/l2_outcomes_london_{a.span}.parquet")
    census = pd.read_parquet(ROOT / f"output/l0_triggers_london_{a.span}.parquet")

    for status, (field, value) in PROBES.items():
        blocked = L2[L2.status == status]
        if not len(blocked):
            continue
        print(f"\n{'=' * 78}\n{status}  ->  re-running with {field}={value}\n"
              f"{len(blocked)} candidates on {blocked.day.nunique()} days\n{'=' * 78}", flush=True)

        trigs = census[census.ts.isin(set(blocked.ts))].reset_index(drop=True)

        # patch the flag into the per-day config for this probe only
        import scripts.build_l2_outcomes_london as L2M
        base = L2M.l2_cfg

        def patched(day, t_cancel=100000.0, _f=field, _v=value, _b=base):
            return _b(day, t_cancel).model_copy(update={_f: _v})

        L2M.l2_cfg = patched
        try:
            out = run(trigs, procs=a.procs)
        finally:
            L2M.l2_cfg = base

        oc = out[out.status == "outcome"].copy()
        print(f"\nadmitted {len(oc)} outcomes of {len(trigs)} previously-vetoed candidates")
        if not len(oc):
            continue
        oc["era"] = [era(d, a.span) for d in oc.day]
        big = oc[oc.risk >= 9.5]

        print("\nALL admitted (includes the sub-9.5 population that loses regardless):")
        table(oc, "all eras")
        for e in sorted(oc.era.unique()):
            table(oc[oc.era == e], e)

        print("\nrisk >= 9.5pt ONLY — the population the book actually trades:")
        table(big, "all eras")
        for e in sorted(big.era.unique()):
            table(big[big.era == e], e)

        if status == "vetoed_news_preopen" and len(oc):
            ex = pd.to_datetime(oc.exit_ts, format="mixed", utc=True).dt.tz_convert(NY)
            open_at_release = (ex.dt.hour * 60 + ex.dt.minute) >= RELEASE_HM
            print(f"\nEXPOSURE TEST — the rule exists to avoid holding into the 08:30 release:")
            print(f"  admitted fills still open at 08:30 ET: {int(open_at_release.sum())} "
                  f"of {len(oc)} ({100 * open_at_release.mean():.1f}%)")
            if open_at_release.any():
                table(oc[open_at_release], "still open at 08:30")
            print(f"  median hold: {((ex - pd.to_datetime(oc.fill_ts, format='mixed', utc=True).dt.tz_convert(NY)).dt.total_seconds() / 60).median():.0f} min")


if __name__ == "__main__":
    main()
