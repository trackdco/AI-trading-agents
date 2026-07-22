#!/usr/bin/env python3
"""STAGE 1 — COMPONENT EDGE GATE for the multi-agent trading sim.

Universe: the point-in-time journal of in-window (09:40-10:15) breakout events with a defined
DOL (dol_records.csv, built by dol_reach_eval.py under the audited <=-now harness). Outcome =
m2_R: realized R per trade under REAL Campion v1.1 money rules (slip, commission, pad-20 stop,
>40pt -> 5-micro derisk, nearest-draw target capped 4R, EOD flatten). ~33 candidate components,
each a point-in-time selection/direction rule on the event set.

PASS (all required, per spec #1):
  - test N >= 30
  - (component - counter-baseline) expectancy diff: bootstrap 95% CI lower bound > 0 on TEST
  - positive diff in >= 60% of valid anchored walk-forward folds
Then BH multiple-comparisons across the whole battery, and a shuffle/placebo test on anything
that passes. Survivors (if any) feed Stage 2; empty list -> STOP per directive 3/§1.

No naked numbers: every figure ships n, CI, baseline. Deterministic (fixed seed). Manifest:
data md5 + git HEAD + params. Fix-6 timestamp proof re-printed from the raw parquet.
"""
import hashlib
import json
import subprocess
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
TRAIN_END = "2024-12-31"
PARQ = "/home/user/gs/data/reference/nq_1m_master.parquet"
rng = np.random.default_rng(42)
B = 3000

# ---------------- run manifest + Fix-6 timestamp proof ----------------
h = hashlib.md5()
with open(PARQ, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 22), b""):
        h.update(chunk)
data_md5 = h.hexdigest()
git_head = subprocess.run(["git", "-C", "/home/user/AI-trading-agents", "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
print("=" * 80 + "\nSTAGE 1 — COMPONENT EDGE GATE\n" + "=" * 80)
print(f"manifest: data md5 {data_md5}  git {git_head[:12]}  seed 42  bootstrap {B}")

bars = pd.read_parquet(PARQ)
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert("America/New_York")
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
print("\nFix-6 timestamp proof (08:00/09:30/10:15 ET rows, winter + summer):")
for d in ["2023-01-17", "2023-07-11", "2024-03-15", "2024-11-06", "2025-06-10"]:
    g = bars[bars.day == d]
    row = {}
    for hh, mm in [(8, 0), (9, 30), (10, 15)]:
        m = g[g.ts.dt.time == dtime(hh, mm)]
        row[f"{hh:02d}:{mm:02d}"] = str(m.iloc[0].ts) if len(m) else "MISSING"
    print(f"  {d}: " + "  ".join(f"{k} -> {v}" for k, v in row.items()))
del bars

# ---------------- event journal + day-level concept signals ----------------
RC = pd.read_csv(f"{S}/dol_records.csv")
EV = RC[(RC.get("has_dol", False) == True) & (RC.get("m2_taken", 0) == 1)].copy()
EV["is_train"] = EV.day <= TRAIN_END
lab = json.load(open(f"{S}/_win.json"))
SIGD = np.load(f"{S}/_win_sig.npy")
names, order = lab["names"], lab["order"]
sig_by_day = {names[k]: dict(zip(order, SIGD[k])) for k in range(len(names))}
y = EV.m2_R.values
te_mask = (~EV.is_train).values
print(f"\nevents with real-money outcome: {len(EV)}  (train {int(EV.is_train.sum())} / "
      f"test {int((~EV.is_train).sum())})   outcome = Campion v1.1 R/trade")

# ---------------- component definitions (selection + counter-baseline masks) ----------------
COMP = {}
def add(name, sel, ctr, note=""):
    COMP[name] = (np.asarray(sel, bool), np.asarray(ctr, bool), note)

add("reaction_all", np.ones(len(EV), bool), np.zeros(len(EV), bool), "baseline 0 (no counter)")
add("bias_aligned", EV.aligned.values == True, EV.counter.values == True, "rolling bias at entry")
b930 = EV.b930.fillna(0).values; b800 = EV.b800.fillna(0).values; bd = EV.bdir.values
add("bias_at_0930", (b930 != 0) & (bd == b930), (b930 != 0) & (bd == -b930), "bias frozen 09:30")
add("bias_at_0800", (b800 != 0) & (bd == b800), (b800 != 0) & (bd == -b800), "bias frozen 08:00")
add("long_breakouts", bd == 1, bd == -1, "constant long")
add("short_breakouts", bd == -1, bd == 1, "constant short")
t_init = pd.to_datetime(EV.t_init, format="%H:%M:%S").dt.time
early = np.array([t <= dtime(9, 50) for t in t_init])
add("early_entry", early, ~early, "initiation <=09:50")
add("near_draw_R", (EV.R.values <= 1.5), (EV.R.values > 1.5), "geometry: near target")
vix = EV.vix.values
q1, q2 = np.nanpercentile(EV[EV.is_train].vix.dropna(), [33.3, 66.6])
add("vix_mid", (vix >= q1) & (vix <= q2), (vix < q1) | (vix > q2), "regime gate")
add("vix_high", vix > q2, vix <= q2, "regime gate")
for cn in names:
    s = np.array([sig_by_day[cn].get(d, 0) for d in EV.day])
    add(f"c_{cn}", (s != 0) & (bd == s), (s != 0) & (bd == -s), "daily concept gate")
print(f"battery: {len(COMP)} components (hypotheses), BH applied once across all")

# ---------------- stats ----------------
def boot_mean_ci(v):
    if len(v) == 0:
        return (0.0, 0.0)
    bm = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)]
    return (round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3))

