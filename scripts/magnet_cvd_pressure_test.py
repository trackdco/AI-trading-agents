#!/usr/bin/env python3
"""PRESSURE-TEST the magnet+CVD=60% April lead (engine-lane, Brake, 20 Jul 2026).

Advances the lead WITHOUT the missing Feb/Mar/May depth by asking: is n=10/60% real
signal or an in-sample small-n artifact? Three honesty tests:
  1. Outlier concentration  — is the +$3,345 / +1.01R carried by 1-2 trades?
  2. Wilson 95% CI on the win rate at n=10.
  3. Permutation test        — over the 30 April champion trades, how often does a RANDOM
                               10-subset match magnet+CVD's win-rate and avg-R? = p-value that
                               the selection beats random.
  4. Marginal value of the magnet over the depth-FREE combo (CVD-confirm + real-stop), since
     that combo needs no depth buy — this tells us whether pulling more depth is worth it.

Run from the getting-started-6lwnvs worktree (needs its data + the fixed selection_signal_test).
    python3 scripts/magnet_cvd_pressure_test.py
"""
import sys, importlib.util
from pathlib import Path
import numpy as np, pandas as pd

np.random.seed(7)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("sst", ROOT / "scripts" / "selection_signal_test.py")
sst = importlib.util.module_from_spec(spec); spec.loader.exec_module(sst)


def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (c-h, c+h)


def main():
    J = sst.load()
    apr = sst.add_magnet(J[J.day.str.startswith("2026-04")]).reset_index(drop=True)
    apr["R"] = apr.points / apr.risk_pts
    mc = apr[apr.magnet & apr.cvd_confirm].copy()
    print(f"April champion n={len(apr)}  |  magnet+CVD subset n={len(mc)}")
    print("="*68)

    # 1. concentration
    print("\n[1] THE 10 magnet+CVD TRADES (is it outlier-driven?)")
    show = mc[["day","dir","risk_pts","points","R","dollars","win"]].sort_values("dollars")
    print(show.to_string(index=False))
    tot = mc.dollars.sum(); top = mc.dollars.max()
    print(f"  total ${tot:+,.0f}  |  biggest single trade ${top:+,.0f} = {top/tot*100:.0f}% of P&L")
    print(f"  win rate {mc.win.mean()*100:.0f}%  avg {mc.R.mean():+.2f}R  median {mc.R.median():+.2f}R")
    print(f"  drop the single best trade -> {mc.sort_values('dollars')[:-1].R.mean():+.2f}R avg, "
          f"${mc.sort_values('dollars')[:-1].dollars.sum():+,.0f}")

    # 2. Wilson CI
    k = int(mc.win.sum()); n = len(mc)
    lo, hi = wilson(k, n)
    print(f"\n[2] WIN-RATE CONFIDENCE (n={n}, {k}W/{n-k}L)")
    print(f"  point 60%  |  Wilson 95% CI = [{lo*100:.0f}%, {hi*100:.0f}%]  <- base rate 33% sits inside")

    # 3. permutation vs random 10-of-30
    N = 50000
    wins = apr.win.values.astype(float); Rs = apr.R.values
    idx = np.arange(len(apr))
    rw = np.empty(N); rr = np.empty(N)
    for i in range(N):
        s = np.random.choice(idx, size=n, replace=False)
        rw[i] = wins[s].mean(); rr[i] = Rs[s].mean()
    p_win = (rw >= mc.win.mean()).mean(); p_r = (rr >= mc.R.mean()).mean()
    print(f"\n[3] PERMUTATION TEST (random {n}-of-{len(apr)}, {N:,} draws)")
    print(f"  P(random subset win% >= 60%) = {p_win:.3f}")
    print(f"  P(random subset avgR  >= {mc.R.mean():.2f}) = {p_r:.3f}   <- the real p-value")

    # 4. marginal value over depth-free combo
    print("\n[4] IS THE MAGNET WORTH THE DEPTH BUY? (April, magnet vs depth-free combo)")
    for lab, m in [("magnet + CVD  (needs depth)", apr.magnet & apr.cvd_confirm),
                   ("CVD + real-stop (NO depth)", apr.cvd_confirm & apr.real_stop),
                   ("magnet + CVD + real-stop", apr.magnet & apr.cvd_confirm & apr.real_stop)]:
        s = apr[m]
        if len(s):
            print(f"  {lab:30s} {len(s):2d}t  win {s.win.mean()*100:2.0f}%  "
                  f"${s.dollars.sum():+6,.0f}  {s.R.mean():+.2f}R")
    print("\nFull Feb-Jul depth-free combo for reference: CVD+real-stop = 73t / 42% / +0.65R (n=73).")


if __name__ == "__main__":
    main()
