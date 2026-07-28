#!/usr/bin/env python3
"""Brake's three pre-ruling checks (2026-07-28). Feature/data-quality lane ONLY — no outcome
column is loaded anywhere in this script.

CHECK 1 — task-2 containment rerun at ZERO tolerance (was +/-1 tick).
CHECK 2 — the +/-25pt cleaning band was a CHOSEN constant (step5 PRICE BAND note, ~0.1% of
  price), not derived from data. Rebuild the full v2 feature set at pad=10 and pad=50 and count,
  per feature, trades whose value changes vs the registered pad=25 build, plus trades whose
  BIN changes (IS-calibrated tercile of that pad's own build for continuous; binary flips for
  stacks/divergence). Proposed materiality line, stated before the numbers: >5% of trades
  (>=11/215) changing bin on any feature => band is a free parameter and gets registered as one.
  The pad=25 rebuild is asserted equal to the committed of_features_premarket_v2.csv.
CHECK 3 — v2 IS-vs-OOS distributional comparison per feature (KS + day-block permutation p,
  2000 perms, day-level label shuffle), OOS occupancy of IS-calibrated terciles (the mis-binning
  number), IS/OOS rates for binaries, and attribution: v1-vs-v2 KS per shared feature plus the
  cleaning delta (v2-v1) by half — if cleaning moved IS features materially more than OOS, the
  residual half-difference has a data-quality component, not just market drift.
Primary set n=215 (stamp_edge excluded per Amendment 1); the edge trade is OOS so IS edges are
unaffected either way.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")
W_LONG, W_MID, W_SHORT = 30, 15, 5
STACK_RATIO, STACK_MIN = 3.0, 3
SPLIT = "2025-12-11"
STAMP_EDGE = {("2026-03-13", "2026-03-13 12:31:00+00:00")}
BINARY = {"stack_bid_bin", "stack_ask_bin", "delta_div_15"}
NPERM = 2000
rng = np.random.default_rng(20260728)
REPORT = {}

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv",
                usecols=["day", "ft", "direction", "risk_pts"])
F["ft"] = pd.to_datetime(F.ft, utc=True)
assert len(F) == 216

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event).dt.tz_convert("UTC")
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
H, L, BI = bars.high, bars.low, bars.index

# ================================================================ CHECK 1: zero-tol containment
print("=" * 90)
print("CHECK 1 — limit-entry containment at ZERO tolerance (task 2 was +/-0.25)")
print("=" * 90)
cb = pd.read_parquet(f"{REPO}/output/canon_book.parquet")
cb["ft"] = pd.to_datetime(cb.fill, utc=True)
cb["rk"] = cb["risk"].round(4)
F["rk"] = F.risk_pts.round(4)
J = F.merge(cb.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "entry"]],
            on=["ft", "direction", "rk"], how="left")
assert J.entry.notna().all() and len(J) == 216

def contains(minute, px, tol):
    k = BI.searchsorted(minute)
    if k >= len(BI) or BI[k] != minute:
        return None
    return bool(L.iloc[k] - tol <= px <= H.iloc[k] + tol)

for tol in (0.25, 0.0):
    res = dict(stamped=0, prior_only=0, next_only=0, both_adjacent_only=0, nowhere=0, nobar=0)
    exc = []
    for r in J.itertuples(index=False):
        m = r.ft.floor("min")
        in_m = contains(m, r.entry, tol)
        if in_m is None:
            res["nobar"] += 1
            continue
        if in_m:
            res["stamped"] += 1
            continue
        in_prev = contains(m - pd.Timedelta(minutes=1), r.entry, tol)
        in_next = contains(m + pd.Timedelta(minutes=1), r.entry, tol)
        key = ("prior_only" if in_prev and not in_next else
               "next_only" if in_next and not in_prev else
               "both_adjacent_only" if in_prev and in_next else "nowhere")
        res[key] += 1
        exc.append((r.day, str(r.ft), float(r.entry), key))
    print(f"  tol={tol}: stamped {res['stamped']}/216  prior_only {res['prior_only']}  "
          f"next_only {res['next_only']}  both_adj {res['both_adjacent_only']}  "
          f"nowhere {res['nowhere']}  nobar {res['nobar']}")
    for e in exc:
        print(f"      exception: {e[0]}  {e[1]}  entry {e[2]}  -> {e[3]}")
    REPORT[f"check1_tol{tol}"] = dict(res=res, exceptions=exc)

# ================================================================ CHECK 2: band sensitivity
print("\n" + "=" * 90)
print("CHECK 2 — cleaning-band sensitivity: pad 10 / 25(registered) / 50")
print("=" * 90)
print("load tape ...", flush=True)
T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
               for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
              ignore_index=True)
T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
T["volume"] = T.volume.astype("int64")
n0, v0 = len(T), int(T.volume.sum())
band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
           .agg(lo=("low", "min"), hi=("high", "max"))
T["eday"] = T.ts_minute.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
T = T.join(band, on="eday")

fm_all = F.ft.dt.floor("min")
fm1_idx = pd.DatetimeIndex(sorted(set(fm_all - pd.Timedelta(minutes=1))))

def stack_from(d):
    if d is None or not len(d):
        return np.nan, np.nan
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

def build_features(pad):
    keep = T.hi.isna() | ((T.price >= T.lo - pad) & (T.price <= T.hi + pad))
    Tc = T[keep]
    drop = dict(rows=int(n0 - len(Tc)), vol=int(v0 - int(Tc.volume.sum())))
    M = Tc.assign(signed=Tc.volume.values * np.where(Tc.side.values == "B", 1, -1)) \
          .groupby("ts_minute", observed=True).agg(vol=("volume", "sum"), delta=("signed", "sum"))
    G = {k: g for k, g in Tc[Tc.ts_minute.isin(fm1_idx)].groupby("ts_minute")}
    pc = bars.close
    rows = []
    for r in F.itertuples(index=False):
        fm = r.ft.floor("min")
        def window(n):
            return M.loc[fm - pd.Timedelta(minutes=n): fm - pd.Timedelta(minutes=1)]
        w30, w15, w5 = window(W_LONG), window(W_MID), window(W_SHORT)
        k1 = pc.index.searchsorted(fm - pd.Timedelta(minutes=1), side="right") - 1
        k16 = pc.index.searchsorted(fm - pd.Timedelta(minutes=16), side="right") - 1
        dpx = float(pc.iloc[k1] - pc.iloc[k16]) if k1 > k16 >= 0 else np.nan
        brange = float(bars.high.iloc[max(k16, 0):k1 + 1].max()
                       - bars.low.iloc[max(k16, 0):k1 + 1].min()) if k1 > k16 >= 0 else np.nan
        cvd15 = float(w15.delta.sum()) if len(w15) else np.nan
        sb, sa = stack_from(G.get(fm - pd.Timedelta(minutes=1)))
        rows.append(dict(
            day=r.day, ft=str(r.ft),
            stamp_edge=int((r.day, str(r.ft)) in STAMP_EDGE),
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
            stack_bid_bin=int(sb > 0) if np.isfinite(sb) else np.nan,
            stack_ask_bin=int(sa > 0) if np.isfinite(sa) else np.nan,
            vol_15=float(w15.vol.sum()) if len(w15) else np.nan,
            vol_30=float(w30.vol.sum()) if len(w30) else np.nan,
            abs_cvd_15=abs(cvd15) if np.isfinite(cvd15) else np.nan,
        ))
    return pd.DataFrame(rows), drop

builds, drops = {}, {}
for pad in (10, 25, 50):
    print(f"  build pad={pad} ...", flush=True)
    builds[pad], drops[pad] = build_features(pad)
    print(f"    dropped {drops[pad]['rows']:,} rows / {drops[pad]['vol']:,} contracts "
          f"({drops[pad]['vol']/v0*100:.3f}% of volume)")

v2 = pd.read_csv(f"{OUT}/of_features_premarket_v2.csv")
FEATS = [c for c in v2.columns if c not in ("day", "ft", "stamp_edge")]
CONT = [c for c in FEATS if c not in BINARY]
X25 = builds[25]
assert (X25.ft.values == v2.ft.values).all()
for c in FEATS:
    a, b = X25[c].values, v2[c].values
    ok = np.isclose(a, b, rtol=1e-9, atol=1e-9, equal_nan=True).all()
    assert ok, f"pad=25 rebuild does not reproduce committed v2 on {c}"
print("  pad=25 rebuild reproduces committed v2 EXACTLY on all features  [anchor OK]")

prim = v2.stamp_edge.values == 0                      # n=215 primary
is_m = (v2.day.values < SPLIT) & prim
oos_m = (v2.day.values >= SPLIT) & prim

def edges(vals):
    return np.nanpercentile(vals, [100 / 3, 200 / 3])

def binify(vals, e):
    return np.where(np.isnan(vals), -1, np.digitize(vals, e))   # 0/1/2, -1 for NaN

def neq(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return int(((a != b) & ~(np.isnan(a) & np.isnan(b))).sum())

print(f"\n  {'feature':16s} {'chg@10':>7} {'bin@10':>7} {'chg@50':>7} {'bin@50':>7}   "
      f"med|d|@10 / med|d|@50 (changed rows)")
c2 = {}
for c in FEATS:
    a25 = builds[25][c].values.astype(float)
    row = {}
    for pad in (10, 50):
        ap = builds[pad][c].values.astype(float)
        nch = neq(ap, a25)
        if c in BINARY:
            nbin = nch                                # a change IS a bin flip
        else:
            b_pad = binify(ap[prim], edges(builds[pad][c].values[is_m]))
            b_25 = binify(a25[prim], edges(a25[is_m]))
            nbin = int((b_pad != b_25).sum())
        ch = np.abs(ap - a25)[(~np.isnan(ap)) & (~np.isnan(a25)) & (ap != a25)]
        row[pad] = dict(changed=nch, bin_changed=nbin,
                        med_absdelta=float(np.median(ch)) if len(ch) else 0.0)
    c2[c] = row
    print(f"  {c:16s} {row[10]['changed']:>7} {row[10]['bin_changed']:>7} "
          f"{row[50]['changed']:>7} {row[50]['bin_changed']:>7}   "
          f"{row[10]['med_absdelta']:.4g} / {row[50]['med_absdelta']:.4g}")
worst = max(max(r[10]["bin_changed"], r[50]["bin_changed"]) for r in c2.values())
print(f"  worst bin-change count across features/pads: {worst}/215 "
      f"({worst/215*100:.1f}%)  [pre-stated materiality line: >5% => free parameter]")
REPORT["check2"] = dict(drops={str(k): v for k, v in drops.items()}, per_feature=c2,
                        worst_bin_changed=worst)

# ================================================================ CHECK 3: IS vs OOS on v2
print("\n" + "=" * 90)
print("CHECK 3 — v2 feature distributions, IS half vs OOS half (primary n=215)")
print("=" * 90)
days = v2.day.values
u_days = pd.unique(days[prim])
is_days = set(days[is_m])
k_is = sum(1 for d in u_days if d in is_days)
print(f"  IS trades {int(is_m.sum())} over {k_is} days | OOS trades {int(oos_m.sum())} over "
      f"{len(u_days)-k_is} days | split {SPLIT} | {NPERM} day-block perms")

def ks_stat(a, b):
    a, b = np.sort(a[~np.isnan(a)]), np.sort(b[~np.isnan(b)])
    allv = np.concatenate([a, b])
    return float(np.abs(np.searchsorted(a, allv, side="right") / len(a)
                        - np.searchsorted(b, allv, side="right") / len(b)).max())

def rate_diff(a, b):
    return float(abs(np.nanmean(a) - np.nanmean(b)))

def dayblock_p(x, stat_fn):
    obs = stat_fn(x[is_m], x[oos_m])
    hits = 0
    for _ in range(NPERM):
        pick = set(rng.choice(u_days, size=k_is, replace=False))
        m = np.array([d in pick for d in days]) & prim
        if stat_fn(x[m], x[prim & ~m]) >= obs - 1e-12:
            hits += 1
    return obs, (hits + 1) / (NPERM + 1)

v1 = pd.read_csv(f"{OUT}/of_features_premarket.csv")
assert (v1.ft.values == v2.ft.values).all()

c3 = {}
print(f"\n  {'feature':16s} {'medIS':>10} {'medOOS':>10} {'KS':>6} {'p_perm':>7} "
      f"{'OOS terc occ lo/mid/hi %':>24}  {'KS_v1':>6}  {'chgIS/chgOOS':>12}  note")
for c in FEATS:
    x = v2[c].values.astype(float)
    if c in BINARY:
        obs, p = dayblock_p(x, rate_diff)
        rI, rO = float(np.nanmean(x[is_m])), float(np.nanmean(x[oos_m]))
        occ = ""
        ksv1 = np.nan
        note = "binary: rate IS %.3f vs OOS %.3f" % (rI, rO)
        if c == "delta_div_15":
            note += " (LOW-POWER)"
        c3[c] = dict(kind="binary", rate_is=rI, rate_oos=rO, absdiff=obs, p_perm=p)
        print(f"  {c:16s} {rI:>10.3f} {rO:>10.3f} {obs:>6.3f} {p:>7.3f} {occ:>24}  "
              f"{'':>6}  {'':>12}  {note}")
    else:
        obs, p = dayblock_p(x, ks_stat)
        e = edges(x[is_m])
        bo = binify(x[oos_m], e)
        occ_pct = [float((bo == k).mean() * 100) for k in (0, 1, 2)]
        occ = "/".join(f"{o:.0f}" for o in occ_pct)
        x1 = v1[c].values.astype(float) if c in v1.columns else None
        ksv1 = ks_stat(x1[is_m], x1[oos_m]) if x1 is not None else np.nan
        d = x - x1 if x1 is not None else np.full_like(x, np.nan)
        chI = neq(x[is_m], x1[is_m]) if x1 is not None else 0
        chO = neq(x[oos_m], x1[oos_m]) if x1 is not None else 0
        c3[c] = dict(kind="cont", med_is=float(np.nanmedian(x[is_m])),
                     med_oos=float(np.nanmedian(x[oos_m])), ks=obs, p_perm=p, ks_v1=float(ksv1),
                     oos_terc_occ=occ_pct, clean_changed_is=chI, clean_changed_oos=chO,
                     clean_med_absdelta_is=float(np.nanmedian(np.abs(d[is_m][d[is_m] != 0])))
                     if x1 is not None and (d[is_m] != 0).any() else 0.0,
                     clean_med_absdelta_oos=float(np.nanmedian(np.abs(d[oos_m][d[oos_m] != 0])))
                     if x1 is not None and (d[oos_m] != 0).any() else 0.0)
        print(f"  {c:16s} {c3[c]['med_is']:>10.4g} {c3[c]['med_oos']:>10.4g} {obs:>6.3f} "
              f"{p:>7.3f} {occ:>24}  {ksv1:>6.3f}  {chI:>5}/{chO:<6}  ")
print("\n  reading: p_perm is a day-block permutation p for 'the halves are exchangeable at")
print("  day level'. OOS tercile occupancy far from 33/33/33 = the mis-binning Brake named.")
print("  KS_v1 ~= KS_v2 per feature => the half-difference exists in the RAW tape too (market")
print("  drift, not created by cleaning); chgIS >> chgOOS quantifies where cleaning bit harder.")
print("  fp_imb_15 is cvd_norm_15/2 exactly (linear) — identical KS/terciles by construction.")
REPORT["check3"] = c3

json.dump(REPORT, open(f"{OUT}/pre_ruling_checks.json", "w"), indent=1,
          default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
print(f"\nwrote {OUT}/pre_ruling_checks.json")
print("STOPPED. No outcomes examined.")
