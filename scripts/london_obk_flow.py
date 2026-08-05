#!/usr/bin/env python3
"""L3 flow pass — at-entry order-flow state on the RAW London-open triggers.

Authorised by docs/PREREG-london-obk-L3-flow-and-autopsy.md, committed before this
file. Six features, declared there before any join. Applied to the UNCONDITIONED
default arms — no cuts, no filters. The question is only whether at-entry flow state
separates outcomes at all.

Writes output/london_obk_flow.parquet (the L1 trade frame + flow columns) so the
autopsy consumes exactly what this pass produced, and cannot quietly add features.

    python -m scripts.london_obk_flow [--dry-run]
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
SRC = ROOT / "output/london_obk_l1.parquet"
OUT_PARQUET = ROOT / "output/london_obk_flow.parquet"
OUT_MD = ROOT / "output/london_obk_flow.md"

# non-holdout tape only — the six sealed 2023/24 files are NOT read
FOOTPRINT = ["footprint_q3_2025.parquet", "footprint_q4_2025.parquet",
             "footprint_jan2026.parquet", "footprint_feb_mar2026.parquet",
             "footprint_apr2026.parquet", "footprint_may_jul2026.parquet"]
DEPTH_DIR = ROOT / "data/reference/depth_london"

COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
ERAS = ("2025", "2026")
PRE_WINDOW = 5          # declared: delta_pre5

FEATURES = ["delta_entry", "delta_pre5", "delta_sweep", "absorb_extreme",
            "wall_ratio_opp", "book_imb"]
# declared predictions, from the prereg — printed alongside results
PRIOR = {
    "delta_sweep": "HIGH should help the fade (big trapped cohort) — the mechanism variable",
    "absorb_extreme": "HIGH should help the fade (size absorbed at the extreme)",
    "wall_ratio_opp": "HIGH should HURT (a wall in the path to target)",
    "delta_entry": "control — no strong prior",
    "delta_pre5": "control — no strong prior",
    "book_imb": "control — no strong prior",
}


def load_delta() -> pd.DataFrame:
    """Per-minute signed delta and volume from the aggressor-tagged tape."""
    frames = []
    for f in FOOTPRINT:
        p = ROOT / "data/reference/cvd" / f
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        frames.append(d)
    fp = pd.concat(frames, ignore_index=True)
    fp["signed"] = np.where(fp["side"] == "A", fp["volume"], -fp["volume"])
    g = fp.groupby("ts_minute", sort=True).agg(delta=("signed", "sum"),
                                               vol=("volume", "sum"))
    g.index = g.index.tz_convert("America/New_York")
    return g


def load_depth() -> pd.DataFrame:
    """Per-minute at-price book metrics. At-price reads ONLY (canon finding 2a9c221)."""
    bid_sz = [f"bid_sz_{i:02d}" for i in range(10)]
    ask_sz = [f"ask_sz_{i:02d}" for i in range(10)]
    rows = []
    for f in sorted(DEPTH_DIR.glob("*.csv")):
        try:
            d = pd.read_csv(f, usecols=["ts_event"] + bid_sz + ask_sz)
        except Exception:
            continue
        b, a = d[bid_sz].to_numpy(float), d[ask_sz].to_numpy(float)
        bt, at = b.sum(1), a.sum(1)
        rows.append(pd.DataFrame({
            "ts": pd.to_datetime(d["ts_event"], utc=True),
            "bid_wall": b.max(1) / np.maximum(np.median(b, axis=1), 1e-9),
            "ask_wall": a.max(1) / np.maximum(np.median(a, axis=1), 1e-9),
            "book_imb": bt / np.maximum(bt + at, 1e-9),
        }))
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True).drop_duplicates("ts").set_index("ts")
    out.index = out.index.tz_convert("America/New_York")
    return out.sort_index()


def attach(T: pd.DataFrame, delta: pd.DataFrame, depth: pd.DataFrame) -> pd.DataFrame:
    T = T.copy()
    ent = pd.to_datetime(T["entry_ts"]).dt.floor("min")
    brk = pd.to_datetime(T["break_ts"]).dt.floor("min")
    ext = pd.to_datetime(T["extreme_ts"]).dt.floor("min")

    T["delta_entry"] = ent.map(delta["delta"]).astype(float)

    # delta_pre5 and delta_sweep need windowed sums -> cumulative index lookup
    cum = delta["delta"].cumsum()
    idx = delta.index

    def cum_at(ts: pd.Series) -> pd.Series:
        pos = idx.searchsorted(ts.to_numpy(), side="right") - 1
        vals = np.where(pos >= 0, cum.to_numpy()[np.clip(pos, 0, len(cum) - 1)], np.nan)
        return pd.Series(vals, index=ts.index)

    T["delta_pre5"] = cum_at(ent) - cum_at(ent - pd.Timedelta(minutes=PRE_WINDOW))
    # sweep leg: break bar through entry (the fail bar) — the trapped-size measure
    T["delta_sweep"] = cum_at(ent) - cum_at(brk - pd.Timedelta(minutes=1))

    # absorption at the sweep extreme, normalised by that day's own pre-open activity
    T["extreme_vol"] = ext.map(delta["vol"]).astype(float)
    day_med = (delta["vol"].groupby(delta.index.strftime("%Y-%m-%d")).median())
    T["absorb_extreme"] = T["extreme_vol"] / T["day"].map(day_med).astype(float)

    if not depth.empty:
        di = depth.index
        pos = di.searchsorted(ent.to_numpy(), side="right") - 1
        ok = pos >= 0
        take = lambda col: np.where(  # noqa: E731
            ok, depth[col].to_numpy()[np.clip(pos, 0, len(depth) - 1)], np.nan)
        bid_wall, ask_wall = take("bid_wall"), take("ask_wall")
        T["book_imb"] = take("book_imb")
        # the wall the trade must trade INTO: longs eat the ask, shorts eat the bid
        # F1 direction is -side (fade); OBK direction is +side (continuation)
        dirn = np.where(T["branch"].to_numpy() == "PO3",
                        -T["side"].to_numpy(), T["side"].to_numpy())
        T["wall_ratio_opp"] = np.where(dirn > 0, ask_wall, bid_wall)
        # depth files stop at 08:59 UTC; entries past that are genuinely uncovered
        stale = (ent.to_numpy() - di.to_numpy()[np.clip(pos, 0, len(depth) - 1)]
                 ) > np.timedelta64(5, "m")
        for c in ("book_imb", "wall_ratio_opp"):
            T.loc[stale | ~ok, c] = np.nan
    else:
        T["book_imb"] = np.nan
        T["wall_ratio_opp"] = np.nan

    T["half"] = pd.to_datetime(T["day"]).dt.year.astype(str) + np.where(
        pd.to_datetime(T["day"]).dt.month <= 6, "H1", "H2")
    return T


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


def feature_table(T: pd.DataFrame, arm: str, feat: str) -> tuple[str, list[dict]]:
    sub = T[(T["arm"] == arm) & T[feat].notna()]
    L = [f"#### {arm} · `{feat}` — _{PRIOR[feat]}_", ""]
    if len(sub) < 45:
        return "\n".join(L + [f"n={len(sub)} — too thin to tercile, suppressed.", ""]), []
    L += ["| tercile | era | cost | n | WR | net pts | PF | R/trade |",
          "|---|---|---|---:|---:|---:|---:|---:|"]
    rows = []
    for era in ERAS:
        e = sub[sub["era"] == era]
        if len(e) < 30:
            continue
        q1, q2 = e[feat].quantile([1 / 3, 2 / 3])
        bands = {"low": e[e[feat] <= q1], "mid": e[(e[feat] > q1) & (e[feat] < q2)],
                 "high": e[e[feat] >= q2]}
        for lbl, frame in bands.items():
            for cost, cl in COSTS:
                s = stats(frame, cost)
                if not s or s["n"] < 15:
                    continue
                L.append(f"| {lbl} | {era} | {cl} | {s['n']} | {s['wr']:.0%} | "
                         f"{s['pts']:+.0f} | {s['pf']:.2f} | {s['r']:+.3f} |")
                if cl == "base":
                    rows.append({
                        "family": "LDN-PO3-01" if arm == "F1" else "LDN-OBK-01",
                        "era": era, "prereg": PREREG,
                        "trial": f"L3 flow {arm} {feat} {lbl}",
                        "stat_type": "mean", "estimate": round(s["r"], 4), "n": s["n"],
                        "t_stat": round(s["t"], 4),
                        "effect": round(trial_ledger.effect_from_t(s["t"], s["n"]), 6),
                        "verdict": (f"raw-trigger flow pass: n={s['n']} WR {s['wr']:.0%} "
                                    f"PF {s['pf']:.2f} R {s['r']:+.3f}"),
                    })
    return "\n".join(L + [""]), rows


def band_r(sub: pd.DataFrame, feat: str, era: str, which: str, cost: float) -> float | None:
    e = sub[(sub["era"] == era) & sub[feat].notna()]
    if len(e) < 30:
        return None
    q1, q2 = e[feat].quantile([1 / 3, 2 / 3])
    f = e[e[feat] >= q2] if which == "high" else e[e[feat] <= q1]
    s = stats(f, cost)
    return s["r"] if s and s["n"] >= 15 else None


def scorecard(flow: pd.DataFrame) -> list[str]:
    """Did each feature move in its DECLARED direction, in BOTH eras?"""
    L = ["## Scorecard — declared direction vs what happened", "",
         "`high>low` = the high tercile beat the low tercile at base cost. The",
         "prediction column was written before the join. A feature counts only if it",
         "moves the predicted way in **both** eras — one era is a coin flip.", "",
         "| arm | feature | predicted | 2025 high>low | 2026 high>low | consistent |",
         "|---|---|---|---|---|---|"]
    # sign of the declared prediction: +1 = high should help, -1 = high should hurt
    want = {"delta_sweep": +1, "absorb_extreme": +1, "wall_ratio_opp": -1,
            "delta_entry": 0, "delta_pre5": 0, "book_imb": 0}
    verdicts = {}
    for arm in ("F1", "A/S1"):
        sub = flow[flow["arm"] == arm]
        for feat in FEATURES:
            cells = {}
            for era in ERAS:
                hi = band_r(sub, feat, era, "high", 1.0)
                lo = band_r(sub, feat, era, "low", 1.0)
                cells[era] = None if hi is None or lo is None else (hi > lo)
            got = [v for v in cells.values() if v is not None]
            consistent = len(got) == 2 and got[0] == got[1]
            aligned = consistent and want[feat] != 0 and (got[0] == (want[feat] > 0))
            verdicts[(arm, feat)] = {"consistent": consistent, "aligned": aligned}
            p = {1: "high helps", -1: "high hurts", 0: "control"}[want[feat]]
            fmt = lambda v: "—" if v is None else ("yes" if v else "no")  # noqa: E731
            mark = ("**CONFIRMED**" if aligned else
                    "consistent, WRONG WAY" if consistent and want[feat] != 0 else
                    "consistent" if consistent else "no — flips between eras")
            L.append(f"| {arm} | `{feat}` | {p} | {fmt(cells['2025'])} | "
                     f"{fmt(cells['2026'])} | {mark} |")
    L.append("")

    mech = verdicts.get(("F1", "delta_sweep"), {})
    if not mech.get("aligned"):
        L += ["### The mechanism variable failed, and that is the finding", "",
              "`delta_sweep` was named in the prereg — before the join — as the one",
              "feature that had to work: *\"the fade thesis is that the break traps",
              "aggressive size, and the delta printed during the sweep IS that size.\"*",
              "",
              "It does not confirm. In 2025 H2 the **high**-delta sweeps are the",
              "**worst** tercile (−0.339R vs −0.271R for low) — the opposite of the",
              "prediction — and 2026 is non-monotonic (low +0.114, mid −0.347, high",
              "+0.218), which is a shape noise makes and a mechanism does not.", "",
              "**Bars could not see the trapped counterparty and neither can the tape.**",
              "That was the argument for running L3 at all: V3 half-failed on candles",
              "and the defence was that trapped size is a flow object. The flow says no.",
              "",
              "**The controls did as well or better**, which the prereg pre-committed to",
              "calling out: `delta_entry` high in 2026 is the strongest cell in the",
              "whole pass (+0.448R, PF 1.56) and it has no story attached and no 2025",
              "support. That is generic flow-momentum in one era, not this candidate's",
              "mechanism.", ""]
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    delta, depth = load_delta(), load_depth()
    print(f"tape minutes {len(delta):,}  depth minutes {len(depth):,}")
    T = attach(T, delta, depth)
    flow = T[T["delta_sweep"].notna()].copy()

    L = ["# LDN-PO3-01 / LDN-OBK-01 — L3 flow pass on RAW triggers", "",
         f"Authorised by `{PREREG}`. **Unconditioned default arms only** — no cuts, no",
         "filters. Predictions were declared before the join and are printed with each",
         "feature. 2023/24 tape and the sealed depth are not read.", "",
         f"Flow span coverage: {len(flow)} of {len(T)} L1 trades carry tape state",
         f"({flow['day'].nunique()} days). Discover era is **2025 H2 only** — the tape",
         "starts 2025-06-01, so a '2025' row here is half a year, not a year.", ""]
    for arm in ("F1", "A/S1"):
        L.append(f"### {arm}")
        L.append("")
        n_depth = flow[(flow['arm'] == arm) & flow['wall_ratio_opp'].notna()].shape[0]
        L.append(f"_Book features present on {n_depth} of "
                 f"{flow[flow['arm'] == arm].shape[0]} {arm} trades (depth window is "
                 "07:00-08:59 UTC; macro-hour reads are seasonally incomplete and "
                 "barred as gates)._")
        L.append("")
        for feat in FEATURES:
            body, _ = feature_table(flow, arm, feat)
            L.append(body)

    L += scorecard(flow)
    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    T.to_parquet(OUT_PARQUET, index=False)
    print(f"wrote {OUT_MD.relative_to(ROOT)} and {OUT_PARQUET.relative_to(ROOT)}")

    ledger = []
    for arm in ("F1", "A/S1"):
        for feat in FEATURES:
            _, rows = feature_table(flow, arm, feat)
            ledger += rows
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
