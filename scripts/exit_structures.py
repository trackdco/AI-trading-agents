#!/usr/bin/env python3
"""EXIT STRUCTURES — testing the exit, not the entry, on the M2/M3 race
population where the current exit (first structure beyond entry) is
known to be badly wrong (census median 0.95R exit vs 6.15R actual run
for the 3R+ subset).

Population: `race_wide.parquet`, mech in {M2, M3} (M1's baseline target
is the 15m MA itself, a different exit paradigm — out of scope here,
stated not silently dropped). Structure levels (POC, VWAP mid/+-1/+-2,
VAL, VAH) rebuilt per-fight, as-of, exactly as `race_outcomes.py` does,
then ranked by distance ahead of entry in the trade direction to get
the 1st/2nd/3rd structure.

COST CONVENTION: the task specifies "0.5pt/side" for this exercise —
0.5pt entry-side + 0.5pt exit-side = 1.0pt round trip. Per
`docs/real-exit-rescore.md`'s already-established equivalence, when a
position's exit is split across legs by weight, apportioning the
0.5pt exit-side cost by leg weight is mathematically identical to a
FLAT `cost_r = 1.0/risk` subtracted once from the weighted-average
GROSS R — so every variant below computes weighted gross R across legs,
then subtracts one flat `cost_r`. This is DIFFERENT from the
`race_outcomes.py` walk() convention baked into the recorded `out`
column (`COST_PTS=0.5` applied ONCE = 0.5pt round trip total, i.e.
half our convention). Variant 1 is run BOTH ways: under the task's
0.5pt/side convention (headline) and under the legacy 0.5pt-total
convention (diagnostic control, to isolate that any gap from `out` is
pure cost-convention, not a target/walk logic bug).

    python -m scripts.exit_structures [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.conviction_lib import dboot_mean                       # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
RUNS = ROOT / "output/htf_ma_census/race_runs.parquet"
OUT = ROOT / "output/htf_ma_census/exit_structures.parquet"

MENU = ["poc", "vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2",
        "val", "vah"]
COST_SIDE = 0.5                       # pt, per side (task spec)
COST_R_FLAT = 2 * COST_SIDE           # 1.0pt round trip, flat, in points
COST_LEGACY = 0.5                     # race_outcomes.py's walk() convention
SESSIONS = ["LONDON", "NY_PRE", "NY_AM"]
MECHS = ["M2", "M3"]

# ---- the 8 exit variants + fixed-3R control -------------------------
# each: (name, leg1_kind, leg2_kind, w1, w2)
#   leg1_kind in {'s1','s2','s3','r3'} (structure 1/2/3, or fixed 3R)
#   leg2_kind in {None,'s1','s2','trail','none'}  (None = single leg)
VARIANTS = {
    "V1_full_s1":     ("s1", None, 1.00, 0.00),
    "V2_full_s2":     ("s2", None, 1.00, 0.00),
    "V3_full_s3":     ("s3", None, 1.00, 0.00),
    "V4_75s1_25s2":   ("s1", "s2", 0.75, 0.25),
    "V5_75s1_25trail": ("s1", "trail", 0.75, 0.25),
    "V6_50s1_50s2":   ("s1", "s2", 0.50, 0.50),
    "V7_fixed3R":     ("r3", None, 1.00, 0.00),
    "V8_75s1_25none": ("s1", "none", 0.75, 0.25),
}
STOP_XS = [0.5, 0.75, 1.0]


def day_context(bars, sess_day):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    if hist.empty:
        return None
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return None
    idx = seg.index
    hi, lo, cl, op = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy(), seg.open.to_numpy())
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"):
        S[b] = vw[b].reindex(idx).to_numpy()

    # ---- 15m-bar-close trail arrays (variant 5), same grammar as
    # trigger_race_census.py / race_realexit.py: MA judged at the
    # candle's own close minute (developing-bar-included convention).
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)
    trail_close = np.full(N, np.nan)
    trail_ma = np.full(N, np.nan)
    for bi in range(len(f15)):
        end = min(int(pos15[bi]), N)
        last_row = end - 1
        if 0 <= last_row < N and np.isfinite(ma_at15[bi]):
            trail_close[last_row] = float(f15.close.iloc[bi])
            trail_ma[last_row] = float(ma_at15[bi])

    return dict(idx=idx, hi=hi, lo=lo, cl=cl, op=op, N=N, S=S,
               trail_close=trail_close, trail_ma=trail_ma)


def structure_candidates(S, p, d, entry):
    """Sorted (name, price) for menu structures strictly ahead of entry
    in the trade direction, at decision row p — identical selection
    logic to race_outcomes.py's near/far."""
    cand = [(k, float(S[k][p])) for k in MENU
            if np.isfinite(S[k][p]) and d * (S[k][p] - entry) > 0]
    cand.sort(key=lambda kv: d * (kv[1] - entry))
    return cand


