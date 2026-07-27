#!/usr/bin/env python3
"""PRE-REGISTER the 2023/2024 out-of-regime holdout sample.

The canon is fitted on 2025-06-02 -> 2026-07-15 (the span where MBP-10 depth exists).
This draws the out-of-fit sample from 2023/2024 and SEALS it: the day list plus its
SHA-256 are written to disk and committed BEFORE any data is pulled or scored, so the
sample cannot be quietly redrawn once results are visible.

Design guardrail (docs/HANDOFF-pat-session-2026-07-27.md §3): "Random days,
pre-registered before scoring (journal the sampled dates first, then run) — no peeking,
no resampling until the story looks good."

Eligible universe = days carrying >= MIN_BARS 1-minute bars in data/reference/
nq_1m_master.parquet (excludes holidays and half-days). 513 days across 2023-2024.

Two modes:

  months  draw whole calendar months, stratified N/2 per year. Preserves the
          months-green frame Angus reads first (a month needs ~20 trades to be
          callable; the fit window averages 20.3/month).

  days    draw scattered individual days, stratified evenly across the 24 months.
          Cheapest defensible pull, maximum robustness to regime autocorrelation,
          but yields a pooled two-year verdict only — months-green is not callable.

    python -m scripts.sample_holdout_days --mode months --n 8 --seed 20260727
    python -m scripts.sample_holdout_days --mode days   --n 100 --seed 20260727

Writes data/reference/holdout_2023_24_days.csv (the sealed list, consumed verbatim by
notebooks/colab_holdout_pull.ipynb) and docs/HOLDOUT-2023-24-PREREGISTRATION.md.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BARS = ROOT / "data/reference/nq_1m_master.parquet"
OUT_CSV = ROOT / "data/reference/holdout_2023_24_days.csv"
OUT_DOC = ROOT / "docs/HOLDOUT-2023-24-PREREGISTRATION.md"
NY = "America/New_York"
MIN_BARS = 1000
YEARS = (2023, 2024)


def eligible_days() -> pd.DataFrame:
    """Trading days in 2023-2024 with full 1m bar coverage, from the bar master."""
    d = pd.read_parquet(BARS, columns=["ts_event"])
    ts = pd.to_datetime(d["ts_event"], utc=True).dt.tz_convert(NY)
    day = ts.dt.normalize()
    cov = day.value_counts().sort_index()
    cov = cov[cov.index.year.isin(YEARS)]
    keep = cov[cov >= MIN_BARS]
    return pd.DataFrame({
        "day": keep.index.strftime("%Y-%m-%d"),
        "year": keep.index.year,
        "month": keep.index.strftime("%Y-%m"),
        "bars": keep.to_numpy(),
    }).reset_index(drop=True)


def draw_months(univ: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Draw n whole calendar months, stratified n/2 per year."""
    if n % 2:
        raise SystemExit(f"--n must be even in months mode (n/2 per year); got {n}")
    per_year = n // 2
    picks: list[str] = []
    for i, yr in enumerate(YEARS):
        months = sorted(univ.loc[univ.year == yr, "month"].unique())
        if per_year > len(months):
            raise SystemExit(f"asked {per_year} months from {yr}, only {len(months)} exist")
        # Distinct sub-seed per year so the two draws are independent, not mirrored.
        chosen = (pd.Series(months)
                  .sample(n=per_year, random_state=seed + i)
                  .sort_values()
                  .tolist())
        picks.extend(chosen)
    out = univ[univ.month.isin(picks)].copy()
    out["block"] = out["month"]
    return out.sort_values("day").reset_index(drop=True)


