#!/usr/bin/env python3
"""SMT DIVERGENCE (NQ vs ES) as an as-of-signal feature on the NQ book.

PREREGISTERED (written before any result was read, same bar as rounds 1-3):
  SURVIVOR if the confirm-vs-diverge net EV spread is >= 0.05R with the
  ordering holding in BOTH halves and n >= 400 per half in each extreme
  bucket. WATCH at >= 0.03R. NULL otherwise. A bucket negative in both
  halves at n >= 400/half is a CUT candidate.
  Known in advance: the overlapping ES/NQ sample is ~40 session-days, so
  the n>=400/half condition CANNOT be met. This run is therefore a LOOK,
  not a verdict, and is labelled as such wherever it is reported.

Feature, computed at the signal bar with a fixed 30-bar lookback:
  for a long break  (NQ closed UP through its level)
      nq_new = NQ's signal-bar high exceeds the prior 30-bar high
      es_new = ES's signal-bar high exceeds the prior 30-bar high
  for a short break, the same on lows.
  confirm   both markets made the new extreme  (they agree)
  diverge   NQ made it, ES did not             (classic SMT divergence)
  es_leads  ES made it, NQ did not
  neither   neither made a new extreme
No lookahead: every input is the signal bar or earlier.
"""
import gzip, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import scripts.offline_briefings as OB

K, COST = 30, 0.5
DEPTH, TGT = 3.0, 1.0
nq = OB.get_bars()
es = pd.read_parquet("data/reference/es_1m.parquet")
es["ts"] = pd.to_datetime(es.ts_event, utc=True).dt.tz_convert(OB.NY)
es = es.set_index("ts").sort_index()[["open","high","low","close"]]

ts = [json.loads(l) for l in gzip.open(
    "output/analysis/pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz", "rt")]
ts = [t for t in ts if t["depth"] == DEPTH and t["target_r"] == TGT
      and "2026-06-03" <= t["day"] <= "2026-09-02"]
days = sorted({t["day"] for t in ts})
MID = days[len(days)//2]
print(f"NQ certified-cell trades in the ES window: {len(ts):,} over {len(days)} days")

out = []
for t in ts:
    t0 = pd.Timestamp(t["day"] + " 18:00", tz=OB.NY)
    sig = (t0 + pd.Timedelta(hours=t["t_sig_hrs"])).floor("min")
    n = nq[(nq.index <= sig) & (nq.index > sig - pd.Timedelta(minutes=K+1))]
    e = es[(es.index <= sig) & (es.index > sig - pd.Timedelta(minutes=K+1))]
    if len(n) < K or len(e) < K:
        continue
    d = t["dir"]
    if d == 1:
        nq_new = n.high.iloc[-1] > n.high.iloc[:-1].max()
        es_new = e.high.iloc[-1] > e.high.iloc[:-1].max()
    else:
        nq_new = n.low.iloc[-1] < n.low.iloc[:-1].min()
        es_new = e.low.iloc[-1] < e.low.iloc[:-1].min()
    smt = ("confirm" if (nq_new and es_new) else "diverge" if nq_new
           else "es_leads" if es_new else "neither")
    out.append((smt, t["r"] - COST/t["risk"], t["day"], t["res"]))
print(f"matched to ES bars: {len(out):,}\n")

print(f"  {'SMT state':<12}{'n':>7}{'share':>8}{'WR':>8}{'net EV':>10}"
      f"{'IS':>10}{'OOS':>10}{'IS n':>7}{'OOS n':>7}")
agg = {}
for smt, r, day, res in out:
    a = agg.setdefault(smt, {"i": [], "o": [], "w": 0, "l": 0})
    a["o" if day >= MID else "i"].append(r)
    if res == "TARGET": a["w"] += 1
    elif res == "STOP": a["l"] += 1
for k in ("confirm", "diverge", "es_leads", "neither"):
    if k not in agg: continue
    a = agg[k]; al = a["i"] + a["o"]
    m = lambda x: np.mean(x) if x else float("nan")
    print(f"  {k:<12}{len(al):>7}{len(al)/len(out):>8.1%}"
          f"{a['w']/max(a['w']+a['l'],1):>8.3f}{m(al):>+10.4f}"
          f"{m(a['i']):>+10.4f}{m(a['o']):>+10.4f}{len(a['i']):>7}{len(a['o']):>7}")

if "confirm" in agg and "diverge" in agg:
    c, g = agg["confirm"], agg["diverge"]
    di = np.mean(c["i"]) - np.mean(g["i"]); do = np.mean(c["o"]) - np.mean(g["o"])
    print(f"\n  confirm - diverge:  IS {di:+.4f}   OOS {do:+.4f}")
    same = np.sign(di) == np.sign(do)
    print(f"  ordering holds in both halves: {same}")
    smallest = min(len(agg[k]["i"] + agg[k]["o"]) for k in ("confirm", "diverge"))
    need = 800 / (smallest / len(days))
    print(f"\n  VERDICT: LOOK ONLY - smallest extreme bucket has {smallest} trades, "
          f"the rule needs 400/half = 800.")
    print(f"  To clear it: ~{need:.0f} overlapping session-days of ES "
          f"(~{need/252:.1f} years). Have {len(days)}.")


# RESULT OF THE 2026-09-03 LOOK (33 overlapping session-days, 427 trades):
#   swing-SMT  confirm 73 / diverge 25 / es_leads 19 / neither 310
#              confirm-minus-diverge  IS -0.1402  OOS +0.3479  -> sign flips
#   level-SMT (+/-15min, is ES breaking its own VA the same way?)
#              confirm 106 (25%) / oppose 35 (8%) / silent 286 (67%)
#              every cell flips sign between halves
# NOTHING IS CONCLUDED. The smallest extreme bucket holds 16-35 trades
# against the rule's 800. Settling it needs ES history matching NQ's:
#   dataset GLBX.MDP3, schema ohlcv-1m, symbols ["ES.FUT"], stype_in
#   parent, start 2023-01-01 -> ~28 MB, ~1,050 overlapping days.
# Note the divergence bucket is only 6-8% of signals either way, so even a
# positive result is a small overlay - size it, do not filter on it.
