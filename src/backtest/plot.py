"""Equity curve + by-year for the first-pass backtest (diagnostic, unvalidated)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

t = pd.read_csv("output/trades.csv").sort_values("ts").reset_index(drop=True)
t["date"] = pd.to_datetime(t["date"])
t["eq"] = t["r"].cumsum()
t["peak"] = t["eq"].cummax()
t["dd"] = t["eq"] - t["peak"]

fig, ax = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[3, 1], sharex=True)
fig.patch.set_facecolor("#0f1419")
for a in ax:
    a.set_facecolor("#0f1419")
    a.tick_params(colors="#9aa5b1"); a.grid(alpha=.12, color="#9aa5b1")
    for s in a.spines.values(): s.set_color("#2a2f36")

ax[0].plot(t["date"], t["eq"], color="#4c9aff", lw=1.4)
ax[0].axhline(0, color="#6b7280", lw=.8, ls="--")
ax[0].set_ylabel("Cumulative R", color="#e5e9f0")
ax[0].set_title("NQ strategy — FIRST-PASS mechanical backtest (UNVALIDATED, pre-gate)\n"
                f"{len(t)} trades  |  Jan 2023–Jan 2026  |  net +{t['eq'].iloc[-1]:.0f}R  "
                f"|  win {(t['r']>0).mean()*100:.0f}%  |  PF 1.01  |  maxDD {t['dd'].min():.0f}R",
                color="#e5e9f0", fontsize=11, loc="left")
ax[1].fill_between(t["date"], t["dd"], 0, color="#f2555a", alpha=.55)
ax[1].set_ylabel("Drawdown R", color="#e5e9f0")
ax[1].set_xlabel("Date", color="#e5e9f0")
plt.tight_layout()
plt.savefig("output/equity_curve.png", dpi=130, facecolor=fig.get_facecolor())
print("saved output/equity_curve.png")
