#!/usr/bin/env python3
"""TRIGGER RACE CENSUS — redeclared grammar, COUNTS ONLY (no outcomes).

Declaration: docs/DECLARATIONS-trigger-race.md (written before this run).

Thesis (15m): M1 displacement / M2 rejection episode / M3 break episode.
Affirmation: >=1 menu structure within TOLW*W15 of the 15m MA (M2/M3 only;
M1 self-affirming). Menu: POC, VWAP mid, VWAP +/-1, +/-2, VAL, VAH.
Entry: FIRST close through own BB(20) MA across the admissible TF race
{1m, 2m, 3m}; 1m admissible only when affirmation count >= 2. Winning TF
recorded as data. No band-pierce requirement.

    python -m scripts.trigger_race_census [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUT = ROOT / "output/htf_ma_census/race_fit.parquet"
TFS = [1, 2, 3]
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
MENU = ["poc", "vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2",
        "val", "vah"]
TOLW = 0.10                     # declared affirmation-zone tolerance, in W15
TOL_SWEEP = [0.05, 0.10, 0.15, 0.20]
DISP = 0.5                      # M1 displacement, in W15 (BR-1 convention)
XDEC = 0.5                      # first-of-fight clustering, in W15
MECHS = ["M1", "M2", "M3"]
DIAG = {}                       # funnel at the DECLARED tol, per (mech, win)


def _diag(mech, win, stage, k=1):
    d = DIAG.setdefault((mech, win), {"armed": 0, "affirmed": 0, "raw": 0})
    d[stage] += k


def in_window(hm):
    for nm, (a, b) in SESSIONS.items():
        if a <= hm <= b:
            return nm
    return None


def day_rows(bars, sess_day, tols=TOL_SWEEP, funnel=False):
    """All raw triggers for one session-day, at every tolerance in `tols`
    (rows carry a `tol` field). Counts only — no outcome walks."""
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
    cl, op = seg.close.to_numpy(), seg.open.to_numpy()
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    vw = vwap_bands(hist)
    req = list(idx + pd.Timedelta(minutes=1))
    prof = profile_at_minutes(hist, req)
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"):
        S[b] = vw[b].reindex(idx).to_numpy()

    # affirmation count per 1m row, per tolerance (state, anchored on the
    # 15m MA, width-relative)
    dist = np.stack([np.abs(S[k] - ma15_1m) for k in MENU])       # 8 x N
    aff = {}
    for tol in tols:
        ok = dist <= tol * w15_1m
        aff[tol] = np.where(np.isfinite(w15_1m) & (w15_1m > 0),
                            np.nansum(ok, axis=0), 0).astype(int)
    which = {tol: (dist <= tol * w15_1m) for tol in tols}          # per row

    # ---- M2 / M3 episode state from 15m bars (same grammar as published)
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
        crossed = (b_.close > m) != (b_.open > m)
        if crossed:
            cur2 = 0
            cur3 = 1 if b_.close > m else -1
        elif (b_.close < m) and (b_.high >= m) and (b_.open < m):
            cur2 = -1
        elif (b_.close > m) and (b_.low <= m) and (b_.open > m):
            cur2 = +1
        a = min(pos15[bi], N)
        b2 = min(pos15[bi + 1], N) if bi + 1 < len(f15) else N
        live2[a:b2] = cur2
        live3[a:b2] = cur3

    # ---- funnel (declared tol only): armed / affirmed direction-minutes
    if funnel:
        hm_end = [(t + pd.Timedelta(minutes=1)) for t in idx]
        wins = np.array([in_window(t.hour * 60 + t.minute) or ""
                         for t in hm_end])
        disp_state = (cl - ma15_1m) / np.where(w15_1m > 0, w15_1m, np.nan)
        for d in (+1, -1):
            armed = {"M1": ((-disp_state if d > 0 else disp_state) >= DISP),
                     "M2": live2 == d, "M3": live3 == d}
            for mech in MECHS:
                a = armed[mech] & (wins != "")
                need = (aff[TOLW] >= 1) if mech != "M1" else np.ones(N, bool)
                for w in SESSIONS:
                    mw = a & (wins == w)
                    _diag(mech, w, "armed", int(mw.sum()))
                    _diag(mech, w, "affirmed", int((mw & need).sum()))

    # ---- the race: per TF, fresh closes through the TF's OWN BB MA
    fires = {}                  # (ts_end, mech, d) -> {tf: (p, disp_o)}
    for tf in TFS:
        ma_tf, _ = bb_ma_asof(hist, tf)
        if tf == 1:
            ftf = seg.copy()
            ftf.index = ftf.index + pd.Timedelta(minutes=1)   # right label
        else:
            ftf = hist.resample(f"{tf}min", label="right",
                                closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        pos = np.clip(np.searchsorted(
            idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
            0, N - 1)
        matf_at = ma_tf.reindex(idx).to_numpy()[pos]
        fo, fc = ftf.open.to_numpy(), ftf.close.to_numpy()
        for bi, ts in enumerate(ftf.index):
            sess = in_window(ts.hour * 60 + ts.minute)
            if sess is None:
                continue
            p = pos[bi]
            m_tf, m15, w = matf_at[bi], ma15_1m[p], w15_1m[p]
            if not (np.isfinite(m_tf) and np.isfinite(m15)
                    and np.isfinite(w) and w > 0):
                continue
            disp_o = (fo[bi] - m15) / w
            for d in (+1, -1):
                if not (d * (fc[bi] - m_tf) > 0
                        and d * (fo[bi] - m_tf) <= 0):
                    continue        # no fresh close through own MA
                if (-disp_o if d > 0 else disp_o) >= DISP:
                    mech = "M1"
                elif live2[p] == d:
                    mech = "M2"
                elif live3[p] == d:
                    mech = "M3"
                else:
                    continue
                fires.setdefault((ts, mech, d), {})[tf] = (p, disp_o, sess)

    # ---- collapse simultaneous closes; apply affirmation + 1m gates
    rows = []
    for (ts, mech, d), by_tf in sorted(fires.items()):
        for tol in tols:
            adm = []
            for tf, (p, disp_o, sess) in sorted(by_tf.items()):
                n_aff = int(aff[tol][p])
                if mech != "M1" and n_aff < 1:
                    continue                 # M2/M3 need >=1 affirmation
                if tf == 1 and n_aff < 2:
                    continue                 # 1m only on double confirmation
                adm.append((tf, p, disp_o, sess, n_aff))
            if not adm:
                continue
            tf, p, disp_o, sess, n_aff = adm[0]      # smallest TF wins tie
            if tol == TOLW and funnel:
                _diag(mech, sess, "raw")
            rows.append({
                "sess_day": sess_day, "t": ts, "tol": tol, "mech": mech,
                "direction": d, "dir": "long" if d > 0 else "short",
                "session": sess, "tf_won": tf,
                "tie_tfs": ",".join(str(x[0]) for x in adm),
                "n_aff": n_aff,
                "aff_list": ",".join(k for i, k in enumerate(MENU)
                                     if which[tol][i, p]),
                "m1_admissible": bool(n_aff >= 2),
                "w15": float(w15_1m[p]), "ma15": float(ma15_1m[p]),
                "close_px": float(cl[p]), "disp_w": float(disp_o)})
    return rows


def cluster(F, bars, x=XDEC):
    """First-of-fight per (day, mech, dir) — ONE stream across TFs.
    Fixed-ref: new fight only if price left the EARLIER trigger's 15m MA
    by >= x*W15 between the two triggers."""
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


def gate(bars, days):
    """Integrity probe: flatten all bars after a sampled trigger's time;
    the trigger set at or before that time must be unchanged."""
    bad = n = 0
    for day in days:
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        win = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        rows = [r for r in day_rows(win, day, tols=[TOLW])]
        if not rows:
            continue
        for r in rows[:1] + rows[len(rows) // 2:len(rows) // 2 + 1]:
            t = pd.Timestamp(r["t"])
            prior = win[win.index < t]
            if prior.empty:
                continue
            pc = float(prior.close.iloc[-1])
            wf = win.copy()
            m = wf.index >= t
            wf.loc[m, ["open", "high", "low", "close"]] = pc
            wf.loc[m, "volume"] = 1
            re = [x for x in day_rows(wf, day, tols=[TOLW])
                  if pd.Timestamp(x["t"]) <= t]
            og = [x for x in rows if pd.Timestamp(x["t"]) <= t]
            n += 1
            same = (len(re) == len(og) and all(
                a["t"] == b["t"] and a["mech"] == b["mech"]
                and a["dir"] == b["dir"] and a["tf_won"] == b["tf_won"]
                and a["n_aff"] == b["n_aff"] for a, b in zip(og, re)))
            if not same:
                bad += 1
    ok = bad == 0 and n > 0
    print(f"   flatten probe: {n} probes, bad {bad} -> "
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
    nd = len(days)

    print("=" * 100)
    print("TRIGGER RACE CENSUS — redeclared grammar "
          "(docs/DECLARATIONS-trigger-race.md). COUNTS ONLY.")
    print(f"affirmation zone: {TOLW}*W15 of the 15m MA (width-relative); "
          f"sweep {TOL_SWEEP} for shape")
    print(f"entry race {TFS} — 1m admissible only at >=2 affirmations; "
          f"windows unchanged; fit {FIT_START}..{FIT_END} ({nd} days)")
    print("=" * 100)

    print("\nINTEGRITY PROBE (before anything is read):")
    if not gate(bars, days[::60]):
        sys.exit(1)

    if "--build" in sys.argv or not OUT.exists():
        DIAG.clear()
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d, funnel=True))
            if k % 40 == 0:
                print(f"  {k}/{nd}...", flush=True)
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        np.save(OUT.with_suffix(".funnel.npy"), np.array([DIAG]),
                allow_pickle=True)
        print(f"written: {OUT.name} ({len(F):,} rows across "
              f"{len(TOL_SWEEP)} tolerances)")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)
    FUNNEL = np.load(OUT.with_suffix(".funnel.npy"),
                     allow_pickle=True)[0] if \
        OUT.with_suffix(".funnel.npy").exists() else {}

    B = {tol: cluster(F[F.tol == tol].copy(), bars) for tol in TOL_SWEEP}
    Bd = B[TOLW]

    print("\n" + "=" * 100)
    print(f"MAIN COUNTS at the DECLARED {TOLW}W — per window x thesis, "
          f"one race stream across TFs")
    print("=" * 100)
    print(f"   {'window':7s} {'mech':4s} {'armed-min/d':>11s} "
          f"{'affirmed/d':>10s} {'raw/d':>6s} {'fights/d':>8s} "
          f"{'fights':>6s}   tf_won 1/2/3   n_aff 1/2/3+   1m-adm%")
    for w in SESSIONS:
        for mech in MECHS:
            g = Bd[(Bd.session == w) & (Bd.mech == mech)]
            gr = F[(F.tol == TOLW) & (F.session == w) & (F.mech == mech)]
            fn = FUNNEL.get((mech, w), {})
            tfw = g.tf_won.value_counts()
            na = g.n_aff.clip(upper=3).value_counts()
            print(f"   {w:7s} {mech:4s} {fn.get('armed', 0)/nd:11.1f} "
                  f"{fn.get('affirmed', 0)/nd:10.1f} {len(gr)/nd:6.2f} "
                  f"{len(g)/nd:8.2f} {len(g):6d}   "
                  f"{tfw.get(1, 0):3d}/{tfw.get(2, 0):3d}/{tfw.get(3, 0):3d}"
                  f"   {na.get(1, 0):3d}/{na.get(2, 0):3d}/{na.get(3, 0):3d}"
                  f"   {g.m1_admissible.mean()*100 if len(g) else 0:5.1f}%")
        g = Bd[Bd.session == w]
        print(f"   {w:7s} ALL  fights/day {len(g)/nd:.2f}  ({len(g)})")
    print(f"   TOTAL fights/day {len(Bd)/nd:.2f}  ({len(Bd)} fights, "
          f"{nd} days)")

    print(f"\n   affirming structures on fights (declared tol): ")
    from collections import Counter
    c = Counter()
    for s in Bd.aff_list:
        for k in str(s).split(","):
            if k:
                c[k] += 1
    print("      " + "  ".join(f"{k}:{v}" for k, v in c.most_common()))

    print("\n" + "=" * 100)
    print("TOLERANCE SWEEP — shape only, nothing picked (fights/day)")
    print("=" * 100)
    print(f"   {'tolW':>5s} " + " ".join(f"{w:>13s}" for w in SESSIONS)
          + f" {'TOTAL':>8s}   per-mech total M1/M2/M3")
    for tol in TOL_SWEEP:
        bt = B[tol]
        mc = bt.mech.value_counts()
        cells = " ".join(
            f"{len(bt[bt.session == w])/nd:13.2f}" for w in SESSIONS)
        print(f"   {tol:5.2f} {cells} {len(bt)/nd:8.2f}   "
              f"{mc.get('M1', 0)/nd:.2f}/{mc.get('M2', 0)/nd:.2f}"
              f"/{mc.get('M3', 0)/nd:.2f}")

    print("\n" + "=" * 100)
    print("DECAY CHECK at the declared tol — the width-relative "
          "restatement should flatten the flat-10pt collapse")
    print("=" * 100)
    half = nd // 2
    h1, h2 = set(days[:half]), set(days[half:])
    a = Bd[Bd.sess_day.isin(h1)]
    b = Bd[Bd.sess_day.isin(h2)]
    print(f"   fights/day: first half {len(a)/half:.2f}   second half "
          f"{len(b)/(nd-half):.2f}   (old flat-10pt census: 2.36 -> 1.86 "
          f"raw at 2m)")
    mon = Bd.assign(m=Bd.sess_day.str[:7]).groupby("m").size()
    print("   monthly fights: " + "  ".join(
        f"{m[2:]}:{v}" for m, v in mon.items()))


if __name__ == "__main__":
    main()
