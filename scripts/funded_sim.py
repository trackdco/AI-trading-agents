#!/usr/bin/env python3
"""FUNDED-ACCOUNT simulator for the London 10-13 book, Scheme A conviction sizing.
$50k account, $2,000 TRAILING drawdown (trails realized-equity peak, LOCKS at $50k start once
you're up $2k -> that lock IS the buffer). Fixed-DOLLAR risk per trade (correct for funded):
P&L_i = netR_i * risk$_i, risk$_i = base$ * conviction_mult (A: confirm 1.0 / else 0.5), base$<=$300 to start.
Tests: (1) historical-path DD per base$, (2) MONTE-CARLO blow probability (order-shuffle + bootstrap),
(3) buffer-based scaling ladder, (4) best static + best ladder. Seeded, reproducible."""
import numpy as np, pandas as pd
rng=np.random.default_rng(7)
D=pd.read_csv("london_conviction_book.csv")
D=D.rename(columns={"cov":"cvcov","ok":"cvok"})
D=D.sort_values(["day","ent"]).reset_index(drop=True)
mult=np.where(D.cvcov&D.cvok,1.0,0.5)          # Scheme A
wR=(D.R.values*mult)                            # weighted R per trade (in units of base$)
START,DDLIM=50000.0,2000.0

def sim(seq_wR, base_fn):
    """base_fn(buffer)->$risk on a 1.0-mult trade; seq_wR already mult-weighted.
    returns (final_pnl, worst_dd_from_peak, blown, min_room)."""
    bal=START; peak=START; worst=0.0; blown=False; minroom=DDLIM
    for w in seq_wR:
        buf=bal-START
        base=base_fn(buf)
        bal+=w*base
        floor=min(peak-DDLIM, START)            # trailing, locks at start
        room_before=bal-floor
        if bal<=floor: blown=True
        peak=max(peak,bal)
        floor=min(peak-DDLIM,START)
        worst=max(worst,peak-bal)
        minroom=min(minroom,bal-floor)
    return bal-START, worst, blown, minroom

# ---- D_R: historical R-drawdown of the weighted series ----
eq=np.cumsum(wR); DR=float((np.maximum.accumulate(eq)-eq).max())
print(f"Scheme A weighted-R series: total {eq[-1]:.1f}R, max R-drawdown = {DR:.2f}R over {len(wR)} trades")
print(f"  => at base$ risk, historical $DD = base$ x {DR:.2f}. To cap $DD<=$2000: base$<= ${2000/DR:.0f}")
print(f"  => to cap $DD<=$1200 (buffer-safe): base$<= ${1200/DR:.0f}\n")

# ---- (1) static base$ grid, historical path ----
print("=== STATIC base$ (historical single path) ===")
print(f"  {'base$':>6}{'maxRisk$':>9}{'finalP&L$':>11}{'worstDD$':>10}{'minRoom$':>9}{'blown':>7}")
for base in (100,150,200,250,300,350,400):
    p,wd,bl,mr=sim(wR, lambda buf,b=base:b)
    print(f"  {base:6d}{base:9d}{p:+11,.0f}{wd:10,.0f}{mr:9,.0f}{'BLOWN' if bl else 'ok':>7}")

# ---- (2) Monte-Carlo blow probability ----
def mc(base_fn, K=8000, mode="shuffle"):
    blow=0; dds=[]; fins=[]
    n=len(wR)
    for _ in range(K):
        if mode=="shuffle": s=wR[rng.permutation(n)]
        else: s=wR[rng.integers(0,n,n)]                 # bootstrap w/ replacement (harsher)
        p,wd,bl,mr=sim(s,base_fn); blow+=bl; dds.append(wd); fins.append(p)
    dds=np.array(dds); fins=np.array(fins)
    return dict(pblow=100*blow/K, dd95=np.percentile(dds,95), ddmed=np.percentile(dds,50),
                finmed=np.percentile(fins,50), fin5=np.percentile(fins,5))
print("\n=== MONTE-CARLO blow probability (8000 paths each) ===")
print(f"  {'base$':>6} | shuffle: P(blow) dd50 dd95 | bootstrap: P(blow) dd95  | med final$")
for base in (100,150,200,250,300):
    sh=mc(lambda b,x=base:x,mode="shuffle"); bo=mc(lambda b,x=base:x,mode="boot")
    print(f"  {base:6d} |   {sh['pblow']:5.1f}% ${sh['ddmed']:5,.0f} ${sh['dd95']:6,.0f} |    {bo['pblow']:5.1f}% ${bo['dd95']:6,.0f} | ${sh['finmed']:+,.0f}")

# ---- (3) scaling ladders (base$ grows with locked buffer) ----
def ladder_conservative(buf):
    if buf< 500: return 150
    if buf<1500: return 225
    if buf<3000: return 300
    if buf<6000: return 450
    return 600
def ladder_aggr(buf):
    if buf< 400: return 200
    if buf<1200: return 300
    if buf<3000: return 450
    return 700
def ladder_tight(buf):
    if buf< 750: return 120
    if buf<2000: return 200
    if buf<4000: return 300
    return 450
print("\n=== SCALING LADDERS (base$ scales with buffer=bal-50k) ===")
for nm,fn in [("conservative",ladder_conservative),("tight",ladder_tight),("aggressive",ladder_aggr)]:
    p,wd,bl,mr=sim(wR,fn); sh=mc(fn,mode="shuffle"); bo=mc(fn,mode="boot")
    print(f"  {nm:12s} histP&L ${p:+8,.0f} histDD ${wd:6,.0f} | MC P(blow) shuf {sh['pblow']:.1f}% boot {bo['pblow']:.1f}%  dd95 ${sh['dd95']:,.0f}  medFinal ${sh['finmed']:+,.0f}")

# ---- (4) the recommended start: fixed $150 base until buffer, MC detail ----
print("\n=== DETAIL: recommended start (tight ladder) ===")
sh=mc(ladder_tight,K=20000,mode="shuffle"); bo=mc(ladder_tight,K=20000,mode="boot")
print(f"  shuffle:  P(blow)={sh['pblow']:.2f}%  medFinal ${sh['finmed']:+,.0f}  5th-pctile ${sh['fin5']:+,.0f}  dd95 ${sh['dd95']:,.0f}")
print(f"  bootstrap:P(blow)={bo['pblow']:.2f}%  medFinal ${bo['finmed']:+,.0f}  5th-pctile ${bo['fin5']:+,.0f}  dd95 ${bo['dd95']:,.0f}")
# contracts illustration
print("\n  micro-contract sizing @ $150 base (confirm) on typical stops:")
for stop in (15,25,36,50,70):
    micros=max(1,round(150/(stop*2))); print(f"    {stop}pt stop -> {micros} MNQ (risk ${micros*stop*2})")