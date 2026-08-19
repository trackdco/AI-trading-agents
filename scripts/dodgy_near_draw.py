#!/usr/bin/env python3
"""The near draw set — L1 equal highs/lows and L9 intermediate-term — on 08:30-11:00.

`FINDINGS-dodgy-structural-target.md` closed with this as the bound on its own result:
the draw set held prior-day, prior-week, completed Asia/London and the last confirmed
swing, but NOT the two level types he weights most. Building them is the only route by
which the structural target could be argued to have been tested unfairly.

Restricted to 08:30-11:00 ET entries per the operator's instruction. That is 9,802 of
85,277 signals; every unrestricted number in this stream carried 88.5% of its weight in
hours he tells students to avoid, so the window is the population he actually trades.

FOUR THINGS, one pass:

1. SYNTHETIC-TARGET CONTAMINATION. `signals()` falls back to a manufactured 1R "target"
   when no confirmed swing survives ahead of price. That fallback is 28.0% of the
   in-window book, and `dodgy_structural_target.py` fed it into the draw set as if it
   were a level. So the published structural arm was part fixed-1R in disguise. Priced
   here, both ways.

2. THE NEAR DRAW SET.
   L1  equal highs/lows: confirmed k=3 pivots clustered within `tol`, >= `min_touch`
       members, level = cluster extreme (where the stops sit). tol and lookback are his
       unstated free parameters, so both are swept and every cell is reported.
   L9  intermediate-term: a short-term pivot with LOWER short-term pivots on both sides
       (higher, for lows). Confirmed only when the right-hand neighbour confirms.
   Both are as-of: a pivot is unknown until i+PIVOT_K and dead once swept.

3. E5 RULE 4 as a REJECTING filter -- "we haven't already taken out those highs". The
   predicate exists in the incumbent harness and is used backwards: when no unswept
   target is left it manufactures one and keeps the trade. Here the trade is dropped,
   and the exit stays the incumbent fixed 2R so this reads as a filter, not an exit.

4. THE L1 PROBABILITY LADDER -- 2 wicks ~50%, 3+ 89%, 4+ 90-95%. A base rate needing no
   entry model, and the one claim in the lecture that can CONFIRM rather than only fail.
   Single unclustered pivots are the control: his ladder must rise above them, and it
   must survive stratifying on distance, because a further level is a rarer one.

LAW 2 throughout: a structural target sets reward from the same geometry as risk, so
dollars are printed beside R on every row.

    .venv/bin/python scripts/dodgy_near_draw.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import COST_PTS, PIVOT_K, report
from scripts.dodgy_structural_target import (
    HI_COLS,
    LO_COLS,
    PT,
    draw_levels,
)
from src.research.tomtrades import autopsy as AU

WIN = (510, 660)                 # 08:30-11:00 ET, minutes past midnight
LOOKBACK = 4320                  # ~3 session days of 1m bars for cluster membership
TOLS = (0.25, 2.0, 5.0)          # "to the tick" .. loose; his rule states none
MIN_TOUCH = 2


# ---------------------------------------------------------------- primitives
def next_greater(a: np.ndarray) -> np.ndarray:
    """first j>p with a[j] > a[p], else len(a). Monotonic stack, O(n).

    For a pivot high this IS its sweep bar, which is what makes 'unswept as of bar i'
    an O(1) test instead of a range-max scan per query.
    """
    n = len(a)
    out = np.full(n, n, dtype=np.int64)
    st = np.empty(n, dtype=np.int64)
    top = 0
    for j in range(n):
        x = a[j]
        while top and x > a[st[top - 1]]:
            top -= 1
            out[st[top]] = j
        st[top] = j
        top += 1
    return out


def pivots(a: np.ndarray, hi: bool, k: int = PIVOT_K) -> np.ndarray:
    """k-bar fractal indices; k=3 is the incumbent detector's own condition.

    k is the SCALE OF THE CLAIM. He draws equal highs on swings that are obvious from
    ten feet away; a 3-bar fractal on 1m data is a 4-point wiggle. Testing his ladder
    only at k=3 would answer a question he never asked.
    """
    s = pd.Series(a)
    w = 2 * k + 1
    ext = (s.rolling(w, center=True).max() if hi else s.rolling(w, center=True).min())
    m = (s >= ext) if hi else (s <= ext)
    m.iloc[:k] = False
    m.iloc[len(s) - k:] = False
    return np.flatnonzero(m.to_numpy())


class Side:
    """Per-side geometry that does not depend on the clustering tolerance."""

    def __init__(self, px: np.ndarray, hi: bool, k: int = PIVOT_K):
        self.px, self.hi, self.k = px, hi, k
        self.idx = pivots(px, hi, k)
        self.val = px[self.idx]
        self.conf = self.idx + k
        sw = next_greater(px if hi else -px)
        self.sweep = sw[self.idx]


class Pool:
    """One side's confirmed-pivot book, with L1 clusters and L9 flags precomputed."""

    def __init__(self, side: Side, tol: float):
        hi = self.hi = side.hi
        self.tol = tol
        self.idx, self.val = side.idx, side.val
        self.conf, self.sweep = side.conf, side.sweep

        # --- L9: lower short-term pivots on both sides (higher, for lows).
        # Confirmed when the RIGHT neighbour confirms, not when the pivot forms.
        v = self.val
        m = np.zeros(len(v), dtype=bool)
        if len(v) > 2:
            inner = (v[1:-1] > v[:-2]) & (v[1:-1] > v[2:]) if hi else \
                    (v[1:-1] < v[:-2]) & (v[1:-1] < v[2:])
            m[1:-1] = inner
        self.itl = m
        self.itl_conf = np.where(m, np.roll(self.conf, -1), np.iinfo(np.int64).max)

        # --- L1: cluster each pivot with earlier UNSWEPT pivots within tol.
        # Size counts the members alive when the newest one lands; the level is the
        # cluster extreme, because that is the price the stops sit beyond, and the
        # cluster dies when THAT price is taken -- not when its newest member is.
        n = len(v)
        size = np.ones(n, dtype=np.int64)
        lvl = v.copy()
        csweep = self.sweep.copy()
        sgn = 1 if hi else -1
        for k in range(n):
            p = self.idx[k]
            lo = np.searchsorted(self.idx, p - LOOKBACK)
            if k <= lo:
                continue
            live = (self.sweep[lo:k] > p) & (np.abs(self.val[lo:k] - v[k]) <= tol)
            if not live.any():
                continue
            mem = np.flatnonzero(live) + lo
            mem = np.append(mem, k)                  # members, newest included
            q = mem[np.argmax(self.val[mem] * sgn)]  # the one holding the extreme
            size[k] = len(mem)
            lvl[k] = self.val[q]
            csweep[k] = self.sweep[q]                # every member is unswept at p,
        self.csize, self.clvl, self.csweep = size, lvl, csweep   # so this is > p

    def _ahead(self, mask: np.ndarray, vals: np.ndarray, price: float) -> float:
        good = mask & ((vals > price) if self.hi else (vals < price))
        if not good.any():
            return np.nan
        v = vals[good]
        return float(v.min() if self.hi else v.max())

    def nearest(self, i: int, price: float, kind: str, min_touch: int = MIN_TOUCH) -> float:
        k = np.searchsorted(self.conf, i, "right")           # confirmed as of bar i
        lo = np.searchsorted(self.idx, i - LOOKBACK)
        if k <= lo:
            return np.nan
        s = slice(lo, k)
        if kind == "swing":
            return self._ahead(self.sweep[s] > i, self.val[s], price)
        if kind.startswith("eqh"):
            mt = int(kind[3:]) if len(kind) > 3 else min_touch
            m = (self.csweep[s] > i) & (self.csize[s] >= mt)
            return self._ahead(m, self.clvl[s], price)
        if kind == "itl":
            m = (self.sweep[s] > i) & self.itl[s] & (self.itl_conf[s] <= i)
            return self._ahead(m, self.val[s], price)
        raise ValueError(kind)


