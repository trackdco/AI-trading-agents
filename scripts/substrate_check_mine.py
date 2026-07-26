#!/usr/bin/env python3
"""CHECK-MINING CAMPAIGN on the 3,005-fill engine substrate — the Angus ladder, done with power.

Substrate: london_engine_substrate.parquet (10:00-13:00 UK, both books, no pre-filtering,
raw -$114k at 26% WR -- Angus's raw substrates were also breakeven-to-negative; the profit in
his canons comes from the mined multi-check ladder). His NY ladder was mined on ~713 fills,
his London one on ~749. This substrate has 3,005 across 2023-01..2026-07.

DESIGN (every lesson from the 10-13 campaign is structural here, not advisory):
  split        TRAIN = 2023-01..2024-12 (1,644 fills) fit + freeze thresholds
               TEST  = 2025-01..2026-07 (1,361 fills) never touched by selection
  features     ~30 bar-derived families, all causal at fill (last CLOSED 1m/M15 bar), spanning
               ROOM, value area, VWAP geometry, tape, vol regime, session levels, pattern/book/
               time. NO CVD features -- tape coverage starts 2025-06 and cannot be train-fitted.
  rules        each numeric feature x train quantiles {20,33,50,67,80} x both sides + one
               interior band; booleans as-is. Every rule counted.
  null         the WHOLE pipeline (rank on train -> take best -> read test) re-run under a
               DAY-BLOCK permutation: R is decomposed into day-mean + residual and the day
               means are permuted across days, preserving within-day clustering. Sign
               stability is NOT used as a gate (measured this session at ~coin-flip).
  ladder       top 4 train-selected, redundancy-pruned (phi<0.5) checks -> score 0-4; the
               ladder's test top-minus-bottom spread gets its own pipeline null.
  carve-out    SESSION-LEVEL RECLAIM, pre-registered as: pattern in {A,B2} AND entry within
               0.5*ATR14 of the nearest overnight/prior-day extreme. One definition, no
               fishing; dist terciles reported as description only.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/substrate_check_mine.py
"""
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
NY = "America/New_York"
PV = 20.0
TICK = 0.25
COMM = 5.0
SPLIT = "2025-01-01"
NPERM = 1000
rng = np.random.default_rng(17)
import sys
RBASIS = sys.argv[sys.argv.index("--rbasis")+1] if "--rbasis" in sys.argv else "engine"
BIN, VA = 1.0, 0.70

