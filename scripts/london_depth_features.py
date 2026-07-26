#!/usr/bin/env python3
"""ORDER-BOOK FEATURES for the London 10-13 UK book -> conviction-sizing substrate.

Builds every qualifying London signal (pre-day-stop, so the largest honest sample), attaches
MBP-10 order-book features measured at the SIGNAL BAR CLOSE, and writes a feature matrix.

    output: $LONDON_SCRATCH/london_depth_features.csv

NO-LOOKAHEAD TIMING. The M15 frame uses label="right"/closed="right", so the bar labelled
10:15 spans 10:00:01-10:15:00 and the fill is the open of the next M15 bar, which is the 1-minute
bar beginning ~10:16. The depth row for minute 10:15 is the LAST book state inside 10:15:00-10:15:59,
i.e. strictly before the fill. That is the freshest snapshot that is honestly knowable, and it is
what every feature here is computed from. Lookback features (_d5, _d15) reach further back only.

THIN-BOOK DISCIPLINE. data/reference/depth_london_10_13/README.md measures the median level at
2 contracts / 2 orders. Absolute size thresholds are meaningless at that scale, so every size
feature is ALSO emitted normalised by the same day's session median. A "wall" in NQ is tens of
contracts, not thousands.

FEATURE FAMILIES (the ones that actually matter in a book, not just top-of-book):
  imbalance   bid-vs-ask size at L0, L0-4, L0-9, direction-signed (support minus resistance)
  counts      the same on ORDER COUNT rather than size -- many small orders vs few large ones
  avgsize     size/count, at best and across the book: big single orders = institutional prints
  thickness   total resting size, raw and vs the day's median (is the book unusually deep?)
  walls       largest level on the support and resistance side: distance, size, size-vs-median
  slope       how quickly size accumulates away from mid (steep = shallow book, air above)
  micro       size-weighted microprice minus mid, in ticks: pure pressure
  spread      best ask - best bid
  dynamics    5- and 15-minute deltas of thickness, imbalance and the support wall
              -- "wall pulled" / "book building" are the ones traders actually watch

WINDOW-EDGE CAVEAT. Depth coverage is 10:00-12:59 UK. A signal labelled 10:00 has no prior
minutes inside the file, so _d5/_d15 are NaN there; those columns are emitted as NaN rather than
back-filled. The 08:00-10:00 book lives in data/reference/depth_london/ in a different (wide CSV)
format and is NOT loaded here.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_depth_features.py
"""
import os
import glob
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
DEPTH_DIR = f"{WT}/data/reference/depth_london_10_13"

# ---------------------------------------------------------------- signals
print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukt"] = b.uk.dt.time

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
ud, utt, uts = M.ukday.values, M.ukt.values, M.uts.values


def _utc(x):
    """M.uts.values strips the tz -- restore it so timestamps join the UTC depth index."""
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def all_signals():
    """Every qualifying signal with its resolution. NO day-stop applied -- the day-stop is a
    position-management rule, and feature->outcome estimation wants the largest honest sample."""
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
        rows.append(dict(day=d, sig=i, res=j, ent=str(utt[i]), ext=str(utt[j]), dr=dr,
                         entry=en, rk=rk, net=net, R=net / (rk * PV), how=how,
                         mins=(j - i) * 15, feat_ts=_utc(uts[i])))
    return pd.DataFrame(rows).sort_values(["day", "sig"]).reset_index(drop=True)


SIG = all_signals()
print(f"qualifying signals: {len(SIG)}  netR {SIG.R.sum():+.2f}", flush=True)


def day_stop(mode):
    """'aswritten' = published book A (contains lookahead). 'realtime_single' = book C."""
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


IN_A = day_stop("aswritten")
IN_C = day_stop("realtime_single")
SIG["in_A"] = [ix in IN_A for ix in SIG.index]
SIG["in_C"] = [ix in IN_C for ix in SIG.index]

