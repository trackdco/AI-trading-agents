"""Orchestrator. Loads data once, builds the CVD book and per-TF signal context once, then
runs the configuration grid (TF x CVD-mode x min-confluence x target-mode), writes a master
summary + per-trade CSVs, a CVD-mode comparison table, monthly split, and an equity curve for
the headline configuration.

    python -m backtester.run                 # full grid + reports
    python -m backtester.run --smoke         # quick single-config smoke test
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

# allow both `python -m backtester.run` and `python backtester/run.py`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backtester import data as D, signals as S, engine as E, report as R
    from backtester.cvd import CVDBook
else:
    from . import data as D, signals as S, engine as E, report as R
    from .cvd import CVDBook


def load_cfg(path="backtester/config.yaml"):
    return yaml.safe_load(open(path))


def build(cfg):
    bars = D.load_bars(cfg["data"]["bars_1m"], cfg["data"]["tz"])
    delta = D.load_footprint_delta(cfg["data"]["cvd_glob"], cfg["data"]["tz"])
    total = D.load_footprint_totals(cfg["data"]["cvd_glob"], cfg["data"]["tz"])
    from .indicators import anchor_session_date  # noqa
    csig = D.session_cvd(delta, D_time(cfg["cvd"]["anchor"]))
    book = CVDBook(delta, total, csig, cfg["cvd"]["swing_lookback_min"],
                   cfg["cvd"]["initiative_delta_pct"])
    ctx = S.Context(bars.copy(), cfg)
    book.bind_price(ctx.close_1m)
    return bars, ctx, book


def D_time(s):
    from datetime import time
    h, m = s.split(":"); return time(int(h), int(m))


def run_grid(cfg, ctx, book, smoke=False):
    out_dir = cfg["reporting"]["out_dir"]; os.makedirs(out_dir, exist_ok=True)
    tfs = cfg["timeframes"]["entry"]
    modes = cfg["cvd"]["modes"]
    confs = cfg["confluence"]["min_confluence_grid"]
    targets = cfg["targets"]["modes"]
    if smoke:
        tfs, modes, confs, targets = ["3min"], ["a"], [4], ["fixed100"]

    # detect candidates once per TF, precompute CVD signals + config-independent execution prep
    cand = {}; ready = {}
    for tf in tfs:
        c = S.detect(ctx, tf, cfg)
        c = E.attach_cvd(c, cfg, tf, book)
        cand[tf] = c
        ready[tf] = E.prepare(ctx, c, cfg, tf, book)
        print(f"[detect] {tf}: {len(c)} raw candidates -> {len(ready[tf])} prepared (fillable, <=70pt stop)")

    summary = []; all_trades = []
    for tf in tfs:
        for mode in modes:
            for mc in confs:
                for tgt in targets:
                    T = E.simulate(ctx, cand[tf], cfg, tf, mode, mc, tgt, book, ready=ready[tf])
                    m = R.metrics(T)
                    m.update(dict(tf=tf, cvd_mode=mode, min_conf=mc, target_mode=tgt))
                    summary.append(m)
                    if len(T):
                        all_trades.append(T)
    Summ = pd.DataFrame(summary)
    Summ.to_csv(f"{out_dir}/summary_grid.csv", index=False)
    if all_trades:
        pd.concat(all_trades, ignore_index=True).to_csv(f"{out_dir}/all_trades.csv", index=False)
    return Summ, cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--headline-tf", default="3min")
    ap.add_argument("--headline-mode", default="b")
    ap.add_argument("--headline-conf", type=int, default=4)
    ap.add_argument("--headline-target", default="fixed100")
    args = ap.parse_args()

    cfg = load_cfg()
    bars, ctx, book = build(cfg)
    print(f"[data] bars {bars.ts_event.min()} -> {bars.ts_event.max()} ({len(bars):,} rows)")

    Summ, cand = run_grid(cfg, ctx, book, smoke=args.smoke)

    print("\n================= MASTER GRID (sorted by PF, n>=15) =================")
    good = Summ[Summ.n >= 15].sort_values("pf", ascending=False)
    cols = ["tf", "cvd_mode", "min_conf", "target_mode", "n", "win", "pf", "exp_usd",
            "net_usd", "maxdd_usd", "months_green"]
    print(good[cols].head(20).to_string(index=False) if len(good) else "  (no config reached n>=15)")

    if args.smoke:
        return

    out_dir = cfg["reporting"]["out_dir"]
    # headline detailed report
    T = E.simulate(ctx, cand[args.headline_tf], cfg, args.headline_tf, args.headline_mode,
                   args.headline_conf, args.headline_target, book)
    title = (f"HEADLINE  tf={args.headline_tf} cvd={args.headline_mode} "
             f"min_conf={args.headline_conf} target={args.headline_target}")
    print("\n" + R.full_report(T, cfg, title))

    # CVD-mode a-d comparison at fixed tf/conf/target
    print("\n=== CVD-mode comparison (tf=%s, min_conf=%d, target=%s) ==="
          % (args.headline_tf, args.headline_conf, args.headline_target))
    moderows = Summ[(Summ.tf == args.headline_tf) & (Summ.min_conf == args.headline_conf)
                    & (Summ.target_mode == args.headline_target)]
    print(R.cvd_mode_table(moderows))

    if len(T):
        p = R.equity_curve(T, f"{out_dir}/equity_headline.png", title)
        T.to_csv(f"{out_dir}/headline_trades.csv", index=False)
        print(f"\nsaved: {out_dir}/summary_grid.csv, headline_trades.csv"
              + (f", {p}" if p else " (matplotlib unavailable, no chart)"))


if __name__ == "__main__":
    main()
