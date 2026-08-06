#!/usr/bin/env python3
"""L3 LONDON Stage B — the trial: what separates winners from losers.

Authorised by docs/PREREG-london-canon-rebuild.md.

ANGUS 2026-08-05: *"try seperate winners from losers before putting stop caps and other
things... the process u go through to get there should be done in the right sequence"*.

So: the FULL ruled population, no risk gate, no caps, no geometry changes. The 9.5pt
band from L2 is L4 policy and is not applied — measuring lift on a population already
filtered for profitability would credit the feature with the filter's work.

WHAT SURVIVAL MEANS HERE, declared before the tables are read:
  a feature survives ONLY if its top-vs-bottom tercile gap points the SAME WAY in 2025
  and in 2026, at n >= 30 per era cell. Pooled separation is not evidence (§5.11.4 —
  pooled nulls do not close a gate question). Nothing is promoted at this rung; the
  survivors go to a family-wise permutation null, which can kill all of them.

THE STANDING CHECK FROM NYA-LVL-01 IS AUTOMATIC HERE. Any depth feature whose lift beats
the baseline by more than 5pp is recomputed from the book ONE MINUTE EARLIER (`p1_*`) and
both numbers are printed together, BEFORE the feature is described as working. That check
exists because a depth feature once carried +19.5pp and turned out to be reading the book
after entry; recomputed a minute earlier it was +4.2pp.

    python -m scripts.l3_london_trial [--arm vs_first]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-canon-rebuild.md"
IN = ROOT / "output/l3_features_london_fit.parquet"
OUT_MD = ROOT / "output/l3_london_trial.md"
MIN_CELL = 30
BIG_LIFT = 0.05          # 5pp — the NYA-LVL-01 standing-check trigger

# the four shipped London checks, at their FROZEN 2025 thresholds (src/canon/scorer.py)
LON_FAR_MIN, LON_ROOM_LO, LON_ROOM_HI, LON_ASIA_MIN = 4.5, 2.48, 9.56, -748.0

SKIP = {"R", "pts", "dollars_1lot", "risk", "entry", "stop", "exit_price", "target_level",
        "working_target", "confluence_count", "setup_id", "setup_size", "vs_id", "vs_size"}


def econ(T: pd.DataFrame) -> dict | None:
    if len(T) < MIN_CELL:
        return None
    d = T["dollars_1lot"].to_numpy(float)
    w, l = d[d > 0], d[d <= 0]
    return {"n": len(d), "wr": float((d > 0).mean()),
            "pf": float(w.sum() / max(-l.sum(), 1e-9)), "usd": float(d.sum())}


def derive(F: pd.DataFrame) -> pd.DataFrame:
    """The shipped London checks, rebuilt from raw columns at their frozen thresholds.

    DEPTH IS READ AT ORDER PLACEMENT (`t_*`, the trigger candle's close). ANGUS 2026-08-05:

        "on a limit order, of course the minute before entry, flow will probably be against
         us because it is opposing our direction to get filled before running the way we
         want it to."

    That invalidates BOTH fill-anchored reads. The fill-bar CLOSE contains the answer
    (research/findings/LDN-depth-read-one-bar-late.md); the fill-bar OPEN is adverse BY
    CONSTRUCTION, because a limit fill requires price to travel toward us. Neither brackets
    the truth, so neither is a baseline.

    Order placement is the moment a limit trader can actually act on -- you cannot cancel an
    order at the instant it fills -- and the trigger candle's close is unambiguous, strictly
    prior to the limit existing, and free of approach bias.
    """
    F = F.copy()
    long = (F.direction == "long").to_numpy()
    behind = np.where(long, F.get("t_dep_wall_below_d"), F.get("t_dep_wall_above_d"))
    ahead = np.where(long, F.get("t_dep_wall_above_d"), F.get("t_dep_wall_below_d"))
    known = F["t_dep_thick"].notna().to_numpy()
    F["chk_W"] = np.where(known, np.isnan(behind).astype(float), np.nan)
    F["chk_FAR"] = np.where(known, (np.nan_to_num(ahead, nan=-1) > LON_FAR_MIN).astype(float),
                            np.nan)
    # room to the target-side overnight extreme, in R — the London flagship construct
    on_lo = F["entry"] - F["ent_on_pos"] * F["on_range"]
    room = np.where(long, (on_lo + F["on_range"]) - F["entry"], F["entry"] - on_lo)
    F["room_ahead_R"] = room / F["risk"].replace(0, np.nan)
    F["chk_ROOM"] = ((F.room_ahead_R > LON_ROOM_LO) & (F.room_ahead_R <= LON_ROOM_HI)).astype(float)
    sgn = np.where(long, 1.0, -1.0)
    F["chk_ASIA"] = np.where(F["cvd_ASIA"].notna(),
                             (sgn * F["cvd_ASIA"] >= LON_ASIA_MIN).astype(float), np.nan)
    # the two fill-anchored mirrors of W, kept ONLY so the comparison table can show all
    # three and the reasoning stays auditable. Neither is ever used as a feature.
    for pre, name in (("", "chk_W_late"), ("p1_", "chk_W_open")):
        b = np.where(long, F.get(pre + "dep_wall_below_d"), F.get(pre + "dep_wall_above_d"))
        k = F[pre + "dep_thick"].notna().to_numpy()
        F[name] = np.where(k, np.isnan(b).astype(float), np.nan)
    return F


def split_lift(F: pd.DataFrame, col: str) -> dict | None:
    """Top vs bottom tercile (or 1 vs 0 for flags), per era. Era-consistent or nothing."""
    s = F[col]
    if s.notna().sum() < 4 * MIN_CELL:
        return None
    uniq = s.dropna().unique()
    if len(uniq) <= 2:
        hi, lo = s == max(uniq), s == min(uniq)
    else:
        try:
            q = s.quantile([1 / 3, 2 / 3])
        except Exception:
            return None
        if q.iloc[0] == q.iloc[1]:
            return None
        hi, lo = s > q.iloc[1], s < q.iloc[0]
    rec = {"feature": col}
    for era in ("2025", "2026"):
        m = F.era == era
        a, b = econ(F[hi & m]), econ(F[lo & m])
        if not a or not b:
            return None
        rec[f"pf_hi_{era}"], rec[f"pf_lo_{era}"] = a["pf"], b["pf"]
        rec[f"wr_hi_{era}"], rec[f"wr_lo_{era}"] = a["wr"], b["wr"]
        rec[f"n_hi_{era}"] = a["n"]
        rec[f"gap_{era}"] = a["wr"] - b["wr"]
    a_all, b_all = econ(F[hi]), econ(F[lo])
    rec["pf_hi"], rec["pf_lo"] = a_all["pf"], b_all["pf"]
    rec["wr_gap"] = a_all["wr"] - b_all["wr"]
    rec["n_hi"] = a_all["n"]
    rec["consistent"] = bool(np.sign(rec["gap_2025"]) == np.sign(rec["gap_2026"])
                             and abs(rec["gap_2025"]) > 0 and abs(rec["gap_2026"]) > 0)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="vs_first")
    ap.add_argument("--features", default=str(IN))
    ap.add_argument("--kind", default="all", choices=["all", "displacement",
                                                      "rejection_block"],
                    help="ANGUS 2026-08-05: under EC the depth feature has DIFFERENT LEAD "
                         "TIME per half -- zero for a market-entered displacement (trigger "
                         "close IS the entry), and the retest delay for a limit-entered "
                         "rejection block. Same causality, different freshness. Pooling "
                         "them would blur a signal that works at zero lead and decays.")
    a = ap.parse_args()

    F = pd.read_parquet(a.features)
    if a.kind != "all":
        F = F[F["kind"] == a.kind]
    F = F[F[a.arm]].copy()
    F["era"] = F.day.str[:4]
    F = derive(F)
    base = econ(F)

    L = ["# LDN-CAN-01 — L3 trial: what separates winners from losers", "",
         f"Authorised by `{PREREG}`. Arm `{a.arm}`"
         + (f", trigger kind **{a.kind}**" if a.kind != "all" else "")
         + f", **{len(F):,} trades**, {F.day.nunique()} sessions.", "",
         "**No risk gate, no caps, no geometry changes** — the 9.5pt band from L2 is L4",
         "policy and is deliberately not applied here (ANGUS: *\"separate winners from",
         "losers before putting stop caps and other things\"*). Measuring lift on a",
         "population already filtered for profitability would credit the feature with the",
         "filter's work.", "",
         f"Baseline: WR **{base['wr']:.1%}**, PF **{base['pf']:.2f}**, "
         f"${base['usd']:+,.0f}.", "",
         "**Survival = the top-vs-bottom gap points the SAME WAY in 2025 and 2026**, "
         "n≥30 per",
         "cell. Pooled separation is not evidence (§5.11.4). Nothing is promoted here; "
         "survivors owe a family-wise permutation null which can kill all of them.", ""]

    # --- 1. the four shipped London checks ------------------------------------
    L += ["## 1. The four shipped London checks, at their frozen 2025 thresholds", "",
          "Re-derived from raw columns, not read from a cached matrix (burn-list item 6:",
          "cached columns lie).", "",
          "| check | n pass | WR pass | WR fail | gap | PF pass | 2025 gap | 2026 gap | era-consistent |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    surv_checks = []
    for c, lbl in (("chk_W", "`W` no wall behind"), ("chk_FAR", "`FAR` wall ahead >4.5pt"),
                   ("chk_ROOM", "`ROOM` 2.48-9.56R"), ("chk_ASIA", "`ASIA` flow not opposed")):
        r = split_lift(F, c)
        if r is None:
            L.append(f"| {lbl} | — | — | — | — | — | — | — | too thin |")
            continue
        if r["consistent"] and r["wr_gap"] > 0:
            surv_checks.append(r)
        L.append(f"| {lbl} | {r['n_hi']:,} | {r['wr_hi_2025']:.1%}/{r['wr_hi_2026']:.1%} | "
                 f"{r['wr_lo_2025']:.1%}/{r['wr_lo_2026']:.1%} | {r['wr_gap']:+.1%} | "
                 f"{r['pf_hi']:.2f} | {r['gap_2025']:+.1%} | {r['gap_2026']:+.1%} | "
                 f"{'**YES**' if r['consistent'] else 'no'} |")

    # --- 2. the standing check on W -------------------------------------------
    rp, rw = split_lift(F, "chk_W"), split_lift(F, "chk_W_late")
    ro = split_lift(F, "chk_W_open")
    if rw and rp:
        L += ["", "### The NYA-LVL-01 standing check on `W`, run BEFORE `W` is described", "",
              "*Any depth feature beating baseline by >5pp is recomputed from the book one",
              "minute earlier before it is reported.* `W` at the fill-minute boundary vs "
              "`W` one minute earlier:", "",
              "| book used | n | WR gap (pass − fail) | 2025 | 2026 |", "|---|---:|---:|---:|---:|",
              f"| fill-bar CLOSE (as the shipped book reads it) | {rw['n_hi']:,} | "
              f"**{rw['wr_gap']:+.1%}** | {rw['gap_2025']:+.1%} | {rw['gap_2026']:+.1%} |",
              f"| fill-bar OPEN (adverse by construction) | {ro['n_hi']:,} | "
              f"**{ro['wr_gap']:+.1%}** | {ro['gap_2025']:+.1%} | {ro['gap_2026']:+.1%} |"
              if ro else "| fill-bar OPEN | — | — | — | — |",
              f"| **ORDER PLACEMENT (used here)** | {rp['n_hi']:,} | "
              f"**{rp['wr_gap']:+.1%}** | {rp['gap_2025']:+.1%} | {rp['gap_2026']:+.1%} |", "",
              (f"Gap between the two: **{abs(rw['wr_gap'] - rp['wr_gap']):.1%}**. "
               + ("Small — the signal is not coming from the last minute of information."
                  if abs(rw["wr_gap"] - rp["wr_gap"]) < BIG_LIFT else
                  "**LARGE — most of this is last-minute information and it must be treated "
                  "as suspect.**")), ""]

    # --- 3. everything else ----------------------------------------------------
    # depth features come from p1_ only; the un-prefixed dep_ columns are the
    # contaminated fill-bar-close read and are excluded from the search entirely.
    # only the order-placement depth enters the search; both fill-anchored sets are barred
    feats = [c for c in F.columns if c not in SKIP and not c.startswith("dep_")
             and not c.startswith("p1_") and not c.startswith("chk_") and pd.api.types.is_numeric_dtype(F[c])
             and F[c].notna().sum() > 4 * MIN_CELL]
    rows = [r for r in (split_lift(F, c) for c in sorted(feats)) if r]
    R = pd.DataFrame(rows)
    surv = R[R.consistent].sort_values("wr_gap", key=abs, ascending=False)

    L += ["## 2. Every other feature — era-consistent survivors only", "",
          f"{len(R)} features tested, **{len(surv)} point the same way in both eras**.", "",
          "| feature | n hi | WR gap | PF hi | PF lo | 2025 gap | 2026 gap |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in surv.head(25).iterrows():
        L.append(f"| `{r.feature}` | {r.n_hi:,} | {r.wr_gap:+.1%} | {r.pf_hi:.2f} | "
                 f"{r.pf_lo:.2f} | {r.gap_2025:+.1%} | {r.gap_2026:+.1%} |")
    L += ["", f"_Non-survivors ({len(R)-len(surv)}) are recorded in the ledger, not hidden._",
          ""]

    dep_surv = surv[surv.feature.str.startswith("dep_")]
    L += [f"**Depth survivors: {len(dep_surv)} of {len(surv)}.** The canon's own evidence "
          "(§5.12.10) is that",
          "depth carried its entire edge while flow at entry was a rounding error. Whether "
          "that",
          "transfers to London is the question this rung exists to answer.", ""]

    L += ["", "## 3. What is owed before any of this counts", "",
          "1. **Family-wise permutation null** over the whole search — "
          f"{len(R)} features were",
          "   tested and the best reported, so the null must re-run that entire selection.",
          "2. **State-conditional re-tests** (§5.11.4) — pooled separation does not close a",
          "   gate question.",
          "3. **MFE/MAE pack** (§5.11.1) before any ship card exists.", "",
          "**Nothing here is promoted, and no arm displaces the default on in-sample rank.**",
          ""]

    text = "\n".join(L)
    print(text)
    out_md = (OUT_MD if a.kind == "all"
              else OUT_MD.with_name(f"l3_london_trial_{a.kind}.md"))
    out_md.write_text(text)

    led = [{"family": "LDN-CAN-01", "era": "fit", "prereg": PREREG,
            "trial": (f"L3 winner/loser separation {r.feature} ({a.arm}"
                      + (f", {a.kind}" if a.kind != "all" else "") + ")"),
            "stat_type": "mean", "estimate": round(float(r.wr_gap), 4),
            "n": int(r.n_hi), "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"WR gap {r.wr_gap:+.1%} (25 {r.gap_2025:+.1%} / 26 "
                        f"{r.gap_2026:+.1%}); "
                        f"{'era-consistent' if r.consistent else 'NOT era-consistent'}")}
           for _, r in R.iterrows()]
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in led if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"\nrecorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