# ---------------------------------------------------------------- attach + sim
def attach(sig: pd.DataFrame, bars: pd.DataFrame, lv: pd.DataFrame,
           ph: Pool, pl: Pool, kinds: tuple[str, ...]) -> pd.DataFrame:
    """Nearest unswept level ahead, drawn from `kinds` plus the coarse session boxes.

    'coarse' is the old draw set MINUS the synthetic t1. Nothing here can return a
    manufactured level: every candidate is a price the market actually printed.
    """
    hi, lo = lv[HI_COLS].to_numpy(), lv[LO_COLS].to_numpy()
    c = bars["close"].to_numpy()
    tgt, nm = [], []
    for r in sig.itertuples(index=False):
        i, d = int(r.i), int(r.direction)
        px = c[i]
        cand: list[tuple[float, str]] = []
        if "coarse" in kinds:
            arr, cols = (hi[i], HI_COLS) if d > 0 else (lo[i], LO_COLS)
            cand += [(float(v), cols[k]) for k, v in enumerate(arr) if np.isfinite(v)]
        pool = ph if d > 0 else pl
        for k in kinds:
            if k == "coarse":
                continue
            v = pool.nearest(i, px, k)
            if np.isfinite(v):
                cand.append((v, k))
        ahead = [(v, n) for v, n in cand if (v > px if d > 0 else v < px)]
        if ahead:
            v, n = min(ahead, key=lambda x: abs(x[0] - px))
            tgt.append(v); nm.append(n)
        else:
            tgt.append(np.nan); nm.append("")
    out = sig.copy()
    out["struct_t"], out["struct_name"] = tgt, nm
    return out


