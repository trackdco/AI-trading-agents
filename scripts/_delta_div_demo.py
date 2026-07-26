#!/usr/bin/env python3
"""Delta (CVD) divergence — teaching demo + Task-4 scan over give-back losers.
For each give-back short/long: does CVD diverge at the MFE extreme (selling/buying pressure
peaks BEFORE price makes its extreme = exhaustion), flagging the round-trip top?"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd, numpy as np, glob

NY = "America/New_York"
SC = f"{S}"

# per-minute close/high/low + delta, whole span, NY tz
b = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
b = b.set_index("ts")[["open", "high", "low", "close"]].sort_index()
fp = pd.concat([pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
                for f in glob.glob("data/reference/cvd/footprint_*2026.parquet")])
fp["ts"] = pd.to_datetime(fp.ts_minute, utc=True).dt.tz_convert(NY)
delta = fp.assign(sg=np.where(fp.side == "B", fp.volume, -fp.volume)).groupby("ts").sg.sum()


def day_frame(day):
    lo = pd.Timestamp(f"{day} 07:00", tz=NY); hi = pd.Timestamp(f"{day} 11:30", tz=NY)
    f = b[(b.index >= lo) & (b.index <= hi)].copy()
    f["delta"] = delta.reindex(f.index).fillna(0)
    f["cvd"] = f["delta"].cumsum()
    return f


def analyze(day, entry_ts, direction, stop):
    f = day_frame(day)
    e = pd.Timestamp(entry_ts).tz_convert(NY)
    after = f[f.index >= e]
    # stop-hit time (round-trip end)
    hit = after[(after.high >= stop) if direction == "short" else (after.low <= stop)]
    end = hit.index[0] if len(hit) else after.index[-1]
    run = f[(f.index >= e) & (f.index <= end)]
    if len(run) < 4:
        return None, f
    if direction == "short":
        px_ext_t = run.low.idxmin()                    # price MFE low
        cvd_ext_t = run.cvd.idxmin()                   # selling-pressure trough
        diverge = px_ext_t > cvd_ext_t                 # price bottomed AFTER selling peaked
    else:
        px_ext_t = run.high.idxmax()
        cvd_ext_t = run.cvd.idxmax()
        diverge = px_ext_t > cvd_ext_t
    return dict(day=day, dir=direction, px_ext_t=px_ext_t, cvd_ext_t=cvd_ext_t,
                diverge=diverge, entry=e, end=end, stop=stop), f


# ---- Task-4 scan over give-back losers ----
J = pd.read_csv("output/journal_champion.csv")
gb = J[(J.mfe_r >= 2.5) & (J.points <= 0) & (J.risk_pts >= 2.0)].copy()   # drop tiny-stop artifacts
gb["ets"] = gb.apply(lambda r: pd.Timestamp(f"{r.day} {r.fill}", tz=NY), axis=1)
gb["stop_px"] = gb.entry + np.where(gb.dir == "short", gb.risk_pts, -gb.risk_pts)
rows = []
for _, r in gb.iterrows():
    res, _ = analyze(r.day, r.ets, r.dir, r.stop_px)
    if res:
        rows.append({**res, "mfe_r": r.mfe_r})
R = pd.DataFrame(rows)
n_div = R.diverge.sum()
print(f"TASK-4 SCAN: give-back losers (MFE>=2.5R, real stop): {len(R)}")
print(f"  CVD divergence at the MFE extreme (pressure peaked BEFORE price): {n_div}/{len(R)} "
      f"({n_div/len(R)*100:.0f}%)")
print("  (i.e. on that many, a divergence exit would have flagged the top before the round-trip)")
for _, r in R.iterrows():
    lead = (pd.Timestamp(r.px_ext_t) - pd.Timestamp(r.cvd_ext_t)).total_seconds() / 60
    print(f"  {r.day} {r.dir:5s} MFE {r.mfe_r:5.1f}R  diverge={bool(r.diverge)!s:5s}  "
          f"(price extreme {lead:+.0f} min after CVD extreme)")

# ---- chart the clearest diverging example ----
cand = R[R.diverge].copy()
cand["lead"] = (pd.to_datetime(cand.px_ext_t) - pd.to_datetime(cand.cvd_ext_t)).dt.total_seconds() / 60
pick = cand.sort_values("lead", ascending=False).iloc[0]
res, f = analyze(pick.day, pick.entry, pick["dir"], pick.stop)
win = f[(f.index >= res["entry"] - pd.Timedelta(minutes=10)) &
        (f.index <= res["end"] + pd.Timedelta(minutes=5))]
x = win.index.tz_localize(None)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[2, 1], sharex=True)
fig.patch.set_facecolor("#0f1419")
for a in (a1, a2):
    a.set_facecolor("#0f1419"); a.tick_params(colors="#9aa5b1"); a.grid(alpha=.12)
    for s in a.spines.values(): s.set_color("#2a2f36")
a1.plot(x, win.close, color="#4c9aff", lw=1.3)
a1.axhline(res["entry"] and pick.entry and f.loc[res["entry"], "close"], color="#e5b567", ls="--", lw=1)
a1.axhline(pick.stop, color="#f2555a", ls="--", lw=1, label=f"stop {pick.stop:.0f}")
pe = pd.Timestamp(res["px_ext_t"]).tz_localize(None); ce = pd.Timestamp(res["cvd_ext_t"]).tz_localize(None)
a1.axvline(pe, color="#6dd66a", lw=1, ls=":"); a1.axvline(ce, color="#c586c0", lw=1, ls=":")
a1.set_ylabel("price", color="#e5e9f0")
a1.set_title(f"Delta/CVD divergence — {pick.day} {pick['dir']} give-back (MFE {pick.mfe_r:.1f}R)\n"
             "green=price extreme, purple=CVD extreme: CVD turned FIRST = exhaustion (exit signal)",
             color="#e5e9f0", fontsize=11, loc="left")
a2.plot(x, win.cvd, color="#c586c0", lw=1.4, label="CVD")
a2.axvline(pe, color="#6dd66a", lw=1, ls=":"); a2.axvline(ce, color="#c586c0", lw=1, ls=":")
a2.set_ylabel("CVD", color="#e5e9f0"); a2.set_xlabel("time (ET)", color="#e5e9f0")
plt.tight_layout(); plt.savefig(f"{SC}/delta_divergence_demo.png", dpi=130, facecolor=fig.get_facecolor())
print(f"\ncharted: {pick.day} {pick['dir']} — CVD extreme {(pd.Timestamp(res['px_ext_t'])-pd.Timestamp(res['cvd_ext_t'])).total_seconds()/60:+.0f} min before price extreme")
print("saved", f"{SC}/delta_divergence_demo.png")
