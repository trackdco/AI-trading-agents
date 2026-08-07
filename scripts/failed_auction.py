#!/usr/bin/env python3
"""Failed auction off the overnight volume profile — run at literal stated defaults.

THE MODEL, exactly as stated in the transcript, with nothing tuned:

  1. Build a volume profile over 18:00 -> 09:30 New York (the GLOBEX session), 70% value area.
     That gives VAH, POC, VAL.
  2. FAILED AUCTION: after the open, price trades ABOVE the value area high and is then rejected
     -- it closes back BELOW the VAH. The breakout attempt failed; sellers stepped in. Short.
     Mirrored at the value area low for longs.
  3. The rejection must be prompt. "Instant close below", no consolidation above -- consolidation
     above VAH is the BREAKOUT case, which is the opposite trade.
  4. Entry confirmation: an inversion (IFVG) on 2/3/4/5m. The transcript is explicit that 1m is
     not used here. Both the raw failing close and the inversion entry are measured.
  5. Stop above the bodies of the excursion. Target the POC first -- "that is your safe level" --
     then the value area low.

WHY THIS ONE IS WORTH A SHOT AFTER SO MANY NEGATIVES. Every trigger tested on this project so
far has been a directional guess at a drawn level. This is an ACCEPTANCE test: price left the
area where business was done, failed to find business outside it, and returned. The target is
not a fixed R multiple, it is the place the volume actually is. If mean reversion to traded
value exists at all, this is its cleanest statement, and the profile is arithmetic rather than
drawn -- two people with the same tape get the same VAH.

METHOD, per the critique that arrived with this model: the FIRST pass does not optimise. Every
number below comes from the stated defaults. If the unoptimised model is not near breakeven net
of realistic costs, there is nothing to search for and searching would only find noise faster.
So no grid, no filter, no selection -- and the MFE before the stop is recorded so that every
possible target is priced from one pass rather than one being chosen and reported as if it had
been chosen first.

    python -m scripts.failed_auction
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
TICK = 0.25
BIN = 1.0                             # profile resolution, NQ points
VA_PCT = 0.70                         # stated: value area volume 70
GLOBEX = (18 * 60, 9 * 60 + 30)       # 18:00 -> 09:30, wraps midnight
RTH = (9 * 60 + 30, 16 * 60)
FVG_TFS = (5, 4, 3, 2)                # stated: 2/3/4/5m for the inversion, NOT 1m
PROMPT_BARS = 30                      # "instant" rejection; beyond this it is acceptance
ENTRY_WAIT = 45                       # bars allowed to find the inversion after the failure
MIN_STOP_PTS = 2.0
MAX_STOP_PTS = 60.0
FRICTION_R = 0.03
FIT0, FIT1 = "2025-06-01", "2026-07-31"


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    sd = pd.to_datetime(b.day).to_numpy()
    b["sday"] = pd.to_datetime(np.where(b.hm.to_numpy() >= 18 * 60,
                                        sd + np.timedelta64(1, "D"), sd)).strftime("%Y-%m-%d")
    return b


def profile(h: np.ndarray, lo: np.ndarray, v: np.ndarray) -> tuple[float, float, float]:
    """POC, VAH, VAL from volume-at-price.

    1m OHLCV has no per-price breakdown, so each bar's volume is spread uniformly across the
    prices it traded through. That is the standard reconstruction and it is an approximation --
    it cannot know where inside the bar the volume actually sat. It is unbiased for the shape of
    a profile built from hundreds of bars, which is what is used here."""
    p0 = np.floor(lo.min() / BIN) * BIN
    p1 = np.ceil(h.max() / BIN) * BIN
    nb = int((p1 - p0) / BIN) + 1
    if nb < 5:
        return float("nan"), float("nan"), float("nan")
    acc = np.zeros(nb)
    i0 = np.floor((lo - p0) / BIN).astype(int)
    i1 = np.floor((h - p0) / BIN).astype(int)
    for a, b_, vol in zip(i0, i1, v):
        acc[a:b_ + 1] += vol / (b_ - a + 1)
    poc = int(acc.argmax())
    tot = acc.sum()
    if tot <= 0:
        return float("nan"), float("nan"), float("nan")
    # expand from the POC toward whichever neighbour holds more volume, until 70% is enclosed
    lo_i = hi_i = poc
    got = acc[poc]
    while got < VA_PCT * tot and (lo_i > 0 or hi_i < nb - 1):
        dn = acc[lo_i - 1] if lo_i > 0 else -1.0
        upv = acc[hi_i + 1] if hi_i < nb - 1 else -1.0
        if upv >= dn:
            hi_i += 1
            got += max(upv, 0.0)
        else:
            lo_i -= 1
            got += max(dn, 0.0)
    return p0 + poc * BIN, p0 + hi_i * BIN, p0 + lo_i * BIN


def tf_fvgs(h: np.ndarray, lo: np.ndarray, tf: int) -> list[dict]:
    n = len(h) // tf * tf
    if n < tf * 3:
        return []
    H = h[:n].reshape(-1, tf).max(1)
    L = lo[:n].reshape(-1, tf).min(1)
    out = []
    for i in range(2, len(H)):
        ready = (i + 1) * tf - 1                  # known only once the third bar CLOSES
        if L[i] > H[i - 2]:
            out.append({"tf": tf, "dir": "bull", "top": float(L[i]),
                        "bottom": float(H[i - 2]), "ready": ready})
        if H[i] < L[i - 2]:
            out.append({"tf": tf, "dir": "bear", "top": float(L[i - 2]),
                        "bottom": float(H[i]), "ready": ready})
    return out


def run_day(g: pd.DataFrame, poc: float, vah: float, val: float) -> list[dict]:
    o = g.open.to_numpy(float)
    h = g.high.to_numpy(float)
    lo = g.low.to_numpy(float)
    c = g.close.to_numpy(float)
    hm = g.hm.to_numpy(int)
    n = len(h)
    if n < 60 or not np.isfinite([poc, vah, val]).all() or vah <= val:
        return []

    gaps = [x for tf in FVG_TFS for x in tf_fvgs(h, lo, tf)]
    gaps.sort(key=lambda x: x["ready"])
    out: list[dict] = []

    for side, lvl, tgt1, tgt2 in (("short", vah, poc, val), ("long", val, poc, vah)):
        # first excursion beyond the value area edge
        beyond = (h > lvl) if side == "short" else (lo < lvl)
        if not beyond.any():
            continue
        b0 = int(np.argmax(beyond))
        # the rejection must be PROMPT -- a close back inside within PROMPT_BARS.
        # A slower return is acceptance outside value, which is the breakout case, not this one.
        fail = None
        ext = h[b0] if side == "short" else lo[b0]
        for u in range(b0, min(b0 + PROMPT_BARS, n - 2)):
            ext = max(ext, h[u]) if side == "short" else min(ext, lo[u])
            if (c[u] < lvl) if side == "short" else (c[u] > lvl):
                fail = u
                break
        if fail is None:
            continue

        for mode in ("close", "inversion"):
            if mode == "close":
                ent_i = fail + 1
                cand_tf = 0
            else:
                want = "bull" if side == "short" else "bear"   # the gap we invert against
                ent_i, cand_tf = None, 0
                for u in range(fail, min(fail + ENTRY_WAIT, n - 2)):
                    ext = max(ext, h[u]) if side == "short" else min(ext, lo[u])
                    vis = [x for x in gaps if x["dir"] == want and b0 - 10 <= x["ready"] <= u]
                    cur = None
                    for tf in FVG_TFS:                        # highest timeframe first
                        m = [x for x in vis if x["tf"] == tf]
                        if m:
                            cur = m[-1]
                            break
                    if cur is None:
                        continue
                    edge = cur["bottom"] if side == "short" else cur["top"]
                    if (c[u] < edge) if side == "short" else (c[u] > edge):
                        ent_i, cand_tf = u + 1, cur["tf"]
                        break
                if ent_i is None:
                    continue
            if ent_i >= n - 2 or hm[ent_i] >= 15 * 60:
                continue

            entry = o[ent_i]
            stop = ext + TICK if side == "short" else ext - TICK
            risk = abs(entry - stop)
            if not (MIN_STOP_PTS <= risk <= MAX_STOP_PTS):
                continue
            if (tgt1 >= entry) if side == "short" else (tgt1 <= entry):
                continue                                       # already through the POC

            r = {"sday": g.sday.iloc[0], "side": side, "mode": mode, "tf": cand_tf,
                 "hm": int(hm[ent_i]), "entry": entry, "stop": stop, "risk": risk,
                 "r_poc": abs(tgt1 - entry) / risk, "r_va": abs(tgt2 - entry) / risk,
                 "window": "AM" if hm[ent_i] < 12 * 60 else "PM"}
            # MFE before the stop, no target in the way -> prices every target at once
            mfe = 0.0
            for u in range(ent_i, n):
                fav = (entry - lo[u]) / risk if side == "short" else (h[u] - entry) / risk
                mfe = max(mfe, fav)
                if (h[u] >= stop) if side == "short" else (lo[u] <= stop):
                    break
            r["mfe"] = mfe
            r["hit_poc"] = mfe >= r["r_poc"]
            r["hit_va"] = mfe >= r["r_va"]
            # stated management: POC is the first target, value-area edge the second
            r["R"] = r["r_poc"] if r["hit_poc"] else -1.0
            r["R_va"] = r["r_va"] if r["hit_va"] else -1.0
            out.append(r)
    return out


def book(x: pd.DataFrame, label: str, col: str = "R") -> None:
    if len(x) < 10:
        print(f"  {label:32} n={len(x):4d}    --")
        return
    R = x[col] - FRICTION_R
    pf = R[R > 0].sum() / max(-R[R < 0].sum(), 1e-9)
    print(f"  {label:32} n={len(x):4d}  win={(R>0).mean():5.1%}  PF={pf:5.2f}  "
          f"E[R]={R.mean():+.3f}  medTgt={x['r_poc'].median():4.2f}R")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="output/failed_auction.csv")
    a = ap.parse_args()

    b = load()
    gx = b[(b.hm >= GLOBEX[0]) | (b.hm < GLOBEX[1])]
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]

    prof = {}
    for d, g in gx.groupby("sday", sort=True):
        if len(g) < 200:
            continue
        prof[d] = profile(g.high.to_numpy(float), g.low.to_numpy(float),
                          g.volume.to_numpy(float))

    rows = []
    for d, g in rth.groupby("day", sort=True):
        if d not in prof:
            continue
        poc, vah, val = prof[d]
        rows += run_day(g.reset_index(drop=True), poc, vah, val)

    T = pd.DataFrame(rows)
    if T.empty:
        print("no trades")
        return 1
    T["fit"] = (T.sday >= FIT0) & (T.sday <= FIT1)
    T.to_csv(ROOT / a.csv, index=False)
    nd = T.sday.nunique()

    print(f"FAILED AUCTION off the 18:00-09:30 profile — {len(T):,} trades, {nd} days, "
          f"{len(T)/nd:.2f}/day.  LITERAL DEFAULTS, NOTHING TUNED.\n")
    print("target = POC (the stated first target, 'your safe level')")
    for mode in ("close", "inversion"):
        for lab, sel in (("fit 2025-06..2026-07", T.fit), ("out-of-fit", ~T.fit)):
            book(T[(T["mode"] == mode) & sel], f"{mode:9} {lab}")
    print("\nsame entries, target = far value-area edge")
    for mode in ("close", "inversion"):
        for lab, sel in (("fit 2025-06..2026-07", T.fit), ("out-of-fit", ~T.fit)):
            book(T[(T["mode"] == mode) & sel], f"{mode:9} {lab}", col="R_va")

    print("\nPAYOFF CURVE — E[R] at every fixed target, from MFE. No target was chosen first.")
    print(f"{'cell':30}{'n':>6}" + "".join(f"{k:>8}" for k in (0.5, 1, 1.5, 2, 3, 4)))
    for mode in ("close", "inversion"):
        for w in ("AM", "PM"):
            for lab, sel in (("fit", T.fit), ("oos", ~T.fit)):
                x = T[(T["mode"] == mode) & (T.window == w) & sel]
                if len(x) < 30:
                    continue
                row = []
                for k in (0.5, 1, 1.5, 2, 3, 4):
                    p = (x.mfe >= k).mean()
                    row.append(p * k - (1 - p) - FRICTION_R)
                print(f"{mode+' '+w+' '+lab:30}{len(x):6d}"
                      + "".join(f"{q:+8.3f}" for q in row)
                      + ("   <--" if max(row) > 0 else ""))
    print(f"\nwrote {a.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
