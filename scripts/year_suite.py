#!/usr/bin/env python3
"""Pass-31 YEAR SUITE — the per-year report card over the master dataset.

    python -m scripts.year_suite --year 2023 [--daydir output/triggers_hist2326_days]

Per month of the year, runs (4 workers):
  E3+V8 book (all days) · E4tight15 V0 book (all days) · static switch (blend v1 pick)
  · champion v1.1 (blend + the three cuts) — plus the ORACLE column (better book per day).
Reports trades / win% / points / dollars / maxDD per month per arm. All zero-lookahead:
the switch uses the pre-open regime vector; cuts are the frozen v1.1 rules."""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NY = "America/New_York"
_ctx = {}
YEAR = None
DAYDIR = None


def _init(year, daydir, norm="none"):
    import ast

    from src.backtest.engine import load_backtest_config
    from src.engine.triggers import Trigger
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    _ctx["df"] = df

    # pass-32 NORMALIZATION (Angus: "a 15-point stop cap is a 30-point cap equivalent"):
    # per-month scale factor vs the 2026 calibration era, computed from TRAILING data only.
    #   price: trailing 20-day median close / same measure over Feb-Jul 2026
    #   vol:   trailing 20-day median morning range (08:00-10:15) / same over Feb-Jul 2026
    _ctx["SCALE"] = {}
    if norm != "none":
        morn = df[(df.ts_event.dt.time >= dtime(8, 0)) & (df.ts_event.dt.time <= dtime(10, 15))]
        g = morn.groupby(morn.ts_event.dt.strftime("%Y-%m-%d"))
        rng = (g.high.max() - g.low.min())
        px = g.close.last()
        ref_days = [d for d in rng.index if "2026-02" <= d[:7] <= "2026-07"]
        ref = float((rng if norm == "vol" else px)[ref_days].median())
        series = rng if norm == "vol" else px
        days_sorted = sorted(series.index)
        for mo in {d[:7] for d in days_sorted}:
            prior = [d for d in days_sorted if d < mo + "-01"][-20:]
            if len(prior) >= 10:
                _ctx["SCALE"][mo] = float(series[prior].median()) / ref
    _ctx["NORM"] = norm
    trigs = []
    for p in sorted(Path(daydir).glob(f"{year}-*.csv")):
        if p.stat().st_size == 0:
            continue
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            trigs.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    trigs = [t for t in trigs if t.pattern != "unclassified"]
    _ctx["TRIGS"] = trigs
    V = pd.read_csv("output/regime_vector.csv")
    _ctx["WARDAY"] = {r.day for _, r in V.iterrows()
                      if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    base = load_backtest_config().model_copy(
        update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    _ctx["E3"] = base.model_copy(update={"mgmt_variant": "V8"})
    _ctx["E4"] = base.model_copy(update={"entry_variant": "E4"})


def _tight(ts, s=1.0):
    return [t for t in ts if abs(t.close - t.stop_ref) <= 15.0 * s]


def _cuts(ts, branch):
    """Champion v1.1 CUT2 (B-pattern triggered in the 09h) and CUT3 (rotation book only
    fades). CUT1 (risk<5pts) is fill-dependent -> applied post-sim on trade records."""
    out = []
    for t in ts:
        hour = pd.Timestamp(t.ts).hour
        if t.pattern == "B" and hour == 9:
            continue
        if branch == "E3" and t.htf_flag == "with_trend":
            continue
        out.append(t)
    return out


def _scaled(cfg, s):
    """Point-denominated params scaled by the era factor (pass 32)."""
    if s == 1.0:
        return cfg
    return cfg.model_copy(update={
        "min_stop_points": cfg.min_stop_points * s,
        "t_cancel": cfg.t_cancel * s,
        "front_run": cfg.front_run * s,
        "oversized_stop": cfg.oversized_stop * s,
    })


def run_task(task):
    from src.backtest.engine import simulate
    arm, month = task
    df = _ctx["df"]
    trigs = [t for t in _ctx["TRIGS"] if t.ts[:7] == month]
    end = pd.Timestamp((pd.Timestamp(month + "-01", tz=NY)
                        + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    start = pd.Timestamp(month + "-01", tz=NY) - pd.Timedelta(days=12)
    seg = df[(df.ts_event <= end) & (df.ts_event >= start)].reset_index(drop=True)
    war = _ctx["WARDAY"]
    s = _ctx["SCALE"].get(month, 1.0) if _ctx.get("NORM", "none") != "none" else 1.0
    cfg_e3, cfg_e4 = _scaled(_ctx["E3"], s), _scaled(_ctx["E4"], s)

    def sim(ts, cfg):
        tr, _, _ = simulate(seg, ts, cfg)
        return list(tr)

    if arm == "e3book":
        tr = sim(trigs, cfg_e3)
    elif arm == "e4book":
        tr = sim(_tight(trigs, s), cfg_e4)
    elif arm == "switch":
        tr = sim([t for t in trigs if t.ts[:10] not in war], cfg_e3) \
            + sim(_tight([t for t in trigs if t.ts[:10] in war], s), cfg_e4)
    else:  # v1.1
        e3 = _cuts([t for t in trigs if t.ts[:10] not in war], "E3")
        e4 = _cuts(_tight([t for t in trigs if t.ts[:10] in war], s), "E4")
        tr = sim(e3, cfg_e3) + sim(e4, cfg_e4)
        tr = [r for r in tr if abs(r.entry - r.stop_initial) >= 5.0 * s]  # CUT1
    daily = {}
    for r in tr:
        daily.setdefault((r.trade_date, arm), 0.0)
    if not tr:
        return arm, month, "  0tr", {}
    d = sorted(tr, key=lambda t: t.exit_ts)
    dollars = [t.dollars for t in d]
    pts = sum(t.points * t.size for t in d)
    total = sum(dollars)
    wins = sum(1 for x in dollars if x > 0)
    cum = peak = dd = 0.0
    for x in dollars:
        cum += x
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    per_day = {}
    for r in d:
        per_day[r.trade_date] = per_day.get(r.trade_date, 0.0) + r.dollars
    return arm, month, (f"{len(d):3d}tr {wins / len(d) * 100:4.1f}%win {pts:+7.1f}pts "
                        f"{total:+8,.0f}$ maxDD {dd:6,.0f}$"), per_day


def main():
    global YEAR, DAYDIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", required=True)
    ap.add_argument("--daydir", default="output/triggers_hist2326_days")
    ap.add_argument("--norm", default="none", choices=["none", "price", "vol"],
                    help="scale point-params per month: by price level or morning-range vol")
    a = ap.parse_args()
    months = [f"{a.year}-{m:02d}" for m in range(1, 13)]
    arms = ["e3book", "e4book", "switch", "v1.1"]
    tasks = [(arm, m) for m in months for arm in arms]
    res, days = {}, {}
    with ProcessPoolExecutor(max_workers=4, initializer=_init,
                             initargs=(a.year, a.daydir, a.norm)) as ex:
        for arm, m, line, per_day in ex.map(run_task, tasks):
            res.setdefault(arm, {})[m] = line
            days.setdefault(m, {})[arm] = per_day
    for arm in arms:
        print(f"== {arm} ==", flush=True)
        for m in months:
            if res[arm].get(m, "").strip() != "0tr":
                print(f"  {m}  {res[arm][m]}", flush=True)
    # oracle per month: better of the two books per day
    print("== oracle (better book per day) ==", flush=True)
    for m in months:
        e3d, e4d = days.get(m, {}).get("e3book", {}), days.get(m, {}).get("e4book", {})
        alld = sorted(set(e3d) | set(e4d))
        if not alld:
            continue
        orc = sum(max(e3d.get(x, 0.0), e4d.get(x, 0.0)) for x in alld)
        print(f"  {m}  {orc:+9,.0f}$", flush=True)


if __name__ == "__main__":
    main()
