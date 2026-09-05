#!/usr/bin/env python3
"""
Analysis of sealed retest_backtest.py outputs — PREREGISTRATION.md §4 as code.

For each labelled output:
  * n, win rate, PF, total net, mean net $/trade, max DD, RTH share, mean stop, counters
  * session-block bootstrap of the mean net $/trade: blocks = CME trading days of the ENTRY
    bar (bot's get_trading_day: ET, 18:00 boundary), resampled with replacement, 10,000
    iterations, one-sided 95% lower bound = 5th percentile of the bootstrap means.
    PRNG: numpy PCG64, seed 20260905 — fixed here, before any holdout data exists.
  * pass-mark conditions: mean > 0 AND LB > 0; abort if n < 300.

`--verdict` additionally prints the MINIMUM across the given combinations (holdout only):
PASS only if every combination clears both conditions and no abort condition fires.
Abort condition 2 (sign flip under 2x slippage) is checked by pairing each combination
with its `--stress LABEL=PATH` run.

usage: analyze_retest.py LABEL=PATH [LABEL=PATH ...] [--stress LABEL=PATH ...] [--verdict]
                         [--count-from YYYY-MM-DD] [--md OUT.md] [--json OUT.json]
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

ET = ZoneInfo("America/New_York")
SESSION_BOUNDARY_HOUR = 18   # == full_backtest.SESSION_BOUNDARY_HOUR
N_BOOT = 10_000
ALPHA = 0.05
SEED = 20260905
MIN_TRADES = 300


def get_trading_day(dt: datetime) -> date:
    """Replica of full_backtest.get_trading_day (CME day: >=18:00 ET belongs to next date)."""
    et = dt.astimezone(ET)
    if et.hour >= SESSION_BOUNDARY_HOUR:
        return (et + timedelta(days=1)).date()
    return et.date()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: str, count_from: date | None, count_to: date | None = None):
    doc = json.load(open(path))
    trades = doc["complete_trades"]
    if count_from or count_to:
        def keep(t):
            d = datetime.fromisoformat(t["entry_ts"]).astimezone(ET).date()
            return (count_from is None or d >= count_from) and (count_to is None or d <= count_to)
        trades = [t for t in trades if keep(t)]
    return doc, trades


def empty_by_construction(cfg: dict) -> bool:
    """PREREGISTRATION.md §1-bis: C1b (2xATR14 floor) x C3b (gate kept) admits no signal."""
    return cfg.get("stop_floor") == "a22_2xatr" and cfg.get("rr_gate") == "kept"


def block_bootstrap_lb(trades, n_iter=N_BOOT, alpha=ALPHA, seed=SEED):
    """One-sided lower bound on mean net $/trade, blocks = trading days of entry."""
    by_day = defaultdict(list)
    for t in trades:
        by_day[get_trading_day(datetime.fromisoformat(t["entry_ts"]))].append(t["adjusted_pnl"])
    days = sorted(by_day)
    if len(days) < 2:
        return None, len(days)
    blocks = [np.asarray(by_day[d], dtype=float) for d in days]
    sums = np.array([b.sum() for b in blocks])
    counts = np.array([len(b) for b in blocks])
    rng = np.random.Generator(np.random.PCG64(seed))
    nd = len(blocks)
    means = np.empty(n_iter)
    for k in range(n_iter):
        idx = rng.integers(0, nd, size=nd)
        means[k] = sums[idx].sum() / counts[idx].sum()
    return float(np.percentile(means, 100 * alpha)), nd


def stats(trades):
    pnls = np.array([t["adjusted_pnl"] for t in trades], dtype=float)
    n = len(pnls)
    if n == 0:
        return {"n": 0}
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    gp, gl = wins.sum(), -losses.sum()
    cum = np.cumsum(pnls)
    peak = np.maximum.accumulate(np.maximum(cum, 0))
    mdd = float((peak - cum).max())
    monthly = defaultdict(float)
    for t in trades:
        monthly[datetime.fromisoformat(t["entry_ts"]).astimezone(ET).strftime("%Y-%m")] += t["adjusted_pnl"]
    lb, ndays = block_bootstrap_lb(trades)
    return {
        "n": n,
        "win_rate_pct": round(100 * len(wins) / n, 2),
        "profit_factor": round(gp / gl, 3) if gl > 0 else None,
        "total_net": round(float(pnls.sum()), 2),
        "mean_net": round(float(pnls.mean()), 3),
        "sd_net": round(float(pnls.std(ddof=1)), 2) if n > 1 else None,
        "bootstrap_lb95": round(lb, 3) if lb is not None else None,
        "trading_days": ndays,
        "max_dd": round(mdd, 2),
        "rth_share_pct": round(100 * sum(1 for t in trades if t.get("is_rth")) / n, 1),
        "mean_stop": round(float(np.mean([t["stop_distance"] for t in trades])), 2),
        "months": len(monthly),
        "profitable_months": sum(1 for v in monthly.values() if v > 0),
        "monthly": dict(sorted(monthly.items())),
        "cond_mean_pos": bool(pnls.mean() > 0),
        "cond_lb_pos": bool(lb is not None and lb > 0),
        "abort_n": bool(n < MIN_TRADES),
    }


def parse_pairs(items):
    out = []
    for it in items or []:
        if "=" not in it:
            sys.exit(f"expected LABEL=PATH, got {it}")
        lab, path = it.split("=", 1)
        out.append((lab, path))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="LABEL=PATH")
    ap.add_argument("--stress", nargs="*", help="LABEL=PATH of the 2x-slippage run for the same LABEL")
    ap.add_argument("--control", nargs="*", help="LABEL=PATH reported in the table but never part of the verdict (the untouched bot)")
    ap.add_argument("--verdict", action="store_true")
    ap.add_argument("--count-from", default=None, help="count only trades whose entry (ET date) >= this")
    ap.add_argument("--count-to", default=None, help="count only trades whose entry (ET date) <= this")
    ap.add_argument("--md", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    count_from = date.fromisoformat(a.count_from) if a.count_from else None
    count_to = date.fromisoformat(a.count_to) if a.count_to else None

    results = {}
    controls = set()
    for lab, path in parse_pairs(a.runs) + [(l, p) for l, p in parse_pairs(a.control)]:
        doc, trades = load(path, count_from, count_to)
        st = stats(trades)
        st["empty_by_construction"] = empty_by_construction(doc["meta"]["config"])
        if (lab, path) in parse_pairs(a.control):
            controls.add(lab)
            st["control"] = True
        st["file"] = path
        st["file_sha256"] = sha256_file(path)
        st["trades_sha256"] = doc["meta"].get("trades_sha256")
        st["config"] = doc["meta"]["config"]
        st["counters"] = doc["meta"].get("retest_counters")
        st["window"] = doc["meta"]["window"]
        results[lab] = st
    stress = {}
    for lab, path in parse_pairs(a.stress):
        _, trades = load(path, count_from, count_to)
        stress[lab] = stats(trades)

    lines = []
    lines.append("| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lab, st in results.items():
        if st["n"] == 0:
            note = "empty by construction (§1-bis)" if st.get("empty_by_construction") else ""
            lines.append(f"| {lab} | 0 {note} | | | | | | | | | | | |")
            continue
        tag = " (control, not a candidate)" if lab in controls else ""
        lines.append(
            f"| {lab}{tag} | {st['n']} | {st['win_rate_pct']} | {st['profit_factor']} | {st['total_net']:+,.0f} "
            f"| {st['mean_net']:+.2f} | {st['bootstrap_lb95']:+.2f} | {st['max_dd']:,.0f} | {st['rth_share_pct']} "
            f"| {st['mean_stop']} | {st['profitable_months']}/{st['months']} "
            f"| {'yes' if st['cond_mean_pos'] else 'NO'} | {'yes' if st['cond_lb_pos'] else 'NO'} |")
    if stress:
        lines.append("")
        lines.append("| config | mean $/tr (1x) | mean $/tr (2x slippage) | sign flip |")
        lines.append("|---|---|---|---|")
        for lab, st2 in stress.items():
            st1 = results.get(lab)
            flip = (st1 is not None and st1["n"] and st2["n"] and (st1["mean_net"] > 0) != (st2["mean_net"] > 0))
            lines.append(f"| {lab} | {st1['mean_net'] if st1 else 'n/a'} | {st2['mean_net']} | {'YES' if flip else 'no'} |")
    print("\n".join(lines))

    verdict = None
    if a.verdict:
        aborts = []
        live = {lab: st for lab, st in results.items()
                if not st.get("empty_by_construction") and lab not in controls}
        for lab, st in live.items():
            if st["n"] < MIN_TRADES:
                aborts.append(f"{lab}: n={st['n']} < {MIN_TRADES}")
            st2 = stress.get(lab)
            if st2 and st2["n"] and (st["mean_net"] > 0) != (st2["mean_net"] > 0):
                aborts.append(f"{lab}: sign flips under 2x slippage")
        if aborts:
            verdict = "ABORT — no verdict read: " + "; ".join(aborts)
        else:
            all_pass = all(st["cond_mean_pos"] and st["cond_lb_pos"] for st in live.values())
            worst = min(live.items(), key=lambda kv: (kv[1]["bootstrap_lb95"] if kv[1]["bootstrap_lb95"] is not None else -1e9))
            verdict = ("PASS — every combination clears mean>0 and LB95>0" if all_pass
                       else f"NO EDGE DEMONSTRATED — minimum across combinations fails ({worst[0]}: "
                            f"mean {worst[1]['mean_net']:+.2f}, LB95 {worst[1]['bootstrap_lb95']:+.2f})")
        print(f"\nVERDICT (minimum across the {len(live)} non-empty combinations):", verdict)

    if a.md:
        with open(a.md, "w") as f:
            f.write("\n".join(lines) + "\n")
            if verdict:
                f.write(f"\n**VERDICT:** {verdict}\n")
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"results": results, "stress": stress, "verdict": verdict,
                       "bootstrap": {"n_iter": N_BOOT, "alpha": ALPHA, "seed": SEED, "prng": "numpy PCG64"},
                       "count_from": a.count_from}, f, indent=1, default=str)


if __name__ == "__main__":
    main()
