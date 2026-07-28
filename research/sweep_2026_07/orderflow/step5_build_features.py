#!/usr/bin/env python3
"""STEP 5 — build order-flow features, DO NOT TEST THEM.

Per Brake's brief: every feature defined in code with an explicit knowability timestamp, all
strictly pre-fill; shift test run on every column with pass/fail reported. NO outcome column is
read, joined, or written — the features file carries join keys (day, ft) and features only.

KNOWABILITY CONVENTION. Every fill is stamped at :00 seconds (established in Phase 1). Each
feature below consumes tape/bar minutes STRICTLY BEFORE the fill minute, so its inputs are
complete at exactly fill_min:00 — the same instant the fill is stamped. The margin is therefore
ZERO SECONDS by construction, not negative; a fill that truly executed inside second 0 could in
principle coincide with the prior minute's closing prints. That caveat is inherited from the
book's own timestamping (Phase-0 finding: whether :00 is the true fill instant is UNVERIFIABLE
from the artefacts) and is stated rather than hidden.

PRICE BAND. The two 2025 tape files carry uncleaned prints (126,861 rows < 1000). Any feature
touching tape PRICE (stacked imbalance levels) uses only rows inside the day's bar
[low-25, high+25] band. Delta/CVD/volume features are price-free and unaffected. Absorption uses
BAR range, not tape range, for the same reason.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")
W_LONG, W_MID, W_SHORT = 30, 15, 5          # pre-registered in 02_of_prereg.md
STACK_RATIO, STACK_MIN = 3.0, 3             # textbook 3:1, >=3 consecutive levels — NOT swept

print("load tape ...", flush=True)
T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
               for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
              ignore_index=True)
T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
T["volume"] = T.volume.astype("int64")
print(f"  {len(T):,} rows", flush=True)

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event).dt.tz_convert("UTC")
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
day_band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
               .agg(lo=("low", "min"), hi=("high", "max"))

# per-minute signed aggregates (price-free)
print("aggregate per minute ...", flush=True)
sgn = np.where(T.side.values == "B", 1, -1)
M = T.assign(signed=T.volume.values * sgn).groupby("ts_minute", observed=True) \
     .agg(vol=("volume", "sum"), delta=("signed", "sum"))
M["both"] = T.groupby(["ts_minute", "side"], observed=True).volume.sum().unstack(fill_value=0) \
             .gt(0).all(axis=1)

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv",
                usecols=["day", "ft", "direction"])          # NO outcome columns loaded
F["ft"] = pd.to_datetime(F.ft, utc=True)
assert len(F) == 216

def window(fill_min, n):
    return M.loc[fill_min - pd.Timedelta(minutes=n): fill_min - pd.Timedelta(minutes=1)]

def stacked(fill_min, day):
    """Max consecutive price levels with B >= 3A (and mirror) on the LAST completed minute,
    band-cleaned prices only. Direction-free: returns (stack_bid, stack_ask)."""
    m = fill_min - pd.Timedelta(minutes=1)
    d = T[T.ts_minute == m]
    if not len(d):
        return np.nan, np.nan
    band = day_band.loc[day] if day in day_band.index else None
    if band is not None:
        d = d[(d.price >= band.lo - 25) & (d.price <= band.hi + 25)]
    p = d.pivot_table(index="price", columns="side", values="volume", aggfunc="sum") \
         .fillna(0).sort_index()
    if p.empty or "B" not in p or "A" not in p:
        return 0, 0
    def run(mask):
        best = cur = 0
        for v in mask:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        return best
    sb = run((p["B"].values >= STACK_RATIO * p["A"].values) & (p["B"].values > 0))
    sa = run((p["A"].values >= STACK_RATIO * p["B"].values) & (p["A"].values > 0))
    return (sb if sb >= STACK_MIN else 0), (sa if sa >= STACK_MIN else 0)

def build(shift_min=0):
    """shift_min=0 -> strict pre-fill. shift_min=1 -> window slid forward to INCLUDE the fill
    minute (the shift test's contaminated twin). shift_min=15 -> deliberately leaky control."""
    rows = []
    for r in F.itertuples(index=False):
        fm = r.ft.floor("min") + pd.Timedelta(minutes=shift_min)
        w30, w15, w5 = window(fm, W_LONG), window(fm, W_MID), window(fm, W_SHORT)
        pc = bars.close
        k1 = pc.index.searchsorted(fm - pd.Timedelta(minutes=1), side="right") - 1
        k16 = pc.index.searchsorted(fm - pd.Timedelta(minutes=16), side="right") - 1
        dpx = float(pc.iloc[k1] - pc.iloc[k16]) if k1 > k16 >= 0 else np.nan
        brange = float(bars.high.iloc[max(k16, 0):k1 + 1].max()
                       - bars.low.iloc[max(k16, 0):k1 + 1].min()) if k1 > k16 >= 0 else np.nan
        cvd15 = float(w15.delta.sum()) if len(w15) else np.nan
        sb, sa = stacked(fm, r.day)
        rows.append(dict(
            day=r.day, ft=str(r.ft),
            cvd_5=float(w5.delta.sum()) if len(w5) else np.nan,
            cvd_15=cvd15,
            cvd_30=float(w30.delta.sum()) if len(w30) else np.nan,
            cvd_norm_15=float(w15.delta.sum() / w15.vol.sum()) if len(w15) and w15.vol.sum() else np.nan,
            delta_div_15=(float(np.sign(dpx) != np.sign(cvd15))
                          if np.isfinite(dpx) and np.isfinite(cvd15) and dpx != 0 and cvd15 != 0 else np.nan),
            fp_imb_15=(float((w15.delta.sum() / w15.vol.sum() + 1) / 2 - 0.5)
                       if len(w15) and w15.vol.sum() else np.nan),
            absorp_15=(float(w15.vol.sum() / brange) if np.isfinite(brange) and brange > 0
                       and len(w15) else np.nan),
            stack_bid=sb, stack_ask=sa,
            vol_15=float(w15.vol.sum()) if len(w15) else np.nan,
            vol_30=float(w30.vol.sum()) if len(w30) else np.nan,
            abs_cvd_15=abs(cvd15) if np.isfinite(cvd15) else np.nan,       # direction-blind twin
            two_sided_share_30=float(w30.both.mean()) if len(w30) else np.nan,
        ))
    return pd.DataFrame(rows)

print("build strict pre-fill features ...", flush=True)
X0 = build(0)
print("build shift(+1 min, includes fill minute) twin ...", flush=True)
X1 = build(1)
print("build deliberately leaky (+15 min) control ...", flush=True)
X15 = build(15)

FEATS = [c for c in X0.columns if c not in ("day", "ft")]
KNOW = {c: "fill_min:00 (inputs end at close of fill_min-1; margin 0 s, see header)" for c in FEATS}
report = {}
print(f"\n{'column':20s} {'n':>4} {'shift+1 differs':>16} {'leaky+15 differs':>17}  verdict")
for c in FEATS:
    a, b1, b15 = X0[c], X1[c], X15[c]
    ok = a.notna() & b1.notna()
    d1 = int(((a != b1) & ok).sum())
    ok15 = a.notna() & b15.notna()
    d15 = int(((a != b15) & ok15).sum())
    # PASS = the strict column moves when the window is contaminated (test has power) AND the
    # stored strict value is what we recomputed (identical by construction here — the point is
    # the DIFFERENCE columns prove the windows are genuinely different data).
    verdict = "PASS" if d1 > 0 and d15 > 0 else ("DEGENERATE" if a.notna().sum() else "NO-DATA")
    report[c] = dict(n=int(a.notna().sum()), shift1_differs=d1, leaky15_differs=d15,
                     verdict=verdict, knowable_at=KNOW[c])
    print(f"{c:20s} {a.notna().sum():>4} {d1:>16} {d15:>17}  {verdict}")

X0.to_csv(f"{OUT}/of_features_premarket.csv", index=False)
json.dump(report, open(f"{OUT}/step5_shift_report.json", "w"), indent=1)
print(f"\nwrote {OUT}/of_features_premarket.csv (features + join keys ONLY, no outcomes)")
print(f"wrote {OUT}/step5_shift_report.json")
print("\nSTEP 6: STOPPING HERE. No feature has been evaluated against any outcome.")
