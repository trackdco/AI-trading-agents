#!/usr/bin/env python3
"""LEAK DAMAGE — canon depth lookahead (ANGUS 2026-08-06).

condense_depth.py keeps the LAST book state within each minute but stamps it with
the minute's START, so the snapshot labelled 10:15 is the book at ~10:15:59.
features.py:depth_at then selects `dep.ts <= minute`, so a fill at 10:15:00 reads
the 10:15:59 book — up to 60s of future. Live cannot do this.

HONEST read = `dep.ts < minute`: the snapshot stamped 10:14, i.e. the book at
10:14:59 — the last state genuinely available one second before the fill.

Depth is load-bearing in FOUR places, so this measures all of them:
  W       pre-market HARD gate (pre_wall_behind)
  D       gold HARD gate (gold_no_wall_ahead) AND a 2x-weighted score bit
  WALLSZ  gold admission gate (funded_book.load_book)
  dep_wall_below_d >= 2.75   gold admission gate (same)

    python -m scripts.leak_damage_canon
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.score_canon_span import depth_file  # noqa: E402

NY = "America/New_York"
DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026", "data/reference/depth_2023_24"]
Q_WALLSZ_MIN = 7.0


def depth_at_mode(dep: pd.DataFrame, minute: pd.Timestamp, entry: float,
                  direction: str, strict: bool) -> dict:
    """src/canon/features.py::depth_at, with the snapshot selector switchable.
    strict=False reproduces the shipped (leaky) `<=`; strict=True is the honest `<`."""
    sub = dep[dep.ts < minute] if strict else dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1)}
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    return f


def recompute(V: pd.DataFrame, strict: bool) -> pd.DataFrame:
    """Recompute the depth family for every row under one snapshot rule."""
    out, cache = [], {}
    for day, g in V.groupby(V.fill.dt.strftime("%Y-%m-%d"), sort=False):
        if day not in cache:
            f = depth_file(DEPTH_DIRS, day)
            if f is None:
                cache[day] = None
            else:
                dd = pd.read_csv(f)
                dd["ts"] = pd.to_datetime(dd.ts)
                cache[day] = dd
        dep = cache[day]
        for i, t in g.iterrows():
            r = {"_i": i}
            if dep is not None:
                r.update(depth_at_mode(dep, t.fill, float(t.entry), t.direction, strict))
            out.append(r)
    return pd.DataFrame(out).set_index("_i").reindex(V.index)


def gates(V: pd.DataFrame, D: pd.DataFrame) -> pd.DataFrame:
    """W / D / WALLSZ / gold-admission from a depth family (scorer_ny.checks form)."""
    long = V.direction.eq("long")
    thick = D.dep_thick
    below_d = D.get("dep_wall_below_d", pd.Series(np.nan, index=D.index))
    above_d = D.get("dep_wall_above_d", pd.Series(np.nan, index=D.index))
    above_sz = D.get("dep_wall_above_sz", pd.Series(np.nan, index=D.index))
    below_sz = D.get("dep_wall_below_sz", pd.Series(np.nan, index=D.index))
    behind_d = below_d.where(long, above_d)
    ahead_d = above_d.where(long, below_d)
    ahead_sz = above_sz.where(long, below_sz)
    R = pd.DataFrame(index=V.index)
    R["W"] = np.where(thick.isna(), np.nan, behind_d.isna().astype(float))
    R["D"] = np.where(thick.isna(), np.nan, ahead_d.notna().astype(float))
    R["WALLSZ"] = ((R.D == 1) & (ahead_sz >= Q_WALLSZ_MIN)).astype(float)
    R["below_d"] = below_d
    return R


def main() -> None:
    # FULL candidate population, not just S.valid — `valid` is itself the survivor set of
    # the LEAKY gates, so filtering on it hides candidates the leaky read rejected but an
    # honest read would admit. Every refusal in this book is depth-driven
    # (gold_no_wall_ahead / pre_wall_behind) and every refused row carries its outcome,
    # so the honest book is fully measurable off the same rows.
    frames = []
    for span in ("fit", "holdout"):
        S = pd.read_parquet(ROOT / f"output/aikido_{span}.parquet")
        S = S.copy()
        S["span"] = span
        frames.append(S)
    V = pd.concat(frames, ignore_index=True)
    V["fill"] = pd.to_datetime(V.fill_ts, format="mixed", utc=True).dt.tz_convert(NY)
    print(f"candidates: {len(V)} ({(V.sess=='gold').sum()} gold, "
          f"{(V.sess=='pre').sum()} pre) | shipped-valid {int(V.valid.sum())}\n", flush=True)

    print("recomputing depth family both ways...", flush=True)
    D_leak = recompute(V, strict=False)
    D_hon = recompute(V, strict=True)

    # sanity: the leaky recompute must reproduce the shipped book
    shipped = V.WALLSZ.fillna(-1).to_numpy()
    repro = gates(V, D_leak).WALLSZ.fillna(-1).to_numpy()
    agree = (shipped == repro).mean()
    print(f"  reproduction check (leaky vs shipped WALLSZ): {agree*100:.2f}% agree\n")

    Gl, Gh = gates(V, D_leak), gates(V, D_hon)

    # --- how often does the snapshot even differ? ---
    same_snap = np.isclose(D_leak.dep_thick.fillna(-1), D_hon.dep_thick.fillna(-1))
    print(f"BOOK STATE CHANGED by the honest read: "
          f"{(~same_snap).sum()}/{len(V)} ({(~same_snap).mean()*100:.1f}%)")

    # --- gate flips ---
    gold = V.sess.eq("gold").to_numpy()
    pre = V.sess.eq("pre").to_numpy()
    adm_l = (Gl.D == 1) & (Gl.below_d >= 2.75) & (Gl.WALLSZ == 1)
    adm_h = (Gh.D == 1) & (Gh.below_d >= 2.75) & (Gh.WALLSZ == 1)
    print("\nGOLD ADMISSION (D gate + wall-quality cut + WALLSZ):")
    print(f"  leaky  admits {int(adm_l[gold].sum())}/{int(gold.sum())}")
    print(f"  honest admits {int(adm_h[gold].sum())}/{int(gold.sum())}")
    lost = int((adm_l & ~adm_h)[gold].sum())
    gained = int((~adm_l & adm_h)[gold].sum())
    print(f"  admitted ONLY thanks to the leak: {lost}   newly admitted: {gained}")

    Wl = Gl.W.fillna(0).to_numpy() == 1
    Wh = Gh.W.fillna(0).to_numpy() == 1
    print("\nPRE-MARKET W GATE:")
    print(f"  leaky admits {int(Wl[pre].sum())}/{int(pre.sum())} | "
          f"honest admits {int(Wh[pre].sum())}/{int(pre.sum())} | "
          f"flips {int((Wl[pre]!=Wh[pre]).sum())}")
    dd = pd.to_numeric(V.dollars_1lot, errors="coerce")
    for tag, m in (("leaky ", pre & Wl), ("honest", pre & Wh),
                   ("leak-only", pre & Wl & ~Wh)):
        x = dd[m].dropna()
        print(f"  {tag}: n={len(x)} WR={100*(x>0).mean():.1f}% sum=${x.sum():+,.0f}"
              if len(x) else f"  {tag}: none")

    # --- dollar consequence on the gold book, 1-lot ---
    d = pd.to_numeric(V.dollars_1lot, errors="coerce")
    gl = gold & adm_l.to_numpy()
    gh = gold & adm_h.to_numpy()
    def stat(m, tag):
        x = d[m].dropna()
        if not len(x):
            print(f"  {tag}: none"); return
        print(f"  {tag}: n={len(x)} WR={100*(x>0).mean():.1f}% "
              f"sum=${x.sum():+,.0f} mean=${x.mean():+.1f}")
    print("\nGOLD BOOK, 1-lot dollars:")
    stat(gl, "leaky (shipped) ")
    stat(gh, "honest          ")
    only = gold & adm_l.to_numpy() & ~adm_h.to_numpy()
    stat(only, "leak-only trades")

    V.assign(**{f"leak_{c}": Gl[c] for c in ("W", "D", "WALLSZ")},
             **{f"hon_{c}": Gh[c] for c in ("W", "D", "WALLSZ")},
             leak_adm=adm_l, hon_adm=adm_h).to_parquet(
        ROOT / "output/leak_damage_canon.parquet")
    print("\nwrote output/leak_damage_canon.parquet")


if __name__ == "__main__":
    main()
