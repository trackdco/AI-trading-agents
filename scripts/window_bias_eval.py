#!/usr/bin/env python3
"""WINDOW-BIAS EVALUATION — can we call the 08:00->10:15 ET window direction, locked at 08:00?

Target = direction of the trading window 08:00->10:15 ET (NOT the daily close). One call/day
{bull/bear/neutral}, locked at 08:00 using only data <=08:00. Reuses the EXACT feature frame and
24 concept definitions from bias_lab.py (so the no-lookahead discipline is provably identical);
only the OUTCOME changes to the window, plus every requested fix:

Fix 1 selection frozen on TRAIN; all 24 reported; multiple-comparisons check; learner past-only.
Fix 2 Grade B = symmetric +/-15 first-touch race from the 08:00 open (in-direction target before
      the against-direction stop), path-walked on 1m bars, ties/ambiguous -> neutral.
Fix 3 base rate, acc, acc-base, 95% Wilson CI, 3x3 confusion, N>=30 gate.
Fix 4 anchored walk-forward folds + VIX-regime buckets.
Fix 6 endpoint/DST/holiday handling with an exclusion log (Good Fridays dropped).
Fix 7 volatility-normalized deadband (fraction of overnight range) alongside fixed 0/10/15/20.
Fix 5 (expectancy under real Campion v1.1) is gated on survivors and run separately if any exist.
"""
import json
import math
import importlib.util
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
TRAIN_END = "2024-12-31"

# ---- reuse bias_lab's feature frame F and concept dict C (identical <=08:00 construction) ----
spec = importlib.util.spec_from_file_location("bias_lab", f"{S}/bias_lab.py")
bl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bl)
F, C, by_day = bl.F, bl.C, bl.by_day
print("\n" + "=" * 78)
print("WINDOW-BIAS EVALUATION  (08:00 -> 10:15 ET)")
print("=" * 78)

# ---------------- Fix 6: window endpoints, path, exclusion log ----------------
def win_bars(g):
    return g[(g.t >= dtime(8, 0)) & (g.t <= dtime(10, 15))]

WIN, excl = {}, []
for day in F.index:
    g = by_day[day]
    if pd.Timestamp(day).dayofweek >= 5:
        excl.append((day, "weekend")); continue
    has_o = bool((g.t == dtime(8, 0)).any()); has_c = bool((g.t == dtime(10, 15)).any())
    if not (has_o and has_c):
        excl.append((day, "missing 08:00 or 10:15 endpoint (holiday/half-day)")); continue
    w = win_bars(g)
    pre = g[(g.t >= dtime(0, 0)) & (g.t < dtime(8, 0))]
    gold = g[(g.t >= dtime(9, 30)) & (g.t <= dtime(10, 15))]
    r930 = g[g.t == dtime(9, 30)]
    WIN[day] = dict(
        p_open=float(w.open.iloc[0]), p_close=float(w.close.iloc[-1]),
        hi=w.high.values.astype(float), lo=w.low.values.astype(float),
        p930=float(r930.open.iloc[0]) if len(r930) else np.nan,
        g_open=float(gold.open.iloc[0]) if len(gold) else np.nan,
        g_close=float(gold.close.iloc[-1]) if len(gold) else np.nan,
        ghi=gold.high.values.astype(float), glo=gold.low.values.astype(float),
        on_range=float(pre.high.max() - pre.low.min()) if len(pre) else np.nan,
        half=bool(g.t.iloc[-1] < dtime(15, 0)),
    )
F = F.loc[[d for d in F.index if d in WIN]].copy()
print(f"\ngraded days: {len(F)}   excluded: {len(excl)}")
from collections import Counter
for reason, n in Counter(r for _, r in excl).items():
    print(f"   excluded [{n:3d}]  {reason}")
gf = [d for d, r in excl if "endpoint" in r]
print(f"   endpoint-excluded dates (Good Fridays etc.): {gf}")
print(f"   half-days KEPT (window intact, flagged): {[d for d in F.index if WIN[d]['half']]}")

