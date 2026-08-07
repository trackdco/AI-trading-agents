import sys
import numpy as np, pandas as pd
sys.path.insert(0,'.')
import scripts.build_l2_outcomes as m
from scripts import funded_book as fb

V = fb.load_book('fit')
key = set(zip(V.ts, V.direction))
C = pd.read_parquet('output/l0_triggers_fit.parquet')
C = C[[ (t,d) in key for t,d in zip(C.ts, C.direction) ]]
C = C.drop_duplicates(['ts','direction'])
print('canon triggers to re-simulate:', len(C), 'of', len(V), 'trades')

base_cfg = m.l2_cfg
results = {}
for pct in [0.0, 25.0, 75.0, 100.0]:
    m.l2_cfg = lambda t_cancel=100000.0, _p=pct: base_cfg(t_cancel).model_copy(
        update={"v8_partial_pct": _p})
    out = m.run(C.copy(), procs=8)
    oc = out[out.status=='outcome'].drop_duplicates(['ts','direction'])
    results[pct] = oc
    oc.to_parquet(f'output/partial_sweep_fit_{int(pct)}.parquet', index=False)
    print(f'pct={pct}: {len(oc)} outcomes', flush=True)
m.l2_cfg = base_cfg
