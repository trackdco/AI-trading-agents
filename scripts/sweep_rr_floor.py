import sys
import pandas as pd
sys.path.insert(0,'.')
import scripts.build_l2_outcomes as m
from scripts import funded_book as fb

V = fb.load_book('fit')
key = set(zip(V.ts, V.direction))
C = pd.read_parquet('output/l0_triggers_fit.parquet')
C = C[[(t,d) in key for t,d in zip(C.ts, C.direction)]].drop_duplicates(['ts','direction'])
base_cfg = m.l2_cfg
for floor in [2.5, 3.0, 4.0]:
    m.l2_cfg = lambda t_cancel=100000.0, _f=floor: base_cfg(t_cancel).model_copy(
        update={"rr_floor": _f})
    out = m.run(C.copy(), procs=8)
    oc = out[out.status=='outcome'].drop_duplicates(['ts','direction'])
    oc.to_parquet(f'output/rrfloor_sweep_fit_{int(floor*10)}.parquet', index=False)
    print(f'rr_floor={floor}: {len(oc)} outcomes of {len(C)} triggers', flush=True)
m.l2_cfg = base_cfg
