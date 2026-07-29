#!/usr/bin/env python3
"""BASE-RATES DIGEST (Angus, 18 Jul): give the agent the oracle stand-down dataset
to refer to when forming its regime thesis — not raw rows, but the distilled base
rates of the last three years: P(FLAT / rotation-best / momentum-best) and the
oracle+SD expectancy, conditioned on the features the briefing already shows.

This is the counterweight to the fear inputs. Today the briefing says "red folder,
shocks elevated" and nothing answers "...and how often did trading PAY on mornings
like that?" The digest answers with counts, so prudence gets priced instead of
assumed. Companion to the A1 analog block: analogs = the 15 nearest days;
base rates = the whole book's priors.

    python -m scripts.build_base_rates                    # full history (live use)
    python -m scripts.build_base_rates --asof 2025-04-01  # replay-safe cutoff

--asof matters: a graded replay must not read base rates computed over its own
future. For the Q2 2025 exam generate with --asof 2025-04-01.

Output: output/base_rates.json (briefing-embeddable) + printed preview.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def action(e3, e4):
    # Angus ruling (18 Jul): best-book $0 on no trades counts as FLAT
    return "FLAT" if max(e3, e4) <= 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")


def table(d, col):
    g = d.groupby(col, observed=True)
    t = pd.DataFrame({
        "n": g.size(),
        "p_flat": g.apply(lambda x: (x.act == "FLAT").mean(), include_groups=False),
        "p_rotation": g.apply(lambda x: (x.act == "ROTATION").mean(), include_groups=False),
        "p_momentum": g.apply(lambda x: (x.act == "MOMENTUM").mean(), include_groups=False),
        "oracle_sd_mean": g.oracle_sd.mean(),
        "rotation_book_mean": g.pl_e3.mean(),
        "momentum_book_mean": g.pl_e4.mean(),
    }).round(2)
    return {str(k): {c: (int(v) if c == "n" else float(v)) for c, v in row.items()}
            for k, row in t.iterrows()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None,
                    help="use only days strictly before this date (replay safety)")
    ap.add_argument("--out", default="output/base_rates.json")
    a = ap.parse_args()

    books = pd.concat([
        pd.read_csv("output/allyears_daily_books.csv")[["day", "E3", "E4"]]
        .rename(columns={"E3": "pl_e3", "E4": "pl_e4"}),
        pd.read_csv("output/l2_analog_routing.csv")[["day", "pl_e3", "pl_e4"]],
    ]).drop_duplicates("day")
    dt = pd.read_csv("output/amt_daytypes.csv")
    v = pd.read_csv("output/regime_vector.csv")
    sh = pd.read_csv("output/shock_ruler.csv")
    d = books.merge(dt, on="day", how="inner").merge(v, on="day", how="left",
                                                     suffixes=("", "_v")) \
        .merge(sh, on="day", how="left")
    if a.asof:
        d = d[d.day < a.asof]
    d["act"] = d.apply(lambda x: action(x.pl_e3, x.pl_e4), axis=1)
    d["oracle_sd"] = d[["pl_e3", "pl_e4"]].max(axis=1).clip(lower=0)

    # conditioning buckets (all pre-open features the briefing already carries)
    d["imbal20_bucket"] = pd.cut(d.imbal_share_20, [0, .35, .5, .65, 1],
                                 labels=["<0.35", "0.35-0.5", "0.5-0.65", ">0.65"])
    d["shock_bucket"] = pd.cut(d.shock50_pctl20, [-.01, .5, .85, 1.01],
                               labels=["calm(<p50)", "mid", "elevated(>p85)"])
    d["inv_bucket"] = pd.cut(d.inventory_pts, [-9e9, -40, 40, 9e9],
                             labels=["short>40pts", "neutral", "long>40pts"])
    d["red"] = (d.red_folder_today.fillna(0) > 0).map({True: "red_folder", False: "clear"})
    d["streak_bucket"] = pd.cut(d.streak_imbal, [-1, 0, 2, 99],
                                labels=["0", "1-2", "3+"])

    digest = {
        "generated_from_days": int(len(d)),
        "asof_cutoff": a.asof or "full_history",
        "note": ("Realized best-action base rates from the oracle+stand-down ledger "
                 "(1 NQ contract, $20/pt). 'FLAT' = both books lost (or made $0). "
                 "red_folder is only populated 2026+ until the historical calendar "
                 "lands — treat the 'clear' bucket as mixed before then."),
        "topline": table(d.assign(all="all_days"), "all")["all_days"],
        "by_year": table(d.assign(y=d.day.str[:4]), "y"),
        "by_day_type": table(d[d.type != "unknown"], "type"),
        "by_value_position": table(d.dropna(subset=["value_position"]), "value_position"),
        "by_imbal_share_20": table(d.dropna(subset=["imbal20_bucket"]), "imbal20_bucket"),
        "by_shock_percentile": table(d.dropna(subset=["shock_bucket"]), "shock_bucket"),
        "by_overnight_inventory": table(d.dropna(subset=["inv_bucket"]), "inv_bucket"),
        "by_red_folder": table(d, "red"),
        "by_imbal_streak": table(d.dropna(subset=["streak_bucket"]), "streak_bucket"),
    }
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_text(json.dumps(digest, indent=1))
    print(f"wrote {a.out} ({len(d)} days, asof={digest['asof_cutoff']})")
    for k in ("topline", "by_day_type", "by_shock_percentile", "by_red_folder"):
        print(f"\n== {k} ==")
        print(pd.DataFrame(digest[k] if k != "topline" else {"all": digest[k]})
              .T.to_string())


if __name__ == "__main__":
    main()
