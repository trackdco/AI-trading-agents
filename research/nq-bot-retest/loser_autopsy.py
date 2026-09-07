#!/usr/bin/env python3
"""
Loser autopsy on a sealed retest output — post-hoc DIAGNOSTIC, reported not binding.
Joins entry and exit records, restricts to entries >= --from, and describes the losing trades:
payoff geometry, exit anatomy, where losses cluster (hour, weekday, month, stop, ATR, HTF, score,
regime, direction), streaks and worst days, friction. Every table is a slice of one outcome set;
none of it is a tuning target (PREREGISTRATION.md §6).
usage: loser_autopsy.py OUTPUT.json --from 2025-09-01 [--md OUT.md]
"""
import argparse
import json
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ap = argparse.ArgumentParser()
ap.add_argument("path")
ap.add_argument("--from", dest="start", required=True)
ap.add_argument("--md", default=None)
a = ap.parse_args()

d = json.load(open(a.path))
ent = {r["trade_id"]: r for r in d["records"] if r["action"] == "entry"}
trades = []
for r in d["records"]:
    if r["action"] != "exit" or r["trade_id"] not in ent:
        continue
    e = ent[r["trade_id"]]
    t_et = datetime.fromisoformat(e["timestamp"]).astimezone(ET)
    if t_et.date() < datetime.fromisoformat(a.start).date():
        continue
    x_et = datetime.fromisoformat(r["timestamp"]).astimezone(ET)
    trades.append({
        "ts": t_et, "exit_ts": x_et, "pnl": r["adjusted_pnl"], "raw": r["raw_pnl"],
        "c1": r["c1_pnl"], "c2": r["c2_pnl"], "c1r": r["c1_exit_reason"], "c2r": r["c2_exit_reason"],
        "dir": e["direction"], "stop": e["stop_distance"], "score": e["signal_score"], "regime": e["regime"],
        "htf": e.get("htf_strength", 0.0), "htf_dir": e.get("htf_bias", ""), "atr": e["atr"],
        "slip_in": e["slippage_applied"], "slip_out": r["exit_slippage_cost"], "comm": r["commission_total"],
        "bars": r["bar_index"] - e["bar_index"], "hour": t_et.hour + t_et.minute / 60.0,
        "wd": t_et.strftime("%a"), "month": t_et.strftime("%Y-%m"),
        "tday": (t_et + timedelta(days=1)).date() if t_et.hour >= 18 else t_et.date(),
    })
trades.sort(key=lambda t: t["ts"])
L = [t for t in trades if t["pnl"] < 0]
W = [t for t in trades if t["pnl"] > 0]
Z = [t for t in trades if t["pnl"] == 0]
out = []
def p(s=""):
    out.append(s)
def q(xs, f):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(f * len(xs)))] if xs else float("nan")
def table(title, key, order=None, fmt=lambda k: str(k)):
    groups = defaultdict(list)
    for t in trades:
        groups[key(t)].append(t)
    keys = order if order else sorted(groups)
    p(f"\n**{title}**\n")
    p("| bucket | n | share of trades | WR% | mean $ | total $ | share of all losses $ | mean loss $ |")
    p("|---|---|---|---|---|---|---|---|")
    tot_loss = sum(t["pnl"] for t in L)
    for k in keys:
        g = groups.get(k, [])
        if not g:
            continue
        gl = [t["pnl"] for t in g if t["pnl"] < 0]
        wr = 100 * sum(1 for t in g if t["pnl"] > 0) / len(g)
        p(f"| {fmt(k)} | {len(g)} | {100*len(g)/len(trades):.0f}% | {wr:.0f} | {st.mean(t['pnl'] for t in g):+.1f} | "
          f"{sum(t['pnl'] for t in g):+,.0f} | {100*sum(gl)/tot_loss if tot_loss else 0:.0f}% | {st.mean(gl) if gl else 0:+.1f} |")

