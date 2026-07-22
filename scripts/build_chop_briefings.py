#!/usr/bin/env python3
"""Morning briefings for the fresh-eyes CHOP-GOVERNOR run (Angus 24-Jul).

One briefing per labeled day. Leakage-clean: the 08:00 section uses only overnight/prior info;
the 09:40 section adds the pre-market window. Continuous features are expressed as trailing
percentile ranks over the prior 60 available days (handles regime level-shifts). Includes the
trailing scoreboard (sized ladder P&L and confirmed-trade WR BEFORE the day). Output:
output/chop_briefings.json {day: briefing}.

    python -m scripts.build_chop_briefings
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def trail_rank(s, w=60):
    out = {}
    v = s.dropna()
    for i, (d, x) in enumerate(v.items()):
        hist = v.iloc[max(0, i - w):i]
        out[d] = float((hist < x).mean()) if len(hist) >= 20 else np.nan
    return pd.Series(out)


def main():
    F = pd.read_parquet("output/dayflow_v2.parquet").sort_index()
    D = pd.read_parquet("output/depth_daywin.parquet")
    S = pd.read_parquet("output/tier1_stack.parquet").sort_values("fill")
    S["size"] = np.select([S.score <= 2, S.score == 3, S.score == 4, S.score == 5], [0, .5, 1, 1.5])
    S["spl"] = S.dollars * S["size"]

    on_feats = ["cvd_ON", "cvd_ASIA", "cvd_LON", "eff_ON", "eff_ASIA", "on_range", "rel_range",
                "rel_vol", "inventory_pts", "on_extreme_age", "on_eff_path", "gap_open_pts"]
    pm_feats = ["cvd_PM", "eff_PM", "pm_eff_path", "pm_crosses", "cvd_accel_PM", "pm_flip",
                "big_print_share_PM", "px_chg_PM", "cvd_OP", "px_chg_OP", "op_eff_path"]
    ranks = {}
    for c in on_feats + pm_feats:
        if c in F:
            base = F[c].abs() if c.startswith(("cvd_", "gap")) else F[c]
            ranks[c] = trail_rank(base)
    R = pd.DataFrame(ranks)

    dayspl = S.groupby("day").spl.sum()
    hi = S[S.score >= 4][["day", "dollars"]].reset_index(drop=True)

    briefs = {}
    days = list(F.index)
    for d in days:
        prior = [x for x in days if x < d]
        last10 = [x for x in prior if x in dayspl.index][-10:]
        hihist = hi[hi.day < d].tail(20)
        b = {
            "day": d,
            "at_0800": {
                "overnight_ranks_pct": {c: (None if c not in R or pd.isna(R.loc[d, c]) else round(R.loc[d, c] * 100))
                                        for c in on_feats if c in R.columns},
                "overnight_raw": {c: (None if pd.isna(F.loc[d, c]) else round(float(F.loc[d, c]), 1))
                                  for c in ["cvd_ON", "cvd_ASIA", "cvd_LON", "on_range", "gap_open_pts",
                                            "inventory_pts", "on_extreme_age"] if c in F.columns},
                "yesterday": {"sized_pl": (round(float(dayspl.get(prior[-1], np.nan)), 0)
                                           if prior and prior[-1] in dayspl.index else None),
                              "was_both_red": (int(F.loc[prior[-1], "both_red"]) if prior else None)},
                "scoreboard": {
                    "last10_traded_days_sized_pl": [round(float(dayspl[x]), 0) for x in last10],
                    "confirmed_trades_trailing20_wr": (round(float((hihist.dollars > 0).mean()), 2)
                                                       if len(hihist) >= 10 else None)},
            },
            "at_0940": {
                "premarket_ranks_pct": {c: (None if c not in R.columns or pd.isna(R.loc[d, c]) else round(R.loc[d, c] * 100))
                                        for c in pm_feats if c in R.columns},
                "premarket_raw": {c: (None if pd.isna(F.loc[d, c]) else round(float(F.loc[d, c]), 2))
                                  for c in ["cvd_PM", "px_chg_PM", "pm_crosses", "px_chg_OP", "cvd_OP"]
                                  if c in F.columns},
                "sweeps": {"london_hi": (None if "sweep_lh_PM" not in F or pd.isna(F.loc[d, "sweep_lh_PM"]) else int(F.loc[d, "sweep_lh_PM"])),
                           "london_lo": (None if "sweep_ll_PM" not in F or pd.isna(F.loc[d, "sweep_ll_PM"]) else int(F.loc[d, "sweep_ll_PM"]))},
                "book_0800_0930": ({c.replace("d_pre_", ""): (None if pd.isna(D.loc[d, c]) else round(float(D.loc[d, c]), 2))
                                    for c in ["d_pre_totsz_mean", "d_pre_imb_flips", "d_pre_thin_frac", "d_pre_totsz_trend"]}
                                   if d in D.index else None),
            },
        }
        briefs[d] = b
    Path("output/chop_briefings.json").write_text(json.dumps(briefs))
    print(f"wrote output/chop_briefings.json: {len(briefs)} days")


if __name__ == "__main__":
    main()
