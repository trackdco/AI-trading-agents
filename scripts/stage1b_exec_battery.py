#!/usr/bin/env python3
"""STAGE 1b — EXECUTION-QUALITY component battery (the legitimate second attempt).

Direction prediction failed Stage 1. This battery tests EXECUTION components — rules that change
how the same in-window breakout trades are managed/selected, not which way to bet. All parameters
FIXED A PRIORI (standard practice values / train-only percentiles, no tuning on test):
  A partial50_1R : bank 50% at +1R, stop to breakeven, runner to original target
  B be_stop_1R   : move full stop to breakeven after +1R touch (no partial)
  C time_stop_60 : flatten at market if unresolved 60 min after entry
  D combo_A_C    : partial50@1R + BE + 60-min time-stop on the runner
  E conf_hold    : skip unless bar i0+1 holds (close stays beyond the broken range edge);
                   entry shifts to i0+2 open (later, safer)
  F chop_skip    : skip days with overnight range below the TRAIN 30th percentile
  G sweep_first  : only take breakouts that swept the 09:30-09:40 opening low/high first

Uniform paired framework: every component = a modified BOOK. Per event, delta = R_variant − R_base
(skipped trade -> R_variant = 0). Gate: test N>=30 nonzero-delta, paired bootstrap 95% CI of mean
delta entirely > 0, >=60% anchored folds positive, THEN BH FDR<=0.10 across ALL 41 hypotheses
tested this session on this outcome set (34 prior + 7 here) — sequential testing is corrected, not
hidden. Placebo (day-level sign shuffle) armed for any pass. Honest null if nothing survives.
"""
import json
import importlib.util
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
TRAIN_END = "2024-12-31"
SLIP = 0.25
rng = np.random.default_rng(42)
B = 3000

