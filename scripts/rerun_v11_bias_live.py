#!/usr/bin/env python3
"""TRUE RE-BACKTEST: Champion v1.1 with the new HTF bias engine as a LIVE gate on trigger
flow (not a post-hoc trade filter). A trigger only reaches its book if the bias in force at
the trigger's print time allows it — so gated-out setups free their 2/day slots and later
setups can fill them, exactly as it would trade live.

Arms (both against the fresh-engine ungated base = 100t / +$16,518, same pinned code):
  DIRECTIONAL: trigger passes if bias is BULLISH or BEARISH (any read; NEUTRAL blocks).
  ALIGNED:     trigger passes only if its direction matches the bias side.

Bias source: htf_bias.py v2 timelines (08:00 INITIAL -> event updates -> 09:30 checkpoint),
built for every trading day Feb 2 - Jul 15. Triggers stamped before 08:00 are judged by the
08:00 premarket read (their fills occur inside the 08:00-10:15 window). Engine/config/
triggers pinned to pass-29 (Feb-May) + current Jun/Jul triggers, identical to the verified
base re-run. v1.1 cuts applied after simulation, as frozen.
"""
import ast
import os
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

SCRATCH = Path(f"{S}")
ROOT = SCRATCH / "gs29"
import importlib.util
_spec = importlib.util.spec_from_file_location("htf_bias", "/home/user/AI-trading-agents/htf_bias.py")
HB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HB)  # loaded by file path: the brake repo NEVER enters sys.path,
                              # so src.backtest.engine can only resolve to the pinned gs29 tree

os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]


# ------------------------------------------------------------------ bias timelines

def build_timelines(bars, news, days):
    tls = {}
    for i, D in enumerate(days):
        sl = bars[(bars.ts >= D - pd.Timedelta(days=60)) & (bars.ts < D + pd.Timedelta(days=1))].reset_index(drop=True)
        T0 = pd.Timestamp.combine(D.date(), dtime(8, 0)).tz_localize(NY)
        _, st = HB.read_at(sl, news, D, T0, "INITIAL premarket")
        if st is None:
            tls[str(D.date())] = [("08:00", "NEUTRAL")]
            continue
        tl = [("08:00", st["bias"])]
        fired = set()
        t = T0 + pd.Timedelta(minutes=15)
        end = pd.Timestamp.combine(D.date(), HB.WIN_END).tz_localize(NY)
        while t <= end:
            candle = sl[(sl.ts >= t - pd.Timedelta(minutes=15)) & (sl.ts < t)]
            if t.time() == dtime(9, 30):
                _, ns = HB.read_at(sl, news, D, t, "UPDATE @ 09:30", prev_bias=st["bias"], trigger="0930")
                st = ns; fired = set(); tl.append(("09:30", st["bias"]))
            elif len(candle):
                hi = float(candle.high.max()); lo = float(candle.low.min()); cl = float(candle.close.iloc[-1])
                reasons = []
                d = st["direction"]
                if d in ("bullish", "bearish"):
                    ip = st["inval_px"]
                    if ip is not None and "inval" not in fired and ((d == "bullish" and cl < ip) or (d == "bearish" and cl > ip)):
                        reasons.append("inval"); fired.add("inval")
                    dp = st["draw_px"]
                    if dp is not None and "draw" not in fired and ((d == "bullish" and hi >= dp) or (d == "bearish" and lo <= dp)):
                        reasons.append("draw"); fired.add("draw")
                    if "cisd" not in fired:
                        f15 = HB.frames_asof(sl, t, D)["15m"]
                        against = "bearish" if d == "bullish" else "bullish"
                        if HB.cisd_last(f15.tail(30), against):
                            reasons.append("cisd"); fired.add("cisd")
                else:
                    if "flip" not in fired:
                        if st["pdh"] is not None and cl > st["pdh"]:
                            reasons.append("flip"); fired.add("flip")
                        elif st["pdl"] is not None and cl < st["pdl"]:
                            reasons.append("flip"); fired.add("flip")
                if reasons:
                    _, ns = HB.read_at(sl, news, D, t, f"UPDATE @ {t.strftime('%H:%M')}",
                                       prev_bias=st["bias"], trigger=";".join(reasons))
                    st = ns; tl.append((t.strftime("%H:%M"), st["bias"]))
            t += pd.Timedelta(minutes=15)
        tls[str(D.date())] = tl
        if (i + 1) % 20 == 0:
            print(f"  timelines {i+1}/{len(days)}", flush=True)
    return tls