# ---------------------------------------------------------------- depth
print("load depth ...", flush=True)
files = sorted(glob.glob(f"{DEPTH_DIR}/nq_depth_london_*.parquet"))
if not files:
    raise SystemExit(f"no depth parquets under {DEPTH_DIR}")
D = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
D["ts"] = pd.to_datetime(D.ts, utc=True)
gaps = pd.read_csv(f"{DEPTH_DIR}/KNOWN_GAPS.csv", parse_dates=["date"])
drop = set(gaps.loc[gaps.status.isin(["MISSING", "DEGRADED"]), "date"].dt.strftime("%Y-%m-%d"))
D["ukday"] = D.ts.dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d")
if drop:
    print(f"  dropping flagged depth days: {sorted(drop)}")
    D = D[~D.ukday.isin(drop)]
print(f"  depth rows {len(D):,}  days {D.ukday.nunique()}  "
      f"{D.ukday.min()} -> {D.ukday.max()}", flush=True)

# pivot to one row per (ts) with arrays -- far faster than groupby per trade
D = D.sort_values(["ts", "side", "level"])
piv = {}
for side in ("bid", "ask"):
    sub = D[D.side == side]
    for col in ("price", "size", "ct"):
        piv[f"{side}_{col}"] = (sub.pivot_table(index="ts", columns="level", values=col,
                                                aggfunc="last").sort_index())
IDX = piv["bid_price"].index
# float64 everywhere: size/ct arrive as UNSIGNED ints, so `support - resist` wraps to a huge
# positive number whenever resist > support -- silently inverting every imbalance feature.
_f = lambda k: piv[k].values.astype(np.float64)
BP, BS, BC = _f("bid_price"), _f("bid_size"), _f("bid_ct")
AP, AS_, AC = _f("ask_price"), _f("ask_size"), _f("ask_ct")
POS = pd.Series(np.arange(len(IDX)), index=IDX)
DAYOF = pd.Series(IDX.tz_convert("Europe/London").strftime("%Y-%m-%d"), index=IDX)

# per-day median total thickness, for normalisation
tot_all = np.nan_to_num(BS).sum(1) + np.nan_to_num(AS_).sum(1)
DAYMED = pd.Series(tot_all, index=DAYOF.values).groupby(level=0).median().to_dict()


def snap(k, dr, entry):
    """Feature dict from book row k. dr=+1 long -> bids are SUPPORT."""
    bp, bs, bc = BP[k], BS[k], BC[k]
    ap, asz, ac = AP[k], AS_[k], AC[k]
    if not np.isfinite(bp[0]) or not np.isfinite(ap[0]):
        return {}
    sup_s, res_s = (bs, asz) if dr > 0 else (asz, bs)
    sup_c, res_c = (bc, ac) if dr > 0 else (ac, bc)
    sup_p, res_p = (bp, ap) if dr > 0 else (ap, bp)
    f = {}
    for lab, n in (("l0", 1), ("l5", 5), ("l10", 10)):
        ss, rs = np.nansum(sup_s[:n]), np.nansum(res_s[:n])
        f[f"imb_{lab}"] = (ss - rs) / (ss + rs) if (ss + rs) else 0.0
        sc, rc = np.nansum(sup_c[:n]), np.nansum(res_c[:n])
        f[f"cimb_{lab}"] = (sc - rc) / (sc + rc) if (sc + rc) else 0.0
    tot = np.nansum(bs) + np.nansum(asz)
    f["thick"] = tot
    f["sup_depth"] = np.nansum(sup_s)
    f["res_depth"] = np.nansum(res_s)
    ctot = np.nansum(bc) + np.nansum(ac)
    f["avgsize"] = tot / ctot if ctot else np.nan
    f["avgsize_l0"] = ((sup_s[0] / sup_c[0]) if sup_c[0] else np.nan)
    f["spread"] = float(ap[0] - bp[0])
    mid = (ap[0] + bp[0]) / 2.0
    f["_mid"] = mid
    micro = ((bp[0] * asz[0] + ap[0] * bs[0]) / (bs[0] + asz[0])) if (bs[0] + asz[0]) else mid
    f["micro_ticks"] = dr * (micro - mid) / TICK          # signed toward the trade
    # walls: largest level each side
    si, ri = int(np.nanargmax(sup_s)), int(np.nanargmax(res_s))
    f["supwall_size"] = float(sup_s[si])
    f["supwall_dist"] = float(abs(entry - sup_p[si]))
    f["reswall_size"] = float(res_s[ri])
    f["reswall_dist"] = float(abs(res_p[ri] - entry))
    f["wall_ratio"] = f["supwall_size"] / f["reswall_size"] if f["reswall_size"] else np.nan
    # slope: mean size of levels 5-9 over levels 0-4 (>1 = size sits away from mid)
    near, far = np.nanmean(np.r_[sup_s[:5], res_s[:5]]), np.nanmean(np.r_[sup_s[5:], res_s[5:]])
    f["slope"] = far / near if near else np.nan
    return f


