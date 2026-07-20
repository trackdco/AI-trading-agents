"""Pass-32 (Angus): STAND-DOWN oracle for ALL years + the 2025 hostility diagnosis.
For each year 2023-2025: both books simulated per month, per-day P&L kept, oracle picks
better-book-or-flat per day; trade-level W/L for the oracle's chosen days; year diagnostics
that compare 2025's tape against its neighbours."""
import ast
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")

NY = "America/New_York"
_ctx = {}


def _init():
    from src.backtest.engine import load_backtest_config
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    _ctx["df"] = df
    base = load_backtest_config().model_copy(
        update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    _ctx["E3"] = base.model_copy(update={"mgmt_variant": "V8"})
    _ctx["E4"] = base.model_copy(update={"entry_variant": "E4"})


def _load_month(month):
    from src.engine.triggers import Trigger
    trigs = []
    for p in sorted(Path("output/triggers_hist2326_days").glob(f"{month}-*.csv")):
        if p.stat().st_size == 0:
            continue
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            trigs.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in trigs if t.pattern != "unclassified"]


def run_task(task):
    from src.backtest.engine import simulate
    book, month = task
    df = _ctx["df"]
    trigs = _load_month(month)
    if book == "E4":
        trigs = [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
    end = pd.Timestamp((pd.Timestamp(month + "-01", tz=NY)
                        + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    start = pd.Timestamp(month + "-01", tz=NY) - pd.Timedelta(days=12)
    seg = df[(df.ts_event <= end) & (df.ts_event >= start)].reset_index(drop=True)
    tr, _, _ = simulate(seg, trigs, _ctx[book])
    out = []
    for r in tr:
        risk = abs(r.entry - r.stop_initial)
        out.append(dict(day=r.trade_date, book=book, dollars=r.dollars,
                        pts=r.points * r.size, win=r.dollars > 0, risk=risk,
                        pattern=r.pattern, fill=r.fill_ts[11:16]))
    return month, book, out


def main():
    months = [f"{y}-{m:02d}" for y in (2023, 2024, 2025) for m in range(1, 13)] + ["2026-01"]
    tasks = [(b, m) for m in months for b in ("E3", "E4")]
    recs = []
    with ProcessPoolExecutor(max_workers=4, initializer=_init) as ex:
        for month, book, out in ex.map(run_task, tasks):
            recs += out
    T = pd.DataFrame(recs)
    T.to_csv("output/allyears_book_trades.csv", index=False)
    day_pl = T.groupby(["day", "book"]).dollars.sum().unstack(fill_value=0.0)
    for b in ("E3", "E4"):
        if b not in day_pl:
            day_pl[b] = 0.0
    day_pl["best"] = day_pl[["E3", "E4"]].max(axis=1)
    day_pl["oracle_sd"] = day_pl["best"].clip(lower=0)
    day_pl["pick"] = day_pl[["E3", "E4"]].idxmax(axis=1)
    day_pl.loc[day_pl["best"] < 0, "pick"] = "FLAT"
    day_pl = day_pl.reset_index()
    day_pl["month"] = day_pl.day.str[:7]
    day_pl["year"] = day_pl.day.str[:4]
    day_pl.to_csv("output/allyears_daily_books.csv", index=False)

    print("=== STAND-DOWN ORACLE, monthly, all years ===")
    for y, g in day_pl.groupby("year"):
        tot = g.oracle_sd.sum()
        flat = (g.pick == "FLAT").sum()
        # trade stats on chosen days
        chosen = []
        for _, r in g[g.pick != "FLAT"].iterrows():
            chosen.append((r.day, r.pick))
        ch = pd.DataFrame(chosen, columns=["day", "book"])
        tt = T.merge(ch, on=["day", "book"])
        w, n = int(tt.win.sum()), len(tt)
        print(f"\n{y}: SD-oracle ${tot:+,.0f} | flat {flat}/{len(g)} days | "
              f"trades {n} W{w}/L{n - w} = {w / n * 100:.0f}% win | "
              f"pick mix {dict(g.pick.value_counts())}")
        for m, gm in g.groupby("month"):
            print(f"  {m}  ${gm.oracle_sd.sum():+9,.0f}  flat {(gm.pick == 'FLAT').sum():2d}/{len(gm)}")

    print("\n=== 2025 DIAGNOSIS vs neighbours ===")
    df = _ctx.get("df") or pd.read_parquet("data/reference/nq_1m_master.parquet")
    morn = df[(df.ts_event.dt.time >= dtime(8, 0)) & (df.ts_event.dt.time <= dtime(10, 15))]
    g = morn.groupby(morn.ts_event.dt.strftime("%Y-%m-%d"))
    st = pd.DataFrame({"rng": g.high.max() - g.low.min(), "open": g.open.first(),
                       "close": g.close.last()})
    st["y"] = st.index.str[:4]
    st["drift"] = (st.close - st.open).abs() / st.rng          # directional efficiency
    for y in ("2023", "2024", "2025"):
        gy = day_pl[day_pl.year == y]
        sy = st[st.y == y]
        both_red = ((gy.E3 < 0) & (gy.E4 < 0)).mean()
        ty = T[T.day.str.startswith(y)]
        print(f"{y}: med morn range {sy.rng.median():5.1f}pts | med range/price "
              f"{(sy.rng / sy.close).median() * 100:.2f}% | drift-eff {sy.drift.median():.2f} | "
              f"both-books-red days {both_red * 100:.0f}% | "
              f"book win% E3 {ty[ty.book == 'E3'].win.mean() * 100:.0f} E4 {ty[ty.book == 'E4'].win.mean() * 100:.0f} | "
              f"med |day-oracle| ${gy.best.abs().median():.0f}")


if __name__ == "__main__":
    main()
