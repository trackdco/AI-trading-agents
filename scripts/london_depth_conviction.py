#!/usr/bin/env python3
"""DOES ANY ORDER-BOOK FEATURE SUPPORT CONVICTION SIZING on the London 10-13 UK book?

Reads $LONDON_SCRATCH/london_depth_features.csv (built by london_depth_features.py) and asks
one question per feature: does knowing it at entry tell you how much to bet?

THE STATISTICAL PROBLEM, STATED UP FRONT. There are 31 features and 70 signals. Splitting each
feature at its median gives 31 independent-ish tests; at alpha=0.05 you EXPECT ~1.6 to look
significant with no signal whatsoever. Any single "winner" here is worthless on its own. So the
bar is deliberately set higher than a p-value:

  gate 1  univariate separation      permutation p on the median split (20k shuffles)
  gate 2  multiplicity survival      Benjamini-Hochberg FDR across all features tested
  gate 3  SPLIT-HALF STABILITY       same sign AND same side in BOTH halves of the sample
                                     -- this is the gate that kills curve-fits, not the p-value
  gate 4  monotonicity               tercile means ordered, not a middle-bucket spike
  gate 5  economic size              does acting on it actually make money on book C

Canon precedent (docs/FINDING-oracle-is-hindsight-books-dont-generalize.md): every book-derived
predictor tested there was "either noise or a 2026 curve-fit", and CVD confirmation moved win
rate without moving dollars. Expect the same here and require proof otherwise.

PERMANENT LIMIT -- THERE IS NO OUT-OF-SAMPLE. Depth coverage starts 2025-06-02. The 2023-24
holdout that can validate the book's GEOMETRY can never validate a depth feature, because the
data does not exist. Split-half is the strongest test available and it is weaker than a holdout.

    LONDON_SCRATCH=<dir> python3 scripts/london_depth_conviction.py
"""
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
rng = np.random.default_rng(11)
NPERM = 20_000

F = pd.read_csv(f"{S}/london_depth_features.csv")
META = ["day", "sig", "res", "ent", "ext", "dr", "entry", "rk", "net", "R", "how", "mins",
        "feat_ts", "in_A", "in_C"]
FEATS = [c for c in F.columns if c not in META]
print(f"signals {len(F)}  features {len(FEATS)}  netR {F.R.sum():+.2f}  "
      f"WR {(F.R>0).mean()*100:.0f}%")
print(f"books: A={int(F.in_A.sum())} (lookahead)  C={int(F.in_C.sum())} (leakage-clean)\n")