def boot_diff(a, b):
    """diff of means a-b with CI and one-sided p (b empty -> baseline 0)."""
    if len(a) == 0:
        return 0.0, (0.0, 0.0), 1.0
    if len(b) == 0:
        bm = np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(B)])
    else:
        bm = np.array([a[rng.integers(0, len(a), len(a))].mean()
                       - b[rng.integers(0, len(b), len(b))].mean() for _ in range(B)])
    d = float(a.mean() - (b.mean() if len(b) else 0.0))
    p = float(max((bm <= 0).mean(), 1.0 / B))
    return round(d, 3), (round(float(np.percentile(bm, 2.5)), 3),
                         round(float(np.percentile(bm, 97.5)), 3)), round(p, 4)

def bh_reject(ps, q=0.10):
    m = len(ps); idx = sorted(range(m), key=lambda i: ps[i]); kmax = -1
    for rank, i in enumerate(idx, 1):
        if ps[i] <= q * rank / m:
            kmax = rank
    out = [False] * m
    for rank, i in enumerate(idx, 1):
        out[i] = rank <= kmax
    return out

bounds = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
days = EV.day.values
rows = []
for name, (sel, ctr, note) in COMP.items():
    a_te, b_te = y[sel & te_mask], y[ctr & te_mask]
    a_tr, b_tr = y[sel & ~te_mask], y[ctr & ~te_mask]
    d_te, ci_te, p_te = boot_diff(a_te, b_te)
    d_tr, _, _ = boot_diff(a_tr, b_tr)
    pos, valid = 0, 0
    for j in range(len(bounds) - 1):
        fm = (days >= bounds[j]) & (days < bounds[j + 1])
        af, bf = y[sel & fm], y[ctr & fm]
        if len(af) >= 10 and (len(bf) >= 10 or ctr.sum() == 0):
            valid += 1
            if af.mean() - (bf.mean() if len(bf) else 0.0) > 0:
                pos += 1
    n_te = int((sel & te_mask).sum())
    rows.append(dict(component=name, note=note, n_tr=int((sel & ~te_mask).sum()), tr_diff=d_tr,
                     n_te=n_te, te_expR=round(float(a_te.mean()), 3) if n_te else 0.0,
                     te_expR_ci=boot_mean_ci(a_te),
                     te_ctr_expR=round(float(b_te.mean()), 3) if len(b_te) else None,
                     te_diff=d_te, te_diff_ci=ci_te, te_p=p_te,
                     folds_pos=pos, folds_valid=valid,
                     gate_n="OK" if n_te >= 30 else "LOW-N"))
