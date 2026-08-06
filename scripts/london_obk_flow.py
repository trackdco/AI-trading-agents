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

from src.engine import book as _book  # noqa: E402
from src.engine import footprint as _fp  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-obk-L3-flow-and-autopsy.md"
SRC = ROOT / "output/london_obk_l1.parquet"
OUT_PARQUET = ROOT / "output/london_obk_flow.parquet"
OUT_MD = ROOT / "output/london_obk_flow.md"

# non-holdout tape only — the six sealed 2023/24 files are NOT read
# Retained for the record of what the original run consumed. The live file list now
# comes from _fp.fit_span_files(), which excludes the six sealed holdout files by name
# rather than relying on this literal staying correct.
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
    """Per-minute signed delta and volume from the aggressor-tagged tape.

    THREE DEFECTS FIXED 2026-08-06 (Phase 4 inventory). All predate this line and all
    fed `output/london_obk_flow.parquet`, so that artifact and the L3 flow numbers built
    on it need regenerating before they are quoted again:

    1. **Inverted sign.** This read `np.where(side == "A", volume, -volume)`, making the
       SELLER-aggressor positive. The convention is B - A (buyer-positive), settled
       empirically at r = +0.7293 over 287 sessions. Every `delta_*` feature here --
       including `delta_sweep`, the prereg's named mechanism variable -- carried the
       wrong sign, and R^2 cannot see that.
    2. **No band clean.** It read only `["ts_minute", "side", "volume"]`, so without
       `price` it could not band-filter, and consumed calendar-spread and back-month
       prints alongside the outright.
    3. **Bypassed the chokepoint**, which is why (1) and (2) survived: the path was
       assembled in a variable, so `test_no_direct_footprint_reads` never matched it.
       `test_no_footprint_reads_via_a_variable_path` now catches that shape.
    """
    d = _fp.load_footprint(_fp.fit_span_files(), _fp.cached_front_month_bands(),
                           report=False)
    delta = _fp.signed_delta(d, by=("ts_minute",)).rename("delta")
    vol = d.groupby("ts_minute").volume.sum().rename("vol")
    g = pd.concat([delta, vol], axis=1)
    g.index = g.index.tz_convert("America/New_York")
    return g


def load_depth() -> pd.DataFrame:
    """Per-minute at-price book metrics. At-price reads ONLY (canon finding 2a9c221).

    FIXED 2026-08-06: this indexed the book by `ts_event`, which the extraction FLOORS
    to the minute -- the row labelled T is the book at ~T+59.9s (`ts_recv` carries the
    truth). Combined with the `searchsorted(..., "right") - 1` below, an entry at minute
    M took the row labelled M and therefore the book as it stood ~60 seconds AFTER the
    decision. A one-minute lookahead on `book_imb` and `wall_ratio_opp`, invisible to
    every downstream check. `src.engine.book` indexes by true observation time.
    """
    D = _book.load_depth(depth_dir=DEPTH_DIR, tz="America/New_York")
    bsz = D[_book.BID_SZ].to_numpy(float)
    asz = D[_book.ASK_SZ].to_numpy(float)
    bt, at = bsz.sum(1), asz.sum(1)
    return pd.DataFrame({
        "bid_wall": bsz.max(1) / np.maximum(np.median(bsz, axis=1), 1e-9),
        "ask_wall": asz.max(1) / np.maximum(np.median(asz, axis=1), 1e-9),
        # kept as the historical bid-share in [0,1] rather than the [-1,1] form, so the
        # column means what the prereg declared. src.engine.book.features gives imb_L*.
        "book_imb": bt / np.maximum(bt + at, 1e-9),
    }, index=D.index).sort_index()


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
        F1 = flow[flow["arm"] == "F1"]
        num = lambda f, e, w: band_r(F1, f, e, w, 1.0)          # noqa: E731
        s = lambda v: "n/a" if v is None else f"{v:+.3f}R"      # noqa: E731
        # Every number below is READ FROM THE DATA. It was hardcoded prose until
        # 2026-08-06, and when the inverted delta sign was fixed the table regenerated
        # while the narrative beneath it did not -- leaving a document that contradicted
        # itself and still quoted +0.448R for a cell that had become -0.099R. A verdict
        # that cannot regenerate is a verdict that quietly goes stale.
        sw25_hi, sw25_lo = num("delta_sweep", "2025", "high"), num("delta_sweep", "2025", "low")
        sw26_hi, sw26_lo = num("delta_sweep", "2026", "high"), num("delta_sweep", "2026", "low")
        de26_hi = num("delta_entry", "2026", "high")
        worse25 = (sw25_hi is not None and sw25_lo is not None and sw25_hi < sw25_lo)
        L += ["### The mechanism variable failed, and that is the finding", "",
              "`delta_sweep` was named in the prereg — before the join — as the one",
              "feature that had to work: *\"the fade thesis is that the break traps",
              "aggressive size, and the delta printed during the sweep IS that size.\"*",
              "",
              f"It does not confirm. 2025 H2: high {s(sw25_hi)} vs low {s(sw25_lo)} "
              f"({'high is WORSE — against the prediction' if worse25 else 'high is better — WITH the prediction'}). "
              f"2026: high {s(sw26_hi)} vs low {s(sw26_lo)}.",
              "**The two eras point opposite ways, and that is the kill** — an era-flip",
              "is not a weak confirmation, it is the absence of one.", "",
              "**Bars could not see the trapped counterparty and neither can the tape.**",
              "That was the argument for running L3 at all: V3 half-failed on candles",
              "and the defence was that trapped size is a flow object. The flow says no.",
              "",
              f"Control reference, which the prereg pre-committed to calling out: "
              f"`delta_entry` high in 2026 is {s(de26_hi)}, with no story attached and",
              "no 2025 support.", ""]
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
