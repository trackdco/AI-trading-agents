#!/usr/bin/env python3
"""JOB 2 (Brake, 2026-07-28): H0 evidence — re-derive the book over 2025-07-01 -> 2026-07-10,
once with the leaky column in the selection path and once without. Research lane only:
canon scripts are REUSED VERBATIM (build_canon / size_book / NewsGate), nothing in the canon
or live path is touched, no threshold is invented or tuned, and no outcome-conditioned choice
is made anywhere in this script.

ARMS
  L (leaky):  build_canon(T_window) as stored — the pre-window C check reads `conf_PM`
              (whole 08:00-09:30 PM window, a lookahead for pre fills).
  C (clean):  identical except conf_PM := pm_sofar_conf (PM CVD truncated AT fill) — the
              certified remediation, copied from scripts/leakage_clean_compare.py:45.
Each arm is produced BOTH WAYS on news, since the certified lineage has both:
  nonews:     no news gate, no dead zones  (= the arming-reference configuration,
              baseline_book_clean lineage)
  news:       NewsGate.load() + dead_zones [(595,600)]  (= baseline_book_news lineage)

SCOPE LIMITATION, stated up front: the Phase-0 audit's "40 FAIL columns" list was never
committed and its lane artifacts were destroyed with the containers (LANE-MAP.md). Of the
FAILs named in surviving prose (W, C/conf_PM, cvd_conf, div15, fade_last15, stacked_imb,
delta_div, the dep_* family, and the propagation W->D->WALLSZ->score->Q->struct->size), only
C has a committed clean counterpart column. W and dep_* have NO pre-fill-clean substitute in
any committed artifact, so they sit in the selection path of BOTH arms. This comparison
therefore isolates the C leak — the one leak with a certified fix — it is NOT "all 40".

FRESH-START SEMANTICS: build_canon's stateful layers (Layer-3 governor rolling-15, Layer-2e
trail-20 cold flag, Layer-2b nth, Layer-2c day ladder) start empty at 2025-07-01 — that is
what "derive over the period" means. The certified full-range book sliced to the window is
also reported so the boundary-state effect is visible instead of silent.

ANCHORS validated before any windowed number is printed:
  A1  build_canon(trade_matrix) reproduces output/canon_book.parquet to the cent.
  A2  sized clean full-range reproduces output/baseline_book_clean.parquet: 404 / +$52,522.81.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
sys.path.insert(0, REPO)
from scripts.baseline_dollar_risk import size_book          # noqa: E402
from scripts.canon_mechanical import build_canon            # noqa: E402
from src.canon.news_gate import NewsGate                    # noqa: E402

OUT = f"{REPO}/research/sweep_2026_07/orderflow"
BOOKS = f"{OUT}/job2_books"
os.makedirs(BOOKS, exist_ok=True)
W0, W1 = "2025-07-01", "2026-07-10"
R = {"window": [W0, W1]}

T = pd.read_parquet("output/trade_matrix.parquet")
lon = pd.read_parquet("output/london_canon_book.parquet")
gate = NewsGate.load()

# ---------------------------------------------------------------- anchors
cb = pd.read_parquet("output/canon_book.parquet")
A1 = build_canon(T.copy())
assert len(A1) == len(cb) == 713 and abs(A1.pl.sum() - cb.pl.sum()) < 0.01, \
    (len(A1), A1.pl.sum(), cb.pl.sum())
Tc_full = T.copy()
Tc_full["conf_PM"] = Tc_full["pm_sofar_conf"]
A2 = pd.concat([size_book(build_canon(Tc_full), "NY"), size_book(lon, "LONDON")],
               ignore_index=True).sort_values("fill").reset_index(drop=True)
bbc = pd.read_parquet("output/baseline_book_clean.parquet")
assert len(A2) == len(bbc) == 404 and abs(A2.pl.sum() - 52522.81) < 0.01 \
    and abs(A2.pl.sum() - bbc.pl.sum()) < 0.01, (len(A2), A2.pl.sum())
print(f"A1 OK: build_canon == canon_book  ({len(A1)} rows, pl ${A1.pl.sum():+,.2f})")
print(f"A2 OK: sized clean == baseline_book_clean  (404 / ${A2.pl.sum():+,.2f})")

# ---------------------------------------------------------------- windowed derivations
Tw = T[(T.day >= W0) & (T.day <= W1)].copy()
lon_w = lon[(lon.day >= W0) & (lon.day <= W1)].copy()
print(f"\nwindow {W0} -> {W1}: {len(Tw)}/{len(T)} candidate rows, "
      f"{Tw.day.nunique()} days; London rows {len(lon_w)}/{len(lon)}")
R["candidates"] = dict(rows=int(len(Tw)), days=int(Tw.day.nunique()))

Tw_clean = Tw.copy()
Tw_clean["conf_PM"] = Tw_clean["pm_sofar_conf"]
VAR = {}
for arm, frame in (("L", Tw), ("C", Tw_clean)):
    for news, kw in (("nonews", {}), ("news", dict(news_gate=gate, dead_zones=[(595, 600)]))):
        VAR[f"{arm}_{news}"] = build_canon(frame.copy(), **kw)

PM = lambda d: d[(d.win_ == "pre") & (d.fillhm >= 480) & (d.fillhm < 570)]      # half-open bins

def mech_stats(d):
    t = d[d["size"] > 0]
    pm = PM(t)
    return dict(taken=int(len(t)), pl=round(float(t.pl.sum()), 2),
                pl_2025=round(float(t[t.yr == 2025].pl.sum()), 2),
                pl_2026=round(float(t[t.yr == 2026].pl.sum()), 2),
                days=int(t.day.nunique()),
                pm_n=int(len(pm)), pm_pl=round(float(pm.pl.sum()), 2),
                pm_wr=round(float((pm.pl > 0).mean() * 100), 1) if len(pm) else None)

def sized_stats(ny_canon):
    b = pd.concat([size_book(ny_canon, "NY"), size_book(lon_w, "LONDON")],
                  ignore_index=True).sort_values("fill").reset_index(drop=True)
    ft = pd.to_datetime(b.fill, utc=True).dt.tz_convert("America/New_York")
    hm = ft.dt.hour * 60 + ft.dt.minute
    pm = b[(b.session == "NY") & (hm >= 480) & (hm < 570)]
    return b, dict(n=int(len(b)), pl=round(float(b.pl.sum()), 2),
                   ny_n=int((b.session == "NY").sum()),
                   ny_pl=round(float(b[b.session == "NY"].pl.sum()), 2),
                   lon_n=int((b.session == "LONDON").sum()),
                   lon_pl=round(float(b[b.session == "LONDON"].pl.sum()), 2),
                   pm_n=int(len(pm)), pm_pl=round(float(pm.pl.sum()), 2))

print("\n" + "=" * 96)
print("MECHANICAL LAYER (canon-native pl, fresh state at window start)")
print(f"{'variant':10s} {'taken':>6} {'pl':>12} {'pl 2025h':>11} {'pl 2026h':>11} "
      f"{'PM n':>5} {'PM pl':>11} {'PM WR':>6}")
for k, d in VAR.items():
    s = mech_stats(d)
    R[f"mech_{k}"] = s
    print(f"{k:10s} {s['taken']:>6} {s['pl']:>+12,.2f} {s['pl_2025']:>+11,.2f} "
          f"{s['pl_2026']:>+11,.2f} {s['pm_n']:>5} {s['pm_pl']:>+11,.2f} {s['pm_wr']:>5}%")
    d.to_parquet(f"{BOOKS}/mech_{k}.parquet")

print("\nSIZED LAYER (dollar-risk sizing, + London windowed; baseline_book lineage)")
print(f"{'variant':10s} {'n':>5} {'pl':>12} {'NY n':>5} {'NY pl':>11} {'LON n':>6} "
      f"{'LON pl':>11} {'PM n':>5} {'PM pl':>11}")
for k, d in VAR.items():
    b, s = sized_stats(d)
    R[f"sized_{k}"] = s
    print(f"{k:10s} {s['n']:>5} {s['pl']:>+12,.2f} {s['ny_n']:>5} {s['ny_pl']:>+11,.2f} "
          f"{s['lon_n']:>6} {s['lon_pl']:>+11,.2f} {s['pm_n']:>5} {s['pm_pl']:>+11,.2f}")
    b.to_parquet(f"{BOOKS}/sized_{k}.parquet")

# ---------------------------------------------------------------- overlap, trade-for-trade
def mk(d):
    return d.day.astype(str) + "|" + d.fill.astype(str) + "|" + d.direction.astype(str)

print("\n" + "=" * 96)
print("TRADE-FOR-TRADE OVERLAP, L vs C (mechanical taken rows; key = day|fill|direction)")
for news in ("nonews", "news"):
    tl = VAR[f"L_{news}"]; tl = tl[tl["size"] > 0]
    tc = VAR[f"C_{news}"]; tc = tc[tc["size"] > 0]
    tl2, tc2 = tl.assign(k=mk(tl)), tc.assign(k=mk(tc))
    shared = set(tl2.k) & set(tc2.k)
    sh_l = tl2[tl2.k.isin(shared)]
    sh_c = tc2[tc2.k.isin(shared)]
    szdiff = sh_l[["k", "size", "pl"]].merge(sh_c[["k", "size", "pl"]], on="k",
                                             suffixes=("_l", "_c"))
    nsz = int((szdiff.pl_l.round(2) != szdiff.pl_c.round(2)).sum())
    only_l, only_c = tl2[~tl2.k.isin(shared)], tc2[~tc2.k.isin(shared)]
    pml, pmc = PM(tl2), PM(tc2)
    pm_shared = set(pml.k) & set(pmc.k)
    o = dict(n_L=len(tl), n_C=len(tc), shared=len(shared),
             shared_pl_diff=nsz,
             only_L=len(only_l), only_L_pl=round(float(only_l.pl.sum()), 2),
             only_C=len(only_c), only_C_pl=round(float(only_c.pl.sum()), 2),
             pm_L=len(pml), pm_C=len(pmc), pm_shared=len(pm_shared),
             pm_only_L=int(len(pml) - len(pm_shared)), pm_only_C=int(len(pmc) - len(pm_shared)))
    R[f"overlap_{news}"] = o
    print(f"  [{news}]  L {o['n_L']} vs C {o['n_C']}: shared {o['shared']} "
          f"(of which {nsz} differ in size/pl), only-L {o['only_L']} (${o['only_L_pl']:+,.0f}), "
          f"only-C {o['only_C']} (${o['only_C_pl']:+,.0f})")
    print(f"           PM slice: L {o['pm_L']} vs C {o['pm_C']}, shared {o['pm_shared']}, "
          f"only-L {o['pm_only_L']}, only-C {o['pm_only_C']}")

# ---------------------------------------------------------------- boundary-state context
sl = cb[(cb.day >= W0) & (cb.day <= W1)]
sl = sl[sl["size"] > 0]
lw = VAR["L_nonews"]; lw = lw[lw["size"] > 0]
kk = set(mk(sl)) ^ set(mk(lw))
R["boundary_state"] = dict(full_slice_n=len(sl), full_slice_pl=round(float(sl.pl.sum()), 2),
                           fresh_n=len(lw), fresh_pl=round(float(lw.pl.sum()), 2),
                           sym_diff_trades=len(kk))
print(f"\nBOUNDARY-STATE CONTEXT (leaky arm): certified full-range book sliced to window = "
      f"{len(sl)} trades ${sl.pl.sum():+,.2f}; fresh-start derivation = {len(lw)} trades "
      f"${lw.pl.sum():+,.2f}; symmetric-difference {len(kk)} trades")

print(f"\nNEWS GATE: calendar releases {len(gate.releases)}, promoted-high names "
      f"{len(gate.promoted)}, stale_after {gate.stale_after.date()}")
R["news_gate"] = dict(releases=int(len(gate.releases)), promoted=int(len(gate.promoted)),
                      stale_after=str(gate.stale_after.date()))

json.dump(R, open(f"{OUT}/job2_report.json", "w"), indent=1, default=float)
print(f"\nwrote {BOOKS}/(mech|sized)_*.parquet + {OUT}/job2_report.json")
print("STOPPED before any scoring. Feature rebuild runs next as a separate step.")
