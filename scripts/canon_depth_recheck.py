#!/usr/bin/env python3
"""CANON DEPTH RE-CHECK — what are W / D / WALLSZ worth at the HONEST read?

ANGUS 2026-08-05. Motivated by research/findings/LDN-depth-read-one-bar-late.md:

  * the archived depth snapshot stamped T is the INSTANTANEOUS book at T
  * engine bars are CLOSE-labeled, so a bar stamped T covers (T-1min, T]
  * fills land inside their stamped bar (95.8% on canon_book.parquet)
  * `scripts/score_canon_span.py:196` reads `depth_at(dep, fill, ...)` -- the book at T

=> the backtest's depth features are read at or AFTER the fill. The LIVE bot is NOT
   affected: `src/canon/ingestor.py` reads the real book at decision time and cannot see
   the rest of the bar. This is a CALIBRATION question, not a correctness incident.

THE QUESTION: §5.12.10 records that depth carried the canon's entire edge, +0.5 to +1.3R.
That was measured at the late read. What is it at the honest one?

METHOD. Take the canon's own book. For every trade recompute the depth features twice from
the raw archive -- at the fill bar's CLOSE (as shipped) and at its OPEN (honest, and the
conservative bound on what live holds) -- rebuild `W`, `D` and `WALLSZ` at their frozen
canon definitions from `src/canon/scorer.ny_checks`, and compare the per-check R lift.

NOTHING IS CHANGED. This writes no config, no threshold, no book. It reports a number.

    python -m scripts.canon_depth_recheck
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.features import depth_at  # noqa: E402

NY = "America/New_York"
OUT_MD = ROOT / "output/canon_depth_recheck.md"
DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026"]
Q_WALLSZ_MIN = 7.0          # frozen canon constant (src/canon/scorer.py)


def load_depth(day: str):
    for d in DEPTH_DIRS:
        f = ROOT / d / f"nq_depth_{day}_ny.csv"
        if f.exists():
            dd = pd.read_csv(f)
            dd["ts"] = pd.to_datetime(dd.ts, utc=True).dt.tz_convert(NY)
            return dd
    return None


def checks(F: pd.DataFrame, pre: str) -> pd.DataFrame:
    """W / D / WALLSZ at the canon's frozen definitions, from a given depth read."""
    long = (F.direction == "long").to_numpy()
    behind = np.where(long, F[pre + "dep_wall_below_d"], F[pre + "dep_wall_above_d"])
    ahead = np.where(long, F[pre + "dep_wall_above_d"], F[pre + "dep_wall_below_d"])
    ahead_sz = np.where(long, F[pre + "dep_wall_above_sz"], F[pre + "dep_wall_below_sz"])
    known = F[pre + "dep_thick"].notna().to_numpy()
    C = pd.DataFrame(index=F.index)
    C["W"] = np.where(known, np.isnan(behind).astype(float), np.nan)
    C["D"] = np.where(known, (~np.isnan(ahead)).astype(float), np.nan)
    C["WALLSZ"] = np.where(known, ((~np.isnan(ahead))
                                   & (np.nan_to_num(ahead_sz) >= Q_WALLSZ_MIN)).astype(float),
                           np.nan)
    return C


def lift(F: pd.DataFrame, c: pd.Series) -> dict | None:
    a, b = F[c == 1], F[c == 0]
    if len(a) < 30 or len(b) < 30:
        return None
    return {"n_pass": len(a), "r_pass": float(a.R.mean()), "r_fail": float(b.R.mean()),
            "lift": float(a.R.mean() - b.R.mean()),
            "wr_pass": float((a.dollars > 0).mean()),
            "wr_fail": float((b.dollars > 0).mean())}