def draw_days(univ: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Draw n individual days, spread as evenly as possible across all 24 months."""
    months = sorted(univ.month.unique())
    base, extra = divmod(n, len(months))
    # Which months get the +1 remainder is itself drawn, so it is not a fixed bias.
    bonus = set(pd.Series(months).sample(n=extra, random_state=seed - 1)) if extra else set()
    frames = []
    for i, m in enumerate(months):
        pool = univ[univ.month == m]
        k = min(base + (1 if m in bonus else 0), len(pool))
        if k:
            frames.append(pool.sample(n=k, random_state=seed + i))
    out = pd.concat(frames, ignore_index=True)
    out["block"] = out["month"]
    return out.sort_values("day").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("months", "days"), default="months")
    ap.add_argument("--n", type=int, default=8,
                    help="months mode: number of calendar months (even). days mode: number of days.")
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing sealed sample (this breaks pre-registration)")
    a = ap.parse_args()

    if OUT_CSV.exists() and not a.force:
        raise SystemExit(
            f"{OUT_CSV.relative_to(ROOT)} already exists — the sample is SEALED.\n"
            "Redrawing after seeing results is exactly what pre-registration prevents.\n"
            "Pass --force only if nothing has been pulled or scored yet.")

    univ = eligible_days()
    sample = draw_months(univ, a.n, a.seed) if a.mode == "months" else draw_days(univ, a.n, a.seed)

    days = sample.day.tolist()
    digest = hashlib.sha256("\n".join(days).encode()).hexdigest()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    sample[["day", "year", "month", "block", "bars"]].to_csv(OUT_CSV, index=False)

    blocks = sorted(sample.block.unique())
    by_year = sample.groupby("year").size().to_dict()
    per_block = sample.groupby("block").size()

    lines = [
        "# HOLDOUT PRE-REGISTRATION — 2023/2024 out-of-regime canon validation",
        "",
        "**This file is the commitment.** It is written and committed BEFORE any depth or",
        "trades data is pulled and before anything is scored. The SHA-256 below fixes the",
        "day list. If a later result is reported against a different set of days, this file",
        "is the evidence.",
        "",
        "| field | value |",
        "|---|---|",
        f"| mode | `{a.mode}` |",
        f"| n requested | {a.n} |",
        f"| seed | `{a.seed}` |",
        f"| days drawn | **{len(days)}** |",
        f"| 2023 / 2024 split | {by_year.get(2023, 0)} / {by_year.get(2024, 0)} |",
        f"| eligible universe | {len(univ)} days (>= {MIN_BARS} 1m bars, 2023-2024) |",
        f"| **SHA-256 of day list** | `{digest}` |",
        "",
        "Regenerate the digest to verify:",
        "",
        "```bash",
        ("python3 -c \"import hashlib,pandas as pd; "
         "d=pd.read_csv('data/reference/holdout_2023_24_days.csv'); "
         "print(hashlib.sha256(chr(10).join(d.day).encode()).hexdigest())\""),
        "```",
        "",
        "## Why these days are out of fit",
        "",
        "The canon is fitted on **2025-06-02 -> 2026-07-15** — the span begins on the exact",
        "day MBP-10 depth coverage begins. Every threshold in `scripts/live_thresholds.py`",
        "is a frozen 2025 quantile. No 2023 or 2024 day contributed to any of them.",
        "",
        f"## Blocks drawn ({len(blocks)})",
        "",
        "| block | days |",
        "|---|---|",
    ]
    lines += [f"| {b} | {int(per_block[b])} |" for b in blocks]
    lines += [
        "",
        "## The sealed day list",
        "",
        "```",
    ]
    lines += ["  ".join(days[i:i + 8]) for i in range(0, len(days), 8)]
    lines += [
        "```",
        "",
        "## What happens next",
        "",
        "1. Commit this file and `data/reference/holdout_2023_24_days.csv`. **Before the pull.**",
        "2. Run `notebooks/colab_holdout_pull.ipynb` — it reads the sealed list verbatim and",
        "   pulls MBP-10 depth + trades for exactly these days, nothing else.",
        "3. Condensed artifacts land in `data/reference/depth_2023_24/` and",
        "   `data/reference/cvd/`. Raw data never enters the repo.",
        "4. Score with the canon **unchanged** — no refits, no new knobs. Any threshold that",
        "   moves makes this a fit, not a holdout.",
        "",
        "## Known limit, stated up front",
        "",
        "The golden window fires 0.20 trades/day. The `Q <= 1` cut — already flagged in",
        "`docs/CANON-MECHANICAL.md` as a 16-trade watch item and \"first thing to re-test on",
        "2023/24\" — will land only a handful of trades at this sample size. **This holdout",
        "cannot settle that layer.** It is recorded here so the result is not over-read later.",
    ]
    OUT_DOC.write_text("\n".join(lines) + "\n")

    print(f"mode={a.mode} n={a.n} seed={a.seed}")
    print(f"eligible universe: {len(univ)} days")
    print(f"drawn: {len(days)} days across {len(blocks)} blocks "
          f"({by_year.get(2023, 0)} in 2023, {by_year.get(2024, 0)} in 2024)")
    print(f"blocks: {', '.join(blocks)}")
    print(f"SHA-256: {digest}")
    print(f"\nwrote {OUT_CSV.relative_to(ROOT)}")
    print(f"wrote {OUT_DOC.relative_to(ROOT)}")
    print("\nCOMMIT BOTH BEFORE PULLING ANY DATA.")


if __name__ == "__main__":
    main()