R = pd.DataFrame(rows)
R["bh_pass"] = bh_reject(R.te_p.tolist(), q=0.10)
R["ci_pass"] = R.te_diff_ci.apply(lambda c: c[0] > 0)
R["fold_pass"] = R.apply(lambda r: r.folds_valid > 0 and r.folds_pos / r.folds_valid >= 0.6, axis=1)
R["PASS"] = (R.n_te >= 30) & R.ci_pass & R.fold_pass
R = R.sort_values("te_diff", ascending=False).reset_index(drop=True)

print("\n--- BATTERY (sorted by TEST diff = component − counter-baseline, R/trade) ---")
for _, r in R.iterrows():
    print(f"  {r.component:22s} n_te={r.n_te:3d} E[R]={r.te_expR:+.3f} CI{r.te_expR_ci}  "
          f"ctr={r.te_ctr_expR if r.te_ctr_expR is not None else '0(base)':>7}  "
          f"diff={r.te_diff:+.3f} CI{r.te_diff_ci} p={r.te_p:.3f}  "
          f"folds {r.folds_pos}/{r.folds_valid}  train_diff={r.tr_diff:+.3f}  "
          f"{'PASS' if r.PASS else '-'}{' BH' if r.bh_pass else ''}{' ' + r.gate_n if r.gate_n != 'OK' else ''}")

survivors = R[R.PASS].component.tolist()
print(f"\nBH-corrected significant (FDR<=0.10): {R[R.bh_pass].component.tolist() or 'NONE'}")
print(f"PASS (N>=30 & diff-CI>0 & >=60% folds): {survivors or 'NONE'}")

# ---------------- placebo/shuffle audit on any PASS ----------------
placebo = {}
for name in survivors:
    sel, ctr, _ = COMP[name]
    day_list = EV.day.unique()
    lab_by_day = {}
    for d in day_list:
        m = (days == d)
        lab_by_day[d] = (bool(sel[m].any()), bool(ctr[m].any()))
    real_d, _, _ = boot_diff(y[sel & te_mask], y[ctr & te_mask])
    perm = []
    labs = list(lab_by_day.values())
    for _ in range(1000):
        rng.shuffle(labs)
        pm = dict(zip(day_list, labs))
        ps = np.array([pm[d][0] for d in days]); pc = np.array([pm[d][1] for d in days])
        a, b2 = y[ps & te_mask], y[pc & te_mask]
        if len(a) and len(b2):
            perm.append(a.mean() - b2.mean())
    pct = float((np.array(perm) >= real_d).mean()) if perm else 1.0
    placebo[name] = dict(real=real_d, placebo_p=round(pct, 4))
    print(f"  placebo[{name}]: real diff {real_d:+.3f}, shuffle p={pct:.3f} "
          f"({'SURVIVES' if pct < 0.05 else 'FAILS placebo -> not real'})")

final = [n for n in survivors if placebo.get(n, {}).get("placebo_p", 1) < 0.05]
print("\n" + "=" * 80)
print(f"STAGE-1 SURVIVOR LIST: {final if final else 'EMPTY'}")
if not final:
    print("=> per spec §1/§8: STOP. Stage 2+ (agents, meta-learner) is NOT built on nothing.")
print("=" * 80)

json.dump(dict(manifest=dict(data_md5=data_md5, git=git_head, seed=42, bootstrap=B,
                             train_end=TRAIN_END, outcome="Campion v1.1 m2_R"),
               n_events=len(EV), n_train=int(EV.is_train.sum()), n_test=int((~EV.is_train).sum()),
               n_components=len(COMP),
               battery=R.assign(te_expR_ci=R.te_expR_ci.apply(list),
                                te_diff_ci=R.te_diff_ci.apply(list)).to_dict("records"),
               bh_significant=R[R.bh_pass].component.tolist(),
               pass_pre_placebo=survivors, placebo=placebo, survivors=final),
          open(f"{S}/stage1_battery.json", "w"))
R.to_csv(f"{S}/stage1_battery.csv", index=False)
print("\nsaved stage1_battery.csv, stage1_battery.json")
