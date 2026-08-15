#!/usr/bin/env python3
"""MONTE CARLO on the agent trade ledger — from run logs, no Pine required.

    python -m scripts.mc_bootstrap output/agent_runs/*_jn1.jsonl
    python -m scripts.mc_bootstrap output/agent_runs/*.jsonl --risk-pct 1.0 --draws 20000

THE POINT, because the premise it answers is a common one: Monte Carlo, DSR
and PBO do NOT need a mechanical strategy engine or a Pine backtest. They
consume a TRADE LEDGER (and, for PBO, a configuration matrix). The run logs
already carry a richer ledger than any strategy tester exports — entry,
stop, targets, R at full target and blended, MFE/MAE, the management trail,
and the reasoning behind each decision.

WHAT THIS COMPUTES (all resampled from the realised R sequence):
  - terminal-equity distribution over a resampled path of the same length
  - max-drawdown distribution (the number that actually decides survivability
    on a prop account, and the one a single equity curve hides)
  - risk-of-ruin against a stated drawdown limit
  - longest losing streak distribution
  - the sequence-risk check: realised order vs resampled order

TWO RESAMPLERS, and the difference matters:
  iid       draw trades independently with replacement. Standard, and it
            assumes trades are exchangeable.
  block     draw contiguous BLOCKS of trades (default 5). Preserves local
            dependence — clustering of losers within a regime, which is
            exactly what an iid bootstrap flatters away. Report both; if
            block drawdowns are materially worse, dependence is real and the
            iid number is optimistic.

HONESTY RAILS, printed with the output:
  - n is stated everywhere. Under ~100 trades these intervals are wide and
    are described as such.
  - R multiples assume the stated stop was honoured and fills were achieved
    at the logged prices. Replay fills are touch-model (documented
    optimism); live paper will recalibrate this.
  - This measures the DISPERSION of a strategy's own realised edge. It says
    nothing about whether that edge survives out of sample — that is what
    the walk-forward and PBO are for. A Monte Carlo on an overfit backtest
    produces beautiful, meaningless intervals.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

R_FIELDS_FULL = ("r_result", "r_full_target_whole_position_at_final_exit")
R_FIELDS_BLEND = ("r_blended", "r_blended_across_partials")


def _first(d: dict, keys) -> float | None:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def load_ledger(paths: list[Path], blended: bool) -> list[tuple[str, str, float]]:
    """(day, candidate_id, R) for every closed trade, in chronological order."""
    out = []
    for p in sorted(paths):
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("row") != "exit":
                continue
            v = _first(r, R_FIELDS_BLEND if blended else R_FIELDS_FULL)
            if v is None:                       # fall back to the other convention
                v = _first(r, R_FIELDS_FULL if blended else R_FIELDS_BLEND)
            if v is not None:
                out.append((p.stem, r.get("candidate_id", "?"), v))
    return out


def paths_iid(R: np.ndarray, n: int, draws: int, rng) -> np.ndarray:
    return rng.choice(R, size=(draws, n), replace=True)


def paths_block(R: np.ndarray, n: int, draws: int, rng, block: int) -> np.ndarray:
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, len(R), size=(draws, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % len(R)
    return R[idx.reshape(draws, -1)[:, :n]]


def summarise(sims: np.ndarray, risk_pct: float, ruin_dd: float, label: str,
              realised: np.ndarray) -> None:
    draws, n = sims.shape
    eq = np.cumsum(sims * risk_pct, axis=1)                 # % of starting equity
    peak = np.maximum.accumulate(eq, axis=1)
    dd = np.max(peak - eq, axis=1)
    term = eq[:, -1]
    streak = np.zeros(draws, dtype=int)
    cur = np.zeros(draws, dtype=int)
    for j in range(n):
        cur = np.where(sims[:, j] < 0, cur + 1, 0)
        streak = np.maximum(streak, cur)

    r_eq = np.cumsum(realised * risk_pct)
    r_dd = float(np.max(np.maximum.accumulate(r_eq) - r_eq))

    q = lambda a, p: float(np.percentile(a, p))
    print(f"\n  {label}  ({draws:,} paths of {n} trades, {risk_pct:.2f}% risk/trade)")
    print(f"    terminal return %   p5 {q(term,5):+7.1f}   p50 {q(term,50):+7.1f}"
          f"   p95 {q(term,95):+7.1f}   ·  realised {r_eq[-1]:+.1f}")
    print(f"    max drawdown %      p50 {q(dd,50):7.1f}   p95 {q(dd,95):7.1f}"
          f"   p99 {q(dd,99):7.1f}   ·  realised {r_dd:.1f}")
    print(f"    longest losing run  p50 {q(streak,50):7.0f}   p95 {q(streak,95):7.0f}"
          f"   max {int(streak.max()):7d}")
    print(f"    P(terminal < 0)     {float((term < 0).mean()) * 100:5.1f}%"
          f"        P(drawdown > {ruin_dd:.0f}%)  "
          f"{float((dd > ruin_dd).mean()) * 100:5.1f}%")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--blended", action="store_true",
                    help="use blended-R (partials weighted) instead of full-target R")
    ap.add_argument("--risk-pct", type=float, default=1.0,
                    help="%% of equity risked per trade (default 1.0)")
    ap.add_argument("--ruin-dd", type=float, default=10.0,
                    help="drawdown %% treated as ruin, e.g. a prop limit (default 10)")
    ap.add_argument("--draws", type=int, default=20000)
    ap.add_argument("--block", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260810,
                    help="fixed by default, matching the repo's permutation seed")
    a = ap.parse_args()

    paths = sorted({Path(x) for pat in a.runs for x in glob.glob(pat)})
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise SystemExit("no run files matched")

    led = load_ledger(paths, a.blended)
    if len(led) < 5:
        raise SystemExit(f"only {len(led)} closed trades found — nothing to resample")
    R = np.array([x[2] for x in led], dtype=float)
    rng = np.random.default_rng(a.seed)

    wins, losses = R[R > 0], R[R < 0]
    print("\n" + "=" * 78)
    print("  MONTE CARLO — resampled from the agent trade ledger")
    print("=" * 78)
    print(f"  source: {len(paths)} run log(s), {len(R)} closed trades  "
          f"({'blended' if a.blended else 'full-target'} R)")
    print(f"  realised: total {R.sum():+.2f}R   mean {R.mean():+.3f}R   "
          f"WR {100 * len(wins) / len(R):.1f}%   "
          f"avg win {wins.mean() if len(wins) else 0:+.2f}R   "
          f"avg loss {losses.mean() if len(losses) else 0:+.2f}R")

    summarise(paths_iid(R, len(R), a.draws, rng), a.risk_pct, a.ruin_dd,
              "IID BOOTSTRAP", R)
    summarise(paths_block(R, len(R), a.draws, rng, a.block), a.risk_pct,
              a.ruin_dd, f"BLOCK BOOTSTRAP (block={a.block})", R)

    print(f"\n  n = {len(R)}. ", end="")
    if len(R) < 100:
        print("UNDER 100 TRADES — these intervals are wide and must be")
        print("  presented as indicative, never as a performance claim. The"
              " walk-forward,")
        print("  not this, is what tests whether the edge survives out of sample.")
    else:
        print("Intervals are meaningful for dispersion; out-of-sample survival")
        print("  is still the walk-forward's job, not this one's.")
    print("  R assumes logged stops were honoured and replay touch-fills were"
          " achievable.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
