"""LEVEL-SMT on the full history: is ES closing through ITS OWN prior-day
value area in the same direction, at the same moment as the NQ signal?

Cleaner than the fill-based version used on the short sample: ES SIGNALS
are computed directly (crossing closes of ES's own PD VAH/VAL at ES's
certified depth), so the feature is "did the other index break its level",
not "did the other index's retest happen to fill".

PREREGISTERED, written before the full-history result was read:
  primary window +/-15 min, sensitivity +/-5 min (both were examined on the
  33-day sample where every cell was noise; carrying both forward and
  declaring the primary now).
  SURVIVOR if the confirm-vs-oppose net EV spread is >= 0.05R with the
  ordering holding in BOTH halves and n >= 400 per half in each extreme
  bucket. WATCH at >= 0.03R. NULL otherwise.
No lookahead: ES levels are prior-day, ES signals are closed candles at or
before the NQ signal minute.
"""
import gzip, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import scripts.offline_briefings as OB
from scripts.agent_context import volume_profile
import scripts.pd_va_backtest as PB

COST, ES_DEPTH, ES_BIN, ES_TICK = 0.5, 0.75, 0.25, 0.25
PB.TICK = ES_TICK
es = pd.read_parquet("data/reference/es_1m.parquet")
es["ts"] = pd.to_datetime(es.ts_event, utc=True).dt.tz_convert(OB.NY)
es = es.set_index("ts").sort_index()[["open","high","low","close","volume"]]
roll = set(json.load(open("data/reference/es_roll_days.json")))

ts = [json.loads(l) for l in gzip.open(
    "output/analysis/pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz", "rt")]
ts = [t for t in ts if t["depth"] == 3.0 and t["target_r"] == 1.0]
days = sorted({t["day"] for t in ts}); MID = days[len(days)//2]
print(f"NQ trades {len(ts):,} over {len(days)} days, split {MID}")

# ES signals per session-day, from ES's OWN prior-day value area
es_sig, prev_t0, built = {}, None, 0
for day in sorted({str(d.date()) for d in (es.index - pd.Timedelta(hours=18)).normalize()}):
    t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
    if prev_t0 is None:
        prev_t0 = t0; continue
    pseg = es[(es.index >= prev_t0) & (es.index < t0)]
    sess = es[(es.index >= t0) & (es.index < t0 + pd.Timedelta(hours=23))]
    prev_t0 = t0
    if len(pseg) < 300 or len(sess) < 600 or day in roll:
        continue
    _, val, vah = volume_profile(pseg, bin_w=ES_BIN)
    if not (np.isfinite(vah) and np.isfinite(val)):
        continue
    vah = round(vah/ES_TICK)*ES_TICK; val = round(val/ES_TICK)*ES_TICK
    c1 = sess.resample("1min").agg({"open":"first","high":"max","low":"min",
                                     "close":"last"}).dropna()
    hrs = (c1.index - t0).total_seconds()/3600
    c1 = c1[(hrs >= 1.0 - 1/60 - 0.02) & (hrs + 1/60 <= 21 + 55/60 + 1e-6)]
    if len(c1) < 50: continue
    sigs = PB.day_signals(c1, vah, val, ES_DEPTH, tf=1)
    es_sig[day] = [((s["t"] - t0).total_seconds()/3600, s["dir"]) for s in sigs]
    built += 1
print(f"ES signal days built: {built}  "
      f"(mean {np.mean([len(v) for v in es_sig.values()]):.1f} ES signals/day)\n")

for WIN in (15, 5):
    agg = {}
    matched = 0
    for t in ts:
        if t["day"] not in es_sig: continue
        matched += 1
        near = [d for h, d in es_sig[t["day"]] if abs(h - t["t_sig_hrs"])*60 <= WIN]
        k = ("confirm" if t["dir"] in near else
             "oppose" if -t["dir"] in near else "silent")
        a = agg.setdefault(k, {"i": [], "o": [], "w": 0, "l": 0})
        a["o" if t["day"] >= MID else "i"].append(t["r"] - COST/t["risk"])
        if t["res"] == "TARGET": a["w"] += 1
        elif t["res"] == "STOP": a["l"] += 1
    tag = "PRIMARY" if WIN == 15 else "sensitivity"
    print(f"+/-{WIN} min ({tag}) - {matched:,} NQ trades on ES-covered days")
    print(f"  {'state':<9}{'n':>7}{'share':>8}{'WR':>7}{'net EV':>10}"
          f"{'IS EV':>10}{'OOS EV':>10}{'IS n':>7}{'OOS n':>7}")
    for k in ("confirm", "oppose", "silent"):
        if k not in agg: continue
        a = agg[k]; al = a["i"] + a["o"]
        print(f"  {k:<9}{len(al):>7,}{len(al)/matched:>8.1%}"
              f"{a['w']/max(a['w']+a['l'],1):>7.1%}{np.mean(al):>+10.4f}"
              f"{np.mean(a['i']):>+10.4f}{np.mean(a['o']):>+10.4f}"
              f"{len(a['i']):>7,}{len(a['o']):>7,}")
    c, o = agg["confirm"], agg["oppose"]
    di = np.mean(c["i"]) - np.mean(o["i"]); do = np.mean(c["o"]) - np.mean(o["o"])
    nmin = min(len(c["i"]), len(c["o"]), len(o["i"]), len(o["o"]))
    m = min(abs(di), abs(do)); same = np.sign(di) == np.sign(do)
    v = ("NULL (n<400)" if nmin < 400 else "NULL (sign flips)" if not same
         else "SURVIVOR" if m >= 0.05 else "WATCH" if m >= 0.03
         else "NULL (spread<0.03)")
    print(f"  confirm - oppose: IS {di:+.4f}  OOS {do:+.4f}   "
          f"smallest half-cell {nmin:,}")
    print(f"  VERDICT: {v}\n")
