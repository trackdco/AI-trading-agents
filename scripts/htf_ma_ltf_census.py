#!/usr/bin/env python3
"""LTF TRIGGER RE-CENSUS — the conjunction (DECLARATIONS-ltf-trigger-recensus).

Trigger at TF in {1,2,3,5}:
  (A) the TF candle interacts with the locus (reject / break), AND
  (B) that same candle closes through its OWN TF BB(20) middle band in the
      trade direction.

The locus set is unchanged (7 loci). An LTF BB MA is NOT a locus — it is
momentum confirmation on the entry candle. Both (A)-only and (A)^(B) are
emitted so (B)'s MARGINAL lift can be priced (D1a).

Stages:
  --preflight   trigger counts per (TF, locus, arm, session) ONLY, no
                outcome walks, plus the TF=15 (A)-only calibration control
  (default)     full census with outcome walks

    python -m scripts.htf_ma_ltf_census --preflight
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import LOCI, level_series          # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, session_tag           # noqa: E402

TICK = 0.25
COST_PTS = 0.5
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
TFS = [1, 2, 3, 5]
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
EXCL = {"no_next_open": 0, "gap_through_stop": 0, "level_nan": 0}


def in_window(hm: int) -> str | None:
    for name, (a, b) in SESSIONS.items():
        if a <= hm <= b:
            return name
    return None


def day_triggers(bars: pd.DataFrame, sess_day: str, tfs=TFS,
                 walk: bool = True) -> list[dict]:
    """All conjunction triggers for one session, all TFs, all loci.

    LEVEL CONSTRUCTION USES THE FULL SESSION (D5): the profile is
    18:00-anchored, VWAP session-anchored, the 15m BB MA needs 20 prior
    completed 15m bars. Only the TRIGGER SEARCH is window-restricted."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    ma15, w15 = bb_ma_asof(hist, 15)
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    op = seg.open.to_numpy()
    lv = level_series(hist, idx, ma15)              # full-session levels
    w_1m = w15.reindex(idx).to_numpy()

    # trail reference stays the 15m BB MA at 15m granularity (shipped exit)
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
    ma_f15.index = f15.index

    def walk_exits(j0, d, entry, stop):
        risk = abs(entry - stop)
        if risk <= 0 or j0 >= len(idx):
            return None
        cost = COST_PTS / risk
        stop_j, t3, mfe = None, None, 0.0
        for j in range(j0, len(idx)):
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stop_j = j
                break
            fav = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
            mfe = max(mfe, fav)
            if t3 is None and fav >= 3.0:
                t3 = j
        eod = d * (cl[-1] - entry) / risk
        hold = -1.0 if stop_j is not None else eod
        tstop, trail, j_trail = stop, None, None
        fb2 = f15[f15.index > idx[j0]]
        fi, pos = list(fb2.index), 0
        for j in range(j0, len(idx)):
            if (lo[j] <= tstop) if d > 0 else (hi[j] >= tstop):
                trail = d * (tstop - entry) / risk
                j_trail = j
                break
            while pos < len(fi) and fi[pos] <= idx[j]:
                b_ = fb2.iloc[pos]
                m = ma_f15.get(fi[pos], np.nan)
                if np.isfinite(m) and d * (b_.close - m) > 0:
                    cand = (b_.low - TICK) if d > 0 else (b_.high + TICK)
                    if d * (cand - tstop) > 0:
                        tstop = cand
                pos += 1
        if trail is None:
            trail, j_trail = eod, len(idx) - 1
        leg3 = (3.0 * risk - TICK) / risk if t3 is not None else None
        ship = (0.75 * leg3 + 0.25 * trail if leg3 is not None else trail) - cost
        j_exit = stop_j if (stop_j is not None and t3 is None) else j_trail
        return {"risk": risk, "mfe_r": mfe, "out_ship": ship,
                "out_trail": trail - cost, "out_hold": hold - cost,
                "t_entry": idx[j0], "t_exit": idx[j_exit],
                "t_3r": idx[t3] if t3 is not None else pd.NaT}

    rows = []
    for tf in tfs:
        # TF candles + that TF's OWN BB MA (momentum confirmation, NOT a locus)
        if tf == 1:
            ftf = seg[["open", "high", "low", "close"]].copy()
            ftf.index = idx + pd.Timedelta(minutes=1)   # label=right
        else:
            ftf = hist.resample(f"{tf}min", label="right", closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        if len(ftf) < 25:
            continue
        ma_tf, _ = bb_ma_asof(hist, tf)
        # the TF's own BB MA as-of the candle's last completed minute
        ma_at = ma_tf.reindex(ftf.index - pd.Timedelta(minutes=1))
        ma_at.index = ftf.index
        pos_tf = np.searchsorted(idx.values,
                                 (ftf.index - pd.Timedelta(minutes=1)).values)
        pos_tf = np.clip(pos_tf, 0, len(idx) - 1)
        fo = ftf.open.to_numpy()
        fh, fl, fc = (ftf.high.to_numpy(), ftf.low.to_numpy(),
                      ftf.close.to_numpy())
        mtf = ma_at.to_numpy()

        for locus in LOCI:
            l_1m = lv[locus]
            l_at = l_1m[pos_tf]
            w_at = w_1m[pos_tf]
            for side in ("below", "above"):
                count, cluster = 0, 0
                for bi in range(len(ftf)):
                    lvl_e, w_e = l_at[bi], w_at[bi]
                    if not (np.isfinite(lvl_e) and np.isfinite(w_e)
                            and w_e > 0):
                        EXCL["level_nan"] += 1
                        continue
                    tstamp = ftf.index[bi]
                    hm = tstamp.hour * 60 + tstamp.minute
                    sess = in_window(hm)
                    crossed = (fc[bi] > lvl_e) != (fo[bi] > lvl_e)
                    fail = ((fc[bi] < lvl_e) and (fh[bi] >= lvl_e)
                            and (fo[bi] < lvl_e)) if side == "below" else \
                           ((fc[bi] > lvl_e) and (fl[bi] <= lvl_e)
                            and (fo[bi] > lvl_e))
                    if crossed:
                        prev_count = count
                        count = 0
                        cluster += 1
                        if prev_count < 1 or sess is None:
                            continue
                        d = 1 if fc[bi] > lvl_e else -1
                        arm = "break"
                    elif fail:
                        count += 1
                        if sess is None:
                            continue
                        d = -1 if side == "below" else 1
                        arm = "reject"
                    else:
                        continue
                    # ---- condition (B): the SAME candle closes through its
                    # own TF BB MA in the trade direction -------------------
                    m_ = mtf[bi]
                    condB = bool(np.isfinite(m_)
                                 and (d * (fc[bi] - m_) > 0)
                                 and (d * (fo[bi] - m_) <= 0))
                    j0 = int(np.searchsorted(idx.values,
                                             tstamp.to_datetime64()))
                    rec = {"sess_day": sess_day, "t": tstamp, "tf": tf,
                           "locus": locus, "arm": arm, "side": side,
                           "session": sess, "direction": d,
                           "n_attempts": count, "condB": condB,
                           "cluster_id": f"{sess_day}:{tf}:{locus}:{side}:{cluster}",
                           "w15": w_e, "lvl_px": lvl_e,
                           "trig_high": fh[bi], "trig_low": fl[bi]}
                    if not walk:
                        rows.append(rec)
                        continue
                    if j0 >= len(idx):
                        EXCL["no_next_open"] += 1
                        continue
                    entry = float(op[j0])
                    stop = (fl[bi] - TICK) if d > 0 else (fh[bi] + TICK)
                    if d * (entry - stop) <= 0:
                        EXCL["gap_through_stop"] += 1
                        continue
                    w = walk_exits(j0, d, entry, stop)
                    if not w:
                        continue
                    rec.update({"entry": entry, "stop": stop, **w})
                    rows.append(rec)
    return rows


def main() -> None:
    pre = "--preflight" in sys.argv
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END]
    tfs = TFS + [15] if pre else TFS
    rows = []
    for k, d in enumerate(days):
        rows.extend(day_triggers(bars, d, tfs=tfs, walk=not pre))
        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    X = pd.DataFrame(rows)
    nd = len(days)

    if pre:
        print(f"\n=== D8 PRE-FLIGHT: raw trigger counts, {nd} fit days, "
              f"NO outcome walks ===")
        print("\n-- (A)-only counts, per day, by TF x locus x arm x session --")
        for arm in ("reject", "break"):
            print(f"\n[{arm}]")
            t = (X[X.arm == arm].groupby(["session", "locus", "tf"]).size()
                 / nd).unstack("tf").round(2)
            print(t.to_string())
        print("\n-- (A)^(B) share of (A), by TF --")
        s = X.groupby("tf").condB.agg(["mean", "size"])
        for tf, r in s.iterrows():
            print(f"   TF={tf:2d}: (A) {int(r['size']):7d}  "
                  f"(A)^(B) {r['mean']*100:5.1f}%  "
                  f"= {int(r['size']*r['mean']):6d}")
        print("\n-- (A)^(B) share of (A), per TF x arm --")
        s = X.groupby(["tf", "arm"]).condB.agg(["mean", "size"])
        for (tf, arm), r in s.iterrows():
            print(f"   TF={tf:2d} {arm:6s}: (A) {int(r['size']):7d}  "
                  f"(A)^(B) {r['mean']*100:5.1f}%  "
                  f"= {int(round(r['size']*r['mean'])):6d}  "
                  f"({r['size']*r['mean']/nd:5.2f}/day)")

        print("\n-- D8 PATHOLOGY CHECK 1: any cell > 50 triggers/day --")
        per = X.groupby(["session", "locus", "arm", "tf"]).size() / nd
        bad = per[per > 50]
        print(f"   cells over the bar: {len(bad)} of {len(per)}   "
              f"(max cell = {per.max():.2f}/day)"
              + ("" if len(bad) == 0 else f"\n{bad.to_string()}"))

        print("\n-- D8 PATHOLOGY CHECK 2: 1m/15m scaling (must be SUB-linear, "
              "i.e. < 15x) --")
        key = ["session", "locus", "arm"]
        r15 = X[X.tf == 15].groupby(key).size()
        for tf in (1, 2, 3, 5):
            rt = X[X.tf == tf].groupby(key).size()
            rat = (rt / r15).replace([np.inf], np.nan).dropna()
            lin = 15.0 / tf
            sup = rat[rat > lin]
            print(f"   TF={tf}m vs 15m  candle ratio {lin:5.1f}x | trigger "
                  f"ratio med {rat.median():5.2f} p90 {rat.quantile(.9):5.2f} "
                  f"max {rat.max():5.2f} | super-linear cells: {len(sup)}"
                  + ("" if len(sup) == 0 else
                     "\n" + sup.round(2).to_string()))

        print("\n-- D8 PATHOLOGY CHECK 3: (A)^(B) <= (A) in every cell --")
        g = X.groupby(["session", "locus", "arm", "tf"]).condB.agg(
            ["sum", "size"])
        viol = g[g["sum"] > g["size"]]
        print(f"   violating cells: {len(viol)} of {len(g)}   "
              f"(max share {(g['sum']/g['size']).max()*100:.1f}%)")
        print("   NOTE: condB is a boolean column ON the (A) rows, so the "
              "subset relation is structural, not an empirical result. The "
              "informative number is the SHARE above, not this check.")

        print("\n-- CALIBRATION CONTROL: TF=15 (A)-only vs the existing "
              "level census --")
        ref_p = ROOT / "output/htf_ma_census/levels_fit.parquet"
        if not ref_p.exists():
            print(f"   MISSING {ref_p} — control cannot run")
        else:
            ref = pd.read_parquet(ref_p)
            ref["t"] = pd.to_datetime(ref["t"], utc=True).dt.tz_convert(NY)
            ref["hm"] = ref.t.dt.hour * 60 + ref.t.dt.minute
            ref["wsess"] = [in_window(h) for h in ref.hm]
            ref = ref[ref.wsess.notna() & ref.sess_day.between(FIT_START,
                                                              FIT_END)]
            kc = ["sess_day", "t", "locus", "arm", "side"]
            a = set(map(tuple, X[X.tf == 15][kc].astype(str).to_numpy()))
            b = set(map(tuple, ref[kc].astype(str).to_numpy()))
            print(f"   level census (windowed): {len(b):6d} triggers")
            print(f"   this pass, TF=15 (A):    {len(a):6d} triggers")
            print(f"   identical on (day,t,locus,arm,side): "
                  f"{'YES' if a == b else 'NO'}   "
                  f"| only-here {len(a-b)}  only-there {len(b-a)}")
            if a != b:
                for lab, ss in (("only-here", a - b), ("only-there", b - a)):
                    d_ = pd.DataFrame(sorted(ss), columns=kc)
                    print(f"   {lab} by locus x arm:")
                    print(d_.groupby(["locus", "arm"]).size().to_string())
            print("   (the level census DROPS reject rows that gap through "
                  "the stop; those are counted in EXCL there and kept here, "
                  "so a small only-here residue is expected and is listed "
                  "above rather than smoothed over.)")

        X.to_parquet(ROOT / "output/htf_ma_census/ltf_preflight.parquet",
                     index=False)
        print(f"\nwritten: ltf_preflight.parquet ({len(X):,} rows)")
        return

    out = ROOT / "output/htf_ma_census"
    X.to_parquet(out / "ltf_fit.parquet", index=False)
    print(f"LTF CENSUS: {len(X):,} fit rows | excl {EXCL}")


if __name__ == "__main__":
    main()
