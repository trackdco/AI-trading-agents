#!/usr/bin/env python3
"""Order-flow autopsy of the 10:15-10:30 window (ANGUS 2026-07-26).

  "you have 10:15 to 10:30 raw data now. run the order flow variables that we did for the
   golden window. what is order flow saying at the entries that fired from 10:15-10:30?
   lets find that subset that produces the majority of the profit, and cut the losers."

Three stages in one script:
  1. RE-SIMULATE late-a (10:15-10:30) over 2025-07..2026-07 capturing FULL TradeRecords
     (entry price is needed for wall geometry; the probe CSV didn't carry it).
  2. Compute the SAME order-flow variables the golden checklist was built on, using the
     canonical implementations in src/canon/features.py (depth_at / tape_features /
     vwap_geometry — the definitions the canon was validated on). Depth covers to 10:29,
     so walls are available for this whole window.
  3. Winners-vs-losers per variable, then the trade_angles survival rule: a check counts
     only if the on-vs-off $/trade direction AGREES IN BOTH 2025 AND 2026 with a >=$60/t
     gap and n>=12 per cell. Then a small conjunction from the survivors = the subset.

DISCIPLINE: stage 3 is exploratory. Anything that comes out of it needs the same
freeze-and-OOS treatment as the golden checks before it trades a dollar. n=292 is small.

    python -m scripts.late_a_orderflow
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.grade_window_cap import books, load                      # noqa: E402
from scripts.late_window_probe import MONTHS, TRIGGERS, WARMUP_DAYS   # noqa: E402
from src.backtest.engine import load_backtest_config, simulate        # noqa: E402
from src.canon.features import depth_at, load_depth_day, tape_features, vwap_geometry  # noqa: E402
from src.engine.indicators import daily_vwap                          # noqa: E402

NY = "America/New_York"
WS, WE = dtime(10, 15), dtime(10, 30)
OUT = Path("output/late_a_flow_matrix.parquet")


# ------------------------------------------------------------------ 1. re-simulate
def run_sim() -> pd.DataFrame:
    allt = load(TRIGGERS)
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows()
           if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    base = load_backtest_config().model_copy(update={
        "no_trade_start": None, "no_trade_end": None, "win_start": WS, "win_end": WE,
        "max_trades_per_day": 2, "post_open_min_stop": 0.0})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        start = pd.Timestamp((pd.Timestamp(m + "-01")
                              - pd.Timedelta(days=WARMUP_DAYS)).strftime("%Y-%m-%d"), tz=NY)
        seg = df[(df.ts_event >= start) & (df.ts_event <= end)].reset_index(drop=True)
        for tt, cfg in (([t for t in trigs if t.ts[:10] not in war], cfg_e3),
                        ([t for t in trigs if t.ts[:10] in war], cfg_e4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (WS <= ft < WE):
                    continue
                rows.append(dict(day=r.trade_date, month=m, fill_ts=str(r.fill_ts),
                                 direction=r.direction, kind=r.kind, pattern=r.pattern,
                                 htf_flag=r.htf_flag, tf=r.tf, confluence=r.confluence,
                                 entry=r.entry, stop=r.stop_initial,
                                 risk_pts=abs(r.entry - r.stop_initial),
                                 dollars=r.dollars, r_multiple=r.r_multiple,
                                 exit_reason=r.exit_reason))
        print(f"  sim {m} done", flush=True)
    J = (pd.DataFrame(rows)
         .drop_duplicates(subset=["fill_ts", "direction"]).sort_values("fill_ts")
         .reset_index(drop=True))
    return J


# ------------------------------------------------------------------ 2. flow matrix
def add_features(J: pd.DataFrame) -> pd.DataFrame:
    # tape — identical prep to trade_matrix.py
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()
    M["cum"] = M.groupby("sday").delta.cumsum()
    M["runmin"] = M.groupby("sday").cum.cummin()
    M["runmax"] = M.groupby("sday").cum.cummax()
    daymed = M.groupby("sday").vol.median()
    byday_tape = {d: g for d, g in M.groupby("sday")}

    # bars + vwap bands — identical prep to trade_matrix.py
    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet").drop(
        columns=["roll"], errors="ignore")
    bars = (pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event")
            .sort_values("ts_event").reset_index(drop=True))
    ind = daily_vwap(bars, bands=[1, 2])
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(mi=bt.dt.floor("min"),
                       sday=(bt + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"),
                       hm=bt.dt.hour * 60 + bt.dt.minute,
                       vw=ind["vwap"].values, up1=ind["upper_1"].values)
    byday_bars = {d: g for d, g in bars.groupby("sday")}

    depth_cache: dict = {}
    feats = []
    for t in J.itertuples():
        fill = pd.Timestamp(t.fill_ts)
        if fill.tzinfo is None:
            fill = fill.tz_localize(NY)
        fill = fill.tz_convert(NY)
        f: dict = {}
        # depth (walls) at the fill minute — canon convention
        if t.day not in depth_cache:
            depth_cache[t.day] = load_depth_day(t.day)
        dep = depth_cache[t.day]
        if dep is not None:
            f.update(depth_at(dep, fill.floor("min"), t.entry, t.direction))
        # tape strictly before the fill
        g = byday_tape.get(t.day)
        if g is not None:
            upto = g[g.index < fill]
            if len(upto):
                f.update(tape_features(upto, t.direction, fill,
                                       float(daymed.get(t.day, np.nan))))
                # PAQ-equivalent: 30-min path efficiency of the tape price proxy
                w30 = upto[upto.index >= fill - pd.Timedelta(minutes=30)]
                if len(w30) > 2:
                    net = abs(w30.vwp.iloc[-1] - w30.vwp.iloc[0])
                    tot = w30.vwp.diff().abs().sum()
                    f["netpath_30"] = net / tot if tot > 0 else np.nan
        # vwap geometry strictly before the fill
        gb = byday_bars.get(t.day)
        if gb is not None:
            pre = gb[gb.mi < fill.floor("min")]
            f.update(vwap_geometry(pre, t.entry, t.direction))
        feats.append(f)
    F = pd.DataFrame(feats, index=J.index)
    return pd.concat([J, F], axis=1)


# ------------------------------------------------------------------ 3. analysis
def analyse(X: pd.DataFrame, label: str = "10:15-10:30") -> None:
    X = X.copy()
    X["win"] = X.dollars > 0
    X["yr"] = X.month.str[:4]
    long = X.direction == "long"

    # the golden-checklist checks, canon definitions/thresholds where they exist
    wall_behind = np.where(long, X.get("dep_wall_below_d"), X.get("dep_wall_above_d"))
    wall_ahead = np.where(long, X.get("dep_wall_above_d"), X.get("dep_wall_below_d"))
    wall_ahead_sz = np.where(long, X.get("dep_wall_above_sz"), X.get("dep_wall_below_sz"))
    has_depth = X.get("dep_thick", pd.Series(np.nan, index=X.index)).notna()
    checks = {
        "W  no-wall-behind": pd.Series(pd.isna(wall_behind), index=X.index).where(has_depth),
        "D  wall-ahead":     pd.Series(pd.notna(wall_ahead), index=X.index).where(has_depth),
        "WALLSZ ahead>=7":   pd.Series(pd.notna(wall_ahead)
                                       & (pd.Series(wall_ahead_sz, index=X.index) >= 7),
                                       index=X.index).where(has_depth),
        "IMB book-with (dir)": (np.sign(X.get("dep_imb", np.nan)) == np.where(long, 1, -1)),
        "F  fill_delta_conf": X.get("fill_delta_conf") == 1,
        "BIGFD |fd|>=173":   X.get("fill_delta", pd.Series(np.nan, index=X.index)).abs() >= 173,
        "Tc d15_conf":       X.get("d15_conf") == 1,
        "d5_conf":           X.get("d5_conf") == 1,
        "d30_conf":          X.get("d30_conf") == 1,
        "C  op_sofar_conf":  X.get("op_sofar_conf") == 1,
        "pm_sofar_conf":     X.get("pm_sofar_conf") == 1,
        "G  vwapd>=0.107":   X.get("ent_vs_vwap_sd_dir", pd.Series(np.nan, index=X.index)) >= 0.107,
        "PAQ netpath30>=.30": X.get("netpath_30", pd.Series(np.nan, index=X.index)) >= 0.30,
        "path_hi (cvd top-q)": X.get("pathpos", pd.Series(np.nan, index=X.index)) >= 0.75,
        "path_lo (cvd bot-q)": X.get("pathpos", pd.Series(np.nan, index=X.index)) <= 0.25,
        "REJ  kind=rejection": X.kind == "rejection_block",
        "DISP kind=displacement": X.kind == "displacement",
    }

    print(f"\n================ 1. what order flow says at {label} entries ================")
    print(f"{'check':<26}{'n_on':>6}{'$/t on':>9}{'win on':>8}{'n_off':>7}{'$/t off':>9}"
          f"{'win off':>8}{'gap $/t':>9}{'25 dir':>7}{'26 dir':>7}{'SURVIVES':>10}")
    surv = {}
    for name, flag in checks.items():
        m = pd.Series(flag).astype("boolean")
        on, off = X[m == True], X[m == False]              # noqa: E712
        if len(on) < 5 or len(off) < 5:
            continue
        gap = on.dollars.mean() - off.dollars.mean()
        oks = []
        for yr in ("2025", "2026"):
            o, f_ = on[on.yr == yr], off[off.yr == yr]
            oks.append("?" if (len(o) < 12 or len(f_) < 12) else
                       ("+" if o.dollars.mean() - f_.dollars.mean() >= 60 else
                        "-" if o.dollars.mean() - f_.dollars.mean() <= -60 else "0"))
        alive = (oks[0] == oks[1]) and oks[0] in ("+", "-")
        if alive:
            surv[name] = (oks[0] == "+")
        print(f"{name:<26}{len(on):>6}{on.dollars.mean():>+9,.0f}"
              f"{on.win.mean()*100:>7.0f}%{len(off):>7}{off.dollars.mean():>+9,.0f}"
              f"{off.win.mean()*100:>7.0f}%{gap:>+9,.0f}{oks[0]:>7}{oks[1]:>7}"
              f"{'YES' if alive else '':>10}")

    print(f"\nbaseline: {len(X)}t  ${X.dollars.sum():+,.0f}  win {X.win.mean()*100:.0f}%  "
          f"({X.r_multiple.sum():+.1f}R = ${X.r_multiple.sum()*200:+,.0f} @floor)")
    print(f"depth coverage: {has_depth.sum()}/{len(X)} trades have book data")

    print(f"\n================ 2. survivors -> the kept subset ({label}) ================")
    if not surv:
        print("NO check survives the both-years rule. The window has no honest flow edge "
              "at n=292 — report that, do not fit one.")
        return
    keep = pd.Series(True, index=X.index)
    applied = []
    cur = X
    for name, want_on in sorted(surv.items(),
                                key=lambda kv: -abs(pd.Series(checks[kv[0]]).astype("boolean").eq(kv[1]).sum())):
        flag = pd.Series(checks[name]).astype("boolean") == want_on
        trial = keep & flag.fillna(False)
        t = X[trial]
        if len(t) >= 25 and t.dollars.sum() > cur.dollars.sum():
            keep, cur, applied = trial, t, applied + [f"{name}={'ON' if want_on else 'OFF'}"]
        if len(applied) == 3:
            break
    kept, cut = X[keep], X[~keep]
    mo = kept.groupby("month").dollars.sum()
    print(f"rules: {' AND '.join(applied) if applied else '(none improved the total)'}")
    print(f"KEPT {len(kept)}t  ${kept.dollars.sum():+,.0f}  win {kept.win.mean()*100:.0f}%  "
          f"({kept.r_multiple.sum():+.1f}R = ${kept.r_multiple.sum()*200:+,.0f} @floor)  "
          f"months green {int((mo > 0).sum())}/{len(mo)}")
    for yr in ("2025", "2026"):
        k = kept[kept.yr == yr]
        print(f"   {yr}: {len(k)}t  ${k.dollars.sum():+,.0f}  win {k.win.mean()*100 if len(k) else 0:.0f}%")
    print(f"CUT  {len(cut)}t  ${cut.dollars.sum():+,.0f}  win {cut.win.mean()*100:.0f}%")
    print("\nmonth-by-month of the kept subset:")
    print(mo.to_string(float_format=lambda v: f"{v:+,.0f}"))


def main() -> None:
    if OUT.exists():
        X = pd.read_parquet(OUT)
        print(f"loaded cached {OUT} ({len(X)} trades)")
    else:
        J = run_sim()
        print(f"sim complete: {len(J)} trades")
        X = add_features(J)
        X.to_parquet(OUT)
        print(f"wrote {OUT}")
    analyse(X)


if __name__ == "__main__":
    main()
