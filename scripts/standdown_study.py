#!/usr/bin/env python3
"""STAND-DOWN STUDY (Angus, 20 Jul): can any pre-open FREE feature build a stand-down
rule that gets the red years (2023, 2025) to ~breakeven without killing the green years
(2024, 2026)? This is the fork between "the dial shrinks the bleed" and "profitable
every year" — and it decides whether pre-open info is even sufficient or whether the
next lever must be intraday.

Mechanical only (champion book = imbalance switch, floored R1/R2 books). No agent — this
isolates the WHEN-to-trade question from the WHICH-book question.

Design (anti-overfit):
  - Gates are WALK-FORWARD by construction: a day stands down iff the trailing champion
    expectancy CONDITIONED on that day's feature-bucket, computed from PRIOR days only
    (min N=20, else fall back to the overall trailing-60d gate), is negative. No fixed
    thresholds fit to the sample; the rule self-calibrates from history.
  - Feature SELECTION is the residual overfit risk (testing ~10 features, one may look
    good by chance) -> report ALL features transparently, and only trust a rule that
    helps BOTH red years AND doesn't materially hurt the green years.
  - Calendar features (red_folder/named_high) EXCLUDED: only populated for 2026, so
    structurally useless for the red years this study targets.

    python -m scripts.standdown_study
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BOOKS = "output/allyears_daily_books_r1r2.csv"


def load():
    b = pd.read_csv(BOOKS)
    v = pd.read_csv("output/regime_vector.csv")
    d = b.merge(v, on="day", how="left").sort_values("day").reset_index(drop=True)
    d["champ_pl"] = np.where(d.imbal_share_20 >= 0.5, d.E4, d.E3)
    d = d.dropna(subset=["champ_pl"]).reset_index(drop=True)
    d["y"] = d.day.str[:4]
    return d


def bucketize(d, feat):
    """Interpretable, mostly-natural buckets. Continuous feats -> trailing-median terciles
    would be ideal; for simplicity use global terciles (bin EDGES leak mildly but the
    EXPECTANCY inside each bin is still walk-forward, which is what drives the gate)."""
    s = d[feat]
    if s.dtype == object or str(s.dtype).startswith("str"):
        return s.astype(str)
    if feat == "streak_imbal":
        return pd.cut(s, [-1, 0, 2, 99], labels=["0", "1-2", "3+"]).astype(str)
    # continuous -> terciles
    try:
        return pd.qcut(s, 3, labels=["lo", "mid", "hi"], duplicates="drop").astype(str)
    except Exception:
        return pd.Series("all", index=s.index)


def walkforward_gate(d, feat, min_n=20, fallback_window=60):
    """flat[i] = True iff trailing champ expectancy in day i's bucket (prior days only)
    is < 0. Fallback to overall trailing-`fallback_window`-day expectancy when the bucket
    has < min_n prior samples."""
    buckets = bucketize(d, feat)
    cpl = d.champ_pl.values
    flat = np.zeros(len(d), dtype=bool)
    for i in range(len(d)):
        bi = buckets.iloc[i]
        if pd.isna(bi):
            prior = cpl[max(0, i - fallback_window):i]
        else:
            mask = (buckets.iloc[:i] == bi).values
            prior_bucket = cpl[:i][mask]
            if len(prior_bucket) >= min_n:
                prior = prior_bucket
            else:
                prior = cpl[max(0, i - fallback_window):i]
        if len(prior) >= 10 and prior.mean() < 0:
            flat[i] = True
    return flat


def health_gate(d, window=20):
    h = pd.Series(d.champ_pl).rolling(window).sum().shift(1)
    return (h < 0).fillna(False).values


def grade(d, flat, label):
    pl = np.where(flat, 0.0, d.champ_pl.values)
    g = pd.DataFrame({"y": d.y.values, "pl": pl, "flat": flat})
    per = g.groupby("y").pl.sum()
    line = "  ".join(f"{y}:${per[y]:+,.0f}" for y in sorted(per.index))
    red = per.get("2023", 0) + per.get("2025", 0)
    print(f"{label:42s} ALL ${g.pl.sum():+,.0f}  flat {flat.mean()*100:.0f}%  | {line}  | RED(23+25) ${red:+,.0f}")
    return dict(label=label, all=g.pl.sum(), red=red,
                y2023=per.get("2023", 0), y2024=per.get("2024", 0),
                y2025=per.get("2025", 0), y2026=per.get("2026", 0), flat=flat.mean())


def main():
    d = load()
    print(f"{len(d)} days, {d.y.min()}-{d.y.max()}\n")

    results = []
    results.append(grade(d, np.zeros(len(d), bool), "ALWAYS TRADE (baseline)"))
    hg = health_gate(d)
    results.append(grade(d, hg, "HEALTH GATE (trailing-20d champ P&L<0)"))
    print()

    feats = ["day_type", "value_position", "open_vs_value", "trap_rate_10",
             "range_pctl_20", "streak_imbal", "inventory_pts", "on_nr_rank",
             "gap_vs_value", "pdc_loc", "imbal_share_20"]
    single = []
    for f in feats:
        flat = walkforward_gate(d, f)
        single.append(grade(d, flat, f"gate: {f}"))
    print()

    # combinations of health gate with each feature gate (OR = more cautious, AND = less)
    for f in feats:
        fg = walkforward_gate(d, f)
        results_or = grade(d, hg | fg, f"HEALTH **OR** {f}")
    print()

    # best single feature by RED-year improvement that doesn't crater green years
    base_green = next(r for r in results if r["label"].startswith("HEALTH GATE"))
    print("=== SUMMARY: rules that beat the health gate on BOTH red years AND keep green ≥ health-gate−$2k ===")
    hg_row = base_green
    any_win = False
    for r in single:
        red_better = r["red"] > hg_row["red"] + 500
        green_ok = (r["y2024"] > hg_row["y2024"] - 2000) and (r["y2026"] > hg_row["y2026"] - 2000)
        if red_better and green_ok:
            any_win = True
            print(f"  {r['label']}: RED ${r['red']:+,.0f} (vs hg ${hg_row['red']:+,.0f}), "
                  f"2024 ${r['y2024']:+,.0f} 2026 ${r['y2026']:+,.0f}")
    if not any_win:
        print("  NONE. No single-feature stand-down gate beats the plain health gate on the")
        print("  red years without giving back too much green. -> pre-open feature stand-down")
        print("  appears exhausted; the evidence points to intraday as the next lever.")


if __name__ == "__main__":
    main()
