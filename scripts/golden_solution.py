#!/usr/bin/env python3
"""Does adding a REAL volatility exception rescue the cap-kill? Arm B (no 15pt cap, min-stop
15) but stand aside on top-15% NY-range days (>=408pt = June + spikes). Golden 09:40-10:15,
CVD-gated. If win rate + months-green recover while frequency stays up, the vol exception is
the missing piece. Reports."""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from scripts.champion_journal_cvd import conviction, load_cvd_delta  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
GOLD = (dtime(9, 40), dtime(10, 15))


def gw(ts):
    hm = str(ts)[11:16]
    try:
        h, m = int(hm[:2]), int(hm[3:5]); x = h * 60 + m
        return 9 * 60 + 40 <= x <= 10 * 60 + 15
    except Exception:
        return False


def vol_exception_days(df):
    d = df[(df.ts_event >= "2026-02") & (df.ts_event < "2026-08")].copy()
    d["day"] = d.ts_event.dt.strftime("%Y-%m-%d"); d["t"] = d.ts_event.dt.strftime("%H:%M")
    ny = d[(d.t >= "09:30") & (d.t <= "11:00")]
    dr = ny.groupby("day").agg(hi=("high", "max"), lo=("low", "min"))
    dr["range"] = dr.hi - dr.lo
    return set(dr[dr.range >= dr.range.quantile(0.85)].index)


def main():
    allt = [t for t in load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]) if gw(t.ts)]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    volx = vol_exception_days(df)
    print("loading CVD ...", flush=True); delta = load_cvd_delta()
    B = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2, "post_open_min_stop": 15.0})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war]  # NO 15pt cap
        for tt, cfg in ((e3in, books(B)[0]), (e4in, books(B)[1])):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (GOLD[0] <= ft < GOLD[1]):
                    continue
                rows.append(dict(month=m, date=r.trade_date, dollars=r.dollars, win=r.dollars > 0,
                                 volx=r.trade_date in volx, cvd=-conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    V = pd.read_csv("output/regime_vector.csv")[["day", "open_vs_value"]].rename(columns={"day": "date"})
    J = J.merge(V, on="date", how="left")
    G = apply_selection_gate(J, load_selection_filters())

    def show(fr, label):
        mg = fr.groupby("month").dollars.sum(); g = (mg > 0).sum()
        print(f"\n{label}: {len(fr)}t (~{len(fr)/6:.1f}/mo)  ${fr.dollars.sum():+,.0f}  win {fr.win.mean()*100:.0f}%  green {g}/{len(mg)}")
        for m in MONTHS:
            s = fr[fr.month == m]
            if len(s):
                print(f"    {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")

    print(f"\n### GOLDEN — cap-killed + min15, WITH vs WITHOUT volatility exception ###")
    print(f"(vol-exception = top-15% NY range, {len(volx)} days)")
    show(G, "B  cap-killed, ALL days (gated)")
    show(G[~G.volx], "C  cap-killed MINUS vol-exception days (gated)  <-- the proposed shape")
    show(G[G.volx], "   [what we removed: vol-exception days only]")


if __name__ == "__main__":
    main()