def walk_two_phase(j0, d, entry, risk, N, hi, lo, cl,
                   leg1_arr, leg2_kind, leg2_arr, w1, w2, stop_X,
                   trail_close=None, trail_ma=None):
    """Two-phase first-passage walk. Returns dict with gross_R (no
    cost, weighted across legs), leg1_hit, leg1_gross, leg2_gross,
    resolved (str), j_end. Same-bar -> stop always wins."""
    stop_px = entry - d * stop_X * risk
    leg1_hit, leg1_gross, j1 = False, None, None
    for j in range(j0, N):
        stop_touched = (lo[j] <= stop_px) if d > 0 else (hi[j] >= stop_px)
        if stop_touched:
            return dict(gross_R=-float(stop_X), leg1_hit=False,
                       leg1_gross=None, leg2_gross=None,
                       resolved="stop1", j_end=j)
        if leg1_arr is not None:
            tv = leg1_arr[j - 1] if j > 0 else np.nan
            if np.isfinite(tv) and lo[j] <= tv <= hi[j]:
                leg1_hit, leg1_gross, j1 = True, d * (tv - entry) / risk, j
                break
    if not leg1_hit:
        gross = d * (cl[N - 1] - entry) / risk
        return dict(gross_R=gross, leg1_hit=False, leg1_gross=None,
                   leg2_gross=None, resolved="eod1", j_end=N - 1)
    if w2 <= 0:
        return dict(gross_R=leg1_gross, leg1_hit=True,
                   leg1_gross=leg1_gross, leg2_gross=None,
                   resolved="target1_full", j_end=j1)
    # ---- PHASE 2: weight w2 remains, stop moved to break-even
    be = entry
    leg2_gross, resolved2, j2 = None, "eod2", N - 1
    for j in range(j1 + 1, N):
        be_touched = (lo[j] <= be) if d > 0 else (hi[j] >= be)
        if be_touched:
            leg2_gross, resolved2, j2 = 0.0, "be_stop", j
            break
        if leg2_kind == "trail":
            if trail_close is not None and np.isfinite(trail_close[j]):
                tc, tm = trail_close[j], trail_ma[j]
                bad = (tc < tm) if d > 0 else (tc > tm)
                if bad:
                    leg2_gross = d * (tc - entry) / risk
                    resolved2, j2 = "trail", j
                    break
        elif leg2_kind == "structure" and leg2_arr is not None:
            tv = leg2_arr[j - 1] if j > 0 else np.nan
            if np.isfinite(tv) and lo[j] <= tv <= hi[j]:
                leg2_gross = d * (tv - entry) / risk
                resolved2, j2 = "target2", j
                break
        # leg2_kind == "none": only the BE stop is monitored
    if leg2_gross is None:
        leg2_gross = d * (cl[N - 1] - entry) / risk
        resolved2, j2 = "eod2", N - 1
    gross = w1 * leg1_gross + w2 * leg2_gross
    return dict(gross_R=gross, leg1_hit=True, leg1_gross=leg1_gross,
               leg2_gross=leg2_gross, resolved=f"{resolved2}_p2", j_end=j2)


