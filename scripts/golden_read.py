#!/usr/bin/env python3
"""GOLDEN-WINDOW INTRADAY READ (Angus 21 Jul). Re-evaluate at 09:30-09:40 (the cash-open
sit-out) and decide the GOLDEN window (09:40-10:15) action: E3 / E4 / stand-down. This
respects intraday adaptation -- the 8am bias is NOT carried into the golden window.

  * LABEL  : per day, the correct golden action from each book's 09:40-10:15 P&L (CVD-gated,
             canon). E3 if it beats max(E4,0); E4 if it beats max(E3,0); else STAND_DOWN.
  * READ   : open character over 09:30-09:40 -- drive dir/size, overnight-liquidity sweep,
             CVD confirm vs diverge. (Brake's bias def slots in here when it lands.)
  * TEST   : does the 09:30-09:40 read predict the golden action better than the base rate,
             and does a simple interpretable rule hold out-of-fit (train Feb-Apr / test May-Jul)?

    python -m scripts.golden_read
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from scripts.champion_journal_cvd import conviction, load_cvd_delta     # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
TRAIN = {"2026-02", "2026-03", "2026-04"}
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
GOLD = (dtime(9, 40), dtime(10, 15))


# ---------- LABEL: per-day golden book P&L ----------
def golden_book_pnl(allt, df, delta, V, filt):
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
                                                     "win_start": GOLD[0], "win_end": GOLD[1],
                                                     "max_trades_per_day": 2})
    cfg_e3, cfg_e4 = books(base)
    recs = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        for book, cfg, tt in (("E3", cfg_e3, trigs),
                              ("E4", cfg_e4, [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0])):
            tr, _, _ = simulate(seg, tt, cfg)
            rows = []
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (GOLD[0] <= ft < GOLD[1]):
                    continue
                rows.append(dict(date=r.trade_date, dollars=r.dollars, direction=r.direction,
                                 cvd=-conviction(delta, r.fill_ts, r.direction)))
            if rows:
                G = apply_selection_gate(pd.DataFrame(rows).merge(V, on="date", how="left"), filt)
                for date, s in G.groupby("date"):
                    recs.append(dict(date=date, book=book, pnl=s.dollars.sum()))
    P = pd.DataFrame(recs).pivot_table(index="date", columns="book", values="pnl", aggfunc="sum").fillna(0.0)
    for b in ("E3", "E4"):
        if b not in P:
            P[b] = 0.0
    def act(r):
        if r.E3 <= 0 and r.E4 <= 0:
            return "STAND_DOWN"
        return "E3" if r.E3 > r.E4 else "E4"
    P["action"] = P.apply(act, axis=1)
    return P.reset_index()


# ---------- READ: open character 09:30-09:40 ----------
def open_read(df, cvd):
    px = df.copy()
    sd = px.ts_event.dt.tz_convert(NY)
    px["session"] = (sd + pd.Timedelta(hours=6)).dt.date
    sgn = 1  # verified: +delta = buying (corr +0.64)
    rows = []
    for sess, day in px.groupby("session"):
        day = day.set_index("ts_event").sort_index()
        hm = np.array([t.hour * 60 + t.minute for t in day.index])
        drive = day[(hm >= 9 * 60 + 30) & (hm < 9 * 60 + 40)]
        on = day[hm < 9 * 60 + 30]
        if len(drive) < 3 or len(on) < 10:
            continue
        o = drive.open.iloc[0]
        up = (drive.close.iloc[-1] - o) >= 0
        dirn = 1 if up else -1
        d_hi, d_lo = drive.high.max(), drive.low.min()
        swept = (d_hi > on.high.max()) if up else (d_lo < on.low.min())
        cvd_drive = sgn * cvd.reindex(drive.index).fillna(0).sum()
        confirmed = (cvd_drive * dirn) > 0 and abs(cvd_drive) > 100
        diverge = (cvd_drive * dirn) < 0 or abs(cvd_drive) < 50
        rng = d_hi - d_lo
        if swept and diverge:
            label = "manipulation"
        elif confirmed and not swept:
            label = "continuation"
        elif confirmed and swept:
            label = "breakout"           # swept WITH flow -> genuine break
        else:
            label = "unclear"
        rows.append(dict(date=str(sess), odir=("up" if up else "dn"), swept=bool(swept),
                         cvd=int(cvd_drive), confirmed=bool(confirmed), diverge=bool(diverge),
                         rng=round(rng, 1), oc_label=label))
    return pd.DataFrame(rows)


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    df = pd.read_parquet(DATA)
    filt = load_selection_filters()
    print("loading CVD ...", flush=True)
    cvd = load_cvd_delta()
    print("labels: golden book P&L per day ...", flush=True)
    lab = golden_book_pnl(allt, df, cvd, V, filt)
    print("read: open character 09:30-09:40 ...", flush=True)
    rd = open_read(df, cvd)
    M = lab.merge(rd, on="date", how="inner")
    M["mo"] = M.date.str[:7]
    M.to_csv("output/golden_read.csv", index=False)
    print(f"\n{len(M)} days with both label + read\n")

    base = M.action.value_counts(normalize=True).mul(100).round(0)
    print("golden correct-action base rate:")
    print(M.action.value_counts().to_string(), f"\n  (majority = {M.action.mode()[0]} @ {base.max():.0f}%)\n")

    print("=== open-character label  x  correct golden action ===")
    print(pd.crosstab(M.oc_label, M.action).to_string())
    print("\n=== does the open read separate STAND-DOWN from TRADE? ===")
    M["tradeable"] = M.action != "STAND_DOWN"
    print(pd.crosstab(M.oc_label, M.tradeable).to_string())

    # simple interpretable rule, fit on TRAIN, scored on TEST
    tr, te = M[M.mo.isin(TRAIN)], M[~M.mo.isin(TRAIN)]
    # rule candidate: manipulation/unclear -> STAND_DOWN; continuation/breakout -> trade the drive book
    def rule(r):
        if r.oc_label in ("manipulation", "unclear"):
            return "STAND_DOWN"
        return "E4" if r.confirmed else "E3"
    for name, s in (("TRAIN Feb-Apr", tr), ("TEST May-Jul", te)):
        if not len(s):
            continue
        pred = s.apply(rule, axis=1)
        acc = (pred == s.action).mean() * 100
        # stand-down sub-accuracy
        sd = s[s.action == "STAND_DOWN"]
        sd_hit = (sd.apply(rule, axis=1) == "STAND_DOWN").mean() * 100 if len(sd) else 0
        print(f"\n  {name}: rule accuracy {acc:.0f}%  (n={len(s)}, base {s.action.value_counts(normalize=True).max()*100:.0f}%)"
              f"   stand-down recall {sd_hit:.0f}%")


if __name__ == "__main__":
    main()
