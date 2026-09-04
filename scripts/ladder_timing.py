"""Days per rung of the scaling ladder. Union armed 2020-26 daily $ at 1 micro (after 0.5pt cost), 5-day block bootstrap,
$2,000 EOD-trailing floor locking at breakeven, engine day cap -$1,000-per-8-micros scaled to size. 10,000 runs each."""
import numpy as np, importlib.util, sys
spec=importlib.util.spec_from_file_location("mc","monte_carlo.py")
src=open("monte_carlo.py").read().split("rng=np.random")[0]  # reuse the loader only
exec(src)
rng=np.random.default_rng(11); BL=5; NS=10000
def draw(k):
    n=len(lit); nb=int(np.ceil(k/BL)); s=rng.integers(0,n-BL+1,size=(NS,nb))
    return lit[(s[:,:,None]+np.arange(BL)[None,None,:]).reshape(NS,-1)[:,:k]]
def stage(micros, target, min_days, edge=1.0, cap_per8=1000, horizon=200):
    X=draw(horizon); X=(X-(1-edge)*lit.mean())*micros; X=np.maximum(X,-cap_per8*micros/8-300*micros/8)  # cap + open-risk slop
    cum=np.concatenate([np.zeros((NS,1)),X.cumsum(1)],1); pk=np.maximum.accumulate(cum,axis=1); floor=np.minimum(pk-2000,0)
    dead=(cum<=floor); hit=(cum>=target)&(np.arange(horizon+1)[None,:]>=min_days)
    d_day=np.where(dead.any(1),dead.argmax(1),10**6); h_day=np.where(hit.any(1),hit.argmax(1),10**6)
    ok=h_day<d_day; days=h_day[ok]
    return ok.mean(), (np.median(days) if ok.any() else None), (np.percentile(days,90) if ok.any() else None)
for edge in (1.0,0.5):
    print(f"\n=== real edge = {int(edge*100)}% of backtest ===")
    for label,m,t,md in (("eval @8 micros -> +$3,000",8,3000,1),("funded @4 micros -> floor locks (+$2,000)",4,2000,1),
                         ("funded @4 micros -> first payout (+$4,000, >=10d)",4,4000,10),("funded @8 micros -> a $4,000 payout cycle",8,4000,10),
                         ("funded @8 micros -> a $10,000 cycle",8,10000,10)):
        p,med,p90=stage(m,t,md,edge)
        print(f"  {label:<52} pass {p:6.1%}   median {med if med is None else int(med):>3} days   slow-90% {p90 if p90 is None else int(p90):>3} days")