def build() -> pd.DataFrame:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    W = pd.read_parquet(WIDE)
    W["t"] = pd.to_datetime(W.t)
    W = W[W.mech.isin(MECHS)].copy()
    RN = pd.read_parquet(RUNS)
    W = W.merge(RN[["scid", "run_mfe_r", "run_mae_r", "reach_1r",
                    "reach_2r", "reach_3r"]], on="scid", how="left",
               validate="1:1")
    print(f"population: {len(W)} M2/M3 fights, {W.sess_day.nunique()} days")

    rows = []
    days = sorted(W.sess_day.unique())
    for k, day in enumerate(days):
        ctx = day_context(bars, day)
        if ctx is None:
            continue
        idx = ctx["idx"]
        hi, lo, cl, N = ctx["hi"], ctx["lo"], ctx["cl"], ctx["N"]
        S = ctx["S"]
        trail_close, trail_ma = ctx["trail_close"], ctx["trail_ma"]
        DR = W[W.sess_day == day]
        for r in DR.itertuples():
            t = pd.Timestamp(r.t)
            pos = int(np.searchsorted(idx.values, t.to_datetime64()))
            if pos >= N or idx[pos] != t:
                continue
            j0 = int(pos)
            p = j0 - 1
            if p < 0:
                continue
            d = int(r.direction)
            entry, risk = float(r.entry), float(r.risk)
            if not (np.isfinite(risk) and risk > 0):
                continue
            cand = structure_candidates(S, p, d, entry)
            s1 = cand[0][0] if len(cand) >= 1 else None
            s2 = cand[1][0] if len(cand) >= 2 else None
            s3 = cand[2][0] if len(cand) >= 3 else None
            r3_level = entry + d * 3.0 * risk
            fixed_arr = np.full(N, r3_level)   # constant "structure"

            leg_arr = {
                "s1": S[s1] if s1 else None,
                "s2": S[s2] if s2 else None,
                "s3": S[s3] if s3 else None,
                "r3": fixed_arr,
            }
            leg_name = {"s1": s1, "s2": s2, "s3": s3, "r3": "fixed_3R"}

            base = dict(scid=r.scid, sess_day=day, session=r.session,
                       mech=r.mech, direction=d, dir=r.dir,
                       entry=entry, stop=r.stop, risk=risk,
                       near_name=r.near_name, s1=s1, s2=s2, s3=s3,
                       near_out=r.near_out, out=r.out,
                       run_mfe_r=r.run_mfe_r, run_mae_r=r.run_mae_r,
                       reach_1r=r.reach_1r, reach_2r=r.reach_2r,
                       reach_3r=r.reach_3r)

            for vname, (l1k, l2k, w1, w2) in VARIANTS.items():
                l1arr = leg_arr[l1k]
                l2arr = leg_arr[l2k] if l2k in ("s1", "s2") else None
                l2kind = ({"s1": "structure", "s2": "structure",
                          "trail": "trail", "none": "none",
                          None: None})[l2k]
                for X in (STOP_XS if vname in
                         ("V4_75s1_25s2", "V5_75s1_25trail",
                          "V8_75s1_25none", "V1_full_s1",
                          "V6_50s1_50s2") else [1.0]):
                    res = walk_two_phase(
                        j0, d, entry, risk, N, hi, lo, cl,
                        l1arr, l2kind, l2arr, w1, w2, X,
                        trail_close, trail_ma)
                    cost_r_flat = COST_R_FLAT / risk
                    total_r = res["gross_R"] - cost_r_flat
                    rec = dict(base)
                    rec.update(variant=vname, stop_X=X,
                              gross_R=res["gross_R"], total_R=total_r,
                              win=total_r > 0, leg1_hit=res["leg1_hit"],
                              leg1_gross=res["leg1_gross"],
                              leg2_gross=res["leg2_gross"],
                              resolved=res["resolved"], j_end=res["j_end"],
                              leg1_name=leg_name[l1k],
                              leg2_name=(leg_name.get(l2k)
                                        if l2k in ("s1", "s2") else l2k))
                    rows.append(rec)

            # ---- diagnostic control: variant-1 under the LEGACY
            # (0.5pt total, single-side) cost convention, to isolate
            # cost-convention drift from logic drift vs recorded `out`
            resL = walk_two_phase(j0, d, entry, risk, N, hi, lo, cl,
                                  leg_arr["s1"], None, None, 1.0, 0.0, 1.0,
                                  trail_close, trail_ma)
            total_legacy = resL["gross_R"] - COST_LEGACY / risk
            rec = dict(base)
            rec.update(variant="V1_full_s1_LEGACYCOST", stop_X=1.0,
                      gross_R=resL["gross_R"], total_R=total_legacy,
                      win=total_legacy > 0, leg1_hit=resL["leg1_hit"],
                      leg1_gross=resL["leg1_gross"], leg2_gross=None,
                      resolved=resL["resolved"], j_end=resL["j_end"],
                      leg1_name=s1, leg2_name=None)
            rows.append(rec)

        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)

    R = pd.DataFrame(rows)
    R.to_parquet(OUT, index=False)
    print(f"written: {OUT} ({len(R):,} rows)")
    return R


def main() -> None:
    if "--build" in sys.argv or not OUT.exists():
        build()


if __name__ == "__main__":
    main()
