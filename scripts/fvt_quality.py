#!/usr/bin/env python3
"""What separates a good FVT setup from a bad one — measured on GROSS expectancy.

ANGUS 2026-08-06: *"we need to define what a good setup is from a bad one instead of just
attacking this shit at face value."*

WHY GROSS AND NOT NET. `scripts/fvt_oos.py` established that the entry has **zero gross
expectancy**: +0.07 pt/trade at RR1.5 and +0.01 at RR2.5 across 2,756 trades and four years,
*before any costs at all*. That is the whole reason nothing could be tuned into profit — exits,
stops, RR, sessions and flow filters cannot manufacture direction that the entry does not have.

So the only question worth asking is: **is the zero an average of a good population and a bad
one, or is it zero everywhere?** That is a question about GROSS expectancy, because costs are a
constant subtraction and cannot change the answer.

THE QUALITY DIMENSIONS. Taken from what a discretionary trader actually judges, and from JJ's
own words rather than invented:

  disp_size     candle range / ATR. **HIS OWN RULE, WHICH I HAD DROPPED**: "a candle that
                closes decisively (small counter-wick) and ideally is larger than the candles
                before it... 'Large candle size' is discretionary so it's optional." Only the
                counter-wick half was implemented. This is the missing half.
  body_frac     body / range — how decisive the close is beyond the wick test
  break_depth   how far past the swing level it closed, in ATR. A 1-tick break and a decisive
                one are not the same event.
  swing_age     bars since the broken swing formed. An old level is a level people watch; a
                three-bar-old one is noise.
  dist_fv       |close − fair value| / ATR. His premise is displacement AWAY from fair value,
                so how far it has already gone should matter.
  vol_ratio     candle volume vs the prior 30 bars. Displacement on no volume is not
                displacement.
  first_break   is this the first structure break of the window?

BAR: consistent in ALL FOUR YEARS (2023, 2024, 2025, 2026) independently. Two-era and even
three-era consistency have both already produced false positives in this project -- the
three-era bar was measurably ANTI-predictive (research/findings/FVT-TOMBSTONE.md).

    python -m scripts.fvt_quality
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402

YEARS = ("2023", "2024", "2025", "2026")
RR = 2.5
MIN_N = 120


def build(b: pd.DataFrame) -> pd.DataFrame:
    b = b.copy()
    b["atr"] = F.atr_series(b, 1)
    b["vma"] = b.volume.rolling(30).mean().shift(1)
    rng = (b.high - b.low).to_numpy()
    upw = (b.high - np.maximum(b.open, b.close)).to_numpy()
    dnw = (np.minimum(b.open, b.close) - b.low).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d_up = (b.close > b.open).to_numpy() & (np.where(rng > 0, dnw / rng, 1.0) <= F.WICK_MAX)
        d_dn = (b.close < b.open).to_numpy() & (np.where(rng > 0, upw / rng, 1.0) <= F.WICK_MAX)
    b["d_up"], b["d_dn"] = d_up, d_dn

    rows = []
    for day, g in b.groupby("day"):
        g = g.reset_index(drop=True)
        hi, lo, cl, op = (g.high.to_numpy(float), g.low.to_numpy(float),
                          g.close.to_numpy(float), g.open.to_numpy(float))
        hm, atr, vol, vma = (g.hm.to_numpy(), g.atr.to_numpy(float),
                             g.volume.to_numpy(float), g.vma.to_numpy(float))
        du, dd = g.d_up.to_numpy(), g.d_dn.to_numpy()

        sw_hi = np.full(len(g), np.nan); sw_lo = np.full(len(g), np.nan)
        ah = np.full(len(g), np.nan); al = np.full(len(g), np.nan)
        lh = ll = np.nan; lhi = lli = np.nan
        for i in range(len(g)):
            if i >= 2:
                if hi[i - 1] > hi[i - 2] and hi[i - 1] > hi[i]:
                    lh, lhi = hi[i - 1], i - 1
                if lo[i - 1] < lo[i - 2] and lo[i - 1] < lo[i]:
                    ll, lli = lo[i - 1], i - 1
            sw_hi[i], sw_lo[i], ah[i], al[i] = lh, ll, lhi, lli

        for wn, wlo, whi in F.WINDOW_SETS["all"]:
            seg = np.flatnonzero(hm >= wlo)
            if not len(seg):
                continue
            fv = float(op[seg[0]])
            start = wlo + (F.SKIP_FIRST_MIN if wn == "AM" else 0)
            idx = np.flatnonzero((hm >= start) & (hm < wlo + 15))
            nbreak = 0
            for i in idx:
                if not np.isfinite(atr[i]) or atr[i] <= 0:
                    continue
                above = cl[i] > fv
                d_ = 0; lvl = np.nan; age = np.nan
                if above and np.isfinite(sw_hi[i]) and cl[i] > sw_hi[i] and du[i]:
                    d_, lvl, age = 1, sw_hi[i], i - ah[i]
                elif (not above) and np.isfinite(sw_lo[i]) and cl[i] < sw_lo[i] and dd[i]:
                    d_, lvl, age = -1, sw_lo[i], i - al[i]
                if d_ == 0:
                    continue
                nbreak += 1
                if nbreak > 1:
                    continue                       # first attempt per window
                fwd = np.flatnonzero((hm > hm[i]) & (hm < whi))
                if not len(fwd):
                    continue
                e = cl[i]
                sd = next(s for a, s in F.TIERS if atr[i] > a)
                adv = np.maximum.accumulate((e - lo[fwd]) if d_ == 1 else (hi[fwd] - e))
                fav = np.maximum.accumulate((hi[fwd] - e) if d_ == 1 else (e - lo[fwd]))
                tgt = sd * RR
                ts = np.argmax(adv >= sd) if (adv >= sd).any() else 10**9
                tt = np.argmax(fav >= tgt) if (fav >= tgt).any() else 10**9
                gross = (-sd if ts <= tt else tgt) if min(ts, tt) < 10**9 \
                    else (cl[fwd[-1]] - e) * d_
                rows.append({
                    "day": day, "yr": day[:4], "win": wn, "dir": d_, "gross": float(gross),
                    "disp_size": rng[i] / atr[i],
                    "body_frac": abs(cl[i] - op[i]) / rng[i] if rng[i] > 0 else np.nan,
                    "break_depth": abs(cl[i] - lvl) / atr[i],
                    "swing_age": float(age),
                    "dist_fv": abs(cl[i] - fv) / atr[i],
                    "vol_ratio": vol[i] / vma[i] if np.isfinite(vma[i]) and vma[i] > 0 else np.nan,
                    "mins_in": int(hm[i] - wlo)})
    return pd.DataFrame(rows)


def main() -> int:
    b = F.load()
    Q = build(b)
    print(f"{len(Q):,} first-attempt continuation setups, {Q.day.nunique()} sessions, "
          f"gross mean {Q.gross.mean():+.3f} pt", flush=True)

    L = ["# What separates a good FVT setup from a bad one", "",
         "Measured on **gross** expectancy (pre-cost), because the entry was shown to have zero",
         "gross edge overall — so the only question is whether that zero hides a good population",
         "and a bad one, or is zero everywhere. Costs are a constant and cannot change it.", "",
         f"**{len(Q):,} first-attempt continuation setups over {Q.day.nunique()} sessions "
         f"(2023–2026). Overall gross {Q.gross.mean():+.3f} pt/trade.**", "",
         "Bar: **consistent in all four years independently.** Three-era consistency was already",
         "shown to be anti-predictive here, so four is the minimum worth reporting.", "",
         "| variable | tier | n | gross | 2023 | 2024 | 2025 | 2026 | 4/4 |",
         "|---|---|---:|---:|---:|---:|---:|---:|:---:|"]

    hits = []
    for v in ["disp_size", "body_frac", "break_depth", "swing_age", "dist_fv",
              "vol_ratio", "mins_in"]:
        s = Q[v].replace([np.inf, -np.inf], np.nan)
        if s.notna().sum() < 500:
            continue
        q = s.quantile([1 / 3, 2 / 3]).values
        for nm, S in [("LOW", Q[s <= q[0]]), ("MID", Q[(s > q[0]) & (s < q[1])]),
                      ("HIGH", Q[s >= q[1]])]:
            if len(S) < MIN_N:
                continue
            ys = [S[S.yr == y].gross.mean() if (S.yr == y).sum() > 40 else np.nan for y in YEARS]
            ok = all(np.isfinite(x) and x > 0 for x in ys)
            if ok:
                hits.append((v, nm, S.gross.mean(), len(S)))
            L.append(f"| `{v}` | {nm} | {len(S):,} | **{S.gross.mean():+.2f}** | "
                     + " | ".join(f"{x:+.2f}" if np.isfinite(x) else "—" for x in ys)
                     + f" | {'**yes**' if ok else ''} |")

    L += ["", "---", "", "## Verdict", ""]
    if hits:
        L += [f"**{len(hits)} tier(s) positive in all four years:**", ""]
        for v, nm, g, n in sorted(hits, key=lambda x: -x[2]):
            L.append(f"- `{v}` = {nm}: gross **{g:+.2f}** pt on {n:,} setups")
        L += ["", "Gross positive in four independent years is the strongest signal available",
              "short of a fresh holdout. Costs (~0.5 pt realistic on NQ) still have to come out",
              "of it, so anything under +0.5 gross is not tradeable however consistent.", ""]
    else:
        L += ["**No quality tier is positive in all four years.** The zero gross expectancy is",
              "not an average of a good and a bad population — it is zero throughout. The",
              "displacement-plus-structure-break entry carries no directional information on NQ",
              "that any of these quality measures can isolate.", "",
              "That includes `disp_size`, which is JJ's own stated rule and was the strongest",
              "candidate going in — the half of his displacement definition this project had",
              "not implemented.", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_quality.md").write_text(text)
    Q.to_parquet(ROOT / "output/fvt_quality.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
