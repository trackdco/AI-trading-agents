#!/usr/bin/env python3
"""IN-TRADE EARLY-EXIT — per-session / per-mechanism policy breakdown,
day-block bootstrap significance, and the true/false-positive R accounting
that explains WHY a high-AUC classifier can still fail to beat do-nothing.

Reads the outputs of scripts/intrade_exit_model.py:
  intrade_exit_oof.parquet       per-fight OOF junk-probability by horizon
  intrade_exit_tightstops.parquet  blanket -0.5R / -0.75R re-simulated book

    python -m scripts.intrade_exit_breakdown
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CENSUS = ROOT / "output/htf_ma_census"
SEED = 20260808
DRAWS = 4000


def policy_outcome(O: pd.DataFrame, h: int, kind: str, thresh: float):
    resolved = O[f"h{h}_resolved_early"].to_numpy()
    close_r = O[f"h{h}_close_r"].to_numpy()
    p = O[f"h{h}_oof_{kind}"].to_numpy()
    cost_r = O["cost_r"].to_numpy()
    flag = (p > thresh) & (~resolved)
    out = np.where(flag, close_r - cost_r, O.real_out.to_numpy())
    r3 = np.where(flag, False, O.reached_3r.to_numpy())
    return out, r3, flag


def dboot_ev(days: np.ndarray, values: np.ndarray, draws: int = DRAWS):
    """Day-block bootstrap CI on the mean of `values`, resampling sess_day."""
    g = pd.Series(values, index=days)
    by_day = g.groupby(level=0).agg(["sum", "count"])
    s, n = by_day["sum"].to_numpy(), by_day["count"].to_numpy()
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(s), (draws, len(s)))
    tot = s[idx].sum(1)
    cnt = n[idx].sum(1)
    means = tot / cnt
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def group_table(O: pd.DataFrame, group_col: str | None, policies: dict) -> pd.DataFrame:
    rows = []
    groups = [None] if group_col is None else sorted(O[group_col].unique())
    for g in groups:
        sub = O if g is None else O[O[group_col] == g]
        for name, out_arr, r3_arr in policies_for(sub, policies):
            rows.append(dict(group=g if g is not None else "ALL", policy=name,
                             n=len(sub), ev=out_arr.mean(), sum_r=out_arr.sum(),
                             p3r=r3_arr.mean()))
    return pd.DataFrame(rows)


def policies_for(sub: pd.DataFrame, policies: dict):
    """policies: name -> (h, kind, thresh) or 'do_nothing' or ('tight', T)."""
    out = []
    for name, spec in policies.items():
        if spec == "do_nothing":
            out.append((name, sub.real_out.to_numpy(), sub.reached_3r.to_numpy()))
        elif isinstance(spec, tuple) and spec[0] == "tight":
            out.append((name, sub[f"tight_{spec[1]}_out"].to_numpy(),
                        sub[f"tight_{spec[1]}_r3"].to_numpy()))
        else:
            h, kind, th = spec
            o, r3, _ = policy_outcome(sub, h, kind, th)
            out.append((name, o, r3))
    return out


def main() -> None:
    O = pd.read_parquet(CENSUS / "intrade_exit_oof.parquet")
    TW = pd.read_parquet(CENSUS / "intrade_exit_tightstops.parquet")
    for sr in sorted(TW.stop_r.unique()):
        t = TW[TW.stop_r == sr][["scid", "real_out", "reached_3r"]]
        t = t.rename(columns={"real_out": f"tight_{sr}_out",
                              "reached_3r": f"tight_{sr}_r3"})
        O = O.merge(t, on="scid", how="left")

    # curated policy set: best-EV row per horizon x model from the sweep,
    # read back so this script stays in sync with intrade_exit_model's grid
    POL = pd.read_csv(CENSUS / "intrade_exit_policy.csv")
    best = {}
    for h in [1, 2, 3, 5, 10]:
        for kind in ("lr", "gbm"):
            sub = POL[POL.policy == f"h{h}_{kind}"]
            row = sub.loc[sub.ev.idxmax()]
            best[f"h{h}_{kind}_best"] = (h, kind, float(row.thresh))

    policies = {"do_nothing": "do_nothing", "blanket_-0.5R": ("tight", 0.5),
               "blanket_-0.75R": ("tight", 0.75), **best}

    print("=" * 100)
    print("POOLED — do-nothing vs blanket stops vs best-EV early-exit policy per horizon")
    print("=" * 100)
    pooled = group_table(O, None, policies)
    print(pooled.drop(columns="group").to_string(index=False))

    print("\n" + "=" * 100)
    print("PER SESSION (never pooled for conclusions)")
    print("=" * 100)
    per_sess = group_table(O, "session", policies)
    for pol in policies:
        sub = per_sess[per_sess.policy == pol]
        print(f"\n{pol}:")
        print(sub[["group", "n", "ev", "p3r"]].to_string(index=False))

    print("\n" + "=" * 100)
    print("PER MECHANISM (never pooled for conclusions)")
    print("=" * 100)
    per_mech = group_table(O, "mech", policies)
    for pol in policies:
        sub = per_mech[per_mech.policy == pol]
        print(f"\n{pol}:")
        print(sub[["group", "n", "ev", "p3r"]].to_string(index=False))

    pooled.to_csv(CENSUS / "intrade_exit_pooled_table.csv", index=False)
    per_sess.to_csv(CENSUS / "intrade_exit_session_table.csv", index=False)
    per_mech.to_csv(CENSUS / "intrade_exit_mech_table.csv", index=False)

    # ---- day-block bootstrap: is the best policy's EV distinguishable from
    # do-nothing's EV? (paired by day: resample the SAME day draws for both)
    print("\n" + "=" * 100)
    print("DAY-BLOCK BOOTSTRAP — EV(best policy) - EV(do_nothing), 95% CI")
    print("=" * 100)
    days = O.sess_day.to_numpy()
    rng = np.random.default_rng(SEED)
    day_list = sorted(O.sess_day.unique())
    day_idx = {d: i for i, d in enumerate(day_list)}
    row_day = np.array([day_idx[d] for d in days])
    for name, spec in best.items():
        h, kind, th = spec
        out, r3, flag = policy_outcome(O, h, kind, th)
        diff = out - O.real_out.to_numpy()
        # per-day sums of the paired difference and day fight-count
        by_day_sum = np.zeros(len(day_list))
        by_day_cnt = np.zeros(len(day_list))
        np.add.at(by_day_sum, row_day, diff)
        np.add.at(by_day_cnt, row_day, 1)
        draws = rng.integers(0, len(day_list), (DRAWS, len(day_list)))
        tot = by_day_sum[draws].sum(1)
        cnt = by_day_cnt[draws].sum(1)
        means = tot / cnt
        lo, hi = np.percentile(means, [2.5, 97.5])
        obs = diff.mean()
        sig = "!" if (lo > 0 or hi < 0) else ""
        print(f"  {name:14s} (h={h:2d} {kind:3s} th={th:.2f}): "
              f"delta_EV {obs:+.4f}R  95%CI [{lo:+.4f},{hi:+.4f}]{sig}  "
              f"flagged={flag.sum()} ({flag.mean()*100:.1f}%)")

    # ---- true/false-positive R accounting at a representative threshold:
    # WHY high AUC does not automatically mean positive policy EV.
    print("\n" + "=" * 100)
    print("TRUE/FALSE-POSITIVE R ACCOUNTING (h1 LR best threshold)")
    print("=" * 100)
    for name, (h, kind, th) in best.items():
        out, r3, flag = policy_outcome(O, h, kind, th)
        d = out - O.real_out.to_numpy()
        tp = flag & (O.is_junk.to_numpy() == 1)
        fp = flag & (O.is_junk.to_numpy() == 0)
        runner_fp = flag & (O.reached_3r.to_numpy())
        print(f"\n{name} (h={h} {kind} th={th:.2f}): flagged {flag.sum()} "
              f"({flag.mean()*100:.1f}%)")
        print(f"  true positives (actually junk):  n={tp.sum():4d}  "
              f"mean R saved  {d[tp].mean():+.3f}  total {d[tp].sum():+.1f}R")
        print(f"  false positives (not junk):      n={fp.sum():4d}  "
              f"mean R cost   {d[fp].mean():+.3f}  total {d[fp].sum():+.1f}R")
        print(f"    of which reached 3R+ (runners cut): n={runner_fp.sum():4d}  "
              f"mean R cost {d[runner_fp].mean():+.3f}  total {d[runner_fp].sum():+.1f}R")
        print(f"  NET: {d[flag].sum():+.1f}R over {flag.sum()} flagged trades "
              f"(mean {d[flag].mean():+.4f}R/flag)")


if __name__ == "__main__":
    main()
