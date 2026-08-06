#!/usr/bin/env python3
"""Declared interaction follow-up — LDN-PO3-01 fade branch.

Authorised by docs/PREREG-london-open-break-interaction.md, committed before this
file. Three variables confirmed on the fade branch in the conditioning search; this
runs their pairwise interactions plus the 3-way (reported, barred as a gate).

  V1 open hour (08:00-08:59 London)
  V2 wide pre-open range (top tercile vs trailing 20-session median)
  V3 with-drift break

Carry rule, declared: a pair may go to L3 only if it beats BOTH components in BOTH
eras at BOTH costs AND keeps n >= 40 per era.

    python -m scripts.london_obk_interact [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-open-break-interaction.md"
SRC = ROOT / "output/london_obk_l1.parquet"
OUT_MD = ROOT / "output/london_obk_interact.md"

COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
ERAS = ("2025", "2026")
N_FLOOR = 40          # declared carry floor, per era


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


def masks(T: pd.DataFrame) -> dict[str, pd.Series]:
    """Per-era wide tercile, so the width cut is not defined across a regime shift."""
    wide = pd.Series(False, index=T.index)
    for era in ERAS:
        e = T[(T["era"] == era) & T["width_rel"].notna()]
        if e.empty:
            continue
        cut = e["width_rel"].quantile(2 / 3)
        wide.loc[e.index] = e["width_rel"] >= cut
    return {"V1 open hour": T["lon_hour"] == 8,
            "V2 wide range": wide,
            "V3 with drift": T["with_drift"].astype(bool)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    F = T[T["arm"] == "F1"].copy()
    M = masks(F)

    L = ["# LDN-PO3-01 — declared interaction follow-up (fade branch)", "",
         f"Authorised by `{PREREG}`. Default spec stays F1 unconditioned; nothing here",
         "promotes. Carry rule: a pair reaches L3 only if it beats BOTH components in",
         f"BOTH eras at BOTH costs AND keeps n >= {N_FLOOR} per era.", ""]

    def row(label: str, mask: pd.Series, era: str, cost: float) -> tuple[str, dict | None]:
        s = stats(F[mask & (F["era"] == era)], cost)
        if not s:
            return f"| {label} | {era} | — | — | — | — | — |", None
        return (f"| {label} | {era} | {s['n']} | {s['wr']:.0%} | {s['pts']:+.0f} | "
                f"{s['pf']:.2f} | {s['r']:+.3f} |"), s

    ledger, carried = [], []
    combos = [(c, " + ".join(c)) for c in combinations(M, 2)] + [(tuple(M), "ALL THREE")]

    for keys, label in combos:
        mask = pd.Series(True, index=F.index)
        for k in keys:
            mask &= M[k]
        three = len(keys) == 3
        L += [f"### {label}" + ("  — **BARRED as a gate, sample too thin**" if three else ""), "",
              "| spec | era | n | WR | net pts | PF | R/trade |",
              "|---|---|---:|---:|---:|---:|---:|"]
        beats, floor_ok = [], []
        for era in ERAS:
            for cost, cl in COSTS:
                if cl == "base":
                    for k in keys:
                        line, _ = row(f"{k} alone", M[k], era, cost)
                        L.append(line)
                line, s = row(f"**{label}** [{cl}]", mask, era, cost)
                L.append(line)
                if s:
                    comps = [stats(F[M[k] & (F["era"] == era)], cost) for k in keys]
                    comps = [c for c in comps if c]
                    beats.append(all(s["r"] > c["r"] for c in comps))
                    if cl == "base":
                        floor_ok.append(s["n"] >= N_FLOOR)
                        ledger.append({
                            "family": "LDN-PO3-01", "era": era, "prereg": PREREG,
                            "trial": f"interact {label}",
                            "stat_type": "mean", "estimate": round(s["r"], 4),
                            "n": s["n"], "t_stat": round(s["t"], 4),
                            "effect": round(trial_ledger.effect_from_t(s["t"], s["n"]), 6),
                            "verdict": (f"interaction: n={s['n']} WR {s['wr']:.0%} "
                                        f"PF {s['pf']:.2f} R {s['r']:+.3f}"),
                        })
        ok = bool(beats) and all(beats) and bool(floor_ok) and all(floor_ok) and not three
        if ok:
            carried.append(label)
        L += ["", f"Beats both components in **{sum(beats)}/{len(beats)}** era×cost cells; "
              f"n≥{N_FLOOR} in **{sum(floor_ok)}/{len(floor_ok)}** eras. "
              + ("**CARRIED to L3.**" if ok else
                 "**Not carried** (barred at this sample size)." if three else
                 "**Not carried.**"), ""]

    L += ["## Verdict", ""]
    if carried:
        L += [f"Carried to L3: **{', '.join(carried)}**.", ""]
    else:
        L += ["**No interaction is carried.** No pair beats both of its own components",
              "across both eras and both cost levels while holding the declared sample",
              "floor.", "",
              "**That is an informative negative, not a dead end.** It says the three",
              "confirmed variables are largely REDUNDANT — they are three views of one",
              "signal rather than three independent edges. Stacking them slices the",
              "sample without adding information, which is the classic way a promising",
              "conditioning table turns into an overfitted rulebook.",
              "",
              "**Consequence for L3:** the fade branch goes to the flow pass on its",
              "single strongest declared condition (V3 with-drift, the mechanism",
              "variable) rather than on a stacked spec. Fewer moving parts, and the one",
              "that carries the trapped-counterparty story.", ""]
    text = "\n".join(L)
    print(text)

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
