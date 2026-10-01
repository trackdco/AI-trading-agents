#!/usr/bin/env python3
"""Faithful port of dearvn/tradovate-trading-bot strategy.js (commit 6056eb6).
Rules frozen in docs/PREREG-tradovate-bot-port.md. Exits checked from the bar AFTER entry."""
import argparse, gzip, json, numpy as np, pandas as pd

def wma(x, n):
    w = np.arange(1, n+1, dtype=float); w /= w.sum()
    return pd.Series(x).rolling(n).apply(lambda v: np.dot(v, w), raw=True).values

def rsi(x, n=9):
    d = np.diff(x, prepend=x[0]); up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    au = pd.Series(up).ewm(alpha=1/n, adjust=False).mean().values
    ad = pd.Series(dn).ewm(alpha=1/n, adjust=False).mean().values
    rs = np.divide(au, ad, out=np.full_like(au, np.inf), where=ad > 0)
    return 100 - 100/(1+rs)

def atr(h, l, c, n=14):
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h-l, np.maximum(abs(h-pc), abs(l-pc)))
    return pd.Series(tr).ewm(alpha=1/n, adjust=False).mean().values

def macd_hist(c):
    e12 = pd.Series(c).ewm(span=12, adjust=False).mean()
    e26 = pd.Series(c).ewm(span=26, adjust=False).mean()
    m = e12 - e26
    return (m - m.ewm(span=9, adjust=False).mean()).values

def load(path, tf):
    b = pd.read_parquet(path); t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close","volume"]].sort_index()
    if tf > 1:
        b = b.resample(f"{tf}min").agg(open=("open","first"),high=("high","max"),low=("low","min"),
                                       close=("close","last"),volume=("volume","sum")).dropna(subset=["close"])
    return b

