#!/usr/bin/env python3
"""At the +1R decision point, does the FULL order-flow stack separate hold from cut?

`scripts/intrade_flow_autopsy.py` asked this with aggressor delta alone and got AUC 0.69 —
real but not decisive. Angus, correctly: we hold the book snapshots and every other flow
tool too, so measure with all of them before concluding anything about what is readable.

The decision point is identical for every trade: the first minute it is +1R. Half the
trades that get there go on to run; the others give it back. If the flow stack separates
those two populations at that moment, in-trade discretion has something to work with.

Feature families at the decision minute:
  FLOW   trailing signed delta at 5 / 15 / 30 min, and its acceleration
  BOOK   `src/canon/features.depth_at` semantics EXACTLY (the definition the canon's own
         depth checks were validated on), referenced to the CURRENT price rather than the
         entry — "wall ahead" means ahead of where the trade is now, not where it started
  DELTA-BOOK  how the book CHANGED between the fill and the decision: is the wall ahead
         building or thinning, is the book thickening behind us

    python -m scripts.intrade_book_autopsy

METHODOLOGICAL WARNING, read before quoting any number below. This is in-sample univariate
screening on ~140 trades. `docs/CANON-MECHANICAL.md` (26-Jul bad-PA campaign) is the
cautionary precedent: 18 rules cleared the win-rate bar on canon trades and ZERO
corroborated on the full universe across both years. Everything here is a HYPOTHESIS FOR
THE 2023/24 HOLDOUT, not a finding, and certainly not a rule.
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.features import (
    depth_at,  # the canonical definition the canon validated on
)

BARS = ROOT / "data/reference/nq_1m_master.parquet"
BOOK = ROOT / "output/canon_book.parquet"
CVD = ROOT / "data/reference/cvd"
DEPTH_DIRS = [ROOT / "data/reference/depth_2025", ROOT / "data/reference/depth_2026"]
NY = "America/New_York"
SESSION_END = 16 * 60


def load_delta() -> pd.Series:
    parts = []
    for f in sorted(glob.glob(str(CVD / "footprint_*.parquet"))):
        d = pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
        d["volume"] = d["volume"].astype("int64")
        d["signed"] = np.where(d["side"] == "B", d["volume"], -d["volume"])
        parts.append(d.groupby("ts_minute")["signed"].sum())
    s = pd.concat(parts).groupby(level=0).sum().sort_index()
    s.index = pd.to_datetime(s.index, utc=True).tz_convert(NY)
    return s


def depth_index() -> dict[str, str]:
    idx = {}
    for d in DEPTH_DIRS:
        for f in glob.glob(str(d / "nq_depth_*_ny.csv")):
            idx[Path(f).stem.split("_")[2]] = f
    return idx


def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(BARS)
    ts = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    return b.assign(ts=ts, day=ts.dt.strftime("%Y-%m-%d"),
                    mins=ts.dt.hour * 60 + ts.dt.minute).sort_values("ts")


def build(book, bars, delta, didx) -> pd.DataFrame:
    by_day = {d: g for d, g in bars.groupby("day")}
    dep_cache: dict[str, pd.DataFrame] = {}
    rows = []
    for t in book.itertuples():
        g = by_day.get(str(t.day))
        if g is None:
            continue
        fill = pd.Timestamp(t.fill)
        fwd = g[(g.ts >= fill) & (g.mins <= SESSION_END)]
        if len(fwd) < 5:
            continue
        sign = 1.0 if t.direction == "long" else -1.0
        risk = float(t.risk)
        if risk <= 0:
            continue

        adverse = (fwd.low <= float(t.stop)) if sign > 0 else (fwd.high >= float(t.stop))
        alive = fwd.loc[:adverse.idxmax()] if adverse.any() else fwd
        favour = sign * (alive.high.to_numpy() - float(t.entry)) / risk
        hit = np.where(favour >= 1.0)[0]
        if not len(hit):
            continue                                  # never reached the decision point
        i = int(hit[0])
        t_dec = alive.ts.iloc[i]
        px_dec = float(t.entry) + sign * risk         # price at +1R

        d = delta.reindex(alive.ts).fillna(0.0).to_numpy() * sign
        rec = {"day": t.day, "fill": t.fill, "win_": t.win_, "direction": t.direction,
               "dollars": t.dollars, "risk": risk,
               # LABEL: did it keep running, or give it back?
               "ran_further": float(favour[i:].max() - 1.0),
               "won": bool(t.dollars > 0)}

        for k in (5, 15, 30):
            rec[f"flow_{k}"] = float(d[max(0, i - k + 1): i + 1].sum())
        rec["flow_accel"] = rec["flow_5"] - (rec["flow_15"] - rec["flow_5"]) / 2.0

        # ---- book, canonical semantics, referenced to the CURRENT price -----
        f = didx.get(str(t.day))
        if f:
            if f not in dep_cache:
                dd = pd.read_csv(f)
                dd["ts"] = pd.to_datetime(dd.ts)
                dep_cache[f] = dd
            dep = dep_cache[f]
            now = depth_at(dep, t_dec, px_dec, t.direction)
            at_fill = depth_at(dep, fill, float(t.entry), t.direction)
            for k, v in now.items():
                rec[f"bk_{k}"] = v
            # is the obstacle ahead building or thinning since we got in?
            for k in ("dep_thick", "dep_imb", "dep_sup_m_res"):
                if k in now and k in at_fill:
                    rec[f"chg_{k}"] = now[k] - at_fill[k]
            wa = "dep_wall_above_sz" if t.direction == "long" else "dep_wall_below_sz"
            if wa in now and wa in at_fill:
                rec["chg_wall_ahead_sz"] = now[wa] - at_fill[wa]
        rows.append(rec)
    return pd.DataFrame(rows)


def auc(pos: pd.Series, neg: pd.Series) -> float:
    """P(random positive ranks above random negative). 0.5 = nothing."""
    pos, neg = pos.dropna(), neg.dropna()
    if len(pos) < 8 or len(neg) < 8:
        return np.nan
    r = pd.concat([pos, neg]).rank()
    return float((r[:len(pos)].mean() - (len(pos) + 1) / 2) / len(neg))


def main() -> None:
    C = pd.read_parquet(BOOK)
    taken = C[C["size"] > 0].copy()
    print("loading tape + book ...", flush=True)
    T = build(taken, load_bars(), load_delta(), depth_index())
    if T.empty:
        raise SystemExit("nothing reconstructed")

    # HOLD = ran >=1R further from the decision point. CUT = gave it back / lost.
    T["hold_was_right"] = T.ran_further >= 1.0
    hold, cut = T[T.hold_was_right], T[~T.hold_was_right]
    bkcols = [c for c in T.columns if c.startswith(("bk_", "chg_"))]
    cov = T[bkcols].notna().any(axis=1).mean() * 100 if bkcols else 0.0

    print(f"\n{len(T)} trades reached +1R   |   book snapshot available for {cov:.0f}% of them")
    print(f"  HOLD was right (ran >=1R further) : {len(hold)}")
    print(f"  CUT  was right (gave it back)     : {len(cut)}\n")

    feats = [c for c in T.columns
             if c.startswith(("flow_", "bk_", "chg_")) and T[c].notna().sum() >= 30]
    res = []
    for c in feats:
        a = auc(hold[c], cut[c])
        if not np.isnan(a):
            res.append((c, a, abs(a - 0.5), int(T[c].notna().sum())))
    res.sort(key=lambda r: -r[2])

    print("UNIVARIATE SEPARATION at the +1R decision point")
    print(f"{'feature':<26}{'AUC':>7}{'|edge|':>9}{'n':>6}   direction")
    print("-" * 66)
    for c, a, e, n in res:
        d = "higher => HOLD" if a > 0.5 else "higher => CUT "
        star = "  <<<" if e >= 0.10 else ""
        print(f"{c:<26}{a:>7.2f}{e:>9.2f}{n:>6}   {d}{star}")

    print("\n" + "=" * 66)
    best = [r for r in res if r[2] >= 0.10]
    if not best:
        print("NOTHING clears |AUC-0.5| >= 0.10. On this sample the flow stack does not")
        print("separate hold from cut at +1R — which would mean the discretion case rests")
        print("on something not in this data, not on delta or the level book.")
    else:
        print(f"{len(best)} feature(s) clear |AUC-0.5| >= 0.10:")
        for c, a, e, n in best:
            print(f"  {c:<24} AUC {a:.2f}  (n={n})")
    print("=" * 66)
    print("IN-SAMPLE UNIVARIATE SCREENING ON ~140 TRADES. The 26-Jul bad-PA campaign put 18")
    print("rules through this exact bar and ZERO survived on the full universe across both")
    print("years. Treat every line above as a HYPOTHESIS FOR THE 2023/24 HOLDOUT. Nothing")
    print("here is a finding, and nothing here is a rule.")


if __name__ == "__main__":
    main()