# ---------------- window outcomes: Grade A (deadbands) + Grade B (first-touch race) ----------------
def race(hi, lo, entry, R=15.0):
    """+1 if +R touched before -R, -1 if -R first, 0 if neither/ambiguous. Conservative on ties."""
    up, dn = entry + R, entry - R
    iu = np.argmax(hi >= up) if (hi >= up).any() else 10**9
    idn = np.argmax(lo <= dn) if (lo <= dn).any() else 10**9
    if iu == 10**9 and idn == 10**9:
        return 0
    if iu == idn:
        return 0                      # same bar spans both -> ambiguous
    return 1 if iu < idn else -1

net = np.array([WIN[d]["p_close"] - WIN[d]["p_open"] for d in F.index])
on_rng = np.array([WIN[d]["on_range"] for d in F.index])
def deadband_out(k):
    return np.where(net > k, 1, np.where(net < -k, -1, 0))
OUT_A = {k: deadband_out(k) for k in (0, 10, 15, 20)}
kv = 0.33 * np.nan_to_num(on_rng, nan=np.nanmedian(on_rng))     # vol-normalized band
OUT_A["vol"] = np.where(net > kv, 1, np.where(net < -kv, -1, 0))
OUT_B = np.array([race(WIN[d]["hi"], WIN[d]["lo"], WIN[d]["p_open"], 15.0) for d in F.index])
OUT = OUT_A[15]                                                  # PRIMARY grade (headline A, +/-15)

order = list(F.index)
is_train = np.array([d <= TRAIN_END for d in order])
te = ~is_train
SIG = {n: np.array([fn(F.loc[d]) for d in order]) for n, fn in C.items()}
vix_p = F["vix_p"].values                                        # prior-day VIX, known at 08:00

# ---------------- Fix 3 statistics helpers ----------------
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
    return (round(100*(c-h), 1), round(100*(c+h), 1))

def binom_sf(k, n, p):
    """one-sided P(X>=k) for X~Binom(n,p). exact."""
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1)))

def bh_reject(pvals, q=0.10):
    m = len(pvals); idx = sorted(range(m), key=lambda i: pvals[i]); rej = [False]*m; kmax = -1
    for rank, i in enumerate(idx, 1):
        if pvals[i] <= q*rank/m:
            kmax = rank
    for rank, i in enumerate(idx, 1):
        if rank <= kmax:
            rej[i] = True
    return rej

def grade(sig, out, mask):
    fire = (sig != 0) & mask
    n = int(fire.sum())
    if n == 0:
        return dict(n=0, acc=0.0, base_up=0.0, best_const=0.0, skill=0.0, ci=(0, 0), p=1.0)
    real = out[fire]; pred = sig[fire]
    acc = float((pred == real).mean())
    p_up = float((real == 1).mean()); p_dn = float((real == -1).mean()); p_ne = float((real == 0).mean())
    best_const = max(p_up, p_dn, p_ne)
    k = int((pred == real).sum())
    return dict(n=n, acc=round(100*acc, 1), base_up=round(100*p_up, 1),
                best_const=round(100*best_const, 1), skill=round(100*(acc-p_up), 1),
                skill_bc=round(100*(acc-best_const), 1), ci=wilson(k, n),
                p=round(binom_sf(k, n, p_up), 4))

def base_up(out, mask):
    o = out[mask]
    return round(100*(o == 1).mean(), 1) if len(o) else 0.0

# ---------------- Fix 1: freeze selection on TRAIN, report ALL, multiple-comparisons ----------------
rows = []
for n_, sig in SIG.items():
    tr = grade(sig, OUT, is_train); ts = grade(sig, OUT, te)
    tsB = grade(sig, OUT_B, te)
    rows.append(dict(concept=n_, tr_n=tr["n"], tr_acc=tr["acc"], tr_skill=tr["skill"],
                     te_n=ts["n"], te_acc=ts["acc"], te_base=ts["base_up"],
                     te_skill=ts["skill"], te_skill_bc=ts["skill_bc"],
                     te_ci_lo=ts["ci"][0], te_ci_hi=ts["ci"][1], te_p=ts["p"],
                     teB_acc=tsB["acc"], teB_skill=tsB["skill"], gate="OK" if ts["n"] >= 30 else "LOW-N"))
