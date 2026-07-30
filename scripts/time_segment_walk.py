import sys
import numpy as np, pandas as pd
sys.path.insert(0,'.')
from scripts import funded_book as fb
from scripts.build_l2_outcomes import load_bars

NY='America/New_York'
bars = load_bars()
bars['mi'] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
B = bars.set_index('mi').sort_index()
BDAY = B.index.strftime('%Y-%m-%d')
CHECKS=[2,3,5,8,10]

def walk(span):
    V = fb.load_book(span)
    O = pd.read_parquet(f'output/l2_outcomes_{span}.parquet')
    O = O[O.status=='outcome'].drop_duplicates(['day','ts','direction','risk'])
    J = V.merge(O[['day','ts','direction','risk','entry','fill_ts','exit_ts']],
                on=['day','ts','direction','risk'], how='inner', suffixes=('','_o'))
    recs=[]
    for day, g in J.groupby('day', sort=True):
        db = B[BDAY==day]
        h,lo,cl = db.high.to_numpy(), db.low.to_numpy(), db.close.to_numpy()
        mi = db.index
        for r in g.itertuples():
            s = 1 if r.direction=='long' else -1
            entry = float(r.entry_o); risk=float(r.risk)
            fill = pd.Timestamp(r.fill_ts); ex = pd.Timestamp(r.exit_ts)
            i0 = int(np.searchsorted(mi, fill, side='left'))
            held = int((ex - fill).total_seconds()//60)
            rec = {'day':day,'sess':r.sess,'era':day[:4],'span':span,
                   'win': r.dollars_1lot>0, 'R': None, 'held':held,
                   'dollars_1lot': float(r.dollars_1lot), 'tier': float(r.tier)}
            for t in CHECKS:
                i = i0+t-1
                if i < len(cl) and held > t:
                    fav = s*((h if s==1 else lo)[i0:i+1]-entry)/risk
                    adv = s*((lo if s==1 else h)[i0:i+1]-entry)/risk
                    rec[f'open{t}']=True
                    rec[f'r{t}']= s*(cl[i]-entry)/risk
                    rec[f'mf{t}']= float(fav.max())      # MFE so far
                    rec[f'ma{t}']= float(adv.min())      # MAE so far
                else:
                    rec[f'open{t}']=False
                    rec[f'r{t}']=rec[f'mf{t}']=rec[f'ma{t}']=np.nan
            recs.append(rec)
    D = pd.DataFrame(recs)
    # final R in risk units for book math: dollars_1lot/(risk*20)... use dollars sign for win; R from V8 join not needed
    return D

for span in ['fit','holdout']:
    D = walk(span)
    D.to_parquet(f'output/time_segments2_{span}.parquet', index=False)
    print(span, len(D), 'trades walked')