spec = importlib.util.spec_from_file_location("bias_lab", f"{S}/bias_lab.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
by_day = bl.by_day

RC = pd.read_csv(f"{S}/dol_records.csv")
EV = RC[(RC.get("has_dol", False) == True) & (RC.get("m2_taken", 0) == 1)].copy().reset_index(drop=True)
EV["is_train"] = EV.day <= TRAIN_END
print("=" * 80 + "\nSTAGE 1b — EXECUTION-QUALITY BATTERY (paired vs baseline book)\n" + "=" * 80)
print(f"events: {len(EV)} (train {int(EV.is_train.sum())} / test {int((~EV.is_train).sum())})")
print("params fixed a priori: partial 50%@+1R, BE@+1R, time-stop 60m, chop=train p30 ON-range, "
      "sweep window 09:30-09:40")

DAY = {}
for d in EV.day.unique():
    g = by_day[d]
    t = g.t.values
    pm = g[(g.t >= dtime(0, 0)) & (g.t < dtime(9, 40))]
    op = g[(g.t >= dtime(9, 30)) & (g.t < dtime(9, 40))]
    DAY[d] = dict(t=t, o=g.open.values.astype(float), h=g.high.values.astype(float),
                  l=g.low.values.astype(float), c=g.close.values.astype(float),
                  on_range=float(pm.high.max() - pm.low.min()) if len(pm) else np.nan,
                  o930h=float(op.high.max()) if len(op) else np.nan,
                  o930l=float(op.low.min()) if len(op) else np.nan)

def idx_at(t_arr, tt):
    w = np.where(t_arr == tt)[0]
    return int(w[0]) if len(w) else None

def walk(D, j_entry, entry, sd, tgt, bdir, be_at_1r=False, partial=False, tstop=None):
    """R outcome from entry bar j_entry. Conservative: stop checked before target each bar."""
    j16 = idx_at(D["t"], dtime(16, 0)) or (len(D["t"]) - 1)
    jflat = idx_at(D["t"], dtime(15, 55)) or (len(D["t"]) - 1)
    stop = entry - bdir * sd
    one_r = entry + bdir * sd
    banked, live, hit1r = 0.0, 1.0, False
    for j in range(j_entry, j16 + 1):
        hi, lo = D["h"][j], D["l"][j]
        hit_stop = (lo <= stop) if bdir > 0 else (hi >= stop)
        hit_tgt = (hi >= tgt) if bdir > 0 else (lo <= tgt)
        hit_one = (hi >= one_r) if bdir > 0 else (lo <= one_r)
        if hit_stop:
            pts = (stop - entry) * bdir - SLIP
            return banked + live * pts / sd
        if hit_one and not hit1r:
            hit1r = True
            if partial:
                banked += 0.5 * ((one_r - entry) * bdir - SLIP) / sd
                live = 0.5
            if be_at_1r or partial:
                stop = entry
        if hit_tgt:
            return banked + live * ((tgt - entry) * bdir - SLIP) / sd
        if tstop is not None and (j - j_entry) >= tstop:
            return banked + live * ((D["c"][j] - entry) * bdir) / sd
        if j >= jflat:
            return banked + live * ((D["c"][j] - entry) * bdir) / sd
    return banked + live * ((D["c"][j16] - entry) * bdir) / sd

# per-event geometry (from journal) + recomputed base R for exact pairing
base_R = np.zeros(len(EV)); ok = np.ones(len(EV), bool)
V = {k: np.zeros(len(EV)) for k in ["partial50_1R", "be_stop_1R", "time_stop_60", "combo_A_C", "conf_hold"]}
chop_thr = np.nanpercentile([DAY[d]["on_range"] for d in EV[EV.is_train].day.unique()], 30)
sel_chop = np.zeros(len(EV), bool); sel_sweep = np.zeros(len(EV), bool)
for i, r in EV.iterrows():
    D = DAY[r.day]
    tt = pd.to_datetime(r.t_init).time()
    i0 = idx_at(D["t"], tt)
    if i0 is None or i0 + 2 >= len(D["t"]):
        ok[i] = False; continue
    bdir = int(r.bdir); sd = float(r.m2_sd)
    entry = D["o"][i0 + 1] + bdir * SLIP
    tgt = entry + bdir * float(r.m2_tgt_dist)
    base_R[i] = walk(D, i0 + 1, entry, sd, tgt, bdir)
    V["partial50_1R"][i] = walk(D, i0 + 1, entry, sd, tgt, bdir, partial=True)
    V["be_stop_1R"][i] = walk(D, i0 + 1, entry, sd, tgt, bdir, be_at_1r=True)
    V["time_stop_60"][i] = walk(D, i0 + 1, entry, sd, tgt, bdir, tstop=60)
    V["combo_A_C"][i] = walk(D, i0 + 1, entry, sd, tgt, bdir, partial=True, tstop=60)
    # conf-hold: bar i0+1 must CLOSE still beyond the broken extreme (approx: beyond breakout close's range edge = r.px)
    held = (D["c"][i0 + 1] > r.px) if bdir > 0 else (D["c"][i0 + 1] < r.px)
    if held:
        e2 = D["o"][i0 + 2] + bdir * SLIP
        V["conf_hold"][i] = walk(D, i0 + 2, e2, sd, e2 + bdir * float(r.m2_tgt_dist), bdir)
    else:
        V["conf_hold"][i] = 0.0     # skipped
    sel_chop[i] = D["on_range"] >= chop_thr if not np.isnan(D["on_range"]) else True
    swept = ((D["l"][idx_at(D['t'], dtime(9, 40)):i0 + 1].min() <= D["o930l"]) if bdir > 0
             else (D["h"][idx_at(D['t'], dtime(9, 40)):i0 + 1].max() >= D["o930h"]))
    sel_sweep[i] = bool(swept) if not np.isnan(D["o930l"]) else False
V["chop_skip"] = np.where(sel_chop, base_R, 0.0)
V["sweep_first"] = np.where(sel_sweep, base_R, 0.0)

EVo = EV[ok].reset_index(drop=True); base_R = base_R[ok]
for k in V:
    V[k] = V[k][ok]
te = (~EVo.is_train).values; days = EVo.day.values
print(f"paired events usable: {len(EVo)}  |  recomputed base book: train E[R] "
      f"{base_R[~te].mean():+.3f}  test E[R] {base_R[te].mean():+.3f}")

def boot_ci_p(delta):
    bm = np.array([delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(B)])
    return (round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3)), \
           float(max((bm <= 0).mean(), 1.0 / B))

