#!/usr/bin/env python3
"""END-TO-END verification of the LIVE lane on real days.

`tests/test_canon_scorer_ny.py` proves the scorer reproduces the book from the book's own
feature columns. This proves the rest of the live chain: real bars and real tape streamed
through `CanonIngestor` minute by minute, features assembled by the LIVE code path
(`src/canon/features.py` via `ingestor.feature_row`), mapped by the LIVE lane
(`src/canon/ny_lane.py`), and scored by the LIVE scorer — then diffed against
`scripts/funded_book.py` for the same days.

Anything this reproduces is verified live-path. Anything it cannot is stated, not glossed:

  DEPTH IS INJECTED FROM THE BATCH ARCHIVE, NOT FROM THE LIVE BOOK.
  `ReplaySource` streams bars and tape but never calls `on_depth`, and the batch depth
  archive is per-snapshot CSVs rather than an event stream, so there is no way to drive the
  live `DepthBook` from history. This script therefore hands the depth family the same frame
  the batch used (`features.load_depth_day`). Consequence: the wall gates W and D — which are
  LOAD-BEARING for both sessions — are verified here as FEATURES, but the live
  `.depth` -> DepthBook -> long_form path that will feed them in production is NOT verified by
  this script. That parity check is a separate, required gate before arming.

    python -m scripts.ny_lane_replay --span fit --days 8
    python -m scripts.ny_lane_replay --day 2026-04-20 --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import funded_book as fb                              # noqa: E402
from scripts.build_l2_outcomes import load_bars                    # noqa: E402
from scripts.score_canon_span import depth_file                    # noqa: E402
from src.canon.features import depth_at                            # noqa: E402
from src.canon.ingestor import CanonIngestor, ReplaySource         # noqa: E402
from src.canon.ny_lane import NYLane, session_day       # noqa: E402
from src.canon.scorer_ny import PROFILES                           # noqa: E402

class NoData(RuntimeError):
    """The harness cannot honestly evaluate this day — reported as SKIP, never as a DIFF."""


NY = "America/New_York"
DEPTH_DIRS = {"fit": ["data/reference/depth_2025", "data/reference/depth_2026",
                      "data/reference/depth_apr2026"],
              "holdout": ["data/reference/depth_2023_24"]}


class DepthInjectingIngestor(CanonIngestor):
    """CanonIngestor whose depth family reads the BATCH archive for the day.

    This is the one seam replay cannot drive honestly (see the module docstring). Everything
    else — tape, VWAP geometry, badpa/trigdens, bp5opp, lon_slope, on_extreme_age — comes from
    the live code path over streamed minutes."""

    def __init__(self, depth_frame: pd.DataFrame | None, **kw):
        super().__init__(**kw)
        self._dep = depth_frame

    def feature_row(self, fill_ts, entry, direction, trigger_times=None) -> dict:
        f = super().feature_row(fill_ts, entry, direction, trigger_times=trigger_times)
        if self._dep is not None:
            f.update(depth_at(self._dep, pd.Timestamp(fill_ts).tz_convert(NY),
                              float(entry), direction))
        return f


def load_depth(span: str, day: str) -> pd.DataFrame | None:
    p = depth_file([ROOT / d for d in DEPTH_DIRS[span]], day)
    if p is None:
        return None
    d = pd.read_csv(p)
    d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
    return d


def replay_day(span: str, day: str, cands: pd.DataFrame, bars: pd.DataFrame,
               fp: pd.DataFrame, profile, buffer: float, trig=None,
               verbose: bool = False) -> list[dict]:
    """Stream one session day and run the lane over that day's real candidate fills."""
    sess0 = pd.Timestamp(f"{day} 00:00", tz=NY) - pd.Timedelta(hours=6)
    end = pd.Timestamp(f"{day} 11:00", tz=NY)
    b = bars[(bars.ts_event >= sess0) & (bars.ts_event <= end)]
    t = fp[(fp.index >= sess0) & (fp.index <= end)]
    if b.empty:
        raise NoData(f"{day}: no bars in the session window")
    if t.empty:
        # output/fp_minutes.parquet covers 2025-06..2026-07 only. Without the tape the
        # delta/CVD family is absent, so Tc and T2 read 0 and every score is understated —
        # the run would print plausible-looking DIFFs that say nothing about the lane. Refuse.
        raise NoData(f"{day}: no footprint tape (fp_minutes covers 2025-06..2026-07 only)")
    ing = DepthInjectingIngestor(load_depth(span, day))
    ReplaySource(b, t).drive(ing)

    lane = NYLane(ingestor=ing, profile=profile)
    lane.start_day(day, buffer=buffer)
    out = []
    live: list[tuple] = []
    for r in cands.itertuples():
        for item in [x for x in live if x[0] <= r.fill]:
            lane.on_exit(item[1], pl=item[2])
            live.remove(item)
        # risk_pts EXPLICITLY: `entry`/`stop` are the trigger's reference levels and
        # disagree with the canon's realized risk on 28% of trades. Live, this comes from the
        # bracket as placed; here it comes from the same column the book sized on.
        v = lane.on_candidate(fill_ts=r.fill, entry=r.entry, stop=r.stop,
                              direction=r.direction, trigger_times=trig,
                              struct_event=r.struct_event, risk_pts=r.risk)
        if verbose:
            print(f"    {r.fill.tz_convert(NY):%H:%M} {r.direction:<5} {v['window']:<4} "
                  f"take={v['take']!s:<5} tier={v['conviction']} micros={v['micros']:<3} "
                  f"{','.join(v['reasons'])}")
        if v["take"]:
            lane.confirm(v)
            pl = v["micros"] * r.dollars_1lot / 10.0
            live.append((r.exit, v, pl))
            out.append({"day": day, "fill": r.fill, "sess": v["window"],
                        "tier": v["conviction"], "micros": v["micros"], "pl": pl})
    for item in live:
        lane.on_exit(item[1], pl=item[2])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
    ap.add_argument("--profile", default="lucid", choices=sorted(PROFILES))
    ap.add_argument("--day", default=None, help="one session day; else --days most recent")
    ap.add_argument("--days", type=int, default=8)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    book = fb.run(fb.load_book(a.span), a.profile)
    S = pd.read_parquet(ROOT / f"output/aikido_{a.span}.parquet").copy()
    S["fill"] = pd.to_datetime(S.fill_ts, format="mixed", utc=True)
    S["exit"] = pd.to_datetime(S.exit_ts, format="mixed", utc=True)
    S = S.sort_values("fill", kind="mergesort")

    days = [a.day] if a.day else sorted(book.day.unique())[-a.days:]
    bars = load_bars()
    bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    # trigdens_30 counts ALL triggers in the census, not just validated ones — the same
    # source scripts/build_l3_features.py feeds it. Anything else understates the density.
    C = pd.read_parquet(ROOT / f"output/l0_triggers_{a.span}.parquet", columns=["ts"])
    C["ts"] = pd.to_datetime(C.ts, utc=True)
    C["day"] = [session_day(t) for t in C.ts]        # the census carries no day column

    print(f"LIVE-LANE REPLAY [{a.span} · {a.profile}] — {len(days)} day(s)\n"
          f"  depth injected from the batch archive (the one seam replay cannot drive)\n")
    tot_match = tot_days = skipped = 0
    for day in days:
        cands = S[(S.day == day) & S.valid]
        want = book[book.day == day]
        stamps = sorted(C.ts[C.day == day])
        try:
            got = replay_day(a.span, day, cands, bars, fp, PROFILES[a.profile],
                             buffer=2_000.0, trig=(stamps or None), verbose=a.verbose)
        except NoData as e:
            print(f"  SKIP {day}  {e}")
            skipped += 1
            continue
        G = pd.DataFrame(got)
        ok = len(G) == len(want)
        if ok and len(G):
            ok = (np.allclose(G.tier.to_numpy(), want.tier.to_numpy())
                  and np.allclose(G.micros.to_numpy(), want.micros.to_numpy()))
        tot_days += 1
        tot_match += bool(ok)
        flag = "OK  " if ok else "DIFF"
        print(f"  {flag} {day}  live {len(G):>2} trades / book {len(want):>2}"
              f"{'' if ok else '   <-- investigate'}")
    print(f"\n  {tot_match}/{tot_days} days reproduce the book through the live lane"
          + (f"  ({skipped} skipped — no data)" if skipped else ""))
    if tot_match != tot_days:
        print("  NOT CLEAN — do not arm. Diff the failing day with --day <d> --verbose")


if __name__ == "__main__":
    main()
