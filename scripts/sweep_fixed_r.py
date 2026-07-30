"""Fixed-R partial family grid (ANGUS queued 2026-07-30): X% partial at +1R, BE variants,
runner policies. Motivation: ~80% of canon trades touch +1R before the original stop in BOTH
spans (95% touch +0.5R) — a 1R partial banks on 4 of 5 trades and needs no structure
detection on the partial leg live.

Same discipline as sweep_v8_partial / sweep_rr_floor: the canon fills' triggers re-simulated
through the REAL engine with a patched l2_cfg — no re-implementation. Management-only change:
n must stay identical to canon in every arm (partials are post-fill; unlike rr_floor this
cannot veto entries — the report asserts it).

Arms: partial_at_r=1.0 x pct {25,50} x BE-at-partial {off,on} x runner {trail,hold,hold2r},
plus 'base_v8' (unpatched cfg = shipped exits on the same triggers — parity anchor vs aikido).
Discovery on FIT only. Resumable: existing output parquets are skipped.

    python scripts/sweep_fixed_r.py [--procs 4]
"""
import argparse
import itertools
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')
import scripts.build_l2_outcomes as m           # noqa: E402
from scripts import funded_book as fb           # noqa: E402


def arms() -> list[tuple[str, dict]]:
    out = [('base_v8', {})]
    for pct, be, runner in itertools.product([25.0, 50.0], [False, True],
                                             ['trail', 'hold', 'hold2r']):
        name = f'r1p{int(pct)}{"be" if be else ""}_{runner}'
        out.append((name, dict(v8_partial_at_r=1.0, v8_partial_pct=pct,
                               v8_be_at_partial=be, v8_runner=runner)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()

    V = fb.load_book('fit')
    key = set(zip(V.ts, V.direction))
    C = pd.read_parquet('output/l0_triggers_fit.parquet')
    C = C[[(t, d) in key for t, d in zip(C.ts, C.direction)]].drop_duplicates(
        ['ts', 'direction'])
    print(f'canon triggers to re-simulate: {len(C)} of {len(V)} trades', flush=True)

    base_cfg = m.l2_cfg
    for name, upd in arms():
        path = Path(f'output/fixedr_fit_{name}.parquet')
        if path.exists():
            print(f'{name}: exists, skipped', flush=True)
            continue
        m.l2_cfg = (lambda t_cancel=100000.0, _u=upd:
                    base_cfg(t_cancel).model_copy(update=_u))
        out = m.run(C.copy(), procs=a.procs)
        oc = out[out.status == 'outcome'].drop_duplicates(['ts', 'direction'])
        oc.to_parquet(path, index=False)
        print(f'{name}: {len(oc)} outcomes, 1-lot ${oc.dollars_1lot.sum():+,.0f}',
              flush=True)
    m.l2_cfg = base_cfg


if __name__ == '__main__':
    main()
