#!/usr/bin/env python3
"""L1b LONDON — collapse multi-timeframe repeats of the SAME setup into one position.

ANGUS 2026-08-05, and this is a defect in the L1 population, not a refinement:

    "big thing is overlapping entries. for example if it broke the 1 minute bb ma, and
     then 3 minute as well after the 1 minute filled, it should not double up on the same
     trade if that makes sense. for me im always looking at multi time frames, and i enter
     whats best. i dont scale my entry just because it broke the MA on multiple time
     frames sequentially."

L1 walks every trigger independently — deliberately, so execution capacity cannot shape
the population. But one move through a BB basis trips the 1-minute, then the 2-minute,
then the 3-minute, and L1 counted that as three trades. Measured on the fit span:

    52% of fills sit within 5 minutes and 2 points of an earlier same-direction fill
    74% within 15 minutes and 5 points
    97.7% of same-direction fills inside 15 minutes SHARE A CLUSTER LEVEL with the earlier
      one -- they are structurally the same setup, not merely adjacent in price

The detector already resolves SIMULTANEOUS multi-TF collisions ("highest TF wins", §1 MTF
arbitration). Nothing ever resolved SEQUENTIAL ones. This does.

THE RULE (declared here, and it is a population definition, not a filter):
a fill joins an OPEN setup when, within the same day and direction, it lands within
`WINDOW_MIN` minutes of that setup's FIRST fill AND either
  (a) shares a cluster level NAME with it, or
  (b) fills within `PRICE_PT` points of it.
Otherwise it opens a new setup. Window is measured from the setup's first fill, never
from its latest, so a chain of triggers cannot extend a setup indefinitely.

TIE-BREAK — which member of the setup you actually trade. Two arms, both recorded:
  `first`  the earliest fill. DEFAULT, on causality: at the moment the 1-minute fills you
           do not yet know a 3-minute is coming, so taking it needs no foreknowledge and
           no waiting. This is the same principle as the L4 burn-list rule
           "first-N-clearing, never best-of-day".
  `htf`    the highest timeframe in the setup. DECLARED CHALLENGER, not default: live it
           requires standing aside for an arbitration window and it may pick a fill that
           already happened. Its causality has to be proven before it can be traded.

NOTHING IS ENFORCED HERE. Both tie-breaks are written as boolean columns beside the
untouched population, exactly as the cancel policies were. L2 chooses by declared arm.

    python -m scripts.l1_london_dedup
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IN_PARQUET = ROOT / "output/l1_fills_london_fit.parquet"
OUT_PARQUET = ROOT / "output/l1_fills_london_fit_dedup.parquet"

WINDOW_MIN = 15.0        # declared: entry TFs span 1-5 min, a cluster re-trips within a few bars
PRICE_PT = 5.0           # declared: ~one median intended stop (4.00 pt)
TF_RANK = {"1min": 1, "2min": 2, "3min": 3, "5min": 5}


def assign(F: pd.DataFrame) -> pd.DataFrame:
    """Attach setup_id + both tie-break flags. Unfilled rows carry setup_id -1."""
    F = F.copy()
    F["setup_id"] = -1
    F["setup_size"] = 0
    fl = F[F["arm_none"]].copy()
    fl["fill_ts"] = pd.to_datetime(fl["fill_ts"], utc=True, format="mixed")
    fl["names"] = fl["cluster_members"].map(
        lambda s: frozenset(m[0] for m in json.loads(s or "[]")))
    fl = fl.sort_values(["day", "direction", "fill_ts", "tf"])

    sid = 0
    assign_map: dict[int, int] = {}
    for (_day, _dirn), g in fl.groupby(["day", "direction"], sort=False):
        open_setups: list[dict] = []          # {id, ts0, px0, names}
        for r in g.itertuples():
            hit = None
            for s in open_setups:
                if (r.fill_ts - s["ts0"]).total_seconds() / 60.0 > WINDOW_MIN:
                    continue
                if (r.names & s["names"]) or abs(r.fill_px - s["px0"]) <= PRICE_PT:
                    hit = s
                    break
            if hit is None:
                sid += 1
                open_setups.append({"id": sid, "ts0": r.fill_ts, "px0": r.fill_px,
                                    "names": r.names})
                hit = open_setups[-1]
            else:
                # a setup's identity grows with its members: a 3-min trigger sharing the
                # POC pulls in a later 5-min trigger sharing only the BB basis
                hit["names"] = hit["names"] | r.names
            assign_map[r.Index] = hit["id"]
            open_setups = [s for s in open_setups
                           if (r.fill_ts - s["ts0"]).total_seconds() / 60.0 <= WINDOW_MIN]

    F.loc[list(assign_map), "setup_id"] = list(assign_map.values())
    sizes = F[F.setup_id > 0].groupby("setup_id").size()
    F["setup_size"] = F["setup_id"].map(sizes).fillna(0).astype(int)

    # tie-breaks
    D = F[F.setup_id > 0].copy()
    D["fill_ts_p"] = pd.to_datetime(D["fill_ts"], utc=True, format="mixed")
    D["rank_tf"] = D["tf"].map(TF_RANK)
    first_ix = D.sort_values(["setup_id", "fill_ts_p", "rank_tf"]).groupby(
        "setup_id").head(1).index
    htf_ix = D.sort_values(["setup_id", "rank_tf", "fill_ts_p"],
                           ascending=[True, False, True]).groupby("setup_id").head(1).index
    F["setup_first"] = F.index.isin(first_ix)
    F["setup_htf"] = F.index.isin(htf_ix)
    return F


def main() -> int:
    F = pd.read_parquet(IN_PARQUET)
    F = assign(F)
    F.to_parquet(OUT_PARQUET, index=False)
    fl = F[F.arm_none]
    nd = F["day"].nunique()
    ns = int(F.loc[F.setup_id > 0, "setup_id"].nunique())

    print(f"wrote {OUT_PARQUET.relative_to(ROOT)}")
    print(f"\nfills {len(fl):,} over {nd} sessions ({len(fl)/nd:.1f}/session)")
    print(f"distinct SETUPS {ns:,} ({ns/nd:.1f}/session) — "
          f"{1 - ns/len(fl):.0%} of the fill population was the same trade counted again")
    print(f"\nsetup size (fills collapsed into one position):")
    print(F[F.setup_first].setup_size.value_counts().sort_index().to_string())
    print(f"\n{'arm':<22}{'n':>8}{'/session':>10}   timeframe mix")
    for lbl, col in (("as walked (no dedup)", "arm_none"),
                     ("setup_first (DEFAULT)", "setup_first"),
                     ("setup_htf (challenger)", "setup_htf")):
        K = F[F[col]]
        mix = " ".join(f"{t.replace('min','m')} {(K.tf==t).mean():.0%}"
                       for t in ("1min", "2min", "3min", "5min"))
        print(f"{lbl:<22}{len(K):>8,}{len(K)/nd:>10.1f}   {mix}")
    for lbl, col in (("setup_first", "setup_first"), ("setup_htf", "setup_htf")):
        K = F[F[col]]
        print(f"\n{lbl}: pattern " + " ".join(
            f"{p} {(K.pattern==p).mean():.0%}" for p in ("B2", "B", "A"))
            + f" | median intended risk {K.risk_intended.median():.2f} pt"
            + f" | below 9.5pt {(K.risk_intended < 9.5).mean():.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
