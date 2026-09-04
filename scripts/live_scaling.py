"""Same rule with a hard size cap (40 micros = 4 minis) and step-up only after a new high held >=10 days since last step. Start $25k."""
import numpy as np
exec(open("monte_carlo.py").read().split("rng=np.random")[0])
rng=np.random.default_rng(31); BL=5; NS=10000; H=250; CAP=40
n=len(lit); nb=int(np.ceil(H/BL)); s=rng.integers(0,n-BL+1,size=(NS,nb)); IDX=(s[:,:,None]+np.arange(BL)[None,None,:]).reshape(NS,-1)[:,:H]
def run(E0,B,edge,extra_cost=36.0):
    X=lit[IDX]-(1-edge)*lit.mean()-extra_cost; X=np.maximum(X,-125.0)
    E=np.full(NS,float(E0)); pk=E.copy(); m=np.minimum(np.maximum(np.floor(E/B),1),CAP); dd=np.zeros(NS); last=np.zeros(NS); tcap=np.full(NS,999)
    for t in range(H):
        E=E+X[:,t]*m; pk=np.maximum(pk,E); dd=np.maximum(dd,1-E/pk)
        tgt=np.minimum(np.maximum(np.floor(E/B),1),CAP)
        canup=(E>=pk)&(t-last>=10)&(tgt>m); m=np.where(canup,m+1,m); last=np.where(canup,t,last)  # one step at a time
        down=tgt<m; m=np.where(down,tgt,m)
        tcap=np.where((m>=CAP)&(tcap==999),t,tcap)
    return np.mean(dd>0.25), np.median(dd), np.percentile(dd,95), np.median(E-E0), np.median(tcap[tcap<999]) if (tcap<999).any() else None
print(f"{'$/micro':>8}{'edge':>6} | {'P(DD>25%)':>10}{'DD med':>8}{'DD bad5%':>9}{'year P&L med':>14}{'days to 40 cap':>15}")
for B in (2500,4000,6000,8000,10000):
    for e in (1.0,0.5,0.25):
        a,d,d95,pl,tc=run(25000,B,e); print(f"{B:>8,}{int(e*100):>5}% | {a:>10.1%}{d:>8.1%}{d95:>9.1%}{pl:>14,.0f}{'' if tc is None else int(tc):>15}")
    print()
