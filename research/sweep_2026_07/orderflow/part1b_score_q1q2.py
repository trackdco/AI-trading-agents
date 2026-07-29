#!/usr/bin/env python3
"""PART 1b — SCORE Q1 and Q2 on the partially-remediated (C-only) news-filtered baseline.

W and the dep_* family remain LEAKY in this book's selection path. Nothing here is clean.

INFERENCE. Trades cluster within days, so every interval is a DAY-CLUSTER BOOTSTRAP (resample
days with replacement, 4000 draws). A second, fully-valid permutation null is run at DAY level
(one observation per day, so days are exchangeable and label shuffling is exact) — it costs
power but cannot be gamed by within-day correlation.

MULTIPLICITY. Priced on the EFFECTIVE number of independent tests (Li & Ji 2005 eigenvalue
method) over the scored feature correlation matrix, NOT on the nominal count: the CVD family
are all functions of one delta series and fp_imb_15 was dropped as an exact duplicate.

Q1 PRIMARY is threshold-free (Spearman vs realized R). Binaries are secondary.
Q2 asks only one thing: does entry order flow add anything BEYOND gap size, which is knowable
at 08:00 ET with no tape at all.

Cells with fewer than MIN_CELL trades are rendered "insufficient", never as numbers.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
NBOOT, NPERM, MIN_CELL = 4000, 5000, 10
rng = np.random.default_rng(20260729)

X = pd.read_csv(f"{OUT}/part1_features.csv")
P1 = json.load(open(f"{OUT}/part1_report.json"))
SCORED = P1["scored_features"]
R = {"scored_features": SCORED, "failing_exchangeability": P1["scored_failing_exchangeability"],
     "absorption_choice": P1["absorption_choice"],
     "baseline": "PARTIALLY REMEDIATED (C only) + news filter; W and dep_* STILL LEAKY"}
print(f"{len(X)} trades | scored features {len(SCORED)}")

days = X.day.values
u_days = pd.unique(days)
day_idx = {d: np.flatnonzero(days == d) for d in u_days}

# ---------------------------------------------------------------- effective number of tests
Z = X[SCORED].apply(lambda s: s.rank(na_option="keep"))
C = np.array(Z.corr(method="pearson").fillna(0).to_numpy(), dtype=float, copy=True)
np.fill_diagonal(C, 1.0)
ev = np.linalg.eigvalsh(C)
ev = np.clip(ev, 0, None)
M_eff = float(sum((e >= 1) + (e - np.floor(e)) for e in ev))
print(f"\nCORRELATION / MULTIPLICITY")
print(f"  nominal tests {len(SCORED)}  ->  effective independent tests M_eff = {M_eff:.2f} "
      f"(Li & Ji eigenvalue method)")
alpha_fw = 1 - (1 - 0.05) ** (1 / M_eff)
print(f"  family-wise alpha 0.05 -> per-test alpha {alpha_fw:.4f} (Sidak on M_eff)")
hi_corr = [(SCORED[i], SCORED[j], round(float(C[i, j]), 3))
           for i in range(len(SCORED)) for j in range(i + 1, len(SCORED)) if abs(C[i, j]) >= 0.6]
print(f"  |rank correlation| >= 0.6 pairs: {hi_corr if hi_corr else 'none'}")
R["multiplicity"] = dict(nominal=len(SCORED), m_eff=M_eff, alpha_per_test=alpha_fw,
                         high_corr_pairs=hi_corr,
                         corr_matrix={f: {g: round(float(C[i, j]), 3)
                                          for j, g in enumerate(SCORED)}
                                      for i, f in enumerate(SCORED)})

# ---------------------------------------------------------------- inference helpers
def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 8:
        return np.nan
    return float(stats.spearmanr(a[m], b[m]).statistic)

def auc(score, lab):
    m = np.isfinite(score)
    s, y = score[m], lab[m].astype(bool)
    if y.sum() < 3 or (~y).sum() < 3:
        return np.nan
    r = stats.rankdata(s)
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def day_boot(fn, sub=None):
    """Day-cluster bootstrap: resample DAYS with replacement."""
    dd = u_days if sub is None else pd.unique(days[sub])
    out = []
    for _ in range(NBOOT):
        pick = rng.choice(dd, size=len(dd), replace=True)
        ix = np.concatenate([day_idx[d] for d in pick])
        v = fn(ix)
        if np.isfinite(v):
            out.append(v)
    if len(out) < 100:
        return (np.nan, np.nan, np.nan)
    o = np.array(out)
    p = 2 * min((o <= 0).mean(), (o >= 0).mean())
    return float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5)), float(min(p, 1.0))

def day_level_perm(feat, out_col, sub):
    """Exact permutation at DAY level: one obs per day => days are exchangeable."""
    d = pd.DataFrame({"day": days[sub], "f": X[feat].values[sub], "y": X[out_col].values[sub]}) \
        .groupby("day").mean()
    if len(d) < 10:
        return np.nan, np.nan
    obs = spearman(d.f.values, d.y.values)
    if not np.isfinite(obs):
        return np.nan, np.nan
    hits = sum(abs(spearman(d.f.values, rng.permutation(d.y.values))) >= abs(obs) - 1e-12
               for _ in range(NPERM))
    return obs, (hits + 1) / (NPERM + 1)

def req_n(rho):
    if not np.isfinite(rho) or abs(rho) < 1e-6:
        return np.inf
    return float((2.802 / np.arctanh(min(abs(rho), 0.999))) ** 2 + 3)

# ---------------------------------------------------------------- Q1
print("\n" + "=" * 104)
print("Q1 — does STRICTLY PRE-FILL entry order flow separate the trades that pay?")
print("     (this is the honest re-test of conf_PM, which was itself an OF entry-conviction")
print("      signal and was the leak that made this baseline necessary)")
print("=" * 104)
res_q1 = {}
for half, sub, lab in (("OOS", X.oos.values, "OOS  << HEADLINE"),
                       ("IS", (~X.oos).values, "IS   (in-sample, for reference only)")):
    n = int(sub.sum())
    print(f"\n--- {lab}  n={n} ---")
    print(f"{'feature':16s} {'rho(R)':>8} {'95% CI':>18} {'p_boot':>8} {'p_day':>8} "
          f"{'AUC R>=2':>9} {'AUC mfe4':>9}  {'n_req':>7}")
    for f in SCORED:
        fv, rv = X[f].values, X.R.values
        rho = spearman(fv[sub], rv[sub])
        lo, hi, pb = day_boot(lambda ix: spearman(X[f].values[ix], X.R.values[ix]), sub)
        _, pday = day_level_perm(f, "R", sub)
        a2 = auc(fv[sub], X.big_R2.values[sub])
        a4 = auc(fv[sub], X.reach4.values[sub])
        rn = req_n(rho)
        res_q1[f"{half}|{f}"] = dict(rho=rho, ci=[lo, hi], p_boot=pb, p_day=pday,
                                     auc_R2=a2, auc_mfe4=a4, n=n, n_required=rn)
        print(f"{f:16s} {rho:>+8.3f} [{lo:>+7.3f},{hi:>+7.3f}] {pb:>8.3f} {pday:>8.3f} "
              f"{a2:>9.3f} {a4:>9.3f}  {rn:>7.0f}")
R["q1"] = res_q1

oos = X.oos.values
best = max(((f, abs(res_q1[f"OOS|{f}"]["rho"])) for f in SCORED
            if np.isfinite(res_q1[f"OOS|{f}"]["rho"])), key=lambda t: t[1], default=(None, 0))
signed = [f for f in SCORED if f.startswith(("cvd_5", "cvd_15", "cvd_30", "cvd_norm", "stack"))]
blind = [f for f in SCORED if f in ("abs_cvd_15", "vol_15_rel", "vol_30_rel")
         or f.startswith("absorp")]
bs = max((abs(res_q1[f"OOS|{f}"]["rho"]) for f in signed
          if np.isfinite(res_q1[f"OOS|{f}"]["rho"])), default=np.nan)
bb = max((abs(res_q1[f"OOS|{f}"]["rho"]) for f in blind
          if np.isfinite(res_q1[f"OOS|{f}"]["rho"])), default=np.nan)
print(f"\nFALSIFIER (direction-blind twins): best SIGNED |rho| {bs:.3f} vs best "
      f"DIRECTION-BLIND |rho| {bb:.3f}  -> "
      f"{'signed does NOT beat blind: FALSIFIER FIRES' if bb >= bs else 'signed exceeds blind'}")
print(f"Best OOS feature: {best[0]} |rho|={best[1]:.3f}; family-wise threshold requires "
      f"p <= {alpha_fw:.4f}")
surv = [f for f in SCORED if np.isfinite(res_q1[f'OOS|{f}']['p_boot'])
        and res_q1[f"OOS|{f}"]["p_boot"] <= alpha_fw]
print(f"Features surviving family-wise correction OOS: {surv if surv else 'NONE'}")
R["q1_falsifier"] = dict(best_signed=bs, best_blind=bb, fires=bool(bb >= bs))
R["q1_survivors_fw"] = surv

# ---------------------------------------------------------------- terciles, IS edges -> OOS
print("\nTERCILE TRANSFER (edges fixed on the RE-FIXED IS half, applied to OOS)")
print(f"{'feature':16s} {'OOS lo n/meanR':>20} {'OOS hi n/meanR':>20}  {'hi-lo':>8}  95% CI")
terc = {}
for f in SCORED:
    e = np.nanpercentile(X[f].values[~oos], [100 / 3, 200 / 3])
    b = np.digitize(X[f].values, e)
    lo_m, hi_m = oos & (b == 0) & np.isfinite(X[f].values), oos & (b == 2) & np.isfinite(X[f].values)
    if lo_m.sum() < MIN_CELL or hi_m.sum() < MIN_CELL:
        terc[f] = dict(insufficient=True, n_lo=int(lo_m.sum()), n_hi=int(hi_m.sum()))
        print(f"{f:16s} {'insufficient':>20} {'insufficient':>20}   (n_lo={int(lo_m.sum())}, "
              f"n_hi={int(hi_m.sum())}; floor {MIN_CELL})")
        continue
    d_obs = X.R.values[hi_m].mean() - X.R.values[lo_m].mean()
    lo_c, hi_c, pb = day_boot(lambda ix: (X.R.values[ix][np.isin(ix, np.flatnonzero(hi_m))].mean()
                                          - X.R.values[ix][np.isin(ix, np.flatnonzero(lo_m))].mean())
                              if np.isin(ix, np.flatnonzero(hi_m)).sum() > 2
                              and np.isin(ix, np.flatnonzero(lo_m)).sum() > 2 else np.nan, oos)
    terc[f] = dict(n_lo=int(lo_m.sum()), n_hi=int(hi_m.sum()),
                   meanR_lo=float(X.R.values[lo_m].mean()), meanR_hi=float(X.R.values[hi_m].mean()),
                   diff=float(d_obs), ci=[lo_c, hi_c], p=pb)
    print(f"{f:16s} {int(lo_m.sum()):>7}/{X.R.values[lo_m].mean():>+11.3f} "
          f"{int(hi_m.sum()):>7}/{X.R.values[hi_m].mean():>+11.3f}  {d_obs:>+8.3f}  "
          f"[{lo_c:+.3f},{hi_c:+.3f}] p={pb:.3f}")
R["q1_terciles_IS_to_OOS"] = terc

# ---------------------------------------------------------------- Q2: beyond gap size
print("\n" + "=" * 104)
print("Q2 — does entry order flow add anything BEYOND GAP SIZE (knowable at 08:00, no tape)?")
print("=" * 104)
g = X.gap_abs.values
gs = X.gap_pts.values
ok = np.isfinite(g)
print(f"gap computable on {int(ok.sum())}/{len(X)} trades")
for nm, v in (("|gap|", g), ("signed gap", gs)):
    rho = spearman(v[ok], X.R.values[ok])
    lo, hi, pb = day_boot(lambda ix: spearman((np.abs(X.gap_pts.values) if nm == "|gap|"
                                               else X.gap_pts.values)[ix], X.R.values[ix]), ok)
    print(f"  {nm:12s} vs realized R: rho {rho:+.3f}  CI [{lo:+.3f},{hi:+.3f}]  p {pb:.3f}")
    R[f"q2_gap_{nm}"] = dict(rho=rho, ci=[lo, hi], p=pb)

gq = np.nanpercentile(g[ok & ~oos], [100 / 3, 200 / 3])
gb = np.digitize(g, gq)
print(f"\n  gap terciles (edges from IS half: {gq[0]:.0f}, {gq[1]:.0f} pts) — OOS outcomes")
for k, lab in ((0, "small gap"), (1, "mid gap"), (2, "large gap")):
    m_ = oos & (gb == k) & ok
    if m_.sum() < MIN_CELL:
        print(f"    {lab:11s} insufficient (n={int(m_.sum())})")
        continue
    print(f"    {lab:11s} n={int(m_.sum()):>3}  meanR {X.R.values[m_].mean():+.3f}  "
          f"WR {(X.pl.values[m_]>0).mean()*100:.0f}%  pl ${X.pl.values[m_].sum():+,.0f}")

print("\n  PARTIAL association: feature vs R, CONTROLLING for |gap| (rank-residualised)")
print(f"  {'feature':16s} {'rho_raw':>9} {'rho|gap':>9} {'95% CI':>18} {'p_boot':>8}  reading")
def partial(ix, f):
    a, b, c = X[f].values[ix], X.R.values[ix], np.abs(X.gap_pts.values)[ix]
    m = np.isfinite(a) & np.isfinite(b) & np.isfinite(c)
    if m.sum() < 12:
        return np.nan
    ra, rb, rc = (stats.rankdata(v[m]) for v in (a, b, c))
    ea = ra - np.polyval(np.polyfit(rc, ra, 1), rc)
    eb = rb - np.polyval(np.polyfit(rc, rb, 1), rc)
    return float(stats.spearmanr(ea, eb).statistic)

q2 = {}
for f in SCORED:
    raw = spearman(X[f].values[oos & ok], X.R.values[oos & ok])
    pr = partial(np.flatnonzero(oos & ok), f)
    lo, hi, pb = day_boot(lambda ix: partial(ix, f), oos & ok)
    keeps = np.isfinite(pr) and np.isfinite(raw) and abs(pr) >= 0.7 * abs(raw)
    q2[f] = dict(rho_raw=raw, rho_partial=pr, ci=[lo, hi], p=pb)
    print(f"  {f:16s} {raw:>+9.3f} {pr:>+9.3f} [{lo:>+7.3f},{hi:>+7.3f}] {pb:>8.3f}  "
          f"{'retains' if keeps else 'attenuates'}")
R["q2_partial_given_gap"] = q2
sig_q2 = [f for f in SCORED if np.isfinite(q2[f]["p"]) and q2[f]["p"] <= alpha_fw]
print(f"\n  Features with an OOS association surviving family-wise correction AFTER "
      f"controlling for gap: {sig_q2 if sig_q2 else 'NONE'}")
R["q2_survivors_fw"] = sig_q2

m_e, m_n = oos & X.expiry_week.values, oos & ~X.expiry_week.values
if m_e.sum() >= MIN_CELL:
    print(f"\n  expiry-week OOS: n={int(m_e.sum())} meanR {X.R.values[m_e].mean():+.3f} vs "
          f"other n={int(m_n.sum())} meanR {X.R.values[m_n].mean():+.3f}")
    R["q2_expiry"] = dict(n_exp=int(m_e.sum()), meanR_exp=float(X.R.values[m_e].mean()),
                          n_oth=int(m_n.sum()), meanR_oth=float(X.R.values[m_n].mean()))
else:
    print(f"\n  expiry-week OOS: insufficient (n={int(m_e.sum())})")
    R["q2_expiry"] = dict(insufficient=True, n_exp=int(m_e.sum()))

json.dump(R, open(f"{OUT}/part1b_results.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part1b_results.json")
