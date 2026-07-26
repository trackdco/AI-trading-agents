#!/usr/bin/env python3
"""SMA-AS-BIAS test on the engine substrate — the user's proposed architecture inversion.

The trend-pullback book uses the 50-SMA touch as the ENTRY. The proposal: enter off a DIFFERENT
confluence and use the SMA stack only as short-term BIAS. The engine substrate is exactly that
universe: 3,005 fills 2023-01 -> 2026-07 whose entries are cluster retests / displacements
(BB MA, daily-VWAP dev bands, POC) under two management books, with no MA logic anywhere.

This grades every substrate fill by the M15 SMA state at the LAST CLOSED bar before the fill:
  FULL stack  ma20 > ma50 > ma200 (or mirror)   -- the trend-pullback book's regime definition
  LIGHT stack ma20 > ma50 only                  -- "more short-term bias", per the proposal
  aligned / opposed / flat(no stack)            -- vs the trade's direction

Splits: HOLDOUT = 2023-01..2025-06 (2,090 fills, never used to build anything) vs
IS = 2025-07+ (915). The raw substrate loses ~$114k at 26% WR by design (Angus's raw substrates
were breakeven-to-negative too) -- the question is whether SMA-bias isolates a subset that works
ACROSS YEARS, which no entry-off-the-SMA variant managed.

No lookahead: the M15 bar labelled T (label='right') is closed at T; a fill at any 1-minute time
uses the latest label <= fill time.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_substrate_bias.py
"""
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
NY = "America/New_York"
PV = 20.0

print("load substrate + bars ...", flush=True)
F = pd.read_parquet(f"{S}/london_engine_substrate.parquet")
F["fill_ts"] = pd.to_datetime(F.fill, utc=True).dt.tz_convert(NY)
F["risk"] = (F.entry - F.stop).abs()
F = F[F.risk >= 1.0].copy()                     # a sub-1pt stop is an engine artefact, not a trade
F["R"] = F.dollars / (F.risk * PV)

bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    close=("close", "last")).dropna()
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m = m.dropna()
labels = m.index.values
ma20, ma50, ma200 = m.ma20.values, m.ma50.values, m.ma200.values

ix = np.searchsorted(labels, F.fill_ts.values, side="right") - 1
ok = ix >= 0
F, ix = F[ok].reset_index(drop=True), ix[ok]
up_full = (ma20[ix] > ma50[ix]) & (ma50[ix] > ma200[ix])
dn_full = (ma20[ix] < ma50[ix]) & (ma50[ix] < ma200[ix])
up_lite = ma20[ix] > ma50[ix]
dr = np.where(F.direction.values == "long", 1, -1)
F["bias_full"] = np.select([up_full & (dr > 0) | dn_full & (dr < 0),
                            up_full & (dr < 0) | dn_full & (dr > 0)],
                           ["aligned", "opposed"], default="flat")
F["bias_lite"] = np.where(up_lite == (dr > 0), "aligned", "opposed")
F["year"] = F.day.str[:4]


def line(s, lab):
    if len(s) < 5:
        print(f"      {lab:<9} n={len(s):5d}   (too few)"); return
    print(f"      {lab:<9} n={len(s):5d}  WR {100*(s.R>0).mean():3.0f}%  "
          f"E[R] {s.R.mean():+.3f}  net ${s.dollars.sum():+10,.0f}")


if __name__ == "__main__":
    print(f"fills graded: {len(F)}  (HOLDOUT {int(F.oos.sum())} / IS {int((1-F.oos).sum())})")
    for bias in ("bias_full", "bias_lite"):
        print(f"\n{'='*88}\n{bias.upper()}  — SMA stack as bias only, entries stay the engine's confluences\n{'='*88}")
        for split, sub in (("HOLDOUT 2023-01..2025-06", F[F.oos == 1]),
                           ("IS 2025-07+", F[F.oos == 0])):
            print(f"    {split}:")
            for lab in ("aligned", "opposed", "flat"):
                s = sub[sub[bias] == lab]
                if len(s):
                    line(s, lab)
    print(f"\n{'='*88}\nALIGNED (full stack) per year — the cross-regime question\n{'='*88}")
    A = F[F.bias_full == "aligned"]
    for yr in sorted(F.year.unique()):
        line(A[A.year == yr], yr)
    print("\n    per book (aligned, full):")
    for bk in ("E3", "E4"):
        line(A[A.book == bk], bk)
    print("\n    per pattern (aligned, full)  [A=reversal, B=continuation, B2=fade]:")
    for pt in ("A", "B", "B2"):
        line(A[A.pattern == pt], pt)
    print("\n    OPPOSED, per pattern (does counter-trend want the stack AGAINST it?):")
    O = F[F.bias_full == "opposed"]
    for pt in ("A", "B", "B2"):
        line(O[O.pattern == pt], pt)
