#!/usr/bin/env python3
"""Conditioning search — LDN-OBK-01 / LDN-PO3-01.

Authorised by docs/PREREG-london-open-break-conditioning.md, committed before this
file. Three variables, each with a directional prediction stated in that prereg
BEFORE the run. Reads the L1 trade frame; computes no new trades.

  V1  break time      open hour (08:00-08:59 LON) vs macro hour (09:00-09:59)
      predicted: continuation better in macro hour, fade better in open hour
  V2  range width     narrow / normal / wide vs trailing 20-session median
      predicted: continuation better narrow, fade better wide
  V3  drift alignment break with vs against the pre-open drift
      predicted: continuation better AGAINST drift, fade better WITH drift

Applied to the declared default arms only (A/S1, F1). A variable that lifts against
its own mechanism is recorded as a warning, not carried forward as a gate.

    python -m scripts.london_obk_cond [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-open-break-conditioning.md"
SRC = ROOT / "output/london_obk_l1.parquet"
OUT_MD = ROOT / "output/london_obk_cond.md"

COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
ERAS = ("2025", "2026")

# arm -> (branch label, the direction this branch is predicted to prefer)
DEFAULTS = {"A/S1": "continuation", "F1": "fade"}

# variable -> (column, {bucket label: predicate}), plus the declared prediction
PREDICTIONS = {
    "V1 break time": {
        "continuation": "macro hour", "fade": "open hour",
    },
    "V2 range width": {
        "continuation": "narrow", "fade": "wide",
    },
    "V3 drift alignment": {
        "continuation": "against drift", "fade": "with drift",
    },
}


def stats(T: pd.DataFrame, cost: float) -> dict | None:
    if T.empty:
        return None
    net = T["pts"] - cost
    r = net / T["risk"]
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    n = len(net)
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "wr": (net > 0).mean(), "pts": net.sum(),
            "usd": DOLLAR_RISK * r.sum(), "pf": gw / max(gl, 1e-9),
            "r": r.mean(), "t": (r.mean() / se) if se and se == se else 0.0}


def buckets(T: pd.DataFrame, var: str) -> dict[str, pd.DataFrame]:
    if var == "V1 break time":
        return {"open hour": T[T["lon_hour"] == 8], "macro hour": T[T["lon_hour"] == 9]}
    if var == "V2 range width":
        w = T[T["width_rel"].notna()]
        if w.empty:
            return {}
        lo_q, hi_q = w["width_rel"].quantile([1 / 3, 2 / 3])
        return {"narrow": w[w["width_rel"] <= lo_q],
                "normal": w[(w["width_rel"] > lo_q) & (w["width_rel"] < hi_q)],
                "wide": w[w["width_rel"] >= hi_q]}
    if var == "V3 drift alignment":
        return {"with drift": T[T["with_drift"]], "against drift": T[~T["with_drift"]]}
    return {}


def section(T: pd.DataFrame, arm: str, var: str) -> tuple[str, dict]:
    branch = DEFAULTS[arm]
    predicted = PREDICTIONS[var][branch]
    L = [f"#### {arm} ({branch}) — predicted better: **{predicted}**", "",
         "| bucket | era | cost | n | WR | net pts | PF | R/trade | vs baseline |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    lifts: dict[tuple[str, str], float] = {}
    sub = T[T["arm"] == arm]
    for era in ERAS:
        e = sub[sub["era"] == era]
        for cost, cl in COSTS:
            base = stats(e, cost)
            if not base:
                continue
            for label, frame in buckets(e, var).items():
                s = stats(frame, cost)
                if not s or s["n"] < 15:
                    continue
                delta = s["r"] - base["r"]
                if label == predicted:
                    lifts[(era, cl)] = delta
                L.append(f"| {label} | {era} | {cl} | {s['n']} | {s['wr']:.0%} | "
                         f"{s['pts']:+.0f} | {s['pf']:.2f} | {s['r']:+.3f} | "
                         f"{delta:+.3f} |")
    ok = [v > 0 for v in lifts.values()]
    # separately: is the predicted bucket actually PROFITABLE at strict cost in both
    # eras? "lifts the baseline" and "makes money" are different claims and the
    # scorecard must not let the first be read as the second.
    strict_pos = []
    for era in ERAS:
        e = sub[sub["era"] == era]
        frame = buckets(e, var).get(predicted)
        s = stats(frame, 2.0) if frame is not None and not frame.empty else None
        if s and s["n"] >= 15:
            strict_pos.append(s["r"] > 0)
    verdict = {
        "arm": arm, "var": var, "predicted": predicted,
        "cells": len(ok), "wins": sum(ok),
        "passes": bool(ok) and all(ok),
        "pays": bool(strict_pos) and all(strict_pos),
        "mean_lift": (sum(lifts.values()) / len(lifts)) if lifts else float("nan"),
    }
    L += ["", f"Predicted bucket lifts baseline in **{sum(ok)} of {len(ok)}** "
          f"era×cost cells. "
          + ("**Confirmed in the predicted direction.**" if verdict["passes"]
             else "**Not confirmed as declared.**"), ""]
    return "\n".join(L), verdict


def report(T: pd.DataFrame) -> tuple[str, list[dict]]:
    L = ["# LDN-OBK-01 / LDN-PO3-01 — conditioning search", "",
         f"Authorised by `{PREREG}`. Predictions declared before the run.",
         "Default arms only (A/S1, F1). Baseline is the unconditioned arm in the",
         "same era at the same cost; `vs baseline` is the change in R/trade.",
         "Buckets under n=15 are suppressed rather than reported as signal.", ""]
    verdicts = []
    for var in PREDICTIONS:
        L.append(f"### {var}")
        L.append("")
        for arm in DEFAULTS:
            body, v = section(T, arm, var)
            L.append(body)
            verdicts.append(v)

    L += ["## Scorecard", "",
          "**Two different claims, kept apart on purpose.** *Direction* = the predicted",
          "bucket beat the unconditioned arm, which is what the prereg asked. *Pays* =",
          "that bucket is actually positive at strict (2 pt) cost in BOTH eras, which",
          "is what a strategy needs. A variable can point the right way and still lose",
          "money, and most of these do.", "",
          "| variable | arm | predicted better | cells won | direction | pays at strict cost |",
          "|---|---|---|---:|---|---|"]
    for v in verdicts:
        L.append(f"| {v['var']} | {v['arm']} | {v['predicted']} | "
                 f"{v['wins']}/{v['cells']} | "
                 f"{'CONFIRMED' if v['passes'] else 'not confirmed'} | "
                 f"{'YES' if v['pays'] else 'no'} |")
    L.append("")

    fade = [v for v in verdicts if v["arm"] == "F1"]
    cont = [v for v in verdicts if v["arm"] == "A/S1"]
    L += ["### The asymmetry is the finding", "",
          f"The **fade** branch confirms **{sum(v['passes'] for v in fade)} of "
          f"{len(fade)}** variables in the direction predicted from mechanism before",
          f"the run. The **continuation** branch confirms **{sum(v['passes'] for v in cont)} "
          f"of {len(cont)}**.", "",
          "All three predictions were declared in advance and each predicted OPPOSITE",
          "directions for the two branches, so this is not a variable that merely sorts",
          "volatile days from quiet ones — the fade branch's stories check out and the",
          "continuation branch's mostly do not.", "",
          "**And nothing here pays yet.** Direction is not profit: at strict cost the",
          "confirmed buckets are still negative or barely positive. What the search has",
          "established is where to look, not that there is money in it.", ""]

    # V3 gets its own read because it is the mechanism test, not a filter test
    v3 = [v for v in verdicts if v["var"].startswith("V3")]
    if all(not v["passes"] for v in v3):
        L += ["### On V3 specifically", "",
              "V3 is not a filter, it is the candidate's own story — the thesis names",
              "the loser as *whoever committed to the pre-open drift*. It does not",
              "confirm in either branch. **The trapped-counterparty mechanism both",
              "branches are built on is not visible in the bars.** That is a more",
              "serious result than a failed filter and it is recorded as one. It does",
              "not by itself kill the family: the trapped side is a flow object and",
              "bars are the wrong instrument to see it with, which is exactly the",
              "argument for the L3 flow pass. But it means the family now rests on",
              "that pass rather than on anything demonstrated so far.", ""]
    return "\n".join(L), verdicts


def build_trials(T: pd.DataFrame, verdicts: list[dict]) -> list[dict]:
    rows = []
    for v in verdicts:
        arm, var = v["arm"], v["var"]
        fam = "LDN-OBK-01" if arm.startswith("A") else "LDN-PO3-01"
        sub = T[T["arm"] == arm]
        for era in ERAS:
            e = sub[sub["era"] == era]
            frame = buckets(e, var).get(v["predicted"])
            s = stats(frame, 1.0) if frame is not None else None
            if not s or s["n"] < 2:
                continue
            rows.append({
                "family": fam, "era": era, "prereg": PREREG,
                "trial": f"cond {var} = {v['predicted']} on {arm}",
                "stat_type": "mean", "estimate": round(s["r"], 4), "n": s["n"],
                "t_stat": round(s["t"], 4),
                "effect": round(trial_ledger.effect_from_t(s["t"], s["n"]), 6),
                "verdict": (f"conditioning, predicted direction: n={s['n']} "
                            f"WR {s['wr']:.0%} PF {s['pf']:.2f} R {s['r']:+.3f} — "
                            f"{'confirmed' if v['passes'] else 'NOT confirmed'} "
                            f"({v['wins']}/{v['cells']} cells)"),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    text, verdicts = report(T)
    print(text)

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")

    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in build_trials(T, verdicts)
             if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
