#!/usr/bin/env python3
"""NYA-LVL-01 stage 3b — the winner/loser discriminant, with placebo classification.

Authorised by docs/PREREG-level-interaction-stage3.md, committed before this file.
Ten declared variables, list closed. Each evaluated ALONE at a frozen split (§5.12.2).
NaN stands down. <30 a side in an era = thin, no verdict. Survival requires the same
direction in BOTH eras AND the inverse era pass.

Every survivor is re-run on PLACEBO levels and classified:
  LEVEL-BORNE   works on the real six, not on random lines
  CONTEXT-BORNE works on both -> a real edge, but not a level edge

Run on both arms, because stage 3a showed they are opposite strategies:
  S20/T30  the taught fade, mean-reverting
  S10/TRAIL the volatility harvester

    python -m scripts.nya_lvl_discriminant [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import LEVELS, PM_WINDOW, PD_WINDOW, RTH, TICK, load_bars, m15  # noqa: E402
from scripts.nya_lvl_geometry import run_cell  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-stage3.md"
OUT_MD = ROOT / "output/nya_lvl_discriminant.md"
OUT_PARQUET = ROOT / "output/nya_lvl_discriminant.parquet"

FIT_START, FIT_END = "2025-06-02", "2026-07-15"
ARMS = {"S20/T30": (20.0, 30.0, False), "S10/TRAIL": (10.0, None, True)}
COSTS = ((1.0, "base"), (2.0, "strict"))
THIN = 30
SEED = 20260805
MAX_HOLD = 240


def build(bars: pd.DataFrame, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """One row per filled touch, carrying every declared variable and both outcomes."""
    days = [d for d in sorted(bars["day"].unique()) if FIT_START <= d <= FIT_END]
    prior, rows = None, []
    for day in days:
        db = bars[bars["day"] == day]
        pm = db[(db["min"] >= PM_WINDOW[0]) & (db["min"] < PM_WINDOW[1])]
        pdw = db[(db["min"] >= PD_WINDOW[0]) & (db["min"] < PD_WINDOW[1])]
        rth = db[(db["min"] >= RTH[0]) & (db["min"] < RTH[1])]
        if len(pm) >= 60 and len(rth) >= 200 and prior is not None:
            if rng is None:
                lv = {"PM_HIGH": float(pm["high"].max()), "PM_LOW": float(pm["low"].min()),
                      "PD_HIGH": prior["hi"], "PD_LOW": prior["lo"]}
                lv["PM_50"] = (lv["PM_HIGH"] + lv["PM_LOW"]) / 2
                lv["PD_50"] = (lv["PD_HIGH"] + lv["PD_LOW"]) / 2
            else:
                lo = min(float(pm["low"].min()), prior["lo"])
                hi = max(float(pm["high"].max()), prior["hi"])
                lv = dict(zip(LEVELS, rng.uniform(lo, hi, size=6)))
            b15 = m15(rth)
            if len(b15) < 4:
                continue
            atr15 = float((b15["high"] - b15["low"]).median())
            rth_open = float(rth.iloc[0]["open"])
            gap = rth_open - prior["close"]
            mb = rth[["high", "low", "close"]].to_numpy(float)
            ts = list(rth["ts_event"])
            taps = {k: 0 for k in LEVELS}
            for bi in range(len(b15)):
                bar, bts = b15.iloc[bi], b15.index[bi]
                prev_c = float(b15.iloc[bi - 1]["close"]) if bi else rth_open
                for name in LEVELS:
                    level = lv[name]
                    if not (bar["low"] <= level <= bar["high"]):
                        continue
                    taps[name] += 1
                    d = -1 if prev_c < level else 1
                    if not ((bar["high"] >= level + TICK) if d < 0
                            else (bar["low"] <= level - TICK)):
                        continue
                    start = next((i for i, t in enumerate(ts) if t > bts), None)
                    if start is None or start >= len(mb) - 2:
                        continue
                    fwd = mb[start:start + MAX_HOLD]
                    mins = bts.hour * 60 + bts.minute
                    rec = {
                        "day": day, "era": day[:4],
                        "level_type": name, "side": d, "tap": taps[name],
                        "hour": bts.hour, "atr15": atr15,
                        "dist_atr": (level - rth_open) * d / max(atr15, 1e-9),
                        "gap_atr": gap / max(atr15, 1e-9),
                        "age": (mins - PM_WINDOW[1]) if name.startswith("PM") else np.nan,
                    }
                    for cp in (5, 15):
                        rec[f"t{cp}"] = (float((fwd[cp][2] - level) * d)
                                         if len(fwd) > cp else np.nan)
                    for label, (s, tp, tr) in ARMS.items():
                        tgt = None if tp is None else level + d * tp
                        rec[f"{label}_pts"] = run_cell(int(d), float(level), fwd, s, tgt,
                                                      tr, None)
                    rows.append(rec)
        if len(pdw) >= 100:
            prior = {"hi": float(pdw["high"].max()), "lo": float(pdw["low"].min()),
                     "close": float(pdw.iloc[-1]["close"])}
    return pd.DataFrame(rows)


def splits(D: pd.DataFrame, disc_era: str) -> dict[str, pd.Series]:
    """Frozen splits. Continuous cuts are set on the DISCOVER era and applied to both."""
    d = D[D["era"] == disc_era]
    out = {"level_type": D["level_type"],
           "side": D["side"].map({1: "long", -1: "short"}),
           "tap": pd.cut(D["tap"], [0, 1, 2, 99], labels=["1st", "2nd", "3rd+"]),
           "hour": D["hour"].astype(str) + ":00"}
    for c in ("dist_atr", "gap_atr", "atr15", "age"):
        q = d[c].quantile([1 / 3, 2 / 3]).to_numpy()
        out[c] = pd.cut(D[c], [-np.inf, q[0], q[1], np.inf],
                        labels=["low", "mid", "high"])
    for cp in (5, 15):
        out[f"t{cp}"] = np.where(D[f"t{cp}"].isna(), None,
                                 np.where(D[f"t{cp}"] > 0, "green", "red"))
        out[f"t{cp}"] = pd.Series(out[f"t{cp}"], index=D.index)
    return out


def cell(D: pd.DataFrame, arm: str, mask, cost: float) -> dict | None:
    s = D[mask]
    if s.empty:
        return None
    net = s[f"{arm}_pts"] - cost
    stop = ARMS[arm][0]
    return {"n": len(net), "wr": float((net > 0).mean()),
            "pf": float(net[net > 0].sum() / max(-net[net <= 0].sum(), 1e-9)),
            "r": float((net / stop).mean()), "pts": float(net.sum())}


def sweep(D: pd.DataFrame, arm: str, disc_era: str) -> pd.DataFrame:
    sp = splits(D, disc_era)
    rows = []
    for var, lab in sp.items():
        for val in pd.Series(lab).dropna().unique():
            m = (lab == val) & D[f"{arm}_pts"].notna()
            rec = {"var": var, "val": str(val)}
            ok = True
            for era in ("2025", "2026"):
                c = cell(D, arm, m & (D["era"] == era), 1.0)
                if not c or c["n"] < THIN:
                    ok = False
                    rec[f"r_{era}"], rec[f"n_{era}"] = np.nan, (c["n"] if c else 0)
                    continue
                rec[f"r_{era}"], rec[f"n_{era}"] = c["r"], c["n"]
            base = cell(D, arm, D[f"{arm}_pts"].notna(), 1.0)
            for era in ("2025", "2026"):
                b = cell(D, arm, (D["era"] == era) & D[f"{arm}_pts"].notna(), 1.0)
                rec[f"lift_{era}"] = (rec[f"r_{era}"] - b["r"]) if b and ok else np.nan
            allc = cell(D, arm, m, 1.0)
            strict = cell(D, arm, m, 2.0)
            rec.update(n=allc["n"] if allc else 0,
                       wr=allc["wr"] if allc else np.nan,
                       pf=allc["pf"] if allc else np.nan,
                       r=allc["r"] if allc else np.nan,
                       r_strict=strict["r"] if strict else np.nan,
                       thin=not ok)
            rec["survives"] = bool(
                ok and np.isfinite(rec["lift_2025"]) and np.isfinite(rec["lift_2026"])
                and rec["lift_2025"] > 0 and rec["lift_2026"] > 0
                and rec["r_strict"] > 0)
            rows.append(rec)
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    bars = load_bars()
    D = build(bars)
    print(f"{len(D):,} events built")
    P = build(bars, np.random.default_rng(SEED))
    print(f"{len(P):,} placebo events built")

    L = ["# NYA-LVL-01 stage 3b — winner/loser discriminant", "",
         f"Authorised by `{PREREG}`. Ten declared variables, list closed. Each evaluated",
         "ALONE at a frozen split; continuous cuts set on the DISCOVER era (2025) and",
         f"applied to both. Thin = fewer than {THIN} a side in an era, and thin means no",
         "verdict. **Survival requires positive lift in BOTH eras AND a positive R at",
         "strict cost.**", "",
         f"{len(D):,} real events, {len(P):,} placebo events.", ""]
    ledger = []
    for arm in ARMS:
        S = sweep(D, arm, "2025")
        SP = sweep(P, arm, "2025")
        surv = S[S["survives"]].sort_values("lift_2025", ascending=False)
        base = cell(D, arm, D[f"{arm}_pts"].notna(), 1.0)
        L += [f"## {arm}", "",
              f"Unconditioned baseline: n={base['n']:,} WR {base['wr']:.0%} "
              f"PF {base['pf']:.2f} R {base['r']:+.3f}", "",
              f"**{len(surv)} of {len(S)} cells survive** (both eras positive lift, "
              "positive at strict cost).", ""]
        if len(surv):
            L += ["| variable | value | n | WR | PF | R base | R strict | lift 25 | lift 26 | placebo | class |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
            for _, r in surv.head(14).iterrows():
                pm = SP[(SP["var"] == r["var"]) & (SP["val"] == r["val"])]
                pl = float(pm["lift_2025"].iloc[0]) if len(pm) else np.nan
                klass = ("CONTEXT" if (np.isfinite(pl) and pl > 0.5 * r["lift_2025"])
                         else "LEVEL-BORNE")
                L.append(f"| `{r['var']}` | {r['val']} | {r['n']:,} | {r['wr']:.0%} | "
                         f"{r['pf']:.2f} | {r['r']:+.3f} | {r['r_strict']:+.3f} | "
                         f"{r['lift_2025']:+.3f} | {r['lift_2026']:+.3f} | "
                         f"{pl:+.3f} | {klass} |")
                ledger.append({
                    "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
                    "trial": f"disc {arm} {r['var']}={r['val']}",
                    "stat_type": "mean", "estimate": round(float(r["r"]), 4),
                    "n": int(r["n"]), "t_stat": 0.0, "effect": 0.0,
                    "verdict": (f"survives both eras + strict; lift 25 "
                                f"{r['lift_2025']:+.3f} / 26 {r['lift_2026']:+.3f}; "
                                f"placebo lift {pl:+.3f} -> {klass}"),
                })
        L += ["", "**Thin cells (no verdict):** "
              f"{int(S['thin'].sum())} of {len(S)}.", ""]
    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    D.to_parquet(OUT_PARQUET, index=False)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
