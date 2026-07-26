#!/usr/bin/env python3
"""PBAL — independent reproduction of the one check that survived family-wise correction.

RULE      PASS if d_imb_absmean <= 0.1056
VARIABLE  For each of the 120 one-minute MBP-10 snapshots in 08:00-09:59 UK:
              bid_tot = sum(bid_sz_00..09), ask_tot = sum(ask_sz_00..09)   (cast to float FIRST)
              imb     = (bid_tot - ask_tot) / (bid_tot + ask_tot)
          d_imb_absmean = mean(|imb|) over the 120 snapshots.
MEANING   LOW  = the pre-window book stayed genuinely two-sided for two hours
          HIGH = it was persistently lopsided, either way
          Deliberately UNSIGNED: every direction-signed variant failed.

WHY IT IS STRUCTURALLY CLEAN
  - source is data/reference/depth_london/ which spans 08:00-09:59 UK only; the last snapshot is
    09:59 and the earliest fill in the book is 10:00, so lookahead is impossible by construction
  - it reads only SIZES, never prices, so the NQ.v.0 continuous-contract roll cannot contaminate it
  - it is a whole-day constant, so it cannot encode anything about the individual trade

WHY IT IS STILL FRAGILE
  - 24 signals but only 14 distinct days (8 in H1, 6 in H2). Effective n is days, not signals.
  - depth begins 2025-06-02, so this can NEVER be validated on the 2023-24 holdout. Those 14 days
    are the entire evidence base that will exist until more data accrues.
  - the q33 threshold was the best of six tried (q20..q67 all positive); the reporting hardener
    priced that threshold-shopping at roughly 0.4-0.8R of the headline lift.

Writes $LONDON_SCRATCH/london_pbal.csv and a CHECKS file usable by london_score_ladder.py.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_prewindow_bal.py
"""
import glob
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
PRE = f"{WT}/data/reference/depth_london"
THR = 0.1056
SPLIT = "2026-01-13"
rng = np.random.default_rng(31)

BID = [f"bid_sz_{i:02d}" for i in range(10)]
ASK = [f"ask_sz_{i:02d}" for i in range(10)]


def day_absmean(path):
    try:
        d = pd.read_csv(path, usecols=["ts_event"] + BID + ASK)
    except (ValueError, KeyError):
        return None
    if not len(d):
        return None
    ts = pd.to_datetime(d.ts_event, utc=True, format="mixed").dt.tz_convert("Europe/London")
    # keep only 08:00-09:59 UK, and guard against a file that carries extra minutes
    keep = (ts.dt.hour >= 8) & (ts.dt.hour < 10)
    d, ts = d[keep], ts[keep]
    if len(d) < 100:
        return None
    b = d[BID].astype(np.float64).sum(axis=1)
    a = d[ASK].astype(np.float64).sum(axis=1)
    tot = b + a
    imb = np.where(tot > 0, (b - a) / tot, np.nan)
    v = np.nanmean(np.abs(imb))
    return dict(day=str(ts.dt.strftime("%Y-%m-%d").iloc[0]), n_snap=len(d), absmean=float(v))