R = pd.DataFrame(rows)
# selection frozen on TRAIN: the "pick" = best train skill
pick = R.sort_values("tr_skill", ascending=False).iloc[0]["concept"]
R["selected_on_train"] = R["concept"] == pick
# multiple comparisons over the 24 test p-values
R["te_reject_BH10"] = bh_reject(R["te_p"].tolist(), q=0.10)
exp_false = round(len(R) * 0.05, 1)
R = R.sort_values("te_skill", ascending=False).reset_index(drop=True)

print("\n--- Fix 1: base rates (period) ---")
print(f"   P(window up, +/-15) : train {base_up(OUT, is_train)}%   test {base_up(OUT, te)}%")
print(f"   window neutral share: train {round(100*(OUT[is_train]==0).mean(),1)}%   "
      f"test {round(100*(OUT[te]==0).mean(),1)}%")
print(f"\n--- Fix 1: multiple comparisons ---")
print(f"   24 concepts screened; by chance ~{exp_false} would look significant at a=0.05.")
print(f"   concepts passing Benjamini-Hochberg FDR<=0.10 on TEST: "
      f"{R[R.te_reject_BH10].concept.tolist() or 'NONE'}")
print(f"   TRAIN-selected pick (frozen before seeing test): {pick}")

print("\n--- ALL 24 CONCEPTS (sorted by TEST skill = acc - base). CI/p on TEST. ---")
show = R[["concept", "te_n", "te_acc", "te_base", "te_skill", "te_ci_lo", "te_ci_hi",
          "te_p", "teB_acc", "tr_skill", "gate", "te_reject_BH10"]]
print(show.to_string(index=False))

# ---------------- walk-forward LEARNING ensemble (past-only) ----------------
from collections import deque
names = list(C)
ens = np.zeros(len(order), int)
hist = {n_: deque(maxlen=60) for n_ in names}
base_hist = deque(maxlen=120)          # trailing base-rate of "up" among past days (past-only)
journal = []
for i in range(len(order)):
    br = (sum(base_hist)/len(base_hist)) if len(base_hist) >= 20 else 0.5
    vote = 0.0
    for n_ in names:
        s = int(SIG[n_][i])
        if s == 0:
            continue
        h = hist[n_]
        if len(h) >= 15:
            acc = sum(h)/len(h)
            vote += s * (acc - 0.5)
    ens[i] = int(np.sign(vote)) if abs(vote) >= 0.5 else 0
    for n_ in names:                    # update AFTER deciding (past-only)
        s = int(SIG[n_][i])
        if s != 0:
            hist[n_].append(1 if s == OUT[i] else 0)
    base_hist.append(1 if OUT[i] == 1 else 0)
    mo = order[i][:7]
    if i == len(order)-1 or order[i+1][:7] != mo:
        snap = {n_: round(100*sum(hist[n_])/len(hist[n_])) for n_ in names if len(hist[n_]) >= 15}
        journal.append(dict(mo=mo,
                            trusted=[f"{n_}({a}%)" for n_, a in sorted(snap.items(), key=lambda x: -x[1]) if a >= 55][:5],
                            faded=[f"{n_}({a}%)" for n_, a in sorted(snap.items(), key=lambda x: x[1]) if a <= 45][:5]))

