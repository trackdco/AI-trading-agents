#!/usr/bin/env python3
"""Mechanical scorer for the 2017-2019 holdout. docs/PREREG-holdout-2017-2019.md.

    python3 score_holdout_2017_2019.py --gate0   # tick screen per year, k, writes nq17b
    python3 score_holdout_2017_2019.py           # Tests A-E, predictions P1-P6

Every threshold below is copied from the pre-registration. Nothing is tuned here.
Run from the engine worktree (cwd = ql18) by scripts/run_holdout_2017_2019.sh.
"""
import json, re, sys, gzip
from collections import defaultdict
from pathlib import Path
import numpy as np, pandas as pd

QL = Path.cwd()
sys.path.insert(0, str(QL))
import scripts.conviction_sizing as CS           # noqa: E402
import scripts.offline_briefings as OB           # noqa: E402

OUT, TICK, COST = QL / "output/analysis", 0.25, CS.COST_PTS
BARS17 = QL / "data/reference/nq_2017_2019_1m.parquet"
ROLLS17 = QL / "data/reference/nq_2017_2019_roll_days.json"
FROZEN = dict(floor=5.0, depth=3.0, cap=30.0, bin=1.0)
SCORE_FROM, SCORE_TO = "2017-01-01", "2019-12-31"   # Amendment 1: declared window, hard filter


def bars17():
    b = pd.read_parquet(BARS17)
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
    return b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]


def q(x):  # round to tick
    return round(round(x / TICK) * TICK, 2)


# ----------------------------------------------------------------- GATE 0
def gate0():
    b = bars17()
    rolls = set(json.loads(ROLLS17.read_text()))
    sess = (b.index - pd.Timedelta(hours=18)).normalize().strftime("%Y-%m-%d")
    b = b[~pd.Series(sess, index=b.index).isin(rolls)]
    b = b[(b.index >= pd.Timestamp(f"{SCORE_FROM} 00:00", tz=OB.NY)) & (b.index < pd.Timestamp("2020-01-01 00:00", tz=OB.NY))]
    print("GATE 0 - tick screen (02:00-16:00 ET median 1m high-low; law: >=20 ticks; NQ 2023-26 = 28)")
    act = b[(b.index.hour >= 2) & (b.index.hour < 16)]
    ticks = {}
    for y, g in act.groupby(act.index.year):
        ticks[str(y)] = float(((g.high - g.low).median()) / TICK)
        print(f"  {y}: {ticks[str(y)]:.1f} ticks  {'BELOW 20' if ticks[str(y)] < 20 else 'ok'}")
    m_era = float((b.high - b.low).median())
    prev = json.loads((OUT / "holdout_constants.json").read_text())
    m_now = float(prev.get("m_now", 5.25))
    k = m_era / m_now
    era = dict(floor=q(FROZEN["floor"] * k), depth=q(FROZEN["depth"] * k),
               cap=q(FROZEN["cap"] * k), bin=q(FROZEN["bin"] * k), k=round(k, 4),
               m_era=m_era, m_now=m_now, ticks_by_year=ticks)
    (OUT / "holdout17_constants.json").write_text(json.dumps(era, indent=1))
    print(f"  m_now {m_now:.4f}  m_era {m_era:.4f}  k = {k:.4f}")
    print(f"  Run B constants: floor {era['floor']} depth {era['depth']} cap {era['cap']} bin {era['bin']}")
    # add nq17b to INSTRUMENTS by formula (mechanical; declared in prereg S3)
    p = QL / "scripts/pd_va_backtest.py"; s = p.read_text()
    if '"nq17b"' not in s:
        dep = tuple(q(d * k) for d in (0.0, 1.0, 2.0, 3.0))
        blk = (f'    "nq17b": dict(tick=0.25, min_risk={era["floor"]}, bin_w={era["bin"]},\n'
               f'                  depths={dep},\n'
               f'                  bars="data/reference/nq_2017_2019_1m.parquet",\n'
               f'                  rolls="data/reference/nq_2017_2019_roll_days.json"),\n')
        # anchor on the nq17a dict's LAST line (its rolls= entry), not its first "),\n" -
        # the first attempt matched the depths tuple's close and spliced nq17b inside nq17a
        s = re.sub(r'(    "nq17a": dict\(.*?rolls="data/reference/nq_2017_2019_roll_days\.json"\),\n)',
                   lambda m: m.group(1) + blk, s, count=1, flags=re.S)
        p.write_text(s); print("  nq17b added to INSTRUMENTS")
    return 0