print("attach features ...", flush=True)
recs = []
for _, r in SIG.iterrows():
    t = r.feat_ts.floor("min")
    if t not in POS.index:
        recs.append({}); continue
    k = int(POS[t])
    f = snap(k, r.dr, r.entry)
    if not f:
        recs.append({}); continue
    # CONTRACT-MISMATCH GUARD. Depth is NQ.v.0 and the bars are their own continuous series;
    # around a quarterly roll the two can sit on different contracts, which shows up as the
    # entry price being hundreds of points off the book. Genuine agreement is ~half a spread
    # (median 0.50pt, p90 1.51pt across all signals), so 10pt is far outside normal and can
    # only be a different instrument. Those snapshots are dropped, not silently used.
    if abs(r.entry - f["_mid"]) > 10.0:
        recs.append({}); continue
    f.pop("_mid", None)
    dm = DAYMED.get(r.day, np.nan)
    f["thick_vs_day"] = f["thick"] / dm if dm else np.nan
    f["supwall_vs_day"] = f["supwall_size"] / (dm / 20.0) if dm else np.nan   # vs mean level size
    # dynamics: same-day lookbacks only
    for lb in (5, 15):
        t0 = t - pd.Timedelta(minutes=lb)
        if t0 in POS.index and DAYOF.get(t0) == r.day:
            g = snap(int(POS[t0]), r.dr, r.entry)
            if g:
                f[f"thick_d{lb}"] = f["thick"] - g["thick"]
                f[f"thick_r{lb}"] = f["thick"] / g["thick"] if g["thick"] else np.nan
                f[f"imb_d{lb}"] = f["imb_l10"] - g["imb_l10"]
                f[f"supwall_d{lb}"] = f["supwall_size"] - g["supwall_size"]
                f[f"supwall_r{lb}"] = (f["supwall_size"] / g["supwall_size"]
                                       if g["supwall_size"] else np.nan)
    recs.append(f)

F = pd.concat([SIG.reset_index(drop=True), pd.DataFrame(recs)], axis=1)
FEATS = [c for c in F.columns if c not in SIG.columns]
print(f"\nfeature columns: {len(FEATS)}")
if "imb_l0" not in F.columns:
    raise SystemExit("no depth snapshot matched any signal -- check the timestamp join")
print(f"depth coverage on signals: {F.imb_l0.notna().sum()}/{len(F)} "
      f"({F.imb_l0.notna().mean()*100:.0f}%)")
miss = F[F.imb_l0.isna()]
if len(miss):
    print(f"  signals without a depth snapshot: {sorted(set(miss.day))}")
for lb in (5, 15):
    c = f"thick_d{lb}"
    if c in F:
        print(f"  {c} present on {F[c].notna().sum()}/{len(F)} "
              f"(NaN at the 10:00 window edge, as documented)")

out = f"{S}/london_depth_features.csv"
F.to_csv(out, index=False)
print(f"\nwrote {out}")
print(f"  books: A(published,lookahead)={int(F.in_A.sum())}  C(leakage-clean)={int(F.in_C.sum())}  "
      f"all signals={len(F)}")