eg_tr = grade(ens, OUT, is_train); eg_te = grade(ens, OUT, te); eg_teB = grade(ens, OUT_B, te)
print("\n--- WALK-FORWARD LEARNING ENSEMBLE (past-only weights; never sees test aggregate) ---")
for lab, gg in [("TRAIN 23-24", eg_tr), ("TEST 25-26", eg_te), ("TEST Grade-B", eg_teB)]:
    print(f"   {lab:13s} fired {gg['n']:3d}d  acc {gg['acc']}%  base {gg['base_up']}%  "
          f"skill {gg['skill']:+.1f}  CI[{gg['ci'][0]},{gg['ci'][1]}]  p={gg['p']}")

# ---------------- Fix 4a: anchored walk-forward folds ----------------
print("\n--- Fix 4a: anchored walk-forward folds (select best concept on train-so-far, test next block) ---")
bounds = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
fold_out = []
for j in range(len(bounds)-1):
    b0, b1 = bounds[j], bounds[j+1]
    tr_mask = np.array([d < b0 for d in order]); te_mask = np.array([b0 <= d < b1 for d in order])
    if tr_mask.sum() < 60 or te_mask.sum() < 10:
        continue
    # select best concept by train skill, evaluate on this fold's test (single touch)
    best_c, best_s = None, -99
    for n_, sig in SIG.items():
        gg = grade(sig, OUT, tr_mask)
        if gg["n"] >= 20 and gg["skill"] > best_s:
            best_s, best_c = gg["skill"], n_
    gsel = grade(SIG[best_c], OUT, te_mask); gens = grade(ens, OUT, te_mask)
    fold_out.append(dict(test=f"{b0}->{b1}", sel=best_c, sel_acc=gsel["acc"], sel_base=gsel["base_up"],
                         sel_skill=gsel["skill"], sel_n=gsel["n"], ens_acc=gens["acc"],
                         ens_skill=gens["skill"], ens_n=gens["n"]))
FD = pd.DataFrame(fold_out)
print(FD.to_string(index=False))
pos = (FD["ens_skill"] > 0).sum()
print(f"   ensemble positive-skill folds: {pos}/{len(FD)}   selected-concept positive folds: "
      f"{(FD['sel_skill']>0).sum()}/{len(FD)}")

# ---------------- Fix 4b: VIX-regime buckets (cutpoints from TRAIN) ----------------
print("\n--- Fix 4b: TEST accuracy by VIX regime (terciles from TRAIN prior-day VIX) ---")
vtr = vix_p[is_train]; q1, q2 = np.nanpercentile(vtr, [33.3, 66.6])
print(f"   VIX terciles (train): low<{q1:.1f}  mid  high>{q2:.1f}")
vbuck = []
for lab, m in [("low", vix_p < q1), ("mid", (vix_p >= q1) & (vix_p <= q2)), ("high", vix_p > q2)]:
    mm = te & m
    gens = grade(ens, OUT, mm); gpick = grade(SIG[pick], OUT, mm)
    vbuck.append(dict(vix=lab, n_days=int(mm.sum()), base=base_up(OUT, mm),
                      ens_acc=gens["acc"], ens_n=gens["n"], ens_skill=gens["skill"],
                      pick_acc=gpick["acc"], pick_skill=gpick["skill"], pick_n=gpick["n"]))
VB = pd.DataFrame(vbuck)
print(VB.to_string(index=False))

# ---------------- Fix 3: 3x3 confusion for ensemble (TEST) ----------------
def confusion(sig, out, mask):
    labels = [-1, 0, 1]
    M = [[int(((sig == p) & (out == r) & mask).sum()) for r in labels] for p in labels]
    return M
conf = confusion(ens, OUT, te)
print("\n--- Fix 3: ensemble 3x3 confusion (TEST). rows=predicted, cols=realized [bear,neutral,bull] ---")
print("            realized: bear  neutral  bull")
for p, rowlab in zip(conf, ["pred bear ", "pred neut ", "pred bull "]):
    print(f"   {rowlab} {p[0]:5d} {p[1]:7d} {p[2]:6d}")