# ----------------------------------------------------------------- helpers
def load(name, cell=None):
    f = OUT / name
    if not f.exists():
        print(f"  MISSING {name}"); return None
    ts = [json.loads(l) for l in gzip.open(f, "rt")]
    pre = sum(1 for t in ts if t["day"] < SCORE_FROM)
    ts = [t for t in ts if SCORE_FROM <= t["day"] <= SCORE_TO]
    if pre: print(f"  ({name}: {pre:,} warmup-period trades before {SCORE_FROM} excluded from scoring)")
    return [t for t in ts if t["depth"] == cell[0] and t["target_r"] == cell[1]] if cell else ts


def net(t): return t["r"] - COST / t["risk"]
def wr(ts):
    tp = sum(t["res"] == "TARGET" for t in ts); st = sum(t["res"] == "STOP" for t in ts)
    return tp / max(tp + st, 1)
def ev(ts): return sum(map(net, ts)) / len(ts)
def maxdd(v): e = np.cumsum(v); return float((e - np.maximum.accumulate(e)).min())
def byyear(ts):
    d = defaultdict(list)
    for t in ts: d[t["day"][:4]].append(t)
    return dict(sorted(d.items()))
def dayseries(kept, mult=None):
    days = sorted(kept)
    v = np.array([sum((mult[t["tier"]] if mult else 1) * net(t) for t in kept[d]) for d in days])
    return days, v
def P(ok): return "PASS" if ok else "FAIL"


