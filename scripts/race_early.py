#!/usr/bin/env python3
"""NO-LOOKAHEAD EARLY-ENTRY CONSTRUCTION — Amendment 2. REPORT-ONLY.

Declaration: docs/DECLARATIONS-trigger-race.md Amendment 2 (committed
before this build). At each 1m close: for each admissible TF, fire if
the CURRENT bucket opened on the far side of the TF's DEVELOPING MA and
this minute's close is through it. Stop = the bucket's extreme SO FAR
± 1 tick. Nothing from any later minute appears anywhere; the flatten
gate proves it.

    python -m scripts.race_early [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.race_diagnose import cluster as _cluster_book          # noqa: E402
from scripts.trigger_race_census import (MENU, SESSIONS, TOLW,      # noqa: E402
                                         in_window, m1_episode_arrays)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUT = ROOT / "output/htf_ma_census/race_early.parquet"
NULLP = ROOT / "output/htf_ma_census/race_outcomes_epi.parquet"
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
TICK, COST_PTS = 0.25, 0.5
SEED, DRAWS = 20260807, 2000
MECHS = ["M1", "M2", "M3"]


def day_rows(bars, sess_day):
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
        mfe = 0.0
        for j in range(j0, N):
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stop_j = j
                break
            tv = tgt_arr[j - 1] if j > 0 else np.nan
            if np.isfinite(tv) and lo[j] <= tv <= hi[j]:
                tgt_j, hitv = j, tv
                break
            mfe = max(mfe, d * ((hi[j] if d > 0 else lo[j]) - entry) / risk)
        if tgt_j is not None:
            return True, d * (hitv - entry) / risk - cost, mfe
        if stop_j is not None:
            return False, -1.0 - cost, mfe
        return False, d * (cl[-1] - entry) / risk - cost, mfe

    # per-TF developing state, per 1m row: developing MA, bucket id,
    # bucket open, bucket running extreme
    tfstate = {}
    for tf in (1, 2, 3):
        ma_tf, _ = bb_ma_asof(hist, tf)
        ma_1m = ma_tf.reindex(idx).to_numpy()
        # buckets anchored on wall clock, matching resample(closed="left")
        bucket = idx.floor(f"{tf}min").asi8 if tf > 1 else idx.asi8
        bopen = np.full(N, np.nan)
        bhi = np.full(N, np.nan)
        blo = np.full(N, np.nan)
        cur_b = None
        for j in range(N):
            if bucket[j] != cur_b:
                cur_b = bucket[j]
                bopen[j] = op[j]
                bhi[j] = hi[j]
                blo[j] = lo[j]
            else:
                bopen[j] = bopen[j - 1]
                bhi[j] = max(bhi[j - 1], hi[j])
                blo[j] = min(blo[j - 1], lo[j])
        tfstate[tf] = (ma_1m, bucket, bopen, bhi, blo)

    rows = []
    fired = set()                      # (tf, bucket_id, mech, d) once
    for j in range(N):
        t_dec = idx[j] + pd.Timedelta(minutes=1)
        sess = in_window(t_dec.hour * 60 + t_dec.minute)
        if sess is None:
            continue
        w = w15_1m[j]
        m15 = ma15_1m[j]
        if not (np.isfinite(w) and w > 0 and np.isfinite(m15)):
            continue
        cands = []
        for tf in (1, 2, 3):
            ma_1m, bucket, bopen, bhi, blo = tfstate[tf]
            mk = ma_1m[j]
            if not np.isfinite(mk):
                continue
            for d in (+1, -1):
                if not (d * (cl[j] - mk) > 0 and d * (bopen[j] - mk) <= 0):
                    continue
                if armed1[j] == d:
                    mech = "M1"
                elif live2[j] == d:
                    mech = "M2"
                elif live3[j] == d:
                    mech = "M3"
                else:
                    continue
                n_aff = int(aff[j])
                if mech != "M1" and n_aff < 1:
                    continue
                if tf == 1 and n_aff < 2:
                    continue
                key = (tf, bucket[j], mech, d)
                if key in fired:
                    continue
                cands.append((tf, d, mech, n_aff, bhi[j], blo[j], key))
        for tf, d, mech, n_aff, bh, bl, key in sorted(cands):
            fired.add(key)
            if j + 1 >= N:
                continue
            entry = float(op[j + 1])
            stop = (bl - TICK) if d > 0 else (bh + TICK)
            if d * (entry - stop) <= 0:
                continue
            risk = abs(entry - stop)
            if mech == "M1":
                tgt = ma15_1m
                tname = "ma15"
            else:
                cand = [(k, float(S[k][j])) for k in MENU
                        if np.isfinite(S[k][j])
                        and d * (S[k][j] - entry) > 0]
                cand.sort(key=lambda kv: d * (kv[1] - entry))
                if not cand:
                    continue
                tname = cand[0][0]
                tgt = S[tname]
            h, o, mfe = walk(j + 1, d, entry, stop, tgt)
            rows.append({
                "sess_day": sess_day, "t": t_dec, "mech": mech,
                "direction": d, "dir": "long" if d > 0 else "short",
                "session": sess, "tf_won": tf, "n_aff": n_aff,
                "entry": entry, "stop": stop, "risk": risk,
                "w15": float(w), "ma15": float(m15),
                "tgt_name": tname, "hit": h, "out": o, "mfe_r": mfe})
    return rows


def dboot(df, col, draws=DRAWS):
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def gate(bars, days):
    """Flatten gate: trigger set at/before the flatten point — including
    ENTRY and STOP — must be unchanged. One moved stop = FAIL."""
    bad = n = 0
    for day in days:
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        win = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        rows = day_rows(win, day)
        for r in rows[:2] + rows[len(rows) // 2:len(rows) // 2 + 2]:
            t = pd.Timestamp(r["t"])
            prior = win[win.index < t]
            if prior.empty:
                continue
            pc = float(prior.close.iloc[-1])
            wf = win.copy()
            m = wf.index >= t
            wf.loc[m, ["open", "high", "low", "close"]] = pc
            wf.loc[m, "volume"] = 1
            re = [x for x in day_rows(wf, day)
                  if pd.Timestamp(x["t"]) <= t]
            og = [x for x in rows if pd.Timestamp(x["t"]) <= t]
            n += 1
            same = (len(re) == len(og) and all(
                a["t"] == b["t"] and a["mech"] == b["mech"]
                and a["dir"] == b["dir"] and a["tf_won"] == b["tf_won"]
                and abs(a["stop"] - b["stop"]) < 1e-9
                and (abs(a["entry"] - b["entry"]) < 1e-9
                     or pd.Timestamp(a["t"]) == t)
                for a, b in zip(og, re)))
            if not same:
                bad += 1
    ok = bad == 0 and n > 0
    print(f"   flatten gate (entry+stop invariance): {n} probes, "
          f"bad {bad} -> {'PASS' if ok else 'FAIL'}")
    return ok


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
    print("NO-LOOKAHEAD EARLY ENTRY (Amendment 2) — developing MA, "
          "developing-extreme stop. REPORT-ONLY, no declared bar.")
    print("=" * 100)
    print("\nGATE (before anything is read):")
    if not gate(bars, days[::60]):
        sys.exit(1)

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
    B = _cluster_book(F, bars)
    print(f"book: {len(B)} fights ({len(B)/nd:.2f}/day)")

    NL = pd.read_parquet(NULLP)
    NL["t"] = pd.to_datetime(NL.t)
    NL["out"] = np.where(NL.mech == "M1", NL.m1_out, NL.near_out)
    BN = _cluster_book(NL, bars)

    def ci(lo_, hi_):
        return (f"[{lo_:+.3f},{hi_:+.3f}]" if np.isfinite(lo_)
                else "[thin]")

    print("\nPER CELL — EARLY (this build) vs CLOSURE CENSUS (the null):")
    print(f"   {'window':7s} {'mech':4s} {'n_e':>5s} {'/d':>5s} "
          f"{'EV_early':>9s} {'95% CI':>18s} {'hit%':>6s} | "
          f"{'n_null':>6s} {'EV_null':>8s}")
    for w_ in SESSIONS:
        for mech in MECHS:
            g = B[(B.session == w_) & (B.mech == mech)]
            gn = BN[(BN.session == w_) & (BN.mech == mech)]
            lo_, hi_ = dboot(g, "out")
            sig = "!" if np.isfinite(lo_) and (lo_ > 0 or hi_ < 0) else ""
            print(f"   {w_:7s} {mech:4s} {len(g):5d} {len(g)/nd:5.2f} "
                  f"{g.out.mean():+9.3f} {ci(lo_, hi_):>18s}{sig} "
                  f"{g.hit.mean()*100:5.1f}% | {len(gn):6d} "
                  f"{gn.out.mean():+8.3f}")
    print(f"\n   whole book: EARLY {B.out.mean():+.3f} "
          f"({len(B)/nd:.2f}/d, risk med {B.risk.median():.1f}pt) vs "
          f"NULL {BN.out.mean():+.3f} ({len(BN)/nd:.2f}/d, risk med "
          f"{BN.risk.median():.1f}pt)")
    print("   by tf_won (EARLY): " + "  ".join(
        f"{tf}m n={len(B[B.tf_won == tf])} EV "
        f"{B[B.tf_won == tf].out.mean():+.3f}"
        for tf in (1, 2, 3) if len(B[B.tf_won == tf]) >= 10))
    m = B.mfe_r
    print(f"   MFE: p25 {m.quantile(.25):.2f} p50 {m.median():.2f} "
          f"p75 {m.quantile(.75):.2f} p90 {m.quantile(.9):.2f}")
    print("   cost sensitivity: " + "  ".join(
        f"@{0.5+x:.1f}pt {(B.out - x/B.risk).mean():+.3f}"
        for x in (0.0, 0.5, 1.0)))


if __name__ == "__main__":
    main()
