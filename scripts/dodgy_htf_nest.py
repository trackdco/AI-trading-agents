#!/usr/bin/env python3
"""X1 — the higher-timeframe nest: a 1m iFVG taken only inside a 1h/4h FVG or order block.

Run against DECLARATIONS-dodgy-htf-nest.md, committed before this script was run.

This is the last live item in the lecture. FINDINGS-dodgy-placebo.md showed the 1-minute
trigger carries no measurable information -- flipped backwards it produces the same book --
and barred further FILTER tests on that population. X1 is exempt because he states it as a
change of population, not a filter: "tap into a giant 1 hour or 4 hour fair value gap and
then find a one minute entry out of that rally gap. So, it's a trade off of a trade."

BINNING. Higher-timeframe candles are grouped by HOURS ELAPSED SINCE EACH SESSION'S 18:00
OPEN, not by clock time. Two reasons, and the second is the one that matters: it is
DST-safe (a fixed pandas `origin` drifts an hour twice a year across a 3.5-year sample),
and it puts the 4h boundaries on 22:00/02:00/06:00/10:00/14:00/18:00 ET -- so 10:00 is a
4-hour candle close, which is his own R1 claim and a free check that the binning is the one
he is describing.

NO LOOKAHEAD. A zone is born at the CLOSE of the candle that completes it, so it first
becomes usable on the next 1-minute bar. It dies when price closes beyond its far side, or
at max_age HTF candles.

THE PLACEBO POOL IS RESTRICTED TO IN-ZONE BARS. That is the whole design. An unrestricted
pool would measure whether a 1h zone is a good place to be; the restricted one asks the
question that matters -- given that price is inside the zone, does his trigger beat a coin
flip taken there?

    .venv/bin/python scripts/dodgy_htf_nest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import COST_PTS, TICK, report
from scripts.dodgy_near_draw import PT, simulate
from scripts.dodgy_placebo import SEED, audit, paired, placebo
from src.research.tomtrades import autopsy as AU

MAX_AGE = 30          # HTF candles a zone may live; [R], not his number
WIN = (510, 660)


def htf_index(bars: pd.DataFrame, hours: float) -> np.ndarray:
    """Bin id per 1m bar: session day + slot of `hours` elapsed since that day's 18:00."""
    ts = bars.index
    sd = (ts - pd.Timedelta(hours=18)).date
    naive = pd.to_datetime(pd.Series(sd, index=ts).astype("string")) + pd.Timedelta(hours=18)
    start = naive.dt.tz_localize(ts.tz, nonexistent="shift_forward", ambiguous=True)
    elapsed = (ts - pd.DatetimeIndex(start)).total_seconds() / 3600.0
    slot = np.floor(elapsed / hours).astype(np.int64)
    day = pd.factorize(pd.Series(sd, index=ts))[0]
    return day * 1000 + slot


def zones(bars: pd.DataFrame, hours: float, kind: str) -> list[tuple[int, int, float, float, int]]:
    """(birth_1m_idx, death_1m_idx, lo, hi, direction) for every zone of this type.

    direction is the side the zone SUPPORTS: +1 bullish (price above it), -1 bearish.
    """
    bid = htf_index(bars, hours)
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(bars)
    # last 1m bar of each HTF candle, in order
    ends = np.flatnonzero(np.r_[bid[1:] != bid[:-1], True])
    starts = np.r_[0, ends[:-1] + 1]
    H = np.maximum.reduceat(h, starts)
    L = np.minimum.reduceat(l_, starts)
    O, C = o[starts], c[ends]
    m = len(ends)
    out = []
    for k in range(2, m):
        cand = []
        if kind == "fvg":
            if L[k] > H[k - 2]:
                cand.append((H[k - 2], L[k], 1))
            if H[k] < L[k - 2]:
                cand.append((H[k], L[k - 2], -1))
        else:                                   # order block
            j = k - 1
            if C[j] < O[j] and C[k] > H[j]:     # down candle, next closes above its high
                cand.append((L[j], H[j], 1))
            if C[j] > O[j] and C[k] < L[j]:
                cand.append((H[j], L[j], -1))
        if not cand:
            continue
        birth = ends[k] + 1                     # first bar AFTER the completing close
        if birth >= n:
            continue
        stop_at = ends[min(k + MAX_AGE, m - 1)]
        for lo, hi, d in cand:
            lo, hi = min(lo, hi), max(lo, hi)
            w = slice(birth, stop_at + 1)
            bad = (c[w] < lo) if d > 0 else (c[w] > hi)
            k2 = np.flatnonzero(bad)
            death = birth + int(k2[0]) if len(k2) else stop_at
            if death > birth:
                out.append((birth, death, lo, hi, d))
    return out


