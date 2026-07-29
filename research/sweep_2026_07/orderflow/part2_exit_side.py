#!/usr/bin/env python3
"""PART 2 — EXIT-SIDE order-flow study: continuous in-trade flow, scored.

BASELINE: partially remediated (C only) + news filter, 182 PM trades. W and dep_* STILL LEAKY.

WHY THIS ANGLE. Every exit rule tested so far is flow-blind and clips the winners that carry
the book (H1 fixed targets FAIL, H4 bar-close MAE cuts FAIL, breakeven-at-+1R a wash). The
untested question is whether order flow, read DURING the trade, distinguishes a retrace that
resumes from one that reverses.

PRE-REGISTRATION — every constant below is frozen HERE, before any outcome was computed, and
is committed to 02_of_prereg.md (Amendment 4) before the scoring step runs. Nothing is swept.

  PEAK_MIN      = 1.0 R   a trade becomes eligible once its running peak reaches +1R
  RETRACE_TRIG  = 0.5 R   an EVENT fires at the first bar whose give-back from that running
                          peak reaches 0.5R
  RESUME        = after the event bar, price makes a NEW peak (> prior peak) before the stop
  REVERSE       = otherwise (stop touched, or trade life ends, without a new peak)
  WINDOW        = 15 minutes rolling, plus since-entry cumulative
  UNIT          = the FIRST event per trade (one observation per trade => independence by
                  construction; the all-events version is reported second, trade-clustered)
  SPLIT         = the re-fixed 2025-12-23 IS/OOS boundary, unchanged from Part 0

STRICT CAUSALITY. At event bar N every feature uses tape through bar N-1 only. The shift-test
harness is extended to EVERY bar of every trade, not just the fill: for each feature the strict
build is compared against a +1 twin (includes bar N) and a +15 twin (grossly leaky), and the
pass/fail is reported per feature AND per bar-index bucket.

CLUSTERING. Bars within a trade are not independent observations. Every interval here is a
TRADE-CLUSTER bootstrap. Bar counts are reported for the shift test only and are never used as
a sample size for inference.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
PEAK_MIN, RETRACE_TRIG = 1.0, 0.5
WIN, PAD, NBOOT, MIN_CELL = 15, 25.0, 4000, 10
rng = np.random.default_rng(20260729)
REP = {"prereg": dict(PEAK_MIN=PEAK_MIN, RETRACE_TRIG=RETRACE_TRIG, WIN=WIN,
                      unit="first event per trade", split="2025-12-23"),
       "baseline": "PARTIALLY REMEDIATED (C only) + news; W and dep_* STILL LEAKY"}

F = pd.read_csv(f"{OUT}/part0_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
print(f"{len(F)} trades")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values

CACHE = f"{OUT}/minute_grid.parquet"
if os.path.exists(CACHE):
    M = pd.read_parquet(CACHE)
    print(f"minute grid from cache: {len(M):,}")
else:
    print("load + band-clean tape ...", flush=True)
    T = pd.concat([pq.read_table(f, columns=["ts_minute", "price", "side", "volume"]).to_pandas()
                   for f in sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))],
                  ignore_index=True)
    T["ts_minute"] = pd.to_datetime(T.ts_minute, utc=True)
    T["volume"] = T.volume.astype("int64")
    band = bars.groupby(bars.index.tz_convert("America/New_York").strftime("%Y-%m-%d")) \
               .agg(lo=("low", "min"), hi=("high", "max"))
    T["eday"] = T.ts_minute.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    T = T.join(band, on="eday")
    T = T[T.hi.isna() | ((T.price >= T.lo - PAD) & (T.price <= T.hi + PAD))]
    M = T.assign(signed=T.volume.values * np.where(T.side.values == "B", 1, -1)) \
         .groupby("ts_minute", observed=True).agg(vol=("volume", "sum"), delta=("signed", "sum"))
    M = M.reindex(pd.date_range(M.index.min(), M.index.max(), freq="min", tz="UTC"), fill_value=0)
    M.to_parquet(CACHE)
    print(f"minute grid built + cached: {len(M):,}")

# align the minute grid to the bar index so a bar position maps to a grid position
MG = M.reindex(BI, fill_value=0)
VOL, DEL = MG.vol.to_numpy(float), MG.delta.to_numpy(float)

def roll(a, w, shift):
    """Rolling sum of the w values ending `shift` bars before the current bar.
    shift=1 -> strictly causal (uses <= N-1). shift=0 -> includes bar N (+1 twin).
    shift=-15 -> uses N+1..N+15 (grossly leaky control)."""
    c = np.concatenate([[0.0], np.cumsum(a)])
    n = len(a)
    idx = np.arange(n)
    hi = np.clip(idx - shift + 1, 0, n)
    lo = np.clip(hi - w, 0, n)
    return c[hi] - c[lo]

GR = {s: dict(vol=roll(VOL, WIN, s), delta=roll(DEL, WIN, s)) for s in (1, 0, -15)}
rng_hi = pd.Series(BH).rolling(WIN).max().shift(1).to_numpy()
rng_lo = pd.Series(BL).rolling(WIN).min().shift(1).to_numpy()
px_chg = pd.Series(BC).diff(WIN).shift(1).to_numpy()

# ---------------------------------------------------------------- events + per-bar features
FEATS = ["cvd_roll_dir", "cvd_since_dir", "imb_roll_dir", "absorp_roll", "delta_div_roll"]

def feats_at(k, k0, d, shift):
    g = GR[shift]
    v, dl = g["vol"][k], g["delta"][k]
    since_lo, since_hi = k0, max(k - shift + 1, k0)
    cum = float(DEL[since_lo:since_hi].sum()) * d
    rr = rng_hi[k] - rng_lo[k]
    pc = px_chg[k]
    return dict(
        cvd_roll_dir=float(dl) * d,
        cvd_since_dir=cum,
        imb_roll_dir=float(dl) * d / v if v > 0 else np.nan,
        absorp_roll=float(v) / rr if np.isfinite(rr) and rr > 0 else np.nan,
        delta_div_roll=(float(np.sign(pc) != np.sign(dl))
                        if np.isfinite(pc) and pc != 0 and dl != 0 else np.nan),
    )

ev_rows, bar_rows = [], []
for r in F.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    k0, kx = int(r.k0), int(r.k0) + int(r.life_min)
    if kx <= k0:
        continue
    peak = -np.inf
    fired = False
    for k in range(k0, kx + 1):
        hiR = (BH[k] - r.entry) * d / r.risk_pts if d > 0 else (r.entry - BL[k]) * d / r.risk_pts
        hiR = ((BH[k] - r.entry) if d > 0 else (r.entry - BL[k])) / r.risk_pts
        loR = ((BL[k] - r.entry) if d > 0 else (r.entry - BH[k])) / r.risk_pts
        clR = ((BC[k] - r.entry) if d > 0 else (r.entry - BC[k])) / r.risk_pts
        for s in (1, 0, -15):
            f = feats_at(k, k0, d, s)
            bar_rows.append(dict(ft=str(r.ft), bar=k - k0, shift=s, **f))
        if not fired and peak >= PEAK_MIN and (peak - loR) >= RETRACE_TRIG:
            # OUTCOME: new peak beyond `peak` before life end?
            fut_hi = np.array([((BH[j] - r.entry) if d > 0 else (r.entry - BL[j])) / r.risk_pts
                               for j in range(k + 1, kx + 1)]) if k < kx else np.array([])
            resume = bool(len(fut_hi) and fut_hi.max() > peak + 1e-9)
            ev_rows.append(dict(ft=str(r.ft), day=r.day, oos=bool(r.oos), bar=k - k0,
                                peak_R=float(peak), R=float(r.R), pl=float(r.pl),
                                resume=resume, **feats_at(k, k0, d, 1)))
            fired = True
        peak = max(peak, hiR)
E = pd.DataFrame(ev_rows)
B = pd.DataFrame(bar_rows)
print(f"\nbar-observations (shift harness): {len(B)//3:,} bars x 3 builds")
print(f"retrace EVENTS (first per trade): {len(E)} trades of {len(F)} "
      f"({len(E)/len(F)*100:.0f}%) reached +{PEAK_MIN}R then gave back {RETRACE_TRIG}R")
if len(E):
    print(f"  resume {int(E.resume.sum())} / reverse {int((~E.resume).sum())}  "
          f"| IS {int((~E.oos).sum())} OOS {int(E.oos.sum())}")

# ---------------------------------------------------------------- per-bar shift test
print("\n" + "=" * 96)
print("SHIFT TEST AT EVERY BAR (not just the fill) — strict vs +1 twin vs +15 leaky control")
print("=" * 96)
P = B.pivot_table(index=["ft", "bar"], columns="shift", values=FEATS)
buckets = [(0, 5, "bars 0-5"), (6, 15, "bars 6-15"), (16, 30, "bars 16-30"), (31, 10 ** 6, "bars 31+")]
shift_rep = {}
print(f"{'feature':16s} {'bucket':12s} {'n_bars':>8} {'differ +1':>10} {'differ +15':>11}  verdict")
for f in FEATS:
    a, b1, b15 = P[(f, 1)], P[(f, 0)], P[(f, -15)]
    bar_ix = P.index.get_level_values("bar")
    for lo, hi, lab in buckets:
        m = (bar_ix >= lo) & (bar_ix <= hi)
        if m.sum() == 0:
            continue
        d1 = float(((a[m] != b1[m]) & a[m].notna() & b1[m].notna()).mean())
        d15 = float(((a[m] != b15[m]) & a[m].notna() & b15[m].notna()).mean())
        ok = d1 > 0.05 and d15 > 0.05
        shift_rep[f"{f}|{lab}"] = dict(n=int(m.sum()), differ1=d1, differ15=d15, passes=ok)
        print(f"{f:16s} {lab:12s} {int(m.sum()):>8,} {d1*100:>9.1f}% {d15*100:>10.1f}%  "
              f"{'PASS' if ok else 'DEGENERATE'}")
REP["shift_per_bar"] = shift_rep
fails = [k for k, v in shift_rep.items() if not v["passes"]]
print(f"\nbuckets failing the shift test: {fails if fails else 'none'}")

# ---------------------------------------------------------------- score: resume vs reverse
print("\n" + "=" * 96)
print("SCORING — does in-trade order flow at the retrace distinguish RESUME from REVERSE?")
print("=" * 96)
if len(E) < 2 * MIN_CELL:
    print(f"INSUFFICIENT: only {len(E)} events; floor is {2*MIN_CELL}. Not scored.")
    REP["scoring"] = dict(insufficient=True, n=len(E))
else:
    def auc(s, y):
        m = np.isfinite(s)
        s, y = s[m], y[m].astype(bool)
        if y.sum() < 3 or (~y).sum() < 3:
            return np.nan
        r = stats.rankdata(s)
        n1, n0 = y.sum(), (~y).sum()
        return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

    def tboot(fn, sub):
        ix_all = np.flatnonzero(sub)
        out = []
        for _ in range(NBOOT):
            ix = rng.choice(ix_all, size=len(ix_all), replace=True)   # cluster = trade
            v = fn(ix)
            if np.isfinite(v):
                out.append(v)
        if len(out) < 100:
            return np.nan, np.nan, np.nan
        o = np.array(out)
        return (float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5)),
                float(min(2 * min((o <= 0.5).mean(), (o >= 0.5).mean()), 1.0)))

    Z = E[FEATS].apply(lambda s: s.rank(na_option="keep"))
    C = Z.corr().fillna(0).to_numpy()
    np.fill_diagonal(C, 1.0)
    ev_ = np.clip(np.linalg.eigvalsh(C), 0, None)
    M_eff = float(sum((e >= 1) + (e - np.floor(e)) for e in ev_))
    alpha = 1 - 0.95 ** (1 / M_eff)
    print(f"effective independent tests M_eff = {M_eff:.2f} of {len(FEATS)} nominal; "
          f"per-test alpha {alpha:.4f}")
    res = {}
    for half, sub, lab in (("OOS", E.oos.values, "OOS  << HEADLINE"),
                           ("IS", (~E.oos).values, "IS   (reference only)")):
        n = int(sub.sum())
        if n < MIN_CELL:
            print(f"\n--- {lab} n={n}: INSUFFICIENT, not scored ---")
            res[half] = dict(insufficient=True, n=n)
            continue
        print(f"\n--- {lab}  n={n} events (trade-clustered) ---")
        print(f"{'feature':16s} {'AUC':>7} {'95% CI':>18} {'p':>7}  reading")
        for f in FEATS:
            a = auc(E[f].values[sub], E.resume.values[sub])
            lo, hi, p = tboot(lambda ix: auc(E[f].values[ix], E.resume.values[ix]), sub)
            res[f"{half}|{f}"] = dict(auc=a, ci=[lo, hi], p=p, n=n)
            sig = "SURVIVES fw" if np.isfinite(p) and p <= alpha else "ns"
            print(f"{f:16s} {a:>7.3f} [{lo:>7.3f},{hi:>7.3f}] {p:>7.3f}  {sig}")
    REP["scoring"] = res
    REP["m_eff"] = M_eff
    REP["alpha_per_test"] = alpha
    base_rate = float(E.resume.mean())
    print(f"\nbase rate: {base_rate*100:.1f}% of retraces resume "
          f"({int(E.resume.sum())}/{len(E)}) — an AUC of 0.5 means flow adds nothing")
    REP["base_rate_resume"] = base_rate
    # power: what |AUC-0.5| would this n have detected?
    n_oos = int(E.oos.sum())
    det = 0.5 + 1.96 / np.sqrt(12 * max(n_oos, 1)) * 2
    print(f"detectable |AUC-0.5| at n={n_oos} (80% power, approx): "
          f"{det-0.5:.3f} -> AUC {det:.3f}; anything smaller is invisible at this sample")
    REP["detectable_auc_oos"] = det

E.to_csv(f"{OUT}/part2_events.csv", index=False)
json.dump(REP, open(f"{OUT}/part2_results.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part2_events.csv + part2_results.json")
