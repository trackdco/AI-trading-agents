#!/usr/bin/env python3
"""CVD-CONFIRM LOOKAHEAD AUDIT — the flag the whole conviction ladder is built on.

scripts/london_conviction.py:54-55 computes the "3-minute pre-entry CVD confirm" as:

    em = pd.Timestamp(a["uts"][i+1])              # <-- right-LABEL of the next M15 bar
    v3 = delta3.get(em - pd.Timedelta(minutes=1))

The M15 frame is built with label="right", so uts[i+1] is the next bar's CLOSE. The fill is
that bar's OPEN, fifteen minutes earlier. delta3 is a 3-minute rolling sum, so v3 covers the
three minutes ending one minute before the next bar's close -- i.e. minutes +11 to +13 AFTER
the fill. The flag reads tape from the future.

Correct window: the three minutes ending at the SIGNAL bar's close (uts[i]), which is the last
tape knowable before the fill at uts[i] + ~1 minute.

This script computes both flags on the same trade set and reports what changes. It is keyed to
the leakage-clean book C as well as the published book A, because both the day-stop lookahead
and this one inflate the same headline.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_cvd_lookahead.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
SPLIT = "2026-01-13"
rng = np.random.default_rng(5)

print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukt"] = b.uk.dt.time

print("load cvd ...", flush=True)
FILES = ["footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
         "footprint_apr2026", "footprint_may_jul2026"]
parts, cvd_days = [], set()
for f in FILES:
    p = f"{WT}/data/reference/cvd/{f}.parquet"
    if not os.path.exists(p):
        print(f"  MISSING {f}"); continue
    d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
    uk = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert("Europe/London")
    cvd_days |= set(uk.dt.strftime("%Y-%m-%d").unique())
    d["s"] = np.where(d.side == "B", d.volume, -d.volume)
    parts.append(d.groupby("ts_minute")["s"].sum())
    del d
delta = pd.concat(parts).groupby(level=0).sum().sort_index()
delta.index = pd.to_datetime(delta.index, utc=True)
delta3 = delta.rolling(3).sum()
print(f"  cvd days {len(cvd_days)}", flush=True)

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
M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= "2025-07-01") & (M.ukday <= "2026-07-15")].reset_index(drop=True)
a = {c: M[c].values for c in
     ["uts", "open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "v10", "slo", "shi"]}
ud, utt = M.ukday.values, M.ukt.values


def _utc(x):
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


rows = []
for i in range(1, len(M) - 1):
    d = ud[i]
    if d in ("2025-11-28", "2026-04-03") or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
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
    gg, j = None, i + 1
    while j < len(M) and ud[j] == d:
        if utt[j] >= dtime(16, 30):
            gg = dr * (a["close"][j] - en); break
        hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
        ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
        if hs:
            gg = -rk - TICK; break
        if ht:
            gg = 3 * rk - TICK; break
        j += 1
    if gg is None:
        j = min(j, len(M) - 1); gg = dr * (a["close"][j] - en)

    # ---- the two flags -------------------------------------------------
    bad_t = _utc(a["uts"][i + 1]) - pd.Timedelta(minutes=1)   # AS SHIPPED: +11..+13 min post-fill
    good_t = _utc(a["uts"][i])                                # 3 min ending at the signal-bar close
    # STRICT: the fill lands inside the minute labelled uts[i], so that minute's delta contains
    # post-fill trades. Ending one minute earlier is fully pre-fill and is the honest flag.
    strict_t = good_t - pd.Timedelta(minutes=1)
    vb, vg = delta3.get(bad_t, np.nan), delta3.get(good_t, np.nan)
    vs_ = delta3.get(strict_t, np.nan)
    covb = (d in cvd_days) and np.isfinite(vb)
    covg = (d in cvd_days) and np.isfinite(vg)
    covs = (d in cvd_days) and np.isfinite(vs_)
    rows.append(dict(day=d, sig=i, res=j, ent=str(utt[i]), dr=dr, rk=rk,
                     net=gg * PV - COMM, R=(gg * PV - COMM) / (rk * PV),
                     conf_bad=bool((vb > 0) if dr > 0 else (vb < 0)) if covb else False,
                     conf_good=bool((vg > 0) if dr > 0 else (vg < 0)) if covg else False,
                     conf_strict=bool((vs_ > 0) if dr > 0 else (vs_ < 0)) if covs else False,
                     cov_bad=covb, cov_good=covg, cov_strict=covs,
                     lag_min=int((bad_t - good_t).total_seconds() // 60)))

SIG = pd.DataFrame(rows).sort_values(["day", "sig"]).reset_index(drop=True)


def day_stop(mode):
    keep = []
    for d, g in SIG.groupby("day"):
        taken, stopped = [], False
        for _, r in g.iterrows():
            if mode == "aswritten":
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
    return set(keep)


SIG["in_A"] = [x in day_stop("aswritten") for x in SIG.index]
SIG["in_C"] = [x in day_stop("realtime_single") for x in SIG.index]


def perm_gap(flag, R, n=20000):
    obs = R[flag].mean() - R[~flag].mean()
    k = flag.sum()
    c = sum(1 for _ in range(n)
            if abs((p := rng.permutation(R))[:k].mean() - p[k:].mean()) >= abs(obs) - 1e-12)
    return obs, (c + 1) / (n + 1)


def report(D, label):
    print(f"\n{'='*78}\n{label}  (n={len(D)}, netR {D.R.sum():+.2f})\n{'='*78}")
    print(f"{'flag':<22} {'n_conf':>6} {'WR_conf':>8} {'WR_unconf':>10} "
          f"{'avgR_conf':>10} {'avgR_unc':>9} {'gap':>7} {'perm p':>8}")
    for col, nm in (("conf_bad", "AS SHIPPED (+13..15m)"), ("conf_good", "ends at sig close"),
                    ("conf_strict", "STRICT pre-fill")):
        f = D[col].values.astype(bool)
        if f.sum() < 3 or (~f).sum() < 3:
            print(f"{nm:<22}  too few"); continue
        g, p = perm_gap(f, D.R.values)
        print(f"{nm:<22} {f.sum():>6} {(D.R[f]>0).mean()*100:>7.0f}% "
              f"{(D.R[~f]>0).mean()*100:>9.0f}% {D.R[f].mean():>+10.2f} "
              f"{D.R[~f].mean():>+9.2f} {g:>+7.2f} {p:>8.4f}")
    # split-half
    print(f"\n  split-half gap (avgR confirmed minus unconfirmed):")
    for col, nm in (("conf_bad", "AS SHIPPED"), ("conf_good", "ends at close"),
                    ("conf_strict", "STRICT")):
        out = []
        for lab, H in (("H1", D[D.day < SPLIT]), ("H2", D[D.day >= SPLIT])):
            f = H[col].values.astype(bool)
            out.append(f"{lab} {H.R[f].mean()-H.R[~f].mean():+.2f}"
                       if f.sum() >= 3 and (~f).sum() >= 3 else f"{lab} n/a")
        print(f"    {nm:<12} {'   '.join(out)}")


if __name__ == "__main__":
    print(f"\nlag between the two windows: {SIG.lag_min.unique()} minutes "
          f"(entry is ~1 min after the signal-bar close, so 'as shipped' reads "
          f"{SIG.lag_min.iloc[0]-1}..{SIG.lag_min.iloc[0]+1} min AFTER the fill)")
    agree = (SIG.conf_bad == SIG.conf_good).mean()
    print(f"the two flags agree on {agree*100:.0f}% of signals "
          f"({int((SIG.conf_bad!=SIG.conf_good).sum())} disagreements of {len(SIG)})")

    for lbl, D in (("ALL SIGNALS", SIG), ("BOOK A (published, day-stop lookahead)", SIG[SIG.in_A]),
                   ("BOOK C (leakage-clean)", SIG[SIG.in_C])):
        report(D.reset_index(drop=True), lbl)

    print(f"\n{'='*78}\nECONOMICS — scheme A (confirm 1.0x / else 0.5x) on book C\n{'='*78}")
    C = SIG[SIG.in_C].reset_index(drop=True)
    base = C.R.sum()
    print(f"  flat 1.0x                       {base:>+8.2f}R")
    for col, nm in (("conf_bad", "AS SHIPPED (lookahead)"), ("conf_good", "ends at sig close"),
                    ("conf_strict", "STRICT pre-fill")):
        w = np.where(C[col], 1.0, 0.5)
        net = (C.R.values * w).sum()
        print(f"  {nm:<30} {net:>+8.2f}R   avg size {w.mean():.2f}   "
              f"vs matched-exposure flat {net - base*w.mean():>+7.2f}R")
    print("\n  'vs matched-exposure flat' is the honest column: it removes the de-risking effect.")
