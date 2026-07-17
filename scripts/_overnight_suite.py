#!/usr/bin/env python3
"""ANGUS-authorized overnight suite (pass 10): 15 arms on February.

Phase A - the three pass-9 rulings isolated + combined (attribution)
Phase B - TF/pattern exclusion matrix on the best A-engine (filter hypotheses; Feb-derived
          CANDIDATES, not rules, until Mar-Jul out-of-sample)
Phase C - VWAP-touch semantics on the best B-base

Never touches config/strategy.yaml: works on BacktestConfig copies. Loads data + triggers
once. Appends each arm's row to the report as it completes (crash-resilient). Emits
output/overnight_suite_report.md.
"""
import ast
import sys
import traceback
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.calibrate import calibrate  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate, write_outputs  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
REPORT = Path("output/overnight_suite_report.md")
PROGRESS = Path("output/overnight_progress.log")


def load_all():
    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    df = pd.read_parquet(full if full.exists() else ref)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)
    rows = pd.read_csv("output/triggers_feb.csv").to_dict("records")
    for r in rows:
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
    trigs = [Trigger(**r) for r in rows]
    return feb, trigs


def stats(trades, equity, res):
    n = len(trades)
    wins = [t.r_multiple for t in trades if t.r_multiple > 0]
    losses = [t.r_multiple for t in trades if t.r_multiple < 0]
    tot = sum(t.r_multiple for t in trades)
    gross_w, gross_l = sum(wins), -sum(losses)
    cum = equity["cum_r"].tolist() if not equity.empty else [0.0]
    peak, maxdd = 0.0, 0.0
    for c in cum:
        peak = max(peak, c)
        maxdd = max(maxdd, peak - c)
    top2 = sum(sorted((t.r_multiple for t in trades if t.r_multiple > 0), reverse=True)[:2])
    matched = res["matched"]
    m_win = 0
    for m in matched:
        try:
            if (float(m["hand"].get("r_mult", 0)) > 0
                    and float(m["engine"].get("r_multiple", 0)) > 0):
                m_win += 1
        except Exception:
            pass
    return {
        "trades": n, "wins": len(wins), "win_pct": 100 * len(wins) / n if n else 0.0,
        "tot_r": tot, "r_per": tot / n if n else 0.0,
        "avg_win": sum(wins) / len(wins) if wins else 0.0,
        "avg_loss": sum(losses) / len(losses) if losses else 0.0,
        "pf": gross_w / gross_l if gross_l > 0 else float("inf"),
        "maxdd": maxdd,
        "top2_pct": 100 * top2 / tot if tot > 0 else float("nan"),
        "matched": len(matched), "matched_won": m_win,
    }


def splits(trades):
    out = {}
    for key in ("pattern", "tf"):
        agg = {}
        for t in trades:
            k = getattr(t, key)
            a = agg.setdefault(k, [0, 0, 0.0])
            a[0] += 1
            a[1] += t.r_multiple > 0
            a[2] += t.r_multiple
        out[key] = {k: (v[0], 100 * v[1] / v[0], v[2]) for k, v in sorted(agg.items())}
    return out


