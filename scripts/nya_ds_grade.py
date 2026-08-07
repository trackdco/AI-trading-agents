#!/usr/bin/env python3
"""NYA-DS-01 trial 6 — grading pack on the tournament default (L1b census
expression): PSR(0) vs the §5.9.5 sleeve floor 0.75, DSR with the merged-
ledger denominator, MTRL, funded MC, canon correlation. Methodology mirrors
scripts/nya_ivb_fade_grade.py for comparability.

    python -m scripts.nya_ds_grade
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.dsr import deflated_sharpe_ratio, min_track_record_length
from src.validation import trial_ledger as TL

FR, RISK = 1.0, 160.0
SEED, N_SIMS, YEAR_DAYS, START, TRAIL = 7, 2_000, 252, 50_000.0, 2_000.0


def main() -> None:
    rng_ = np.random.default_rng(SEED)
    R = pd.read_parquet(ROOT / "output/nya_ds_exitlab.parquet")
    day_r = R[R.arm == "default"].groupby("day").r.sum()

    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    gdays = sorted(set((ts + pd.Timedelta(hours=6)).dt.date.astype(str)))
    s = pd.Series(0.0, index=gdays)
    s.loc[day_r.index] = RISK * day_r

    n_led, var_led = TL.n_trials(), TL.trial_effect_variance()
    d = deflated_sharpe_ratio(s.to_numpy(float), n_trials=n_led, trial_sr_var=var_led)
    print(f"== grading (default spec, {int((s != 0).sum())} trade-days / {len(s)} sessions) ==")
    print(f"  daily SR {d.sr:+.4f} | PSR(0) {d.psr_zero:.3f} vs sleeve floor 0.75 "
          f"{'PASS' if d.psr_zero >= 0.75 else 'FAIL'} | DSR {d.dsr:.3f} "
          f"(ledger {n_led} trials) | MTRL {min_track_record_length(s.to_numpy(float)):.0f}d "
          f"vs {len(s)} held")

    busts, nets = 0, []
    x = s.to_numpy(float)
    for _ in range(N_SIMS):
        path = x[rng_.integers(0, len(x), YEAR_DAYS)]
        bal, line = START, START - TRAIL
        for pl in path:
            bal += pl
            if bal - line <= 0:
                busts += 1
                break
            line = min(START, max(line, bal - TRAIL))
        nets.append(bal - START)
    print(f"  MC 12mo funded shell: P(bust) {busts / N_SIMS:.1%} median ${np.median(nets):+,.0f}")

    canon = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet")
    sc = canon.groupby("day").pl.sum().reindex(s.index).fillna(0.0)
    ok = sc.index[(sc != 0) | (s != 0)]
    pe = float(np.corrcoef(s.loc[ok], sc.loc[ok])[0, 1])
    both = (s != 0) & (sc != 0)
    print(f"== canon correlation == union Pearson {pe:+.3f} | both-active {int(both.sum())} days")
    if both.sum() >= 10:
        print(f"  both-active Pearson {float(np.corrcoef(s[both], sc[both])[0, 1]):+.3f}")

    fade = pd.read_parquet(ROOT / "output/nya_ivb_fade_era.parquet")
    fade["r"] = (fade.pts - FR) / fade.risk
    sf = (RISK * fade.groupby("day").r.sum()).reindex(s.index).fillna(0.0)
    okf = sf.index[(sf != 0) | (s != 0)]
    print(f"== IB-fade correlation == union Pearson "
          f"{float(np.corrcoef(s.loc[okf], sf.loc[okf])[0, 1]):+.3f} | "
          f"both-active {int(((s != 0) & (sf != 0)).sum())} days")


if __name__ == "__main__":
    main()
