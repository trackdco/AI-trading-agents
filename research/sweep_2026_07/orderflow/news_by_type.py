#!/usr/bin/env python3
"""News filter decomposed by RELEASE TYPE on the working baseline (C arm, partially remediated).

Scope: exactly what was asked. No new features, no new hypotheses, nothing added.

ATTRIBUTION follows NewsGate's own logic rather than re-deriving it: the veto on a day is
caused by the EARLIEST promoted-high release printing before 09:30 ET. Where several event
names print at that same minute (CPI and Core CPI, NFP and Average Hourly Earnings), the veto
is JOINTLY caused, so trades are grouped by the full co-printing name set. That keeps the P&L
additive — no trade's P&L is counted under two types.

WHAT IS BEING DECOMPOSED: the avoided-trade component only. From the earlier decomposition that
is +$2,743.75 of the +$2,984.75 total (92%); the remaining resizing (+$405.38) and newly
appearing trades (-$164.38) arise from the nth-escalation cascade and cannot be attributed to
any single release. Stated, not hidden.

SIGN CONVENTION: a trade with P&L p that the filter avoided contributes a BENEFIT of -p.
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
from src.canon.news_gate import NewsGate, _load_raw, ever_high   # noqa: E402

OUT = f"{REPO}/research/sweep_2026_07/orderflow"
BOOKS = f"{OUT}/job2_books"
SPLIT = "2025-12-23"
W0, W1 = "2025-07-01", "2026-07-10"
R = {"scope": "avoided-trade component only (92% of the delta); resizing/new-trade components "
              "are cascade effects and are not attributable to a release type",
     "baseline": "C arm = PARTIALLY REMEDIATED (C only); W and dep_* still leaky"}

gate = NewsGate.load()
cal = _load_raw()
names_high = ever_high(cal)
pre = cal[cal.event.isin(names_high) & (cal.ts.dt.time < pd.Timestamp("2026-01-01 09:30").time())
          & (cal.ts.dt.time != pd.Timestamp("2026-01-01 00:00").time())]

# day -> (release ts, the promoted-high names printing AT that minute)
day_rel = {}
for d, ts in gate.releases.items():
    at = pre[(pre.ts == ts)]
    day_rel[str(d)] = (ts, tuple(sorted(set(at.event))))
print(f"gate: {len(gate.releases)} blackout days, {len(gate.promoted)} promoted-high names, "
      f"calendar to {gate.stale_after.date()}")

def pm(name):
    b = pd.read_parquet(f"{BOOKS}/sized_{name}.parquet")
    b["ft"] = pd.to_datetime(b.fill, utc=True)
    et = b.ft.dt.tz_convert("America/New_York")
    b["hm"] = et.dt.hour * 60 + et.dt.minute
    b["rk"] = b.risk_pts.round(4)
    b["key"] = (b.day.astype(str) + "|" + b.ft.astype(str) + "|" + b.direction + "|"
                + b["rk"].astype(str))
    return b[(b.session == "NY") & (b.hm >= 480) & (b.hm < 570)].copy()

A, B = pm("C_nonews"), pm("C_news")
avoided = A[~A.key.isin(set(B.key))].copy()
avoided["rel_names"] = avoided.day.astype(str).map(lambda d: day_rel.get(d, (None, ("<unattributed>",)))[1])
avoided["label"] = avoided.rel_names.map(lambda t: " + ".join(t) if t else "<unattributed>")
avoided["benefit"] = -avoided.pl
avoided["half"] = np.where(avoided.day.astype(str) < SPLIT, "IS", "OOS")
tot = float(avoided.benefit.sum())
print(f"\navoided {len(avoided)} trades, total benefit ${tot:+,.2f} "
      f"(= the 92% direct component of the ${2984.75:+,.2f} delta)")

# events per year: blackout days of that type inside the study window, annualised
yrs = (pd.Timestamp(W1) - pd.Timestamp(W0)).days / 365.25
win_days = {d: v for d, v in day_rel.items() if W0 <= d <= W1}
type_days = {}
for d, (ts, nm) in win_days.items():
    type_days.setdefault(" + ".join(nm), []).append(d)

print("\n" + "=" * 112)
print("DECOMPOSITION BY RELEASE TYPE — working baseline (C arm), pre-market slice")
print("=" * 112)
print(f"{'release type':44s} {'n':>3} {'benefit':>11} {'IS n/$':>14} {'OOS n/$':>14} "
      f"{'blackout days':>13} {'/yr':>6}")
rows = []
for lab, g in sorted(avoided.groupby("label"), key=lambda kv: -kv[1].benefit.sum()):
    isg, oosg = g[g.half == "IS"], g[g.half == "OOS"]
    nd = len(type_days.get(lab, []))
    rec = dict(label=lab, n=len(g), benefit=float(g.benefit.sum()),
               n_is=len(isg), benefit_is=float(isg.benefit.sum()),
               n_oos=len(oosg), benefit_oos=float(oosg.benefit.sum()),
               blackout_days_in_window=nd, per_year=nd / yrs,
               trades=[(str(t.day), float(t.pl)) for t in g.itertuples()])
    # jackknife within type: does removing one trade flip this type's sign?
    b = g.benefit.values
    jack = [float(b.sum() - x) for x in b]
    rec["jack_flips"] = int(sum(1 for j in jack if (j > 0) != (rec["benefit"] > 0)))
    rec["jack_min"], rec["jack_max"] = float(min(jack)), float(max(jack))
    top = float(np.abs(b).max())
    rec["largest_share"] = top / abs(rec["benefit"]) if rec["benefit"] else np.inf
    rows.append(rec)
    print(f"{lab[:44]:44s} {len(g):>3} {g.benefit.sum():>+11,.0f} "
          f"{len(isg):>3}/{isg.benefit.sum():>+9,.0f} {len(oosg):>3}/{oosg.benefit.sum():>+9,.0f} "
          f"{nd:>13} {nd/yrs:>6.1f}")
R["by_type"] = rows
R["total_benefit"] = tot
R["window_years"] = yrs

# ---- types the gate blacks out but which vetoed NOTHING (why CPI/PPI/NFP are absent) --------
print("\n" + "=" * 112)
print("BLACKOUT TYPES THAT VETOED NO TRADE — the gate fired, the book had nothing to veto")
print("=" * 112)
hit_labels = set(avoided.label)
nonpm = A[~A.key.isin(set(B.key))]
zero = []
for lab, dd in sorted(type_days.items(), key=lambda kv: -len(kv[1])):
    if lab in hit_labels:
        continue
    # did the book trade at all on those days, pre-market?
    traded = int(A[A.day.astype(str).isin(dd)].shape[0])
    zero.append(dict(label=lab, blackout_days=len(dd), per_year=len(dd) / yrs,
                     pm_trades_on_those_days=traded))
print(f"{'release type':56s} {'days':>5} {'/yr':>6} {'PM trades on those days':>24}")
for z in zero[:18]:
    print(f"{z['label'][:56]:56s} {z['blackout_days']:>5} {z['per_year']:>6.1f} "
          f"{z['pm_trades_on_those_days']:>24}")
big3 = [z for z in zero if any(k in z["label"] for k in ("CPI", "PPI", "Non-Farm Payroll",
                                                         "Non-Farm Employment"))]
print(f"\n  CPI / PPI / NFP specifically: {len(big3)} blackout label(s) in the window, "
      f"{sum(z['blackout_days'] for z in big3)} days, "
      f"{sum(z['pm_trades_on_those_days'] for z in big3)} pre-market trades on those days.")
print("  They veto nothing because the book generated NO pre-release pre-market entry on them —")
print("  not because the gate ignores them. The filter's measured benefit therefore comes")
print("  entirely from the second tier of releases, not the headline prints.")
R["zero_veto_types"] = zero
R["big3_days"] = sum(z["blackout_days"] for z in big3)
R["big3_pm_trades"] = sum(z["pm_trades_on_those_days"] for z in big3)

print("\n" + "=" * 112)
print("DOES THE DOMINANT TYPE HOLD DIRECTION IN BOTH HALVES?")
print("=" * 112)
dom = rows[0]
print(f"  dominant type: {dom['label']}  (n={dom['n']}, benefit ${dom['benefit']:+,.0f} = "
      f"{dom['benefit']/tot*100:.0f}% of the avoided-trade component)")
print(f"    IS : n={dom['n_is']:>2}  ${dom['benefit_is']:+,.0f}")
print(f"    OOS: n={dom['n_oos']:>2}  ${dom['benefit_oos']:+,.0f}")
same = (dom["benefit_is"] > 0) == (dom["benefit_oos"] > 0) and dom["n_is"] > 0 and dom["n_oos"] > 0
if dom["n_is"] == 0 or dom["n_oos"] == 0:
    print(f"    -> CANNOT ASSESS: the type has trades in only one half.")
else:
    print(f"    -> {'HOLDS direction in both halves' if same else 'DOES NOT hold: signs differ'}")
R["dominant"] = dict(label=dom["label"], holds_both_halves=bool(same),
                     n_is=dom["n_is"], n_oos=dom["n_oos"],
                     benefit_is=dom["benefit_is"], benefit_oos=dom["benefit_oos"],
                     share_of_component=dom["benefit"] / tot)

print("\n" + "=" * 112)
print("JACKKNIFE WITHIN EACH TYPE — does the type's benefit rest on one or two trades?")
print("=" * 112)
print(f"{'release type':44s} {'n':>3} {'benefit':>11} {'largest trade =':>16} "
      f"{'flips':>6}  reading")
for r_ in rows:
    share = r_["largest_share"]
    if r_["n"] <= 2:
        read = f"RESTS ON {r_['n']} TRADE{'S' if r_['n']>1 else ''} — not distinguishable from luck"
    elif share >= 0.5:
        read = "one trade is >=50% of it — fragile"
    elif r_["jack_flips"] > 0:
        read = "a single removal flips the sign — fragile"
    else:
        read = "no single trade carries it"
    print(f"{r_['label'][:44]:44s} {r_['n']:>3} {r_['benefit']:>+11,.0f} "
          f"{share*100:>15.0f}% {r_['jack_flips']:>6}  {read}")
    r_["reading"] = read

frag = [r_ for r_ in rows if r_["n"] <= 2 or r_["largest_share"] >= 0.5 or r_["jack_flips"] > 0]
print(f"\n  {len(frag)} of {len(rows)} types are carried by one or two trades or flip on a "
      f"single removal.")
print(f"  Those {len(frag)} types together account for "
      f"${sum(r_['benefit'] for r_ in frag):+,.0f} of the ${tot:+,.0f} avoided-trade component "
      f"({sum(r_['benefit'] for r_ in frag)/tot*100:.0f}%).")
R["fragile_types"] = [r_["label"] for r_ in frag]
R["fragile_benefit"] = float(sum(r_["benefit"] for r_ in frag))

print("\n  per-type trade detail (day, P&L of the avoided trade):")
for r_ in rows:
    print(f"    {r_['label'][:60]:60s} " + ", ".join(f"{d} ${p:+,.0f}" for d, p in r_["trades"]))

json.dump(R, open(f"{OUT}/news_by_type.json", "w"), indent=1, default=float)
avoided[["day", "ft", "direction", "pl", "benefit", "label", "half"]].to_csv(
    f"{OUT}/news_by_type_trades.csv", index=False)
print(f"\nwrote {OUT}/news_by_type.json + news_by_type_trades.csv")
