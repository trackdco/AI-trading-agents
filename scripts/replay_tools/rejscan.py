"""SUPPLEMENTARY candidate scan: his actual grammar (T5/T15) -
   rejection off a key level -> closure through the own BB MA stacked with another level -> retest.
   two_level_check only pairs a rejection with a closure in the SAME candle, and its sequential
   logic is MA-first-only. This surfaces REJECTION-FIRST sequences. Orchestrator tool."""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import pandas as pd
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands

WINDOWS = {"LONDON": ("03:00", "04:59"), "NY_PRE": ("08:00", "09:29"), "NY_AM": ("09:30", "11:00")}

def scan(sess_day, tf=2, lookback=4):
    nxt = (pd.Timestamp(sess_day) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    b = load_bars(); b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b = b.set_index("mi").sort_index()[["open","high","low","close","volume"]]
    day = b[f"{sess_day} 18:00":f"{nxt} 13:00"]
    vb = vwap_bands(day)
    ma,_ = bb_ma_asof(day, tf); ma15,_ = bb_ma_asof(day, 15); ma60,_ = bb_ma_asof(day, 60)
    bars = day.resample(f"{tf}min", label="left", closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()
    bars = bars[(bars.index >= f"{nxt} 02:00") & (bars.index <= f"{nxt} 11:00")]
    idx = list(bars.index)
    out = []
    for i, t in enumerate(idx):
        u = t + pd.Timedelta(minutes=tf-1)
        if u not in ma.index: continue
        r = bars.loc[t]; m = float(ma.loc[u])
        thru = (r.open - m) * (r.close - m) < 0
        if not thru: continue
        direction = "DOWN" if r.close < m else "UP"
        # look back for a rejection of a key level in the SAME direction
        rejections = []
        for j in range(max(0, i-lookback), i):
            tj = idx[j]; uj = tj + pd.Timedelta(minutes=tf-1)
            if uj not in vb.index: continue
            rj = bars.loc[tj]
            lv = {"vwap": float(vb.loc[uj,"vwap"]), "vwap_p1": float(vb.loc[uj,"vwap_p1"]),
                  "vwap_m1": float(vb.loc[uj,"vwap_m1"]), "vwap_p2": float(vb.loc[uj,"vwap_p2"]),
                  "vwap_m2": float(vb.loc[uj,"vwap_m2"]), "bb_ma_15m": float(ma15.loc[uj])}
            if uj in ma60.index and not pd.isna(ma60.loc[uj]): lv["bb_ma_60m"] = float(ma60.loc[uj])
            for name, price in lv.items():
                if direction == "DOWN" and rj.high > price >= rj.close and rj.open <= price:
                    rejections.append({"level":name,"price":round(price,2),"at":tj.strftime("%H:%M"),
                                       "wick_beyond":round(float(rj.high-price),2)})
                if direction == "UP" and rj.low < price <= rj.close and rj.open >= price:
                    rejections.append({"level":name,"price":round(price,2),"at":tj.strftime("%H:%M"),
                                       "wick_beyond":round(float(price-rj.low),2)})
        if not rejections: continue
        # second level closed through on the signal candle itself?
        uu = t + pd.Timedelta(minutes=tf-1); second = []
        if uu in vb.index:
            lv = {"vwap": float(vb.loc[uu,"vwap"]), "vwap_p1": float(vb.loc[uu,"vwap_p1"]),
                  "vwap_m1": float(vb.loc[uu,"vwap_m1"]), "bb_ma_15m": float(ma15.loc[uu])}
            for name, price in lv.items():
                if (r.open - price) * (r.close - price) < 0: second.append(name)
        dec = (t + pd.Timedelta(minutes=tf)).strftime("%H:%M")
        win = next((w for w,(a,z) in WINDOWS.items() if a <= dec <= z), None)
        out.append({"candle_start": t.strftime("%H:%M"), "decision_minute": dec, "window": win,
                    "tf": f"{tf}m", "direction": direction, "own_ma": round(m,2),
                    "close": float(r.close), "open": float(r.open), "vol": int(r.volume),
                    "rejections": rejections[:3], "second_level_same_candle": second})
    return out

if __name__ == "__main__":
    sd = sys.argv[1]; tf = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    res = [c for c in scan(sd, tf) if c["window"]]
    print(f"REJECTION-FIRST candidates, session-day {sd}, {tf}m, inside entry windows: {len(res)}")
    for c in res:
        rj = "; ".join(f"{x['level']}@{x['at']}(+{x['wick_beyond']})" for x in c["rejections"])
        print(f"  {c['decision_minute']} {c['window']:7s} {c['direction']:4s} own_ma {c['own_ma']:9.2f} C{c['close']:9.2f} vol{c['vol']:>6} | rejected: {rj} | same-candle 2nd: {c['second_level_same_candle']}")
