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

§2 THREE MECHANISMS, mirrored long and short (6 setup-direction combos/TF),
   priority M1 > M2 > M3 when HTF states overlap (overlaps recorded as
   flags on the row). EVERYTHING reported split by session — LONDON,
   NY_PRE, NY_AM — never pooled. Raw diagnostic funnel counts reported
   alongside the joined confluence counts.
   M1 REBALANCE     HTF: price displaced >=0.5*W15 beyond the 15m BB MA
                    (BR-1's displacement convention). Trigger fires back
                    TOWARD the MA. Scored against BOTH rebalance targets
                    SEPARATELY, side by side, never pooled or averaged:
                    the 15m BB MA and the 1-HOUR BB MA, each its own
                    first-passage race (as-of previous-1m value; same-bar
                    -> stop wins).
   M2 CONTINUATION  HTF: a 15m bar touches the 15m MA and rejects (the
                    census reject grammar); the cycle stays live until a
                    15m close through the MA. Trigger fires AWAY from the
                    MA in the original direction. No exit assumed — scored
                    against NEAR and FAR structural targets selected
                    RELATIVE TO THE BAND THAT FIRED THE TRIGGER (fix of the
                    first build's flaw, where a fixed set put the first
                    target behind the entry):
                      fired band = VWAP middle -> near VWAP-/+1, far VWAP-/+2
                      fired band = VWAP-/+1     -> near VAL/VAH,  far VWAP-/+2
                      any other fired band      -> next two bands in the
                                                  trade direction (recorded)
                    first-passage hit rate and realized R to each.
   M3 BREAK         HTF: a 15m candle CLOSES THROUGH its own MA — that
                    close opens a break episode in the break direction,
                    live until the next 15m cross. The break candle's
                    closeloc (oriented by break direction) is recorded on
                    every row; the "high closeloc" threshold is SWEPT at
                    report time ({None, 0.5, 0.6, 0.7, 0.8}), never fixed
                    in advance. Entry is the same confluence trigger,
                    firing in the break's direction; scored against the
                    same band-relative NEAR/FAR targets as M2.

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
CL_SWEEP = [None, 0.5, 0.6, 0.7, 0.8]   # M3 break-candle closeloc thresholds
DIAG = {}                                # raw diagnostic funnel, per (tf, mech)


def _diag(tf, mech, sess, stage):
    k = (tf, mech, sess)
    DIAG.setdefault(k, {"state": 0, "ma": 0, "conf": 0, "join": 0})
    DIAG[k][stage] += 1

_m = re.search(r"tolerance_points:\s*([0-9.]+)",
               (ROOT / "config/strategy.yaml").read_text())
TOL = float(_m.group(1))        # 10.0 — the existing stacking tolerance


def in_window(hm):
    for nm, (a, b) in SESSIONS.items():
        if a <= hm <= b:
            return nm
    return None


def day_rows(bars, sess_day, tfs=TFS, tol=TOL):
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
    ma60, _ = bb_ma_asof(hist, 60)
    ma60_1m = ma60.reindex(idx).to_numpy()
    vw = vwap_bands(hist)
    band_1m = {b: vw[b].reindex(idx).to_numpy() for b in BANDS}
    req = list(idx + pd.Timedelta(minutes=1))
    prof = profile_at_minutes(hist, req)
    poc_1m = prof["poc"].to_numpy()
    val_1m = prof["val"].to_numpy()
    vah_1m = prof["vah"].to_numpy()
    BIDX = {"vwap_p3": 3, "vwap_p2": 2, "vwap_p1": 1, "vwap": 0,
            "vwap_m1": -1, "vwap_m2": -2, "vwap_m3": -3}
    BNAME = {v: k for k, v in BIDX.items()}

    def m2_targets(qband, d):
        """(near_name, near_arr, far_name, far_arr, case) — targets selected
        RELATIVE TO THE FIRED BAND, in the trade direction d."""
        k = BIDX[qband]
        if k == 0:                              # middle -> -/+1 then -/+2
            return (BNAME[d], band_1m[BNAME[d]],
                    BNAME[2 * d], band_1m[BNAME[2 * d]], "mid")
        if k == d:                              # the -/+1 on the trade side
            nm = "vah" if d > 0 else "val"
            return (nm, vah_1m if d > 0 else val_1m,
                    BNAME[2 * d], band_1m[BNAME[2 * d]], "band1")
        near_k, far_k = k + d, k + 2 * d        # any other fired band
        near = (BNAME[near_k], band_1m[BNAME[near_k]]) \
            if abs(near_k) <= 3 else (None, None)
        far = (BNAME[far_k], band_1m[BNAME[far_k]]) \
            if abs(far_k) <= 3 else (None, None)
        return near[0], near[1], far[0], far[1], "other"

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
    live3 = np.zeros(N, dtype=int)       # M3 break episode direction
    cl3 = np.full(N, np.nan)             # break candle's oriented closeloc
    cur = cur3 = 0
    curcl = np.nan
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
            # M3: a 15m close through the MA opens a break episode in the
            # break direction; the episode lives until the next cross (which
            # replaces it). closeloc oriented by break direction, recorded —
            # the threshold is SWEPT at report time, never fixed here.
            cur3 = 1 if b_.close > m else -1
            rng_ = float(b_.high - b_.low)
            curcl = (((b_.close - b_.low) / rng_) if cur3 > 0
                     else ((b_.high - b_.close) / rng_)) if rng_ > 0 else np.nan
        elif rej_dn:
            cur = -1
        elif rej_up:
            cur = +1
        a = min(pos15[bi], N)
        b2 = min(pos15[bi + 1], N) if bi + 1 < len(f15) else N
        live[a:b2] = cur
        live3[a:b2] = cur3
        cl3[a:b2] = curcl

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
                # priority M1 > M2 > M3 (most-specific HTF state first);
                # the other states are recorded as flags for diagnostics.
                if (-disp_o if d > 0 else disp_o) >= DISP:
                    mech = "M1"          # displaced, firing back toward MA
                elif live[p] == d:
                    mech = "M2"          # live rejection cycle, firing away
                elif live3[p] == d:
                    mech = "M3"          # live break episode, firing with it
                else:
                    continue
                _diag(tf, mech, sess, "state")
                # ---- condition: close through OWN TF BB MA, direction d
                if not (d * (fc[bi] - m_tf) > 0 and d * (fo[bi] - m_tf) <= 0):
                    continue
                _diag(tf, mech, sess, "ma")
                # ---- AND through a VWAP band in confluence with that MA
                qual, stack = None, 0
                for b in BANDS:
                    bv = band_1m[b][p]
                    if not np.isfinite(bv) or abs(bv - m_tf) > tol:
                        continue
                    stack += 1
                    thru = (d * (fc[bi] - bv) > 0 and d * (fo[bi] - bv) <= 0)
                    if thru and (qual is None
                                 or abs(bv - m_tf) < abs(qual[1] - m_tf)):
                        qual = (b, bv)
                if stack:
                    _diag(tf, mech, sess, "conf")
                if qual is None:
                    continue
                _diag(tf, mech, sess, "join")
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
                                        and abs(pocv - m_tf) <= tol),
                       "htf_m2_live": bool(live[p] == d),
                       "htf_m3_live": bool(live3[p] == d),
                       "brk_closeloc": float(cl3[p])
                       if live3[p] == d else np.nan}
                if mech == "M1":
                    # BOTH rebalance targets, separately — never pooled:
                    # the 15m MA and the 1-hour MA, each its own race.
                    hit, out, mfe = walk(j0, d, entry, stop, ma15_1m)
                    h60, o60, mfe60 = walk(j0, d, entry, stop, ma60_1m)
                    m60 = ma60_1m[p]
                    rec.update({"m1_hit": hit, "m1_out": out,
                                "m1_dist_r": d * (m15 - entry) / risk,
                                "m1h_hit": h60, "m1h_out": o60,
                                "m1h_dist_r": (d * (m60 - entry) / risk)
                                if np.isfinite(m60) else np.nan,
                                "mfe_r": max(mfe, mfe60)})
                else:
                    nn, na, fn, fa, case = m2_targets(qual[0], d)
                    rec["tgt_case"] = case
                    mfe_all = 0.0
                    for lbl, nm, arr in (("near", nn, na), ("far", fn, fa)):
                        if nm is None:
                            rec.update({f"{lbl}_name": None,
                                        f"{lbl}_hit": False,
                                        f"{lbl}_out": np.nan,
                                        f"{lbl}_dist_r": np.nan})
                            continue
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

    FUNNEL = {}
    if "--build" in sys.argv or not OUT.exists():
        DIAG.clear()                    # gate() ran day_rows; drop its counts
        for k in EXCL:
            EXCL[k] = 0
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d))
            if k % 40 == 0:
                print(f"  {k}/{len(days)}...", flush=True)
        FUNNEL = {k: dict(v) for k, v in DIAG.items()}
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(F):,} rows) | excl {EXCL}")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)
    nd = len(days)

    books = {x: cluster(F, bars, x) for x in XS}
    B = books[XDEC]
    SESS = list(SESSIONS)
    MECHS = ["M1", "M2", "M3"]

    def ci(lo_, hi_):
        return (f"[{lo_:+.3f},{hi_:+.3f}]" if np.isfinite(lo_)
                else "[thin: <3 days]")

    for tf in TFS:
        print("\n" + "=" * 100)
        print(f"TF = {tf}m   (never pooled with the other timeframe; "
              f"overlap not computed this pass)")
        print("=" * 100)
        Bt = B[B.tf == tf]
        Ft = F[F.tf == tf]

        print(f"\n§0 RAW DIAGNOSTIC FUNNEL — raw {tf}m-candle counts on the "
              f"build pass, pre-clustering, per session.")
        print(f"   stages: HTF state live at the candle -> + closes through "
              f"own {tf}m MA -> + that MA has >=1 VWAP band")
        print(f"   within {TOL:.0f}pt (confluence exists) -> + the close is "
              f"through the stacked band too (JOINED trigger).")
        if FUNNEL:
            print(f"   {'mech':4s} {'session':7s} {'state':>8s} {'ma':>7s} "
                  f"{'conf':>7s} {'join':>7s}")
            for mech in MECHS:
                tot = {"state": 0, "ma": 0, "conf": 0, "join": 0}
                for s in SESS:
                    c = FUNNEL.get((tf, mech, s))
                    if not c:
                        continue
                    for k2 in tot:
                        tot[k2] += c[k2]
                    print(f"   {mech:4s} {s:7s} {c['state']:8,d} "
                          f"{c['ma']:7,d} {c['conf']:7,d} {c['join']:7,d}")
                print(f"   {mech:4s} {'SUM':7s} {tot['state']:8,d} "
                      f"{tot['ma']:7,d} {tot['conf']:7,d} {tot['join']:7,d}"
                      f"   (arithmetic total, not a pooled verdict)")
        else:
            print("   (funnel is recorded on --build passes only; this run "
                  "read the existing parquet)")

        print(f"\n§1 POPULATION — raw {len(Ft)}, first-of-fight "
              f"{len(Bt)} ({len(Bt)/nd:.2f}/day) at X={XDEC}W; per session:")
        for s in SESS:
            fs, bs = Ft[Ft.session == s], Bt[Bt.session == s]
            mc = bs.mech.value_counts()
            print(f"   {s:7s} raw {len(fs):4d}   fof {len(bs):4d} "
                  f"({len(bs)/nd:5.2f}/day)   "
                  + "  ".join(f"{m}:{mc.get(m, 0)}" for m in MECHS))
        q = Bt.qual_band.value_counts()
        print("   qualifying band (recorded, not fixed): "
              + "  ".join(f"{b}:{q.get(b, 0)}" for b in BANDS))
        print(f"   POC in confluence (flag, NOT required): "
              f"{Bt.poc_conf.mean()*100:.1f}% of rows")

        print(f"\n§2 M1 REBALANCE — BOTH targets side by side, each its own "
              f"first-passage race (same-bar -> stop wins);")
        print(f"   never pooled, never averaged. Sessions never pooled.")
        for s in SESS:
            for dr in ("long", "short"):
                g = Bt[(Bt.mech == "M1") & (Bt.session == s)
                       & (Bt.dir == dr)]
                if len(g) == 0:
                    print(f"   {s:7s} {dr:6s} n=  0")
                    continue
                thin = "   THIN" if len(g) < 10 else ""
                print(f"   {s:7s} {dr:6s} n={len(g):3d} "
                      f"({len(g)/nd:.2f}/day){thin}")
                for lbl, hitc, outc, distc in (
                        ("15m MA", "m1_hit", "m1_out", "m1_dist_r"),
                        ("60m MA", "m1h_hit", "m1h_out", "m1h_dist_r")):
                    lo_, hi_ = dboot(g, outc)
                    print(f"      {lbl:7s} medD {g[distc].median():5.2f}R  "
                          f"hit {g[hitc].mean()*100:5.1f}%  EV "
                          f"{g[outc].mean():+7.3f} {ci(lo_, hi_)}")

        print(f"\n§2 M2 CONTINUATION — live episode until a 15m close "
              f"through the MA; NEAR/FAR relative to the FIRED band.")
        for s in SESS:
            for dr in ("long", "short"):
                g = Bt[(Bt.mech == "M2") & (Bt.session == s)
                       & (Bt.dir == dr)]
                cases = "  ".join(f"{k}:{v}" for k, v in
                                  g.tgt_case.value_counts().items())
                thin = "   THIN" if len(g) < 10 else ""
                print(f"   {s:7s} {dr:6s} n={len(g):3d} "
                      f"({len(g)/nd:.2f}/day)  {cases}{thin}")
                if len(g) == 0:
                    continue
                for lbl in ("near", "far"):
                    gg = g[g[f"{lbl}_name"].notna()]
                    if len(gg) == 0:
                        continue
                    lo_, hi_ = dboot(gg, f"{lbl}_out")
                    print(f"      {lbl:5s} medD "
                          f"{gg[f'{lbl}_dist_r'].median():5.2f}R  hit "
                          f"{gg[f'{lbl}_hit'].mean()*100:5.1f}%  EV "
                          f"{gg[f'{lbl}_out'].mean():+7.3f} {ci(lo_, hi_)}")

        print(f"\n§2 M3 BREAK — a 15m close through its own MA opens the "
              f"episode (lives until the next cross);")
        print(f"   entry = the same confluence trigger, in the break's "
              f"direction. Targets as M2 (near/far vs fired band).")
        print(f"   Break candle's oriented closeloc recorded on every row; "
              f"threshold SWEPT below, never fixed.")
        for s in SESS:
            for dr in ("long", "short"):
                g = Bt[(Bt.mech == "M3") & (Bt.session == s)
                       & (Bt.dir == dr)]
                cases = "  ".join(f"{k}:{v}" for k, v in
                                  g.tgt_case.value_counts().items())
                thin = "   THIN" if len(g) < 10 else ""
                print(f"   {s:7s} {dr:6s} n={len(g):3d} "
                      f"({len(g)/nd:.2f}/day)  {cases}{thin}")
                if len(g) == 0:
                    continue
                for lbl in ("near", "far"):
                    gg = g[g[f"{lbl}_name"].notna()]
                    if len(gg) == 0:
                        continue
                    lo_, hi_ = dboot(gg, f"{lbl}_out")
                    print(f"      {lbl:5s} medD "
                          f"{gg[f'{lbl}_dist_r'].median():5.2f}R  hit "
                          f"{gg[f'{lbl}_hit'].mean()*100:5.1f}%  EV "
                          f"{gg[f'{lbl}_out'].mean():+7.3f} {ci(lo_, hi_)}")
        print(f"   closeloc-threshold sweep (break candle's closeloc >= thr, "
              f"oriented by break direction; 'none' = all M3;")
        print(f"   directions pooled for SHAPE only — sessions stay split):")
        print(f"   {'session':7s} {'thr':>5s} {'n':>4s} {'/day':>6s} "
              f"{'near-hit':>9s} {'near-EV':>8s} {'far-hit':>8s} "
              f"{'far-EV':>8s}")
        for s in SESS:
            gs = Bt[(Bt.mech == "M3") & (Bt.session == s)]
            for thr in CL_SWEEP:
                g = gs if thr is None else gs[gs.brk_closeloc >= thr]
                tag = "none" if thr is None else f"{thr:.1f}"
                if len(g) == 0:
                    print(f"   {s:7s} {tag:>5s}    0")
                    continue
                print(f"   {s:7s} {tag:>5s} {len(g):4d} {len(g)/nd:6.2f} "
                      f"{g.near_hit.mean()*100:8.1f}% "
                      f"{g.near_out.mean():+8.3f} "
                      f"{g.far_hit.mean()*100:7.1f}% "
                      f"{g.far_out.mean():+8.3f}")

        print(f"\n§3 BATTERY (compact)")
        print(f"   MFE-in-R (bounded by stop), per mech x dir, all sessions' "
              f"rows listed together as counts:")
        for mech in MECHS:
            for dr in ("long", "short"):
                g = Bt[(Bt.mech == mech) & (Bt.dir == dr)]
                if len(g) < 10:
                    continue
                m = g.mfe_r
                print(f"      {mech} {dr:6s} n={len(g):4d}  p25 "
                      f"{m.quantile(.25):5.2f}  p50 {m.median():5.2f}  p75 "
                      f"{m.quantile(.75):5.2f}  p90 {m.quantile(.9):5.2f}  "
                      f"P(>=2R) {(m >= 2).mean()*100:4.1f}%")
        print(f"   clustering-X sensitivity (n/day; M1 15m-EV / M2 near-hit "
              f"/ M3 near-hit):")
        for x in XS:
            bx = books[x]
            bt = bx[bx.tf == tf]
            m1 = bt[bt.mech == "M1"]
            m2 = bt[bt.mech == "M2"]
            m3 = bt[bt.mech == "M3"]
            print(f"      X={x:4.2f}  n/day {len(bt)/nd:5.2f}  "
                  f"M1 EV {m1.m1_out.mean():+.3f} (n={len(m1)})  "
                  f"M2 near-hit {m2.near_hit.mean()*100:5.1f}% (n={len(m2)})  "
                  f"M3 near-hit {m3.near_hit.mean()*100:5.1f}% (n={len(m3)})")
        print(f"   cost sensitivity (M1 15m-EV / M1 60m-EV / M2 near / "
              f"M3 near) at 0.5/1.0/1.5pt:")
        m1 = Bt[Bt.mech == "M1"]
        m2 = Bt[Bt.mech == "M2"]
        m3 = Bt[Bt.mech == "M3"]
        for extra in (0.0, 0.5, 1.0):
            print(f"      @{0.5+extra:3.1f}pt  M1-15m "
                  f"{(m1.m1_out - extra/m1.risk).mean():+.3f}  M1-60m "
                  f"{(m1.m1h_out - extra/m1.risk).mean():+.3f}  M2-near "
                  f"{(m2.near_out - extra/m2.risk).mean():+.3f}  M3-near "
                  f"{(m3.near_out - extra/m3.risk).mean():+.3f}")

    # ---- FREQUENCY, restated with the construction complete --------------
    print("\n" + "=" * 100)
    print("FREQUENCY — the full construction is now in (M1 rebalance + M2 "
          "episode + M3 break), split by")
    print(f"session. Tolerance stays the declared {TOL:.0f}pt — the sweep "
          "(addendum 1) showed tighter-is-better")
    print("and nothing here touches it. THIS is the table for any future "
          "loosening conversation.")
    print("=" * 100)
    print(f"   {'tf':>3s} {'session':7s} {'M1/day':>7s} {'M2/day':>7s} "
          f"{'M3/day':>7s} {'all/day':>8s}")
    for tf in TFS:
        Bt = B[B.tf == tf]
        for s in SESS:
            g = Bt[Bt.session == s]
            mc = g.mech.value_counts()
            print(f"   {tf:3d} {s:7s} {mc.get('M1', 0)/nd:7.2f} "
                  f"{mc.get('M2', 0)/nd:7.2f} {mc.get('M3', 0)/nd:7.2f} "
                  f"{len(g)/nd:8.2f}")
        print(f"   {tf:3d} {'TOTAL':7s} — {len(Bt)} fights over {nd} days "
              f"= {len(Bt)/nd:.2f}/day across the three windows")


if __name__ == "__main__":
    main()
