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
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')
import scripts.build_l2_outcomes as m           # noqa: E402
from scripts import funded_book as fb           # noqa: E402


def arms() -> list[tuple[str, dict]]:
    """ANGUS 2026-07-30 (this session): "we found 25% was most profitable, but id say our
    first target is too short looking at the % of trades that ran atleast 1.5r, 2r and 3r".
    Primary axis: the R-LADDER of the first profit leg — how deep the partial books —
    with the shipped trail/BE behavior held fixed. Secondary: the 1R banking variants
    (BE-at-partial, no-trail hold) from the original queue, in case shallow-and-protect
    beats deep. Reach context (capture_mfe_fit): 95% touch 0.5R, 75% touch 1R, 48% touch
    2R in-trade; 58%/40% reach 2R/3R to-EOD."""
    out = [('base_v8', {})]
    for pr in (1.0, 1.5, 2.0, 3.0):
        for pct in (25.0, 50.0):
            tag = str(pr).replace('.', '')
            out.append((f'p{int(pct)}_at{tag}r_trail',
                        dict(v8_partial_at_r=pr, v8_partial_pct=pct)))
    for pct in (25.0, 50.0):
        out.append((f'p{int(pct)}_at10r_be_trail',
                    dict(v8_partial_at_r=1.0, v8_partial_pct=pct, v8_be_at_partial=True)))
        out.append((f'p{int(pct)}_at10r_hold',
                    dict(v8_partial_at_r=1.0, v8_partial_pct=pct, v8_runner='hold')))
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
