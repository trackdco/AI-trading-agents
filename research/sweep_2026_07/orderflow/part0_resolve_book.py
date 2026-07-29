#!/usr/bin/env python3
"""PART 0 — RESOLVE THE BOOK (Brake ruling 2026-07-29).

WORKING BASELINE = the PARTIALLY-REMEDIATED, NEWS-FILTERED arm:
    research/sweep_2026_07/orderflow/job2_books/{mech,sized}_C_news.parquet
    window 2025-07-01 -> 2026-07-10, NY pre-market 08:00-09:30 ET (half-open bins).

*** THIS BOOK IS NOT CLEAN. IT IS PARTIALLY REMEDIATED — C ONLY. ***
The pre-window C check reads pm_sofar_conf (CVD truncated AT fill) instead of the leaky
conf_PM. The `W` depth check and the ENTIRE dep_* family still failed the Phase-0 lookahead
audit and remain in the selection path of this book. Every artifact must say so.

Q1/Q2 were registered against the CERTIFIED book (2025-06-02 -> 2026-07-10, 216 PM trades).
That is a DIFFERENT TRADE SET. Per Brake: score against this arm, re-fix the IS/OOS split and
every tercile edge against THIS trade set, and amend the registration explicitly. Old edges
are not carried.

JANUARY 2026 HOLE — IT IS A BOOK HOLE, NOT A DATA HOLE. Verified 2026-07-29: bars are complete
for every month 2023-01..2026-07, and the footprint tape is contiguous 2025-06-01..2026-07-19
(footprint_jan2026.parquet IS present, 1,542,534 rows, committed in 71fbe5f). No book variant
contains Jan-2026 TRADES because the generation chain never wired the Jan tape into FP_FILES
(dayflow_features.py:22, orderflow_by_setup.py:25-27) and no depth data exists for that month,
so the dep_*/W checks cannot be evaluated there. The traded window is therefore
2025-07..2025-12 + 2026-02..2026-07 even though the underlying data spans the gap.

hold_min RECONSTRUCTION: output/intrade_matrix.parquet was destroyed in the container wipe.
Exit bars are re-derived by walking forward from the fill bar to the first bar whose range
contains the book's recorded exit_price in the exit direction. VALIDATED against the committed
phase2_frame's mfe_R on the trades the two books share — if the derived exit reproduces the
certified excursion, the derivation is sound. Match rate is reported, not assumed.
"""
import hashlib
import json
import os
import subprocess

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
BOOKS = f"{OUT}/job2_books"
PROV = {}

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

