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


def assign(F: pd.DataFrame, prefix: str = "setup", eligible=None) -> pd.DataFrame:
    """Attach <prefix>_id + both tie-break flags. Ineligible/unfilled rows carry id -1.

    `eligible` is a boolean mask applied BEFORE grouping, not after. Order matters: a
    trigger the spec does not admit must not be able to claim a setup and block a valid
    trigger queued behind it. (ANGUS 2026-08-05 on the VWAP touch — it is part of the
    trigger definition, so it filters first.)
    """
    F = F.copy()
    F[f"{prefix}_id"] = -1
    F[f"{prefix}_size"] = 0
    keep = F["arm_none"] if eligible is None else (F["arm_none"] & eligible)
    fl = F[keep].copy()
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

    F.loc[list(assign_map), f"{prefix}_id"] = list(assign_map.values())
    sizes = F[F[f"{prefix}_id"] > 0].groupby(f"{prefix}_id").size()
    F[f"{prefix}_size"] = F[f"{prefix}_id"].map(sizes).fillna(0).astype(int)

    # tie-breaks
    D = F[F[f"{prefix}_id"] > 0].copy()
    D["fill_ts_p"] = pd.to_datetime(D["fill_ts"], utc=True, format="mixed")
    D["rank_tf"] = D["tf"].map(TF_RANK)
    first_ix = D.sort_values([f"{prefix}_id", "fill_ts_p", "rank_tf"]).groupby(
        f"{prefix}_id").head(1).index
    htf_ix = D.sort_values([f"{prefix}_id", "rank_tf", "fill_ts_p"],
                           ascending=[True, False, True]).groupby(f"{prefix}_id").head(1).index
    F[f"{prefix}_first"] = F.index.isin(first_ix)
    F[f"{prefix}_htf"] = F.index.isin(htf_ix)
    return F


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="",
                    help="census arm suffix, e.g. `_pp`. Suffixes input AND output.")
    a = ap.parse_args()
    src = IN_PARQUET.with_name(f"l1_fills_london_fit{a.arm}.parquet")
    dst = OUT_PARQUET.with_name(f"l1_fills_london_fit{a.arm}_dedup.parquet")
    if not src.exists():
        ap.error(f"{src.relative_to(ROOT)} does not exist — build that L1 arm first")

    F = pd.read_parquet(src)
    nd = F["day"].nunique()

    # `setup_*`  every filled trigger — kept for the record, NOT the default any more
    # `vs_*`     VWAP-REQUIRED, the shipped population (ANGUS 2026-08-05)
    F = assign(F, "setup")
    F = assign(F, "vs", eligible=F["vwap_touched"])
    F.to_parquet(dst, index=False)

    print(f"wrote {dst.relative_to(ROOT)}\n")
    print(f"fills {int(F.arm_none.sum()):,} over {nd} sessions")
    for pre, lbl in (("setup", "any trigger (superseded)"),
                     ("vs", "VWAP touched/closed through (DEFAULT)")):
        n = int(F.loc[F[f"{pre}_id"] > 0, f"{pre}_id"].nunique())
        print(f"  {lbl:<42} {n:>6,} setups  {n/nd:>5.2f}/session")
    print(f"\n{'arm':<26}{'n':>8}{'/session':>10}   timeframe mix")
    for lbl, col in (("as walked (no dedup)", "arm_none"),
                     ("setup_first (superseded)", "setup_first"),
                     ("vs_first  (DEFAULT)", "vs_first"),
                     ("vs_htf    (challenger)", "vs_htf")):
        K = F[F[col]]
        mix = " ".join(f"{t.replace('min','m')} {(K.tf==t).mean():.0%}"
                       for t in ("1min", "2min", "3min", "5min"))
        print(f"{lbl:<26}{len(K):>8,}{len(K)/nd:>10.2f}   {mix}")
    for lbl, col in (("vs_first", "vs_first"), ("vs_htf", "vs_htf")):
        K = F[F[col]]
        print(f"\n{lbl}: pattern " + " ".join(
            f"{p} {(K.pattern==p).mean():.0%}" for p in ("B2", "B", "A"))
            + f" | median intended risk {K.risk_intended.median():.2f} pt"
            + f" | below 9.5pt {(K.risk_intended < 9.5).mean():.0%}"
            + f" | median setup size {K.vs_size.median():.0f}")

    # what the ordering actually bought: setups the VWAP rule RESCUED rather than deleted
    old = set(F.loc[F.setup_first, "ts"])
    new = set(F.loc[F.vs_first, "ts"])
    print(f"\nfilter-BEFORE-dedup vs after: {len(new - old):,} entries are triggers that a "
          f"VWAP-less\ntrigger had been blocking — they would have been lost had the rule "
          f"been applied\nafter grouping instead of before.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
