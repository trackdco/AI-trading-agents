#!/usr/bin/env python3
"""Evaluate the no-trade (both-red) classifier (Angus 22 Jul). Single-signal separation vs an
equal-weight z-consensus STACK, judged the honest way: AUC (threshold-free) two-way out-of-fit
(2026->2025 and 2025->2026), plus precision/recall/$ at a fixed stand-down rate. No fitted
weights. Ships only if the stack beats the best single signal out-of-fit in BOTH directions.

    python -m scripts.eval_standdown
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# each signal oriented so HIGHER = more chop / more stand-down lean
SIGS = {
    "cvd_conv":   lambda f: -f.abs_cvd,          # low conviction -> chop
    "drive_con":  lambda f:  f.drive_contra.astype(float),  # open-drive contradiction
    "coil":       lambda f:  f.coil,             # balanced book -> chop
    "va_narrow":  lambda f: -f.va_width,         # narrow value area -> rotation
    "open_rng":   lambda f: -f.open_range,       # tight opening range -> chop
    "gap_small":  lambda f: -f.gap,              # small overnight gap -> balance
}


def auc(score, label):
    s = pd.Series(score).astype(float)
    y = np.asarray(label)
    m = s.notna().values
    s, y = s[m].values, y[m]
    if len(np.unique(y)) < 2:
        return np.nan
    order = s.argsort()
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    # average ties
    df = pd.DataFrame({"s": s, "r": ranks}); df["r"] = df.groupby("s").r.transform("mean")
    n1 = y.sum(); n0 = len(y) - n1
    return (df.r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def zscore(col, train):
    mu, sd = train.mean(), train.std()
    sd = sd if sd and not np.isnan(sd) else 1.0
    return (col - mu) / sd


def stack_score(tr, te):
    """equal-weight mean of train-standardized signals; NaN -> 0 (neutral)."""
    acc_tr = np.zeros(len(tr)); acc_te = np.zeros(len(te))
    for name, fn in SIGS.items():
        vtr, vte = fn(tr), fn(te)
        mu, sd = np.nanmean(vtr), np.nanstd(vtr)
        sd = sd if sd else 1.0
        acc_tr += np.nan_to_num((vtr - mu) / sd)
        acc_te += np.nan_to_num((vte - mu) / sd)
    return acc_tr / len(SIGS), acc_te / len(SIGS)


def dollar(te, flag):
    newpl = np.where(flag, 0.0, te.pl)
    d = newpl.sum() - te.pl.sum()
    g = te[flag]
    saved = -g[(g.both_red == 1) & (g.traded == 1)].pl.sum()
    killed = g[g.both_red == 0].pl.sum()
    return d, saved, killed


def main():
    F = pd.read_parquet("output/standdown_features.parquet")
    print(f"{len(F)} days   both-red base rate {F.both_red.mean()*100:.0f}%\n")

    print("=== SINGLE-SIGNAL out-of-fit AUC (threshold-free separation) ===")
    print(f"  {'signal':11s} {'2026->2025':>11s} {'2025->2026':>11s}   (0.50 = coin flip)")
    best_single = {}
    for name, fn in SIGS.items():
        a25 = auc(fn(F[F.yr == 2025]), F[F.yr == 2025].both_red)   # test 2025 (train-free metric)
        a26 = auc(fn(F[F.yr == 2026]), F[F.yr == 2026].both_red)
        best_single[name] = (a25, a26)
        print(f"  {name:11s} {a25:11.2f} {a26:11.2f}")
    # stack AUC out-of-fit
    print("\n=== STACK (equal-weight z-consensus) out-of-fit AUC ===")
    res = {}
    for train, test in ((2026, 2025), (2025, 2026)):
        tr, te = F[F.yr == train], F[F.yr == test]
        _, sc = stack_score(tr, te)
        res[test] = (te.reset_index(drop=True), sc)
        print(f"  train {train} -> test {test}:  AUC {auc(sc, te.both_red):.2f}")

    print("\n=== at a fixed stand-down rate (flag top-40% chop-scored days) ===")
    print(f"  {'method':14s} {'dir':11s} {'prec':>5s} {'rec':>5s} {'stood':>6s} {'$delta':>9s} {'saved':>8s} {'killed':>8s}")
    def report(name, test, sc, te):
        thr = np.nanquantile(sc, 0.60)                     # top 40%
        flag = sc >= thr
        tp = int((flag & (te.both_red == 1)).sum()); fp = int((flag & (te.both_red == 0)).sum())
        fn_ = int((~flag & (te.both_red == 1)).sum())
        prec = tp / max(tp + fp, 1) * 100; rec = tp / max(tp + fn_, 1) * 100
        d, saved, killed = dollar(te, flag)
        print(f"  {name:14s} {f'{2026 if test==2025 else 2025}->{test}':11s} "
              f"{prec:4.0f}% {rec:4.0f}% {int(flag.sum()):5d}  ${d:+8,.0f} ${saved:+7,.0f} ${killed:+7,.0f}")
    base = F.both_red.mean() * 100
    for test in (2025, 2026):
        te, sc = res[test]
        report("STACK", test, sc, te)
    # best single signal (cvd_conv) and coil for comparison, same fixed-rate
    for signame in ("cvd_conv", "coil"):
        for test in (2025, 2026):
            te = F[F.yr == test].reset_index(drop=True)
            report(signame, test, SIGS[signame](te).values.astype(float), te)
    print(f"\n  (both-red base rate {base:.0f}% — precision must clear this to add real value)")


if __name__ == "__main__":
    main()