def bias_at(tls, day, hhmm):
    tl = tls.get(day)
    if tl is None:
        return "NEUTRAL"
    cur = tl[0][1]
    for tm, b in tl:
        if tm <= hhmm:
            cur = b
        else:
            break
    return cur


# ------------------------------------------------------------------ triggers + blend

def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv",
              "/home/user/gs/output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            src = "pass29" if not p.startswith("/home/user") else "current"
            out.append((src, Trigger(**{k: v for k, v in r.items() if k != "session_day"})))
    return [t for src, t in out if t.pattern != "unclassified"
            and ((src == "pass29") or (t.ts[:7] in ("2026-06", "2026-07")))]


def run_blend(allt, war, df, base_cfg):
    CFG_E3 = base_cfg.model_copy(update={"mgmt_variant": "V8"})
    CFG_E4 = base_cfg.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3 = [t for t in trigs if t.ts[:10] not in war]
        e4 = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for name, tt, cfg in (("E3bal", e3, CFG_E3), ("E4war", e4, CFG_E4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ts = pd.Timestamp(r.fill_ts).tz_convert(NY)
                rows.append(dict(month=r.trade_date[:7], day=r.trade_date, fill=ts.strftime("%H:%M"),
                                 branch=name, dir=r.direction, pattern=r.pattern, htf=r.htf_flag,
                                 risk_pts=round(abs(r.entry - r.stop_initial), 2),
                                 points=r.points, dollars=r.dollars, win=r.dollars > 0))
    return pd.DataFrame(rows)


def cuts(J):
    if not len(J):
        return J
    fh = J.fill.str.slice(0, 2).astype(int)
    return J[(J.risk_pts >= 5.0) & ~((J.pattern == "B") & (fh == 9))
             & ~((J.branch == "E3bal") & (J.htf == "with_trend"))]


def rep(x, label):
    if not len(x):
        print(f"  {label:44s} 0t"); return
    m = x.groupby("month").dollars.sum()
    print(f"  {label:44s} {len(x):3d}t  win {x.win.mean()*100:4.1f}%  ${x.dollars.sum():+8,.0f}  "
          f"green {int((m>0).sum())}/{m.size}  $/t {x.dollars.mean():+.0f}")


# ------------------------------------------------------------------ main

bars = HB.load_bars()
news = HB.load_news()
allt = load_triggers()
V = pd.read_csv("/home/user/gs/output/regime_vector.csv")
war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")

trig_days = sorted({t.ts[:10] for t in allt})
days = [pd.Timestamp(d, tz=NY) for d in trig_days]
print(f"triggers {len(allt)} over {len(days)} days; building bias timelines ...", flush=True)
tls = build_timelines(bars, news, days)
pd.DataFrame([dict(day=d, time=tm, bias=b) for d, tl in tls.items() for tm, b in tl]) \
    .to_csv(SCRATCH / "bias_timelines_all.csv", index=False)

def tbias(t):
    hhmm = t.ts[11:16]
    return bias_at(tls, t.ts[:10], hhmm if hhmm >= "08:00" else "08:00")

t_dir = [t for t in allt if tbias(t) in ("BULLISH", "BEARISH")]
t_aln = [t for t in allt if (tbias(t) == "BULLISH" and t.direction == "long")
         or (tbias(t) == "BEARISH" and t.direction == "short")]
print(f"gate pass rates: directional {len(t_dir)}/{len(allt)}  aligned {len(t_aln)}/{len(allt)}")

base_cfg = load_backtest_config().model_copy(
    update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})

print("simulating DIRECTIONAL arm ...", flush=True)
J_dir = cuts(run_blend(t_dir, war, df, base_cfg))
print("simulating ALIGNED arm ...", flush=True)
J_aln = cuts(run_blend(t_aln, war, df, base_cfg))

print("\n=== TRUE RE-BACKTEST: v1.1 with LIVE bias gate on trigger flow (post-cuts) ===")
base = pd.read_csv(SCRATCH / "champion_v11_rerun.csv")
rep(base, "BASE ungated (verified fresh re-run)")
rep(J_dir, "LIVE GATE directional (any read, no NEUTRAL)")
rep(J_aln, "LIVE GATE aligned-only")
for name, JJ in (("directional", J_dir), ("aligned", J_aln)):
    if len(JJ):
        print(f"\n  monthly, {name}:")
        print("  " + JJ.groupby("month").dollars.sum().round(0).to_string().replace("\n", "\n  "))
J_dir.to_csv(SCRATCH / "v11_live_directional.csv", index=False)
J_aln.to_csv(SCRATCH / "v11_live_aligned.csv", index=False)
print("\nsaved v11_live_directional.csv, v11_live_aligned.csv, bias_timelines_all.csv")
