#!/usr/bin/env python3
"""A1 (v0.4 proposal): the ANALOG BLOCK, precomputed for every day in the library.

Standalone engine-lane artifact — Pat's briefing builder joins one row per day and
drops the JSON block straight into the agent's briefing. Nothing in the live desk
pipeline changes until Pat chooses to include the column, so in-flight v0.4 runs
are untouched.

For each session day: the K=15 most similar PRIOR days by normalized regime-vector
distance (same metric as scripts/l2_analog_benchmark.py, walk-forward, zero
lookahead), each with its realized oracle action (FLAT if both books red, else the
better book) and both book P&Ls. Summary fields give the agent the base rates it
has been trying to guess: how days that looked like today actually resolved.

    python -m scripts.build_analog_briefing   -> output/analog_briefing.csv

Book P&L sources: allyears_daily_books.csv (2023-01 .. 2026-01) +
l2_analog_routing.csv (2026-02 .. present). red_folder is 0 for 2023-25 until the
historical FF calendar lands, so the distance metric leans on tape features there.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FEATS = ["imbal_share_20", "imbal_share_10", "trap_rate_10", "range_pctl_20",
         "gap_open_pts", "streak_imbal", "red_folder_today"]
K = 15
MIN_ANALOGS = 10


def action(e3, e4):
    return "FLAT" if max(e3, e4) < 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")


def main():
    a = pd.read_csv("output/allyears_daily_books.csv")[["day", "E3", "E4"]] \
        .rename(columns={"E3": "pl_e3", "E4": "pl_e4"})
    l2 = pd.read_csv("output/l2_analog_routing.csv")[["day", "pl_e3", "pl_e4"]]
    books = pd.concat([a, l2]).drop_duplicates("day").set_index("day")

    V = pd.read_csv("output/regime_vector.csv")
    V["is_imbal"] = (V.day_type == "imbalanced").astype(float)
    feats = FEATS + ["is_imbal"]

    rows = []
    for i, r in V.iterrows():
        d = r.day
        prior = V.iloc[:i].dropna(subset=feats)
        prior = prior[prior.day.isin(books.index)]
        if len(prior) < MIN_ANALOGS or pd.isna(r[feats]).any():
            rows.append(dict(day=d, n_analogs=0, analog_block=""))
            continue
        mu, sd = prior[feats].mean(), prior[feats].std().replace(0, 1)
        dist = ((((prior[feats].astype(float) - r[feats].astype(float)) / sd) ** 2)
                .sum(axis=1)) ** 0.5
        an = prior.assign(dist=dist).nsmallest(K, "dist")
        neigh = []
        for _, n in an.iterrows():
            e3, e4 = books.loc[n.day, "pl_e3"], books.loc[n.day, "pl_e4"]
            neigh.append(dict(day=n.day, dist=round(float(n.dist), 2),
                              action=action(e3, e4), e3=round(e3), e4=round(e4)))
        acts = pd.Series([n["action"] for n in neigh])
        counts = acts.value_counts()
        e3s = pd.Series([n["e3"] for n in neigh])
        e4s = pd.Series([n["e4"] for n in neigh])
        block = dict(
            k=len(neigh),
            best_action_counts={x: int(counts.get(x, 0))
                                for x in ("FLAT", "ROTATION", "MOMENTUM")},
            majority_action=counts.idxmax(),
            mean_pl_if_rotation=round(float(e3s.mean())),
            mean_pl_if_momentum=round(float(e4s.mean())),
            share_both_books_red=round(float(((e3s < 0) & (e4s < 0)).mean()), 2),
            analogs=neigh,
        )
        rows.append(dict(day=d, n_analogs=len(neigh),
                         majority_action=block["majority_action"],
                         flat_share=round(counts.get("FLAT", 0) / len(neigh), 2),
                         mean_pl_rotation=block["mean_pl_if_rotation"],
                         mean_pl_momentum=block["mean_pl_if_momentum"],
                         analog_block=json.dumps(block)))
    out = pd.DataFrame(rows)
    out.to_csv("output/analog_briefing.csv", index=False)
    done = out[out.n_analogs > 0]
    print(f"wrote output/analog_briefing.csv: {len(done)}/{len(out)} days with analog blocks")

    # honesty check: does the majority-of-analogs action carry signal vs realized oracle?
    chk = done[done.day.isin(books.index)].copy()
    chk["oracle"] = [action(books.loc[d, "pl_e3"], books.loc[d, "pl_e4"]) for d in chk.day]
    hit = (chk.majority_action == chk.oracle).mean()
    print(f"majority-of-analogs vs realized oracle (3-way): {hit * 100:.0f}% "
          f"over {len(chk)} days (random ≈ 33%)")
    chk["y"] = chk.day.str[:4]
    print((chk.groupby("y").apply(lambda x: (x.majority_action == x.oracle).mean() * 100,
                                  include_groups=False)).round(0).to_string())


if __name__ == "__main__":
    main()