def main() -> int:
    B = pd.read_parquet(ROOT / "output/canon_book.parquet")
    # the book already carries dep_* from the shipped (late) build -- drop them so the
    # recomputed pair below cannot collide with, or be mistaken for, the stored ones
    B = B.drop(columns=[c for c in B.columns if c.startswith("dep_")])
    B["fill_t"] = pd.to_datetime(B.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    B = B.sort_values(["day", "fill_t"]).reset_index(drop=True)

    rows, dep, dday, miss = [], None, None, set()
    for t in B.itertuples():
        if t.day != dday:
            dday, dep = t.day, load_depth(t.day)
            if dep is None:
                miss.add(t.day)
        r = {}
        if dep is not None:
            r.update(depth_at(dep, t.fill_t, float(t.entry), t.direction))
            r.update({f"o_{k}": v for k, v in
                      depth_at(dep, t.fill_t - pd.Timedelta(minutes=1),
                               float(t.entry), t.direction).items()})
        rows.append(r)
    X = pd.DataFrame(rows, index=B.index)
    for c in ("dep_thick", "dep_wall_above_d", "dep_wall_above_sz",
              "dep_wall_below_d", "dep_wall_below_sz"):
        for p in ("", "o_"):
            if p + c not in X:
                X[p + c] = np.nan
    F = pd.concat([B, X], axis=1)
    cov = int(F.dep_thick.notna().sum())

    C_late, C_open = checks(F, ""), checks(F, "o_")
    L = ["# CANON DEPTH RE-CHECK — W / D / WALLSZ at the honest read", "",
         "Motivated by `research/findings/LDN-depth-read-one-bar-late.md`. **Nothing is",
         "changed by this script** — no config, no threshold, no book. It reports a number.",
         "",
         "**The live bot is not affected.** `src/canon/ingestor.py` reads the real order",
         "book at decision time and cannot see the rest of the bar. This is about what the",
         "*calibration* credited depth with, not about what the bot did.", "",
         f"Canon book: **{len(F)} trades**, depth resolved on {cov} ({cov/len(F):.0%})"
         + (f", {len(miss)} days without a depth file." if miss else "."), "",
         "| check | read | n pass | R pass | R fail | **R lift** | WR pass | WR fail |",
         "|---|---|---:|---:|---:|---:|---:|---:|"]
    summary = {}
    for name in ("W", "D", "WALLSZ"):
        for lbl, C in (("fill-bar CLOSE (as calibrated)", C_late),
                       ("**fill-bar OPEN (honest)**", C_open)):
            r = lift(F, C[name])
            if r is None:
                L.append(f"| `{name}` | {lbl} | — | — | — | — | — | — |")
                continue
            summary[(name, lbl[:4])] = r["lift"]
            L.append(f"| `{name}` | {lbl} | {r['n_pass']} | {r['r_pass']:+.3f} | "
                     f"{r['r_fail']:+.3f} | **{r['lift']:+.3f}R** | {r['wr_pass']:.0%} | "
                     f"{r['wr_fail']:.0%} |")
    L.append("")

    keep = [(k[0], summary.get((k[0], "fill"), np.nan), summary.get((k[0], "**fi"), np.nan))
            for k in [("W",), ("D",), ("WALLSZ",)]]
    L += ["## What it means", "", "| check | calibrated lift | honest lift | retained |",
          "|---|---:|---:|---:|"]
    for name, a, b in keep:
        L.append(f"| `{name}` | {a:+.3f}R | {b:+.3f}R | "
                 + (f"{b/a:.0%} |" if a and np.isfinite(a) and abs(a) > 1e-9 else "— |"))
    L += ["", "§5.12.10 records depth as carrying the canon's entire edge at **+0.5 to",
          "+1.3R**. That band was measured at the fill-bar-close read. The honest column",
          "above is the conservative bound on what the live bot can hold — live sits",
          "*between* the two reads, because a fill happens somewhere inside its bar.", "",
          "**No threshold, config or book is changed by this. Angus's call.**", ""]

    text = "\n".join(L)
    print(text)
    OUT_MD.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
