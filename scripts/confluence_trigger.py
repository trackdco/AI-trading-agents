#!/usr/bin/env python3
"""CONFLUENCE TRIGGER — fresh build at 2m and 3m. REPORT-ONLY.

§1 TRIGGER, per timeframe (2m and 3m, reported separately, NEVER pooled;
   overlap between them not computed this pass):
   a TF candle closes through its OWN TF BB(20) MA in the required
   direction AND through whichever VWAP band is currently in CONFLUENCE
   with that MA — checked across ALL bands (middle, ±1, ±2, ±3) using the
   confluence work's existing stacking tolerance
   (config/strategy.yaml cluster.tolerance_points = 10.0 NQ pts, the value
   src/engine/snapshot.py reads; same at both TFs, not re-tuned).
   The qualifying band is RECORDED as data on the row, never fixed.
   POC is OPTIONAL: the base population does not require it; rows where POC
   is also in confluence with the stack are flagged so its contribution is
   testable afterward, not baked in.

§2 TWO MECHANISMS, mirrored long and short (4 setup-direction combos/TF):
   M1 REBALANCE     HTF: price displaced >=0.5*W15 beyond the 15m BB MA
                    (BR-1's displacement convention). Trigger fires back
                    TOWARD the MA. Target: the 15m MA itself, first-passage
                    (as-of previous-1m value; same-bar -> stop wins).
   M2 CONTINUATION  HTF: a 15m bar touches the 15m MA and rejects (the
                    census reject grammar); the cycle stays live until a
                    15m close through the MA. Trigger fires AWAY from the
                    MA in the original direction. No exit assumed — scored
                    against three structural targets side by side:
                    short: VWAP-1, VAL, VWAP-2  |  long: VWAP+1, VAH, VWAP+2
                    first-passage hit rate and realized R to each.

Entry: next 1m open (standing entry law; flatten gate below). Stop: the
trigger candle's extreme ± 1 tick. Levels full-session, triggers inside the
trading windows (D5). Day-clustered bootstrap from the start, seed 20260807.

    python -m scripts.confluence_trigger [--build]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUT = ROOT / "output/htf_ma_census/confluence_fit.parquet"
TFS = [2, 3]
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
BANDS = ["vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2",
         "vwap_p3", "vwap_m3"]
TICK, COST_PTS = 0.25, 0.5
SEED, DRAWS = 20260807, 2000
XS = [0.25, 0.5, 1.0, 2.0]
XDEC = 0.5
DISP = 0.5                      # M1 displacement, in W15 (BR-1 convention)
EXCL = {"no_next_open": 0, "gap_through_stop": 0, "nan_state": 0}

_m = re.search(r"tolerance_points:\s*([0-9.]+)",
               (ROOT / "config/strategy.yaml").read_text())
TOL = float(_m.group(1))        # 10.0 — the existing stacking tolerance


def in_window(hm):
    for nm, (a, b) in SESSIONS.items():
        if a <= hm <= b:
            return nm
    return None


def day_rows(bars, sess_day, tfs=TFS):
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
    vw = vwap_bands(hist)
    band_1m = {b: vw[b].reindex(idx).to_numpy() for b in BANDS}
    req = list(idx + pd.Timedelta(minutes=1))
    prof = profile_at_minutes(hist, req)
    poc_1m = prof["poc"].to_numpy()
    val_1m = prof["val"].to_numpy()
    vah_1m = prof["vah"].to_numpy()
    tgt_series = {"short": [("vwap_m1", band_1m["vwap_m1"]),
                            ("val", val_1m),
                            ("vwap_m2", band_1m["vwap_m2"])],
                  "long": [("vwap_p1", band_1m["vwap_p1"]),
                           ("vah", vah_1m),
                           ("vwap_p2", band_1m["vwap_p2"])]}

    # ---- M2 cycle state from 15m bars (reject grammar, cycle ends on a
    # 15m close through the MA). live_dir[j] = continuation direction in
    # force at 1m row j (0 = none).
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)
    live = np.zeros(N, dtype=int)
    cur = 0
    for bi in range(len(f15)):
        m = ma_at15[bi]
        b_ = f15.iloc[bi]
        if not np.isfinite(m):
            continue
        crossed = (b_.close > m) != (b_.open > m)
        rej_dn = (b_.close < m) and (b_.high >= m) and (b_.open < m)
        rej_up = (b_.close > m) and (b_.low <= m) and (b_.open > m)
        if crossed:
            cur = 0
        elif rej_dn:
            cur = -1
        elif rej_up:
            cur = +1
        a = min(pos15[bi], N)
        b2 = min(pos15[bi + 1], N) if bi + 1 < len(f15) else N
        live[a:b2] = cur

    def walk(j0, d, entry, stop, tgt_arr):
        """First-passage race: target (as-of previous-1m value) vs stop.
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

    rows = []
    for tf in tfs:
        ma_tf, _ = bb_ma_asof(hist, tf)
        ftf = hist.resample(f"{tf}min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        pos = np.clip(np.searchsorted(
            idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
            0, N - 1)
        matf_at = ma_tf.reindex(idx).to_numpy()[pos]
        fo, fc = ftf.open.to_numpy(), ftf.close.to_numpy()
        fh, fl = ftf.high.to_numpy(), ftf.low.to_numpy()
        for bi, ts in enumerate(ftf.index):
            sess = in_window(ts.hour * 60 + ts.minute)
            if sess is None:
                continue
            p = pos[bi]
            m_tf, m15, w = matf_at[bi], ma15_1m[p], w15_1m[p]
            if not (np.isfinite(m_tf) and np.isfinite(m15)
                    and np.isfinite(w) and w > 0):
                EXCL["nan_state"] += 1
                continue
            # M1 displacement is measured at the candle OPEN — the state
            # when the trigger candle began. Measuring it at the CLOSE
            # (first build) demanded the market still be >=0.5W displaced
            # AFTER the reversal candle, which the funnel showed is nearly
            # a null set (11 of 2,073 displaced candles at 2m, 0 at 3m).
            # Caught at the population stage, before any M1 outcome was
            # read. The close-displacement value stays on the row as data.
            disp_o = (fo[bi] - m15) / w
            disp = (fc[bi] - m15) / w
            for d in (+1, -1):
                # which mechanism does a d-directed trigger belong to here?
                if (-disp_o if d > 0 else disp_o) >= DISP:
                    mech = "M1"          # displaced, firing back toward MA
                elif live[p] == d:
                    mech = "M2"          # live rejection cycle, firing away
                else:
                    continue
                # ---- condition: close through OWN TF BB MA, direction d
                if not (d * (fc[bi] - m_tf) > 0 and d * (fo[bi] - m_tf) <= 0):
                    continue
                # ---- AND through a VWAP band in confluence with that MA
                qual, stack = None, 0
                for b in BANDS:
                    bv = band_1m[b][p]
                    if not np.isfinite(bv) or abs(bv - m_tf) > TOL:
                        continue
                    stack += 1
                    thru = (d * (fc[bi] - bv) > 0 and d * (fo[bi] - bv) <= 0)
                    if thru and (qual is None
                                 or abs(bv - m_tf) < abs(qual[1] - m_tf)):
                        qual = (b, bv)
                if qual is None:
                    continue
                j0 = int(np.searchsorted(idx.values, ts.to_datetime64()))
                if j0 >= N:
                    EXCL["no_next_open"] += 1
                    continue
                entry = float(op[j0])
                stop = (fl[bi] - TICK) if d > 0 else (fh[bi] + TICK)
                if d * (entry - stop) <= 0:
                    EXCL["gap_through_stop"] += 1
                    continue
                risk = abs(entry - stop)
                pocv = poc_1m[p]
                rec = {"sess_day": sess_day, "t": ts, "tf": tf, "mech": mech,
                       "direction": d, "dir": "long" if d > 0 else "short",
                       "session": sess, "entry": entry, "stop": stop,
                       "risk": risk, "w15": w, "disp_w": disp_o,
                       "disp_close_w": disp,
                       "qual_band": qual[0], "qual_px": qual[1],
                       "n_stack": stack,
                       "poc_conf": bool(np.isfinite(pocv)
                                        and abs(pocv - m_tf) <= TOL)}
                if mech == "M1":
                    hit, out, mfe = walk(j0, d, entry, stop, ma15_1m)
                    rec.update({"m1_hit": hit, "m1_out": out, "mfe_r": mfe,
                                "m1_dist_r": d * (m15 - entry) / risk})
                else:
                    mfe_all = 0.0
                    for lbl, (nm, arr) in zip(
                            ("t1", "t2", "t3"),
                            tgt_series["long" if d > 0 else "short"]):
                        hit, out, mfe = walk(j0, d, entry, stop, arr)
                        tv = arr[p]
                        rec.update({f"{lbl}_name": nm, f"{lbl}_hit": hit,
                                    f"{lbl}_out": out,
                                    f"{lbl}_dist_r": (d * (tv - entry) / risk)
                                    if np.isfinite(tv) else np.nan})
                        mfe_all = max(mfe_all, mfe)
                    rec["mfe_r"] = mfe_all
                rows.append(rec)
    return rows


