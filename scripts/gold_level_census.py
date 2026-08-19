#!/usr/bin/env python3
"""E1 on GOLD — the NQ level-family census, re-run on GC front month.

Imports ``scripts.htf_ma_level_census`` and calls ITS ``day_rows``, so the fight
grammar, the as-of level construction, the stop rule and the shipped exit are the
incumbent's, not a reimplementation. Only three things change, and each is a property
of the instrument rather than of the method:

    TICK       0.25 (NQ) -> 0.10 (GC minimum increment)
    COST_PTS   0.50 (NQ) -> set by --cost, swept, because gold friction is unmeasured
    bars       NQ front month -> GC front month, 2023-01 .. 2026-08

W stays the 15m BB width, which is the point: it is an instrument-relative ruler, so
"0.5W of displacement" means the same thing in both markets without rescaling anything
by hand.

    python scripts/gold_level_census.py [--days N] [--cost 0.2]
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import htf_ma_level_census as C
from src.htf_ma.levels import NY
from src.htf_ma.levels import profile_at_minutes as _profile
from src.research.tomtrades import data as D


def main() -> None:
    n_days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else None
    cost = float(sys.argv[sys.argv.index("--cost") + 1]) if "--cost" in sys.argv else 0.2
    sym = sys.argv[sys.argv.index("--symbol") + 1] if "--symbol" in sys.argv else "gc"
    tick = float(sys.argv[sys.argv.index("--tick") + 1]) if "--tick" in sys.argv else 0.10
    # Volume-profile bin width. levels.profile_at_minutes defaults to 1.0 PRICE UNITS,
    # which is scale-dependent and silently destroys the profile loci off NQ: 1.0 is
    # 4 ticks at NQ's ~20,000, 10 ticks at GC's ~2,600, ~200 ticks at DX's ~102, and
    # larger than the entire instrument at 6J's ~0.0067 — where POC/VAL/VAH produced
    # literally zero fights. Default here anchors to NQ's implied 4 ticks.
    binw = (float(sys.argv[sys.argv.index("--binw") + 1]) if "--binw" in sys.argv
            else 4.0 * tick)

    C.TICK = tick
    # rebind in the census module's namespace rather than editing the NQ module:
    # same technique as overriding TICK, and it leaves the NQ book untouched
    C.profile_at_minutes = functools.partial(_profile, bin_width=binw)
    C.COST_PTS = cost      # round-turn, in points; swept rather than assumed

    gc = D.load(str(ROOT / f"data/{sym}_1m.parquet"))
    bars = (gc.set_index(gc["ts_event"].dt.tz_convert(NY))
              [["open", "high", "low", "close", "volume"]].sort_index())
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    if n_days:
        sess_days = sess_days[-n_days:]
    print(f"{sym.upper()} {len(bars):,} bars · {len(sess_days):,} session-days · "
          f"TICK={C.TICK} COST_PTS={C.COST_PTS} BINW={binw:g}", flush=True)

    rows = []
    for k, d in enumerate(sess_days):
        rows.extend(C.day_rows(bars, d, C.LOCI))
        if k % 100 == 0:
            print(f"  {k}/{len(sess_days)} days · {len(rows):,} fights", flush=True)
    out = pd.DataFrame(rows)
    print(f"fights: {len(out):,}", flush=True)
    p = ROOT / f"output/level_census_{sym}_cost{cost}_bin{binw:g}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(p, index=False)
    print(f"wrote {p}", flush=True)
    print("columns:", list(out.columns))


if __name__ == "__main__":
    main()
