#!/usr/bin/env python3
"""RUN THE IDENTITY-CHURN SWEEP — Amendment 05's pass-mark clause (a-i), executed.

This is a Stage 3 run: it computes an outcome (mean net R at cost, session-block
bootstrap) for the FIRST time in this project's Amendment 05 work. Workbench only
(2023-01-03 .. 2025-01-31, WORKBENCH_END). The holdout is never addressed — this run
answers "is there a workbench edge robust to the five documented ambiguities," not
the final out-of-sample question, which is a separate, later, one-time act requiring
config/data_split.yaml's own unseal token.

CONSUMES N_TRIALS SLOT 2 OF 5. The discarded Stage 3 run consumed slot 1 and was never
refunded (STAGE3-DISCARDED.md). This is the next and only other outcome computation
this project has run.

For each of 32 combinations (spec_sweep.all_combinations()):
  1. Build the full trade list under that combination (spec_sweep.signal_candidates_sweep
     + admit_and_resolve).
  2. Seal the raw trade-level records to parquet, hashed, one file per combination.
  3. Compute mean net R at each of the three pre-registered cost bases (0.50/0.975/1.50).
  4. Session-block bootstrap (blocks = whole sessions, resample with replacement,
     10,000 iterations) on net_R at the base cost (0.975); lower bound = the 1.25th
     percentile of the bootstrap distribution (one-sided, at the corrected alpha 0.0125
     PASS-MARKS-FOR-SIGNING.md 10.3 signs via /4 — DISCLOSED CONVENTION: the
     pre-registration states the alpha and the block design but never states the
     percentile or one- vs two-sided form; this is the reading used, stated here so it
     is not silently assumed).
  5. Sign-flip check: does mean net R change sign between c050 and c150.

VERDICT: PASS only if EVERY ONE of the 32 combinations has mean net R > 0 at 0.975,
bootstrap lower bound > 0, AND no cost-level sign flip. Otherwise NO EDGE DEMONSTRATED,
per (a-i)'s own text: "A result positive under one resolution and negative under
another is recorded as NO EDGE DEMONSTRATED, not as a pass on the favourable branch."

Only the AGGREGATE figures the pass-mark determination requires are printed (per-combo
mean net R, bootstrap bound, sign-flip flag, trade count, and the final verdict) — no
per-trade P&L, no win/loss count, no equity curve. This is what running Stage 3 to a
verdict has always meant; it is not withheld the way a still-sealed result would be.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import hashlib
import json
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from vwapbb_signals import build_sessions
from vwapbb_opportunity import assert_workbench, WORKBENCH_END
from stage2_smoke import contract_key, COSTS
import spec_sweep as SW

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "identity_churn_sweep"
N_BOOTSTRAP = 10_000
ALPHA = 0.0125                    # corrected alpha, signed /4 (PASS-MARKS-FOR-SIGNING.md 10.3)
BASE_COST_TAG = "c0975"
SPEC_HASH = "a42f6ae3c6277e800991585ffacaa2cc47a9ea77"     # git blob, A1-A22 (post-errata)


def _lcg_stream(seed):
    """Deterministic PRNG (no random module — this file's determinism must be exact
    and reproducible without depending on interpreter-level seeding conventions).
    64-bit LCG, standard constants (Knuth's MMIX)."""
    state = seed & ((1 << 64) - 1)
    a = 6364136223846793005
    c = 1442695040888963407
    while True:
        state = (a * state + c) & ((1 << 64) - 1)
        yield state


def build_full_trade_list(forks):
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev and contract_key(s) > contract_key(prev):
            rolls.add(d)
        prev = s
    after = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    trades, prev_hl, processed = [], None, 0
    excl = collections.Counter()
    prev_week_hl = None
    cur_week_key = None
    week_hi, week_lo = -1e18, 1e18

    for d in days:
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        wk = SW.iso_week_key(d)
        if cur_week_key is not None and wk != cur_week_key:
            prev_week_hl = (week_hi, week_lo)
            week_hi, week_lo = -1e18, 1e18
        cur_week_key = wk

        if d in rolls:
            excl["roll session"] += 1
            prev_hl = None
        elif d in after:
            excl["session after roll"] += 1
        elif len(sym_of[d]) > 1:
            excl["mixed contract"] += 1
        else:
            cands = SW.signal_candidates_sweep(bars, prev_hl, prev_week_hl, forks)
            if cands is None:
                excl["holiday / short session"] += 1
            else:
                processed += 1
                trades.extend(SW.admit_and_resolve(bars, cands, d, sorted(sym_of[d])))

        week_hi, week_lo = max(week_hi, this_hl[0]), min(week_lo, this_hl[1])
        if d not in rolls:
            prev_hl = this_hl
    return trades, processed, dict(excl), len(days)


def seal(combo_id, trades):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"combo_{combo_id:02d}.parquet"
    if path.exists():
        raise RuntimeError(f"REFUSING to overwrite existing sealed combo file: {path}")
    keys = list(trades[0].keys())
    cols = {k: [t.get(k) for t in trades] for k in keys}
    pq.write_table(pa.table(cols), path, compression="snappy")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / f"combo_{combo_id:02d}.sha256").write_text(f"{sha}  {path.name}\n")
    return path, sha