# ----------------------------------------------------------------- VERDICT
def verdict():
    c = json.loads((OUT / "holdout17_constants.json").read_text())
    R = {}
    print("=" * 80); print("TEST A - base grammar, value-area book, frozen constants"); print("=" * 80)
    va = load("pd_va_trades_nq17a_xr30_sar_through_tf1.jsonl.gz")
    A = [t for t in va if t["depth"] == 3.0 and t["target_r"] == 1.0] if va else []
    if A:
        yy = byyear(A)
        for y, ts in yy.items():
            print(f"  {y}: n {len(ts):>6,}  WR {wr(ts):.1%}  EV {ev(ts):+.4f}  netR {sum(map(net, ts)):+.0f}")
        okA = all(sum(map(net, ts)) > 0 for ts in yy.values()) and wr(A) >= 0.60 and ev(A) >= 0.08
        print(f"  pooled: n {len(A):,}  WR {wr(A):.1%}  EV {ev(A):+.4f}   -> TEST A {P(okA)}")
        R["A"] = okA; R["A_by_year"] = {y: ev(ts) for y, ts in yy.items()}

    print("\n" + "=" * 80); print("TEST B - the empire, flat"); print("=" * 80)
    lv = load("pd_va_trades_nq17a_lvall_xr30_sar_through_tf1.jsonl.gz")
    sv = load("vwap_rev_tf1_retest_nq17a_ng0_xr30_dd.jsonl.gz", (3.0, 1.0))
    nv = load("vwap_rev_tf1_retest_nq17a_ng0_xr30_nyanc_dd.jsonl.gz", (3.0, 1.0))
    if lv and sv and nv:
        books = {"8-level": lv, "vwap-session": sv, "vwap-ny": nv}
        for n, b in books.items():
            print(f"  {n:<14} n {len(b):>7,}  WR {wr(b):.1%}  EV {ev(b):+.4f}")
        kf = CS.rail_pass([lv, sv, nv]); flat = [t for d in kf for t in kf[d]]
        yy = byyear(flat)
        for y, ts in yy.items():
            dv = np.array([sum(map(net, kf[d])) for d in sorted(kf) if d.startswith(y)])
            print(f"  {y}: netR {dv.sum():+.0f}  worst day {dv.min():+.1f}  maxDD {maxdd(dv):+.1f}")
        okB = all(ev(b) >= 0.08 for b in books.values()) and \
              all(sum(map(net, ts)) > 0 for ts in yy.values()) and wr(flat) >= 0.60
        print(f"  railed pooled: n {len(flat):,}  WR {wr(flat):.1%}  EV {ev(flat):+.4f}   -> TEST B {P(okB)}")
        R["B"] = okB; R["book_ev"] = {n: ev(b) for n, b in books.items()}
        R["kf"] = kf

        print("\n" + "=" * 80); print("TEST C - ARMING (primary). dd-matched R/day >= +5% in BOTH halves"); print("=" * 80)
        lva = load("pd_va_trades_nq17a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz")
        sva = load("vwap_rev_tf1_retest_nq17a_ng0_xr30_dd_arm1.jsonl.gz", (3.0, 1.0))
        nva = load("vwap_rev_tf1_retest_nq17a_ng0_xr30_nyanc_dd_arm1.jsonl.gz", (3.0, 1.0))
        if lva and sva and nva:
            ka = CS.rail_pass([lva, sva, nva])
            dF, vF = dayseries(kf); dA, vA = dayseries(ka)
            common = sorted(set(dF) & set(dA)); iF = [dF.index(d) for d in common]; iA = [dA.index(d) for d in common]
            vF, vA = vF[iF], vA[iA]; MID = common[len(common) // 2]
            sc = abs(maxdd(vF)) / abs(maxdd(vA)); vAs = vA * sc
            m = np.array([d < MID for d in common]); lifts = {}
            for h, msk in (("IS", m), ("OOS", ~m)):
                lifts[h] = vAs[msk].mean() / vF[msk].mean() - 1
                print(f"  {h}: flat {vF[msk].mean():+.3f}  armed {vA[msk].mean():+.3f}  dd-matched {vAs[msk].mean():+.3f}  lift {lifts[h]:+.1%}")
            armed = [t for d in ka for t in ka[d]]
            print(f"  raw: EV {ev(flat):+.4f} -> {ev(armed):+.4f} ({ev(armed)/ev(flat)-1:+.1%})  "
                  f"maxDD {maxdd(vF):+.1f} -> {maxdd(vA):+.1f}  split {MID}")
            okC = all(v >= 0.05 for v in lifts.values())
            print(f"  -> TEST C {P(okC)}"); R["C"] = okC; R["lifts"] = lifts

        print("\n" + "=" * 80); print("TEST D - conviction sizing 2:1 on displacement, same rule"); print("=" * 80)
        if all("tier" in t for t in flat):
            mult = {"A": 1.0, "B": 1.0, "C": 0.5, "D": 0.5}
            dF, vF = dayseries(kf); _, vS = dayseries(kf, mult)
            sc = abs(maxdd(vF)) / abs(maxdd(vS)); vSs = vS * sc; MID = dF[len(dF) // 2]
            m = np.array([d < MID for d in dF]); lifts = {}
            for h, msk in (("IS", m), ("OOS", ~m)):
                lifts[h] = vSs[msk].mean() / vF[msk].mean() - 1
                print(f"  {h}: flat {vF[msk].mean():+.3f}  sized dd-matched {vSs[msk].mean():+.3f}  lift {lifts[h]:+.1%}")
            okD = all(v >= 0.05 for v in lifts.values()); print(f"  -> TEST D {P(okD)}"); R["D"] = okD
        else:
            print("  dumps untagged - rerun with --conviction")

        print("\n" + "=" * 80); print("TEST E - loser-autopsy claims"); print("=" * 80)
        b = bars17(); days = sorted(kf); feat = {}; hist = []; prev = None
        for d in days:
            t0 = pd.Timestamp(f"{d} 18:00", tz=OB.NY)
            if prev is not None:
                ps = b[(b.index >= prev) & (b.index < t0)]
                if len(ps) >= 300:
                    rng = float(ps.high.max() - ps.low.min())
                    med20 = float(np.median(hist[-20:])) if len(hist) >= 20 else np.nan
                    if med20 and med20 > 0: feat[d] = rng / med20
                    hist.append(rng)
            prev = t0
        ds = [d for d in days if d in feat]; xs = np.array([feat[d] for d in ds])
        e = np.quantile(xs, [0, .25, .5, .75, 1]); e[0], e[-1] = -np.inf, np.inf
        idx = np.clip(np.digitize(xs, e[1:-1]), 0, 3)
        lo = [d for d, i in zip(ds, idx) if i == 0]; hi = [d for d, i in zip(ds, idx) if i == 3]
        tl = [t for d in lo for t in kf[d]]; th = [t for d in hi for t in kf[d]]
        cnt = (len(th) / len(hi)) / (len(tl) / len(lo)) - 1; dev = abs(ev(th) - ev(tl))
        print(f"  E1 prior-vol Q4 vs Q1: trades/day {cnt:+.1%}  |dEV| {dev:.4f}   -> {P(cnt >= 0.25 and dev < 0.02)}")
        dr = np.array([sum(map(net, kf[d])) for d in ds]); worst = np.argsort(dr)[:max(len(ds) // 100, 5)]
        gap = abs(xs[worst].mean() - xs.mean())
        print(f"  E2 worst-1% prior-vol {xs[worst].mean():.2f} vs all {xs.mean():.2f} (|d| {gap:.2f})   -> {P(gap <= 0.15)}")
        R["E1"] = cnt >= 0.25 and dev < 0.02; R["E2"] = gap <= 0.15

    print("\n" + "=" * 80); print("PREDICTIONS"); print("=" * 80)
    tk = c["ticks_by_year"]; low = [y for y, v in tk.items() if v < 20]
    if "A_by_year" in R:
        weakest = min(R["A_by_year"], key=R["A_by_year"].get)
        print(f"  P1 year(s) <20 ticks: {low or 'none'}; weakest EV year {weakest}   -> "
              f"{'CORRECT' if low and weakest in low else 'WRONG'}")
    vb = load(f"pd_va_trades_nq17b_xr{c['cap']:g}_sar_through_tf1.jsonl.gz")
    if vb and A:
        Bc = [t for t in vb if abs(t["depth"] - c["depth"]) < 1e-6 and t["target_r"] == 1.0]
        print(f"  P2 frozen EV {ev(A):+.4f} vs era EV {ev(Bc):+.4f}   -> {'CORRECT' if ev(A) > ev(Bc) else 'WRONG'}")
    if "lifts" in R:
        ok = all(0.10 <= v <= 0.40 for v in R["lifts"].values())
        print(f"  P3 arming lift in [+10%,+40%] both halves   -> {'CORRECT' if ok else 'WRONG'}")
    if "kf" in R:
        kf = R["kf"]; chain = False
        for y in sorted({d[:4] for d in kf}):
            dv = np.array([sum(map(net, kf[d])) for d in sorted(kf) if d.startswith(y)])
            if maxdd(dv) < dv.min() - 1e-9: chain = True
        print(f"  P4 losses chain (maxDD deeper than worst day) in >=1 year   -> {'CORRECT' if chain else 'WRONG'}")
    if va:
        ok = True
        for dep in sorted({t["depth"] for t in va}):
            byT = {tg: ev([t for t in va if t["depth"] == dep and t["target_r"] == tg]) for tg in sorted({t["target_r"] for t in va})}
            if max(byT, key=byT.get) != 1.0: ok = False
        print(f"  P5 1R target best at every depth   -> {'CORRECT' if ok else 'WRONG'}")
    if "book_ev" in R:
        be = R["book_ev"]; ok = be["vwap-ny"] > be["8-level"] > be["vwap-session"]
        print(f"  P6 EV order ny > 8-level > session   -> {'CORRECT' if ok else 'WRONG'}")
    print("\nPRIMARY VERDICT (Test C, arming):", P(R.get("C", False)) if "C" in R else "NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(gate0() if "--gate0" in sys.argv else verdict())