def zone_mask(bars: pd.DataFrame, zs, direction: int | None = None):
    """Per-1m-bar: inside a live zone? plus the bounds of the most recent such zone."""
    c = bars["close"].to_numpy()
    n = len(c)
    inz = np.zeros(n, dtype=bool)
    zlo = np.full(n, np.nan)
    zhi = np.full(n, np.nan)
    for birth, death, lo, hi, d in zs:
        if direction is not None and d != direction:
            continue
        w = slice(birth, death + 1)
        hit = (c[w] >= lo) & (c[w] <= hi)
        idx = np.flatnonzero(hit) + birth
        inz[idx] = True
        zlo[idx], zhi[idx] = lo, hi          # later zones overwrite earlier: most recent
    return inz, zlo, zhi


def restop_htf(sig: pd.DataFrame, zlo: np.ndarray, zhi: np.ndarray) -> pd.DataFrame:
    """X2: stop at the far edge of the HTF zone, not the 1m gap edge."""
    i = sig.i.to_numpy()
    d = sig.direction.to_numpy()
    s = sig.copy()
    s["stop"] = np.where(d > 0, zlo[i] - TICK, zhi[i] + TICK)
    return s[np.isfinite(s.stop)].reset_index(drop=True)


def arm(bars, s, label, pool, rng_seed=SEED) -> tuple[dict, dict | None]:
    t = simulate(bars, s, "fixed2r")
    r = report(t, label)
    if "ev" not in r:
        return r, None
    lo, hi = AU.dboot_mean(t.assign(out=t.usd), "out")
    r |= {"med_stop": t.risk.median(), "cost_r": COST_PTS / t.risk.median(),
          "usd": t.usd.mean(), "usd_lo": lo, "usd_hi": hi,
          "gross": (t.out + COST_PTS / t.risk).mean(),
          "usd_day": t.usd.sum() / t.sess_day.nunique()}
    if pool is None:
        return r, None
    rng = np.random.default_rng(rng_seed)
    ctrl = placebo(s, bars, "random_day", rng, pool_mask=pool)
    audit(s, ctrl, bars, label)
    return r, paired(s, ctrl, bars, label) | {"variant": label}