def main():
    feb, trigs = load_all()
    cal = None  # simulate loads the news calendar itself
    base = load_backtest_config()   # committed: E3 + walkout ON + named list ON + prox gate

    def flt_none(t):
        return True

    def no5(t):
        return t.tf != "5min"

    def nob2(t):
        return t.pattern != "B2"

    def nouncl(t):
        return t.pattern != "unclassified"

    def no5_nob2(t):
        return t.tf != "5min" and t.pattern != "B2"

    def tight(t):
        return t.tf in ("1min", "2min", "3min") and t.pattern in ("A", "B")

    def no1(t):
        return t.tf != "1min"

    PRE = {"walkout_under_floor": False, "named_high_impact": []}
    ARMS = [
        ("A0 baseline (pre-rulings)", PRE, flt_none),
        ("A1 +walkout", {"named_high_impact": []}, flt_none),
        ("A2 +E4 only", {**PRE, "entry_variant": "E4"}, flt_none),
        ("A3 +PCE-list", {"walkout_under_floor": False}, flt_none),
        ("A4 walkout+list+E4", {"entry_variant": "E4"}, flt_none),
        ("A4b walkout+list (E3)", {}, flt_none),
    ]

    results = []
    REPORT.parent.mkdir(exist_ok=True)
    PROGRESS.write_text("overnight suite started\n")

    def run_arm(name, upd, flt):
        cfg = base.model_copy(update=upd)
        tt = [t for t in trigs if flt(t)]
        trades, verdicts, equity = simulate(feb, tt, cfg, calendar=cal)
        write_outputs(trades, verdicts, equity)
        res = calibrate()
        s = stats(trades, equity, res)
        s["name"], s["splits"] = name, splits(trades)
        results.append(s)
        with PROGRESS.open("a") as f:
            f.write(f"done {name}: {s['trades']}tr {s['win_pct']:.1f}% {s['tot_r']:+.2f}R "
                    f"M{s['matched']}\n")
        return s

    for name, upd, flt in ARMS:
        try:
            run_arm(name, upd, flt)
        except Exception:
            with PROGRESS.open("a") as f:
                f.write(f"ARM FAILED {name}\n{traceback.format_exc()}\n")

    # Phase B base = better of A4 / A4b by total R
    a4 = next((r for r in results if r["name"].startswith("A4 ")), None)
    a4b = next((r for r in results if r["name"].startswith("A4b")), None)
    if a4 and a4b:
        b_upd = {"entry_variant": "E4"} if a4["tot_r"] >= a4b["tot_r"] else {}
        b_tag = "A4(E4)" if a4["tot_r"] >= a4b["tot_r"] else "A4b(E3)"
    else:
        b_upd, b_tag = {}, "A4b(E3)"

    BARMS = [
        (f"B1 {b_tag} -5min", b_upd, no5),
        (f"B2 {b_tag} -B2", b_upd, nob2),
        (f"B3 {b_tag} -unclassified", b_upd, nouncl),
        (f"B4 {b_tag} -5min-B2", b_upd, no5_nob2),
        (f"B5 {b_tag} A/B only 1-3min", b_upd, tight),
        (f"B6 {b_tag} -1min", b_upd, no1),
        ("B7 baseline(A0) -5min-B2", PRE, no5_nob2),
        (f"C1 {b_tag} +touch", {**b_upd, "require_vwap_touch": True, "require_bb_vwap": False},
         flt_none),
    ]
    for name, upd, flt in BARMS:
        try:
            run_arm(name, upd, flt)
        except Exception:
            with PROGRESS.open("a") as f:
                f.write(f"ARM FAILED {name}\n{traceback.format_exc()}\n")

    # ---- report ----
    lines = [
        "# Overnight suite — February 2026 (pass 10)",
        "",
        f"_Generated {pd.Timestamp.now(tz=NY).strftime('%Y-%m-%d %H:%M ET')}. "
        "All arms on the committed Feb slice; E3/E4 = entry variants; "
        "'walkout' = P5.16 ruling; 'PCE-list' = P5.14 named high-impact list._",
        "",
        "**GUARDRAIL:** Phase B/C exclusions are February-derived CANDIDATES — they become "
        "rules only after surviving Mar–Jul out-of-sample (data pending re-pull, Brake). "
        "Phase A items are Angus rulings and stand on doctrine.",
        "",
        "| arm | tr | wins | win% | totR | R/tr | avgW | avgL | PF | maxDD | top2% | M | Mwon |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in results:
        pf = f"{s['pf']:.2f}" if s["pf"] != float("inf") else "inf"
        t2 = f"{s['top2_pct']:.0f}%" if s["top2_pct"] == s["top2_pct"] else "n/a"
        lines.append(
            f"| {s['name']} | {s['trades']} | {s['wins']} | {s['win_pct']:.1f}% "
            f"| {s['tot_r']:+.2f} | {s['r_per']:+.3f} | {s['avg_win']:+.2f} "
            f"| {s['avg_loss']:+.2f} | {pf} | {s['maxdd']:.2f} | {t2} "
            f"| {s['matched']} | {s['matched_won']} |")

    best = max(results, key=lambda s: s["tot_r"])
    lines += ["", f"## Best arm by total R: {best['name']}", ""]
    for key, title in (("pattern", "By pattern"), ("tf", "By timeframe")):
        lines += [f"### {title}", "", "| value | trades | win% | totR |", "|---|---|---|---|"]
        for k, (n, wp, tr) in best["splits"][key].items():
            lines.append(f"| {k} | {n} | {wp:.0f}% | {tr:+.2f} |")
        lines.append("")

    bestw = max(results, key=lambda s: (s["win_pct"], s["tot_r"]))
    lines += [f"**Best win-rate arm:** {bestw['name']} — {bestw['win_pct']:.1f}% "
              f"({bestw['tot_r']:+.2f}R)", ""]
    REPORT.write_text("\n".join(lines))
    print(f"wrote {REPORT} with {len(results)} arms")


if __name__ == "__main__":
    main()
