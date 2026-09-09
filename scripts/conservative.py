"""Conservative per-account sizing: death odds in year 1 (floor locks at breakeven, engine day cap scaled), $/day, days to eval and first payout."""
import numpy as np
exec(open("monte_carlo.py").read().split("rng=np.random")[0])
rng=np.random.default_rng(23); BL=5; NS=10000
def draw(k):
    n=len(lit); nb=int(np.ceil(k/BL)); s=rng.integers(0,n-BL+1,size=(NS,nb))
    return lit[(s[:,:,None]+np.arange(BL)[None,None,:]).reshape(NS,-1)[:,:k]]
def sim(m, edge, horizon=250):
    X=(draw(horizon)-(1-edge)*lit.mean())*m; X=np.maximum(X,-1300*m/8)
    cum=np.concatenate([np.zeros((NS,1)),X.cumsum(1)],1); pk=np.maximum.accumulate(cum,axis=1); floor=np.minimum(pk-2000,0)
    dead=(cum<=floor).any(1)
    ev=((cum>=3000).any(1)); evd=np.where(ev,(cum>=3000).argmax(1),999); dd=np.where((cum<=floor).any(1),(cum<=floor).argmax(1),999)
    pay=(cum>=4000)&(np.arange(horizon+1)>=10); payd=np.where(pay.any(1),pay.argmax(1),999)
    return dead.mean(), X.mean(), np.median(evd[evd<dd]) if (evd<dd).any() else None, np.mean(evd<dd), np.median(payd[payd<dd]) if (payd<dd).any() else None, np.mean(payd<dd), np.percentile(X.min(1),50)
print(f"{'micros':>6} {'edge':>5} | {'death/yr':>8} {'$/day':>7} {'worst day(med)':>14} | {'eval pass':>9} {'eval days':>9} | {'1st payout':>10} {'days':>5}")
for m in (1,2,3,4,8):
    for e in (1.0,0.5,0.25):
        d,avg,evd,evp,pd_,pp,wd=sim(m,e)
        print(f"{m:>6} {int(e*100):>4}% | {d:>8.1%} ${avg:>6,.0f} ${wd:>13,.0f} | {evp:>9.1%} {evd if evd is None else int(evd):>9} | {pp:>10.1%} {pd_ if pd_ is None else int(pd_):>5}")
