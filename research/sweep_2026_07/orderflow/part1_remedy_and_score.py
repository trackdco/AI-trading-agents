#!/usr/bin/env python3
"""PART 1 — five-feature remedy, exchangeability re-test, then SCORE Q1 and Q2.

BASELINE: the PARTIALLY-REMEDIATED (C only) NEWS-FILTERED arm, 182 pre-market trades.
W and the entire dep_* family remain LEAKY in this book's selection path.

REMEDY (Amendment 3 §7, fixed before any outcome was touched). Every normalizer is built from
a trailing window of the prior TRAIL_DAYS trading days, same time-of-day bucket, closing
STRICTLY BEFORE the fill day — never full-sample, never within-half:
  absorp_atr  = vol_15 / ATR14(prior days)            <- Brake's literal spec
  absorp_rel  = (vol_15/brange) / trailing median of same, same TOD bucket
  vol_15_rel  = vol_15 / trailing median vol_15, same TOD bucket
  vol_30_rel  = vol_30 / trailing median vol_30, same TOD bucket
  stack_*_exc = stack_*_bin - trailing rate of that stack, same TOD bucket
Where two candidate normalizations exist (absorption), the one that is SCORED is chosen by the
exchangeability test alone — an OUTCOME-BLIND criterion. No outcome is consulted in the choice.

fp_imb_15 is DROPPED: it is exactly cvd_norm_15/2, a duplicate test with no new information.

Q1 (re-registered, Amendment 3 §5): PRIMARY = Spearman rank association between each entry
feature and REALIZED R (threshold-free), day-clustered; BINARY-A realized R>=2; BINARY-B
life-window mfe>=4R. Q2 (§6): does entry order flow add anything BEYOND gap size, which is
knowable at 08:00 with no tape at all.

Multiplicity is priced on the EFFECTIVE number of independent tests (Li & Ji eigenvalue
method), not the nominal feature count.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
PAD, TRAIL_DAYS, NPERM = 25.0, 20, 2000
STACK_RATIO, STACK_MIN = 3.0, 3
rng = np.random.default_rng(20260729)
REP = {}

F = pd.read_csv(f"{OUT}/part0_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
print(f"baseline {len(F)} trades | IS {int((~F.oos).sum())} OOS {int(F.oos.sum())}")

# ---------------------------------------------------------------- bars -> per-minute grids
bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
bars = bars.loc["2025-05-01":]
brange16 = bars.high.rolling(16).max().shift(1) - bars.low.rolling(16).min().shift(1)
dpx16 = bars.close.shift(1) - bars.close.shift(16)

# daily ATR14 from prior sessions only
et = bars.index.tz_convert("America/New_York")
bars_d = bars.assign(d=et.strftime("%Y-%m-%d")).groupby("d").agg(
    hi=("high", "max"), lo=("low", "min"), cl=("close", "last"))
tr = pd.concat([bars_d.hi - bars_d.lo, (bars_d.hi - bars_d.cl.shift()).abs(),
                (bars_d.lo - bars_d.cl.shift()).abs()], axis=1).max(axis=1)
ATR14 = tr.rolling(14).mean().shift(1)          # strictly prior sessions

# ---------------------------------------------------------------- tape -> per-minute grids
print("load + band-clean tape ...", flush=True)
T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
               for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
              ignore_index=True)
T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
T["volume"] = T.volume.astype("int64")
band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
           .agg(lo=("low", "min"), hi=("high", "max"))
T["eday"] = T.ts_minute.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
T = T.join(band, on="eday")
T = T[T.hi.isna() | ((T.price >= T.lo - PAD) & (T.price <= T.hi + PAD))]

M = T.assign(signed=T.volume.values * np.where(T.side.values == "B", 1, -1)) \
     .groupby("ts_minute", observed=True).agg(vol=("volume", "sum"), delta=("signed", "sum"))
grid = pd.date_range(M.index.min(), M.index.max(), freq="min", tz="UTC")
M = M.reindex(grid, fill_value=0)
v5 = M.vol.rolling(5).sum().shift(1)
v15 = M.vol.rolling(15).sum().shift(1)
v30 = M.vol.rolling(30).sum().shift(1)
d5 = M.delta.rolling(5).sum().shift(1)
d15 = M.delta.rolling(15).sum().shift(1)
d30 = M.delta.rolling(30).sum().shift(1)
print(f"minute grid {len(M):,}")

# ---------------------------------------------------------------- stacks on every PM minute
print("stacks on all pre-market minutes ...", flush=True)
et_min = T.ts_minute.dt.tz_convert("America/New_York")
hm_min = et_min.dt.hour * 60 + et_min.dt.minute
PMT = T[(hm_min >= 420) & (hm_min < 570)]
piv = PMT.groupby(["ts_minute", "price", "side"], observed=True).volume.sum().unstack(
    "side", fill_value=0)
for c in ("A", "B"):
    if c not in piv:
        piv[c] = 0
piv = piv.sort_index()
codes, uniq = pd.factorize(piv.index.get_level_values(0))
Bv, Av = piv["B"].to_numpy(float), piv["A"].to_numpy(float)
bid_ok = (Bv >= STACK_RATIO * Av) & (Bv > 0)
ask_ok = (Av >= STACK_RATIO * Bv) & (Av > 0)

def runs(mask, codes, n):
    best = np.zeros(n, dtype=int)
    cur = 0
    prev = -1
    for i in range(len(mask)):
        c = codes[i]
        if c != prev:
            cur, prev = 0, c
        cur = cur + 1 if mask[i] else 0
        if cur > best[c]:
            best[c] = cur
    return best

sb = runs(bid_ok, codes, len(uniq))
sa = runs(ask_ok, codes, len(uniq))
STK = pd.DataFrame({"stack_bid_bin": (sb >= STACK_MIN).astype(int),
                    "stack_ask_bin": (sa >= STACK_MIN).astype(int)}, index=uniq).sort_index()
print(f"stack minutes computed: {len(STK):,}")

# ---------------------------------------------------------------- TOD-bucket trailing baselines
def bucket_of(hm):
    return 0 if hm < 510 else (1 if hm < 540 else 2)

idx_et = pd.DatetimeIndex(M.index).tz_convert("America/New_York")
base = pd.DataFrame({"day": idx_et.strftime("%Y-%m-%d"),
                     "hm": idx_et.hour * 60 + idx_et.minute,
                     "v15": v15.values, "v30": v30.values}, index=M.index)
base["absorp_raw"] = base.v15 / brange16.reindex(M.index).values
base = base[(base.hm >= 480) & (base.hm < 570)].copy()
base["buck"] = base.hm.map(bucket_of)
st = STK.reindex(base.index)
base["sbid"] = st.stack_bid_bin.values
base["sask"] = st.stack_ask_bin.values

dayb = base.groupby(["day", "buck"]).agg(
    v15m=("v15", "median"), v30m=("v30", "median"), absm=("absorp_raw", "median"),
    sbr=("sbid", "mean"), sar=("sask", "mean")).reset_index()
dayb = dayb.sort_values("day")

def trailing(dayb, col):
    """Median/mean of `col` over the prior TRAIL_DAYS days for the same bucket, strictly
    before the current day (shift(1) then rolling)."""
    o = {}
    for b, g in dayb.groupby("buck"):
        g = g.sort_values("day")
        r = g[col].shift(1).rolling(TRAIL_DAYS, min_periods=5).median()
        o.update({(d, b): v for d, v in zip(g.day, r)})
    return o

TR = {c: trailing(dayb, c) for c in ("v15m", "v30m", "absm", "sbr", "sar")}

# ---------------------------------------------------------------- fill-level features
print("build features at fills ...", flush=True)
rows = []
for r in F.itertuples(index=False):
    fm = r.ft.floor("min")
    b = bucket_of(int(r.fillhm))
    key = (r.day, b)
    a_raw = float(v15.get(fm, np.nan)) / float(brange16.get(fm, np.nan)) \
        if np.isfinite(brange16.get(fm, np.nan)) and brange16.get(fm, np.nan) > 0 else np.nan
    atr = ATR14.get(r.day, np.nan)
    c15 = float(d15.get(fm, np.nan))
    dp = float(dpx16.get(fm, np.nan))
    sm = STK.reindex([fm - pd.Timedelta(minutes=1)])
    sbid = float(sm.stack_bid_bin.iloc[0]) if sm.stack_bid_bin.notna().iloc[0] else np.nan
    sask = float(sm.stack_ask_bin.iloc[0]) if sm.stack_ask_bin.notna().iloc[0] else np.nan
    tv15, tv30 = TR["v15m"].get(key, np.nan), TR["v30m"].get(key, np.nan)
    tab, tsb, tsa = TR["absm"].get(key, np.nan), TR["sbr"].get(key, np.nan), TR["sar"].get(key, np.nan)
    rows.append(dict(
        day=r.day, ft=str(r.ft), oos=bool(r.oos), R=float(r.R), pl=float(r.pl),
        big_R2=bool(r.big_R2), reach4=bool(r.reach4), gap_abs=float(r.gap_abs),
        gap_pts=float(r.gap_pts), expiry_week=bool(r.expiry_week),
        # --- unchanged (already exchangeable) ---
        cvd_5=float(d5.get(fm, np.nan)), cvd_15=c15, cvd_30=float(d30.get(fm, np.nan)),
        cvd_norm_15=c15 / float(v15.get(fm, np.nan)) if v15.get(fm, 0) else np.nan,
        abs_cvd_15=abs(c15) if np.isfinite(c15) else np.nan,
        delta_div_15=(float(np.sign(dp) != np.sign(c15))
                      if np.isfinite(dp) and np.isfinite(c15) and dp != 0 and c15 != 0 else np.nan),
        # --- pre-remedy (reported for the exchangeability comparison only) ---
        absorp_15=a_raw, vol_15=float(v15.get(fm, np.nan)), vol_30=float(v30.get(fm, np.nan)),
        stack_bid_bin=sbid, stack_ask_bin=sask,
        # --- REMEDIED ---
        absorp_atr=float(v15.get(fm, np.nan)) / atr if np.isfinite(atr) and atr > 0 else np.nan,
        absorp_rel=a_raw / tab if np.isfinite(tab) and tab > 0 else np.nan,
        vol_15_rel=float(v15.get(fm, np.nan)) / tv15 if np.isfinite(tv15) and tv15 > 0 else np.nan,
        vol_30_rel=float(v30.get(fm, np.nan)) / tv30 if np.isfinite(tv30) and tv30 > 0 else np.nan,
        stack_bid_exc=sbid - tsb if np.isfinite(tsb) else np.nan,
        stack_ask_exc=sask - tsa if np.isfinite(tsa) else np.nan,
    ))
X = pd.DataFrame(rows)
X.to_csv(f"{OUT}/part1_features.csv", index=False)

# anchor: unchanged features must reproduce the committed job2 build
prev = pd.read_csv(f"{OUT}/of_features_job2_C_news.csv")
prev["ft"] = pd.to_datetime(prev.ft, utc=True).astype(str)
m = X.merge(prev[["ft", "cvd_15", "vol_15"]], on="ft", how="inner", suffixes=("", "_p"))
agree = np.isclose(m.cvd_15, m.cvd_15_p, atol=1e-6) & np.isclose(m.vol_15, m.vol_15_p, atol=1e-6)
print(f"ANCHOR vs committed job2 features: {int(agree.sum())}/{len(m)} rows identical "
      f"on cvd_15 & vol_15")
REP["anchor_vs_job2"] = f"{int(agree.sum())}/{len(m)}"

# ---------------------------------------------------------------- exchangeability re-test
print("\n" + "=" * 96)
print("EXCHANGEABILITY RE-TEST — IS vs OOS on the RE-FIXED 91/91 split, day-block permutation")
print("=" * 96)
days = X.day.values
u_days = pd.unique(days)
is_m, oos_m = (~X.oos).values, X.oos.values
k_is = len(pd.unique(days[is_m]))

def ks_stat(a, b):
    a, b = np.sort(a[~np.isnan(a)]), np.sort(b[~np.isnan(b)])
    if len(a) < 3 or len(b) < 3:
        return np.nan
    allv = np.concatenate([a, b])
    return float(np.abs(np.searchsorted(a, allv, "right") / len(a)
                        - np.searchsorted(b, allv, "right") / len(b)).max())

def dayblock_p(x):
    obs = ks_stat(x[is_m], x[oos_m])
    if not np.isfinite(obs):
        return obs, np.nan
    hits = 0
    for _ in range(NPERM):
        pick = set(rng.choice(u_days, size=k_is, replace=False))
        m_ = np.array([d in pick for d in days])
        s = ks_stat(x[m_], x[~m_])
        if np.isfinite(s) and s >= obs - 1e-12:
            hits += 1
    return obs, (hits + 1) / (NPERM + 1)

PRE_POST = [("absorp_15", ["absorp_atr", "absorp_rel"]), ("vol_15", ["vol_15_rel"]),
            ("vol_30", ["vol_30_rel"]), ("stack_bid_bin", ["stack_bid_exc"]),
            ("stack_ask_bin", ["stack_ask_exc"])]
exch = {}
print(f"{'feature':16s} {'KS':>6} {'p_perm':>8}  verdict")
for pre, posts in PRE_POST:
    for name in [pre] + posts:
        ks, p = dayblock_p(X[name].values.astype(float))
        v = "PASS" if (np.isfinite(p) and p >= 0.05) else "FAIL"
        exch[name] = dict(ks=ks, p=p, passes=bool(np.isfinite(p) and p >= 0.05),
                          remedied=name != pre)
        tag = "  (pre-remedy)" if name == pre else "  <- REMEDIED"
        print(f"{name:16s} {ks:>6.3f} {p:>8.4f}  {v}{tag}")
UNCH = ["cvd_5", "cvd_15", "cvd_30", "cvd_norm_15", "abs_cvd_15", "delta_div_15"]
for name in UNCH:
    ks, p = dayblock_p(X[name].values.astype(float))
    exch[name] = dict(ks=ks, p=p, passes=bool(np.isfinite(p) and p >= 0.05), remedied=False)
    print(f"{name:16s} {ks:>6.3f} {p:>8.4f}  {'PASS' if p>=0.05 else 'FAIL'}  (unchanged)")
REP["exchangeability"] = exch

# OUTCOME-BLIND choice of absorption normalization
abs_choice = "absorp_atr" if exch["absorp_atr"]["passes"] else (
    "absorp_rel" if exch["absorp_rel"]["passes"] else "absorp_rel")
print(f"\nabsorption scored as: {abs_choice}  (chosen on the exchangeability test ALONE — "
      f"no outcome consulted)")
REP["absorption_choice"] = abs_choice

SCORED = ["cvd_5", "cvd_15", "cvd_30", "cvd_norm_15", "abs_cvd_15", "delta_div_15",
          abs_choice, "vol_15_rel", "vol_30_rel", "stack_bid_exc", "stack_ask_exc"]
n_fail = sum(1 for f in SCORED if not exch[f]["passes"])
print(f"scored set: {len(SCORED)} features ({n_fail} still failing exchangeability — carried "
      f"with the flag, not silently)")
REP["scored_features"] = SCORED
REP["scored_failing_exchangeability"] = [f for f in SCORED if not exch[f]["passes"]]
X.to_csv(f"{OUT}/part1_features.csv", index=False)
json.dump(REP, open(f"{OUT}/part1_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part1_features.csv (scoring continues in part1b)")
