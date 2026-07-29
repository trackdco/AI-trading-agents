import sys, re
import pandas as pd, numpy as np
sys.path.insert(0,'.')
from scripts.canon_mechanical import build_canon

# ---------- Angus's Feb hand log (exact times, ET) ----------
fb = pd.read_csv('data/reference/feb2026_hand_log.csv')
fb.columns=[c.strip() for c in fb.columns]
fb['time']=fb['Entry Time'].astype(str).str.strip()
fb['date']=pd.to_datetime(fb['Date'])
fb['et']=pd.to_datetime(fb['date'].dt.strftime('%Y-%m-%d')+' '+fb['time'])
fb['direction']=fb['Direction'].str.strip().str.lower()
fb['R']=pd.to_numeric(fb['R Multiple'],errors='coerce')
fb['pnl']=pd.to_numeric(fb['P&L $'],errors='coerce')
fb['risk']=pd.to_numeric(fb['Risk $'],errors='coerce')
fb['pattern']=fb['Pattern'].astype(str).str.strip()
fb=fb[['et','direction','R','pnl','risk','pattern']].copy(); fb['src']='FEB(exact)'

# ---------- Angus's Mar log (times +/-15-25 min) ----------
mr = pd.read_csv('data/reference/mar2026_hand_log.csv',comment='#')
mr['et']=pd.to_datetime(mr['Date']+' '+mr['Entry Time'])
mr['direction']=mr['Direction'].str.strip().str.lower()
mr['pnl']=pd.to_numeric(mr['PNL Points'],errors='coerce')*20   # 1-mini $ equiv
mr['R']=np.nan; mr['risk']=np.nan; mr['pattern']='?'
mr=mr[['et','direction','R','pnl','risk','pattern']].copy(); mr['src']='MAR(±25m)'

H=pd.concat([fb,mr],ignore_index=True).sort_values('et').reset_index(drop=True)

# ---------- canon candidates, leakage-clean, ALL rows w/ gate columns ----------
T=pd.read_parquet('output/trade_matrix.parquet')
T2=T.copy(); T2['conf_PM']=T2['pm_sofar_conf']
ny=build_canon(T2)                       # no news gate: diagnose the strategy layer itself
ny['cand_et']=pd.to_datetime(ny.fill,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
ny=ny.sort_values('cand_et').reset_index(drop=True)

# reconstruct WHY size==0
lad=np.select([ny.score<=2,ny.score==3,ny.score==4,ny.score==5],[0,.5,1,1.5])
ny['ladder']=lad
gold_live=(ny.win_=='gold')
ny['kill']=''
ny.loc[(ny['size']==0)&(ny.score<=2),'kill']='score<3'
ny.loc[(ny['size']==0)&(ny.score>=3)&gold_live&(ny.Q<=1),'kill']='gold Q<=1'
ny.loc[(ny['size']==0)&(ny.score>=3)&(ny.kill=='')&(ny.nth>=2)&(ny.score<4),'kill']='nth>=2 needs score>=4'
ny.loc[(ny['size']==0)&(ny.kill==''),'kill']='other'

# ---------- champion trigger cache (raw detector) ----------
tg=pd.concat([pd.read_csv('output/triggers_feb_ob.csv'),pd.read_csv('output/triggers_marjul_ob.csv')],ignore_index=True)
tg['tg_et']=pd.to_datetime(tg.ts,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
tg=tg.sort_values('tg_et').reset_index(drop=True)

def nearest(df,tcol,when,direction,tol_min):
    d=df[(df[tcol].dt.date==when.date())&(df.direction==direction)]
    if not len(d): return None
    i=(d[tcol]-when).abs().idxmin()
    if abs((df.loc[i,tcol]-when).total_seconds())<=tol_min*60: return i
    return None

rows=[]
for _,h in H.iterrows():
    tol=6 if h.src.startswith('FEB') else 25
    ci=nearest(ny,'cand_et',h.et,h.direction,tol)
    ti=nearest(tg,'tg_et',h.et,h.direction,tol)
    hm=h.et.hour*60+h.et.minute
    win=('pre' if 480<=hm<570 else '09:30-40' if 570<=hm<580 else 'gold' if 580<=hm<615 else '10:15+' if hm>=615 else 'early')
    if ci is not None:
        c=ny.loc[ci]
        status='TAKEN' if c['size']>0 else f"KILLED: {c['kill']}"
        det=f"score={c.score:.0f} W={c.W} F={c.F} Tp={c.Tp} G={c.G} C={c.C} Q={c.Q:.0f} nth={c.nth}"
    elif ti is not None:
        status='DETECTOR-ONLY (not in trade_matrix)'
        det=f"kind={tg.loc[ti,'kind']} pat={tg.loc[ti,'pattern']}"
    else:
        status='NOT DETECTED AT ALL'
        det=''
    rows.append(dict(src=h.src,et=h.et,dirn=h.direction,win=win,R=h.R,pnl=h.pnl,pat=h.pattern,status=status,detail=det))

A=pd.DataFrame(rows)
pd.set_option('display.width',250)
print(A.to_string(index=False,max_colwidth=60))
print()
print('======== BUCKET SUMMARY (his $ P&L; Mar = points x $20) ========')
A['bucket']=A.status.str.split(':').str[0]
g=A.groupby('bucket').agg(n=('pnl','size'),his_pnl=('pnl','sum'),avg_R=('R','mean'))
print(g.to_string())
print()
print('by window:')
print(A.groupby(['win','bucket']).agg(n=('pnl','size'),his_pnl=('pnl','sum')).to_string())
A.to_csv('output/capture_audit_handlog.csv',index=False)