# --------------------------------------------------------- clustering ----
def cluster(F, bars, x):
    """First-of-fight per (day, tf, mech, dir): consecutive triggers are one
    fight unless price left the EARLIER row's qualifying-band price by
    >= x*W15 between them (fixed-ref convention, as cluster_sweepb)."""
    key = {}
    for day, D in F.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0)
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        for grp, g in D.groupby(["tf", "mech", "dir"]):
            g = g.sort_values("t")
            ts = g.t.tolist()
            rp = g.qual_px.tolist()
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
    for (day, tf, mech, dr), g in F.groupby(["sess_day", "tf", "mech",
                                             "dir"], sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, (tf, mech, dr), t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{tf}:{mech}:{dr}:S{cid}"
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
    """T1 flatten: rebuild with all post-decision bars flattened; the row's
    entry must equal the flat value (and move vs the real run somewhere)."""
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
            mt = [x for x in day_rows(wf, day, tfs=[r["tf"]])
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
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END]

    print("=" * 100)
    print(f"CONFLUENCE TRIGGER — fresh build, 2m and 3m, reported "
          f"separately. REPORT ONLY.")
    print(f"stacking tolerance = {TOL} pts (config/strategy.yaml "
          f"cluster.tolerance_points — the existing confluence value, "
          f"same at both TFs)")
    print("=" * 100)

    print("\nENTRY GATE (before anything is read):")
    if not gate(bars, days[::60]):
        sys.exit(1)

    if "--build" in sys.argv or not OUT.exists():
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d))
            if k % 40 == 0:
                print(f"  {k}/{len(days)}...", flush=True)
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(F):,} rows) | excl {EXCL}")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)
    nd = len(days)

    books = {x: cluster(F, bars, x) for x in XS}
    B = books[XDEC]

    for tf in TFS:
        print("\n" + "=" * 100)
        print(f"TF = {tf}m   (never pooled with the other timeframe; "
              f"overlap not computed this pass)")
        print("=" * 100)
        Bt = B[B.tf == tf]
        Ft = F[F.tf == tf]

        print(f"\n§1 POPULATION — raw {len(Ft)}, first-of-fight "
              f"{len(Bt)} ({len(Bt)/nd:.2f}/day) at X={XDEC}W")
        print("   qualifying band (recorded, not fixed):")
        q = Bt.qual_band.value_counts()
        print("      " + "  ".join(f"{b}:{q.get(b, 0)}" for b in BANDS))
        print(f"   stack size n_bands within {TOL}pt of the TF MA: "
              + "  ".join(f"{k}:{v}" for k, v in
                          sorted(Bt.n_stack.value_counts().items())))
        print(f"   POC in confluence (flag, NOT required): "
              f"{Bt.poc_conf.mean()*100:.1f}% of rows")

        print(f"\n§2 M1 REBALANCE — first-passage to the 15m MA "
              f"(same-bar -> stop wins)")
        print(f"   {'dir':6s} {'n':>4s} {'/day':>6s} {'medD(R)':>8s} "
              f"{'hit%':>6s} {'EV':>8s} {'day-boot 95%':>20s}  "
              f"POC-flag split (EV flag / no-flag)")
        for dr in ("long", "short"):
            g = Bt[(Bt.mech == "M1") & (Bt.dir == dr)]
            if len(g) < 10:
                print(f"   {dr:6s} {len(g):4d}  THIN")
                continue
            lo_, hi_ = dboot(g, "m1_out")
            gp, gn = g[g.poc_conf], g[~g.poc_conf]
            ps = (f"{gp.m1_out.mean():+.3f} ({len(gp)}) / "
                  f"{gn.m1_out.mean():+.3f} ({len(gn)})"
                  if len(gp) >= 10 and len(gn) >= 10 else "thin")
            print(f"   {dr:6s} {len(g):4d} {len(g)/nd:6.2f} "
                  f"{g.m1_dist_r.median():8.2f} {g.m1_hit.mean()*100:5.1f}% "
                  f"{g.m1_out.mean():+8.3f} [{lo_:+.3f},{hi_:+.3f}]"
                  f"{'!' if lo_ > 0 else ' '}  {ps}")

        print(f"\n§2 M2 CONTINUATION — no exit assumed; three structural "
              f"targets side by side")
        for dr in ("long", "short"):
            g = Bt[(Bt.mech == "M2") & (Bt.dir == dr)]
            print(f"   -- {dr}  n={len(g)}  {len(g)/nd:.2f}/day")
            if len(g) < 10:
                print("      THIN")
                continue
            for lbl in ("t1", "t2", "t3"):
                nm = g[f"{lbl}_name"].iloc[0]
                lo_, hi_ = dboot(g, f"{lbl}_out")
                print(f"      {nm:8s} medD {g[f'{lbl}_dist_r'].median():6.2f}R"
                      f"  hit {g[f'{lbl}_hit'].mean()*100:5.1f}%  EV "
                      f"{g[f'{lbl}_out'].mean():+8.3f} "
                      f"[{lo_:+.3f},{hi_:+.3f}]{'!' if lo_ > 0 else ''}")

        print(f"\n§3 BATTERY")
        print(f"   MFE-in-R (bounded by stop), per mech x dir:")
        for mech in ("M1", "M2"):
            for dr in ("long", "short"):
                g = Bt[(Bt.mech == mech) & (Bt.dir == dr)]
                if len(g) < 10:
                    continue
                m = g.mfe_r
                print(f"      {mech} {dr:6s} n={len(g):4d}  p25 "
                      f"{m.quantile(.25):5.2f}  p50 {m.median():5.2f}  p75 "
                      f"{m.quantile(.75):5.2f}  p90 {m.quantile(.9):5.2f}  "
                      f"P(>=2R) {(m >= 2).mean()*100:4.1f}%")
        print(f"   clustering-X sensitivity (n/day, and M1 EV / M2 t1-hit%):")
        for x in XS:
            bx = books[x]
            bt = bx[bx.tf == tf]
            m1 = bt[bt.mech == "M1"]
            m2 = bt[bt.mech == "M2"]
            print(f"      X={x:4.2f}  n/day {len(bt)/nd:5.2f}  "
                  f"M1 EV {m1.m1_out.mean():+.3f} (n={len(m1)})  "
                  f"M2 t1-hit {m2.t1_hit.mean()*100:5.1f}% (n={len(m2)})")
        print(f"   cost sensitivity (M1 EV; M2 t1 EV) at 0.5/1.0/1.5pt:")
        m1 = Bt[Bt.mech == "M1"]
        m2 = Bt[Bt.mech == "M2"]
        for extra in (0.0, 0.5, 1.0):
            print(f"      @{0.5+extra:3.1f}pt  M1 "
                  f"{(m1.m1_out - extra/m1.risk).mean():+.3f}   M2-t1 "
                  f"{(m2.t1_out - extra/m2.risk).mean():+.3f}")

        print(f"\n   per-session breakdown (compact; no session verdicts "
              f"drawn):")
        for s in SESSIONS:
            g = Bt[Bt.session == s]
            m1 = g[g.mech == "M1"]
            m2 = g[g.mech == "M2"]
            print(f"      {s:7s} n/day {len(g)/nd:5.2f} | M1 n={len(m1):4d} "
                  f"EV {m1.m1_out.mean() if len(m1) else float('nan'):+.3f} | "
                  f"M2 n={len(m2):4d} t1-hit "
                  f"{m2.t1_hit.mean()*100 if len(m2) else float('nan'):5.1f}%")


if __name__ == "__main__":
    main()
