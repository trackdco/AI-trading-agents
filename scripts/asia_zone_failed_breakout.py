#!/usr/bin/env python3
"""Asia-zone failed breakout reverting to the respected VWAP band envelope.
Rules frozen in docs/PREREG-asia-zone-failed-breakout.md. Exits from the bar AFTER entry."""
import argparse, gzip, json, numpy as np, pandas as pd
TICK = 0.25

def load(path):
    b = pd.read_parquet(path); t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close","volume"]].sort_index()
    b["sess"] = (b.index - pd.Timedelta(hours=18)).normalize()
    return b

def session_frame(s):
    """5m OHLC plus live VWAP/sigma sampled at each 5m bar's last 1m bar."""
    tp = (s.high + s.low + s.close) / 3.0; v = s.volume.clip(lower=0).astype(float)
    pv, vv, p2 = (tp*v).cumsum(), v.cumsum(), (tp*tp*v).cumsum()
    vwap = pv / vv.replace(0, np.nan)
    sd = np.sqrt((p2/vv.replace(0, np.nan) - vwap**2).clip(lower=0))
    m = s.resample("5min").agg(open=("open","first"), high=("high","max"), low=("low","min"), close=("close","last")).dropna()
    m["vwap"] = vwap.resample("5min").last().reindex(m.index)
    m["sd"] = sd.resample("5min").last().reindex(m.index)
    c = m.close
    ma = c.rolling(20).mean(); sdv = c.rolling(20).std(ddof=0)
    m["bb_u"], m["bb_l"] = ma + 2*sdv, ma - 2*sdv
    return m.dropna(subset=["vwap","sd"])

def run(bars, target, cost=0.5):
    out = []
    for day, s in bars.groupby("sess"):
        if len(s) < 600: continue
        m = session_frame(s)
        if len(m) < 100: continue
        t0 = pd.Timestamp(day) + pd.Timedelta(hours=18)
        end = m.index + pd.Timedelta(minutes=5)
        win = (end > t0) & (end <= t0 + pd.Timedelta(hours=7))
        w = m[win]
        if len(w) < 60: continue
        k = None
        for kk in (1, 2, 3):
            up, lo = w.vwap + kk*w.sd, w.vwap - kk*w.sd
            inside = ((w.close <= up) & (w.close >= lo)).mean()
            touch = (((w.high >= up) | (w.low <= lo)) & (w.close <= up) & (w.close >= lo)).sum()
            if inside >= 0.90 and touch >= 3: k = kk; break
        if k is None: continue
        act = m[(end > t0 + pd.Timedelta(hours=7)) & (end <= t0 + pd.Timedelta(hours=22))]
        if len(act) < 5: continue
        c, h, l = act.close.values, act.high.values, act.low.values
        bu, bl, vw, sd = act.bb_u.values, act.bb_l.values, act.vwap.values, act.sd.values
        side = 0; ext = np.nan; sig = None
        for i in range(len(act)):
            if np.isnan(bu[i]): continue
            if side == 0:
                if c[i] > bu[i]: side, ext = 1, h[i]
                elif c[i] < bl[i]: side, ext = -1, l[i]
            else:
                still = (c[i] > bu[i]) if side == 1 else (c[i] < bl[i])
                if still:
                    ext = max(ext, h[i]) if side == 1 else min(ext, l[i])
                else:
                    outside_zone = (c[i] > vw[i] + k*sd[i]) if side == 1 else (c[i] < vw[i] - k*sd[i])
                    if outside_zone: sig = (i, -side, ext)
                    side = 0; ext = np.nan
                    if sig: break
        if sig is None: continue
        i, d, ext = sig
        E = c[i]; stop = ext + TICK*(1 if d == -1 else -1); risk = abs(E - stop)
        if risk <= 0: continue
        ts5 = act.index.values
        # exits scanned on 1m bars from the bar AFTER the signal candle closes
        sfull = s[s.index >= ts5[i] + np.timedelta64(5,'m')]
        if len(sfull) < 2: continue
        H1, L1, C1 = sfull.high.values, sfull.low.values, sfull.close.values
        tpv = (sfull.high+sfull.low+sfull.close)/3.0; vv = sfull.volume.clip(lower=0).astype(float)
        vw_live = act.vwap.reindex(sfull.index, method="ffill").values
        sd_live = act.sd.reindex(sfull.index, method="ffill").values
        vw_live = pd.Series(vw_live).ffill().bfill().values; sd_live = pd.Series(sd_live).ffill().bfill().values
        res, r = "FLAT", None
        for q in range(len(sfull)):
            if target == "NEAR":  tgt = vw_live[q] + k*sd_live[q] if d == -1 else vw_live[q] - k*sd_live[q]
            elif target == "VWAP": tgt = vw_live[q]
            else:                  tgt = vw_live[q] - k*sd_live[q] if d == -1 else vw_live[q] + k*sd_live[q]
            hit_s = (H1[q] >= stop) if d == -1 else (L1[q] <= stop)
            hit_t = (L1[q] <= tgt) if d == -1 else (H1[q] >= tgt)
            if hit_s: res, r = "STOP", -1.0; break
            if hit_t: res, r = "TARGET", abs(tgt - E)/risk; break
        if r is None: r = d*(C1[-1] - E)/risk
        out.append(dict(day=str(pd.Timestamp(day).date()), t_sig=str(pd.Timestamp(ts5[i]) + pd.Timedelta(minutes=5)),
                        dir=int(d), k=int(k), entry=float(E), stop=float(stop),
                        risk=float(risk), res=res, r=float(r), hold_min=int(q+1), fill_hrs=0.0,
                        target_r=float(abs(r)) if res=="TARGET" else 1.0, depth=0.0))
    return pd.DataFrame(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True); a = ap.parse_args()
    bars = load(a.bars); nd = bars.sess.nunique()
    print(f"\n{a.label}  ({nd:,} sessions)")
    print(f"  {'target':<8}{'trades':>8}{'/sess':>7}{'R/trade':>10}{'net R':>9}{'win':>7}{'medRR':>7}{'maxDD':>8}{'medRisk':>9}{'k=1/2/3':>12}")
    for tg in ("NEAR","VWAP","FAR"):
        tr = run(bars, tg)
        if len(tr) == 0: print(f"  {tg:<8}   no trades"); continue
        tr["netr"] = tr.r - 0.5/tr.risk
        day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
        wins = tr[tr.res=="TARGET"]
        kc = tr.k.value_counts().reindex([1,2,3]).fillna(0).astype(int)
        print(f"  {tg:<8}{len(tr):>8}{len(tr)/nd:>7.2f}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+9.0f}"
              f"{(tr.res=='TARGET').mean():>7.1%}{(wins.r.median() if len(wins) else float('nan')):>7.2f}"
              f"{dd:>+8.1f}{tr.risk.median():>9.1f}{f'{kc[1]}/{kc[2]}/{kc[3]}':>12}")
        with gzip.open(f"{a.out}_{tg}.jsonl.gz","wt") as fh:
            for _, t in tr.iterrows(): fh.write(json.dumps({q:(v.item() if hasattr(v,'item') else v) for q,v in t.items()})+"\n")
