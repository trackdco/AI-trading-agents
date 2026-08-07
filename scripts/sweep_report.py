import numpy as np, pandas as pd, sys, glob
sys.path.insert(0,'.')
from scripts import funded_book as fb

V = fb.load_book('fit')
def book_with(oc):
    """Swap the canon book's exits/dollars for a variant's and run the funded sim."""
    W = V.drop(columns=['dollars_1lot','exit_ts'], errors='ignore').merge(
        oc[['ts','direction','dollars_1lot','exit_ts','R','exit_reason']],
        on=['ts','direction'], how='inner')
    W['exit'] = pd.to_datetime(W.exit_ts, format='mixed', utc=True)
    W = W.sort_values('fill', kind='mergesort')
    B = fb.run(W, 'lucid')
    D = B.groupby('day').pl.sum(); cum = D.cumsum()
    Rr = W.dollars_1lot/(W.risk*20)
    return {'n': len(W), 'WR%': round((W.dollars_1lot>0).mean()*100),
            'meanR': round(Rr.mean(),3),
            'win meanR': round(Rr[W.dollars_1lot>0].mean(),2),
            '1lot $': round(W.dollars_1lot.sum()),
            'funded net': round(B.pl.sum()),
            'worst day': round(D.min()), 'maxDD': round((cum.cummax()-cum).max())}

rows = {}
base = pd.read_parquet('output/l2_outcomes_fit.parquet')
base = base[base.status=='outcome'].drop_duplicates(['ts','direction'])
rows['50% (SHIPPED)'] = book_with(base)
for f in sorted(glob.glob('output/partial_sweep_fit_*.parquet')):
    pct = f.split('_')[-1].split('.')[0]
    oc = pd.read_parquet(f)
    rows[f'{pct}%'] = book_with(oc)
T = pd.DataFrame(rows).T
print(T.to_string())