# ---------------------------------------------------------------- load
print("load ...", flush=True)
F = pd.read_parquet(f"{S}/london_engine_substrate.parquet")
F["fill_ts"] = pd.to_datetime(F.fill, utc=True).dt.tz_convert(NY)
F["risk"] = (F.entry - F.stop).abs()
F = F[F.risk >= 1.0].sort_values("fill_ts").reset_index(drop=True)
F["R"] = F.dollars / (F.risk * PV)
F["dir"] = np.where(F.direction == "long", 1, -1)
F["sess"] = (F.fill_ts + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
_RBASIS_TGT = None
if RBASIS.startswith("t"):
    _RBASIS_TGT = float(RBASIS[1:])

bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bars["sess"] = (bars.ts + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
bt = bars.ts.values
cl, hi, lo, vol = (bars.close.values.astype(float), bars.high.values.astype(float),
                   bars.low.values.astype(float), bars.volume.values.astype(float))

# per-session context
b_t = bars.ts.dt.time
from datetime import time as dtime                      # noqa: E402
g = bars.groupby("sess")
SESS_HI, SESS_LO = g.high.max(), g.low.min()
SESS_CLO = g.close.last()
PD_HI, PD_LO = SESS_HI.shift(1), SESS_LO.shift(1)
PD_RANGE = (SESS_HI - SESS_LO).shift(1)
PD_CLOSE = SESS_CLO.shift(1)
onm = ((b_t >= dtime(18, 0)) | (b_t < dtime(3, 0))).values
og = bars[onm].groupby("sess")
ON_HI, ON_LO = og.high.max(), og.low.min()
ON_RANGE = ON_HI - ON_LO
ON_REL = ON_RANGE / ON_RANGE.shift(1).rolling(20, min_periods=10).median()
SESS_OPEN = g.open.first()

# day-so-far running extrema + session vwap on the 1m frame
gi = bars.groupby("sess")
run_hi = gi.high.cummax().values
run_lo = gi.low.cummin().values
tp = (hi + lo + cl) / 3.0
cv = pd.Series(vol).groupby(bars.sess.values).cumsum().values
cvp = pd.Series(tp * vol).groupby(bars.sess.values).cumsum().values
vwap1 = np.where(cv > 0, cvp / cv, np.nan)

# M15 ATR14
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
tr = np.maximum(m.high - m.low, np.maximum((m.high - m.close.shift(1)).abs(),
                                           (m.low - m.close.shift(1)).abs()))
atr = tr.rolling(14).mean()
mlab = m.index.values
atr_v = atr.values

# prior-session volume profile
print("profiles ...", flush=True)


def value_area(hist):
    if not hist:
        return None
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * BIN
    if arr.sum() <= 0:
        return None
    poc = int(arr.argmax())
    lo_, hi_ = poc, poc
    cov, tgt, n = arr[poc], VA * arr.sum(), len(arr)
    while cov < tgt - 1e-9 and (lo_ > 0 or hi_ < n - 1):
        bl = arr[lo_ - 1] if lo_ > 0 else -np.inf
        ab = arr[hi_ + 1] if hi_ < n - 1 else -np.inf
        if ab >= bl:
            hi_ += 1; cov += arr[hi_]
        else:
            lo_ -= 1; cov += arr[lo_]
    return dict(poc=float(centers[poc]), vah=float(centers[hi_]), val=float(centers[lo_]))


def profile_of(fr):
    lo_i = np.floor(fr.low.values / BIN).astype(np.int64)
    hi_i = np.floor(fr.high.values / BIN).astype(np.int64)
    v = fr.volume.values.astype(float)
    span = (hi_i - lo_i + 1).clip(min=1)
    idx = np.repeat(np.arange(len(lo_i)), span)
    offs = np.concatenate([np.arange(s) for s in span]) if len(span) else np.array([], np.int64)
    bins = lo_i[idx] + offs
    w = (v / span)[idx]
    if not len(bins):
        return None
    o = np.argsort(bins, kind="stable")
    uq, st = np.unique(bins[o], return_index=True)
    return value_area(dict(zip(uq.tolist(), np.add.reduceat(w[o], st).tolist())))


by_sess = {d: fr for d, fr in bars.groupby("sess")}
sd = sorted(by_sess)
PROF = {}
for k, d in enumerate(sd):
    if k > 0:
        PROF[d] = profile_of(by_sess[sd[k - 1]])

# ---------------------------------------------------------------- features per fill
print("features ...", flush=True)
k1 = np.searchsorted(bt, F.fill_ts.values, side="left") - 1        # last CLOSED 1m bar
kA = np.searchsorted(mlab, F.fill_ts.values, side="right") - 1     # last closed M15 label
ok = (k1 >= 60) & (kA >= 0)
F, k1, kA = F[ok].reset_index(drop=True), k1[ok], kA[ok]
dr = F["dir"].values
en = F.entry.values
rk = F.risk.values
sesss = F.sess.values

atr14 = atr_v[kA]
atr14 = np.where(np.isfinite(atr14) & (atr14 > 0), atr14, np.nan)

if _RBASIS_TGT is not None:
    # fixed-target R: keep engine initial stop (-1R), exit at +TGT*R if reached first, walk to
    # session end (18:00 ET boundary). stop checked before target on the same bar (pessimistic).
    print(f"  recompute R on {RBASIS} target basis ...", flush=True)
    sess_last = {}
    _bs = bars.sess.values
    for _k in range(len(bars)):
        sess_last[_bs[_k]] = _k
    kf_ = np.searchsorted(bt, F.fill_ts.values, side="left")
    newR = np.full(len(F), np.nan)
    _en, _dr, _rk = F.entry.values, F["dir"].values, F.risk.values
    for _n in range(len(F)):
        _e, _d, _r = _en[_n], _dr[_n], _rk[_n]
        _kf = int(kf_[_n]); _kl = sess_last.get(sesss[_n], _kf)
        hi_run, lo_run, out = -np.inf, np.inf, None
        for _k in range(_kf, min(_kl, len(bars) - 1) + 1):
            lo_run = min(lo_run, (_d*(lo[_k]-_e)) if _d>0 else (_d*(hi[_k]-_e)))
            hi_run = max(hi_run, (_d*(hi[_k]-_e)) if _d>0 else (_d*(lo[_k]-_e)))
            if lo_run <= -_r:
                out = -1.0 - TICK/_r; break
            if hi_run >= _RBASIS_TGT*_r:
                out = _RBASIS_TGT - TICK/_r; break
        if out is None:
            out = (_d*(cl[min(_kl,len(bars)-1)]-_e))/_r   # session-end mark
        newR[_n] = out
    F["R"] = newR
    F["dollars"] = newR * _rk * PV - COMM


def sget(series, keys):
    d = series.to_dict()
    return np.array([d.get(k, np.nan) for k in keys])


pdh, pdl = sget(PD_HI, sesss), sget(PD_LO, sesss)
onh, onl = sget(ON_HI, sesss), sget(ON_LO, sesss)
onr, onrel = sget(ON_RANGE, sesss), sget(ON_REL, sesss)
pdr, pdc = sget(PD_RANGE, sesss), sget(PD_CLOSE, sesss)
sopen = sget(SESS_OPEN, sesss)
poc = np.array([PROF.get(s, {}).get("poc", np.nan) if PROF.get(s) else np.nan for s in sesss])
vah = np.array([PROF.get(s, {}).get("vah", np.nan) if PROF.get(s) else np.nan for s in sesss])
val = np.array([PROF.get(s, {}).get("val", np.nan) if PROF.get(s) else np.nan for s in sesss])

c_now = cl[k1]
c15, c30, c60 = cl[k1 - 15], cl[k1 - 30], cl[k1 - 60]
path30 = np.array([np.abs(np.diff(cl[k - 30:k + 1])).sum() for k in k1])
lvl_dist = np.nanmin(np.vstack([np.abs(en - x) for x in (onh, onl, pdh, pdl)]), axis=0)

X = pd.DataFrame(dict(
    risk_pt=rk, risk_atr=rk / atr14,
    tod=F.fill_ts.dt.hour * 60 + F.fill_ts.dt.minute,
    dow=F.fill_ts.dt.dayofweek,
    tfrank=F.tf.map({"1min": 1, "2min": 2, "3min": 3, "5min": 5, "15min": 15}).fillna(0),
    ntrig=F.n_trig,
    atr14=atr14, onrange=onr, onrel=onrel, pdrange=pdr,
    gap_dir=dr * (sopen - pdc),
    room_on_R=np.where(dr > 0, onh - en, en - onl) / rk,
    behind_on_R=np.where(dr > 0, en - onl, onh - en) / rk,
    room_pd_R=np.where(dr > 0, pdh - en, en - pdl) / rk,
    poc_dir_R=dr * (poc - en) / rk,
    in_value=((en >= val) & (en <= vah)).astype(float),
    vwap_side=(dr * (en - vwap1[k1]) > 0).astype(float),
    vwap_dist=dr * (en - vwap1[k1]) / atr14,
    tape15=dr * (c_now - c15) / atr14,
    tape30=dr * (c_now - c30) / atr14,
    tape60=dr * (c_now - c60) / atr14,
    eff30=np.abs(c_now - c30) / np.where(path30 > 0, path30, np.nan),
    posday=np.where(run_hi[k1] > run_lo[k1],
                    (en - run_lo[k1]) / (run_hi[k1] - run_lo[k1]), np.nan),
    lvl_dist_atr=lvl_dist / atr14,
    pat_A=(F.pattern == "A").astype(float), pat_B=(F.pattern == "B").astype(float),
    pat_B2=(F.pattern == "B2").astype(float), book_E4=(F.book == "E4").astype(float),
    is_long=(dr > 0).astype(float),
))
R = F.R.values
day = F.day.values
train = day < SPLIT
print(f"fills {len(F)}  train {int(train.sum())}  test {int((~train).sum())}  "
      f"features {X.shape[1]}", flush=True)

# ---------------------------------------------------------------- rule bank (train-frozen)
NUMS = [c for c in X.columns if X[c].nunique() > 6]
BOOLS = [c for c in X.columns if c not in NUMS]
rules, masks = [], []
for c in NUMS:
    v = X[c].values
    tq = np.nanquantile(v[train], [.2, .33, .5, .67, .8])
    for q, t in zip([20, 33, 50, 67, 80], tq):
        for side, mk in (("hi", v > t), ("lo", v <= t)):
            rules.append(f"{c} {side} q{q}={t:.3g}")
            masks.append(mk & np.isfinite(v))
    b = (v > tq[1]) & (v <= tq[3])
    rules.append(f"{c} band q33..q67")
    masks.append(b & np.isfinite(v))
for c in BOOLS:
    v = X[c].values
    rules.append(f"{c} == 1")
    masks.append(v == 1)
    rules.append(f"{c} == 0")
    masks.append(v == 0)
MK = np.array(masks)
print(f"rule bank: {len(rules)} rules ({len(NUMS)} numeric x 11 + {len(BOOLS)} boolean x 2)", flush=True)

MINF = 0.15


def lifts(Rv, msk_ok):
    tr_, te_ = train, ~train
    out = np.full((len(rules), 2), np.nan)
    for j in range(len(rules)):
        mp = MK[j]
        a1, a0 = mp & tr_, (~mp) & tr_
        if msk_ok[j]:
            out[j, 0] = Rv[a1].mean() - Rv[a0].mean()
            b1, b0 = mp & te_, (~mp) & te_
            if b1.sum() > 30 and b0.sum() > 30:
                out[j, 1] = Rv[b1].mean() - Rv[b0].mean()
    return out


ntr = np.array([(MK[j] & train).sum() for j in range(len(rules))])
frac = ntr / train.sum()
OKR = (frac > MINF) & (frac < 1 - MINF)
L = lifts(R, OKR)

# ---------------------------------------------------------------- pipeline null (day-block)
print(f"pipeline null ({NPERM} day-block perms) ...", flush=True)
udays, dinv = np.unique(day, return_inverse=True)
dmean = np.array([R[dinv == i].mean() for i in range(len(udays))])
resid = R - dmean[dinv]
TRm, TEm = train, ~train
A1 = MK & TRm
A0 = (~MK) & TRm
B1 = MK & TEm
B0 = (~MK) & TEm
s_a1, s_a0 = A1.sum(1), A0.sum(1)
s_b1, s_b0 = B1.sum(1), B0.sum(1)
null_best_test, null_lad = [], []
for it in range(NPERM):
    Rp = resid + dmean[rng.permutation(len(udays))][dinv]
    lt = (A1 @ Rp) / np.maximum(s_a1, 1) - (A0 @ Rp) / np.maximum(s_a0, 1)
    # eligibility must sort LAST: -inf survives abs() and would rank first
    elig = OKR & np.isfinite(lt)
    score_ = np.where(elig, np.abs(lt), -1.0)
    order = np.argsort(-score_)
    jbest = order[0]
    sgn = np.sign(lt[jbest])
    te_l = (B1[jbest] @ Rp) / max(s_b1[jbest], 1) - (B0[jbest] @ Rp) / max(s_b0[jbest], 1)
    null_best_test.append(sgn * te_l)
    # 4-rule ladder under the null (top-4 by |train lift|, oriented positive)
    top4 = order[:4]
    sc = np.zeros(len(R))
    for j in top4:
        sc += (MK[j] if lt[j] > 0 else ~MK[j]).astype(float)
    hi_m, lo_m = (sc >= 3) & TEm, (sc <= 1) & TEm
    if hi_m.sum() > 20 and lo_m.sum() > 20:
        null_lad.append(Rp[hi_m].mean() - Rp[lo_m].mean())
null_best_test = np.array(null_best_test)
null_lad = np.array(null_lad)

# ---------------------------------------------------------------- observed results
_sc = np.where(OKR & np.isfinite(L[:, 0]), np.abs(L[:, 0]), -1.0)
ord_obs = np.argsort(-_sc)
print("\n" + "=" * 108)
print("TOP 12 TRAIN-SELECTED RULES  (train lift ranks; test lift is the verdict)")
print("=" * 108)
print(f"{'rule':<34} {'n_tr':>5} {'trainL':>8} {'testL':>8}   null(best) med={np.median(null_best_test):+.3f} q95={np.quantile(null_best_test,.95):+.3f}")
for j in ord_obs[:12]:
    print(f"{rules[j]:<34} {ntr[j]:>5} {L[j,0]:>+8.3f} {L[j,1] if np.isfinite(L[j,1]) else np.nan:>+8.3f}")
jb = ord_obs[0]
obs_best_test = np.sign(L[jb, 0]) * L[jb, 1]
p_best = float((null_best_test >= obs_best_test).mean())
print(f"\nBEST train rule: {rules[jb]}  -> oriented TEST lift {obs_best_test:+.3f}  "
      f"pipeline-null p = {p_best:.3f}")

# observed ladder
lt0 = np.where(OKR, L[:, 0], -np.inf)
chosen, used = [], []
for j in ord_obs:
    if len(chosen) == 4:
        break
    if not (OKR[j] and np.isfinite(L[j, 0])):
        continue
    mj = (MK[j] if L[j, 0] > 0 else ~MK[j]).astype(float)
    if mj.std() == 0:
        continue
    if all(abs(np.corrcoef(mj, u)[0, 1]) < 0.5 for u in used):
        chosen.append(j)
        used.append(mj)
sc = np.sum([u for u in used], axis=0)
print("\n" + "=" * 108)
print(f"4-CHECK LADDER (train-selected, phi<0.5): {[rules[j] for j in chosen]}")
print("=" * 108)
for split, msk in (("TRAIN", train), ("TEST", ~train)):
    print(f"  {split}:")
    for s0 in range(5):
        g_ = (sc == s0) & msk
        if g_.sum():
            print(f"    score {s0}  n={int(g_.sum()):5d}  WR {100*(R[g_]>0).mean():3.0f}%  "
                  f"E[R] {R[g_].mean():+.3f}  net ${F.dollars.values[g_].sum():+10,.0f}")
hi_m, lo_m = (sc >= 3) & ~train, (sc <= 1) & ~train
obs_lad = R[hi_m].mean() - R[lo_m].mean() if hi_m.sum() > 20 and lo_m.sum() > 20 else np.nan
if len(null_lad) and np.isfinite(obs_lad):
    p_lad = float((null_lad >= obs_lad).mean())
    print(f"\n  TEST spread (score>=3 minus score<=1): {obs_lad:+.3f}R   "
          f"ladder-null med={np.median(null_lad):+.3f} q95={np.quantile(null_lad,.95):+.3f}  p={p_lad:.3f}")
else:
    print(f"\n  TEST spread: {obs_lad}  (ladder null draws: {len(null_lad)})")
print("  per-year, score>=3 fills:")
top = sc >= 3
for yr in ("2023", "2024", "2025", "2026"):
    g_ = top & (F.yr.values == int(yr))
    if g_.sum():
        print(f"    {yr}  n={int(g_.sum()):4d}  WR {100*(R[g_]>0).mean():3.0f}%  "
              f"E[R] {R[g_].mean():+.3f}  net ${F.dollars.values[g_].sum():+10,.0f}")

# ---------------------------------------------------------------- reclaim carve-out
print("\n" + "=" * 108)
print("SESSION-LEVEL RECLAIM carve-out (pre-registered: pattern A/B2 AND lvl_dist <= 0.5*ATR14)")
print("=" * 108)
rec = ((F.pattern.isin(["A", "B2"])).values & (X.lvl_dist_atr.values <= 0.5))
for lab, msk in (("reclaim", rec), ("rest", ~rec)):
    print(f"  {lab}:")
    for yr in ("2023", "2024", "2025", "2026"):
        g_ = msk & (F.yr.values == int(yr))
        if g_.sum() > 4:
            print(f"    {yr}  n={int(g_.sum()):4d}  WR {100*(R[g_]>0).mean():3.0f}%  "
                  f"E[R] {R[g_].mean():+.3f}  net ${F.dollars.values[g_].sum():+10,.0f}")
print("  reclaim by lvl_dist_atr tercile (description only):")
ld = X.lvl_dist_atr.values
recA = (F.pattern.isin(["A", "B2"])).values
tq_ = np.nanquantile(ld[recA], [.33, .67])
for lab, msk in (("near", recA & (ld <= tq_[0])), ("mid", recA & (ld > tq_[0]) & (ld <= tq_[1])),
                 ("far", recA & (ld > tq_[1]))):
    if msk.sum() > 10:
        print(f"    {lab:5s} n={int(msk.sum()):4d}  E[R] {R[msk].mean():+.3f}  "
              f"WR {100*(R[msk]>0).mean():3.0f}%")

out = pd.DataFrame(dict(rule=rules, n_train=ntr, train_lift=L[:, 0], test_lift=L[:, 1]))
out.to_csv(f"{S}/substrate_check_mine.csv", index=False)
print(f"\nwrote {S}/substrate_check_mine.csv  ({len(rules)} rules; null: best-test med "
      f"{np.median(null_best_test):+.3f}, ladder med {np.median(null_lad):+.3f})")