cfg = d["meta"]["config"]
p(f"# Loser autopsy — {a.path.split('/')[-1]} (entries ≥ {a.start})")
p(f"\nconfig: {cfg}\n")
p("## 1. Geometry")
p(f"- trades {len(trades)}: winners {len(W)}, losers {len(L)}, scratch {len(Z)}; win rate {100*len(W)/len(trades):.1f}%")
aw, al = st.mean(t["pnl"] for t in W), st.mean(t["pnl"] for t in L)
p(f"- average win **${aw:+.2f}**, average loss **${al:+.2f}**, payoff ratio {aw/-al:.2f}; breakeven win rate {100*(-al)/(aw-al):.1f}% vs actual {100*len(W)/len(trades):.1f}% → margin {100*len(W)/len(trades) - 100*(-al)/(aw-al):+.1f} points")
p(f"- gross wins ${sum(t['pnl'] for t in W):+,.0f}, gross losses ${sum(t['pnl'] for t in L):+,.0f}, net ${sum(t['pnl'] for t in trades):+,.0f}")
ls = sorted(t["pnl"] for t in L)
p(f"- loss quantiles: p10 {q(ls,0.10):+.0f}, p25 {q(ls,0.25):+.0f}, median {q(ls,0.5):+.0f}, p75 {q(ls,0.75):+.0f}, p90 {q(ls,0.90):+.0f}, worst {ls[0]:+.0f}")
worst5 = ls[: max(1, len(ls) // 20)]
p(f"- worst 5% of losers ({len(worst5)} trades) carry {100*sum(worst5)/sum(ls):.0f}% of all losses; worst 10 trades carry {100*sum(ls[:10])/sum(ls):.0f}%")
p("\n**Ten largest losers**\n\n| entry (ET) | dir | stop | ATR | score | HTF | regime | c1 exit | c2 exit | bars | $ |\n|---|---|---|---|---|---|---|---|---|---|---|")
for t in sorted(L, key=lambda t: t["pnl"])[:10]:
    p(f"| {t['ts']:%Y-%m-%d %H:%M} | {t['dir']} | {t['stop']:.1f} | {t['atr']:.1f} | {t['score']:.2f} | {t['htf']:.2f} | {t['regime']} | {t['c1r']} | {t['c2r']} | {t['bars']} | {t['pnl']:+.0f} |")

p("\n## 2. Exit anatomy")
def combo(t): return f"c1={t['c1r']} / c2={t['c2r']}"
cl, cw = Counter(combo(t) for t in L), Counter(combo(t) for t in W)
p("\n| exit pattern | losers | mean loss $ | winners | mean win $ |\n|---|---|---|---|---|")
for k in sorted(set(cl) | set(cw), key=lambda k: -(cl[k] + cw[k])):
    ml = st.mean(t["pnl"] for t in L if combo(t) == k) if cl[k] else 0
    mw = st.mean(t["pnl"] for t in W if combo(t) == k) if cw[k] else 0
    p(f"| {k} | {cl[k]} | {ml:+.1f} | {cw[k]} | {mw:+.1f} |")
both_stop = [t for t in L if "stop" in t["c1r"].lower() and "stop" in t["c2r"].lower()]
p(f"\n- both legs stopped: {len(both_stop)} of {len(L)} losers ({100*len(both_stop)/len(L):.0f}%), mean {st.mean(t['pnl'] for t in both_stop) if both_stop else 0:+.1f}")
p(f"- losers' median holding {st.median(t['bars'] for t in L):.0f} bars (2-min) vs winners' {st.median(t['bars'] for t in W):.0f}")
p(f"- loss in stop units: median loss / (stop × $2 × 2 contracts) = {st.median(-t['pnl']/(t['stop']*4) for t in L):.2f} R")

p("\n## 3. Where the losses cluster")
table("By entry hour (ET)", lambda t: int(t["hour"]), fmt=lambda k: f"{k:02d}:00")
table("First 30 minutes vs rest", lambda t: "09:30–10:00" if 9.5 <= t["hour"] < 10.0 else ("15:30–16:00" if t["hour"] >= 15.5 else "10:00–15:30"), order=["09:30–10:00", "10:00–15:30", "15:30–16:00"])
table("By weekday", lambda t: t["wd"], order=["Mon", "Tue", "Wed", "Thu", "Fri"])
table("By month", lambda t: t["month"])
table("By stop distance", lambda t: "10.0 (floor bound)" if abs(t["stop"] - 10.0) < 1e-9 else ("10–15" if t["stop"] < 15 else ("15–20" if t["stop"] < 20 else ("20–25" if t["stop"] < 25 else "25–30"))), order=["10.0 (floor bound)", "10–15", "15–20", "20–25", "25–30"])
table("By ATR14 at signal", lambda t: "<10" if t["atr"] < 10 else ("10–15" if t["atr"] < 15 else ("15–20" if t["atr"] < 20 else ("20–30" if t["atr"] < 30 else "≥30"))), order=["<10", "10–15", "15–20", "20–30", "≥30"])
table("By stop / ATR", lambda t: "<0.7" if t["stop"]/t["atr"] < 0.7 else ("0.7–1.0" if t["stop"]/t["atr"] < 1.0 else ("1.0–1.5" if t["stop"]/t["atr"] < 1.5 else "≥1.5")), order=["<0.7", "0.7–1.0", "1.0–1.5", "≥1.5"])
table("By HTF strength", lambda t: f"{round(t['htf']*10)/10:.1f}")
table("By signal score", lambda t: f"{t['score']:.2f}")
table("By regime label", lambda t: t["regime"])
table("By direction", lambda t: t["dir"], order=["long", "short"])
table("Direction vs HTF bias", lambda t: f"{t['dir']} with HTF {t['htf_dir']}")

p("\n## 4. Streaks, days, drawdown")
mx = cur = 0
for t in trades:
    cur = cur + 1 if t["pnl"] < 0 else 0
    mx = max(mx, cur)
days = defaultdict(float)
for t in trades:
    days[t["tday"]] += t["pnl"]
dv = sorted(days.values())
p(f"- max consecutive losers {mx}; trading days {len(days)}, losing days {sum(1 for v in dv if v < 0)} ({100*sum(1 for v in dv if v < 0)/len(dv):.0f}%)")
p(f"- worst day ${dv[0]:+,.0f}, worst 5 days {', '.join(f'{v:+,.0f}' for v in dv[:5])}; best day ${dv[-1]:+,.0f}")
cum = peak = dd = 0.0
ps = trades[0]["ts"]
dd_start = dd_trough = None
for t in trades:
    cum += t["pnl"]
    if cum > peak:
        peak, ps = cum, t["ts"]
    if peak - cum > dd:
        dd, dd_start, dd_trough = peak - cum, ps, t["ts"]
p(f"- max drawdown ${dd:,.0f} from {dd_start:%Y-%m-%d} to {dd_trough:%Y-%m-%d}")
wk = defaultdict(float)
for t in trades:
    wk[t["ts"].strftime("%G-W%V")] += t["pnl"]
wv = sorted(wk.items(), key=lambda kv: kv[1])
p(f"- worst weeks: {', '.join(f'{k} {v:+,.0f}' for k, v in wv[:3])}; losing weeks {sum(1 for _, v in wv if v < 0)} of {len(wv)}")

p("\n## 5. Friction")
slip = sum(t["slip_in"] * 2 * 2 + t["slip_out"] for t in trades)   # entry slippage pts × $2 × 2 contracts + exit $
comm = sum(t["comm"] for t in trades)
gross_raw = sum(t["raw"] for t in trades) + sum(t["comm"] for t in trades)
p(f"- commission ${comm:,.0f}, slippage ${slip:,.0f} (entry {sum(t['slip_in']*4 for t in trades):,.0f} + exit {sum(t['slip_out'] for t in trades):,.0f}); friction total ${comm+slip:,.0f} = {100*(comm+slip)/max(gross_raw,1):.0f}% of pre-friction gross")
p(f"- friction per trade ${(comm+slip)/len(trades):.2f}; on losers it adds ${st.mean(t['slip_in']*4 + t['slip_out'] + t['comm'] for t in L):.2f} to a mean loss of ${al:+.2f} ({100*st.mean(t['slip_in']*4 + t['slip_out'] + t['comm'] for t in L)/-al:.0f}%)")
text = "\n".join(out)
print(text)
if a.md:
    open(a.md, "w").write(text + "\n")
