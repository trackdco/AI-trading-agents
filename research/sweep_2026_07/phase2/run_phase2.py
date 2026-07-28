#!/usr/bin/env python3
"""PHASE 2 RUNNER — NY pre-market 08:00-09:29, per the APPROVED registration + Brake's six
amendments (2026-07-28). Research lane only: reads repo artefacts, writes ONLY into
research/sweep_2026_07/phase2/.

AMENDMENTS APPLIED
  A1  H2 and H4 are re-labelled IN-SAMPLE (selected from Phase-1 results computed on all 216
      trades; H4's theta range came from the 0.98R global max which includes the OOS half).
      Neither is reported under an out-of-sample heading anywhere in the outputs.
  A2  H0 conditionality: the leaky columns SELECTED these trades. Every result dict carries
      `conditional_on_h0` = True and the dashboard headers it.
  A3  Effective sample: the +4R cohort size, its OOS count, and top-5 concentration are computed
      exactly and attached next to every funded-P&L figure.
  A4  The H1 inconsistency is resolved: 138 was the 08:00 bucket's TOTAL n; the OOS census
      69/24/16 is correct. H1 applies to the WHOLE window (OOS n = 216 - 108 = 108).
  A5  H3 is NOT run (moved to the not-tested table). Comparison budget 20 -> 17.
  A6  The 30-OOS floor is sourced: it is Brake's own brief ("no rule is reported as viable on
      fewer than 30 out-of-sample trades in the bucket it applies to"), applied to OOS n. It is
      a refuse-to-report threshold, NOT a validation bar — at sd(R)~2.0, n=30 gives SE~0.37R, so
      only effects > ~0.7R/trade are even detectable above it.

COST ASSUMPTIONS for re-simulated exits (stated, not read from a doc — the costsizing lane's
rules.md was lost with the container; these are conservative and identical across variants):
  commission $1.24 round-trip per MNQ micro; slippage 1 tick = $0.50/micro on stop and
  time/marketable exits, $0 on resting-limit target fills. The INCUMBENT uses the book's
  recorded pl (the canon's own cost model), so incumbent-vs-variant comparisons mix two cost
  models at the margin; stated wherever shown.

FUNDED RULES (as documented in HEADLINE-NUMBERS/SAFETY-SPINE and applied by the costsizing lane):
  start 50,000; EOD-trailing DD $2,000 (line = max(prior, EOD equity - 2000), locks at 50,000
  once equity >= 52,000); Tier-1 daily-loss halt: stop the day once realized day P&L <= -$800
  (the -4R floor figure); 40-micro clamp. DD-scaled sizing (H6 only):
  scale = base_dollar(available_dd)/200 with base = 200 + 75*floor((ad-3000)/1000) above $3k.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/phase2")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(73)

COMM_RT = 1.24        # $/micro round trip (assumption, stated above)
SLIP_MKT = 0.50       # $/micro, 1 MNQ tick, on marketable exits only
START_EQ = 50_000.0
DD_AMT = 2_000.0
LOCK_AT = 52_000.0
DAY_HALT = -800.0
NBOOT = 5_000

# ---------------------------------------------------------------- load + join
b = pd.read_parquet(f"{REPO}/output/baseline_book_clean.parquet")
b["ft"] = pd.to_datetime(b.fill, utc=True)
b["et"] = b.ft.dt.tz_convert("America/New_York")
b["hm"] = b.et.dt.hour * 60 + b.et.dt.minute
PM = b[(b.session == "NY") & (b.hm >= 480) & (b.hm < 570)].sort_values("ft").reset_index(drop=True)
assert len(PM) == 216 and abs(PM.pl.sum() - 18376.0) < 1e-6, (len(PM), PM.pl.sum())

cb = pd.read_parquet(f"{REPO}/output/canon_book.parquet")
cb["ft"] = pd.to_datetime(cb.fill, utc=True)
im = pd.read_parquet(f"{REPO}/output/intrade_matrix.parquet")
im["ft"] = pd.to_datetime(im.fill, utc=True)
# Join on the composite key (ft, direction, risk_pts) — two books can fill the SAME minute in
# the SAME direction with different stops, so (ft, direction) alone collapses 8 trades. The
# excursion lane verified this triple unique across all three frames.
for d_ in (cb, im):
    d_["rk"] = d_["risk"].round(4)
PM["rk"] = PM.risk_pts.round(4)
cb_k = cb.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "entry", "stop"]]
im_k = im.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "hold_min"]]
J = PM.merge(cb_k, on=["ft", "direction", "rk"], how="left")
J = J.merge(im_k, on=["ft", "direction", "rk"], how="left")
J["R"] = J.dollars_1lot / (J.risk_pts * 20.0)
assert len(J) == 216 and J.hold_min.notna().all() and J.entry.notna().all(), \
    (len(J), int(J.hold_min.isna().sum()), int(J.entry.isna().sum()))

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "open", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BO, BH, BL, BC = bars.index, bars.open.values, bars.high.values, bars.low.values, bars.close.values

# chronological 50/50 split (the walk-forward's outermost frame)
HALF = len(J) // 2
J["oos"] = np.arange(len(J)) >= HALF
SPLIT_DAY = J.day.iloc[HALF]

# ---------------------------------------------------------------- per-trade path walk
def walk_fixed_target(r, r_tgt):
    """Fixed-R-target variant: same entry/stop, exit at target/stop/15:55 ET close."""
    d = 1 if r.direction == "long" else -1
    e, risk = float(r.entry), float(r.risk_pts)
    stop = e - d * risk
    tgt = e + d * r_tgt * risk
    t0 = r.ft.floor("min")
    k0 = int(BI.searchsorted(t0, side="right"))
    eod = r.et.replace(hour=15, minute=55).tz_convert("UTC")
    kend = min(int(BI.searchsorted(eod, side="right")), len(BI) - 1)
    for k in range(k0, kend):
        if (BL[k] <= stop) if d > 0 else (BH[k] >= stop):
            return -risk, "stop"
        if (BH[k] >= tgt) if d > 0 else (BL[k] <= tgt):
            return r_tgt * risk, "target"
    return d * (BC[kend - 1] - e), "eod"


def walk_mae_cut(r, theta):
    """H4: canon exit unless bar-CLOSE adverse excursion >= theta*R first; then exit that close."""
    d = 1 if r.direction == "long" else -1
    e, risk = float(r.entry), float(r.risk_pts)
    t0 = r.ft.floor("min")
    k0 = int(BI.searchsorted(t0, side="right"))
    kx = min(k0 + int(r.hold_min), len(BI) - 1)
    for k in range(k0, kx):                      # strictly before the canon exit bar
        adv = d * (e - BC[k])
        if adv >= theta * risk:
            return d * (BC[k] - e), "cut"
    return None, "canon"                          # canon exit stands (use recorded pl)


def pts_to_funded(pts, micros, marketable):
    per_micro = pts * 2.0 - COMM_RT - (SLIP_MKT if marketable else 0.0)
    return micros * per_micro


def funded_series(df, pl_col):
    """Run the funded account: Tier-1 day halt + EOD-trailing DD. Returns dict."""
    eq, line, day_pl, cur_day = START_EQ, START_EQ - DD_AMT, 0.0, None
    halted_days, skipped, busted, min_avail = 0, 0, False, 1e9
    taken_pl = []
    for day_, pl in zip(df["day"].values, df[pl_col].values):
        if day_ != cur_day:
            if cur_day is not None:
                line = min(max(line, eq - DD_AMT), START_EQ)   # EOD ratchet, LOCKED at the 50k floor
            cur_day, day_pl = day_, 0.0
        if day_pl <= DAY_HALT:
            skipped += 1
            continue
        eq += pl
        day_pl += pl
        taken_pl.append(pl)
        min_avail = min(min_avail, eq - line)
        if eq <= line:
            busted = True
        if day_pl <= DAY_HALT:
            halted_days += 1
    return dict(terminal=float(np.sum(taken_pl)), busted=bool(busted),
                min_available_dd=round(min_avail, 2), halted_days=int(halted_days),
                trades_skipped_by_halt=int(skipped), n=len(taken_pl))


def day_block_bootstrap_bust(df, pl_col, nsim=NBOOT, ddscale=False):
    days = df.day.unique()
    by_day = {d: df[df.day == d][pl_col].values for d in days}
    micros_by_day = {d: df[df.day == d]["micros"].values for d in days}
    busts = 0
    for _ in range(nsim):
        order = rng.choice(days, size=len(days), replace=True)
        eq, line = START_EQ, START_EQ - DD_AMT
        dead = False
        for d in order:
            pls, mics = by_day[d], micros_by_day[d]
            avail = eq - line
            scale = 1.0
            if ddscale and avail > 3000:
                scale = (200 + 75 * np.floor((avail - 3000) / 1000)) / 200.0
            day_pl = 0.0
            for pl, m in zip(pls, mics):
                if day_pl <= DAY_HALT * (scale if ddscale else 1.0):
                    continue
                day_pl += pl * scale
            eq += day_pl
            line = min(max(line, eq - DD_AMT), START_EQ)   # EOD ratchet, LOCKED at the 50k floor
            if eq <= line:
                dead = True
                break
        busts += dead
    return 100.0 * busts / nsim


def dcb_ci(df, col, n=4000):
    """Day-clustered bootstrap CI on a mean."""
    days = df.day.unique()
    by = {d: df[df.day == d][col].values for d in days}
    ms = []
    for _ in range(n):
        pick = rng.choice(days, size=len(days), replace=True)
        v = np.concatenate([by[d] for d in pick])
        ms.append(v.mean())
    return [float(np.percentile(ms, 2.5)), float(np.percentile(ms, 97.5))]


RES = {"conditional_on_h0": True, "split_day": str(SPLIT_DAY),
       "oos_n": int(J.oos.sum()), "is_n": int((~J.oos).sum())}

# ---------------------------------------------------------------- A3: effective sample, exact
print("effective sample ...", flush=True)
mfe = []
for r in J.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    t0 = r.ft.floor("min")
    k0 = int(BI.searchsorted(t0, side="right")) - 1
    kx = min(k0 + int(r.hold_min), len(BI) - 1)
    w_hi = BH[k0:kx + 1].max() if kx >= k0 else BH[k0]
    w_lo = BL[k0:kx + 1].min() if kx >= k0 else BL[k0]
    fav = (w_hi - r.entry) if d > 0 else (r.entry - w_lo)
    mfe.append(fav / r.risk_pts)
J["mfe_R"] = mfe
coh4 = J[J.mfe_R >= 4.0]
top26 = J.nlargest(len(coh4), "pl")
RES["effective_sample"] = dict(
    plus4R_cohort_n=int(len(coh4)), plus4R_cohort_pl=float(coh4.pl.sum()),
    plus4R_share_of_window_pl=float(coh4.pl.sum() / J.pl.sum()),
    plus4R_in_OOS_half=int((coh4.ft >= J.ft.iloc[HALF]).sum()),
    top5_pl_share_of_OOS=float(J[J.oos].nlargest(5, "pl").pl.sum() / max(J[J.oos].pl.sum(), 1e-9)),
    note="every funded-P&L criterion below is effectively a test on the OOS members of this cohort",
)
print("  ", RES["effective_sample"], flush=True)

# ---------------------------------------------------------------- H1 (OOS-legitimate)
print("H1 fixed targets, walk-forward ...", flush=True)
TARGETS = [1.5, 2.0, 2.5, 3.0, 4.0]
for t in TARGETS:
    res = [walk_fixed_target(r, t) for r in J.itertuples(index=False)]
    J[f"pts_{t}"] = [x[0] for x in res]
    J[f"mkt_{t}"] = [x[1] != "target" for x in res]
    J[f"pl_{t}"] = [pts_to_funded(p, m, mk) for p, m, mk in zip(J[f"pts_{t}"], J.micros, J[f"mkt_{t}"])]

months = sorted(J[J.oos].day.str[:7].unique())
wf_pl, wf_pick = [], []
for m in months:
    train = J[J.day.str[:7] < m]
    test = J[J.oos & (J.day.str[:7] == m)]
    if not len(test):
        continue
    pick = max(TARGETS, key=lambda t: funded_series(train, f"pl_{t}")["terminal"])
    wf_pick.append((m, pick))
    wf_pl.append(test[[f"pl_{pick}", "day", "micros", "pl"]].rename(columns={f"pl_{pick}": "pl_wf"}))
WF = pd.concat(wf_pl).reset_index(drop=True)
oos = J[J.oos]
h1_cells = {f"{t:g}R": dict(
    oos_funded=funded_series(oos, f"pl_{t}"),
    is_funded=funded_series(J[~J.oos], f"pl_{t}"),
    oos_drop5=float(oos.drop(oos.nlargest(5, f"pl_{t}").index)[f"pl_{t}"].sum()),
) for t in TARGETS}
canon_oos = funded_series(oos, "pl")
canon_oos_drop5 = float(oos.drop(oos.nlargest(5, "pl").index).pl.sum())
wf_funded = funded_series(WF, "pl_wf")
RES["H1"] = dict(
    label="OOS-legitimate (walk-forward, expanding monthly)",
    picks=wf_pick, cells=h1_cells,
    incumbent_oos=canon_oos, incumbent_oos_drop5=canon_oos_drop5,
    walkforward_oos=wf_funded,
    walkforward_oos_drop5=float(WF.drop(WF.nlargest(5, "pl_wf").index).pl_wf.sum()),
    bust_oos_incumbent=day_block_bootstrap_bust(oos, "pl"),
    bust_oos_walkforward=day_block_bootstrap_bust(WF, "pl_wf"),
)
print("  incumbent OOS", canon_oos["terminal"], " wf OOS", wf_funded["terminal"], flush=True)

# ---------------------------------------------------------------- H2 (IN-SAMPLE, A1)
print("H2 bias gate (IN-SAMPLE) ...", flush=True)
# Bias comes from the COMMITTED artefact output/amt_daytypes.csv (the frozen definition,
# build_daytypes.py). The Phase-1 lane re-derived it from raw bars and matched 912/912 days, so
# reading the artefact IS the committed rule, not a shortcut. balanced -> 0; imbalanced -> +/-1
# by overnight-POC-vs-prior-POC. Knowable at 08:00:00 ET (inputs end at the 07:59 bar).
adt = pd.read_csv(f"{REPO}/output/amt_daytypes.csv")[["day", "type", "direction"]]
adt["bias"] = np.where(adt.type == "balanced", 0, adt.direction)
adt.loc[adt.type == "unknown", "bias"] = np.nan
J = J.drop(columns=["bias"], errors="ignore").merge(
    adt[["day", "bias"]], on="day", how="left")
J["dirn"] = np.where(J.direction == "long", 1, -1)
J["align"] = np.where(J.bias.isna() | (J.bias == 0), "no_bias",
                      np.where(J.bias == J.dirn, "with", "against"))
h2 = {}
for cell, mask in [("no_gate", np.ones(len(J), bool)),
                   ("skip_with_bias", (J["align"] != "with").values),
                   ("skip_against_bias", (J["align"] != "against").values)]:
    s = J[mask]
    h2[cell] = dict(n=int(len(s)), funded=funded_series(s, "pl"),
                    mean_R=float(s.R.mean()), mean_R_ci=dcb_ci(s, "R"),
                    by_half={str(y): dict(n=int(len(s[s.yr == y])), pl=float(s[s.yr == y].pl.sum()),
                                     mean_R=float(s[s.yr == y].R.mean()) if len(s[s.yr == y]) else None)
                             for y in sorted(J.yr.unique())})
h2["alignment_counts"] = J["align"].value_counts().to_dict()
RES["H2"] = dict(label="IN-SAMPLE (A1: selected from Phase-1 on these same 216 trades; "
                       "confirmation requires sessions after 2026-07-10)", cells=h2)
print("  ", h2["alignment_counts"], flush=True)

# ---------------------------------------------------------------- H4 (IN-SAMPLE, A1)
print("H4 MAE cut (IN-SAMPLE) ...", flush=True)
h4 = {}
for th in (0.6, 0.7, 0.8, 0.9):
    pls, ncut, winners_cut = [], 0, 0
    for r in J.itertuples(index=False):
        pts, how = walk_mae_cut(r, th)
        if how == "canon":
            pls.append(r.pl)
        else:
            ncut += 1
            winners_cut += r.pl > 0
            pls.append(pts_to_funded(pts, r.micros, True))
    s = J.assign(pl_cut=pls)
    h4[f"theta_{th:g}"] = dict(
        funded_all=funded_series(s, "pl_cut"), n_cut=int(ncut),
        winners_cut=int(winners_cut),
        drop5=float(s.drop(s.nlargest(5, "pl_cut").index).pl_cut.sum()),
        oos_only=funded_series(s[s.oos.values], "pl_cut"),
    )
# the falsifier stat: deepest CLOSE-based winner heat, each half separately
def close_mae(r):
    d = 1 if r.direction == "long" else -1
    k0 = int(BI.searchsorted(r.ft.floor("min"), side="right")) - 1
    kx = min(k0 + int(r.hold_min), len(BI) - 1)
    adv = [d * (r.entry - BC[k]) for k in range(k0, kx)]
    return max(adv) / r.risk_pts if adv else 0.0
J["cmae"] = [close_mae(r) for r in J.itertuples(index=False)]
win = J[J.pl > 0]
RES["H4"] = dict(
    label="IN-SAMPLE (A1: theta range chosen from the 0.98R global max, which includes the OOS "
          "half — the falsifier is partly pre-answered; confirmation requires fresh sessions)",
    cells=h4,
    winner_close_MAE_max_IS=float(win[~win.oos].cmae.max()),
    winner_close_MAE_max_OOS=float(win[win.oos].cmae.max()),
    incumbent_all=funded_series(J, "pl"),
    incumbent_drop5=float(J.drop(J.nlargest(5, "pl").index).pl.sum()),
)
print("  winner close-MAE max IS/OOS:",
      RES["H4"]["winner_close_MAE_max_IS"], RES["H4"]["winner_close_MAE_max_OOS"], flush=True)

# ---------------------------------------------------------------- H5 contract stratum
print("H5 contract stratum ...", flush=True)
import glob
exposed_days = []
for f in sorted(glob.glob(f"{REPO}/data/reference/depth_2025/*.csv") +
                glob.glob(f"{REPO}/data/reference/depth_2026/*.csv")):
    d0 = pd.read_csv(f, nrows=40)
    day = os.path.basename(f)[9:19]
    ts0 = d0.ts.iloc[0]
    bid = d0[d0.side == "bid"].price.max()
    ask = d0[d0.side == "ask"].price.min()
    mid = (bid + ask) / 2
    t = pd.Timestamp(ts0)
    if t.tzinfo is None:
        t = t.tz_localize("America/New_York")
    k = int(BI.searchsorted(t.tz_convert("UTC"), side="right")) - 1
    if k >= 0 and abs(BC[k] - mid) > 100:
        exposed_days.append(day)
J["exposed"] = J.day.isin(exposed_days)
cl, exp = J[~J.exposed], J[J.exposed]
diff_ms = []
days = J.day.unique()
by = {d: J[J.day == d] for d in days}
for _ in range(4000):
    pick = rng.choice(days, size=len(days), replace=True)
    v = pd.concat([by[d] for d in pick])
    a, bb_ = v[~v.exposed], v[v.exposed]
    if len(a) and len(bb_):
        diff_ms.append(a.R.mean() - bb_.R.mean())
RES["H5"] = dict(
    exposed_days_found=len(exposed_days), n_exposed=int(len(exp)), n_clean=int(len(cl)),
    exposed_pl=float(exp.pl.sum()), clean_pl=float(cl.pl.sum()),
    exposed_share_of_pl=float(exp.pl.sum() / J.pl.sum()),
    mean_R_clean=float(cl.R.mean()), mean_R_exposed=float(exp.R.mean()) if len(exp) else None,
    diff_clean_minus_exposed_ci=[float(np.percentile(diff_ms, 2.5)),
                                 float(np.percentile(diff_ms, 97.5))] if diff_ms else None,
)
print("  exposed:", RES["H5"]["n_exposed"], "pl", RES["H5"]["exposed_pl"], flush=True)

# ---------------------------------------------------------------- H6 standalone viability
print("H6 standalone bootstrap ...", flush=True)
RES["H6"] = dict(
    floor_nohalt=day_block_bootstrap_bust(J.assign(), "pl"),
    floor_halt=None, ddscale_nohalt=None, ddscale_halt=None,
)
# halted variant: apply halt inside the bootstrap (already in ddscale path); redo explicitly
def boot(halt, ddscale):
    days_ = J.day.unique()
    byd = {d: J[J.day == d][["pl", "micros"]].values for d in days_}
    busts = 0
    for _ in range(NBOOT):
        order = rng.choice(days_, size=len(days_), replace=True)
        eq, line = START_EQ, START_EQ - DD_AMT
        dead = False
        for d in order:
            avail = eq - line
            scale = 1.0
            if ddscale and avail > 3000:
                scale = (200 + 75 * np.floor((avail - 3000) / 1000)) / 200.0
            if ddscale and avail < 1500:
                # ADOPTED down-ramp (RULING-daily-loss-limit / commit 3d7a9e2): base scales
                # linearly to ZERO at $100 of available DD. Remove-risk-only: never above 1.0.
                scale = min(scale, max(0.0, (avail - 100.0) / 1400.0))
            if halt and avail <= 100.0:
                continue                       # Tier-1 DD-proximity halt: no trades this day
            day_pl = 0.0
            for pl, m in byd[d]:
                if halt and day_pl <= DAY_HALT * scale:
                    continue
                day_pl += pl * scale
            eq += day_pl
            line = min(max(line, eq - DD_AMT), START_EQ)   # EOD ratchet, LOCKED at the 50k floor
            if eq <= line:
                dead = True
                break
        busts += dead
    return 100.0 * busts / NBOOT
RES["H6"] = {k: boot(h, s) for k, (h, s) in
             dict(floor_nohalt=(False, False), floor_halt=(True, False),
                  ddscale_nohalt=(False, True), ddscale_halt=(True, True)).items()}
print("  ", RES["H6"], flush=True)

# ---------------------------------------------------------------- comparisons + save
RES["comparisons"] = dict(H1=len(TARGETS), H2=3, H4=4, H5=1, H6=4, total=17,
                          note="A5: H3 removed; expected min p under a global null at 17 ~ 0.06")
J[["day", "ft", "direction", "risk_pts", "micros", "pl", "R", "oos", "mfe_R", "cmae",
   "bias", "align", "exposed"]].to_csv(f"{OUT}/phase2_frame.csv", index=False)
json.dump(RES, open(f"{OUT}/phase2_results.json", "w"), indent=1,
          default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(f"\nwrote {OUT}/phase2_results.json")
