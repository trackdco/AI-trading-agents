#!/usr/bin/env python3
"""JOB 1 (Brake, 2026-07-28): give-back and hold-through-open DESCRIPTIVES, IS half ONLY.
The OOS half is never loaded into any statistic. No scoring, no thresholds, no proposals.

Conventions (stated before results, matching the certified Phase-2 walk):
- Bar path per trade: k0 = fill bar (floored stamp, inclusive) .. kx = k0 + hold_min (the
  canon exit bar, inclusive), on data/reference/nq_1m_master.parquet. Max favorable over
  [k0,kx] is asserted equal to the frame's certified mfe_R for every IS trade.
- +1R touch bar: first bar in [k0,kx] whose favorable extreme reaches +1.0R.
- Post-touch give-back: the touch bar contributes ONLY its favorable extreme to the running
  peak (its low may precede the touch intra-bar — unknowable); adverse extremes count from
  bars strictly after the touch bar, through the exit bar INCLUSIVE (the frame's inclusive
  fill->exit convention). dd_R = max(running peak R - subsequent low R); floor_R = min low R
  after the touch (relative to entry, so 0 = breakeven, negative = below entry).
- Breakeven-stop counterfactual: BE stop at entry, frictionless, active from the bar AFTER
  the +1R touch bar. BE fires if a bar's adverse extreme touches entry before the canon exit
  bar; touch on the exit bar itself is counted separately as AMBIGUOUS (canon exit and BE
  trigger in the same bar, intra-bar order unknowable); a same-bar entry-touch on the touch
  bar itself is also counted (ambiguity bound, not a firing).
- Exit-vs-open: exit bar START time vs 09:30 ET (exit bar stamped 09:30 covers [09:30,09:31)
  and counts as AFTER the open).
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")

F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["rk"] = F.risk_pts.round(4)
cb = pd.read_parquet(f"{REPO}/output/canon_book.parquet")
cb["ft"] = pd.to_datetime(cb.fill, utc=True)
cb["rk"] = cb["risk"].round(4)
im = pd.read_parquet(f"{REPO}/output/intrade_matrix.parquet")
im["ft"] = pd.to_datetime(im.fill, utc=True)
im["rk"] = im["risk"].round(4)
J = F.merge(cb.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "entry"]],
            on=["ft", "direction", "rk"], how="left") \
     .merge(im.drop_duplicates(["ft", "direction", "rk"])[["ft", "direction", "rk", "hold_min"]],
            on=["ft", "direction", "rk"], how="left")
assert len(J) == 216 and J.entry.notna().all() and J.hold_min.notna().all()

IS = J[~J.oos].reset_index(drop=True)          # IS HALF ONLY from here on
assert not IS.oos.any()
print(f"IS half: {len(IS)} trades, {IS.day.min()} -> {IS.day.max()}  (OOS never touched)")

bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL = bars.index, bars.high.values, bars.low.values

rows = []
for r in IS.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    e, risk = float(r.entry), float(r.risk_pts)
    t0 = r.ft.floor("min")
    k0 = int(BI.searchsorted(t0, side="right")) - 1
    kx = min(k0 + int(r.hold_min), len(BI) - 1)
    hiR = (d * (BH[k0:kx + 1] - e) if d > 0 else d * (BL[k0:kx + 1] - e)) / risk  # fav extreme
    loR = (d * (BL[k0:kx + 1] - e) if d > 0 else d * (BH[k0:kx + 1] - e)) / risk  # adv extreme
    assert abs(hiR.max() - r.mfe_R) < 1e-9, (r.day, hiR.max(), r.mfe_R)
    touch = np.argmax(hiR >= 1.0) if (hiR >= 1.0).any() else -1
    et = r.ft.tz_convert("America/New_York")
    open_et = et.replace(hour=9, minute=30, second=0)
    exit_ts = BI[kx].tz_convert("America/New_York")
    rec = dict(day=r.day, ft=str(r.ft), direction=r.direction, risk_pts=risk,
               R=float(r.R), pl=float(r.pl), mfe_R=float(r.mfe_R),
               min_to_open=float((open_et - et).total_seconds() / 60.0),
               exit_et=str(exit_ts), exit_after_open=bool(exit_ts >= open_et),
               hold_min=int(r.hold_min),
               touched_1R=bool(touch >= 0))
    if touch >= 0:
        after = slice(touch + 1, kx + 1)
        if touch == kx - k0:                       # exited on the touch bar
            rec.update(exited_on_touch_bar=True, dd_R=0.0, floor_R=np.nan,
                       be_hit="exited_on_touch_bar", samebar_entry_touch=bool(loR[touch] <= 0))
        else:
            peaks = np.maximum.accumulate(np.concatenate([[hiR[touch]], hiR[after]]))[1:]
            dd = float((peaks - loR[after]).max())
            rec.update(exited_on_touch_bar=False, dd_R=dd,
                       floor_R=float(loR[after].min()),
                       samebar_entry_touch=bool(loR[touch] <= 0))
            hit = np.nonzero(loR[after] <= 0.0)[0]
            if len(hit) == 0:
                rec["be_hit"] = "never"
            elif hit[0] + touch + 1 == kx - k0:
                rec["be_hit"] = "exit_bar_ambiguous"
            else:
                rec["be_hit"] = "pre_exit"
    rows.append(rec)
P = pd.DataFrame(rows)
P.to_csv(f"{OUT}/job1_per_trade_is.csv", index=False)
REPORT = {"n_is": len(P)}

# ---------------------------------------------------------------- 1. give-back distributions
print("\n" + "=" * 92)
print("1. GIVE-BACK AFTER FIRST +1R TOUCH — IS half, cumulative mfe groups (groups NEST)")
print("   dd_R = worst peak-to-trough after the touch; floor_R = lowest R level after the touch")
print("=" * 92)
def dist(v):
    v = np.sort(np.asarray(v, float))
    q = np.percentile(v, [0, 25, 50, 75, 100]) if len(v) else [np.nan] * 5
    return q, v
g1 = {}
for thr in (2.0, 3.0, 4.0):
    g = P[(P.mfe_R >= thr) & P.touched_1R & (~P.exited_on_touch_bar.fillna(False))]
    got = P[(P.mfe_R >= thr) & P.touched_1R]
    (mn, q25, md, q75, mx), vals = dist(g.dd_R)
    (fn, f25, fm, f75, fx), fvals = dist(g.floor_R.dropna())
    print(f"\n  reached >= {thr:.0f}R: n={len(got)} (of which {len(got)-len(g)} exited on the "
          f"touch bar itself -> no post-touch path)")
    print(f"    dd_R    min {mn:+.3f}  q25 {q25:+.3f}  med {md:+.3f}  q75 {q75:+.3f}  max {mx:+.3f}"
          f"   mean {g.dd_R.mean():+.3f}")
    print(f"    floor_R min {fn:+.3f}  q25 {f25:+.3f}  med {fm:+.3f}  q75 {f75:+.3f}  max {fx:+.3f}"
          f"   mean {g.floor_R.mean():+.3f}")
    print(f"    dd_R sorted:    " + "  ".join(f"{x:+.2f}" for x in vals))
    print(f"    floor_R sorted: " + "  ".join(f"{x:+.2f}" for x in fvals))
    g1[f"mfe_ge_{thr:.0f}"] = dict(n=int(len(got)), exited_on_touch=int(len(got) - len(g)),
                                   dd_sorted=[round(float(x), 4) for x in vals],
                                   floor_sorted=[round(float(x), 4) for x in fvals])
REPORT["giveback"] = g1

# ---------------------------------------------------------------- 2. breakeven-at-+1R counterfactual
print("\n" + "=" * 92)
print("2. BREAKEVEN STOP MOVED AT +1R — frictionless, active from the bar AFTER the touch bar")
print("=" * 92)
T1 = P[P.touched_1R]
print(f"  IS trades touching +1R: {len(T1)}/{len(P)}")
print(f"  be_hit: " + "  ".join(f"{k}={int(v)}" for k, v in T1.be_hit.value_counts().items()))
print(f"  same-bar entry-touch on the touch bar itself (ambiguity bound, not a firing): "
      f"{int(T1.samebar_entry_touch.sum())}")
bands = [(-np.inf, 0, "loss (<0R)"), (0, 1, "[0,1)R"), (1, 2, "[1,2)R"),
         (2, 3, "[2,3)R"), (3, 4, "[3,4)R"), (4, np.inf, ">=4R")]
print(f"\n  {'actual final R band':16s} {'n':>3} {'BE pre_exit':>11} {'exit-bar amb':>12} "
      f"{'never':>6} {'on-touch-exit':>13}   sum pl of BE-stopped")
tab = {}
for lo, hi, lab in bands:
    s = T1[(T1.R >= lo) & (T1.R < hi)]
    be = s[s.be_hit == "pre_exit"]
    tab[lab] = dict(n=int(len(s)), pre_exit=int(len(be)),
                    exit_bar=int((s.be_hit == "exit_bar_ambiguous").sum()),
                    never=int((s.be_hit == "never").sum()),
                    on_touch=int((s.be_hit == "exited_on_touch_bar").sum()),
                    pl_of_stopped=float(be.pl.sum()))
    t = tab[lab]
    print(f"  {lab:16s} {t['n']:>3} {t['pre_exit']:>11} {t['exit_bar']:>12} {t['never']:>6} "
          f"{t['on_touch']:>13}   ${t['pl_of_stopped']:+,.0f}")
print(f"\n  {'mfe group (nested)':16s} {'n':>3} {'BE pre_exit':>11} {'exit-bar amb':>12} {'never':>6}")
for thr in (1.0, 2.0, 3.0, 4.0):
    s = T1[T1.mfe_R >= thr]
    print(f"  mfe >= {thr:.0f}R        {len(s):>3} {int((s.be_hit=='pre_exit').sum()):>11} "
          f"{int((s.be_hit=='exit_bar_ambiguous').sum()):>12} {int((s.be_hit=='never').sum()):>6}")
be = T1[T1.be_hit == "pre_exit"]
print(f"\n  BE-stopped (pre_exit) trades: n={len(be)}, their ACTUAL outcomes: "
      f"mean R {be.R.mean():+.3f}, sum pl ${be.pl.sum():+,.0f} "
      f"(what a frictionless BE stop would have flattened to 0)")
print(f"  not-stopped (never): n={int((T1.be_hit=='never').sum())}, mean R "
      f"{T1[T1.be_hit=='never'].R.mean():+.3f}")
REPORT["breakeven"] = dict(touched=int(len(T1)), by_R_band=tab,
                           stopped_actual_meanR=float(be.R.mean()),
                           stopped_actual_pl=float(be.pl.sum()))

# ---------------------------------------------------------------- 3. time-to-open / exit side
print("\n" + "=" * 92)
print("3. TIME-TO-09:30 AT FILL x EXIT SIDE — IS half (exit bar start vs 09:30 ET)")
print("=" * 92)
mo = P.min_to_open
print(f"  minutes-to-open at fill: min {mo.min():.0f}  q25 {mo.quantile(.25):.0f}  "
      f"med {mo.median():.0f}  q75 {mo.quantile(.75):.0f}  max {mo.max():.0f}")
print(f"  exits after 09:30 ET: {int(P.exit_after_open.sum())}/{len(P)}")

def outrow(s):
    return dict(n=int(len(s)), wr=float((s.R > 0).mean()) if len(s) else np.nan,
                meanR=float(s.R.mean()) if len(s) else np.nan,
                sumR=float(s.R.sum()), pl=float(s.pl.sum()))

print(f"\n  {'group':34s} {'n':>4} {'WR':>6} {'meanR':>7} {'sumR':>8} {'sum pl':>12}")
t3 = {}
for lab, s in (("exit BEFORE open", P[~P.exit_after_open]), ("exit AFTER open", P[P.exit_after_open])):
    t3[lab] = outrow(s)
    r = t3[lab]
    print(f"  {lab:34s} {r['n']:>4} {r['wr']*100:>5.1f}% {r['meanR']:>+7.3f} {r['sumR']:>+8.2f} "
          f"${r['pl']:>+11,.0f}")
FB = [(480, 510, "fill 08:00-08:29"), (510, 540, "fill 08:30-08:59"), (540, 570, "fill 09:00-09:29")]
P["hm"] = 570 - P.min_to_open
for lo, hi, lab in FB:
    s = P[(P.hm >= lo) & (P.hm < hi)]
    t3[lab] = outrow(s)
    r = t3[lab]
    print(f"  {lab:34s} {r['n']:>4} {r['wr']*100:>5.1f}% {r['meanR']:>+7.3f} {r['sumR']:>+8.2f} "
          f"${r['pl']:>+11,.0f}")
    for elab, ss in ((" .. exit before open", s[~s.exit_after_open]),
                     (" .. exit after open", s[s.exit_after_open])):
        rr = outrow(ss)
        t3[lab + elab] = rr
        if rr["n"]:
            print(f"  {lab + elab:34s} {rr['n']:>4} {rr['wr']*100:>5.1f}% {rr['meanR']:>+7.3f} "
                  f"{rr['sumR']:>+8.2f} ${rr['pl']:>+11,.0f}")
        else:
            print(f"  {lab + elab:34s} {rr['n']:>4}")
REPORT["open_split"] = t3

json.dump(REPORT, open(f"{OUT}/job1_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/job1_per_trade_is.csv + job1_report.json")
print("DESCRIPTIVES ONLY — nothing scored, no thresholds proposed. OOS untouched.")
