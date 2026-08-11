#!/usr/bin/env python3
"""OUTCOME SCORER — the agent's picks vs the same-day trigger baseline.

    python -m scripts.score_agent_outcome output/agent_runs/2026-0*.jsonl

THE WALK-FORWARD AXIS. On days he never narrated there are no fills of his to
agree with, so agreement is unmeasurable and outcome is the only test. This
asks of the agent exactly what `trader_selection_effect.py` asks of him:

  of the in-window triggers available on the days it ran, do the ones the
  agent TOOK run further than the ones it passed?

Deliberately the same machinery as the human measurement — same trigger
pool builder (`raw_trigger_census.day_rows`), same 2m+3m dedup, same
in-window restriction, same `run_mfe_r` metric, same permutation test with
the same seed and draw count. That makes the agent's number directly
comparable to his: **median run 2.02R, P(2R) 55.0% vs a 36.3% baseline, at
p ≈ 0.07 over n = 20** (corrected reading; the old 5.48R figure is
withdrawn — see docs/FINDINGS-selection-effect.md).

TWO CONSTRUCTION CHOICES INHERITED, both of which decided the human answer:

1. **Matching is CAUSAL.** A trigger counts as the agent's pick only if it
   closed at or before the fill minute. The two-sided window that let a
   later candle be credited was lookahead in the matcher itself.
2. **The baseline is IN-WINDOW.** The session windows are a hard mechanical
   constraint the orchestrator enforces for free; an all-hours baseline
   credits judgment for that. Both print; in-window is the one that speaks
   to judgment.

WHAT A GOOD RESULT LOOKS LIKE, and what it does not mean. Beating the pool
on median run and P(2R) at a low permutation p means the agent's SELECTION
carries information — the same claim made for him, at the same bar. It does
NOT establish profitability: this metric is maximum favourable excursion in
R, not realised R after his management rules, and it says nothing about
fills he never got. Realised R is in the run logs; this is the selection
question only.

Sample-size honesty, stated up front because it bit the human measurement:
his own 20 matched picks clear the bar only at p ≈ 0.07. An agent run of a
dozen fills will not settle anything either. This is built for the Feb-July
walk-forward, where n gets large enough to speak.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars
from scripts.raw_trigger_census import day_rows
from src.htf_ma.levels import NY

SEED = 20260810          # same seed/draws as trader_selection_effect.py
NDRAW = 20_000
WINDOWS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 660)}
HHMM = re.compile(r"(?<![\d:])([01]?\d|2[0-3]):([0-5]\d)(?!:?\d)")

HUMAN = {"median": 2.02, "p2r": 0.550, "base_median": 1.20,
         "base_p2r": 0.363, "n": 20, "p": 0.07}


def _payload(r: dict) -> dict:
    out = dict(r)
    if isinstance(r.get("output"), dict):
        out.update(r["output"])
    return out


def load_fills(paths: list[Path]) -> pd.DataFrame:
    """Agent FILLS only — a take whose limit actually filled. Unfilled limits
    are real outcomes but they are not selections of a trigger's forward run,
    and counting them would flatter the agent by dropping its worst entries."""
    rows = []
    for p in paths:
        sess_day = p.stem
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            pay = _payload(r)
            dec = str(pay.get("decision", ""))
            if not dec.startswith("take"):
                continue
            outcome = str(pay.get("outcome", "")).lower()
            if outcome.startswith("no_fill") or pay.get("filled") is False:
                continue
            m = HHMM.search(str(r.get("decision_minute", "")))
            if not m:
                continue
            rows.append({
                "sess_day": sess_day,
                "hm": int(m.group(1)) * 60 + int(m.group(2)),
                "direction": 1 if str(pay.get("direction", "")).lower().startswith("l")
                             else -1,
                "conviction": pay.get("conviction"),
                "decision": dec,
                "candidate_id": r.get("candidate_id"),
            })
    return pd.DataFrame(rows)


def build_pool(bars: pd.DataFrame, days: list[str], tfs=(2, 3)) -> pd.DataFrame:
    """Identical construction to trader_selection_effect.build_triggers:
    2m+3m, deduplicated to one row per (day, direction, 3-min bucket) so a
    single move is not counted twice."""
    rows = []
    for d in days:
        rows.extend(day_rows(bars, d))
    T = pd.DataFrame(rows)
    if T.empty:
        return T
    T = T[T.tf.isin(tfs)].copy()
    T["bucket"] = T.hm // 3
    T = (T.sort_values(["sess_day", "direction", "hm"])
          .drop_duplicates(["sess_day", "direction", "bucket"]))
    T["win"] = [next((k for k, (a, b) in WINDOWS.items() if a <= h <= b), None)
                for h in T.hm]
    return T


def match_causal(F: pd.DataFrame, T: pd.DataFrame, tol: int = 15) -> pd.DataFrame:
    """A trigger is the agent's pick only if it closed AT OR BEFORE the fill
    minute, same direction, same day, within `tol` minutes. Causal by
    construction — no later candle may be credited as the selection."""
    picks = []
    for f in F.itertuples():
        cand = T[(T.sess_day == f.sess_day)
                 & (T.direction == f.direction)
                 & (T.hm <= f.hm)
                 & (T.hm >= f.hm - tol)]
        if len(cand):
            picks.append(cand.iloc[(f.hm - cand.hm).argmin()])
    return pd.DataFrame(picks)


def _perm(sel, pool, rng, day_matched):
    cnt = sel.groupby("sess_day").size()
    by_day = {d: g.run_mfe_r.to_numpy() for d, g in pool.groupby("sess_day")}
    flat = pool.run_mfe_r.to_numpy()
    med = np.empty(NDRAW)
    p2 = np.empty(NDRAW)
    for i in range(NDRAW):
        if day_matched:
            parts = [rng.choice(by_day[d], size=min(k, len(by_day[d])),
                                replace=False)
                     for d, k in cnt.items() if d in by_day]
            pick = np.concatenate(parts) if parts else flat[:1]
        else:
            pick = rng.choice(flat, size=min(len(sel), len(flat)), replace=False)
        med[i] = np.median(pick)
        p2[i] = (pick >= 2.0).mean()
    return med, p2


def effect(sel: pd.DataFrame, pool: pd.DataFrame, label: str) -> None:
    n = len(sel)
    if n == 0 or pool.empty:
        print(f"\n   {label}: no matched picks — nothing to measure")
        return
    obs_med = sel.run_mfe_r.median()
    obs_p2 = (sel.run_mfe_r >= 2.0).mean()
    base_med = pool.run_mfe_r.median()
    base_p2 = (pool.run_mfe_r >= 2.0).mean()
    ndays = pool.sess_day.nunique()

    print(f"\n   {label}: {n} agent picks from a pool of {len(pool)} "
          f"({len(pool) / ndays:.1f}/day over {ndays} days)")
    print(f"      median run   AGENT {obs_med:5.2f}R   baseline {base_med:5.2f}R")
    print(f"      P(2R)        AGENT {obs_p2 * 100:5.1f}%   baseline "
          f"{base_p2 * 100:5.1f}%")
    for dm, nm in ((True, "day-matched (strict)"), (False, "pooled (loose)")):
        rng = np.random.default_rng(SEED)
        med, p2 = _perm(sel, pool, rng, dm)
        pm, pp = (med >= obs_med).mean(), (p2 >= obs_p2).mean()
        print(f"      perm {nm:22s} p(median) {pm:.4f}   p(P2R) {pp:.4f}   "
              f"null median-run {med.mean():.2f} "
              f"[p95 {np.percentile(med, 95):.2f}]")
    if n < 25:
        print(f"      !! n = {n}. His own 20 picks clear this bar only at "
              f"p ~= 0.07 — treat as directional, not settled.")



# ---------------------------------------------------------------- realised R
# HIS BAR, stated 2026-08-11: "if it can hold 50%+ WR at around average 2R
# I'll know it's in the ballpark of what I'm at." That is REALISED R after
# management, which is NOT what the selection test below measures — so it
# gets its own scorecard, first, because it is the one he actually cares
# about.
#
# Grounding, from committed data:
#   his January (42 decisions / 14 days): 67% WR, avg win +1,336 vs avg loss
#   -800 USD -> a 1.67 win/loss ratio, expectancy ~ +0.79R/trade.
#   his narrated week (11 takes with recoverable R): 9W / 2L = 82% WR,
#   avg win 2.87R, avg loss 0.73R — his own words call it the cleanest week
#   of the five, so it is a ceiling, not a bar.
# His stated bar (50% WR, 2R winners -> ~+0.5R/trade) is therefore MORE
# FORGIVING than his own January. Report against both.
HIS_BAR = {"wr": 0.50, "avg_win_r": 2.0}
HIS_JAN = {"wr": 0.67, "ratio": 1.67, "n": 42, "days": 14}


def realised(paths: list[Path]) -> None:
    """Realised R from the exit rows — win rate, average winner, expectancy."""
    rs = []
    for p in paths:
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
            v = r.get("r_result")
            if isinstance(v, (int, float)):
                rs.append((p.stem, r.get("candidate_id"), float(v)))
    if not rs:
        print("\n  REALISED — no exit rows with r_result found.")
        return

    vals = np.array([x[2] for x in rs])
    wins, losses = vals[vals > 0], vals[vals < 0]
    scratches = vals[vals == 0]
    wr = len(wins) / max(len(wins) + len(losses), 1)
    aw = wins.mean() if len(wins) else 0.0
    al = abs(losses.mean()) if len(losses) else 0.0
    exp = vals.mean()

    print("\nREALISED R — the bar he actually set")
    print(f"  {len(rs)} closed trades over {len({x[0] for x in rs})} session-day(s)"
          + (f", {len(scratches)} scratch" if len(scratches) else ""))
    print(f"  win rate      {wr * 100:5.1f}%   ({len(wins)}W / {len(losses)}L)")
    print(f"  avg winner    {aw:5.2f}R      avg loser {al:5.2f}R")
    print(f"  expectancy    {exp:+5.2f}R/trade     total {vals.sum():+.2f}R")

    ok_wr = wr >= HIS_BAR["wr"]
    ok_aw = aw >= HIS_BAR["avg_win_r"] - 0.15      # "around 2R"
    print("\n  vs HIS BAR (>=50% WR, ~2R average winner):")
    print(f"     win rate      {'MEETS' if ok_wr else 'BELOW'} the bar")
    print(f"     avg winner    {'MEETS' if ok_aw else 'BELOW'} the bar")
    print(f"  vs HIS JANUARY ({HIS_JAN['wr'] * 100:.0f}% WR, {HIS_JAN['ratio']:.2f} "
          f"win/loss ratio over {HIS_JAN['n']} decisions):")
    ratio = (aw / al) if al else float("inf")
    print(f"     agent ratio   {ratio:.2f}  (his {HIS_JAN['ratio']:.2f})")
    if len(rs) < 30:
        print(f"\n  !! n = {len(rs)}. A win rate on under ~30 trades swings "
              f"double digits on one trade.")
        print("     Directional only until the walk-forward has run.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run JSONLs (globs ok)")
    ap.add_argument("--tol", type=int, default=15,
                    help="max minutes a trigger may precede the fill (default 15)")
    a = ap.parse_args()

    paths = sorted({Path(p) for pat in a.runs for p in glob.glob(pat)})
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise SystemExit("no run files matched")

    realised(paths)

    F = load_fills(paths)
    if F.empty:
        raise SystemExit("no filled agent trades in those runs")
    days = sorted(F.sess_day.unique())

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    T = build_pool(bars, days)
    if T.empty:
        raise SystemExit("trigger pool empty for those days")

    sel = match_causal(F, T, tol=a.tol)
    matched, total = len(sel), len(F)

    print("\nOUTCOME — agent selection vs same-day trigger baseline")
    print(f"  {len(paths)} run(s), {len(days)} session-day(s): "
          f"{days[0]} … {days[-1]}")
    print(f"  {total} agent fills, {matched} matched causally to a trigger "
          f"(±{a.tol}min, same direction, trigger at or before the fill)")
    if matched < total:
        print(f"  {total - matched} unmatched — logged, not dropped silently: "
              f"an entry with no preceding trigger is itself a finding.")

    effect(sel, T, "ALL HOURS (loose — window is a free mechanical constraint)")
    inw = T[T.win.notna()]
    sel_in = sel[sel.win.notna()] if "win" in sel.columns else sel
    effect(sel_in, inw, "IN-WINDOW (the one that speaks to judgment)")

    print(f"\n  His benchmark, same machinery: median {HUMAN['median']}R, "
          f"P(2R) {HUMAN['p2r'] * 100:.1f}% vs a {HUMAN['base_p2r'] * 100:.1f}% "
          f"baseline,")
    print(f"  n = {HUMAN['n']}, p ~= {HUMAN['p']}. Beating the pool here is the "
          f"SAME claim at the SAME bar.")
    print("  Note: run_mfe_r is maximum favourable excursion, NOT realised R "
          "after management.")
    print("  Realised R lives in the run logs; this measures selection only.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
