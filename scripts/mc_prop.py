#!/usr/bin/env python3
"""MONTE CARLO in DOLLARS — conviction sizing, and a SIM-funded evaluation sim.

    python -m scripts.mc_prop output/agent_runs/*_wk1.jsonl
    python -m scripts.mc_prop output/agent_runs/*.jsonl --target 3000 --trail-dd 2000

Two questions this answers that an R-multiple curve cannot:

  1. WHAT DOES CONVICTION SIZING DO? Risk per trade set by the trigger's own
     A/B/C grade (his: A $250 / B $200 / C $150) versus flat sizing. If the
     grade carries information, conviction sizing beats flat at the same
     average risk; if it does not, this is where that shows up.
  2. DOES IT PASS A SIM-FUNDED EVALUATION? A profit target with an
     END-OF-DAY TRAILING DRAWDOWN is a path-dependent survival problem, not
     an expectancy problem. A positive-expectancy strategy fails these
     regularly, and the only honest way to see the failure rate is to
     simulate the rule as written.

RESAMPLING IS BY DAY, NOT BY TRADE. Prop rules settle end-of-day, so the day
is the atom: whole session-days are drawn with replacement, keeping each
day's trade sequence, count and clustering intact. Trade-level resampling
would scramble exactly the structure the drawdown rule acts on.

INTRADAY BREACH USES MAE. A trade that closes green can still dip your
equity below the threshold mid-flight. Where the log carries MAE, the
within-trade trough is modelled; trades without it are marked and their
troughs treated as the closed result (optimistic, and reported as such).

THE EOD TRAILING RULE, as modelled (defaults match the common prop form):
  - threshold starts at (start_balance - trail_dd)
  - at each day's CLOSE, if the closing balance sets a new high-water mark,
    the threshold moves up to (that balance - trail_dd)
  - the threshold LOCKS once it reaches start_balance (--no-lock disables)
  - breach = equity at any modelled point <= threshold  -> FAIL
  - pass  = balance >= start_balance + target           -> PASS
Firms differ on details. --intraday-breach off checks only end-of-day
balances, which is the friendlier reading; run both if the firm's wording is
ambiguous, and quote the worse one.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

R_FULL = ("r_result", "r_full_target_whole_position_at_final_exit")
R_BLEND = ("r_blended", "r_blended_across_partials")


def _num(d: dict, keys) -> float | None:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def load_days(paths: list[Path], blended: bool):
    """{day: [(conviction, R, mae_R_or_None), ...]} in chronological order."""
    days: dict[str, list] = defaultdict(list)
    for p in sorted(paths):
        conv, rpts = {}, {}
        rows = []
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        for r in rows:                      # conviction + risk-in-points live upstream
            pay = {**r, **(r.get("output") or {})}
            cid = pay.get("candidate_id")
            if not cid:
                continue
            if pay.get("conviction"):
                conv[cid] = str(pay["conviction"]).strip().upper()[:1]
            for k in ("R_in_points", "r_points"):
                if isinstance(pay.get(k), (int, float)):
                    rpts[cid] = float(pay[k])
        for r in rows:
            if r.get("row") != "exit":
                continue
            cid = r.get("candidate_id", "?")
            R = _num(r, R_BLEND if blended else R_FULL)
            if R is None:
                R = _num(r, R_FULL if blended else R_BLEND)
            if R is None:
                continue
            mae_pts = r.get("mae_post_fill")
            if mae_pts is None and isinstance(r.get("mfe_mae_points_to_exit"), dict):
                mae_pts = r["mfe_mae_points_to_exit"].get("mae")
            risk_pts = rpts.get(cid) or (
                abs(float(r["entry"]) - float(r["original_stop"]))
                if r.get("entry") and r.get("original_stop") else None)
            mae_R = (float(mae_pts) / risk_pts) if (mae_pts is not None
                                                    and risk_pts) else None
            days[p.stem.replace("_wk1", "").replace("_jn1", "")].append(
                (conv.get(cid, "?"), R, mae_R))
    return dict(sorted(days.items()))


def simulate(day_list, sizes, start, target, trail_dd, draws, rng,
             intraday=True, lock=True, attempt_days=None, haircut=0.0):
    """Draw `attempt_days` days with replacement; run the prop rule on each path.

    `haircut` subtracts R from every trade before sizing — the sensitivity
    lever. It models cost drag (slippage, commissions, worse live fills than
    the replay touch model) AND edge decay together, which is the honest way
    to ask "how much smaller can the real edge be before this stops passing?"
    """
    n_days = len(day_list)
    attempt_days = attempt_days or n_days
    idx = rng.integers(0, n_days, size=(draws, attempt_days))
    passed = np.zeros(draws, dtype=bool)
    failed = np.zeros(draws, dtype=bool)
    day_of_pass = np.full(draws, -1)
    final = np.zeros(draws)
    peak_dd = np.zeros(draws)

    for s in range(draws):
        bal = start
        thresh = start - trail_dd
        hwm = start
        worst = 0.0
        for d in range(attempt_days):
            for conv, R0, mae_R in day_list[idx[s, d]]:
                R = R0 - haircut
                risk = sizes.get(conv, sizes["?"])
                if intraday and mae_R is not None and mae_R > 0:
                    if bal - mae_R * risk <= thresh:
                        failed[s] = True
                        break
                bal += R * risk
                worst = max(worst, hwm - bal)
                if bal <= thresh:
                    failed[s] = True
                    break
                if bal >= start + target:
                    passed[s] = True
                    day_of_pass[s] = d + 1
                    break
            if failed[s] or passed[s]:
                break
            if bal > hwm:                       # END OF DAY: ratchet
                hwm = bal
                nt = bal - trail_dd
                thresh = min(nt, start) if lock else nt
        final[s] = bal
        peak_dd[s] = worst
    return passed, failed, day_of_pass, final, peak_dd


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--blended", action="store_true")
    ap.add_argument("--start", type=float, default=50000.0)
    ap.add_argument("--target", type=float, default=3000.0)
    ap.add_argument("--trail-dd", type=float, default=2000.0)
    ap.add_argument("--draws", type=int, default=20000)
    ap.add_argument("--attempt-days", type=int, default=20,
                    help="length of an evaluation attempt in session-days "
                         "(default 20; independent of how many days the "
                         "ledger holds)")
    ap.add_argument("--seed", type=int, default=20260810)
    ap.add_argument("--no-lock", action="store_true",
                    help="threshold keeps trailing past the starting balance")
    ap.add_argument("--no-intraday-breach", action="store_true",
                    help="check the drawdown only on closed balances")
    a = ap.parse_args()

    paths = sorted({Path(x) for pat in a.runs for x in glob.glob(pat)})
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise SystemExit("no run files matched")
    days = load_days(paths, a.blended)
    day_list = list(days.values())
    trades = [t for d in day_list for t in d]
    if not trades:
        raise SystemExit("no closed trades found")

    R = np.array([t[1] for t in trades])
    have_mae = sum(1 for t in trades if t[2] is not None)
    by_conv = defaultdict(list)
    for c, r, _ in trades:
        by_conv[c].append(r)

    print("\n" + "=" * 78)
    print("  MONTE CARLO IN DOLLARS — conviction sizing + SIM-funded evaluation")
    print("=" * 78)
    print(f"  ledger: {len(day_list)} session-days, {len(trades)} closed trades"
          f"  ({'blended' if a.blended else 'full-target'} R)")
    print(f"  realised: {R.sum():+.2f}R total, {R.mean():+.3f}R/trade, "
          f"WR {100 * (R > 0).mean():.1f}%, "
          f"{len(trades) / len(day_list):.1f} fills/day")
    print("  by conviction: " + "  ".join(
        f"{k}: n={len(v)} mean {np.mean(v):+.2f}R" for k, v in sorted(by_conv.items())))
    print(f"  MAE available on {have_mae}/{len(trades)} trades "
          f"({'intraday breach modelled' if not a.no_intraday_breach else 'intraday check OFF'})")

    schemes = {
        "flat $150": {"?": 150.0},
        "flat $200": {"?": 200.0},
        "flat $250": {"?": 250.0},
        "conviction A250/B200/C150": {"A": 250.0, "B": 200.0, "C": 150.0, "?": 200.0},
    }

    print(f"\n  EVALUATION: start ${a.start:,.0f} · target +${a.target:,.0f} · "
          f"EOD trailing DD ${a.trail_dd:,.0f}"
          f"{' (locks at start)' if not a.no_lock else ' (never locks)'}")
    print(f"  {a.attempt_days}-day attempts, {a.draws:,} simulations each\n")
    print(f"  {'sizing':<26}{'PASS':>7}{'FAIL':>7}{'neither':>9}"
          f"{'med days':>10}{'p50 end $':>11}{'p95 peak DD $':>15}")
    print("  " + "-" * 74)
    for name, sizes in schemes.items():
        rng = np.random.default_rng(a.seed)          # same paths for every scheme
        p, f, dop, fin, dd = simulate(
            day_list, sizes, a.start, a.target, a.trail_dd, a.draws, rng,
            intraday=not a.no_intraday_breach, lock=not a.no_lock,
            attempt_days=a.attempt_days)
        med = np.median(dop[dop > 0]) if (dop > 0).any() else float("nan")
        print(f"  {name:<26}{100 * p.mean():6.1f}%{100 * f.mean():6.1f}%"
              f"{100 * (~p & ~f).mean():8.1f}%{med:10.0f}"
              f"{np.percentile(fin, 50) - a.start:+11,.0f}"
              f"{np.percentile(dd, 95):15,.0f}")

    # ---- SENSITIVITY: the number that actually means something at small n.
    # A 6-day sample with a strong win rate CANNOT produce failures when
    # resampled — the failures live in regimes the ledger never saw. So ask
    # the answerable question instead: how much smaller can the true
    # per-trade edge be before this stops passing?
    print(f"\n  SENSITIVITY — conviction sizing, edge reduced by a fixed R per trade")
    print(f"  (models slippage + commissions + live fills worse than replay's")
    print(f"   touch model + plain edge decay, all at once)\n")
    print(f"  {'haircut':<12}{'mean R/trade':>14}{'PASS':>8}{'FAIL':>8}"
          f"{'neither':>9}{'p50 end $':>12}")
    print("  " + "-" * 63)
    sizes = schemes["conviction A250/B200/C150"]
    for hc in (0.0, 0.25, 0.50, 0.75, 1.00):
        rng = np.random.default_rng(a.seed)
        p, f, dop, fin, dd = simulate(
            day_list, sizes, a.start, a.target, a.trail_dd, a.draws, rng,
            intraday=not a.no_intraday_breach, lock=not a.no_lock,
            attempt_days=a.attempt_days, haircut=hc)
        print(f"  −{hc:<11.2f}{R.mean() - hc:>+14.3f}{100 * p.mean():7.1f}%"
              f"{100 * f.mean():7.1f}%{100 * (~p & ~f).mean():8.1f}%"
              f"{np.percentile(fin, 50) - a.start:+12,.0f}")

    print(f"\n  n = {len(trades)} trades over {len(day_list)} days. ", end="")
    if len(trades) < 100:
        print("UNDER 100 TRADES.")
        print("  Every number above is INDICATIVE ONLY and must not be presented as")
        print("  an expected pass rate. A resample cannot invent days the ledger")
        print("  never saw — a regime absent from the sample is absent from the sim.")
    else:
        print("Sample is usable for dispersion; regime coverage is still the limit.")
    print("  R assumes logged stops held and replay touch-fills were achievable;")
    print("  slippage, commissions and partial-fill risk are NOT modelled here.")
    print("  'neither' = attempts that ended the sample without passing or failing.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
