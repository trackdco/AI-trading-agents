#!/usr/bin/env python3
"""Management dissection of the golden book at rr_floor 2.0 vs 1.5 (ANGUS 2026-07-26).

  "i do wonder what the mae on these low rr winners are tho... i usually never have less
   than 2r on a trade which is why the floor was at 2. perhaps the targets arent optimistic
   enough, and also perhaps the stop could be too big. lots to dissect here."

Separates his three hypotheses, which have three different fixes:
  H1 low-R winners are scrapes      -> MAE distribution of the geometry-save wins
  H2 target menu not optimistic     -> post-target MFE extension (R left on the table)
  H3 stops carry dead width         -> winner MAE/stop distribution; counterfactual R of the
                                       SAME move at a right-sized stop (engine-1.5R == his-2R?)
Plus the 3-minute cut re-test: does (r_3 <= -0.1106 & fw_3 <= -13) still separate losers when
targets are nearer and trades resolve faster? (Rule from canon Layer 2d, calibrated at rr 2.0.)

Path metrics are computed from 1m bars with ONE convention for both books (fill-minute
inclusive, so MAE can slightly overstate by the pre-fill part of the fill bar — identical
treatment both sides, comparisons unaffected). fw_3 from fp_minutes over (fill, fill+3].

    python -m scripts.mgmt_dissect
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

NY = "America/New_York"
CUT_R, CUT_FW = -0.1106, -13.0        # canon Layer 2d thresholds (calibrated at rr 2.0)


def run(floor: float) -> pd.DataFrame:
    out = Path(f"output/mgmt_rr{str(floor).replace('.','_')}.parquet")
    if out.exists():
        return pd.read_parquet(out)
    allt = load(TRIGGERS)
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows()
           if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    base = load_backtest_config().model_copy(update={
        "no_trade_start": None, "no_trade_end": None,
        "win_start": dtime(9, 40), "win_end": dtime(10, 15),
        "max_trades_per_day": 2, "rr_floor": floor})
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
            for r in simulate(seg, tt, cfg)[0]:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (dtime(9, 40) <= ft < dtime(10, 15)):
                    continue
                rows.append(dict(month=m, fill_ts=str(r.fill_ts), direction=r.direction,
                                 kind=r.kind, entry=r.entry, stop=r.stop_initial,
                                 risk_pts=abs(r.entry - r.stop_initial),
                                 target=r.working_target, exit_ts=str(r.exit_ts),
                                 exit_price=r.exit_price, dollars=r.dollars,
                                 r_multiple=r.r_multiple, exit_reason=r.exit_reason))
        print(f"  rr={floor} {m} done", flush=True)
    J = (pd.DataFrame(rows).drop_duplicates(subset=["fill_ts", "direction"])
         .sort_values("fill_ts").reset_index(drop=True))
    J.to_parquet(out)
    return J


def add_paths(J: pd.DataFrame) -> pd.DataFrame:
    bars = pd.read_parquet("data/reference/nq_1m_master.parquet")
    bt = bars.ts_event.dt.tz_convert(NY)
    bars = bars.assign(mi=bt.dt.floor("min"))
    byday = {d: g for d, g in bars.groupby(bt.dt.strftime("%Y-%m-%d"))}
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)

    feats = []
    for t in J.itertuples():
        fill = pd.Timestamp(t.fill_ts).tz_convert(NY)
        ex = pd.Timestamp(t.exit_ts).tz_convert(NY)
        day = fill.strftime("%Y-%m-%d")
        g = byday.get(day)
        f: dict = {}
        if g is not None:
            w = g[(g.mi >= fill.floor("min")) & (g.mi <= ex.floor("min"))]
            if len(w):
                sgn = 1 if t.direction == "long" else -1
                mae_pts = max(0.0, (t.entry - w.low.min()) if sgn == 1 else (w.high.max() - t.entry))
                mfe_pts = max(0.0, (w.high.max() - t.entry) if sgn == 1 else (t.entry - w.low.min()))
                f["mae_R"] = mae_pts / t.risk_pts
                f["mfe_R"] = mfe_pts / t.risk_pts
                f["mae_pts"], f["mfe_pts"] = mae_pts, mfe_pts
                # post-exit extension: same-direction excursion in the 30m after exit (H2)
                p = g[(g.mi > ex.floor("min")) & (g.mi <= ex.floor("min") + pd.Timedelta(minutes=30))]
                if len(p):
                    ext = (p.high.max() - t.exit_price) if sgn == 1 else (t.exit_price - p.low.min())
                    f["post_ext_R"] = max(0.0, ext) / t.risk_pts
                # r_3: mark at the +3min close
                b3 = w[w.mi <= fill.floor("min") + pd.Timedelta(minutes=3)]
                if len(b3):
                    f["r_3"] = sgn * (b3.close.iloc[-1] - t.entry) / t.risk_pts
        m3 = M[(M.index > fill.floor("min")) & (M.index <= fill.floor("min") + pd.Timedelta(minutes=3))]
        if len(m3):
            f["fw_3"] = (1 if t.direction == "long" else -1) * m3.delta.sum()
        feats.append(f)
    return pd.concat([J, pd.DataFrame(feats, index=J.index)], axis=1)


def main() -> None:
    A = add_paths(run(2.0))          # canon floor
    B = add_paths(run(1.5))          # candidate
    A["yr"], B["yr"] = A.month.str[:4], B.month.str[:4]
    A["win"], B["win"] = A.dollars > 0, B.dollars > 0
    A["key"] = A.fill_ts + "|" + A.direction
    B["key"] = B.fill_ts + "|" + B.direction

    print("\n========== H1: MAE of the winners — are the 1.5R wins scrapes? ==========")
    for name, X in (("rr2.0", A), ("rr1.5", B)):
        w = X[X.win & X.mae_R.notna()]
        print(f"{name} winners ({len(w)}): MAE_R p25/50/75/90 = "
              f"{w.mae_R.quantile(.25):.2f}/{w.mae_R.quantile(.5):.2f}/"
              f"{w.mae_R.quantile(.75):.2f}/{w.mae_R.quantile(.9):.2f}   "
              f">=0.5R DD: {(w.mae_R>=.5).mean()*100:.0f}%   >=0.8R: {(w.mae_R>=.8).mean()*100:.0f}%")
    sa, sb = A.set_index("key"), B.set_index("key")
    shared = sa.index.intersection(sb.index)
    saves = [k for k in shared
             if sb.loc[k, "win"] and not sa.loc[k, "win"]]
    sv = sb.loc[saves]
    print(f"\nGEOMETRY SAVES (win at 1.5, lost/flat at 2.0): {len(sv)}")
    if len(sv):
        print(f"  their MAE_R p50/p90: {sv.mae_R.median():.2f}/{sv.mae_R.quantile(.9):.2f}   "
              f"scrapes (MAE>=0.8R): {(sv.mae_R>=.8).mean()*100:.0f}%   "
              f"R sum {sv.r_multiple.sum():+.1f}")

    print("\n========== H3: is the stop too big? (dead width) ==========")
    for name, X in (("rr2.0", A), ("rr1.5", B)):
        w = X[X.win & X.mae_R.notna()]
        print(f"{name}: winner MAE/stop p75/p90/p95 = {w.mae_R.quantile(.75):.2f}/"
              f"{w.mae_R.quantile(.9):.2f}/{w.mae_R.quantile(.95):.2f}"
              f"   median stop {X.risk_pts.median():.0f}pt (win {X.risk_pts[X.win].median():.0f} / "
              f"lose {X.risk_pts[~X.win].median():.0f})")
    w = B[B.win & B.mae_R.notna()]
    for k in (1.1, 1.25, 1.5):
        newstop = w.mae_R * k                        # stop at k x realized MAE
        # the SAME points move re-measured against the tighter stop
        reR = w.r_multiple / np.maximum(newstop, 1e-9).clip(upper=1.0)
        kept = (newstop < 1.0)                        # trades whose tighter stop survives
        print(f"  counterfactual stop={k:.2f}x MAE: {kept.mean()*100:.0f}% of wins survive; "
              f"their R {w.r_multiple[kept].median():.2f} -> {reR[kept].median():.2f} median "
              f"(engine-1.5R re-measured)")

    print("\n========== H2: post-exit extension — targets not optimistic enough? ==========")
    for name, X in (("rr2.0", A), ("rr1.5", B)):
        tw = X[X.win & (X.exit_reason.str.contains("target")) & X.post_ext_R.notna()]
        print(f"{name} target-hit wins ({len(tw)}): post-exit ext p50/p75 = "
              f"{tw.post_ext_R.median():.2f}R/{tw.post_ext_R.quantile(.75):.2f}R   "
              f"ran >=1R further: {(tw.post_ext_R>=1).mean()*100:.0f}%")

    print("\n========== 3-MIN CUT re-test (r_3<=-0.1106 & fw_3<=-13, calibrated at rr2.0) ==========")
    for name, X in (("rr2.0", A), ("rr1.5", B)):
        v = X[X.r_3.notna() & X.fw_3.notna()]
        flag = (v.r_3 <= CUT_R) & (v.fw_3 <= CUT_FW)
        for yr in ("all", "2025", "2026"):
            s = v if yr == "all" else v[v.yr == yr]
            fl = flag.loc[s.index]
            if fl.sum() < 5:
                continue
            print(f"{name} {yr:>4}: flagged {fl.sum():>3} -> lose {(~s.win[fl]).mean()*100:.0f}%  "
                  f"avgR {s.r_multiple[fl].mean():+.2f}   |   unflagged {(~fl).sum():>3} -> "
                  f"lose {(~s.win[~fl]).mean()*100:.0f}%  avgR {s.r_multiple[~fl].mean():+.2f}")
        # what the cut would have added: exit flagged trades at r_3
        v2 = v.copy()
        cutR = np.where((v2.r_3 <= CUT_R) & (v2.fw_3 <= CUT_FW), v2.r_3, v2.r_multiple)
        print(f"{name}: book {v2.r_multiple.sum():+.1f}R -> with cut {cutR.sum():+.1f}R "
              f"({cutR.sum()-v2.r_multiple.sum():+.1f}R)")


if __name__ == "__main__":
    main()