# ---------------- deadband sensitivity (Fix 7) for ensemble ----------------
print("\n--- Fix 7: ensemble TEST accuracy vs deadband (curve-fit check) ---")
for k in [0, 10, 15, 20, "vol"]:
    gg = grade(ens, OUT_A[k], te)
    lbl = f"vol(~{np.nanmedian(kv):.0f}pt)" if k == "vol" else f"{k}pt"
    print(f"   deadband {lbl:11s}: acc {gg['acc']}%  base {gg['base_up']}%  skill {gg['skill']:+.1f}  n={gg['n']}")

# ---------------- secondary: 09:30 lock on 09:30->10:15 gold sub-window ----------------
gnet = np.array([WIN[d]["g_close"] - WIN[d]["g_open"] for d in F.index])
OUT_G = np.where(gnet > 15, 1, np.where(gnet < -15, -1, 0))
eg_gold = grade(ens, OUT_G, te)
print("\n--- SECONDARY: 09:30->10:15 gold sub-window (ensemble, +/-15) TEST ---")
print(f"   base P(up) {base_up(OUT_G, te)}%   ensemble acc {eg_gold['acc']}%  "
      f"skill {eg_gold['skill']:+.1f}  n={eg_gold['n']}  CI[{eg_gold['ci'][0]},{eg_gold['ci'][1]}]")

# ---------------- survivors (for Fix 5 gating) ----------------
def survives(g_te):
    return (g_te["n"] >= 30) and (g_te["ci"][0] > g_te["base_up"]) and (g_te["skill"] > 0)
surv = [r.concept for _, r in R.iterrows()
        if survives(grade(SIG[r.concept], OUT, te))]
ens_surv = survives(eg_te)
fold_ok = pos >= max(3, int(0.6*len(FD)))
print("\n" + "=" * 78)
print("SURVIVORSHIP (for Fix 5 go/no-go)")
print("=" * 78)
print(f"   concepts with TEST 95%-CI lower bound ABOVE base rate AND n>=30: {surv or 'NONE'}")
print(f"   ensemble survives (CI>base, n>=30): {ens_surv}   walk-forward robust (>=60% folds +): {fold_ok}")
print(f"   => Fix 5 (real Campion v1.1 expectancy) runs only on survivors: "
      f"{surv if surv else ('ensemble' if ens_surv and fold_ok else 'NO SURVIVORS -> N/A')}")

# ---------------- persist ----------------
R.to_csv(f"{S}/window_concepts.csv", index=False)
FD.to_csv(f"{S}/window_folds.csv", index=False)
VB.to_csv(f"{S}/window_vixbuckets.csv", index=False)
json.dump(dict(
    n_days=len(order), base_tr=base_up(OUT, is_train), base_te=base_up(OUT, te),
    neutral_tr=round(100*(OUT[is_train]==0).mean(), 1), neutral_te=round(100*(OUT[te]==0).mean(), 1),
    ens=dict(tr=eg_tr, te=eg_te, teB=eg_teB, gold=eg_gold),
    confusion=conf, pick=pick, exp_false=exp_false,
    reject_BH=R[R.te_reject_BH10].concept.tolist(),
    folds=fold_out, vix=vbuck, survivors=surv, ens_survives=bool(ens_surv and fold_ok),
    journal=journal, excl_endpoint=gf, half_days=[d for d in F.index if WIN[d]["half"]],
    concepts=R.to_dict("records"),
    deadband_curve={str(k): grade(ens, OUT_A[k], te) for k in [0, 10, 15, 20, "vol"]},
), open(f"{S}/window_eval.json", "w"), default=lambda o: o if not isinstance(o, tuple) else list(o))
np.save(f"{S}/_win_sig.npy", np.array([SIG[n] for n in names]))
json.dump(dict(names=names, order=order, out=OUT.tolist(), outB=OUT_B.tolist(),
               is_train=is_train.tolist(), ens=ens.tolist()), open(f"{S}/_win.json", "w"))
print("\nsaved window_concepts.csv, window_folds.csv, window_vixbuckets.csv, window_eval.json")
