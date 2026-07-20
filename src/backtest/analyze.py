"""Summarize backtest results + rough Feb-2026 calibration vs the 28 hand trades."""
import numpy as np, pandas as pd


def summary(t):
    t = t.copy()
    t["year"] = pd.to_datetime(t["date"]).dt.year
    n = len(t)
    wins = (t["r"] > 0).sum(); losses = (t["r"] < 0).sum(); scratch = (t["r"] == 0).sum()
    net_r = t["r"].sum()
    exp = t["r"].mean()
    aw = t.loc[t.r > 0, "r"].mean() if wins else 0
    al = t.loc[t.r < 0, "r"].mean() if losses else 0
    pf = t.loc[t.r > 0, "r"].sum() / abs(t.loc[t.r < 0, "r"].sum()) if losses else np.inf
    # equity/drawdown in R
    eq = t.sort_values("ts")["r"].cumsum()
    dd = (eq - eq.cummax()).min()
    print("="*70)
    print(f"TRADES: {n}   WINS: {wins}  LOSSES: {losses}  SCRATCH: {scratch}")
    print(f"WIN RATE: {wins/n*100:.1f}%   (ex-scratch {wins/max(wins+losses,1)*100:.1f}%)")
    print(f"NET: {net_r:+.1f}R    EXPECTANCY: {exp:+.3f}R/trade")
    print(f"AVG WIN: {aw:+.2f}R   AVG LOSS: {al:+.2f}R   PROFIT FACTOR: {pf:.2f}")
    print(f"MAX DRAWDOWN: {dd:.1f}R   BEST: {t.r.max():+.2f}R  WORST: {t.r.min():+.2f}R")
    print("="*70)
    print("\nBY YEAR:")
    by = t.groupby("year").agg(trades=("r","size"), win_rate=("r",lambda s:(s>0).mean()*100),
                               net_R=("r","sum"), exp_R=("r","mean"))
    print(by.round(2).to_string())
    print("\nBY DIRECTION / TF / HTF:")
    for col in ["direction","tf","htf","confluence","with_trend","reason"]:
        g = t.groupby(col).agg(n=("r","size"), win=("r",lambda s:(s>0).mean()*100),
                               netR=("r","sum"), expR=("r","mean")).round(2)
        print(f"\n[{col}]\n{g.to_string()}")


def calibrate(t):
    ref = pd.read_csv("data/reference/feb2026_hand_log.csv")
    ref["d"] = pd.to_datetime(ref["Date"]).dt.date
    eng = t.copy(); eng["date"] = pd.to_datetime(eng["date"]).dt.date
    feb = eng[(eng.date >= pd.Timestamp("2026-02-01").date()) &
              (eng.date <= pd.Timestamp("2026-02-28").date())]
    print("\n" + "="*70)
    print("FEB-2026 CALIBRATION (rough — data ends 2026-01-30, so likely EMPTY)")
    print(f"reference hand trades: {len(ref)}   engine Feb trades: {len(feb)}")
    print("="*70)


if __name__ == "__main__":
    t = pd.read_csv("output/trades.csv")
    if len(t) == 0:
        print("No trades produced."); raise SystemExit
    summary(t)
    calibrate(t)