bounds = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
prev = json.load(open(f"{S}/stage1_battery.json"))
prev_ps = [r["te_p"] for r in prev["battery"]]
rows = []
for name, vr in V.items():
    delta = vr - base_R
    d_te = delta[te]; nz = d_te[np.abs(d_te) > 1e-12]
    ci, p = boot_ci_p(d_te)
    pos = valid = 0
    for j in range(len(bounds) - 1):
        fm = (days >= bounds[j]) & (days < bounds[j + 1])
        df_ = delta[fm]
        if (np.abs(df_) > 1e-12).sum() >= 10:
            valid += 1; pos += int(df_.mean() > 0)
    n_trades_te = int((np.abs(vr[te]) > 1e-12).sum())
    rows.append(dict(component=name, n_te_events=int(te.sum()), n_te_changed=len(nz),
                     n_te_trades=n_trades_te,
                     book_te_R=round(float(vr[te].mean()), 3),
                     base_te_R=round(float(base_R[te].mean()), 3),
                     delta_te=round(float(d_te.mean()), 3), delta_ci=ci, p=round(p, 4),
                     delta_tr=round(float(delta[~te].mean()), 3),
                     folds_pos=pos, folds_valid=valid,
                     win_te=round(100 * float((vr[te] > 0).mean()), 1)))
R = pd.DataFrame(rows).sort_values("delta_te", ascending=False).reset_index(drop=True)

all_ps = prev_ps + R.p.tolist()
def bh_reject(ps, q=0.10):
    m = len(ps); idx = sorted(range(m), key=lambda i: ps[i]); kmax = -1
    for rank, i in enumerate(idx, 1):
        if ps[i] <= q * rank / m:
            kmax = rank
    out = [False] * m
    for rank, i in enumerate(idx, 1):
        out[i] = rank <= kmax
    return out
bh_all = bh_reject(all_ps, 0.10)[len(prev_ps):]
R["bh_41"] = [bh_all[list(R.index).index(i)] if False else bh_all[i] for i in range(len(R))]
R["ci_pass"] = R.delta_ci.apply(lambda c: c[0] > 0)
R["fold_pass"] = R.apply(lambda r: r.folds_valid > 0 and r.folds_pos / r.folds_valid >= 0.6, axis=1)
R["PASS"] = (R.n_te_changed >= 30) & R.ci_pass & R.fold_pass & R.bh_41

print("\n--- EXECUTION BATTERY (paired delta vs baseline book, R/trade, TEST) ---")
for _, r in R.iterrows():
    print(f"  {r.component:14s} book E[R] {r.book_te_R:+.3f} (base {r.base_te_R:+.3f}) win {r.win_te}%  "
          f"delta {r.delta_te:+.3f} CI{r.delta_ci} p={r.p:.4f}  folds {r.folds_pos}/{r.folds_valid}  "
          f"train delta {r.delta_tr:+.3f}  n_changed={r.n_te_changed}  "
          f"{'PASS' if r.PASS else '-'}{' [BH41 ok]' if r.bh_41 else ''}")

survivors = R[R.PASS].component.tolist()
placebo = {}
for name in survivors:
    delta = V[name] - base_R
    day_u = EVo.day.unique()
    d_by_day = {d: delta[days == d].sum() for d in day_u}
    te_days = [d for d in day_u if d > TRAIN_END]
    real = np.mean([d_by_day[d] for d in te_days])
    perm = []
    vals = np.array([d_by_day[d] for d in te_days])
    for _ in range(2000):
        signs = rng.choice([-1, 1], len(vals))
        perm.append((vals * signs).mean())
    pp = float((np.array(perm) >= real).mean())
    placebo[name] = round(pp, 4)
    print(f"  placebo[{name}]: day-level sign-shuffle p={pp:.4f} "
          f"({'SURVIVES' if pp < 0.05 else 'FAILS -> not real'})")
final = [n for n in survivors if placebo.get(n, 1) < 0.05]

print("\n" + "=" * 80)
print(f"STAGE-1b SURVIVORS (after BH-41 + placebo): {final if final else 'EMPTY'}")
print("NOTE: this test block has now been consulted repeatedly this session. Any pass here is "
      "PROVISIONAL until confirmed on genuinely forward data (2026H2+).")
print("=" * 80)

R.assign(delta_ci=R.delta_ci.apply(list)).to_csv(f"{S}/stage1b_exec.csv", index=False)
json.dump(dict(battery=R.assign(delta_ci=R.delta_ci.apply(list)).to_dict("records"),
               survivors=final, placebo=placebo, chop_thr=round(float(chop_thr), 1),
               base_te_R=round(float(base_R[te].mean()), 3),
               n_hypotheses_cumulative=len(all_ps)),
          open(f"{S}/stage1b_exec.json", "w"))
print("saved stage1b_exec.csv, stage1b_exec.json")