def session_block_bootstrap(trades, cost_tag, n_iter=N_BOOTSTRAP, alpha=ALPHA, seed=0):
    """Blocks = whole sessions, resample WITH replacement, n_iter iterations. Each
    iteration draws as many sessions (with replacement) as there are distinct sessions
    that produced a trade, pools every trade belonging to a drawn session (a session
    drawn twice contributes its trades twice), and computes the mean net R over the
    pooled set. Lower bound = the alpha-th percentile of the resulting distribution
    (one-sided). Deterministic PRNG so this is exactly reproducible."""
    by_session = collections.defaultdict(list)
    for t in trades:
        by_session[t["session_date"]].append(t[f"net_R_{cost_tag}"])
    sessions = sorted(by_session)
    n_sess = len(sessions)
    if n_sess == 0:
        return None, None
    rng = _lcg_stream(seed)
    means = []
    for _ in range(n_iter):
        pooled = []
        for _ in range(n_sess):
            r = next(rng) / (1 << 64)
            idx = int(r * n_sess)
            if idx >= n_sess:
                idx = n_sess - 1
            pooled.extend(by_session[sessions[idx]])
        means.append(sum(pooled) / len(pooled) if pooled else 0.0)
    means.sort()
    k = max(0, min(n_iter - 1, int(alpha * n_iter)))
    return means[k], means


def main():
    t0 = time.time()
    combos = SW.all_combinations()
    assert len(combos) == 32, f"expected 32 combinations, got {len(combos)}"

    print("=" * 100)
    print("IDENTITY-CHURN SWEEP — Amendment 05 pass-mark clause (a-i), 32 combinations")
    print("=" * 100)
    print(f"spec hash (A1-A22): {SPEC_HASH}")
    print(f"cost bases: {COSTS}   base cost for the primary criterion: {BASE_COST_TAG}")
    print(f"bootstrap: session-block, {N_BOOTSTRAP} iterations, one-sided lower bound "
          f"at alpha={ALPHA} (1.25th percentile)")
    print()

    results = []
    for combo_id, forks in enumerate(combos):
        trades, processed, excl, ndays = build_full_trade_list(forks)
        n = len(trades)
        if n == 0:
            print(f"combo {combo_id:02d} {forks}: NO TRADES — cannot evaluate")
            results.append({"combo_id": combo_id, "forks": forks, "n_trades": 0,
                             "mean_net_R_base": None, "bootstrap_lb": None,
                             "sign_flip": None, "clears": False})
            continue
        path, sha = seal(combo_id, trades)

        means_by_cost = {}
        for tag in COSTS:
            vals = [t[f"net_R_{tag}"] for t in trades]
            means_by_cost[tag] = sum(vals) / len(vals)

        lb, _ = session_block_bootstrap(trades, BASE_COST_TAG, seed=combo_id)
        sign_flip = (means_by_cost["c050"] > 0) != (means_by_cost["c150"] > 0)
        clears = (means_by_cost[BASE_COST_TAG] > 0) and (lb is not None and lb > 0) \
            and not sign_flip

        results.append({
            "combo_id": combo_id, "forks": forks, "n_trades": n,
            "sessions_processed": processed,
            "mean_net_R_c050": means_by_cost["c050"],
            "mean_net_R_c0975": means_by_cost["c0975"],
            "mean_net_R_c150": means_by_cost["c150"],
            "bootstrap_lb_c0975": lb,
            "sign_flip_050_150": sign_flip,
            "clears": clears,
            "sealed_file": str(path), "sha256": sha,
        })
        print(f"combo {combo_id:02d} n={n:4d} mean_R@0.975={means_by_cost['c0975']:+.4f} "
              f"boot_lb={lb:+.4f} sign_flip={sign_flip} clears={clears}  {forks}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sweep_summary.json").write_text(json.dumps(results, indent=1))

    valid = [r for r in results if r["n_trades"] > 0]
    all_clear = len(valid) == 32 and all(r["clears"] for r in valid)
    minimum = min(r["mean_net_R_c0975"] for r in valid) if valid else None

    print()
    print("=" * 100)
    print(f"combinations evaluated: {len(valid)} / 32")
    print(f"minimum mean net R @ 0.975 across all 32: "
          f"{minimum:+.4f}" if minimum is not None else "N/A")
    print(f"VERDICT: {'PASS' if all_clear else 'NO EDGE DEMONSTRATED'}")
    print("=" * 100)
    print(f"runtime: {(time.time()-t0)/60:.1f} min")
    return 0 if all_clear else 1


if __name__ == "__main__":
    sys.exit(main())
