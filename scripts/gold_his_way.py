#!/usr/bin/env python3
"""HIS STRATEGY, HIS WAY — the spec as stated, with the dollar correlation read as he reads it.

WHY THIS EXISTS. gold_dxy_test.py encoded the dollar filter as a 15-minute RETURN SIGN: "has DX
gone up over the last 15 minutes". That is a momentum reading and it is NOT what he describes. He
reads correlation off a chart POSITIONALLY: if gold is stretched at the top of its range and about
to fail, the dollar should be stretched at the BOTTOM of its own range and about to rally -- the
mirror image setup. That is a different question and it deserves its own test.

Everything invented in this repo is stripped out. No ADX regime gate, no exit sweep, no liquidity
sweep, no R:R gate, no Bollinger buckets. Just his three steps, his session, his target, plus the
correlation confirmation.

HIS SPEC
  1 CONDITION  middle-timeframe range over the last ~5 hours
  2 AREA       trade only the extremes -- sells in the upper portion, buys in the lower
  3 ENTRY      1-min structure shift, enter on the 50% pullback, stop beyond the extreme,
               target back toward the mean of the range
  TIME         second hour of Asia (00-02 UTC)
  CONFIRM      the dollar must show the MIRROR of the gold setup

THE CORRELATION, THREE READINGS. He is a discretionary trader describing a chart, so "DXY is
inversely correlated" admits more than one mechanical encoding. All three are stated up front and
all three are reported; the primary is named before any result was seen.

  PRIMARY  C1  POSITIONAL. DX sits at the mirror extreme of ITS OWN 5h range.
                 gold SELL (gold in the top of its range) -> DX in the BOTTOM of its range
                 gold BUY                                  -> DX in the TOP of its range
           C2  6E POSITIONAL, the same test on the euro. SIGN NOTE: gold and the euro are both
               inverse-dollar so they move TOGETHER -- 6E must sit at the SAME extreme as gold,
               not the opposite one. Getting this backwards inverts the test.
           C3  STRUCTURAL. DX prints the mirrored structure shift itself -- it breaks its recent
               swing HIGH while gold breaks its swing low. The strictest reading.
           C1+C2 both legs of the dollar agreeing.

  All windows end STRICTLY BEFORE the fill bar. Nothing at or after the fill is read.

  ALREADY DEAD, not retested here: the momentum reading (DX 15m return sign) at gap -0.271,
  p=0.7636, with a deliberately-stale placebo scoring BETTER (+0.368, p=0.0677). That placebo is
  why this script reports a placebo for every confluence it tests.

TARGETS. He says both "target back toward the mean" and "80%+ at 1-1.5R", so all three are shown.

HONESTY. This is another pass over the same 488 trades in one bull regime. A positive here is a
candidate for GC 2021-22, not a result. Every confluence gets a stale-window placebo precisely
because the last one that looked good was noise.

    python3 scripts/gold_his_way.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(HERE, "scripts", "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

rng = np.random.default_rng(103)
H, L, C, TS = grt.H, grt.L, grt.C, grt.TS
SL, PB, SPLIT, EXT = grt.SHIFT_LOOK, grt.PULLBACK, grt.SPLIT, grt.EXT_ZONE
RANGE_H = 5.0                 # his "4-5 hours", as a TIME window (these instruments have gaps)
SHIFT_MIN = 20                # his structure-shift lookback, in minutes
PLACEBO_MIN = 60              # every confluence gets a stale-window twin
NPERM = 20000


class Ref:
    """Time-sliced range/structure reads on a reference instrument."""

    def __init__(self, path, name):
        d = pd.read_parquet(path).sort_values("ts").reset_index(drop=True)
        self.name = name
        self.ts = d.ts.values.astype("datetime64[ns]")
        self.h, self.l, self.c = (d.high.values.astype(float), d.low.values.astype(float),
                                  d.close.values.astype(float))
        print(f"  {name}: {len(d):,} bars")

    def _slice(self, t0, t1):
        a = int(np.searchsorted(self.ts, np.datetime64(t0, "ns"), side="left"))
        b = int(np.searchsorted(self.ts, np.datetime64(t1, "ns"), side="left"))
        return a, b

    def pos_in_range(self, when, hours=RANGE_H, min_bars=60):
        """Where does the last price sit inside its own N-hour range? 0=low, 1=high."""
        t1 = pd.Timestamp(when)
        a, b = self._slice(t1 - pd.Timedelta(hours=hours), t1)
        if b - a < min_bars:
            return np.nan
        hi, lo = self.h[a:b].max(), self.l[a:b].min()
        if not np.isfinite(hi) or hi <= lo:
            return np.nan
        return (self.c[b - 1] - lo) / (hi - lo)

    def shift_dir(self, when, minutes=SHIFT_MIN, min_bars=8):
        """+1 if it just broke its recent swing HIGH, -1 if the swing LOW, else 0."""
        t1 = pd.Timestamp(when)
        a, b = self._slice(t1 - pd.Timedelta(minutes=minutes), t1)
        if b - a < min_bars:
            return np.nan
        last = self.c[b - 1]
        hi, lo = self.h[a:b - 1].max(), self.l[a:b - 1].min()
        if not np.isfinite(hi):
            return np.nan
        if last > hi:
            return 1.0
        if last < lo:
            return -1.0
        return 0.0


print("load reference instruments ...", flush=True)
DX = Ref(os.path.join(HERE, "data/reference/dx_1m_master.parquet"), "DX")
E6 = Ref(os.path.join(HERE, "data/reference/6e_1m_master.parquet"), "6E")


def book(target_mode, r_mult):
    """His setup, one target convention, with the dollar reads attached."""
    rows = []
    for (i, d, sp, rh, rl) in grt.signals({0, 1}):
        r = grt.resolve(i, d, sp, rh, rl, r_mult, target_mode, "pullback")
        if not r:
            continue
        k = int(r["i"])
        when = pd.Timestamp(TS[k])                       # fill bar
        pre = when - pd.Timedelta(minutes=1)             # strictly before it
        stale = pre - pd.Timedelta(minutes=PLACEBO_MIN)  # the placebo window
        dxp, e6p = DX.pos_in_range(pre), E6.pos_in_range(pre)
        dxs = DX.shift_dir(pre)
        dxp_s = DX.pos_in_range(stale)
        # C1 DX at the MIRROR extreme of its own range
        c1 = (np.nan if not np.isfinite(dxp) else
              float(dxp <= 1 - EXT if d < 0 else dxp >= EXT))
        # C2 6E at the SAME extreme as gold (both inverse-dollar -> they move together)
        c2 = (np.nan if not np.isfinite(e6p) else
              float(e6p >= EXT if d < 0 else e6p <= 1 - EXT))
        # C3 DX prints the mirrored structure shift
        c3 = (np.nan if not np.isfinite(dxs) else float(dxs == -d))
        # placebo twin of C1
        cp = (np.nan if not np.isfinite(dxp_s) else
              float(dxp_s <= 1 - EXT if d < 0 else dxp_s >= EXT))
        rows.append(dict(R=r["R"], net=r["net"], day=r["day"], d=d, win=r["R"] > 0,
                         C1=c1, C2=c2, C3=c3, C1_placebo=cp,
                         C1C2=(np.nan if not (np.isfinite(c1) and np.isfinite(c2))
                               else float(c1 == 1 and c2 == 1))))
    D = pd.DataFrame(rows)
    D["train"] = D.day < SPLIT
    return D


def line(sub, lab):
    if len(sub) < 10:
        print(f"    {lab:34s} n={len(sub):4d}   (too few)"); return
    print(f"    {lab:34s} n={len(sub):4d}  WR {100*sub.win.mean():3.0f}%  "
          f"E[R] {sub.R.mean():+.3f}  net ${sub.net.sum():+8,.0f}")


def gap_p(s, col):
    f = s[col].values == 1.0
    if f.sum() < 10 or (~f).sum() < 10:
        return np.nan, np.nan
    ud, inv = np.unique(s.day.values, return_inverse=True)
    dm = s.groupby("day").R.mean().values
    resid = s.R.values - dm[inv]
    obs = s.R.values[f].mean() - s.R.values[~f].mean()
    cnt = sum(1 for _ in range(NPERM)
              if (lambda Rp: Rp[f].mean() - Rp[~f].mean() >= obs)(
                  resid + dm[rng.permutation(len(ud))][inv]))
    return obs, (cnt + 1) / (NPERM + 1)


def confluence(D, col, title):
    s = D.dropna(subset=[col])
    if not len(s):
        print(f"\n  {title}\n    (not evaluable)"); return
    print(f"\n  {title}")
    line(s[s[col] == 1], "CONFIRMED")
    line(s[s[col] == 0], "not confirmed")
    g, p = gap_p(s, col)
    if np.isfinite(g):
        a, b_ = s[s[col] == 1], s[s[col] == 0]
        print(f"      gap {g:+.3f} R/trade   WR gap {100*(a.win.mean()-b_.win.mean()):+.1f}pp   "
              f"perm p = {p:.4f}")
        for tr_, nm in ((True, "train"), (False, "TEST ")):
            t = s[s.train == tr_]
            if len(t[t[col] == 1]) >= 10 and len(t[t[col] == 0]) >= 10:
                print(f"      {nm}  conf {t[t[col]==1].R.mean():+.3f}  "
                      f"unconf {t[t[col]==0].R.mean():+.3f}  "
                      f"gap {t[t[col]==1].R.mean()-t[t[col]==0].R.mean():+.3f}")


if __name__ == "__main__":
    for tm, rm, lbl in (("mean", 0, "TARGET = mean of the range (his '50% back')"),
                        ("R", 1.0, "TARGET = 1R (his '80%+ win rate' claim)"),
                        ("R", 1.5, "TARGET = 1.5R")):
        D = book(tm, rm)
        print("\n" + "=" * 98)
        print(f"{lbl}")
        print("=" * 98)
        line(D, "HIS SETUP, no confluence")
        line(D[D.train], "  train")
        line(D[~D.train], "  TEST")
        print(f"\n  dollar reads available: C1 {D.C1.notna().sum()}  C2 {D.C2.notna().sum()}  "
              f"C3 {D.C3.notna().sum()}  of {len(D)}")
        confluence(D, "C1", "PRIMARY C1 — DX at the MIRROR extreme of its own 5h range")
        confluence(D, "C2", "C2 — 6E at the SAME extreme as gold (both inverse-dollar)")
        confluence(D, "C3", "C3 — DX prints the mirrored structure shift")
        confluence(D, "C1C2", "C1+C2 — both dollar legs agree")
        confluence(D, "C1_placebo",
                   f"PLACEBO — C1 read {PLACEBO_MIN}m stale (must be null if C1 is real)")

    # ---------------------------------------------------------------- decisive falsifier
    print("\n" + "=" * 98)
    print("FALSIFIER — RANDOM-DAY DX PAIRING (the attack that matters)")
    print("=" * 98)
    print("  Every gold signal keeps its TIME OF DAY but is paired with DX's range position from")
    print("  a RANDOM OTHER DAY. This preserves the gold book exactly, preserves DX's own")
    print("  distribution exactly, and destroys ONLY the real-time correspondence between them.")
    print("  If the gap survives that, the confluence is not about the dollar at all.")

    # precompute DX range position for every minute of the Asia window, by day
    grid = {}
    gts = pd.to_datetime(pd.Series(DX.ts))
    for dayv, sub in gts.groupby(gts.dt.strftime("%Y-%m-%d")):
        s = sub[sub.dt.hour.isin([0, 1, 2])]
        for t in s:
            v = DX.pos_in_range(t)
            if np.isfinite(v):
                grid.setdefault(t.strftime("%H:%M"), []).append(v)
    print(f"  DX range-position grid: {sum(len(v) for v in grid.values()):,} readings "
          f"across {len(grid)} minute-of-day slots")

    for tm, rm, lbl in (("R", 1.0, "1R"), ("R", 1.5, "1.5R")):
        D = book(tm, rm)
        s = D.dropna(subset=["C1"])
        obs = s[s.C1 == 1].R.mean() - s[s.C1 == 0].R.mean()
        # rebuild minute-of-day per trade
        mods = []
        for (i, d, sp, rh, rl) in grt.signals({0, 1}):
            r = grt.resolve(i, d, sp, rh, rl, rm, tm, "pullback")
            if r:
                mods.append(pd.Timestamp(TS[int(r["i"])]).strftime("%H:%M"))
        mods = np.array(mods)[s.index.values] if len(mods) == len(D) else None
        if mods is None:
            print(f"  {lbl}: could not align minute-of-day, skipping")
            continue
        Rv, dv = s.R.values, s.d.values
        cnt, ndraw = 0, 2000
        for _ in range(ndraw):
            fake = np.empty(len(s))
            for j, md in enumerate(mods):
                pool = grid.get(md)
                fake[j] = pool[rng.integers(len(pool))] if pool else np.nan
            ok = np.isfinite(fake)
            c = np.where(dv[ok] < 0, fake[ok] <= 1 - EXT, fake[ok] >= EXT)
            if c.sum() < 10 or (~c).sum() < 10:
                continue
            if Rv[ok][c].mean() - Rv[ok][~c].mean() >= obs:
                cnt += 1
        print(f"  {lbl}  observed C1 gap {obs:+.3f}   random-day-DX null p = "
              f"{(cnt+1)/(ndraw+1):.4f}   ({ndraw} draws)")

    print("\n" + "=" * 98)
    print("READING THIS")
    print("=" * 98)
    print("  His claim is 80%+ win rate at 1-1.5R, lifted to ~83% by the dollar. The win-rate")
    print("  columns above are the direct test of that claim, not the E[R] columns.")
    print("  A confluence is only interesting if its gap beats its own PLACEBO. The momentum")
    print("  encoding failed exactly there, and it is the cheapest way to catch a fluke.")
