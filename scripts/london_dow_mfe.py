#!/usr/bin/env python3
"""LONDON day-of-week / time-of-day ledger + the near-miss losers (MFE analysis).

THE ASK (Brake, 2026-07-30): (a) what each weekday makes, split by the three half-hours
of the cut window; (b) "trades going up then coming back down to stop loss."

(b) is MAX FAVORABLE EXCURSION: walk each trade's 1m bars from fill to exit and record
the best unrealized R it reached. A loser with MFE >= 0.5R "went up then came back".
This feeds the BE-at-1R question the strategy doc already lists as a tournament
variant — so the what-if is priced here too, with conservative conventions:

  BE-at-XR what-if: once a trade's MFE first reaches X (in a bar STRICTLY BEFORE its
  exit bar — same-bar spikes don't count, intrabar order is unknowable), a stop at
  entry is assumed. If any LATER bar trades back to entry, the trade exits at 0R
  (winners that dipped die at BE too — the rule cuts both ways). Slippage ignored on
  the BE exit (flatters the rule slightly; stated).

Book = the working stack (cut@09:30 + score-0 veto + one-at-a-time). FIT ONLY.
Descriptive; day-of-week cells are tiny and NOT charged — patterns here are for
eyeballs and forward watching, not rules (a weekday rule would need its own prereg).

    python -m scripts.london_dow_mfe
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd, write
from scripts.london_conviction import lonmins
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book

NQ_PT = 20.0
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri"]
BUCKETS = [(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"), (540, 570, "09:00-09:30")]


def mfe_walk(b: pd.DataFrame) -> pd.DataFrame:
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True)
    bars = bars.set_index("ts_event").sort_index()
    long = b.direction.values == "long"
    f = pd.to_datetime(b.fill_ts, utc=True)
    x = pd.to_datetime(b.exit_ts, utc=True)
    stop_pts = (b.risk / NQ_PT).values
    mfe_r, be05, be10 = np.zeros(len(b)), np.zeros(len(b), bool), np.zeros(len(b), bool)
    ret05, ret10 = np.zeros(len(b), bool), np.zeros(len(b), bool)
    for i in range(len(b)):
        w = bars.loc[f.iloc[i]:x.iloc[i]]
        # the FILL bar's favorable extreme usually predates the fill (a long limit at
        # support fills as price falls INTO it from above — the bar high came first),
        # so excursion counts only bars STRICTLY AFTER the fill minute
        w = w.iloc[1:]
        if not len(w):
            mfe_r[i] = 0.0     # entered and resolved inside the fill minute
            continue
        e = b.entry.iloc[i]
        fav = (w.high - e) if long[i] else (e - w.low)
        adv_touch = (w.low <= e) if long[i] else (w.high >= e)
        r = fav.values / stop_pts[i]
        mfe_r[i] = max(r.max(), 0.0)
        for X, trig_arr, ret_arr in ((0.5, be05, ret05), (1.0, be10, ret10)):
            hit = np.where(r >= X)[0]
            # trigger must land strictly before the exit bar
            hit = hit[hit < len(w) - 1]
            if len(hit):
                trig_arr[i] = True
                ret_arr[i] = bool(adv_touch.values[hit[0] + 1:].any())
    b = b.copy()
    b["mfe_r"], b["be05_trig"], b["be05_ret"] = mfe_r, be05, ret05
    b["be10_trig"], b["be10_ret"] = be10, ret10
    return b


def main() -> None:
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    b["mins"] = lonmins(b.fill)
    b["dow"] = pd.to_datetime(b.day).dt.day_name().str[:3]
    b["bucket"] = pd.cut(b.mins, [x[0] for x in BUCKETS] + [570], right=False,
                         labels=[x[2] for x in BUCKETS])

    L = [f"# London by weekday and half-hour + the near-miss losers ({len(b)} trades)\n",
         "\n**Working stack, FIT ONLY, descriptive — weekday cells are 15-30 trades "
         "and are NOT statistically charged. For eyeballs and forward watching; a "
         "weekday rule would need its own prereg.**\n"]

    # ---------------- 1. day of week
    L.append("\n## 1. Day of week\n\n| day | n | WR | mean R | net | avg/day traded | "
             "2025 | 2026 |\n|---|---|---|---|---|---|---|---|\n")
    for d in DOW:
        g = b[b.dow == d]
        if not len(g):
            continue
        e = {era: g[g.era == era] for era in ("2025", "2026")}
        L.append(f"| {d} | {len(g)} | {(g.R > 0).mean() * 100:.0f}% | "
                 f"{g.R.mean():+.3f} | ${g.dollars.sum():+,.0f} | "
                 f"${g.dollars.sum() / g.day.nunique():+,.0f} | "
                 f"${e['2025'].dollars.sum():+,.0f} | ${e['2026'].dollars.sum():+,.0f} |\n")

    # ---------------- 2. day x half-hour matrix (net, with n)
    L.append("\n## 2. Weekday x half-hour (net $, n in brackets)\n\n| day | " +
             " | ".join(x[2] for x in BUCKETS) + " | day total |\n" +
             "|---|" + "---|" * (len(BUCKETS) + 1) + "\n")
    for d in DOW:
        g = b[b.dow == d]
        if not len(g):
            continue
        cells = []
        for _, _, lab in BUCKETS:
            gb = g[g.bucket == lab]
            cells.append(f"${gb.dollars.sum():+,.0f} ({len(gb)})" if len(gb) else "—")
        L.append(f"| {d} | " + " | ".join(cells) + f" | ${g.dollars.sum():+,.0f} |\n")

    # ---------------- 3. monthly ledger
    mo = b.assign(mo=b.day.str[:7]).groupby("mo").agg(
        n=("R", "size"), net=("dollars", "sum"), wr=("R", lambda s: (s > 0).mean()))
    L.append("\n## 3. Month by month\n\n| month | n | WR | net |\n|---|---|---|---|\n")
    for m, r in mo.iterrows():
        L.append(f"| {m} | {int(r.n)} | {r.wr * 100:.0f}% | ${r.net:+,.0f} |\n")

    # ---------------- 4. near-miss losers (MFE)
    b = mfe_walk(b)
    Ls = b[b.R <= 0]
    L.append(f"\n## 4. Trades that went up, then came back to the stop (MFE on 1m "
             f"bars)\n\nOf {len(Ls)} losers:\n\n| reached before dying | count | "
             "share of losers | dollars lost in these |\n|---|---|---|---|\n")
    for X in (0.25, 0.5, 0.75, 1.0):
        g = Ls[Ls.mfe_r >= X]
        L.append(f"| >= +{X:.2f}R unrealized | {len(g)} | "
                 f"{len(g) / len(Ls) * 100:.0f}% | ${g.dollars.sum():+,.0f} |\n")
    L.append(f"\nMedian loser MFE: {Ls.mfe_r.median():+.2f}R. Median WINNER MFE: "
             f"{b[b.R > 0].mfe_r.median():+.2f}R.\n")

    # the BE what-if, both cuts
    L.append("\n### BE-at-XR what-if (conservative conventions in the header)\n\n"
             "| rule | losers saved -> 0R | winners killed -> 0R | net change | "
             "new book net |\n|---|---|---|---|---|\n")
    for X, trig, ret in (("BE at +0.5R", "be05_trig", "be05_ret"),
                         ("BE at +1.0R", "be10_trig", "be10_ret")):
        lose_saved = b[(b.R <= 0) & b[trig] & b[ret]]
        win_killed = b[(b.R > 0) & b[trig] & b[ret]]
        delta = -lose_saved.dollars.sum() - win_killed.dollars.sum()
        L.append(f"| {X} | {len(lose_saved)} (${-lose_saved.dollars.sum():+,.0f}) | "
                 f"{len(win_killed)} (${-win_killed.dollars.sum():+,.0f}) | "
                 f"${delta:+,.0f} | ${b.dollars.sum() + delta:+,.0f} |\n")
    L.append("\nV8 management already takes partials; this what-if layers a BE stop on "
             "top and is an APPROXIMATION on 1m bars (same-bar spikes excluded, BE "
             "slippage ignored). If the number is material it justifies running the "
             "real engine tournament (V-variants, strategy doc §8) — it does not "
             "justify adopting anything from a bar-walk.\n")
    write("LONDON-DOW-MFE.md", "".join(L))


if __name__ == "__main__":
    main()
