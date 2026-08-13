#!/usr/bin/env python3
"""Run the tomtrades loser autopsy and write the report.

Population is the TRIGGER-ONLY book — every confluence gate off — because that is the
only cell in the ablation with enough trades to answer a separation question. The full
stack had 42 trades in three and a half years; nothing can be learned from that about
which trades lose.

"Trigger only" still means the shift itself: the W-shape (C6), the C7 nested-shift
gate and the stop-size cap are part of the trigger's definition, not confluences, so
they stay on. That matches how the ablation table defined the same row.

    python scripts/tomtrades_autopsy.py [--bars N] [--perm N]
"""
from __future__ import annotations

import argparse
import copy
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.research.tomtrades import autopsy as AU
from src.research.tomtrades import data as D
from src.research.tomtrades import detector as DT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def _md(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "_no rows_"
    cols = [str(c) for c in df.columns]
    body = [["" if pd.isna(v) else (f"{v:.4g}" if isinstance(v, (int, float, np.floating))
                                    else str(v)) for v in row]
            for row in df.itertuples(index=False)]
    w = [max(len(cols[i]), *(len(r[i]) for r in body)) for i in range(len(cols))]
    head = "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(cols)) + " |"
    rule = "|" + "|".join("-" * (x + 2) for x in w) + "|"
    rows = ["| " + " | ".join(r[i].ljust(w[i]) for i in range(len(cols))) + " |" for r in body]
    return "\n".join([head, rule, *rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", type=int, default=0, help="tail N bars (0 = all), for smoke runs")
    ap.add_argument("--perm", type=int, default=200, help="permutations per calibrated statistic")
    a = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config/tomtrades.yaml").read_text())
    gc = D.load(str(ROOT / "data/gc_1m.parquet"))
    dx = D.load(str(ROOT / "data/dx_1m.parquet"))
    j6 = D.load(str(ROOT / "data/6j_1m.parquet"))
    if a.bars:
        gc = gc.tail(a.bars).reset_index(drop=True)
    print(f"GC {len(gc):,} bars  {gc.ts_event.min().date()} -> {gc.ts_event.max().date()}",
          flush=True)

    t = time.time()
    ctx = DT.build_context(gc, cfg, dxy=dx, yen=j6)
    print(f"context {time.time()-t:.0f}s", flush=True)

    t = time.time()
    off = {k: np.ones(len(gc), dtype=bool) for k in ("session", "c1", "c2", "c3", "c4", "c5")}
    sig = DT.detect(ctx, cfg, off)
    print(f"detect {time.time()-t:.0f}s -> {len(sig):,} signals", flush=True)

    # the daily cap is a selection rule, not a confluence: it keeps the first three
    # trades of each day and so biases every clock statistic. The autopsy runs uncapped
    # and prices the cap separately, below.
    cfg_nc = copy.deepcopy(cfg)
    cfg_nc["risk"]["max_trades_per_day"] = 0
    trades = DT.simulate(gc, sig, cfg_nc)
    B = AU.annotate(trades, gc, ctx, cfg)
    OUT.mkdir(exist_ok=True)
    B.to_parquet(OUT / "tomtrades_autopsy_trades.parquet")
    print(f"population {len(B):,} trades over {B.sess_day.nunique():,} days", flush=True)

    arith = AU.arithmetic(B)
    for k, v in arith.items():
        print(f"   {k:<22} {v}", flush=True)

    t = time.time()
    uni = AU.univariate(B, n_perm=a.perm)
    print(f"univariate {time.time()-t:.0f}s", flush=True)
    uni.to_csv(OUT / "tomtrades_autopsy_univariate.csv", index=False)
    print(uni.to_string(index=False), flush=True)

    rr_tab = AU.bucket_table(B, "rr_at_entry", q=5)
    rho_rr, null_rr, p_rr = AU.calibrate(
        lambda d: AU.spearman(d["rr_at_entry"].to_numpy(dtype=float), d["win"].to_numpy()),
        B, n_perm=a.perm)

    t = time.time()
    n_mod = min(a.perm, 40)          # each null re-runs the whole cross-validation
    auc_all = AU.oos_auc(B, AU.MODEL_COLS)
    mc = AU.calibrate_dict(lambda d: AU.model_stats(d, AU.CLEAN_COLS), B, n_perm=n_mod)
    auc_clean, null_auc, p_auc = mc["auc"]
    auc_within, null_within, p_within = mc["auc_within_rr"]
    top_ev, null_top, p_top = mc["top_bin_ev"]
    print(f"model {time.time()-t:.0f}s  auc_all={auc_all:.4f} clean={auc_clean:.4f} "
          f"null={np.nanmean(null_auc):.4f}+-{np.nanstd(null_auc):.4f} p={p_auc:.3f}; "
          f"within-RR={auc_within:.4f} p={p_within:.3f}; "
          f"top-bin EV={top_ev:+.4f} p={p_top:.3f}", flush=True)
    sel = AU.selection_table(B, AU.CLEAN_COLS)

    census = AU.exit_census(B)
    exc = AU.loser_excursions(B)
    costs = AU.cost_ladder(B, tick=float(cfg["instrument"]["tick_size"]))
    stab = AU.stability(B, "year")
    clock = AU.bucket_table(B, "minute_of_hour", q=5)

    # Rule variants, priced not tuned. Every variant runs on the SAME signal subset as
    # the baseline: the impulse target skips signals whose 50% level was already gone,
    # and a fixed-RR run would silently re-admit all of them, so the comparison would be
    # between different books rather than between two exits on one book.
    same = sig[sig["signal_ts"].isin(set(B["signal_ts"]))].reset_index(drop=True)
    variants = []

    def add(name: str, t: pd.DataFrame) -> None:
        r = t["pnl_r"] if "pnl_r" in t else t["out"]
        d = t.assign(sess_day=pd.to_datetime(t["entry_ts"]).dt.tz_convert(
            "America/New_York").dt.date, out=r)
        h1, h2 = AU.split_half(d)
        variants.append({"variant": name, "n": len(t),
                         "win_pct": 100 * float((r > 0).mean()), "ev": float(r.mean()),
                         "ev_first_half": h1, "ev_second_half": h2})

    add("baseline (uncapped)", B)
    add("max 3 trades/day", DT.simulate(gc, sig, cfg))
    for be in (0.15, 0.25, 0.40, 0.60):
        add(f"breakeven stop at +{be:.2f}R", DT.simulate(gc, same, cfg_nc, be_trigger_r=be))
    cfg_rr = copy.deepcopy(cfg_nc)
    cfg_rr["execution"]["target_mode"] = "fixed_rr"
    for rr in (0.5, 1.0, 1.5, 2.0):
        cfg_rr["execution"]["fixed_rr"] = rr
        add(f"fixed {rr:.1f}R target", DT.simulate(gc, same, cfg_rr))
    var_tab = pd.DataFrame(variants)
    var_tab.to_csv(OUT / "tomtrades_autopsy_variants.csv", index=False)
    print(var_tab.to_string(index=False), flush=True)

    lines = [
        "# tomtrades CBR — loser autopsy", "",
        "RESEARCH ONLY. Reverse-engineered from public videos and UNVALIDATED.",
        "",
        (f"- population: trigger-only, uncapped — {arith['n']:,} trades over "
         f"{arith['days']:,} NY days"),
        f"- period: {gc.ts_event.min().date()} -> {gc.ts_event.max().date()}",
        f"- permutations per calibrated statistic: {a.perm}",
        f"- day-clustered bootstrap draws: {AU.DRAWS}",
        "", "## 1. The arithmetic", "",
        _md(pd.DataFrame([arith])), "",
        "## 2. Univariate separation, entry-time features only", "",
        "`rho_win` and `rho_ev` are rank correlations with the win bit and with realised R.",
        "`p_*` is the share of outcome-shuffled nulls that reached the same magnitude.",
        "",
        _md(uni.round(4)), "",
        "## 3. Win rate against reward:risk at entry", "",
        (f"Spearman(rr_at_entry, win) = {rho_rr:+.4f}, null "
         f"{np.nanmean(null_rr):+.4f} +- {np.nanstd(null_rr):.4f}, p = {p_rr:.3f}"), "",
        _md(rr_tab.round(4)), "",
        "## 4. Multivariate: is a winner identifiable at entry?", "",
        f"- day-grouped 5-fold out-of-sample AUC, all actionable features: **{auc_all:.4f}**",
        f"- same, Law-2 (risk-coupled) features dropped: **{auc_clean:.4f}**",
        (f"- shuffled-outcome null: {np.nanmean(null_auc):.4f} "
         f"+- {np.nanstd(null_auc):.4f}, p = {p_auc:.3f}"),
        (f"- **AUC holding reward:risk fixed (pooled within RR quintiles): "
         f"{auc_within:.4f}**, null {np.nanmean(null_within):.4f} "
         f"+- {np.nanstd(null_within):.4f}, p = {p_within:.3f}"),
        (f"- realised EV of the top out-of-sample-EV quintile: **{top_ev:+.4f}R**, null "
         f"{np.nanmean(null_top):+.4f} +- {np.nanstd(null_top):.4f}, p = {p_top:.3f}"), "",
        "### Trades ranked by out-of-sample expected value", "",
        _md(sel.round(4)), "",
        "## 4b. Session, and the stratum the null cannot see", "",
        "Outcomes are shuffled WITHIN session, so a session main effect survives every",
        "shuffle by construction and has no p-value here — read the first table as",
        "intervals, not as a test. Direction is deliberately NOT a shuffle cell, so",
        "`is_long` in section 2 is a real test; the second table is its detail.", "",
        _md(AU.category_table(B, "session").round(4)), "",
        _md(AU.category_table(B, "mech_dir").round(4)), "",
        "## 5. Exit anatomy (post-entry — BR-41, describes, does not select)", "",
        _md(census.round(4)), "", "How far the losers got before dying:", "",
        _md(exc.round(2)), "",
        "## 6. Rule variants, priced", "",
        f"A menu of {len(var_tab)} variants; treat the best cell as a hypothesis, not a result.",
        "", _md(var_tab.round(4)), "",
        "## 7. Transaction costs", "", _md(costs.round(4)), "",
        "## 8. Stability", "", _md(stab.round(4)), "",
        "## 9. Minute of hour, uncapped", "", _md(clock.round(4)), "",
    ]
    (OUT / "tomtrades_autopsy.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT/'tomtrades_autopsy.md'}", flush=True)


if __name__ == "__main__":
    main()