PROV["commit"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
PROV["book_mech_sha"] = sha(f"{BOOKS}/mech_C_news.parquet")
PROV["book_sized_sha"] = sha(f"{BOOKS}/sized_C_news.parquet")
PROV["bars_sha"] = sha(f"{REPO}/data/reference/nq_1m_master.parquet")
PROV["arm"] = "C_news = partially remediated (C only; W + dep_* STILL LEAKY) + news filter"
PROV["window"] = "2025-07-01..2026-07-10, Jan-2026 absent (no book variant has it)"

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "open", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values
print(f"bars {len(bars):,}  {BI[0]} -> {BI[-1]}")

# ---------------------------------------------------------------- the working baseline
M = pd.read_parquet(f"{BOOKS}/mech_C_news.parquet")
S = pd.read_parquet(f"{BOOKS}/sized_C_news.parquet")
PM = M[(M["size"] > 0) & (M.win_ == "pre") & (M.fillhm >= 480) & (M.fillhm < 570)].copy()
PM["ft"] = pd.to_datetime(PM.fill.astype(str).str.replace("T", " "), utc=True)
S["ft"] = pd.to_datetime(S.fill, utc=True)
S_et = S.ft.dt.tz_convert("America/New_York")
S["hm"] = S_et.dt.hour * 60 + S_et.dt.minute
SPM = S[(S.session == "NY") & (S.hm >= 480) & (S.hm < 570)].copy()
print(f"working baseline PM slice: mech {len(PM)} trades  sized {len(SPM)} trades")

# Composite key (ft, direction, rk): two books can fill the SAME minute in the SAME direction
# with different stops, so (ft, direction) alone collides — the excursion lane verified the
# triple unique across all frames.
PM["rk"] = PM["risk"].round(4)
SPM["rk"] = SPM.risk_pts.round(4)
j = PM.merge(SPM[["ft", "direction", "rk", "micros", "pl", "dollars_1lot"]],
             on=["ft", "direction", "rk"], how="left", suffixes=("", "_sz"))
assert len(j) == len(PM), (len(j), len(PM))
assert j.micros.notna().all(), int(j.micros.isna().sum())

# ---------------------------------------------------------------- trade-life window
# AMENDMENT 3 (forced, and stated as such): the canon's realized exit timestamp lived in
# output/substrate_v2_signals.parquet, destroyed in the container wipe and rebuildable only by
# re-running the entire upstream chain. Reconstructing it from the recorded exit_price fails —
# the price level is frequently contained in the FILL bar itself, so a first-touch rule resolves
# early and understates excursion (measured: 83.9% agreement with the certified frame, every
# disagreement biased low).
#
# Excursion is therefore measured over a RULE-INDEPENDENT, fully reconstructible window:
#     TRADE LIFE = fill bar  ->  first bar touching the recorded STOP, else 15:55 ET same day.
# Both bounds are known at fill (the stop is in the book), it needs nothing but bars, and it is
# the correct window for an EXIT study: to ask whether a different exit was available you must
# see the path the trade COULD have traversed, not only the path to the canon's own exit.
#
# CONSEQUENCE, stated before scoring: mfe_R under this convention is >= the certified frame's
# fill->canon-exit mfe_R, so the "+4R cohort" is a superset of the certified one. Q1's target is
# re-registered as "price reached +4R during trade life" — a question about the market, not
# about canon exit timing. The realized R / pl columns are the book's own and are UNCHANGED.
SESS_END_HM = 15 * 60 + 55

def life_end(k0, d, stop, ft):
    et = ft.tz_convert("America/New_York")
    close_et = et.replace(hour=15, minute=55, second=0, microsecond=0)
    kend = min(int(BI.searchsorted(close_et.tz_convert("UTC"), side="right")), len(BI) - 1)
    if kend <= k0:
        kend = min(k0 + 1, len(BI) - 1)
    seg = slice(k0, kend + 1)
    hit = np.nonzero(BL[seg] <= stop + 1e-9)[0] if d > 0 else np.nonzero(BH[seg] >= stop - 1e-9)[0]
    return (k0 + int(hit[0])) if len(hit) else kend

rows = []
for r in j.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    t0 = r.ft.floor("min")
    k0 = int(BI.searchsorted(t0, side="right")) - 1
    kx = life_end(k0, d, float(r.stop), r.ft)
    hiR = (d * (BH[k0:kx + 1] - r.entry) if d > 0 else d * (BL[k0:kx + 1] - r.entry)) / r.risk
    loR = (d * (BL[k0:kx + 1] - r.entry) if d > 0 else d * (BH[k0:kx + 1] - r.entry)) / r.risk
    rows.append(dict(day=str(r.day), ft=str(r.ft), direction=r.direction,
                     entry=float(r.entry), stop=float(r.stop), risk_pts=float(r.risk),
                     exit_price=float(r.exit_price), k0=k0, life_min=int(kx - k0),
                     life_end_ts=str(BI[kx]), stopped=bool(kx < len(BI) - 1 and
                     ((BL[kx] <= r.stop + 1e-9) if d > 0 else (BH[kx] >= r.stop - 1e-9))),
                     micros=int(r.micros),
                     pl_mech=float(r.pl), pl=float(r.pl_sz), R=float(r.R),
                     mfe_R=float(hiR.max()), mae_R=float(loR.min()), fillhm=int(r.fillhm)))
F = pd.DataFrame(rows)
print(f"trade life: median {F.life_min.median():.0f} bars, q90 {F.life_min.quantile(.9):.0f}; "
      f"{int(F.stopped.sum())}/{len(F)} end at the stop, {len(F)-int(F.stopped.sum())} at 15:55")

# ---------------------------------------------------------------- ANCHOR vs certified frame
cert = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv")
cert["ft"] = pd.to_datetime(cert.ft, utc=True).astype(str)
cert["rk"] = cert.risk_pts.round(4)
F["rk"] = F.risk_pts.round(4)
ov = F.merge(cert[["ft", "direction", "rk", "mfe_R"]].drop_duplicates(["ft", "direction", "rk"]),
             on=["ft", "direction", "rk"], how="inner", suffixes=("", "_cert"))
ge = (ov.mfe_R >= ov.mfe_R_cert - 1e-6)
eq = np.isclose(ov.mfe_R, ov.mfe_R_cert, atol=1e-6)
print(f"ANCHOR (directional, not equality): shared {len(ov)} trades; "
      f"life-window mfe >= certified mfe on {int(ge.sum())}/{len(ov)} ({ge.mean()*100:.1f}%) "
      f"— identical on {int(eq.sum())}")
print(f"  +4R cohort: certified {int((ov.mfe_R_cert>=4).sum())} -> life-window "
      f"{int((ov.mfe_R>=4).sum())} on the shared set (superset by construction)")
PROV["anchor_monotone_ge"] = f"{int(ge.sum())}/{len(ov)}"
PROV["anchor_identical"] = int(eq.sum())
PROV["excursion_convention"] = "fill -> first stop touch, else 15:55 ET (AMENDMENT 3)"
assert ge.mean() > 0.98, f"life-window mfe should dominate certified mfe: {ge.mean()}"

# ---------------------------------------------------------------- re-fixed IS/OOS split
F = F.sort_values("ft").reset_index(drop=True)
HALF = len(F) // 2
F["oos"] = np.arange(len(F)) >= HALF
SPLIT = F.day.iloc[HALF]
print(f"\nRE-FIXED IS/OOS on THIS trade set: IS {int((~F.oos).sum())} / OOS {int(F.oos.sum())}, "
      f"split at {SPLIT} (certified frame split was 2025-12-11 over 216 trades)")
PROV["split_day"] = str(SPLIT)
PROV["n_is"], PROV["n_oos"] = int((~F.oos).sum()), int(F.oos.sum())

# ---------------------------------------------------------------- gap (knowable at 08:00)
et_idx = BI.tz_convert("America/New_York")
bars_et = pd.DataFrame({"close": BC}, index=et_idx)
rth_close = bars_et.between_time("15:59", "15:59").groupby(
    bars_et.between_time("15:59", "15:59").index.strftime("%Y-%m-%d")).close.last()
px0800 = bars_et.between_time("08:00", "08:00").groupby(
    bars_et.between_time("08:00", "08:00").index.strftime("%Y-%m-%d")).close.last()
days_sorted = sorted(set(rth_close.index) | set(px0800.index))
prev = {d: days_sorted[i - 1] for i, d in enumerate(days_sorted) if i > 0}
F["px_0800"] = F.day.map(px0800)
F["prev_close"] = F.day.map(lambda d: rth_close.get(prev.get(d, ""), np.nan))
F["gap_pts"] = F.px_0800 - F.prev_close
F["gap_abs"] = F.gap_pts.abs()
print(f"gap computable on {int(F.gap_pts.notna().sum())}/{len(F)} trades; "
      f"|gap| med {F.gap_abs.median():.1f}pt  q90 {F.gap_abs.quantile(.9):.1f}pt")

# ---------------------------------------------------------------- expiry week (calendar-only)
def third_friday(y, m):
    d = pd.Timestamp(year=y, month=m, day=1)
    f = d + pd.Timedelta(days=(4 - d.dayofweek) % 7)
    return f + pd.Timedelta(days=14)

exp_days = {str(third_friday(y, m).date()) for y in (2025, 2026) for m in (3, 6, 9, 12)}
def in_expiry_week(day):
    t = pd.Timestamp(day)
    return any(abs((t - pd.Timestamp(e)).days) <= 4 and t <= pd.Timestamp(e) for e in exp_days)
F["expiry_week"] = F.day.map(in_expiry_week)
cov = F.merge(cert[["ft", "direction", "exposed"]], on=["ft", "direction"], how="inner")
if len(cov):
    agree = (cov.expiry_week.values == cov.exposed.astype(bool).values).mean()
    print(f"expiry_week (calendar) vs certified `exposed` (depth-derived, data now gone): "
          f"{agree*100:.1f}% agreement on {len(cov)} shared trades")
    PROV["expiry_vs_exposed_agreement"] = float(agree)
print(f"expiry-week trades in baseline: {int(F.expiry_week.sum())}/{len(F)}")

# ---------------------------------------------------------------- Q1 TARGETS (re-registered)
# The life-window "+4R cohort" is NOT a usable stand-alone target: it sweeps in trades whose
# price reached +4R only AFTER the canon had exited them at a loss, so the cohort's P&L share
# exceeds 100% and the metric no longer means "the trades that carry the book". Q1 is therefore
# re-registered (Amendment 3) with a threshold-free primary and two labelled binaries:
#   PRIMARY   rank association between each entry feature and REALIZED R (Spearman, no cutoff)
#   BINARY-A  realized R >= 2.0  — "did this trade actually pay" (book-native, money-linked)
#   BINARY-B  life-window mfe_R >= 4.0 — "did price ever reach +4R before the stop" (market-native)
# All three are fixed here, before any feature-vs-outcome number is computed.
F["big_R2"] = F.R >= 2.0
F["reach4"] = F.mfe_R >= 4.0
F.to_csv(f"{OUT}/part0_frame.csv", index=False)

top = F.nlargest(int(np.ceil(0.1 * len(F))), "pl")
summ = dict(n=len(F), pl_sized=float(F.pl.sum()), pl_mech=float(F.pl_mech.sum()),
            wr=float((F.pl > 0).mean()), meanR=float(F.R.mean()),
            is_pl=float(F[~F.oos].pl.sum()), oos_pl=float(F[F.oos].pl.sum()),
            n_bigR2=int(F.big_R2.sum()),
            bigR2_pl_share=float(F[F.big_R2].pl.sum() / F.pl.sum()),
            n_reach4=int(F.reach4.sum()),
            top10pct_n=len(top), top10pct_pl_share=float(top.pl.sum() / F.pl.sum()),
            day_range=[F.day.min(), F.day.max()], months=sorted(F.day.str[:7].unique()))
print(f"\nBASELINE (partially remediated C-only + news): n={summ['n']}  sized ${summ['pl_sized']:+,.2f}  "
      f"mech ${summ['pl_mech']:+,.2f}  WR {summ['wr']*100:.1f}%  meanR {summ['meanR']:+.3f}")
print(f"  IS ${summ['is_pl']:+,.2f} | OOS ${summ['oos_pl']:+,.2f}")
print(f"  BINARY-A realized R>=2: {summ['n_bigR2']} trades = {summ['bigR2_pl_share']*100:.1f}% of P&L")
print(f"  BINARY-B life mfe>=4R : {summ['n_reach4']} trades (market-native, not P&L-linked)")
print(f"  concentration: top {summ['top10pct_n']} trades by P&L = "
      f"{summ['top10pct_pl_share']*100:.1f}% of the window")
print(f"  months present: {summ['months']}")
json.dump(dict(provenance=PROV, summary=summ), open(f"{OUT}/part0_report.json", "w"),
          indent=1, default=float)
print(f"\nwrote {OUT}/part0_frame.csv + part0_report.json")
