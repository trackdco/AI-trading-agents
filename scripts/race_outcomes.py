#!/usr/bin/env python3
"""OUTCOME SCORING on the race census. REPORT-ONLY, first look.

Declaration: docs/DECLARATIONS-race-outcomes.md (committed before this
run). Population = race_fit.parquet at the declared 0.10W, grammar
unchanged. Calibration assertion: the re-derived trigger set must match
the census parquet exactly, else stop.

    python -m scripts.race_outcomes [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.trigger_race_census import (DISP, MENU, SESSIONS,      # noqa: E402
                                         TOLW, in_window,
                                         m1_episode_arrays)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

# AMENDMENT 1: --m1-episode scores the episode-M1 census (the corrected
# population) against its own parquet; default remains the original.
M1_MODE = "episode" if "--m1-episode" in sys.argv else "open"
OUT = ROOT / ("output/htf_ma_census/race_outcomes_epi.parquet"
              if M1_MODE == "episode"
              else "output/htf_ma_census/race_outcomes.parquet")
CENSUS = ROOT / ("output/htf_ma_census/race_fit_m1episode.parquet"
                 if M1_MODE == "episode"
                 else "output/htf_ma_census/race_fit.parquet")
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
TICK, COST_PTS = 0.25, 0.5
SEED, DRAWS = 20260807, 2000
XS = [0.25, 0.5, 1.0, 2.0]
XDEC = 0.5
MECHS = ["M1", "M2", "M3"]
EXCL = {"no_next_open": 0, "gap_through_stop": 0}


def day_rows(bars, sess_day):
    """Triggers (same grammar, declared tol only) WITH outcome walks."""
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
    armed1, _epi1 = m1_episode_arrays(hi, lo, cl, ma15_1m, w15_1m)
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
        """First-passage: target (as-of previous-1m value) vs stop.
        Same-bar -> stop wins. Returns (hit, out_R, mfe_bounded)."""
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

    # per-TF fresh crosses (identical grammar to the census builder)
    fires = {}
    for tf in (1, 2, 3):
        ma_tf, _ = bb_ma_asof(hist, tf)
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
                m1_ok = (armed1[p] == d) if M1_MODE == "episode" else \
                    ((-disp_o if d > 0 else disp_o) >= DISP)
                if m1_ok:
                    mech = "M1"
                elif live2[p] == d:
                    mech = "M2"
                elif live3[p] == d:
                    mech = "M3"
                else:
                    continue
                fires.setdefault((ts, mech, d), {})[tf] = (
                    p, disp_o, sess, float(fh[bi]), float(fl[bi]))

    rows = []
    for (ts, mech, d), by_tf in sorted(fires.items()):
        adm = []
        for tf, (p, disp_o, sess, fhh, fll) in sorted(by_tf.items()):
            n_aff = int(aff[p])
            if mech != "M1" and n_aff < 1:
                continue
            if tf == 1 and n_aff < 2:
                continue
            adm.append((tf, p, disp_o, sess, n_aff, fhh, fll))
        if not adm:
            continue
        tf, p, disp_o, sess, n_aff, fhh, fll = adm[0]
        j0 = int(np.searchsorted(idx.values, ts.to_datetime64()))
        if j0 >= N:
            EXCL["no_next_open"] += 1
            continue
        entry = float(op[j0])
        stop = (fll - TICK) if d > 0 else (fhh + TICK)
        if d * (entry - stop) <= 0:
            EXCL["gap_through_stop"] += 1
            continue
        risk = abs(entry - stop)
        rec = {"sess_day": sess_day, "t": ts, "mech": mech,
               "direction": d, "dir": "long" if d > 0 else "short",
               "session": sess, "tf_won": tf, "n_aff": n_aff,
               "entry": entry, "stop": stop, "risk": risk,
               "w15": float(w15_1m[p]), "ma15": float(ma15_1m[p])}
        if mech == "M1":
            h, o, mfe = walk(j0, d, entry, stop, ma15_1m)
            rec.update({"m1_hit": h, "m1_out": o,
                        "m1_dist_r": d * (ma15_1m[p] - entry) / risk,
                        "mfe_r": mfe})
        else:
            # NEAR/FAR = 1st/2nd menu structure strictly beyond entry in
            # the trade direction, evaluated at the trigger row.
            cand = [(k, float(S[k][p])) for k in MENU
                    if np.isfinite(S[k][p]) and d * (S[k][p] - entry) > 0]
            cand.sort(key=lambda kv: d * (kv[1] - entry))
            mfe_all = 0.0
            for lbl, item in (("near", cand[0] if cand else None),
                              ("far", cand[1] if len(cand) > 1 else None)):
                if item is None:
                    rec.update({f"{lbl}_name": None, f"{lbl}_hit": False,
                                f"{lbl}_out": np.nan,
                                f"{lbl}_dist_r": np.nan})
                    continue
                nm, tv = item
                h, o, mfe = walk(j0, d, entry, stop, S[nm])
                rec.update({f"{lbl}_name": nm, f"{lbl}_hit": h,
                            f"{lbl}_out": o,
                            f"{lbl}_dist_r": d * (tv - entry) / risk})
                mfe_all = max(mfe_all, mfe)
            rec["mfe_r"] = mfe_all
        rows.append(rec)
    return rows


def cluster(F, bars, x=XDEC):
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
            ts = g.t.tolist()
            rp = g.ma15.tolist()
            ws = g.w15.tolist()
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
    """T1 flatten on the OUTCOME builder: entry must equal the flattened
    value (and move vs the real run somewhere)."""
    bad = moved = n = 0
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
            mt = [x for x in day_rows(wf, day)
                  if x["t"] == r["t"] and x["mech"] == r["mech"]
                  and x["dir"] == r["dir"]]
            if mt:
                n += 1
                if abs(mt[0]["entry"] - pc) > 1e-9:
                    bad += 1
                if abs(mt[0]["entry"] - r["entry"]) > 1e-9:
                    moved += 1
    ok = bad == 0 and moved > 0 and n > 0
    print(f"   T1 flatten: {n} probes, bad {bad}, moved {moved} -> "
          f"{'PASS' if ok else 'FAIL'}")
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
    print(f"RACE OUTCOMES — M1 mode: {M1_MODE.upper()}. "
          "REPORT ONLY, no declared bar (~100+ numbers).")
    print("=" * 100)

    print("\nENTRY GATE (before anything is read):")
    if not gate(bars, days[::60]):
        sys.exit(1)

    if "--build" in sys.argv or not OUT.exists():
        for k in EXCL:
            EXCL[k] = 0
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d))
            if k % 40 == 0:
                print(f"  {k}/{nd}...", flush=True)
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(F):,} rows) | excl {EXCL}")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)

    # ---- CALIBRATION ASSERTION vs the census parquet -----------------
    C = pd.read_parquet(CENSUS)
    C["t"] = pd.to_datetime(C.t)
    C = C[C.tol == TOLW]
    ka = set(map(tuple, F[["t", "mech", "dir", "tf_won", "n_aff"]]
                 .itertuples(index=False)))
    kb = set(map(tuple, C[["t", "mech", "dir", "tf_won", "n_aff"]]
                 .itertuples(index=False)))
    extra, missing = ka - kb, kb - ka
    # rows excluded for entry feasibility are the ONLY legitimate gap
    print(f"\nCALIBRATION vs census: outcome {len(ka)} vs census {len(kb)} "
          f"| in-outcome-only {len(extra)} | in-census-only {len(missing)} "
          f"(must be <= excluded {sum(EXCL.values())})")
    if extra or len(missing) > 60:
        print("CALIBRATION FAIL — stopping before any outcome is read.")
        sys.exit(1)

    books = {x: cluster(F, bars, x) for x in XS}
    B = books[XDEC]

    def ci(lo_, hi_):
        return (f"[{lo_:+.3f},{hi_:+.3f}]" if np.isfinite(lo_)
                else "[thin: <3 days]")

    print(f"\nBOOK: {len(B)} fights ({len(B)/nd:.2f}/day) at X={XDEC}W "
          f"from {len(F)} raw")
    for w in SESSIONS:
        print("\n" + "=" * 100)
        print(f"WINDOW {w}  (never pooled with the other windows)")
        print("=" * 100)
        for mech in MECHS:
            for dr in ("long", "short"):
                g = B[(B.session == w) & (B.mech == mech) & (B.dir == dr)]
                thin = "   THIN" if len(g) < 10 else ""
                print(f"  {mech} {dr:6s} n={len(g):3d} "
                      f"({len(g)/nd:.2f}/day){thin}")
                if len(g) == 0:
                    continue
                if mech == "M1":
                    lo_, hi_ = dboot(g, "m1_out")
                    print(f"     15m-MA  medD {g.m1_dist_r.median():5.2f}R"
                          f"  hit {g.m1_hit.mean()*100:5.1f}%  EV "
                          f"{g.m1_out.mean():+7.3f} {ci(lo_, hi_)}")
                else:
                    for lbl in ("near", "far"):
                        gg = g[g[f"{lbl}_name"].notna()]
                        if len(gg) == 0:
                            continue
                        nms = "/".join(
                            gg[f"{lbl}_name"].value_counts().index[:3])
                        lo_, hi_ = dboot(gg, f"{lbl}_out")
                        print(f"     {lbl:5s} medD "
                              f"{gg[f'{lbl}_dist_r'].median():5.2f}R  hit "
                              f"{gg[f'{lbl}_hit'].mean()*100:5.1f}%  EV "
                              f"{gg[f'{lbl}_out'].mean():+7.3f} "
                              f"{ci(lo_, hi_)}  ({nms})")

    print("\n" + "=" * 100)
    print("BATTERY (Law-2 flag: risk is coupled to tf_won — 1m stops are "
          "structurally tighter; cross-TF EV is R-denominator-coupled)")
    print("=" * 100)
    print("  MFE-in-R (stop-bounded) per mech (all windows' rows as "
          "counts):")
    for mech in MECHS:
        g = B[B.mech == mech]
        m = g.mfe_r
        print(f"     {mech} n={len(g):4d}  p25 {m.quantile(.25):5.2f}  "
              f"p50 {m.median():5.2f}  p75 {m.quantile(.75):5.2f}  "
              f"p90 {m.quantile(.9):5.2f}  P(>=2R) {(m>=2).mean()*100:4.1f}%")
    print("  risk (pts) by tf_won: " + "  ".join(
        f"{tf}m med {B[B.tf_won == tf].risk.median():.1f}"
        for tf in (1, 2, 3)))
    print("  EV by tf_won (FLAGGED, not interpreted): " + "  ".join(
        f"{tf}m M1 {B[(B.tf_won==tf)&(B.mech=='M1')].m1_out.mean():+.3f}"
        f"/M23near {B[(B.tf_won==tf)&(B.mech!='M1')].near_out.mean():+.3f}"
        for tf in (1, 2, 3)))
    print("  cost sensitivity (M1 / M2 near / M3 near):")
    for extra_ in (0.0, 0.5, 1.0):
        m1 = B[B.mech == "M1"]
        m2 = B[B.mech == "M2"]
        m3 = B[B.mech == "M3"]
        print(f"     @{0.5+extra_:3.1f}pt  M1 "
              f"{(m1.m1_out - extra_/m1.risk).mean():+.3f}   M2-near "
              f"{(m2.near_out - extra_/m2.risk).mean():+.3f}   M3-near "
              f"{(m3.near_out - extra_/m3.risk).mean():+.3f}")
    print("  clustering-X (fights/day; M1 EV / M2 near EV / M3 near EV):")
    for x in XS:
        bx = books[x]
        m1 = bx[bx.mech == "M1"]
        m2 = bx[bx.mech == "M2"]
        m3 = bx[bx.mech == "M3"]
        print(f"     X={x:4.2f}  {len(bx)/nd:5.2f}/d  "
              f"{m1.m1_out.mean():+.3f}  {m2.near_out.mean():+.3f}  "
              f"{m3.near_out.mean():+.3f}")


if __name__ == "__main__":
    main()
