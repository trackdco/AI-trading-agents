#!/usr/bin/env python3
"""How much does the canon leave on the table at the exit? — sizing the discretion prize.

ANGUS 2026-07-27: *"we have ran 2 r which was our target, but order flow is still extremely
extremely bullish, lets hold this for a bit longer and target a larger structural level but
trail stops into profit. these are all discretionary things i already do, but theres no way
to mechanically code that shit."*

Entry selection is a hard margin to beat — the canon's rejects already run 19% WR / -$73.8k
(`scripts/canon_attribution.py`). This asks the other question: after the canon exits, how
far did the trade keep going? That is the headroom an exit-discretion layer would be
competing for, and it is measurable from bars alone.

Method: for every TAKEN canon trade, walk the 1m master forward from the fill and record the
maximum favourable excursion in R at several horizons. Compare with the R the canon actually
realized. No lookahead concern — this is post-hoc measurement, not a signal.

    python -m scripts.exit_headroom

READ THE CEILING HONESTLY. Max-excursion is a HINDSIGHT number: nobody exits at the high.
`docs/FINDING-oracle-is-hindsight-books-dont-generalize.md` is the standing warning — an
oracle exit is an upper bound on what judgment could ever win, not a target. The useful
figures here are the SHAPE (how often is there meaningful room at all, and for how long)
rather than the headline dollars.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BARS = ROOT / "data/reference/nq_1m_master.parquet"
BOOK = ROOT / "output/canon_book.parquet"
NY = "America/New_York"
HORIZONS = [15, 30, 60, 120]      # minutes after fill
SESSION_END = 16 * 60             # 16:00 ET, the flatten belt


def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(BARS)
    ts = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    b = b.assign(ts=ts, day=ts.dt.strftime("%Y-%m-%d"),
                 mins=ts.dt.hour * 60 + ts.dt.minute)
    return b.sort_values("ts")


def excursions(book: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    by_day = {d: g for d, g in bars.groupby("day")}
    rows = []
    for t in book.itertuples():
        g = by_day.get(str(t.day))
        if g is None:
            continue
        fill_ts = pd.Timestamp(t.fill)
        fwd = g[g.ts >= fill_ts]
        fwd = fwd[fwd.mins <= SESSION_END]
        if fwd.empty:
            continue
        sign = 1.0 if t.direction == "long" else -1.0
        risk = float(t.risk)
        if risk <= 0:
            continue

        rec = {"day": t.day, "fill": t.fill, "win_": t.win_, "direction": t.direction,
               "risk": risk, "dollars": t.dollars, "realized_R": float(t.R),
               "size": t.size}

        # PATH-CORRECT: the position only has access to excursion while it is still ALIVE.
        # Hold with the ORIGINAL stop and stop measuring the bar it would be taken out —
        # otherwise a trade stopped at 09:00 inherits a rally that happened at 15:00, which
        # it never had. (First cut of this script did exactly that and reported 84% of
        # LOSERS reaching +2R, which is what exposed the error.)
        stop = float(t.stop)
        adverse = (fwd.low <= stop) if sign > 0 else (fwd.high >= stop)
        if adverse.any():
            alive = fwd.loc[:adverse.idxmax()]          # inclusive of the stop-out bar
            rec["stopped_out"] = True
        else:
            alive = fwd
            rec["stopped_out"] = False
        rec["alive_min"] = int((alive.ts.iloc[-1] - fill_ts).total_seconds() // 60)

        for h in HORIZONS:
            w = alive[alive.ts <= fill_ts + pd.Timedelta(minutes=h)]
            if w.empty:
                rec[f"mfe_R_{h}"] = np.nan
                continue
            best = w.high.max() if sign > 0 else w.low.min()
            rec[f"mfe_R_{h}"] = sign * (best - float(t.entry)) / risk
        best_eod = alive.high.max() if sign > 0 else alive.low.min()
        rec["mfe_R_eod"] = sign * (best_eod - float(t.entry)) / risk
        idx = alive.high.idxmax() if sign > 0 else alive.low.idxmin()
        rec["mfe_min_eod"] = int((alive.loc[idx, "ts"] - fill_ts).total_seconds() // 60)
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    if not BARS.exists() or not BOOK.exists():
        raise SystemExit("need data/reference/nq_1m_master.parquet and output/canon_book.parquet")
    C = pd.read_parquet(BOOK)
    taken = C[C["size"] > 0].copy()
    bars = load_bars()
    E = excursions(taken, bars)
    if E.empty:
        raise SystemExit("no overlap between the book and the bar master")

    print(f"{len(E)} taken canon trades matched to bars "
          f"({E.day.nunique()} days, {E.day.min()} .. {E.day.max()})\n")

    win = E[E.dollars > 0]
    loss = E[E.dollars <= 0]
    print(f"winners {len(win)}   losers {len(loss)}\n")

    print("MAX FAVOURABLE EXCURSION vs REALIZED, winners only (R multiples)")
    print(f"{'horizon':<12}{'median MFE':>12}{'mean MFE':>11}{'median realized':>17}"
          f"{'median room':>13}")
    print("-" * 66)
    med_real = win.realized_R.median()
    for h in HORIZONS + ["eod"]:
        col = f"mfe_R_{h}"
        v = win[col].dropna()
        if v.empty:
            continue
        label = f"+{h}m" if h != "eod" else "to 16:00"
        print(f"{label:<12}{v.median():>12.2f}{v.mean():>11.2f}"
              f"{med_real:>17.2f}{v.median() - med_real:>13.2f}")

    print("\nHOW OFTEN IS THERE REAL ROOM PAST THE EXIT? (winners)")
    for extra in (0.5, 1.0, 2.0):
        share = (win.mfe_R_eod >= win.realized_R + extra).mean() * 100
        print(f"  ran >= {extra:>3.1f}R beyond the realized exit : {share:>5.1f}% of winners")

    print("\nHOW LONG WOULD YOU HAVE TO HOLD? (minutes from fill to the peak, winners)")
    q = win.mfe_min_eod.quantile([.25, .5, .75, .9])
    print(f"  p25 {q[.25]:.0f}m   median {q[.5]:.0f}m   p75 {q[.75]:.0f}m   p90 {q[.9]:.0f}m")

    print("\nBY WINDOW (winners, median R):")
    print(f"{'window':<8}{'n':>5}{'realized':>10}{'MFE eod':>10}{'room':>8}")
    print("-" * 41)
    for w_ in sorted(win.win_.dropna().unique()):
        g = win[win.win_ == w_]
        print(f"{w_:<8}{len(g):>5}{g.realized_R.median():>10.2f}"
              f"{g.mfe_R_eod.median():>10.2f}{g.mfe_R_eod.median() - g.realized_R.median():>8.2f}")

    print("\nSANITY — losers, holding to the ORIGINAL stop (should be small by construction)")
    for lvl in (0.5, 1.0, 2.0):
        share = (loss.mfe_R_eod >= lvl).mean() * 100
        print(f"  losers that reached >= {lvl:>3.1f}R while still alive : {share:>5.1f}%")
    print(f"  losers stopped out on the original stop: {loss.stopped_out.mean()*100:.0f}%")

    print("\nWINNERS: did the position SURVIVE past its exit, or would holding have stopped out?")
    print(f"  winners that never touched the original stop before 16:00 : "
          f"{(~win.stopped_out).mean()*100:.0f}%")
    print(f"  median minutes the position stayed alive                  : {win.alive_min.median():.0f}m")

    # ---- the two discretion rules Angus described, priced separately -------------
    print("\n" + "=" * 66)
    print("RULE 1 — cut when flow turns on a trade that WAS in profit (losers)")
    print(f"{'was up >=':<12}{'n':>5}{'% of losers':>13}{'ceiling swing @1lot':>22}")
    print("-" * 52)
    for lvl in (0.5, 1.0, 1.5, 2.0):
        sub = loss[loss.mfe_R_eod >= lvl]
        if not len(sub):
            continue
        swing = (lvl * sub.risk * 20 - sub.dollars).sum()
        print(f"{lvl:<12.1f}{len(sub):>5}{len(sub) / len(loss) * 100:>12.1f}%{swing:>22,.0f}")
    up1 = loss[loss.mfe_R_eod >= 1.0]
    print(f"  those {len(up1)} losers actually realized ${up1.dollars.sum():,.0f}")

    print("\nRULE 2 — extend the runners (winners)")
    print(f"{'left behind >=':<16}{'n':>5}{'% of winners':>14}{'ceiling @1lot':>16}")
    print("-" * 51)
    for lvl in (1.0, 2.0, 3.0):
        sub = win[win.mfe_R_eod >= win.realized_R + lvl]
        if not len(sub):
            continue
        extra = ((sub.mfe_R_eod - sub.realized_R) * sub.risk * 20).sum()
        print(f"{lvl:<16.1f}{len(sub):>5}{len(sub) / len(win) * 100:>13.1f}%{extra:>16,.0f}")

    print("\nRULE 1's CEILING IS THE MORE CREDIBLE ONE. Cutting at +1R exits at a price the")
    print("trade actually traded through — you only have to decide to do it. Rule 2's number")
    print("assumes exiting at the exact high of every winner, which nobody achieves. The")
    print("smaller figure is the closer approximation to reachable money.")

    print("\n" + "=" * 66)
    print("CEILING, NOT A TARGET. Max-excursion is hindsight — nobody exits at the high, and")
    print("docs/FINDING-oracle-is-hindsight-books-dont-generalize.md is the standing warning")
    print("that oracle-shaped books do not generalize. Read the SHAPE (is there room, for how")
    print("long, in which window) — not the headline dollars.")


if __name__ == "__main__":
    main()