def simulate(bars: pd.DataFrame, sig: pd.DataFrame, mode: str,
             max_hold: int = 240) -> pd.DataFrame:
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(bars)
    out = []
    for r in sig.itertuples(index=False):
        i0 = int(r.i) + 1
        if i0 >= n:
            continue
        entry, d, stop = o[i0], int(r.direction), float(r.stop)
        risk = abs(entry - stop)
        if risk < 2.0:
            continue
        if mode == "fixed2r":
            final = entry + d * 2.0 * risk
        else:
            if not np.isfinite(r.struct_t) or (float(r.struct_t) - entry) * d <= 0:
                continue
            final = float(r.struct_t)
        rr = abs(final - entry) / risk
        px, why = np.nan, "timeout"
        for j in range(i0, min(i0 + max_hold, n)):
            if (h[j] >= stop) if d < 0 else (l_[j] <= stop):
                px, why = stop, "stop"; break
            if (l_[j] <= final) if d < 0 else (h[j] >= final):
                px, why = final, "target"; break
        else:
            px = c[min(i0 + max_hold, n) - 1]
        g = d * (px - entry)
        out.append({"sid": int(r.sid), "sess_day": r.sess_day, "risk": risk, "rr": rr,
                    "out": g / risk - COST_PTS / risk, "usd": (g - COST_PTS) * PT,
                    "reason": why})
    t = pd.DataFrame(out)
    if not t.empty:
        t["win"] = (t["out"] > 0).astype(float)
    return t


def row(t: pd.DataFrame, label: str) -> dict:
    r = report(t, label)
    if "ev" not in r:
        return r
    lo, hi = AU.dboot_mean(t.assign(out=t.usd), "out")
    r |= {"med_stop": t.risk.median(), "med_rr": t.rr.median(), "usd": t.usd.mean(),
          "usd_lo": lo, "usd_hi": hi, "usd_day": t.usd.sum() / t.sess_day.nunique()}
    return r


