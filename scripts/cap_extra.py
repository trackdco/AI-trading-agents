import sys
from datetime import time as dtime
sys.path.insert(0, "/home/user/AI-trading-agents")
import pandas as pd
from scripts.cap_sweep import load, run

df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
allt = (load("output/triggers_feb_ob.csv") + load("output/triggers_marjul_ob.csv")
        + load("output/triggers_junjul_ob.csv"))
dt = pd.read_csv("output/amt_daytypes.csv")
dtv = dt[dt.type != "unknown"].reset_index(drop=True)
share = dtv.type.eq("imbalanced").rolling(20, min_periods=5).mean()
war = {d for d, s in zip(dtv.day, share) if pd.notna(s) and s >= 0.5}

def rep(J, label):
    print(f"{label:34s} {len(J)}t ${J.dollars.sum():+7,.0f}  win {J.win.mean()*100:.0f}%", flush=True)

print("=== POST-OPEN VARIANTS (09:40 start) ===", flush=True)
rep(run(allt, df, war, 2, dtime(10,15), True, win_start=dtime(9,40)), "post 09:40-10:15 cap=2 (ref)")
rep(run(allt, df, war, 2, dtime(10,30), True, win_start=dtime(9,40)), "post 09:40-10:30 cap=2 (extend)")
rep(run(allt, df, war, 3, dtime(10,15), True, win_start=dtime(9,40)), "post 09:40-10:15 cap=3")
rep(run(allt, df, war, 2, dtime(11,0),  True, win_start=dtime(9,40)), "post 09:40-11:00 cap=2 (full RTH)")
print("DONE", flush=True)
