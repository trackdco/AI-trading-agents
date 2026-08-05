#!/usr/bin/env python3
"""NYA-LVL-01 — the depth pass. Authorised by docs/PREREG-level-interaction-depth.md.

Five canon checks at canon thresholds, each ALONE, NaN standing down.
Scored on WIN RATE AT FIXED R (1.0R and 1.5R), not profit factor — PF rewards a
trivially-close target and that is how a 0.375R arm scored 79%.

Depth covers 08:00-10:29 ET only, so ~43% of events are covered and the rest stand
down. Any result here is about the first ninety minutes of RTH.

    python -m scripts.nya_lvl_depth [--perms N] [--dry-run]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import load_bars  # noqa: E402
from scripts.nya_lvl_rebuild import build, score  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-depth.md"
OUT_MD = ROOT / "output/nya_lvl_depth.md"
STOP = 15.0
OBJ = {"1.0R": 1.0, "1.5R": 1.5}
BE = {"1.0R": 0.50, "1.5R": 0.40}
WALL_SZ_MIN = 7.0
THIN = 30
SEED = 20260805


def depth_index() -> dict[str, pd.DataFrame]:
    """day -> per-minute book snapshot (long form collapsed to one row per minute)."""
    out = {}
    for f in sorted(glob.glob(str(ROOT / "data/reference/depth_202*/*_ny.csv"))):
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        if not {"ts", "side", "price", "size"}.issubset(d.columns):
            continue
        d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce").dt.tz_convert(
            "America/New_York")
        d = d.dropna(subset=["ts"])
        d["mi"] = d["ts"].dt.floor("min")
        out[str(d["ts"].dt.strftime("%Y-%m-%d").iloc[0])] = d
    return out


def at_minute(dep: pd.DataFrame, minute: pd.Timestamp, entry: float, long: bool) -> dict:
    sub = dep[dep["mi"] == minute]
    if sub.empty:
        return {}
    bid, ask = sub[sub["side"] == "bid"], sub[sub["side"] == "ask"]
    if bid.empty or ask.empty:
        bid, ask = sub[sub["side"] == "B"], sub[sub["side"] == "A"]
    if bid.empty or ask.empty:
        return {}
    bt, at = float(bid["size"].sum()), float(ask["size"].sum())
    above, below = sub[sub["price"] > entry], sub[sub["price"] < entry]
    f = {"thick": bt + at, "imb": (bt - at) / max(bt + at, 1e-9)}
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["above_d"], f["above_sz"] = float(w["price"] - entry), float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["below_d"], f["below_sz"] = float(entry - w["price"]), float(w["size"])
    return f


def attach(D: pd.DataFrame, dep_by_day: dict) -> pd.DataFrame:
    rows = []
    for t in D.itertuples():
        dep = dep_by_day.get(t.day)
        rows.append(at_minute(dep, pd.Timestamp(t.entry_ts), float(t.level), t.side > 0)
                    if dep is not None and pd.notna(getattr(t, "entry_ts", None)) else {})
    X = pd.DataFrame(rows, index=D.index)
    for c in ("thick", "imb", "above_d", "above_sz", "below_d", "below_sz"):
        if c not in X:
            X[c] = np.nan
    return pd.concat([D, X], axis=1)


def checks(D: pd.DataFrame) -> pd.DataFrame:
    long = (D["side"] > 0).to_numpy()
    behind = np.where(long, D["below_d"], D["above_d"])
    ahead = np.where(long, D["above_d"], D["below_d"])
    ahead_sz = np.where(long, D["above_sz"], D["below_sz"])
    known = D["thick"].notna().to_numpy()
    g = lambda v: pd.Series(np.where(known, v, np.nan), index=D.index)  # noqa: E731
    C = pd.DataFrame(index=D.index)
    C["W"] = g(np.isnan(behind).astype(float))
    C["D"] = g((~np.isnan(ahead)).astype(float))
    C["WALLSZ"] = g(((~np.isnan(ahead)) & (np.nan_to_num(ahead_sz) >= WALL_SZ_MIN)).astype(float))
    imb_dir = np.where(long, D["imb"], -D["imb"])
    C["IMBWITH"] = g((imb_dir > 0).astype(float))
    med = D.loc[(D["era"] == "2025") & D["thick"].notna(), "thick"].median()
    C["THICKHI"] = g((D["thick"] > med).astype(float))
    return C


def sweep(D: pd.DataFrame, C: pd.DataFrame) -> list[dict]:
    out = []
    for chk in C.columns:
        for val, lab in ((1.0, "pass"), (0.0, "fail")):
            m = C[chk] == val
            rec = {"check": chk, "arm": lab, "n": int(m.sum())}
            for o in OBJ:
                col = f"win{o}"
                rec[f"wr_{o}"] = float(D.loc[m, col].mean()) if m.sum() else np.nan
                cov = D[C[chk].notna()]
                rec[f"base_{o}"] = float(cov[col].mean())
                rec[f"lift_{o}"] = rec[f"wr_{o}"] - rec[f"base_{o}"]
                for era in ("2025", "2026"):
                    me = m & (D["era"] == era)
                    b = cov[cov["era"] == era][col].mean()
                    rec[f"l{era}_{o}"] = (float(D.loc[me, col].mean()) - b
                                          if me.sum() >= THIN else np.nan)
            out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bars = load_bars()
    D, P = build(bars)
    for o, rr in OBJ.items():
        D[f"win{o}"] = (score(D, P, ("x", STOP, STOP * rr, False)) - 1.0) > 0
    print("loading depth ...", flush=True)
    dep = depth_index()
    print(f"depth days loaded: {len(dep)}", flush=True)
    D = attach(D, dep)
    C = checks(D)
    cov = int(D["thick"].notna().sum())
    L = ["# NYA-LVL-01 — depth pass", "",
         f"Authorised by `{PREREG}`. Five canon checks, each ALONE at frozen canon",
         "thresholds. **Scored on win rate at fixed R, not profit factor.** NaN stands",
         "down.", "",
         f"**Depth resolved on {cov:,} of {len(D):,} events ({cov/len(D):.0%})** — the",
         "archive covers 08:00-10:29 ET, so this is a statement about the first ninety",
         "minutes of RTH and nothing else.", "",
         f"Baseline on covered events: 1.0R **{D[D.thick.notna()]['win1.0R'].mean():.1%}** "
         f"(BE 50%) / 1.5R **{D[D.thick.notna()]['win1.5R'].mean():.1%}** (BE 40%)", "",
         "| check | arm | n | WR 1.0R | lift | WR 1.5R | lift | 25 lift | 26 lift | survives |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    ledger, surv = [], []
    for r in sweep(D, C):
        ok = (r["arm"] == "pass" and all(
            np.isfinite(r.get(f"l{e}_{o}", np.nan)) and r[f"l{e}_{o}"] > 0
            for e in ("2025", "2026") for o in OBJ))
        if ok:
            surv.append(r)
        L.append(f"| `{r['check']}` | {r['arm']} | {r['n']:,} | "
                 f"{r['wr_1.0R']:.1%} | {r['lift_1.0R']:+.1%} | {r['wr_1.5R']:.1%} | "
                 f"{r['lift_1.5R']:+.1%} | {r.get('l2025_1.0R', float('nan')):+.1%} | "
                 f"{r.get('l2026_1.0R', float('nan')):+.1%} | "
                 f"{'**YES**' if ok else 'no'} |")
        if r["arm"] == "pass":
            ledger.append({
                "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
                "trial": f"depth {r['check']} WR-lift at 1.0R",
                "stat_type": "mean", "estimate": round(float(r["lift_1.0R"]), 4),
                "n": int(r["n"]), "t_stat": 0.0, "effect": 0.0,
                "verdict": (f"depth check, win-rate objective: 1.0R {r['wr_1.0R']:.1%} "
                            f"(lift {r['lift_1.0R']:+.1%}), 1.5R {r['wr_1.5R']:.1%} "
                            f"(lift {r['lift_1.5R']:+.1%}); "
                            f"{'survives both eras' if ok else 'does not survive'}"),
            })
    L += ["", f"**{len(surv)} of {len(C.columns)} checks survive** (positive win-rate "
          "lift in both eras at both objectives).", ""]
    if surv:
        best = max(surv, key=lambda r: r["lift_1.0R"])
        L += [f"Best: `{best['check']}` — 1.0R **{best['wr_1.0R']:.1%}** vs base "
              f"{best['base_1.0R']:.1%}, n={best['n']:,}.", ""]
    text = "\n".join(L)
    print(text)
    if args.dry_run:
        return 0
    OUT_MD.write_text(text)
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