MID = sorted(F.day.unique())[len(F.day.unique()) // 2]     # median trading DAY, not a numeric
H1, H2 = F[F.day < MID], F[F.day >= MID]
print(f"split-half at {MID}: H1 n={len(H1)}  H2 n={len(H2)}\n")


def perm_p(x, y, nperm=NPERM):
    """Two-sided permutation p on the difference in mean R between the two sides of a split."""
    obs = y[x].mean() - y[~x].mean()
    if not np.isfinite(obs):
        return np.nan, np.nan
    n = x.sum()
    cnt = 0
    for _ in range(nperm):
        p = rng.permutation(y)
        if abs(p[:n].mean() - p[n:].mean()) >= abs(obs) - 1e-12:
            cnt += 1
    return obs, (cnt + 1) / (nperm + 1)


rows = []
for c in FEATS:
    sub = F[F[c].notna()]
    if len(sub) < 30 or sub[c].nunique() < 4:
        continue
    thr = sub[c].median()
    hi = (sub[c] > thr).values
    if hi.sum() < 8 or (~hi).sum() < 8:
        continue
    obs, p = perm_p(hi, sub.R.values)
    # split-half: same direction in both halves?
    def half_gap(H):
        h = H[H[c].notna()]
        if len(h) < 8:
            return np.nan
        m = h[c] > thr                      # SAME threshold, not re-fit per half
        if m.sum() < 3 or (~m).sum() < 3:
            return np.nan
        return h.R[m].mean() - h.R[~m].mean()
    g1, g2 = half_gap(H1), half_gap(H2)
    stable = bool(np.isfinite(g1) and np.isfinite(g2) and np.sign(g1) == np.sign(g2))
    # terciles
    try:
        q = pd.qcut(sub[c], 3, labels=False, duplicates="drop")
        tm = [sub.R[q == k].mean() for k in sorted(pd.unique(q.dropna()))]
        mono = len(tm) == 3 and (tm[0] < tm[1] < tm[2] or tm[0] > tm[1] > tm[2])
    except Exception:
        tm, mono = [], False
    rows.append(dict(feat=c, n=len(sub), thr=thr, gapR=obs, p=p,
                     hiR=sub.R[hi].mean(), loR=sub.R[~hi].mean(),
                     h1=g1, h2=g2, stable=stable, mono=mono,
                     terciles=" ".join(f"{v:+.2f}" for v in tm)))

Rd = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
# Benjamini-Hochberg
mvals = Rd.p.values
order = np.argsort(mvals)
bh = np.full(len(mvals), np.nan)
m = len(mvals)
prev = 1.0
for rank, ix in enumerate(order[::-1]):
    k = m - rank
    prev = min(prev, mvals[ix] * m / k)
    bh[ix] = prev
Rd["p_bh"] = bh

print("=" * 108)
print("UNIVARIATE SWEEP -- median split, R of high side vs low side")
print("=" * 108)
print(f"{'feature':<16} {'n':>3} {'hiR':>6} {'loR':>6} {'gap':>6} {'p':>7} {'p_BH':>7} "
      f"{'H1gap':>6} {'H2gap':>6} {'stable':>6} {'mono':>5}  terciles")
for _, r in Rd.iterrows():
    print(f"{r.feat:<16} {int(r.n):>3} {r.hiR:>+6.2f} {r.loR:>+6.2f} {r.gapR:>+6.2f} "
          f"{r.p:>7.4f} {r.p_bh:>7.3f} "
          f"{r.h1:>+6.2f} {r.h2:>+6.2f} {str(r.stable):>6} {str(r.mono):>5}  {r.terciles}")

print(f"\nexpected false positives at p<0.05 with {len(Rd)} tests: {0.05*len(Rd):.1f}")
print(f"observed p<0.05: {int((Rd.p<0.05).sum())}   surviving BH FDR 0.10: "
      f"{int((Rd.p_bh<0.10).sum())}   AND split-half stable: "
      f"{int(((Rd.p_bh<0.10) & Rd.stable).sum())}")

SURV = Rd[(Rd.p < 0.05) & Rd.stable]
print(f"\n=== candidates passing raw p<0.05 AND split-half stability: {len(SURV)} ===")
if len(SURV):
    print(SURV[["feat", "n", "gapR", "p", "p_bh", "h1", "h2", "mono"]].to_string(index=False))
else:
    print("  none")

# ---------------------------------------------------------------- economic test
print("\n" + "=" * 108)
print("ECONOMIC TEST on book C (leakage-clean) -- conviction sizing 1.0x / 0.5x")
print("=" * 108)
C = F[F.in_C].copy()
base = C.R.sum()
print(f"  book C flat 1.0x: {len(C)} trades  netR {base:+.2f}  WR {(C.R>0).mean()*100:.0f}%\n")
print(f"{'rule':<34} {'n_full':>6} {'netR':>8} {'vs flat':>8} {'WR':>5}")
print("-" * 66)
cand = list(Rd.sort_values("p").feat.head(8))
for c in cand:
    sub = C[C[c].notna()]
    if len(sub) < 20:
        continue
    thr = Rd.loc[Rd.feat == c, "thr"].iloc[0]
    hiR = Rd.loc[Rd.feat == c, "hiR"].iloc[0]
    loR = Rd.loc[Rd.feat == c, "loR"].iloc[0]
    good = (sub[c] > thr) if hiR > loR else (sub[c] <= thr)
    w = np.where(good, 1.0, 0.5)
    net = (sub.R.values * w).sum()
    print(f"{'size 1.0 if ' + c + ' good else 0.5':<34} {int(good.sum()):>6} "
          f"{net:>+8.2f} {net-base:>+8.2f} {(sub.R>0).mean()*100:>4.0f}%")
print("\n  NOTE: 'vs flat' compares to the SAME trade set at flat 1.0x. A rule can only win here")
print("  by putting more size on winners; it cannot add trades. Half-sizing the bad half also")
print("  halves total exposure, so a positive number is necessary but NOT sufficient -- check")
print("  it against the 0.75x flat equivalent before believing it is skill and not de-risking.")
flat75 = C.R.sum() * 0.75
print(f"  reference: flat 0.75x on the same set = {flat75:+.2f}R")

Rd.to_csv(f"{S}/london_depth_conviction_sweep.csv", index=False)
print(f"\nwrote {S}/london_depth_conviction_sweep.csv")
