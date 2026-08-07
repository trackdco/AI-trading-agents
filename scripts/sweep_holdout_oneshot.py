import sys
import pandas as pd
sys.path.insert(0,'.')
import scripts.build_l2_outcomes as m
from scripts import funded_book as fb

V = fb.load_book('holdout')
key = set(zip(V.ts, V.direction))
C = pd.read_parquet('output/l0_triggers_holdout.parquet')
C = C[[(t,d) in key for t,d in zip(C.ts, C.direction)]].drop_duplicates(['ts','direction'])
print('holdout canon triggers:', len(C))
base_cfg = m.l2_cfg
m.l2_cfg = lambda t_cancel=100000.0: base_cfg(t_cancel).model_copy(update={"v8_partial_pct": 25.0})
out = m.run(C.copy(), procs=8)
oc = out[out.status=='outcome'].drop_duplicates(['ts','direction'])
oc.to_parquet('output/partial_sweep_holdout_25.parquet', index=False)
print('holdout 25pct outcomes:', len(oc))
