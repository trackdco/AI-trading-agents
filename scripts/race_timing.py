#!/usr/bin/env python3
"""ENTRY-TIMING GAP — corrected (episode-M1) race census, whole
population. REPORT-ONLY.

Question (the trader's): for every fight, what would entering EARLIER
within the trigger candle — instead of waiting for the full close — have
done to the fill and the resulting R.

DECLARED CONVENTIONS:
- Early entry = the close of the FIRST 1m bar inside the trigger candle
  whose close is through the winning TF's own (developing, as-of) BB MA
  in the trade direction, with the candle's open still on the far side —
  the earliest 1m-resolution moment the cross was visible. For 1m
  triggers this is the trigger candle's own close (the gap is then just
  close-print vs next-minute open).
- The STOP IS KEPT AT THE ACTUAL ROW'S STOP (full-candle extreme ±1
  tick). For the early entry this uses information not final at fill
  time — an accounting convention, declared, that isolates the FILL
  effect from stop redefinition. Flagged, not hidden.
- The early trade is RE-WALKED from its own minute (same first-passage
  rules, same target array as the actual row) — so it carries the extra
  adverse exposure of living through the trigger candle's remainder,
  including being stopped there. Both sides of the trade-off are priced.
- This measures the mechanization gap; it is NOT an adoptable entry rule
  (the early trigger is a different, unconfirmed trigger). Report-only.

    python -m scripts.race_timing [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.trigger_race_census import (MENU, SESSIONS, TOLW,      # noqa: E402
                                         in_window, m1_episode_arrays)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUT = ROOT / "output/htf_ma_census/race_timing.parquet"
CENSUS = ROOT / "output/htf_ma_census/race_fit_m1episode.parquet"
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
TICK, COST_PTS = 0.25, 0.5
SEED, DRAWS = 20260807, 2000
MECHS = ["M1", "M2", "M3"]


def day_rows(bars, sess_day):
    """Episode-census triggers with ACTUAL and EARLY entries, both
    walked. Mirrors race_outcomes day_rows (episode M1 mode)."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    if hist.empty:
        return []
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl, op = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy(), seg.open.to_numpy())
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    armed1, _ = m1_episode_arrays(hi, lo, cl, ma15_1m, w15_1m)
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"):
        S[b] = vw[b].reindex(idx).to_numpy()
    dist = np.stack([np.abs(S[k] - ma15_1m) for k in MENU])
    aff = np.where(np.isfinite(w15_1m) & (w15_1m > 0),
                   np.nansum(dist <= TOLW * w15_1m, axis=0), 0).astype(int)

    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)
    live2 = np.zeros(N, dtype=int)
    live3 = np.zeros(N, dtype=int)
    cur2 = cur3 = 0
    for bi in range(len(f15)):
        m = ma_at15[bi]
        b_ = f15.iloc[bi]
        if not np.isfinite(m):
            continue
        if (b_.close > m) != (b_.open > m):
            cur2, cur3 = 0, (1 if b_.close > m else -1)
        elif (b_.close < m) and (b_.high >= m) and (b_.open < m):
            cur2 = -1
        elif (b_.close > m) and (b_.low <= m) and (b_.open > m):
            cur2 = +1
        a = min(pos15[bi], N)
        b2 = min(pos15[bi + 1], N) if bi + 1 < len(f15) else N
        live2[a:b2] = cur2
        live3[a:b2] = cur3

    def walk(j0, d, entry, stop, tgt_arr):
        risk = abs(entry - stop)
        cost = COST_PTS / risk
        hitv = None
        stop_j = tgt_j = None
        for j in range(j0, N):
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stop_j = j
                break
            tv = tgt_arr[j - 1] if j > 0 else np.nan
            if np.isfinite(tv) and lo[j] <= tv <= hi[j]:
                tgt_j, hitv = j, tv
                break
        if tgt_j is not None:
            return True, d * (hitv - entry) / risk - cost
        if stop_j is not None:
            return False, -1.0 - cost
        return False, d * (cl[-1] - entry) / risk - cost

    ma_tf_1m = {}
    fires = {}
    for tf in (1, 2, 3):
        ma_tf, _ = bb_ma_asof(hist, tf)
        ma_tf_1m[tf] = ma_tf.reindex(idx).to_numpy()
        if tf == 1:
            ftf = seg.copy()
            ftf.index = ftf.index + pd.Timedelta(minutes=1)
        else:
            ftf = hist.resample(f"{tf}min", label="right",
                                closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        pos = np.clip(np.searchsorted(
            idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
            0, N - 1)
        matf = ma_tf.reindex(idx).to_numpy()[pos]
        fh, fl = ftf.high.to_numpy(), ftf.low.to_numpy()
        fo, fc = ftf.open.to_numpy(), ftf.close.to_numpy()
        for bi, ts in enumerate(ftf.index):
            sess = in_window(ts.hour * 60 + ts.minute)
            if sess is None:
                continue
            p = pos[bi]
            m_tf, m15, w = matf[bi], ma15_1m[p], w15_1m[p]
            if not (np.isfinite(m_tf) and np.isfinite(m15)
                    and np.isfinite(w) and w > 0):
                continue
            disp_o = (fo[bi] - m15) / w
            for d in (+1, -1):
                if not (d * (fc[bi] - m_tf) > 0
                        and d * (fo[bi] - m_tf) <= 0):
                    continue
                if armed1[p] == d:
                    mech = "M1"
                elif live2[p] == d:
                    mech = "M2"
                elif live3[p] == d:
                    mech = "M3"
                else:
                    continue
                fires.setdefault((ts, mech, d), {})[tf] = (
                    p, sess, float(fo[bi]), float(fh[bi]), float(fl[bi]))

    rows = []
    for (ts, mech, d), by_tf in sorted(fires.items()):
        adm = []
        for tf, (p, sess, foo, fhh, fll) in sorted(by_tf.items()):
            n_aff = int(aff[p])
            if mech != "M1" and n_aff < 1:
                continue
            if tf == 1 and n_aff < 2:
                continue
            adm.append((tf, p, sess, foo, fhh, fll, n_aff))
        if not adm:
            continue
        tf, p, sess, foo, fhh, fll, n_aff = adm[0]
        j0 = int(np.searchsorted(idx.values, ts.to_datetime64()))
        if j0 >= N:
            continue
        entry = float(op[j0])
        stop = (fll - TICK) if d > 0 else (fhh + TICK)
        if d * (entry - stop) <= 0:
            continue
        risk = abs(entry - stop)
        # target array as the actual row
        if mech == "M1":
            tgt = ma15_1m
        else:
            cand = [(k, float(S[k][p])) for k in MENU
                    if np.isfinite(S[k][p]) and d * (S[k][p] - entry) > 0]
            cand.sort(key=lambda kv: d * (kv[1] - entry))
            if not cand:
                continue
            tgt = S[cand[0][0]]
        _, out_act = walk(j0, d, entry, stop, tgt)
        # ---- EARLY ENTRY: first 1m close through the winning TF's
        # developing MA inside the trigger candle
        q0 = p - tf + 1
        k_e = None
        for k in range(max(q0, 0), p + 1):
            mk = ma_tf_1m[tf][k]
            if np.isfinite(mk) and d * (cl[k] - mk) > 0:
                k_e = k
                break
        if k_e is None:
            k_e = p
        fill_e = float(cl[k_e])
        risk_e = abs(fill_e - stop)
        if d * (fill_e - stop) <= 0 or risk_e <= 0:
            continue                      # early fill already through stop
        _, out_e = walk(k_e + 1, d, fill_e, stop, tgt)
        rows.append({
            "sess_day": sess_day, "t": ts, "mech": mech, "dir":
            "long" if d > 0 else "short", "session": sess, "tf_won": tf,
            "w15": float(w15_1m[p]), "ma15": float(ma15_1m[p]),
            "risk": risk, "entry": entry, "fill_e": fill_e,
            "min_early": int(p - k_e) + 1 if k_e < p else 0,
            "dfill_pts": d * (entry - fill_e),
            "dfill_r": d * (entry - fill_e) / risk,
            "out_act": out_act, "out_e": out_e,
            "dout": out_e - out_act})
    return rows


def cluster(F, bars, x=0.5):
    key = {}
    for day, D in F.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0)
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        for grp, g in D.groupby(["mech", "dir"]):
            g = g.sort_values("t")
            ts, rp, ws = g.t.tolist(), g.ma15.tolist(), g.w15.tolist()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values, ts[a].to_datetime64()))
                i1 = int(np.searchsorted(idx.values,
                                         ts[a + 1].to_datetime64()))
                if i1 <= i0 or ws[a] <= 0 or not np.isfinite(rp[a]):
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - rp[a]),
                                         np.abs(lo[i0:i1] - rp[a])))
                key[(day, grp, ts[a + 1])] = m / ws[a]
    ids = {}
    for (day, mech, dr), g in F.groupby(["sess_day", "mech", "dir"],
                                        sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, (mech, dr), t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{mech}:{dr}:S{cid}"
    return F.assign(scid=pd.Series(ids)).sort_values("t") \
        .groupby("scid", as_index=False).first()


def dboot_mean(df, col):
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (DRAWS, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(DRAWS, np.nan), where=c > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END]
    nd = len(days)

    print("=" * 100)
    print("ENTRY-TIMING GAP — early (first 1m cross inside the trigger "
          "candle) vs waited (next-1m-open). REPORT-ONLY.")
    print("Stop kept at the actual row's stop (declared accounting "
          "convention; look-ahead for the early leg, flagged).")
    print("=" * 100)

    if "--build" in sys.argv or not OUT.exists():
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d))
            if k % 40 == 0:
                print(f"  {k}/{nd}...", flush=True)
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(F):,} rows)")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)
    B = cluster(F, bars)
    print(f"book: {len(B)} fights ({len(B)/nd:.2f}/day)\n")

    def q(s):
        return " ".join(f"{s.quantile(x):+.2f}" for x in
                        (.1, .25, .5, .75, .9))

    print("DISTRIBUTIONS per window x mechanism (p10 p25 p50 p75 p90); "
          "day-boot 95% CI on mean dR:")
    for w_ in SESSIONS:
        for mech in MECHS:
            g = B[(B.session == w_) & (B.mech == mech)]
            if len(g) < 20:
                print(f"  {w_} {mech}: n={len(g)} THIN")
                continue
            lo_, hi_ = dboot_mean(g, "dout")
            print(f"  {w_:7s} {mech}  n={len(g):4d}  min-early med "
                  f"{g.min_early.median():.0f}  dfill_pts [{q(g.dfill_pts)}]"
                  f"  dfill_R [{q(g.dfill_r)}]")
            print(f"          out ACT {g.out_act.mean():+.3f} -> EARLY "
                  f"{g.out_e.mean():+.3f}   mean dR "
                  f"{g.dout.mean():+.3f} [{lo_:+.3f},{hi_:+.3f}]"
                  f"{'!' if np.isfinite(lo_) and (lo_ > 0 or hi_ < 0) else ''}")
    print("\nby winning TF (structural: 1m has no intra-candle room):")
    for tf in (1, 2, 3):
        g = B[B.tf_won == tf]
        if len(g) < 20:
            continue
        lo_, hi_ = dboot_mean(g, "dout")
        print(f"  {tf}m  n={len(g):4d}  min-early med "
              f"{g.min_early.median():.0f}  dfill_pts med "
              f"{g.dfill_pts.median():+.2f}  dfill_R med "
              f"{g.dfill_r.median():+.3f}  mean dR {g.dout.mean():+.3f} "
              f"[{lo_:+.3f},{hi_:+.3f}]")
    flip_w = ((B.out_act <= 0) & (B.out_e > 0)).mean()
    flip_l = ((B.out_act > 0) & (B.out_e <= 0)).mean()
    print(f"\noutcome flips: loser->winner {flip_w*100:.1f}%  "
          f"winner->loser {flip_l*100:.1f}% of fights")
    print(f"whole-book: mean out ACT {B.out_act.mean():+.3f} vs EARLY "
          f"{B.out_e.mean():+.3f}  (dR mean {B.dout.mean():+.3f}, "
          f"med {B.dout.median():+.3f})")


if __name__ == "__main__":
    main()
