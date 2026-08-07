#!/usr/bin/env python3
"""Depth pass — the canon variable map applied to the London-open trade frame.

Authorised by docs/PREREG-london-depth-pass.md, committed before this file. Reuses
scripts.london_depth's loader and `depth_at` unchanged, so the semantics are byte-for-byte
the ones NY used (§5.12.7 provenance: recompute from raw, do not inherit a cached column).

Eight single checks at frozen canon thresholds, each evaluated ALONE (§5.12.2).
NaN stands down. thin (<15 a side) = no verdict. Survival = same direction EVERY era.

    python -m scripts.london_obk_depth [--dry-run]
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

from scripts.london_depth import depth_at, load_day  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-depth-pass.md"
SRC = ROOT / "output/london_obk_flow.parquet"
DEPTH_DIR = ROOT / "data/reference/depth_london"
OUT_MD = ROOT / "output/london_obk_depth.md"
OUT_PARQUET = ROOT / "output/london_obk_depth.parquet"

NY = "America/New_York"
COSTS = ((1.0, "base"), (2.0, "strict"))
ERAS = ("2025", "2026")
ARMS = ("F1", "A/S1", "F2", "B/S1")
THIN = 15
WALL_SZ_MIN = 7.0        # canon, as shipped
WALL_FAR_MIN = 2.75      # canon wall_quality_cut component


def attach_depth(T: pd.DataFrame) -> pd.DataFrame:
    """dep_* at the entry minute, via the identical semantics london_depth uses."""
    T = T.sort_values(["day", "entry_ts"]).reset_index(drop=True)
    cache: dict[str, object] = {}
    rows = []
    for i, t in enumerate(T.itertuples()):
        day = t.day
        if day not in cache:
            cache[day] = load_day(day, DEPTH_DIR)
            if len(cache) > 3:                       # keep memory flat over 396 days
                for k in list(cache)[:-3]:
                    cache.pop(k)
        dep = cache.get(day)
        if dep is None:
            rows.append({})
            continue
        minute = pd.Timestamp(t.entry_ts).tz_convert(NY).floor("min")
        # `long` is the trade's own direction: the fade trades AGAINST the break
        long = (t.side > 0) if t.branch == "OBK" else (t.side < 0)
        rows.append(depth_at(dep, minute, float(t.entry_px), "long" if long else "short"))
        if (i + 1) % 400 == 0:
            print(f"  depth {i+1}/{len(T)}", flush=True)
    X = pd.DataFrame(rows, index=T.index)
    for c in ("dep_thick", "dep_imb", "dep_sup_m_res", "dep_thick_d5m",
              "dep_wall_above_d", "dep_wall_above_sz",
              "dep_wall_below_d", "dep_wall_below_sz"):
        if c not in X.columns:
            X[c] = np.nan
    return pd.concat([T, X], axis=1)


def build_checks(T: pd.DataFrame) -> pd.DataFrame:
    """Direction-resolve (§4.2), then the eight frozen checks. NaN = stand down."""
    long = np.where(T["branch"] == "OBK", T["side"] > 0, T["side"] < 0)
    behind_d = np.where(long, T["dep_wall_below_d"], T["dep_wall_above_d"])
    ahead_d = np.where(long, T["dep_wall_above_d"], T["dep_wall_below_d"])
    ahead_sz = np.where(long, T["dep_wall_above_sz"], T["dep_wall_below_sz"])
    known = T["dep_thick"].notna().to_numpy()       # the stand-down master switch

    def gate(v):
        return pd.Series(np.where(known, v, np.nan), index=T.index)

    C = pd.DataFrame(index=T.index)
    # W: a MISSING wall distance means the check PASSES (nothing behind). Missing
    # thickness means the row stands down. The two nulls mean different things.
    C["W"] = gate(np.isnan(behind_d).astype(float))
    C["D"] = gate((~np.isnan(ahead_d)).astype(float))
    C["WALLSZ"] = gate(((~np.isnan(ahead_d)) & (np.nan_to_num(ahead_sz) >= WALL_SZ_MIN)
                        ).astype(float))
    # WALLFAR asks how far the wall behind is, so rows with no wall behind have no
    # answer -> stand down rather than counting as pass or fail.
    C["WALLFAR"] = pd.Series(np.where(known & ~np.isnan(behind_d),
                                      (behind_d >= WALL_FAR_MIN).astype(float), np.nan),
                             index=T.index)
    imb_dir = np.where(long, T["dep_imb"], -T["dep_imb"])
    C["IMBWITH"] = gate((imb_dir > 0).astype(float))
    C["SUPRES"] = gate((T["dep_sup_m_res"] > 0).astype(float))
    med = T.loc[(T["era"] == "2025") & T["dep_thick"].notna(), "dep_thick"].median()
    C["THICKHI"] = gate((T["dep_thick"] > med).astype(float))
    C["BUILD"] = pd.Series(np.where(known & T["dep_thick_d5m"].notna(),
                                    (T["dep_thick_d5m"] > 0).astype(float), np.nan),
                           index=T.index)
    return C


def mean_r(T: pd.DataFrame, cost: float) -> tuple[float, int, float]:
    if T.empty:
        return float("nan"), 0, float("nan")
    r = (T["pts"] - cost) / T["risk"]
    n = len(r)
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return float(r.mean()), n, (float(r.mean() / se) if se and se == se else 0.0)


def run(T: pd.DataFrame, C: pd.DataFrame) -> tuple[str, list[dict]]:
    L = ["# LDN-OBK-01 / LDN-PO3-01 — depth pass (canon variable map)", "",
         f"Authorised by `{PREREG}`. Eight checks at frozen canon thresholds, each",
         "evaluated ALONE (§5.12.2). NaN stands down — excluded from BOTH arms.",
         f"`thin` = fewer than {THIN} rows a side, and thin means **no verdict**, not a",
         "fail. Survival requires the same direction in EVERY era.", "",
         f"Depth resolved on **{T['dep_thick'].notna().sum()} of {len(T)}** trades.",
         "2025 is H2 only (depth starts June). 2023/24 depth not read.", ""]
    ledger, verdicts = [], []

    for arm in ARMS:
        sel = T["arm"] == arm
        L += [f"## {arm}", "",
              "| check | era | cost | n pass | n fail | R pass | R fail | lift_R |",
              "|---|---|---|---:|---:|---:|---:|---:|"]
        for chk in C.columns:
            dirs = {}
            for era in ERAS:
                m = sel & (T["era"] == era) & C[chk].notna()
                p, f = T[m & (C[chk] == 1)], T[m & (C[chk] == 0)]
                if min(len(p), len(f)) < THIN:
                    L.append(f"| `{chk}` | {era} | — | {len(p)} | {len(f)} | — | — | "
                             f"**thin** |")
                    dirs[era] = None
                    continue
                for cost, cl in COSTS:
                    rp, np_, tp = mean_r(p, cost)
                    rf, nf, _ = mean_r(f, cost)
                    lift = rp - rf
                    L.append(f"| `{chk}` | {era} | {cl} | {np_} | {nf} | {rp:+.3f} | "
                             f"{rf:+.3f} | **{lift:+.3f}** |")
                    if cl == "base":
                        dirs[era] = lift
                        ledger.append({
                            "family": "LDN-PO3-01" if arm.startswith("F") else "LDN-OBK-01",
                            "era": era, "prereg": PREREG,
                            "trial": f"depth {arm} {chk} lift_R",
                            "stat_type": "mean", "estimate": round(lift, 4), "n": np_ + nf,
                            "t_stat": round(tp, 4),
                            "effect": round(trial_ledger.effect_from_t(tp, np_ + nf), 6),
                            "verdict": (f"single-check depth trial, frozen threshold: "
                                        f"lift {lift:+.3f}R (pass {rp:+.3f} n={np_} / "
                                        f"fail {rf:+.3f} n={nf})"),
                        })
            got = [v for v in dirs.values() if v is not None]
            if len(got) < 2:
                cls = "no verdict (thin)"
            elif all(v > 0 for v in got):
                cls = "**SURVIVES — positive every era**"
            elif all(v < 0 for v in got):
                cls = "kill — negative every era"
            else:
                cls = "era-flip — never ship (§5.12.3)"
            verdicts.append({"arm": arm, "check": chk, "class": cls,
                             "lifts": [round(v, 3) for v in got]})
        L.append("")

    L += ["## Scorecard — §5.12.3 kill classes", "",
          "| arm | check | lifts by era (base cost) | class |", "|---|---|---|---|"]
    for v in verdicts:
        L.append(f"| {v['arm']} | `{v['check']}` | "
                 f"{', '.join(f'{x:+.3f}' for x in v['lifts']) or '—'} | {v['class']} |")
    L.append("")

    L += ["## Why `W` and `D` are thin on three arms and not on the fourth", "",
          "Not an artifact — a real property of where each arm enters, and it is the",
          "reason the canon's gate is meaningful here at all.", "",
          "`F1`, `F2` and `B/S1` all enter **inside the book**: at a fail-bar close or a",
          "trigger-candle close, with resting size on both sides. So there is nearly",
          "always a wall both above and below — `W` passes 4–6 times out of 277–314 and",
          "`D` passes almost always. Degenerate, correctly flagged thin, no verdict.", "",
          "`A/S1` enters **at a price extreme**, filled by a resting stop order when price",
          "trades through the trigger candle. At that minute the book is genuinely",
          "one-sided: `W` splits 75/225 and `D` splits 208/92. **A wall behind is only a",
          "meaningful question when you have just pushed to a new extreme** — which is",
          "exactly the condition the canon's pre-market book is in, and exactly why the",
          "same gate transfers.", ""]

    surv = [v for v in verdicts if "SURVIVES" in v["class"]]
    L += ["## Verdict", ""]
    if surv:
        L += [f"**{len(surv)} of {len(verdicts)} check×arm cells survive every era.**", ""]
        for v in surv:
            L.append(f"- `{v['check']}` on **{v['arm']}**: lifts {v['lifts']}")
        L += ["", "A survivor is **not** adopted here. Per the prereg it becomes a",
              "declared arm in a later prereg, after a permutation null (§5.12.4) and a",
              "state-conditional re-test (§5.11.4).", ""]
        # the only thing that matters commercially: does any survivor's PASS arm
        # actually make money at strict cost, in both eras?
        L += ["### Which survivors are positive at STRICT cost in both eras", "",
              "Lift is not profit. A check can separate a bad population into worse and",
              "less-bad and survive every era while never crossing zero — most of the",
              "family's conditioning so far has done exactly that.", "",
              "| arm | check | 2025 R pass (strict) | 2026 R pass (strict) | n pass | pays |",
              "|---|---|---:|---:|---:|---|"]
        for v in surv:
            cells, ns = {}, {}
            for era in ERAS:
                m = (T["arm"] == v["arm"]) & (T["era"] == era) & (C[v["check"]] == 1)
                r, n, _ = mean_r(T[m], 2.0)
                cells[era], ns[era] = r, n
            pays = all(cells[e] == cells[e] and cells[e] > 0 for e in ERAS)
            L.append(f"| {v['arm']} | `{v['check']}` | {cells['2025']:+.3f} | "
                     f"{cells['2026']:+.3f} | {ns['2025']}/{ns['2026']} | "
                     f"{'**YES**' if pays else 'no'} |")
        L.append("")
    else:
        L += ["**No check survives every era on any arm.**", "",
              "This is the outcome the prereg named as the strongest possible ground for",
              "a kill: the variable class that carried the canon's entire edge",
              "(+0.5 to +1.3R there) was tested here at the canon's own thresholds, on",
              "the session's own book, and is not present. Combined with the flow null,",
              "the two highest-prior classes have now both been searched and found",
              "empty.", "",
              "**Still not sufficient on its own.** Three §5.11 gaps remain open —",
              "event-universe sensitivity, the stop-cap arm class, and the in-trade",
              "MFE/MAE pack. Depth being absent at ENTRY does not answer whether depth",
              "or flow matters INSIDE the trade, which is where the canon found flow",
              "decisive.", ""]
    return "\n".join(L), ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    T = T[T["arm"].isin(ARMS)].copy()
    T = attach_depth(T)
    C = build_checks(T)
    text, ledger = run(T, C)
    print(text)

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    pd.concat([T, C.add_prefix("chk_")], axis=1).to_parquet(OUT_PARQUET, index=False)
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
