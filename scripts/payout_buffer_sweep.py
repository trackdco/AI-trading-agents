#!/usr/bin/env python3
"""What retained buffer is optimal after a payout? FIT ONLY.

PAYOUT RULE (ANGUS 2026-07-30): a withdrawal requires **5 trading days of +$100 or better**
since the last payout. That is the cadence gate the earlier MC lacked — it withdrew on every
touch of $54k, pinning the account permanently $2k above a locked floor and inflating
NY-alone P(bust) to 11.8% against an expected ~1%.

THE QUESTION. Convention keeps a $2k buffer. But a larger retained buffer does two things:
  1. moves the account further from the drawdown line  -> lower bust risk
  2. on a BUFFER-SCALED profile, raises the risk unit  -> larger position per trade
against one cost: capital left in the account is capital not withdrawn.

So the sweep must be run on BOTH profiles, because the feedback only exists in one:

  lucid      base $150 STATIC. Buffer changes bust risk and withdrawal timing ONLY — the risk
             unit does not move, so there is no size feedback to find.
  scaled600  base = $150 + $75 per full $2k of buffer past +$3k, capped $600. Here the buffer
             DOES set the risk unit, so a bigger buffer really does buy more risk per trade.
             P&L is rescaled by base(buffer)/base_in_book to model that feedback — the book's
             own `base` column records what it actually used.

    python -m scripts.payout_buffer_sweep
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DOCS = ROOT / "docs"
ET = "America/New_York"
START, TRAIL = 50_000.0, 2_000.0
ELIG_DAYS, ELIG_MIN = 5, 100.0          # 5 trading days of +$100 or better
BUFFERS = [2_000.0, 3_000.0, 4_000.0, 5_000.0, 6_000.0, 8_000.0, 10_000.0, 12_000.0, 16_000.0]
N_PATHS, NDAYS, SEED = 2000, 252, 20260730


def fit_only(p: Path) -> pd.DataFrame:
    if "holdout" in str(p).lower():
        raise SystemExit(f"SEALED SPAN REFUSED: {p}")
    d = pd.read_parquet(p)
    yrs = sorted(set(pd.to_datetime(d.day).dt.year))
    if set(yrs) - {2025, 2026}:
        raise SystemExit(f"SEALED SPAN TOUCHED: {yrs} in {p.name}")
    return d


def scaled_base(buffer: float) -> float:
    """scaled600: $150 + $75 per full $2k of buffer past +$3k, capped $600."""
    return min(600.0, 150.0 + 75.0 * np.floor(max(0.0, buffer - 3000.0) / 2000.0))


def daymap(profile: str):
    b = fit_only(ROOT / f"output/funded_book_{profile}_fit.parquet").copy()
    b["fill_ts"] = pd.to_datetime(b.ts, format="mixed", utc=True).dt.tz_convert(ET)
    b = b.sort_values(["day", "fill_ts"], kind="mergesort")
    dm = {d: list(zip(g.pl.astype(float), g.base.astype(float)))
          for d, g in b.groupby("day")}
    return dm, sorted(dm)


def run(profile: str, retain: float, scale_feedback: bool) -> dict:
    dm, keys = daymap(profile)
    K = np.array(keys, dtype=object)
    rng = np.random.default_rng(SEED)
    busts, paid_tot, cycles, minbuf = 0, [], [], []
    for _ in range(N_PATHS):
        eq, floor, locked = START, START - TRAIL, False
        good, paid, cyc, mb = 0, 0.0, 0, np.inf
        for i in rng.integers(0, len(K), NDAYS):
            dpl = 0.0
            for pl, base_book in dm[K[i]]:
                if scale_feedback:
                    # buffer-scaled risk unit: rescale the trade by the base this buffer buys
                    pl = pl * (scaled_base(eq - floor) / max(base_book, 1e-9))
                eq += pl
                dpl += pl
            if dpl >= ELIG_MIN:
                good += 1
            if not locked:
                floor = max(floor, eq - TRAIL)
                if floor >= START:
                    floor, locked = START, True
            mb = min(mb, eq - floor)
            if eq <= floor:
                busts += 1
                break
            # payout: eligible after ELIG_DAYS qualifying days, withdraw down to `retain`
            if good >= ELIG_DAYS and eq - floor > retain:
                w = eq - floor - retain
                eq -= w
                paid += w
                cyc += 1
                good = 0
        paid_tot.append(paid)
        cycles.append(cyc)
        minbuf.append(0.0 if mb is np.inf else mb)
    return {"bust": busts / N_PATHS, "paid": np.array(paid_tot),
            "cyc": np.array(cycles), "minbuf": np.array(minbuf)}


def main() -> None:
    L = ["# Optimal retained payout buffer\n",
         "\n**Fit only. Sealed 2023/24 never loaded.**\n",
         f"\nPayout rule: **{ELIG_DAYS} trading days of +${ELIG_MIN:,.0f} or better** since the "
         f"last withdrawal (ANGUS 2026-07-30). On eligibility, withdraw everything above the "
         f"retained buffer.\n",
         f"\n{N_PATHS:,} paths x {NDAYS} days, seeded ({SEED}). Day-level bootstrap, intraday "
         f"order preserved. Floor: ${TRAIL:,.0f} trailing, locks at start once equity reaches "
         f"${START + TRAIL:,.0f}.\n"]

    for profile, feedback in (("lucid", False), ("scaled600", True)):
        L.append(f"\n## {profile}"
                 + ("  — base $150 STATIC, no size feedback\n" if not feedback
                    else "  — base SCALES with buffer, size feedback modelled\n"))
        L.append("\n| retained buffer | P(bust) | payout cycles med | total withdrawn "
                 "p10/med/p90 | min buffer med |\n|---|---|---|---|---|\n")
        res = {}
        for B in BUFFERS:
            r = run(profile, B, feedback)
            res[B] = r
            L.append(f"| ${B:,.0f} | **{r['bust'] * 100:.1f}%** | {np.median(r['cyc']):.0f} | "
                     f"${np.percentile(r['paid'], 10):,.0f} / ${np.median(r['paid']):,.0f} / "
                     f"${np.percentile(r['paid'], 90):,.0f} | ${np.median(r['minbuf']):,.0f} |\n")
        best_pay = max(res, key=lambda b: np.median(res[b]["paid"]))
        safest = min(res, key=lambda b: res[b]["bust"])
        L.append(f"\n**Most withdrawn:** ${best_pay:,.0f} buffer "
                 f"(${np.median(res[best_pay]['paid']):,.0f} median). "
                 f"**Lowest bust:** ${safest:,.0f} buffer "
                 f"({res[safest]['bust'] * 100:.1f}%).\n")
        # risk-adjusted: median withdrawn per unit of bust probability
        L.append("\n| buffer | median withdrawn | P(bust) | withdrawn per 1% bust |\n"
                 "|---|---|---|---|\n")
        for B in BUFFERS:
            r = res[B]
            eff = np.median(r["paid"]) / max(r["bust"] * 100, 0.05)
            L.append(f"| ${B:,.0f} | ${np.median(r['paid']):,.0f} | {r['bust'] * 100:.1f}% | "
                     f"${eff:,.0f} |\n")

    L.append("\n## Reading it\n\nOn **lucid** the buffer is a pure safety/liquidity trade: the "
             "risk unit is fixed at $150 so a larger buffer cannot buy more size, it only moves "
             "the account away from the line and delays cash out. On **scaled600** the buffer "
             "sets the risk unit, so raising it compounds — bigger buffer, bigger position, "
             "faster buffer growth — which is why the two profiles can disagree about the "
             "optimum. Pick the profile first, then the buffer.\n")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "PAYOUT-BUFFER-SWEEP.md").write_text("".join(L))
    print("wrote docs/PAYOUT-BUFFER-SWEEP.md")
    print("".join(L[6:]))


if __name__ == "__main__":
    main()