def run(b, fix_bug=False, cost=0.5):
    o,h,l,c,v = (b[x].values.astype(float) for x in ("open","high","low","close","volume"))
    n = len(c)
    R = rsi(c); W11, W48, W200 = wma(c,11), wma(c,48), wma(c,200)
    A = np.maximum(atr(h,l,c)*1.5, 2.5); MH = macd_hist(c); WV = wma(v,6); LOW6 = pd.Series(l).rolling(6).min().values
    ts = b.index.values
    rsi_up = rsi_dn = False; xup = False; xdn = False; cnt_out = 0
    pos = None; last_t = None; out = []
    for i in range(210, n):
        if np.isnan(W200[i]) or np.isnan(WV[i]) or np.isnan(LOW6[i]): continue
        r1, r2 = R[i], R[i-1]
        if r1 - r2 > 5 and r2 < 40 and r1 > 40: rsi_up, rsi_dn = True, False
        if r1 - r2 < -7 and r2 > 70 and r1 < 70: rsi_up, rsi_dn = False, True
        if W11[i-1] <= W48[i-1] and W11[i] > W48[i]: xup = True; xdn = False
        if W11[i-1] >= W48[i-1] and W11[i] < W48[i]:
            xup = False
            if fix_bug: xdn = True
        up10 = W11[i] > W48[i] or c[i] > W11[i]; dn10 = not up10
        up5 = c[i] > W48[i] and c[i] > W11[i]; dn5 = c[i] < W48[i] and c[i] < W11[i]
        bull = MH[i] > 0 or MH[i] > MH[i-1]; bear = MH[i] < 0 or MH[i] < MH[i-1]
        down = (l[i-3] < l[i-4] and l[i-4] < l[i-5] and l[i-2] > l[i-3] and l[i-1] > l[i-2] and v[i-3] > WV[i-3])
        sup = (o[i-3] if c[i-3] >= o[i-3] else c[i-3]) if down else LOW6[i]
        botsup = c[i] > sup and c[i] > c[i-1] and r1 > r2 + 10
        bigdrop = R[i] + 8 < R[i-1] and c[i] > W48[i]
        oc, hl = abs(o[i-1]-c[i-1]), abs(h[i-1]-l[i-1])
        ochl = (oc-hl)/hl if hl > 0 else 0.0
        is_br = (o[i-2] < c[i-2] and o[i-1] < c[i-1] and c[i] < o[i] and c[i-2] < c[i-1]
                 and c[i-1] > c[i] and ochl < 0.1 and l[i-3] < l[i-2] < l[i-1])
        if is_br: cnt_out += 1
        is_out = False
        if cnt_out > 2: is_out = True; cnt_out = 0
        rng = h[i]-l[i]; cl_pos = (c[i]-l[i])/rng if rng > 0 else 0.5
        pb = (c[i-1] > c[i-2] and c[i-2] > c[i-3] and cl_pos < 0.30 and c[i] < c[i-1] and c[i] < o[i-1]) or \
             (c[i-1] > c[i-2] and c[i-2] > c[i-3] and cl_pos < 0.30 and W11[i] < W48[i] and c[i] < c[i-1] and c[i] < o[i-1])
        if pos is None:
            if last_t is not None and (ts[i]-last_t)/np.timedelta64(1,'m') <= 2: continue
            d = 0; stop = None; lg = None
            if rsi_up and up10 and botsup and c[i] > W48[i] and c[i] > W200[i]: d, stop, lg = 1, l[i]-5.0, "C2"
            elif rsi_up and up10 and botsup and (c[i] > W48[i] or c[i] > W200[i]): d, stop, lg = 1, l[i]-5.0, "C1"
            elif rsi_up and up10 and xup and c[i] > W11[i] and c[i] > W48[i] and bull: d, stop, lg = 1, l[i]-A[i], "C3"
            elif rsi_up and up10 and W11[i] > W48[i] and c[i] > W11[i] and c[i] > c[i-1] and bull: d, stop, lg = 1, l[i]-A[i], "C4"
            elif rsi_dn and dn10 and is_out and bigdrop and c[i] < W11[i] and c[i] < W48[i]: d, stop, lg = -1, h[i]+5.0, "P2"
            elif rsi_dn and dn10 and is_out and bigdrop: d, stop, lg = -1, h[i]+5.0, "P1"
            elif rsi_dn and dn10 and xdn and c[i] < W11[i] and c[i] < W48[i] and bear: d, stop, lg = -1, h[i]+A[i], "P3"
            elif rsi_dn and dn10 and W11[i] < W48[i] and c[i] < W48[i] and c[i] < c[i-1] and bear: d, stop, lg = -1, h[i]+A[i], "P4"
            if d != 0 and abs(c[i]-stop) > 0:
                pos = dict(d=d, E=c[i], stop=stop, risk=abs(c[i]-stop), i0=i, logic=lg); last_t = ts[i]
        else:
            d, E = pos["d"], pos["E"]
            if d == 1:
                if pos["stop"] + A[i] < c[i]: pos["stop"] = c[i] - A[i]
                ex = ((not rsi_up and is_out and bigdrop and c[i] < W11[i] and c[i] < W48[i])
                      or (xdn and c[i] < W11[i] and c[i] < W48[i]) or bigdrop or pb or is_out)
                sl = (not rsi_up) and pos["stop"] > c[i] and (not up5)
            else:
                if pos["stop"] - A[i] > c[i]: pos["stop"] = c[i] + A[i]
                ex = ((not rsi_dn and xup and c[i] > W11[i] and c[i] > W48[i])
                      or (botsup and c[i] > W48[i] and c[i] > W200[i]) or (botsup and (c[i] > W48[i] or c[i] > W200[i])) or botsup)
                sl = (not rsi_dn) and pos["stop"] < c[i] and (not dn5)
            if ex or sl or i == n-1:
                r = d*(c[i]-E)/pos["risk"]
                out.append(dict(day=str(pd.Timestamp(ts[i]).date()), dir=d, logic=pos["logic"], entry=float(E),
                                stop=float(pos["stop"]), risk=float(pos["risk"]), res="TARGET" if r > 0 else "STOP",
                                r=float(r), hold_min=int((ts[i]-ts[pos["i0"]])/np.timedelta64(1,'m')),
                                fill_hrs=0.0, target_r=1.0, depth=0.0, exit_kind="signal" if ex else "stop"))
                pos = None; last_t = ts[i]
    return pd.DataFrame(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    BASE = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18/data/reference"
    TAPES = [("2023-26","nq_live_tape.parquet"),("2020-22","nq_2020_2022_1m.parquet"),("2017-19","nq_2017_2019_1m.parquet")]
    for tf in (1,5,15):
        print(f"\n================ {tf}-MINUTE ================")
        print(f"  {'tape':<9}{'variant':<12}{'trades':>8}{'R/trade':>10}{'net R':>9}{'win':>7}{'medHold':>9}{'maxDD':>9}{'@1.25pt':>10}")
        for lab, f in TAPES:
            b = load(f"{BASE}/{f}", tf)
            for fix, vname in ((False,"as-written"),(True,"bug-fixed")):
                tr = run(b, fix)
                if len(tr) == 0: print(f"  {lab:<9}{vname:<12}   no trades"); continue
                tr["netr"] = tr.r - 0.5/tr.risk
                day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
                print(f"  {lab:<9}{vname:<12}{len(tr):>8}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+9.0f}"
                      f"{(tr.r>0).mean():>7.1%}{tr.hold_min.median():>9.0f}{dd:>+9.1f}{(tr.r-1.25/tr.risk).mean():>+10.4f}")
                with gzip.open(f"{a.out}_{tf}m_{lab}_{'fix' if fix else 'asis'}.jsonl.gz","wt") as fh:
                    for _,t in tr.iterrows(): fh.write(json.dumps({q:(v.item() if hasattr(v,'item') else v) for q,v in t.items()})+"\n")
