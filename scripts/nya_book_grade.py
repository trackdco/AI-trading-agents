#!/usr/bin/env python3
"""THE BOOK GRADING — first portfolio-level exam under §5.9.3.

Components (each already past its own sleeve gates or shelved-eligible):
  ny_canon    the live strategy (emission, funded accounting)
  nya_fadeB   IVB range fade, default spec (sleeve gates passed)
  nypre_gap   gap fade, frozen d5-gated spec (shelved-eligible, PSR 0.77)
  nypre_inv   inventory fade, A0 spec per PBO reversion (PSR 0.92 at A1;
              A0 is the process-honest spec)

Two reads:
  COMMON SPAN (flow span, all four defined): correlation matrix, book MC
  (funded shell), book PSR/DSR.
  LONG SPAN (canon + fade, full overlap): the two big books alone.

The §5.9.3 ship screen: book-level PSR/DSR >= 0.95 + MC + no correlation
vetoes. Ledger-DSR carries the known denominator-inflation caveat (flagged
to Brake); PSR reported alongside.

    python -m scripts.nya_book_grade
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.dsr import deflated_sharpe_ratio, probabilistic_sharpe_ratio  # noqa: E402
from src.validation import trial_ledger as TL  # noqa: E402

SEED, N_SIMS, YEAR_DAYS, START, TRAIL = 7, 2_000, 252, 50_000.0, 2_000.0


def ruin(x, rng, label):
    busts, nets, dds = 0, [], []
    for _ in range(N_SIMS):
        path = x[rng.integers(0, len(x), YEAR_DAYS)]
        bal, line, peak, dd = START, START - TRAIL, START, 0.0
        for pl in path:
            bal += pl
            if bal - line <= 0:
                busts += 1; break
            line = min(START, max(line, bal - TRAIL))
            peak = max(peak, bal); dd = max(dd, peak - bal)
        nets.append(bal - START); dds.append(dd)
    print(f"  {label:34s} P(bust) {busts/N_SIMS:.1%}  median ${np.median(nets):+,.0f}  "
          f"median maxDD ${np.median(dds):,.0f}")


def main() -> None:
    rng = np.random.default_rng(SEED)
    canon = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet").groupby("day").pl.sum()
    fadeM = pd.read_parquet(ROOT / "output/nya_ivb_fade_arms.parquet")
    fade = fadeM["E0_default"]
    gap = pd.read_parquet(ROOT / "output/emission_nypre_gap_fit.parquet").groupby("day").pl.sum()
    invA = pd.read_parquet(ROOT / "output/nypre_arms_nypre_inv.parquet")["A0_onh"]

    uni = invA.index  # flow-span sessions
    S = pd.DataFrame({
        "canon": canon.reindex(uni).fillna(0.0),
        "fadeB": fade.reindex(uni).fillna(0.0),
        "gap": gap.reindex(uni).fillna(0.0),
        "inv": invA.reindex(uni).fillna(0.0),
    })
    book = S.sum(axis=1)

    print(f"== BOOK, common span ({len(uni)} sessions {uni.min()}..{uni.max()}) ==")
    print("correlation matrix (union days):")
    print(S.corr().round(3).to_string())
    print("component sums:", {c: f"${S[c].sum():+,.0f}" for c in S})
    print("\n== funded-shell MC ==")
    ruin(S.canon.to_numpy(float), rng, "canon alone")
    ruin(book.to_numpy(float), rng, "BOOK (canon+fade+gap+inv)")
    ruin((S.fadeB + S.gap + S.inv).to_numpy(float), rng, "new sleeves only (no canon)")

    x = book.to_numpy(float)
    psr = probabilistic_sharpe_ratio(x)
    n_led, var_led = TL.n_trials(), TL.trial_effect_variance()
    d = deflated_sharpe_ratio(x, n_trials=n_led, trial_sr_var=var_led)
    print(f"\n== book statistics ==")
    print(f"  daily SR {d.sr:+.4f} | PSR(0) {psr:.3f} vs 0.95 screen "
          f"{'PASS' if psr >= .95 else 'FAIL'} | ledger-DSR {d.dsr:.3f} "
          f"(KNOWN-INFLATED denominator: {n_led} trials var {var_led:.3f} — Brake fix pending)")
    ns = (S != 0).sum()
    print(f"  active days: {dict(ns)}")

    # long span: canon + fade only
    days2 = sorted(set(canon.index) | set(fade.index))
    S2 = pd.DataFrame({"canon": canon.reindex(days2).fillna(0.0),
                       "fadeB": fade.reindex(days2).fillna(0.0)})
    b2 = S2.sum(axis=1).to_numpy(float)
    print(f"\n== LONG SPAN canon+fade ({len(days2)} days) ==")
    print(f"  Pearson {S2.corr().iloc[0,1]:+.3f} | book PSR(0) {probabilistic_sharpe_ratio(b2):.3f}")
    ruin(b2, rng, "canon+fade long span")


if __name__ == "__main__":
    main()
