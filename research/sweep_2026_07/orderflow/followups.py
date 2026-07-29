#!/usr/bin/env python3
"""Brake's four follow-ups on the Parts 0-3 study (2026-07-29).

1. Part 3 arm relationship measured, not asserted: the two arms share most of their trades and
   avoid the same days, so the second arm is a SENSITIVITY CHECK, not an independent
   replication. The leaky arm's CI spans zero and that is stated.
2. Decomposition of the news-filter delta into (a) avoided-trade P&L, (b) resizing of surviving
   trades through the nth-escalation / governor / day-ladder cascade, (c) trades that newly
   appear in freed nth slots. The three must sum to the delta exactly.
3. Funded risk with and without the filter: bust probability (day-block bootstrap), max
   drawdown, and daily-loss-limit breach days. Engine constants are the committed ones from
   phase2/run_phase2.py, including BOTH Tier-1 rules and the DD-scaling down-ramp.
4. Part 2's resume rate restricted to bars at or before the canon's actual exit. A resume after
   the canon has closed the trade is not tradeable. The exit timestamp is destroyed, so the
   FIRST BAR CONTAINING the recorded exit price is used: that is a LOWER BOUND on the true exit
   bar, so the restricted resume rate is CONSERVATIVE (biased low). Both numbers reported.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"
BOOKS = f"{OUT}/job2_books"
START_EQ, DD_AMT, DAY_HALT, NBOOT = 50_000.0, 2_000.0, -800.0, 5_000
rng = np.random.default_rng(20260729)
R = {}

def pm(name):
    b = pd.read_parquet(f"{BOOKS}/sized_{name}.parquet")
    b["ft"] = pd.to_datetime(b.fill, utc=True)
    et = b.ft.dt.tz_convert("America/New_York")
    b["hm"] = et.dt.hour * 60 + et.dt.minute
    b["rk"] = b.risk_pts.round(4)
    b["key"] = (b.day.astype(str) + "|" + b.ft.astype(str) + "|" + b.direction + "|"
                + b["rk"].astype(str))
    return b

def pmslice(b):
    return b[(b.session == "NY") & (b.hm >= 480) & (b.hm < 570)].copy()

BK = {n: pm(n) for n in ("L_nonews", "L_news", "C_nonews", "C_news")}
PMB = {n: pmslice(b) for n, b in BK.items()}

# ================================================================ 1. arms are not independent
print("=" * 100)
print("1. THE TWO ARMS ARE NOT INDEPENDENT — sensitivity check, not replication")
print("=" * 100)
kl, kc = set(PMB["L_news"].key), set(PMB["C_news"].key)
share = len(kl & kc)
lo_n, cn_n = len(PMB["L_nonews"]), len(PMB["C_nonews"])
kln, kcn = set(PMB["L_nonews"].key), set(PMB["C_nonews"].key)
av_L = PMB["L_nonews"][~PMB["L_nonews"].key.isin(kl)]
av_C = PMB["C_nonews"][~PMB["C_nonews"].key.isin(kc)]
dl, dc = set(av_L.day), set(av_C.day)
print(f"  news-filtered arms: L {len(kl)} trades, C {len(kc)} trades, shared {share} "
      f"({share/max(len(kl),len(kc))*100:.0f}% of the larger arm)")
print(f"  no-news arms:       L {lo_n}, C {cn_n}, shared {len(kln & kcn)} "
      f"({len(kln & kcn)/max(lo_n,cn_n)*100:.0f}%)")
print(f"  avoided DAYS: L {len(dl)}, C {len(dc)}, shared {len(dl & dc)} "
      f"({len(dl & dc)/max(len(dl),len(dc))*100:.0f}%)  -> the arms veto the same calendar")
big_L = av_L.reindex(av_L.pl.abs().sort_values(ascending=False).index).iloc[0]
big_C = av_C.reindex(av_C.pl.abs().sort_values(ascending=False).index).iloc[0]
same_big = (big_L.day == big_C.day)
print(f"  largest avoided trade: L {big_L.day} ${big_L.pl:+,.0f} | C {big_C.day} "
      f"${big_C.pl:+,.0f}  -> {'THE SAME TRADE' if same_big else 'different'}")
print(f"  CONCLUSION: the C arm is the L arm with one check re-sourced; they share most trades")
print(f"  and veto the same calendar. The second arm is a SENSITIVITY CHECK on the C-remediation,")
print(f"  NOT independent evidence. The leaky arm's 95% CI [-$294, +$3,925] SPANS ZERO —")
print(f"  on its own it does not establish an effect.")
R["arms"] = dict(shared_news=share, n_L_news=len(kl), n_C_news=len(kc),
                 shared_pct=share / max(len(kl), len(kc)),
                 avoided_days_L=len(dl), avoided_days_C=len(dc), avoided_days_shared=len(dl & dc),
                 same_largest_avoided=bool(same_big),
                 framing="sensitivity check, NOT independent replication")

# ================================================================ 2. decomposition
print("\n" + "=" * 100)
print("2. DECOMPOSITION OF THE NEWS-FILTER DELTA")
print("=" * 100)
dec = {}
for arm in ("C", "L"):
    A, B = PMB[f"{arm}_nonews"], PMB[f"{arm}_news"]
    ka, kb = set(A.key), set(B.key)
    avoided = A[~A.key.isin(kb)]
    added = B[~B.key.isin(ka)]
    sa = A[A.key.isin(kb)].set_index("key").pl
    sb = B[B.key.isin(ka)].set_index("key").pl
    common = sa.index.intersection(sb.index)
    resize = float(sb.loc[common].sum() - sa.loc[common].sum())
    direct = float(-avoided.pl.sum())
    add = float(added.pl.sum())
    delta = float(B.pl.sum() - A.pl.sum())
    n_resized = int((sb.loc[common].round(2) != sa.loc[common].round(2)).sum())
    print(f"\n  --- {arm} arm --- total delta ${delta:+,.2f}")
    print(f"    (a) avoided-trade P&L removed : ${direct:+,.2f}   "
          f"({len(avoided)} trades, they summed ${avoided.pl.sum():+,.2f})")
    print(f"    (b) RESIZING of surviving trades: ${resize:+,.2f}   "
          f"({n_resized} of {len(common)} shared trades change P&L via the nth-escalation /")
    print(f"        governor / day-ladder cascade)")
    print(f"    (c) trades newly appearing      : ${add:+,.2f}   ({len(added)} trades in freed "
          f"nth slots)")
    chk = direct + resize + add
    print(f"    sum check: {direct:+,.2f} {resize:+,.2f} {add:+,.2f} = ${chk:+,.2f} "
          f"vs delta ${delta:+,.2f}  {'OK' if abs(chk-delta) < 0.01 else 'MISMATCH'}")
    print(f"    -> {direct/delta*100:.0f}% of the benefit is avoided trades, "
          f"{resize/delta*100:.0f}% is resizing, {add/delta*100:.0f}% is new trades")
    dec[arm] = dict(delta=delta, avoided_pl_removed=direct, resize=resize, added=add,
                    n_avoided=len(avoided), n_resized=n_resized, n_shared=len(common),
                    n_added=len(added), check_ok=bool(abs(chk - delta) < 0.01),
                    pct_avoided=direct / delta, pct_resize=resize / delta, pct_added=add / delta)
R["decomposition"] = dec

# ================================================================ 3. funded risk
print("\n" + "=" * 100)
print("3. FUNDED RISK WITH AND WITHOUT THE FILTER (full sized book: NY + London, windowed)")
print("=" * 100)
print("  engine = committed constants: $50k start, $2,000 EOD-trailing DD LOCKED at the $50k")
print("  floor, Tier-1 daily-loss halt at -$800 PLUS the $100 DD-proximity halt.")

def funded(df):
    """Realised path. Returns bust, min available DD, max drawdown, breach days."""
    df = df.sort_values("fill")
    eq, line, cur, daypl = START_EQ, START_EQ - DD_AMT, None, 0.0
    busted, minav, breaches = False, 1e9, 0
    peak, mdd, dayeq = START_EQ, 0.0, []
    for day_, pl in zip(df.day.values, df.pl.values):
        if day_ != cur:
            if cur is not None:
                line = min(max(line, eq - DD_AMT), START_EQ)
                if daypl <= DAY_HALT:
                    breaches += 1
                dayeq.append(eq)
            cur, daypl = day_, 0.0
        avail = eq - line
        if daypl <= DAY_HALT or avail <= 100.0:      # Tier-1: both rules
            continue
        eq += pl
        daypl += pl
        minav = min(minav, eq - line)
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
        if eq <= line:
            busted = True
    if daypl <= DAY_HALT:
        breaches += 1
    return dict(final_eq=eq, pl=eq - START_EQ, busted=busted, min_available=minav,
                max_dd=mdd, breach_days=breaches, n_days=len(set(df.day)))

def bust_prob(df, ddscale=False):
    days = df.day.unique()
    by = {d: df[df.day == d].pl.values for d in days}
    busts = 0
    for _ in range(NBOOT):
        order = rng.choice(days, size=len(days), replace=True)
        eq, line, dead = START_EQ, START_EQ - DD_AMT, False
        for d in order:
            avail = eq - line
            scale = 1.0
            if ddscale:
                if avail > 3000:
                    scale = (200 + 75 * np.floor((avail - 3000) / 1000)) / 200.0
                if avail < 1500:
                    scale = min(scale, max(0.0, (avail - 100.0) / 1400.0))
                if avail <= 100.0:
                    continue
            daypl = 0.0
            for pl in by[d]:
                if daypl <= DAY_HALT * scale:
                    continue
                daypl += pl * scale
            eq += daypl
            line = min(max(line, eq - DD_AMT), START_EQ)
            if eq <= line:
                dead = True
                break
        busts += dead
    return 100.0 * busts / NBOOT

frisk = {}
print(f"\n  {'book':22s} {'final P&L':>12} {'bust%':>7} {'bust% (spine)':>14} {'maxDD':>10} "
      f"{'min avail DD':>13} {'breach days':>12}")
for arm in ("C", "L"):
    for tag in ("nonews", "news"):
        b = BK[f"{arm}_{tag}"]
        f = funded(b)
        bp = bust_prob(b, ddscale=False)
        bps = bust_prob(b, ddscale=True)
        lab = f"{arm} {'no filter' if tag=='nonews' else 'WITH filter'}"
        frisk[f"{arm}_{tag}"] = dict(**f, bust_naked=bp, bust_spine=bps)
        print(f"  {lab:22s} ${f['pl']:>+11,.0f} {bp:>6.2f}% {bps:>13.2f}% "
              f"${f['max_dd']:>9,.0f} ${f['min_available']:>12,.0f} {f['breach_days']:>12}")
R["funded_risk"] = frisk
for arm in ("C", "L"):
    a, b = frisk[f"{arm}_nonews"], frisk[f"{arm}_news"]
    print(f"\n  {arm} arm effect of the filter: bust {a['bust_naked']:.2f}% -> "
          f"{b['bust_naked']:.2f}% naked, {a['bust_spine']:.2f}% -> {b['bust_spine']:.2f}% with "
          f"the full spine; maxDD ${a['max_dd']:,.0f} -> ${b['max_dd']:,.0f}; "
          f"breach days {a['breach_days']} -> {b['breach_days']}")

# ================================================================ 4. tradeable resume rate
print("\n" + "=" * 100)
print("4. PART 2 RESUME RATE RESTRICTED TO BARS AT/BEFORE THE CANON'S ACTUAL EXIT")
print("=" * 100)
F = pd.read_csv(f"{OUT}/part0_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL = bars.index, bars.high.values, bars.low.values

PEAK_MIN, RETRACE_TRIG = 1.0, 0.5
rows = []
for r in F.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    k0, kx = int(r.k0), int(r.k0) + int(r.life_min)
    if kx <= k0:
        continue
    # LOWER BOUND on the canon exit bar: first bar containing the recorded exit price.
    seg = slice(k0, kx + 1)
    cont = (BH[seg] >= r.exit_price - 1e-9) & (BL[seg] <= r.exit_price + 1e-9)
    hit = np.nonzero(cont)[0]
    k_exit = k0 + int(hit[0]) if len(hit) else kx
    is_stop = abs(r.exit_price - r.stop) < 0.26
    peak, fired = -np.inf, False
    for k in range(k0, kx + 1):
        hiR = ((BH[k] - r.entry) if d > 0 else (r.entry - BL[k])) / r.risk_pts
        loR = ((BL[k] - r.entry) if d > 0 else (r.entry - BH[k])) / r.risk_pts
        if not fired and peak >= PEAK_MIN and (peak - loR) >= RETRACE_TRIG:
            fut = [((BH[j] - r.entry) if d > 0 else (r.entry - BL[j])) / r.risk_pts
                   for j in range(k + 1, kx + 1)]
            fut_tr = [((BH[j] - r.entry) if d > 0 else (r.entry - BL[j])) / r.risk_pts
                      for j in range(k + 1, min(k_exit, kx) + 1)]
            rows.append(dict(ft=str(r.ft), oos=bool(r.oos), bar=k - k0,
                             event_before_exit=bool(k <= k_exit), is_stop_exit=bool(is_stop),
                             resume_life=bool(len(fut) and max(fut) > peak + 1e-9),
                             resume_tradeable=bool(len(fut_tr) and max(fut_tr) > peak + 1e-9)))
            fired = True
        peak = max(peak, hiR)
E = pd.DataFrame(rows)
n = len(E)
be = E[E.event_before_exit]
print(f"  events (first retrace per trade): {n}")
print(f"  exit_price == stop (exit bar EXACT, no bound needed): "
      f"{int(E.is_stop_exit.sum())}/{n} ({E.is_stop_exit.mean()*100:.0f}%)")
print(f"  events occurring at/before the canon exit bound: {len(be)}/{n} "
      f"({len(be)/n*100:.0f}%) — the rest fire after the canon had already closed the trade")
print(f"\n  RESUME RATE over full trade life          : {E.resume_life.mean()*100:.1f}%  "
      f"({int(E.resume_life.sum())}/{n})")
print(f"  RESUME RATE tradeable (<= canon exit bound): {E.resume_tradeable.mean()*100:.1f}%  "
      f"({int(E.resume_tradeable.sum())}/{n})")
if len(be):
    print(f"  RESUME RATE tradeable, events before exit : "
          f"{be.resume_tradeable.mean()*100:.1f}%  ({int(be.resume_tradeable.sum())}/{len(be)})")
print(f"\n  BOUND DIRECTION: first-touch of the exit price is a LOWER bound on the true exit bar,")
print(f"  so the tradeable rate is CONSERVATIVE (biased low). For the "
      f"{E.is_stop_exit.mean()*100:.0f}% of trades exiting at the stop it is exact.")
R["resume"] = dict(n_events=n, resume_life=float(E.resume_life.mean()),
                   resume_tradeable=float(E.resume_tradeable.mean()),
                   n_resume_life=int(E.resume_life.sum()),
                   n_resume_tradeable=int(E.resume_tradeable.sum()),
                   events_before_exit=len(be),
                   resume_tradeable_before_exit=float(be.resume_tradeable.mean()) if len(be) else None,
                   exact_stop_exits=float(E.is_stop_exit.mean()),
                   bound="first-touch of exit price = LOWER bound on true exit -> conservative")
E.to_csv(f"{OUT}/followup_resume.csv", index=False)
json.dump(R, open(f"{OUT}/followups.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/followups.json + followup_resume.csv")
