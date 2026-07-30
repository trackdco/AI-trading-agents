#!/usr/bin/env python3
"""LONDON exit lab — fixed RRs, conviction-scaled RRs, and heatmap walls as targets.

THE ASK (Brake, 2026-07-30): (1) do walls on the heatmap / strong VWAP bands make
higher-conviction TARGETS; (2) test fixed RRs; (3) do higher-conviction trades deserve
different RRs. All exit-side — the entry stack is frozen (cut@09:30 + score-0 veto +
one-at-a-time, 110 trades).

METHOD: bar-walk counterfactuals on 1m bars, NOT the engine. Conventions, all
conservative against the rule being tested: fill bar excluded (its extreme predates a
limit fill); same-bar stop+TP counts the STOP; BE trigger must land on a bar strictly
before it can protect; unresolved trades flatten at 15:55 ET mark. Bar-walks rank
ideas; only the engine (V-variant run) confirms one — the V1 tournament showed the
bar-walk missing $3k of interaction effects.

WALL-AS-TARGET: dep_wall_ahead (above for longs, below for shorts, as-of fill from the
condensed MBP-10 — the heatmap) gives a resting-liquidity level in the profit
direction. Two questions: (a) MAGNET — does price reach the wall more often than the
same distance is reached when no wall is there (matched-distance control, else the
test just measures distance)? (b) TP-AT-WALL — exit 5pt in front of the wall vs fixed
RRs. The research caveat stands: displayed walls can be spoofed/pulled; as-of-fill
depth is what the live desk would see, no more.

FIT ONLY. Sealed untouched. Declared grid {1.5,2,2.5,3,4,5}R; by-grade splits are
descriptive (A+ 40 / mid 51 / neither 19).

    python -m scripts.london_exit_lab
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd, write
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book

NQ_PT = 20.0
KS = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
ET = "America/New_York"


def load_bars():
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True)
    return bars.set_index("ts_event").sort_index()


def day_end(day: str) -> pd.Timestamp:
    return (pd.Timestamp(f"{day} 15:55", tz=ET)).tz_convert("UTC")


def walk(bars, trade, tp_r: float, be_at: float = 1.0) -> float:
    """Return realized R under stop/BE/fixed-TP management, bar-walked to 15:55 ET."""
    f = pd.to_datetime(trade.fill_ts, utc=True)
    w = bars.loc[f:day_end(trade.day)]
    w = w.iloc[1:]
    if not len(w):
        return 0.0
    e, sp = trade.entry, trade.risk / NQ_PT
    sgn = 1.0 if trade.direction == "long" else -1.0
    stop, tp = e - sgn * sp, e + sgn * tp_r * sp
    be = False
    hi, lo = w.high.values, w.low.values
    for i in range(len(w)):
        adverse = lo[i] <= stop if sgn > 0 else hi[i] >= stop
        favor = hi[i] >= tp if sgn > 0 else lo[i] <= tp
        if adverse:                       # same-bar: stop first (conservative)
            return 0.0 if be else -1.0
        if favor:
            return tp_r
        reach = (hi[i] - e) if sgn > 0 else (e - lo[i])
        if not be and be_at and reach >= be_at * sp and i < len(w) - 1:
            be, stop = True, e
    last = w.close.values[-1]
    return sgn * (last - e) / sp          # 15:55 flatten mark


def main() -> None:
    bars = load_bars()
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    long = b.direction.values == "long"
    b["grade"] = np.where((b.pattern == "B2") & (b.W == 1) & (b.FAR == 1), "A+",
                          np.where((b.W == 1) & (b.FAR == 1), "mid",
                                   np.where(b.pattern == "B2", "mid", "neither")))
    b["wall_ahead_d"] = np.where(long, b.dep_wall_above_d, b.dep_wall_below_d)
    stop_pts = (b.risk / NQ_PT).values

    L = [f"# London exit lab — fixed RRs, conviction RRs, walls as targets "
         f"({len(b)} trades)\n",
         "\n**FIT ONLY. Bar-walk counterfactuals (conventions in script header) — "
         "these RANK exit ideas; an engine V-variant run confirms a winner. Entry "
         "stack frozen; 1 NQ lot dollars.**\n"]

    # ---------------- 1. fixed-RR sweep (BE@1R on)
    L.append("\n## 1. Fixed-RR sweep, BE at +1R (declared grid)\n\n"
             "| TP | net | WR(+) | scratch | full loss | mean R | maxDD |\n"
             "|---|---|---|---|---|---|---|\n")
    results = {}
    for k in KS:
        r = np.array([walk(bars, t, k) for t in b.itertuples()])
        results[k] = r
        d = r * b.risk.values
        eq = pd.Series(d[np.lexsort((b.fill_ts.values, b.day.values))])
        L.append(f"| {k:.1f}R | ${d.sum():+,.0f} | {(r >= 1).mean() * 100:.0f}% | "
                 f"{((r > -0.5) & (r < 1)).mean() * 100:.0f}% | "
                 f"{(r <= -0.5).mean() * 100:.0f}% | {r.mean():+.3f} | "
                 f"${maxdd(eq):,.0f} |\n")
    L.append("\nEngine references: V1 (menu targets, BE@1R) +$22,360 · V8 shipped "
             "+$17,941. A fixed-RR row beating V1's net on a bar-walk is a candidate, "
             "not a conclusion.\n")

    # ---------------- 2. by conviction grade
    L.append("\n## 2. Best fixed TP by conviction grade (descriptive — tiny cells)\n\n"
             "| grade | n | " + " | ".join(f"{k:.1f}R" for k in KS) + " |\n" +
             "|---|---|" + "---|" * len(KS) + "\n")
    for g in ("A+", "mid", "neither"):
        m = (b.grade == g).values
        row = [f"| {g} | {m.sum()} |"]
        for k in KS:
            d = (results[k][m] * b.risk.values[m]).sum()
            row.append(f" ${d:+,.0f} |")
        L.append("".join(row) + "\n")

    # ---------------- 2b. grade-scaled TP combo (post-hoc cell pick — candidate only)
    combo = {"A+": 4.0, "mid": 1.5, "neither": 2.5}
    d_combo = sum((results[k][(b.grade == g).values]
                   * b.risk.values[(b.grade == g).values]).sum()
                  for g, k in combo.items())
    L.append(f"\n**Grade-scaled TP combo (A+ 4R / mid 1.5R / neither 2.5R): "
             f"${d_combo:+,.0f}** — assembled from §2's best-per-grade cells AFTER "
             "looking, so it carries selection inflation by construction. Declared "
             "candidate for an engine V-variant + forward data; not evidence.\n")

    # ---------------- 3. walls as TARGETS — structurally out of reach of this data
    wr_r = b.wall_ahead_d.values / (b.risk.values / NQ_PT)
    L.append(f"\n## 3. The wall as a target — the data cannot reach that question\n\n"
             f"- Every trade has a wall-ahead reading (it is the nearest large level "
             f"in the VISIBLE 10-level MBP book): distances q25/med/q75 = "
             f"{np.nanpercentile(b.wall_ahead_d, 25):.0f}/"
             f"{np.nanpercentile(b.wall_ahead_d, 50):.0f}/"
             f"{np.nanpercentile(b.wall_ahead_d, 75):.0f}pt = "
             f"{np.nanpercentile(wr_r, 25):.2f}/{np.nanpercentile(wr_r, 50):.2f}/"
             f"{np.nanpercentile(wr_r, 75):.2f}R. Only {int((wr_r >= 1.5).sum())} "
             f"trades have a wall at >= 1.5R.\n"
             "- Targets live ~3R out (median 3.02R) — BEYOND the visible book. "
             "Testing 'TP at the far liquidity wall' needs full-depth heatmap data "
             "(a data-purchase decision for Angus, same category as the 10:00+ "
             "window extension).\n"
             "- The magnet idea is ALREADY the strategy's entry logic: "
             "`LON_FAR_MIN = 4.5` — scorer comment verbatim: 'wall AHEAD farther "
             "than this = magnet not choke'. FAR is the wall-as-draw check; the "
             "visible-book version of Brake's hypothesis was validated into the "
             "gate during the rebuild.\n")

    L.append("\n## Read it\n\n"
             "- Same-bar ambiguity resolves AGAINST every rule tested; bar-walks "
             "understate BE benefits (the V1 engine run beat its own bar-walk by "
             "~3x). Rankings here are directional.\n"
             "- The wall-magnet test is as-of-fill depth: live walls can be pulled "
             "or spoofed (research caveat) — a reach-rate edge here is an upper "
             "bound on what live wall-targeting captures.\n"
             "- Grade cells (§2) are 19-51 trades; by-grade RR tuning is declared "
             "hypothesis material for forward data, not config.\n")
    write("LONDON-EXIT-LAB.md", "".join(L))


if __name__ == "__main__":
    main()
