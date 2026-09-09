#!/usr/bin/env python3
"""Scheduled-flow calendar effects in NQ. Rules frozen in docs/PREREG-calendar-effects.md."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/AI-trading-agents/scripts")
from overnight_drift import sessions, roll_window, third_friday

TAPES = [("NQ 2023-26","nq_live_tape.parquet"),("NQ 2020-22","nq_2020_2022_1m.parquet"),("NQ 2017-19","nq_2017_2019_1m.parquet")]
BASE = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18/data/reference"

def buckets(idx):
    """idx = DatetimeIndex of sessions present in the tape. Returns dict name -> boolean Series."""
    s = pd.Series(idx, index=idx)
    ym = s.dt.to_period("M")
    rank_in_m = s.groupby(ym).rank(method="first")                 # 1 = first session of month
    n_in_m = s.groupby(ym).transform("size")
    last_of_m = rank_in_m == n_in_m
    first_of_m = rank_in_m == 1
    # turn of month = last session of a month + first 3 of the next
    tom = last_of_m | (rank_in_m <= 3)
    # expiry weeks
    tf = pd.Series({d: third_friday(d.year, d.month) for d in idx})
    same_week = (s.dt.isocalendar().week.values == pd.DatetimeIndex(tf.values).isocalendar().week.values) & \
                (s.dt.year.values == pd.DatetimeIndex(tf.values).year.values)
    exp_month = pd.Series(same_week, index=idx)
    exp_qtr = exp_month & s.dt.month.isin([3,6,9,12]).values
    # holidays = weekdays with no session, inside the tape's span
    allwd = pd.bdate_range(idx.min(), idx.max())
    hol = allwd.difference(idx)
    before_hol = pd.Series(False, index=idx); after_hol = pd.Series(False, index=idx)
    for h in hol:
        prv = idx[idx < h]; nxt = idx[idx > h]
        if len(prv): before_hol.loc[prv[-1]] = True
        if len(nxt): after_hol.loc[nxt[0]] = True
    iso = s.dt.isocalendar()
    wk = pd.Series(list(zip(iso.year, iso.week)), index=idx)
    rank_in_w = s.groupby(wk).rank(method="first"); n_in_w = s.groupby(wk).transform("size")
    return {"A turn of month": tom, "B last day of month": last_of_m, "C first day of month": first_of_m,
            "D quarterly expiry week": exp_qtr, "E monthly expiry week": exp_month,
            "F day before a holiday": before_hol, "G day after a holiday": after_hol,
            "H last session of week": rank_in_w == n_in_w, "I first session of week": rank_in_w == 1}

data = {}
for lab, f in TAPES:
    df = sessions(f"{BASE}/{f}")
    df["day_clean"] = df.day                              # intraday: roll-free by construction
    df["h24"] = np.where(df.index.isin(roll_window(df.index)), np.nan, df.hold24)
    data[lab] = df

print("ALL-DAYS BASELINE (day session, points/day after cost)")
for lab, df in data.items():
    bh = df.h24.dropna()
    print(f"  {lab}: day session {df.day_clean.mean():+.2f} pts/day over {len(df):,} sessions | "
          f"buy & hold {bh.mean():+.2f} pts/day (roll excluded)")

rows = []
pool = {}
for name in buckets(data["NQ 2023-26"].index):
    rec = {"bucket": name}
    xs = []
    for lab, df in data.items():
        b = buckets(df.index)[name]
        x = df.day_clean[b.values]; rest = df.day_clean[~b.values]
        rec[f"{lab} n"] = int(b.sum()); rec[f"{lab} pts"] = x.mean()
        rec[f"{lab} vs all"] = x.mean() - df.day_clean.mean()
        # benchmark: long only on bucket days, per day of exposure, vs buy & hold per day
        rec[f"{lab} beats BH"] = bool(x.mean() > df.h24.dropna().mean())
        xs.append(x)
    allx = pd.concat(xs)
    rec["pooled n"] = len(allx); rec["pooled pts"] = allx.mean()
    rec["pooled t"] = allx.mean() / (allx.std()/np.sqrt(len(allx)))
    rows.append(rec); pool[name] = allx
R = pd.DataFrame(rows)
print("\nNINE PRE-DECLARED BUCKETS - day-session points per day, and gap vs that tape's all-days mean")
cols = ["bucket"] + [c for lab in data for c in (f"{lab} n", f"{lab} pts", f"{lab} vs all")] + ["pooled n","pooled pts","pooled t"]
print(R[cols].to_string(index=False, float_format=lambda v: f"{v:+.2f}"))

print("\nSCORING THE FOUR PRE-REGISTERED CONDITIONS")
print(f"{'bucket':<26}{'1 beats all-days x3':>21}{'2 pooled t>2.5':>16}{'3 same sign x3':>16}{'4 beats buy&hold x3':>21}{'VERDICT':>10}")
passes = []
for _, r in R.iterrows():
    c1 = all(r[f"{lab} vs all"] > 0 for lab in data)
    c2 = r["pooled t"] > 2.5
    signs = [np.sign(r[f"{lab} pts"]) for lab in data]
    c3 = len(set(signs)) == 1 and signs[0] != 0
    c4 = all(r[f"{lab} beats BH"] for lab in data)
    ok = c1 and c2 and c3 and c4
    if ok: passes.append(r.bucket)
    y = lambda v: "yes" if v else "no"
    print(f"{r.bucket:<26}{y(c1):>21}{f'{r[chr(34)+chr(34)] if False else r[chr(112)+chr(111)+chr(111)+chr(108)+chr(101)+chr(100)+chr(32)+chr(116)]:+.2f}':>16}{y(c3):>16}{y(c4):>21}{'PASS' if ok else 'FAIL':>10}")
print(f"\nBuckets passing all four: {passes if passes else 'NONE'}")
print("\nPREDICTIONS")
best = R.loc[R['pooled pts'].idxmax(), 'bucket']
print(f"  P1 turn of month is the strongest bucket: {'CORRECT' if best.startswith('A') else 'WRONG'} (strongest = {best})")
t2 = R[(R['pooled t'] > 2.5)]
trap = [r.bucket for _, r in t2.iterrows() if not all(r[f'{lab} vs all'] > 0 for lab in data)]
print(f"  P2 at least one bucket clears t>2.5 but fails the all-three-tapes test: "
      f"{'CORRECT' if trap else 'WRONG'} ({trap if trap else 'none'})")
print(f"  P3 no bucket passes all four: {'CORRECT' if not passes else 'WRONG'}")
