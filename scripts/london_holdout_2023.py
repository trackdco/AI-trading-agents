#!/usr/bin/env python3
"""THE HOLDOUT — does the London 10:00-13:00 UK book work before the window it was built on?

The book was developed on 2025-07-01 -> 2026-07-15. Bars exist back to 2023-01-02, and the
entry geometry needs no CVD and no depth, so the pre-sample period is a TRUE out-of-sample test.
It has been the largest open caveat on this project and it has never been run.

Rules are byte-identical to the in-sample builder (MA stack, 50-MA wick with close back, fading
volume, structural stop clamped 5-70pt, fixed 3R, 16:30 flat). Both day-stop variants are
reported: A as-published (contains the lookahead) and C leakage-clean (realtime day-stop, one
position at a time), because the in-sample headline used A and the honest number is C.

Reports per half-year so a regime effect is visible rather than averaged away.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_holdout_2023.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
IS_START, IS_END = "2025-07-01", "2026-07-15"

print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b = b.sort_values("ts").reset_index(drop=True)
m = (b.set_index("ts").resample("15min", label="right", closed="right")
     .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
          close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"]))
_uk = m.index.tz_convert("Europe/London")
m["ukt"] = _uk.time
m["ukday"] = _uk.strftime("%Y-%m-%d")
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["v10"] = m.volume.rolling(10).mean().shift(1)
m["slo"] = m.low.rolling(5).min()
m["shi"] = m.high.rolling(5).max()
M = m.reset_index(names="uts").dropna(subset=["ma200"]).reset_index(drop=True)
print(f"  M15 bars {len(M):,}   {M.ukday.min()} -> {M.ukday.max()}", flush=True)
a = {c: M[c].values for c in
     ["open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "v10", "slo", "shi"]}
ud, utt = M.ukday.values, M.ukt.values

SKIP = {"2025-11-28", "2026-04-03"}


def signals():
    rows = []
    for i in range(1, len(M) - 1):
        d = ud[i]
        if d in SKIP or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
            continue
        up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
        dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
        dr = 1 if (up and a["low"][i] <= a["ma50"][i]) else (-1 if (dn and a["high"][i] >= a["ma50"][i]) else 0)
        if dr == 0 or not (a["v10"][i] > 0 and a["volume"][i] < a["v10"][i]):
            continue
        en = a["open"][i + 1] + dr * TICK
        rf = min(a["slo"][i], a["ma50"][i]) if dr > 0 else max(a["shi"][i], a["ma50"][i])
        rk = abs(en - rf) + TICK
        if rk < 5 or rk > 70:
            continue
        st, tg = en - dr * rk, en + dr * 3 * rk
        gg, j, how = None, i + 1, None
        while j < len(M) and ud[j] == d:
            if utt[j] >= dtime(16, 30):
                gg = dr * (a["close"][j] - en); how = "time"; break
            hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
            ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
            if hs:
                gg = -rk - TICK; how = "stop"; break
            if ht:
                gg = 3 * rk - TICK; how = "target"; break
            j += 1
        if gg is None:
            j = min(j, len(M) - 1); gg = dr * (a["close"][j] - en); how = "dayend"
        net = gg * PV - COMM
        rows.append(dict(day=d, sig=i, res=j, ent=str(utt[i]), dr=dr, rk=rk,
                         net=net, R=net / (rk * PV), how=how))
    return pd.DataFrame(rows).sort_values(["day", "sig"]).reset_index(drop=True)


SIG = signals()


def day_stop(D, mode):
    keep = []
    for d, g in D.groupby("day"):
        taken, stopped = [], False
        for _, r in g.iterrows():
            if mode == "A":
                if stopped:
                    continue
                keep.append(r.name)
                if r.net < 0:
                    stopped = True
                continue
            if any(res <= r.sig and nt < 0 for res, nt in taken):
                continue
            if any(res > r.sig for res, _ in taken):
                continue
            keep.append(r.name)
            taken.append((r.res, r.net))
    return D.loc[keep].copy()


def line(D, lab):
    if not len(D):
        print(f"  {lab:<26}      0 trades"); return
    dd_eq = (D.sort_values(["day", "sig"]).R * 300).cumsum().values
    peak = np.maximum.accumulate(np.concatenate([[0.0], dd_eq]))
    print(f"  {lab:<26} {len(D):>5} trades  {D.day.nunique():>4}d  "
          f"WR {(D.R>0).mean()*100:>3.0f}%  netR {D.R.sum():>+8.2f}  "
          f"avgR {D.R.mean():>+6.2f}  ${dd_eq[-1]:>+9,.0f}  maxDD ${(peak[1:]-dd_eq).max():>7,.0f}")


if __name__ == "__main__":
    IS = SIG[(SIG.day >= IS_START) & (SIG.day <= IS_END)]
    OOS = SIG[SIG.day < IS_START]
    print(f"\nall qualifying signals {len(SIG)}   in-sample {len(IS)}   HOLDOUT {len(OOS)} "
          f"({OOS.day.min()} -> {OOS.day.max()})")

    for nm, D in (("IN-SAMPLE (built on)", IS), ("HOLDOUT (never seen)", OOS), ("ALL", SIG)):
        print(f"\n=== {nm} ===")
        line(D, "raw signals (no day-stop)")
        line(day_stop(D, "A"), "book A (as published)")
        line(day_stop(D, "C"), "book C (leakage-clean)")

    print(f"\n{'='*104}\nPER HALF-YEAR — raw signals, so the regime is visible rather than averaged away")
    print(f"{'='*104}")
    S2 = SIG.copy()
    S2["h"] = S2.day.str[:4] + np.where(S2.day.str[5:7].astype(int) <= 6, "H1", "H2")
    print(f"  {'half':<8} {'n':>4} {'days':>5} {'WR':>5} {'netR':>9} {'avgR':>7}   built-on?")
    for h, g in S2.groupby("h"):
        mark = "  <-- THE SAMPLE" if h in ("2025H2", "2026H1") else ""
        print(f"  {h:<8} {len(g):>4} {g.day.nunique():>5} {(g.R>0).mean()*100:>4.0f}% "
              f"{g.R.sum():>+9.2f} {g.R.mean():>+7.2f}{mark}")

    C_all = day_stop(SIG, "C").copy()
    C_all["h"] = C_all.day.str[:4] + np.where(C_all.day.str[5:7].astype(int) <= 6, "H1", "H2")
    print(f"\n  same, on book C (the tradeable book):")
    print(f"  {'half':<8} {'n':>4} {'WR':>5} {'netR':>9} {'avgR':>7}")
    for h, g in C_all.groupby("h"):
        print(f"  {h:<8} {len(g):>4} {(g.R>0).mean()*100:>4.0f}% {g.R.sum():>+9.2f} {g.R.mean():>+7.2f}")

    print(f"\n{'='*104}")
    oa, ia = OOS.R.mean(), IS.R.mean()
    print(f"VERDICT: holdout avgR {oa:+.3f} vs in-sample {ia:+.3f}. "
          f"Holdout netR {OOS.R.sum():+.1f} over {len(OOS)} signals / {OOS.day.nunique()} days.")
    print(f"{'='*104}")