def main() -> None:
    bars = pd.read_parquet(ROOT / "output/_nq_bars.parquet")
    sig = pd.read_parquet(ROOT / "output/_nq_sig.parquet")
    sig["sid"] = np.arange(len(sig))
    n = len(bars)
    print(f"NQ {n:,} bars · {len(sig):,} signals", flush=True)

    # sanity: the 4h bins must close at 10:00 ET, his own R1 claim
    b4 = htf_index(bars, 4.0)
    ends4 = bars.index[np.flatnonzero(np.r_[b4[1:] != b4[:-1], True])]
    vc = pd.Series((ends4 + pd.Timedelta(minutes=1)).hour).value_counts()
    top = sorted(vc.head(6).index.tolist())
    print(f"4h candle closes, top 6 ET hours: {top} "
          f"({100 * vc.head(6).sum() / vc.sum():.1f}% of all boundaries)", flush=True)
    # 17 rather than 18 is the CME maintenance break, not a binning error: the
    # 14:00-18:00 bin holds no bars after 17:00, so its last bar is 16:59. 18:00 is the
    # session OPEN, so that boundary always coincides with the start of the next session.
    assert top == [2, 6, 10, 14, 17, 22], f"4h binning is not 18:00-anchored: {top}"
    print("  -> 10:00 is a 4h close, which is his own R1 claim. Binning confirmed "
          "(17:00 = the maintenance break standing in for the 18:00 boundary).",
          flush=True)

    Z, M = {}, {}
    for hours, tag in ((1.0, "1h"), (4.0, "4h"), (0.25, "15m")):
        for kind in ("fvg", "ob"):
            zs = zones(bars, hours, kind)
            inz, zlo, zhi = zone_mask(bars, zs)
            Z[f"{tag} {kind}"] = zs
            M[f"{tag} {kind}"] = (inz, zlo, zhi)
            print(f"  {tag:4s} {kind:3s}: {len(zs):6,d} zones · price inside "
                  f"{100 * inz.mean():5.1f}% of bars", flush=True)

    his = np.zeros(n, dtype=bool)
    hlo, hhi = np.full(n, np.nan), np.full(n, np.nan)
    for k in ("1h fvg", "1h ob", "4h fvg", "4h ob"):
        inz, zl, zh = M[k]
        take = inz & ~his
        hlo[take], hhi[take] = zl[take], zh[take]
        his |= inz
    M["HIS SET 1h/4h fvg+ob"] = (his, hlo, hhi)
    print(f"  {'his set':8s}: price inside {100 * his.mean():5.1f}% of bars", flush=True)

    si = sig.i.to_numpy()
    rows, pairs = [], []
    r, _ = arm(bars, sig, "baseline (all signals)", None)
    rows.append(r)
    for key in ("1h fvg", "1h ob", "4h fvg", "4h ob", "HIS SET 1h/4h fvg+ob", "15m fvg"):
        inz, zl, zh = M[key]
        s = sig[inz[si]].reset_index(drop=True)
        share = 100 * len(s) / len(sig)
        print(f"\n{key}: {len(s):,} signals ({share:.1f}% of book)", flush=True)
        r, p = arm(bars, s, key, inz)
        rows.append(r)
        if p:
            pairs.append(p)
        if key == "HIS SET 1h/4h fvg+ob":
            s2 = restop_htf(s, zl, zh)
            r2, p2 = arm(bars, s2, "X2 · HIS SET, stop at HTF edge", inz)
            rows.append(r2)
            if p2:
                pairs.append(p2)

    d = pd.DataFrame([r for r in rows if "ev" in r])
    d["ci"] = d.apply(lambda r: f"[{r.lo:+.3f},{r.hi:+.3f}]", axis=1)
    d["eras"] = np.where(d.both, "BOTH", "-")
    print("\n=== X1 ARMS (Law 3: both currencies; Law 2: stop and cost shown) ===")
    print(d[["variant", "n", "per_day", "win_pct", "gross", "ev", "ci", "h1", "h2", "eras"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(d[["variant", "n", "med_stop", "cost_r", "usd", "usd_day"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    q = pd.DataFrame(pairs)
    q["ci"] = q.apply(lambda r: f"[{r.lo:+.4f},{r.hi:+.4f}]", axis=1)
    q["verdict"] = np.where(q.lo > 0, "REAL > PLACEBO",
                            np.where(q.hi < 0, "REAL < PLACEBO", "indistinguishable"))
    print("\n=== vs IN-ZONE PLACEBO (pool restricted to in-zone bars, paired) ===")
    print(q[["variant", "n_pairs", "real_ev", "ctrl_ev", "diff", "ci", "verdict"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    d.to_csv(ROOT / "output/dodgy_htf_nest.csv", index=False)
    q.to_csv(ROOT / "output/dodgy_htf_placebo.csv", index=False)
    print(f"\nPT=${PT:.0f}/pt · MAX_AGE={MAX_AGE} HTF candles · seed={SEED}")


if __name__ == "__main__":
    main()