def show(res: list[dict], title: str) -> pd.DataFrame:
    d = pd.DataFrame([r for r in res if "ev" in r])
    if d.empty:
        return d
    d["ci"] = d.apply(lambda r: f"[{r.lo:+.3f},{r.hi:+.3f}]", axis=1)
    d["eras"] = np.where(d.both, "BOTH", "-")
    print(f"\n=== {title} ===")
    print(d[["variant", "n", "per_day", "win_pct", "ev", "ci", "h1", "h2", "eras"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(d[["variant", "n", "med_stop", "med_rr", "usd", "usd_day"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    return d


# ---------------------------------------------------------------- L1 ladder
def ladder(side: Side, tol: float, horizons=(390, 1380, 6900)):
    """His probability ladder, as a pure base rate: does a cluster of N wicks get taken?

    Control is the SINGLE unclustered pivot, size 1. The claim is a rising ladder --
    ~50% at two wicks, 89% at three, 90-95% at four -- so size 1 must sit below size 2,
    and each step must rise. Distance is reported and stratified because a further
    level is mechanically a rarer one, and an unstratified ladder would just be
    measuring how far away each bucket sits.
    """
    P, px, hi = Pool(side, tol), side.px, side.hi
    n = len(px)
    d = pd.DataFrame({"conf": P.conf, "sweep": P.csweep, "size": P.csize,
                      "lvl": P.clvl, "px_at": px[np.minimum(P.conf, n - 1)]})
    d["dist"] = (d.lvl - d.px_at).abs()
    d["bucket"] = np.where(d["size"] >= 4, "4+", d["size"].astype(str))
    out = []
    for h in horizons:
        d[f"hit{h}"] = (d.sweep - d.conf) <= h
        g = d.groupby("bucket", observed=True).agg(
            n=("size", "size"), hit=(f"hit{h}", "mean"), med_dist=("dist", "median"))
        for b, r in g.iterrows():
            out.append({"side": "high" if hi else "low", "tol": tol, "horizon_bars": h,
                        "wicks": b, "n": int(r.n), "hit_pct": 100 * r.hit,
                        "med_dist_pt": r.med_dist})
    # distance-stratified at the middle horizon, to kill the "further = rarer" read
    d["dq"] = pd.qcut(d.dist, 3, labels=["near", "mid", "far"], duplicates="drop")
    strat = (d.groupby(["dq", "bucket"], observed=True)
               .agg(n=("size", "size"), hit=("hit1380", "mean")).reset_index())
    strat["hit_pct"] = 100 * strat.hit
    return pd.DataFrame(out), strat


def main() -> None:
    bars = pd.read_parquet(ROOT / "output/_nq_bars.parquet")
    sig = pd.read_parquet(ROOT / "output/_nq_sig.parquet")
    sig["sid"] = np.arange(len(sig))
    ts = pd.DatetimeIndex(sig.ts)
    m = ts.hour * 60 + ts.minute
    win = (m >= WIN[0]) & (m < WIN[1])
    sw = sig[win].reset_index(drop=True)
    print(f"NQ {len(bars):,} bars · {len(sig):,} signals · "
          f"{len(sw):,} in 08:30-11:00 ({100 * win.mean():.1f}%)", flush=True)
    print(f"synthetic t1 (no unswept swing ahead): {100 * sw.t1_synth.mean():.1f}% in-window",
          flush=True)

    lv = draw_levels(bars)
    h, l_ = bars["high"].to_numpy(), bars["low"].to_numpy()
    SH, SL = Side(h, True), Side(l_, False)
    print(f"pivots k=3: {len(SH.idx):,} highs · {len(SL.idx):,} lows", flush=True)

    res = [row(simulate(bars, sw, "fixed2r"), "fixed 2R (incumbent)")]

    # --- the PUBLISHED structural arm, reproduced in-window, synthetics included
    old = attach(sw, bars, lv, None, None, ("coarse",))
    c = bars["close"].to_numpy()[sw.i.to_numpy()]
    t1, d_ = sw.t1.to_numpy(), sw.direction.to_numpy()
    ahead = np.where((t1 - c) * d_ > 0, t1, np.nan)
    cur = old.struct_t.to_numpy()
    better = np.isfinite(ahead) & (~np.isfinite(cur) | (np.abs(ahead - c) < np.abs(cur - c)))
    old.loc[better, "struct_t"] = ahead[better]
    old.loc[better, "struct_name"] = np.where(sw.t1_synth.to_numpy()[better], "SYNTH", "swing")
    res.append(row(simulate(bars, old, "structural"), "structural · PUBLISHED set"))
    print(f"\npublished draw set: {100 * (old.struct_name == 'SYNTH').mean():.1f}% of its "
          f"targets are the manufactured 1R, not a level", flush=True)

    # --- EXCLUSIVE draw sets. Additive ones cannot work and that is arithmetic, not
    # an empirical result: an equal-highs level is the MAX of a pivot cluster and an
    # intermediate-term high IS a pivot high, so under "nearest level ahead" the
    # nearest raw swing dominates both and the extra columns are unreachable.
    ARMS = (("coarse", "swing"), ("swing",), ("coarse",),
            ("eqh",), ("eqh3",), ("itl",), ("coarse", "eqh", "itl"))
    LABEL = {("coarse", "swing"): "coarse+swing (synth removed)",
             ("swing",): "swing only", ("coarse",): "session boxes only",
             ("eqh",): "L1 equal highs only (>=2)", ("eqh3",): "L1 equal highs only (>=3)",
             ("itl",): "L9 intermediate-term only",
             ("coarse", "eqh", "itl"): "HIS set: boxes+L1+L9, no raw swing"}
    for tol in TOLS:
        ph, pl = Pool(SH, tol), Pool(SL, tol)
        for kinds in ARMS:
            if kinds in (("coarse", "swing"), ("swing",), ("coarse",)) and tol != TOLS[0]:
                continue                      # tol-independent, do not print three times
            a = attach(sw, bars, lv, ph, pl, kinds)
            tag = "" if kinds in (("coarse", "swing"), ("swing",), ("coarse",)) else f"tol={tol:g} · "
            res.append(row(simulate(bars, a, "structural"), tag + LABEL[kinds]))
            if kinds == ("coarse", "eqh", "itl"):
                cov = 100 * np.isfinite(a.struct_t.to_numpy()).mean()
                print(f"  tol={tol:g} · his set covers {cov:.1f}% of signals · mix: "
                      + ", ".join(f"{k}={100 * v:.0f}%" for k, v in
                                  a.struct_name.value_counts(normalize=True).head(5).items()),
                      flush=True)
                # --- E5 rule 4 as a REJECTING filter, incumbent fixed-2R exit
                ok = np.isfinite(a.struct_t.to_numpy())
                res.append(row(simulate(bars, sw[ok], "fixed2r"),
                               f"tol={tol:g} · E5r4 KEEP · fixed 2R"))
                res.append(row(simulate(bars, sw[~ok], "fixed2r"),
                               f"tol={tol:g} · E5r4 REJECT · fixed 2R"))

    d = show(res, "08:30-11:00 · exclusive draw sets, incumbent exit as control")
    d.to_csv(ROOT / "output/dodgy_near_draw.csv", index=False)

    # --- the L1 ladder, at three scales, because the scale IS the claim
    print("\n=== L1 PROBABILITY LADDER (base rate, no entry model) ===")
    print("claimed: 2 adjacent ~50% · 2 apart 70-80% · 3+ 89% · 4+ 90-95%")
    lad, strat = [], []
    for k in (3, 15, 30):
        sh, sl = (SH, SL) if k == 3 else (Side(h, True, k), Side(l_, False, k))
        for tol in TOLS:
            for side in (sh, sl):
                a, b = ladder(side, tol)
                a["k"] = k; lad.append(a)
                b["tol"], b["k"] = tol, k
                b["side"] = "high" if side.hi else "low"
                strat.append(b)
    L = pd.concat(lad, ignore_index=True)
    print(L.pivot_table(index=["k", "tol", "wicks"], columns=["side", "horizon_bars"],
                        values="hit_pct").to_string(float_format=lambda v: f"{v:.1f}"))
    print("\nn and median distance to the level, 1-day horizon:")
    print(L[(L.horizon_bars == 1380) & (L.side == "high")]
          [["k", "tol", "wicks", "n", "med_dist_pt"]]
          .to_string(index=False, float_format=lambda v: f"{v:.1f}"))
    S = pd.concat(strat, ignore_index=True)
    print("\nDISTANCE-STRATIFIED, highs, 1-day horizon (hit%) -- this is the control that")
    print("matters: more wicks also means a NEARER level, and nearer levels get hit more.")
    print(S[S.side == "high"].pivot_table(index=["k", "tol", "bucket"], columns="dq",
                                          values="hit_pct", observed=True)
          .to_string(float_format=lambda v: f"{v:.1f}"))
    L.to_csv(ROOT / "output/dodgy_l1_ladder.csv", index=False)
    S.to_csv(ROOT / "output/dodgy_l1_ladder_strat.csv", index=False)
    print(f"\nwrote {ROOT / 'output/dodgy_near_draw.csv'}, dodgy_l1_ladder*.csv")


if __name__ == "__main__":
    main()