if __name__ == "__main__":
    files = sorted(glob.glob(f"{PRE}/*.csv"))
    print(f"pre-window depth files: {len(files)}", flush=True)
    rows = [r for f in files if (r := day_absmean(f))]
    P = pd.DataFrame(rows)
    print(f"days parsed: {len(P)}   snapshots/day median {P.n_snap.median():.0f}")
    print(f"absmean  min {P.absmean.min():.4f}  q25 {P.absmean.quantile(.25):.4f}  "
          f"med {P.absmean.median():.4f}  q75 {P.absmean.quantile(.75):.4f}  max {P.absmean.max():.4f}")
    P.to_csv(f"{S}/london_pbal.csv", index=False)

    F = pd.read_csv(f"{S}/london_depth_features.csv")
    M = F.merge(P[["day", "absmean"]], on="day", how="left")
    print(f"\nsignals matched to a pre-window day: {M.absmean.notna().sum()}/{len(M)}")
    if M.absmean.isna().any():
        print(f"  unmatched days: {sorted(set(M.loc[M.absmean.isna(), 'day']))}")

    M["PBAL"] = (M.absmean <= THR)
    ok = M[M.absmean.notna()]
    p, q = ok[ok.PBAL], ok[~ok.PBAL]
    print(f"\n{'='*70}\nPBAL  (threshold {THR})\n{'='*70}")
    print(f"  PASS n={len(p):>2} ({p.day.nunique()} days)  WR {(p.R>0).mean()*100:>3.0f}%  avgR {p.R.mean():>+6.2f}")
    print(f"  FAIL n={len(q):>2} ({q.day.nunique()} days)  WR {(q.R>0).mean()*100:>3.0f}%  avgR {q.R.mean():>+6.2f}")
    print(f"  lift {p.R.mean()-q.R.mean():+.2f}R")
    for lab, H in (("H1", ok[ok.day < SPLIT]), ("H2", ok[ok.day >= SPLIT])):
        hp, hq = H[H.PBAL], H[~H.PBAL]
        print(f"  {lab}: pass n={len(hp)} ({hp.day.nunique()}d) avgR {hp.R.mean():+.2f} | "
              f"fail n={len(hq)} avgR {hq.R.mean():+.2f} | lift {hp.R.mean()-hq.R.mean():+.2f}R")

    # DAY-LEVEL test: signals cluster within days and PBAL is day-constant, so the honest
    # unit of observation is the day, not the signal.
    D = ok.groupby("day").agg(R=("R", "mean"), PBAL=("PBAL", "first")).reset_index()
    dp, dq = D[D.PBAL], D[~D.PBAL]
    obs = dp.R.mean() - dq.R.mean()
    lab = D.PBAL.values.copy()
    cnt = sum(1 for _ in range(20000)
              if (s := rng.permutation(lab)) is not None
              and abs(D.R.values[s].mean() - D.R.values[~s].mean()) >= abs(obs) - 1e-12)
    print(f"\n  DAY LEVEL (n={len(D)} days): pass {len(dp)}d avgR {dp.R.mean():+.2f} | "
          f"fail {len(dq)}d avgR {dq.R.mean():+.2f} | lift {obs:+.2f}R  perm p={(cnt+1)/20001:.4f}")
    bs = [np.mean(rng.choice(dp.R.values, len(dp))) - np.mean(rng.choice(dq.R.values, len(dq)))
          for _ in range(20000)]
    print(f"  day-bootstrap 95% CI on lift: [{np.percentile(bs,2.5):+.2f}, {np.percentile(bs,97.5):+.2f}]"
          f"   P(lift<=0) = {np.mean(np.array(bs)<=0):.4f}")

    # threshold plateau -- is q33 a knife-edge or a shelf?
    print(f"\n  threshold sensitivity (is {THR} a shelf or a spike?)")
    h1 = ok[ok.day < SPLIT]
    for qq in (0.20, 0.25, 0.33, 0.40, 0.50, 0.67):
        t = h1.absmean.quantile(qq)
        a_, b_ = ok[ok.absmean <= t], ok[ok.absmean > t]
        if len(a_) >= 5 and len(b_) >= 5:
            print(f"    H1 q{int(qq*100):<2} = {t:.4f}  n_pass {len(a_):>2}  "
                  f"lift {a_.R.mean()-b_.R.mean():+.2f}R")

    C = ok[ok.in_C]
    cp, cq = C[C.PBAL], C[~C.PBAL]
    print(f"\n  BOOK C (leakage-clean): pass n={len(cp)} avgR {cp.R.mean():+.2f} | "
          f"fail n={len(cq)} avgR {cq.R.mean():+.2f} | lift {cp.R.mean()-cq.R.mean():+.2f}R")
    base = C.R.sum()
    for hi, lo in ((1.0, 0.5), (1.5, 1.0), (1.25, 0.75)):
        w = np.where(C.PBAL, hi, lo)
        net = (C.R.values * w).sum()
        print(f"    size {hi}/{lo}: {net:+7.2f}R vs flat {base:+.2f}R  "
              f"(avg size {w.mean():.2f}, matched-exposure flat {base*w.mean():+.2f}R, "
              f"edge {net-base*w.mean():+.2f}R)")

    out = f"{S}/checks_pbal.py"
    with open(out, "w") as fh:
        fh.write('"""PBAL check for london_score_ladder.py."""\n'
                 "import numpy as np\n"
                 "CHECKS = {\n"
                 f'    "PBAL": (lambda r: float(r.absmean <= {THR}) '
                 'if np.isfinite(getattr(r, "absmean", np.nan)) else np.nan,\n'
                 '              "pre-window 08:00-09:59 UK book stayed two-sided"),\n'
                 "}\n")
    M.to_csv(f"{S}/london_features_pbal.csv", index=False)
    print(f"\nwrote {out} and {S}/london_features_pbal.csv")
