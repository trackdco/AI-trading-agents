#!/usr/bin/env python3
"""M-TABLE — master completeness table (prereg: M-TABLE block).

Every trigger of both mechanisms, no caps, full span, sealed split, geometry
+ level set + outcomes + TWELVE flow features computed as-of the decision bar
(entry next open) and ASSERTED by the perturbation gate before the main pass.

    python -m scripts.htf_ma_mtable [--days N] [--gate-only]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, vwap_bands,          # noqa: E402
                               profile_at_minutes, session_tag)

TICK = 0.25
COST_PTS = 0.5
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
S_SWEEP = [10, 20, 30, 40, 60, 80]
FLOW_NAMES = ["flowconf", "volx", "closeloc", "rangex", "bp5opp", "d5_conf",
              "d15_conf", "d30_conf", "thru_delta_conf", "eff_result",
              "cvd_slope30", "delta_z"]
EXCL = {"no_next_open": 0, "gap_through_stop": 0}   # named exclusions


def flow_features(fpd: pd.DataFrame | None, bar_start: pd.Timestamp,
                  bar_end: pd.Timestamp, direction: int,
                  tf_bars: pd.DataFrame | None) -> dict:
    """Twelve flow features as-of bar_end (decision-bar close; entry = next
    open). Uses fp minutes with index < bar_end ONLY (the decision bar's own
    minutes are [bar_start, bar_end) — complete at bar_end)."""
    f = {k: np.nan for k in FLOW_NAMES}
    if fpd is None or len(fpd) == 0:
        return f
    upto = fpd[fpd.index < bar_end]
    if len(upto) == 0:
        return f
    bar = upto[upto.index >= bar_start]
    pre = upto[upto.index < bar_start]
    if len(bar):
        dsum = float(bar.delta.sum())
        f["flowconf"] = float(np.sign(dsum) == direction) if dsum != 0 else 0.5
        f["thru_delta_conf"] = float(np.sign(bar.delta.iloc[-1]) == direction) \
            if bar.delta.iloc[-1] != 0 else 0.5
        vs = float(bar.vol.sum())
        if tf_bars is not None and len(tf_bars) >= 20:
            vmed = float(tf_bars.vol.iloc[-20:].median())
            f["volx"] = vs / vmed if vmed > 0 else np.nan
            dstd = float(tf_bars.delta.iloc[-20:].std(ddof=1))
            dmu = float(tf_bars.delta.iloc[-20:].mean())
            f["delta_z"] = (dsum - dmu) / dstd if dstd > 0 else np.nan
        rng = float(bar.vwp.max() - bar.vwp.min())
        f["eff_result"] = vs / rng if rng > 0.5 else np.nan
    if len(pre) >= 5:
        last5 = pre.delta.iloc[-5:]
        f["bp5opp"] = float((np.sign(last5) == -direction).sum() >= 3)
    for w, name in ((5, "d5_conf"), (15, "d15_conf"), (30, "d30_conf")):
        seg = pre[pre.index >= bar_start - pd.Timedelta(minutes=w)]
        if len(seg) >= max(3, w // 2):
            s = float(seg.delta.sum())
            f[name] = float(np.sign(s) == direction) if s != 0 else 0.5
    seg30 = pre[pre.index >= bar_start - pd.Timedelta(minutes=30)]
    if len(seg30) >= 15:
        cvd = seg30.delta.cumsum().to_numpy()
        x = np.arange(len(cvd))
        f["cvd_slope30"] = float(np.polyfit(x, cvd, 1)[0] * direction)
    return f


def day_rows(bars, fp, sess_day: str):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30)) & (fp.index < t1)]
    ma15, w15 = bb_ma_asof(hist, 15)
    vw = vwap_bands(hist)
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    op = seg.open.to_numpy()
    ma_1m = ma15.loc[idx].to_numpy()
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
    ma_at15.index = f15.index
    w_at15 = w15.reindex(f15.index - pd.Timedelta(minutes=1))
    w_at15.index = f15.index
    fp15 = fpd.resample("15min", label="right", closed="left").agg(
        {"vol": "sum", "delta": "sum"}).dropna() if len(fpd) else None
    ma_f15 = ma_at15

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
        tstop, trail = stop, None
        fb2 = f15[f15.index > idx[j0]]
        fi, pos = list(fb2.index), 0
        for j in range(j0, len(idx)):
            if (lo[j] <= tstop) if d > 0 else (hi[j] >= tstop):
                trail = d * (tstop - entry) / risk
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
            trail = eod
        leg3 = (3.0 * risk - TICK) / risk if t3 is not None else None
        ship = (0.75 * leg3 + 0.25 * trail if leg3 is not None else trail) - cost
        return {"risk": risk, "mfe_r": mfe, "out_ship": ship,
                "out_trail": trail - cost, "out_hold": hold - cost}

    rows = []
    below_ma = None
    for side_name, sgn in (("below", 1), ("above", -1)):
        count, cluster = 0, 0
        for bi, tstamp in enumerate(f15.index):
            ma_e, w_e = ma_at15.iloc[bi], w_at15.iloc[bi]
            if not (np.isfinite(ma_e) and np.isfinite(w_e) and w_e > 0):
                continue
            b_ = f15.iloc[bi]
            crossed = (b_.close > ma_e) != (b_.open > ma_e)
            fail = ((b_.close < ma_e) and (b_.high >= ma_e) and (b_.open < ma_e)) \
                if side_name == "below" else \
                ((b_.close > ma_e) and (b_.low <= ma_e) and (b_.open > ma_e))
            if crossed:
                if count >= 1:
                    d = 1 if b_.close > ma_e else -1
                    j0 = int(np.searchsorted(idx.values, tstamp.to_datetime64()))
                    jt = None
                    # ENTRY LAW (entry gate, 2026-08-07): the limit level at
                    # bar j is the MA as-of the PREVIOUS 1m close — ma_1m[j]
                    # includes bar j's own close and is not knowable when the
                    # fill happens inside bar j
                    for j in range(max(j0, 1), len(idx)):
                        lvl = ma_1m[j - 1]
                        if np.isfinite(lvl) and lo[j] <= lvl <= hi[j]:
                            jt = j
                            break
                    # COMPLETENESS LAW: the break event exists at the cross,
                    # unconditionally — the retest is an outcome, not an
                    # existence condition (gate-caught defect, 2026-08-08)
                    entry = float(ma_1m[jt - 1]) if jt is not None else np.nan
                    stop = (b_.low - TICK) if d > 0 else (b_.high + TICK)
                    w = walk_exits(jt, d, entry, stop) if jt is not None else None
                    if w is None:
                        w = {"risk": np.nan, "mfe_r": np.nan, "out_ship": np.nan,
                             "out_trail": np.nan, "out_hold": np.nan}
                    fl = flow_features(fpd, tstamp - pd.Timedelta(minutes=15),
                                       tstamp, d, fp15[fp15.index < tstamp]
                                       if fp15 is not None else None)
                    rows.append({"sess_day": sess_day, "t": tstamp,
                                 "arm": "break", "side": side_name,
                                 "n_attempts": count, "direction": d,
                                 "session": session_tag(tstamp),
                                 "cluster_id": f"{sess_day}:{side_name}:{cluster}",
                                 "entry": entry, "stop": stop,
                                 "w15": w_e, "ma_px": ma_e,
                                 "trig_high": b_.high, "trig_low": b_.low,
                                 "retested": jt is not None, **w, **fl})
                count = 0
                cluster += 1
                continue
            if not fail:
                continue
            count += 1                      # NO CAP (prereg: cap removed)
            d = -1 if side_name == "below" else 1
            j0 = int(np.searchsorted(idx.values, tstamp.to_datetime64()))
            if j0 >= len(idx):
                EXCL["no_next_open"] += 1   # final-bar decision, named excl.
                continue
            # ENTRY LAW (entry gate, 2026-08-07): entry at the NEXT 1m open —
            # the decision bar's close is decision information, not a fill
            entry = float(op[j0])
            stop = (b_.high + TICK) if d < 0 else (b_.low - TICK)
            if d * (entry - stop) <= 0:
                EXCL["gap_through_stop"] += 1   # named excl., counted
                continue
            w = walk_exits(j0, d, entry, stop)
            if w:
                fl = flow_features(fpd, tstamp - pd.Timedelta(minutes=15),
                                   tstamp, d, fp15[fp15.index < tstamp]
                                   if fp15 is not None else None)
                rows.append({"sess_day": sess_day, "t": tstamp, "arm": "reject",
                             "side": side_name, "n_attempts": count,
                             "direction": d, "session": session_tag(tstamp),
                             "cluster_id": f"{sess_day}:{side_name}:{cluster}",
                             "entry": entry, "stop": stop, "w15": w_e,
                             "ma_px": ma_e, "trig_high": b_.high,
                             "trig_low": b_.low, **w, **fl})
    # level-set snapshot + targets, batch
    ev = [r["t"] - pd.Timedelta(minutes=1) for r in rows]
    if ev:
        prof = profile_at_minutes(hist, sorted(set(ev)))
        for r in rows:
            pm = r["t"] - pd.Timedelta(minutes=1)
            p_ = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lv = {"poc": p_.poc, "vah": p_.vah, "val": p_.val}
            if vrow is not None:
                lv.update({"vwap": vrow.vwap, "vwap_p1": vrow.vwap_p1,
                           "vwap_m1": vrow.vwap_m1, "vwap_p2": vrow.vwap_p2,
                           "vwap_m2": vrow.vwap_m2})
            r.update({f"lvl_{k}": v for k, v in lv.items()})
            d, ref, risk = r["direction"], r["entry"], r["risk"]
            if not np.isfinite(ref):
                ref = r["ma_px"]            # unretested break: reference = MA
            ahead = [(k, v) for k, v in lv.items() if np.isfinite(v)
                     and d * (v - ref) > 0]
            if ahead:
                k, v = min(ahead, key=lambda kv: abs(kv[1] - ref))
                r["next_level"], r["next_level_dist_W"] = k, abs(v - ref) / r["w15"]
            else:
                r["next_level"], r["next_level_dist_W"] = "none", np.nan
            r["cnt_ahead_1w"] = sum(1 for _, v in ahead
                                    if abs(v - ref) <= 1.0 * r["w15"])
            r["cnt_beyond_3r"] = sum(1 for _, v in ahead
                                     if 3.0 < d * (v - ref) / risk <= 8.0) \
                if np.isfinite(risk) else np.nan
    return rows


def perturbation_gate(bars, fp, days) -> bool:
    """Flow features must be bit-identical when everything after the decision
    bar is perturbed. PASS required before the main pass."""
    ok = True
    probes = 0
    for day in days:
        rows = day_rows(bars, fp, day)
        if not rows:
            continue
        pick = rows[:: max(1, len(rows) // 3)][:3]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        for r in pick:
            cut = pd.Timestamp(r["t"])
            pb = bars.copy()
            pf = fp.copy()
            mb = pb.index > cut
            pb.loc[mb, ["open", "high", "low", "close"]] *= 1.37
            pb.loc[mb, "volume"] = pb.loc[mb, "volume"] * 3 + 17
            mf = pf.index >= cut
            pf.loc[mf, ["b", "a", "vol", "delta"]] = \
                pf.loc[mf, ["b", "a", "vol", "delta"]] * 3 + 11
            rows2 = day_rows(pb, pf, day)
            match = [x for x in rows2 if x["t"] == r["t"] and x["arm"] == r["arm"]
                     and x["side"] == r["side"] and x["n_attempts"] == r["n_attempts"]]
            if not match:
                ok = False
                print(f"  GATE FAIL {day} {r['t']}: event vanished under perturbation")
                continue
            for k in FLOW_NAMES:
                a_, b2 = r[k], match[0][k]
                if not ((np.isnan(a_) and np.isnan(b2)) or a_ == b2):
                    ok = False
                    print(f"  GATE FAIL {day} {r['t']} {k}: {a_} != {b2}")
            probes += 1
    print(f"perturbation gate: {probes} probes -> {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> None:
    n_days = None
    if "--days" in sys.argv:
        n_days = int(sys.argv[sys.argv.index("--days") + 1])
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    fp = pd.read_parquet(ROOT / "output/fp_minutes_full.parquet")
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    gate_days = [d for d in sess_days if FIT_START <= d <= FIT_END][::40][:5]
    if not perturbation_gate(bars, fp, gate_days):
        sys.exit("PERTURBATION GATE FAILED — no rows written (prereg law)")
    if "--gate-only" in sys.argv:
        return
    if n_days:
        sess_days = sess_days[-n_days:]
    fit, sealed, gray = [], [], []
    for k, d in enumerate(sess_days):
        rows = day_rows(bars, fp, d)
        (fit if FIT_START <= d <= FIT_END else
         sealed if d < "2025-01-01" else gray).extend(rows)
        if k % 60 == 0:
            print(f"  {k}/{len(sess_days)}...", flush=True)
    out = ROOT / "output/htf_ma_census"
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "output/sealed").mkdir(parents=True, exist_ok=True)
    if fit:
        F = pd.DataFrame(fit)
        # continuity assert vs Census B (fit, capped subset, reject arm keys)
        B = pd.read_parquet(out / "censusB_fit.parquet")
        bk = set(map(tuple, B[B.kind == "reject"][["sess_day", "t", "side",
                                                   "n_attempts"]].itertuples(index=False)))
        mk = set(map(tuple, F[(F.arm == "reject") & (F.n_attempts <= 4)]
                     [["sess_day", "t", "side", "n_attempts"]].itertuples(index=False)))
        inter = len(bk & mk)
        F["in_censusB_pop"] = [(r.sess_day, r.t, r.side, r.n_attempts) in bk
                               for r in F.itertuples()]
        print(f"CONTINUITY: censusB reject keys {len(bk):,} | mtable capped "
              f"reject keys {len(mk):,} | intersection {inter:,} "
              f"({inter/len(bk)*100:.1f}% of B)")
        F.to_parquet(out / "mtable_fit.parquet", index=False)
    if sealed:
        pd.DataFrame(sealed).to_parquet(ROOT / "output/sealed/mtable_sealed.parquet",
                                        index=False)
    if gray:
        pd.DataFrame(gray).to_parquet(out / "mtable_gray.parquet", index=False)
    print(f"M-TABLE: fit={len(fit):,} | sealed={len(sealed):,} (written, NOT "
          f"read) | gray={len(gray):,}")
    print(f"named exclusions: no_next_open={EXCL['no_next_open']} | "
          f"gap_through_stop={EXCL['gap_through_stop']}")


if __name__ == "__main__":
    main()
