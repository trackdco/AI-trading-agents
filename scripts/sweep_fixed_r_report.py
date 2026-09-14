"""Report for the exit-lab sweeps (fixed-R family + rr_floor tail): funded-sizing table for
every arm on the SAME canon fills, plus the era x session split that decides freezes.

Baselines on every run: shipped V8 (base_v8 arm), the holdout-confirmed 25% structure
partial (partial_sweep_fit_25.parquet, committed), and any rrfloor_sweep_fit_* present.

Guards printed, not hidden: n per arm (a fixed-R arm whose n != canon is a BUG — partials
cannot veto entries; rr_floor arms legitimately shrink and the report labels the vetoes),
and the exit-reason mix so degradation (partial+stop replacing partial+target) is visible.

    python scripts/sweep_fixed_r_report.py
"""
import glob
import sys

import pandas as pd

sys.path.insert(0, '.')
from scripts import funded_book as fb           # noqa: E402

V = fb.load_book('fit')
N_CANON = len(V)


def book_with(oc: pd.DataFrame) -> dict:
    """Swap the canon book's exits/dollars for an arm's and run the funded sim."""
    W = V.drop(columns=['dollars_1lot', 'exit_ts', 'R', 'exit_reason'],
               errors='ignore').merge(
        oc[['ts', 'direction', 'dollars_1lot', 'exit_ts', 'R', 'exit_reason']],
        on=['ts', 'direction'], how='inner')
    W['exit'] = pd.to_datetime(W.exit_ts, format='mixed', utc=True)
    W = W.sort_values('fill', kind='mergesort')
    B = fb.run(W, 'lucid')
    D = B.groupby('day').pl.sum()
    cum = D.cumsum()
    Rr = W.dollars_1lot / (W.risk * 20)
    row = {'n': len(W), 'WR%': round((W.dollars_1lot > 0).mean() * 100),
           'meanR': round(Rr.mean(), 3),
           'win meanR': round(Rr[W.dollars_1lot > 0].mean(), 2),
           '1lot $': round(W.dollars_1lot.sum()),
           'funded net': round(B.pl.sum()),
           'worst day': round(D.min()), 'maxDD': round((cum.cummax() - cum).max()),
           'win days': int((D > 0).sum())}
    cells = {}
    W = W.assign(Rr=Rr)
    for (era, sess), g in W.groupby(['era', 'sess']):
        cells[f'{era}·{sess}'] = round(g.Rr.mean(), 3)
    reasons = W.exit_reason.value_counts().to_dict()
    return row, cells, reasons


def main() -> None:
    files = {}
    for f in sorted(glob.glob('output/fixedr_fit_*.parquet')):
        files[f.split('fixedr_fit_')[1].split('.parquet')[0]] = f
    for f in sorted(glob.glob('output/partial_sweep_fit_25.parquet')):
        files['struct25 (holdout-OK)'] = f
    for f in sorted(glob.glob('output/rrfloor_sweep_fit_*.parquet')):
        files[f'rrfloor {int(f.split("_")[-1].split(".")[0]) / 10:.1f}'] = f

    rows, cell_rows, reason_rows = {}, {}, {}
    for name, f in files.items():
        oc = pd.read_parquet(f)
        row, cells, reasons = book_with(oc)
        if 'fixedr' in f and row['n'] != N_CANON:
            row['n'] = f"{row['n']} (BUG: != {N_CANON})"
        rows[name] = row
        cell_rows[name] = cells
        reason_rows[name] = reasons

    T = pd.DataFrame(rows).T.sort_values('funded net', ascending=False)
    print(T.to_string())
    print('\n--- era x session meanR ---')
    print(pd.DataFrame(cell_rows).T.to_string())
    print('\n--- exit reasons ---')
    print(pd.DataFrame(reason_rows).T.fillna(0).astype(int).to_string())


if __name__ == '__main__':
    main()
