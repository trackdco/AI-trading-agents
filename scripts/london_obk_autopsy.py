#!/usr/bin/env python3
"""Mandatory loser autopsy (§3.2) — LDN-PO3-01 / LDN-OBK-01.

Authorised by docs/PREREG-london-obk-L3-flow-and-autopsy.md. Runs AFTER the raw-trigger
flow pass, on exactly the frame that pass produced (output/london_obk_flow.parquet), so
no feature can be added at autopsy time.

§3.2 procedure, followed literally:
  1. feature set declared before looking  (6 flow + 4 candle, from the prereg)
  2. loser vs winner distributions per era
  3. HALF-YEAR decomposition — mandatory; the trigger event for this rule was the
     H2-2025 losing stretch both pre-market winners shared, invisible at year level
  4. every candidate cut-set is a ledgered arm
  5. a cut is legal only if the cut cohort is bad in EVERY era (wall-quality precedent)
  6. de-risk (half size) tested alongside every hard cut

    python -m scripts.london_obk_autopsy [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-obk-L3-flow-and-autopsy.md"
SRC = ROOT / "output/london_obk_flow.parquet"
OUT_MD = ROOT / "output/london_obk_autopsy.md"

COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
ERAS = ("2025", "2026")

FLOW_FEATURES = ["delta_entry", "delta_pre5", "delta_sweep", "absorb_extreme",
                 "wall_ratio_opp", "book_imb"]
CANDLE_FEATURES = ["width_rel", "lon_hour", "with_drift", "disp_frac"]
ALL_FEATURES = FLOW_FEATURES + CANDLE_FEATURES


def stats(T: pd.DataFrame, cost: float, size: float = 1.0) -> dict | None:
    if T.empty:
        return None
    net = (T["pts"] - cost) * size
    r = net / T["risk"]
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    n = len(net)
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "wr": (net > 0).mean(), "pts": net.sum(),
            "usd": DOLLAR_RISK * r.sum(), "pf": gw / max(gl, 1e-9),
            "r": r.mean(), "t": (r.mean() / se) if se and se == se else 0.0}


def winner_loser(T: pd.DataFrame, arm: str) -> str:
    """Step 2 — do winners and losers differ on any declared feature, per era?"""
    sub = T[T["arm"] == arm].copy()
    sub["win"] = (sub["pts"] - 1.0) > 0
    L = [f"### {arm} — winner vs loser on every declared feature", "",
         "Medians. `gap` is winner minus loser, expressed in standard deviations of",
         "the feature so the ten are comparable. A feature that separates outcomes",
         "should show the SAME sign in both eras; sign flips are noise.", "",
         "| feature | 2025 win | 2025 lose | 2025 gap σ | 2026 win | 2026 lose | 2026 gap σ | same sign |",
         "|---|---:|---:|---:|---:|---:|---:|---|"]
    for f in ALL_FEATURES:
        cells, gaps = {}, {}
        for era in ERAS:
            e = sub[(sub["era"] == era) & sub[f].notna()]
            if len(e) < 30:
                cells[era] = None
                continue
            x = e[f].astype(float)
            w, l = x[e["win"]], x[~e["win"]]
            if len(w) < 8 or len(l) < 8:
                cells[era] = None
                continue
            sd = x.std(ddof=1) or 1e-9
            cells[era] = (w.median(), l.median())
            gaps[era] = (w.median() - l.median()) / sd
        if not gaps:
            continue
        same = (len(gaps) == 2 and np.sign(list(gaps.values())[0])
                == np.sign(list(gaps.values())[1]) and abs(min(gaps.values(), key=abs)) > 0.1)
        def fmt(era, i):  # noqa: E306
            return "—" if cells.get(era) is None else f"{cells[era][i]:+.2f}"
        L.append(f"| `{f}` | {fmt('2025', 0)} | {fmt('2025', 1)} | "
                 f"{gaps.get('2025', float('nan')):+.2f} | {fmt('2026', 0)} | "
                 f"{fmt('2026', 1)} | {gaps.get('2026', float('nan')):+.2f} | "
                 f"{'**yes**' if same else 'no'} |")
    return "\n".join(L + [""])


def halves(T: pd.DataFrame, arm: str) -> str:
    """Step 3 — half-year decomposition. Mandatory, not optional."""
    sub = T[T["arm"] == arm]
    L = [f"### {arm} — half-year decomposition (§3.2 requires this, not year level)", "",
         "| half | n | WR | net pts base | net pts strict | PF base | R/trade base |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for h in sorted(sub["half"].dropna().unique()):
        e = sub[sub["half"] == h]
        b, s = stats(e, 1.0), stats(e, 2.0)
        if not b:
            continue
        L.append(f"| {h} | {b['n']} | {b['wr']:.0%} | {b['pts']:+.0f} | "
                 f"{s['pts']:+.0f} | {b['pf']:.2f} | {b['r']:+.3f} |")
    return "\n".join(L + [""])


def cuts(T: pd.DataFrame, arm: str) -> tuple[str, list[dict]]:
    """Steps 4-6 — candidate cut-sets, era-consistency test, de-risk alongside."""
    sub = T[T["arm"] == arm].copy()
    # candidate cuts are built from the WORST tercile of each feature in the DISCOVER
    # era only, then tested for whether that same cohort is bad in EVERY era.
    disc = sub[sub["era"] == "2025"]
    cand: dict[str, pd.Series] = {}
    for f in ALL_FEATURES:
        e = disc[disc[f].notna()]
        if len(e) < 45 or e[f].nunique() < 3:
            continue
        q1, q2 = e[f].quantile([1 / 3, 2 / 3])
        for lbl, m in (("low", sub[f] <= q1), ("high", sub[f] >= q2)):
            r = stats(e[e[f] <= q1] if lbl == "low" else e[e[f] >= q2], 1.0)
            if r and r["r"] < 0:
                cand[f"cut {f} {lbl}"] = m.fillna(False)

    L = [f"### {arm} — candidate cut-sets", "",
         "Cuts are proposed from the **discover era only** (worst tercile), then tested",
         "on every era. Per §3.2 a cut is legal ONLY if the cut cohort is bad in EVERY",
         "era — a cut that only works where it was found is a declared negative.",
         "De-risk (half size on the cohort instead of removing it) is tested alongside",
         "every hard cut, because sometimes the answer is smaller, not none.", "",
         "| cut | cohort bad in 2025 | in 2026 | legal | kept R base | kept R strict | de-risk R base |",
         "|---|---|---|---|---:|---:|---:|"]
    rows = []
    for name, mask in sorted(cand.items()):
        bad = {}
        for era in ERAS:
            s = stats(sub[mask & (sub["era"] == era)], 1.0)
            # bool() is load-bearing: s["r"] is a numpy float, so `s["r"] < 0` is a
            # numpy bool and `np.bool_(True) is True` is False — an identity check
            # would silently mark every legal cut illegal.
            bad[era] = None if not s or s["n"] < 12 else bool(s["r"] < 0)
        legal = len(bad) == 2 and all(v is True for v in bad.values())
        kept_b = stats(sub[~mask], 1.0)
        kept_s = stats(sub[~mask], 2.0)
        # de-risk: keep the cohort at half size rather than removing it
        d = sub.copy()
        d["w"] = np.where(mask, 0.5, 1.0)
        net = (d["pts"] - 1.0) * d["w"]
        derisk_r = float((net / d["risk"]).mean())
        fmt = lambda v: "—" if v is None else ("yes" if v else "no")  # noqa: E731
        L.append(f"| {name} | {fmt(bad.get('2025'))} | {fmt(bad.get('2026'))} | "
                 f"{'**LEGAL**' if legal else 'no'} | "
                 f"{kept_b['r']:+.3f} | {kept_s['r']:+.3f} | {derisk_r:+.3f} |")
        rows.append({
            "family": "LDN-PO3-01" if arm == "F1" else "LDN-OBK-01",
            "era": "2025+2026", "prereg": PREREG,
            "trial": f"autopsy {arm} {name}",
            "stat_type": "mean", "estimate": round(kept_b["r"], 4), "n": kept_b["n"],
            "t_stat": round(kept_b["t"], 4),
            "effect": round(trial_ledger.effect_from_t(kept_b["t"], kept_b["n"]), 6),
            "verdict": (f"autopsy cut {'LEGAL' if legal else 'illegal (cohort not bad in '
                        'every era)'}; kept R base {kept_b['r']:+.3f} strict "
                        f"{kept_s['r']:+.3f}; de-risk {derisk_r:+.3f}"),
        })
    baseline_b, baseline_s = stats(sub, 1.0), stats(sub, 2.0)
    L += ["", f"**Unconditioned baseline for reference: R base {baseline_b['r']:+.3f}, "
          f"strict {baseline_s['r']:+.3f} (n={baseline_b['n']}).** A cut only matters "
          "if `kept` clears the baseline AND is legal.", ""]

    legal_rows = [r for r in rows if "LEGAL" in r["verdict"]]
    rescued = [r for r in legal_rows
               if float(r["verdict"].split("strict ")[1].split(";")[0]) > 0]
    L += [f"**{len(legal_rows)} of {len(rows)} cuts are legal** (cohort bad in every "
          f"era). **{len(rescued)} of them leave the arm positive at strict cost.**", ""]
    if legal_rows and not rescued:
        L += ["Every legal cut still leaves a losing arm. Removing the worst cohorts",
              "raises the number without crossing zero, and half-sizing them does the",
              "same thing more slowly — which is what it looks like when the losses are",
              "spread through the sample rather than concentrated in a removable",
              "subset. There is no cut here, and there is no de-risk here.", ""]
    return "\n".join(L), rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    T = T[T["delta_sweep"].notna()].copy()      # flow span only — autopsy needs flow

    L = ["# LDN-PO3-01 / LDN-OBK-01 — mandatory loser autopsy (§3.2)", "",
         f"Authorised by `{PREREG}`. Runs on the frame the raw-trigger flow pass",
         "produced, so no feature could be added after seeing the split. Flow span",
         "only (tape starts 2025-06-01), so **the 2025 column is H2 only**.",
         "2023/24 untouched.", ""]

    ledger = []
    for arm in ("F1", "A/S1"):
        L += [f"## {arm}", "", winner_loser(T, arm), halves(T, arm)]
        body, rows = cuts(T, arm)
        L.append(body)
        ledger += rows

    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
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
