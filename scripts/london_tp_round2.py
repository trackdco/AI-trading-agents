#!/usr/bin/env python3
"""LONDON Trend Pullback — ROUND 2: the combinations round 1 points at, plus the order-flow reality check.

Round 1 (london_tp_variants.py) found:
  - first-touch(1) is the mechanism fix: 2024 -$28,320 -> -$4,500, TRAIN ~flat, TEST still positive
  - VWAP-side raises E[R] everywhere (TEST +0.425 -> +0.483) and cuts 2024 by 43%
  - fixed ATR brackets HURT everywhere (the friend's bracket half is rejected; the first-touch half earns its place)
  - trend-alone (volume rule removed) makes MORE test dollars (+$80,180) at lower E[R]

This runs the intersections of the survivors, then computes the strict pre-fill CVD confirm on the
subset of trades where tape exists (2025-06-02+). ORDER FLOW CANNOT TOUCH 2024: the repo's CVD and
depth data begin 2025-06. That is a data-availability fact, not a modelling choice.

CUMULATIVE-MULTIPLICITY WARNING: round 2 is fitted with knowledge of round 1's test-set readouts,
so TEST is no longer a virgin holdout for these cells. Anything promoted is a candidate to
forward-validate, not a ship.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_tp_round2.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")

spec = importlib.util.spec_from_file_location("tpv", os.path.join(os.path.dirname(__file__), "london_tp_variants.py"))
tpv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tpv)          # builds bars/M/CAND and defines run()/block()

R2 = [
    ("R1 V0 + ft1 + VWAP",                dict(filt=lambda c: c["ft1"] and c["vwap_ok"])),
    ("R2 V0 + ft1 + VWAP + day-stop",     dict(filt=lambda c: c["ft1"] and c["vwap_ok"], daystop=True)),
    ("R3 V0 + ft1, target 2R",            dict(filt=lambda c: c["ft1"], tg=2.0)),
    ("R4 V0 + ft1 + onrange>=100",        dict(filt=lambda c: c["ft1"] and np.isfinite(c["onrange"]) and c["onrange"] >= 100)),
    ("R5 trend-alone + ft1 (1-pos)",      dict(need_fading=False, filt=lambda c: c["ft1"], one_pos=True)),
    ("R6 trend-alone + ft1 + VWAP (1-pos)", dict(need_fading=False, filt=lambda c: c["ft1"] and c["vwap_ok"], one_pos=True)),
    ("R7 V0 + ft1 + day-stop",            dict(filt=lambda c: c["ft1"], daystop=True)),
    ("R8 V0 + ft1 + room>=75pt",          dict(filt=lambda c: c["ft1"] and np.isfinite(c["pd_room"]) and c["pd_room"] >= 75)),
]

print("\n" + "=" * 100)
print("ROUND 2 — intersections of round-1 survivors")
print("=" * 100)
summary = []
for name, kw in R2:
    df = tpv.run(**kw)
    st = tpv.block(df, name)
    summary.append(dict(variant=name,
                        n=st.get("TRAIN", (0, 0, 0))[0] + st.get("TEST", (0, 0, 0))[0],
                        y2024=st.get("2024", (0, 0.0, 0.0))[1],
                        train=st.get("TRAIN", (0, 0.0, 0.0))[1],
                        test=st.get("TEST", (0, 0.0, 0.0))[1],
                        testER=st.get("TEST", (0, 0.0, np.nan))[2]))
Rs = pd.DataFrame(summary)
print("\n" + "=" * 100)
print(f"{'variant':<38} {'n':>5} {'2024$':>10} {'TRAIN$':>10} {'TEST$':>10} {'TEST E[R]':>10}")
for _, r in Rs.sort_values("y2024", ascending=False).iterrows():
    print(f"{r.variant:<38} {r.n:>5} {r.y2024:>+10,.0f} {r.train:>+10,.0f} "
          f"{r.test:>+10,.0f} {r.testER:>+10.3f}")
Rs.to_csv(f"{S}/london_tp_round2.csv", index=False)

# ---------------- ORDER FLOW: strict pre-fill CVD on the trades where tape exists -------------
print("\n" + "=" * 100)
print("ORDER FLOW (CVD) — only computable for trades on/after 2025-06-02; 2024 HAS NO TAPE IN THE REPO")
print("=" * 100)
import glob
parts = []
for f in sorted(glob.glob(f"{WT}/data/reference/cvd/footprint_*.parquet")):
    d = pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
    d["s"] = np.where(d.side == "B", d.volume.astype(float), -d.volume.astype(float))
    parts.append(d.groupby("ts_minute")["s"].sum())
    del d
delta = pd.concat(parts).groupby(level=0).sum().sort_index()
delta.index = pd.to_datetime(delta.index, utc=True)
d3 = delta.rolling(3).sum()
d30 = delta.rolling(30).sum()

V0 = tpv.run()                                   # the committed book
V0 = V0[V0.day >= "2025-06-02"].reset_index(drop=True)
uts = tpv.M.ts


def flags(row):
    t = pd.Timestamp(uts.iloc[int(row.i)]).tz_convert("UTC") - pd.Timedelta(minutes=1)  # strict pre-fill
    v3, v30 = d3.get(t, np.nan), d30.get(t, np.nan)
    dr = row.dr
    return pd.Series(dict(
        c3=(v3 > 0 if dr > 0 else v3 < 0) if np.isfinite(v3) else np.nan,
        c30=(v30 > 0 if dr > 0 else v30 < 0) if np.isfinite(v30) else np.nan))


F = pd.concat([V0, V0.apply(flags, axis=1)], axis=1)
print(f"trades with tape coverage: {int(F.c3.notna().sum())}/{len(F)} "
      f"(Jan-2026 is a known gap)")
for col, nm in (("c3", "3-min delta agrees (strict pre-fill)"), ("c30", "30-min delta agrees")):
    s = F[F[col].notna()]
    a_, b_ = s[s[col] == True], s[s[col] == False]   # noqa: E712
    if len(a_) > 4 and len(b_) > 4:
        print(f"  {nm:38s} agree n={len(a_):3d} E[R] {a_.R.mean():+.3f} WR {100*(a_.R>0).mean():3.0f}%   "
              f"disagree n={len(b_):3d} E[R] {b_.R.mean():+.3f} WR {100*(b_.R>0).mean():3.0f}%   "
              f"gap {a_.R.mean()-b_.R.mean():+.3f}R")
print("\nNOTE: this subset is 2025-06+ only — the good regime. A gap here says nothing about 2024,")
print("and the sibling 10-13 book's full order-flow campaign found nothing that beat its noise floor.")
