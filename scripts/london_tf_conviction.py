#!/usr/bin/env python3
"""LONDON timeframe conviction — which entry TF carries the edge, asked properly. FIT ONLY.

THE ASK (Brake, 2026-07-30): "what timeframe gives highest conviction for entry?" The naive
answer is the book's per-TF table, but the book's `tf` column is not a clean fact — it is
downstream of TWO constitution rules the London rebuild never implemented, and of one
phenomenon the constitution mis-describes.

WHAT THE DATA ACTUALLY SHOWS (all measured here, on the fit census/population):
  - Literal simultaneity NEVER occurs: no two census triggers share (minute, direction) —
    9,352 groups of exactly 1. Strategy-doc §1's "if multiple TFs show valid triggers
    simultaneously, take the highest TF" targets a case with ZERO occurrences. Different
    TF grids close on different minutes.
  - The real phenomenon is SAME-ORDER TWINS: TF grids detect the same level 1-4 minutes
    apart (median 1) and converge on identical (direction, entry, stop) resting at the
    same fill — **329 population groups covering 713 rows, multiplicity up to 4**. Live,
    the first trigger places the order and the later TFs change nothing; the backtest
    simulates each independently and the book COUNTS THE FILL TWICE (a doubled position
    at what is supposed to be flat 1 lot).
  - "Highest TF wins" is not even live-causal here: the LOWEST TF triggers first in
    290/329 groups (finer grid sees the level sooner). The live rule is first-order-wins;
    the doc's rule would require cancel-and-replace on later confirmation.
  - ENGINE FLAG: 46/329 twin groups get DIVERGENT simulated outcomes from the identical
    order (same entry/stop/fill, different exits — e.g. 2026-04-20 +0.26R vs -1.01R),
    because V8 management context leaks from the trigger candle. Live there is ONE exit.
    Which twin's simulation is "the" outcome is an engine question — flagged for Pat's
    lane; both dedup readings are priced below so the ambiguity is bounded.
  - Strategy-doc §5 "one position at a time, no overlapping trades ever" is also
    unimplemented: 31/187 full-window entries (26/144 cut) occur while a prior position
    is open.

REPORTED, NOT FIXED: the frozen book stays the strategy of record until ANGUS rules.
Adoption of any variant = ruling + prereg rev + runner re-rehearsal (rev-3-style).

WHAT IS MEASURED:
  1. Per-TF cells on the book as-is — era split, Wilson LB, worst-of-4 permutation.
     (Composition, not entry-rule quality — the causal answers are 2-4.)
  2. LEVEL BACKING as the conviction signal: distinct TFs converging on the same order
     (the honest version of prereg H1's "concurring timeframes", on taken trades).
  3. Constitution variants, priced:  V0 as-is · V-DEDUP-FIRST (first-order-wins, the
     live-causal collapse of twins) · V-DEDUP-HIGH (doc's highest-TF reading) ·
     V-SERIAL (one-at-a-time on V0) · V-BOTH (dedup-first + serial).
  4. Single-TF gate counterfactuals (gate change, hypothesis-grade by construction).

    python -m scripts.london_tf_conviction
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd, write
from scripts.london_conviction import (CUT_MIN, era_cells, fmt_cell, grade, lonmins,
                                       perm_max_null)
from scripts.london_holdout_report import load_pop

SEED = 20260730
TF_ORD = {"1min": 1, "2min": 2, "3min": 3, "5min": 5}
ORDER_KEY = ["day", "direction", "entry", "stop", "fill"]   # one resting limit order


def tag_orders(P: pd.DataFrame) -> pd.DataFrame:
    """Attach order-group id, backing count (distinct TFs on the order), and first/high
    keep-flags for the two dedup readings."""
    P = P.copy()
    P["tfo"] = P.tf.map(TF_ORD)
    g = P.groupby(ORDER_KEY, sort=False)
    P["order_id"] = g.ngroup()
    P["backing"] = g.tf.transform("nunique")
    first_ts = g.ts.transform("min")
    P["keep_first"] = P.ts == first_ts
    # ties on ts impossible across TFs (verified: zero same-minute census collisions);
    # within-TF duplicates keep one row deterministically
    P.loc[P.keep_first, "keep_first"] = ~P[P.keep_first].duplicated("order_id")
    top = g.tfo.transform("max")
    P["keep_high"] = P.tfo == top
    P.loc[P.keep_high, "keep_high"] = ~P[P.keep_high].duplicated("order_id")
    return P


def serial_walk(cand: pd.DataFrame, day_stop: float = 400.0) -> pd.DataFrame:
    """One position at a time, chronological, causal. Same realized day-stop accounting
    as the L4 walk (outcome added to the day's P&L after the take decision)."""
    rows = cand.sort_values(["day", "fill_ts"], kind="mergesort").reset_index(drop=True)
    f = pd.to_datetime(rows.fill_ts, utc=True)
    x = pd.to_datetime(rows.exit_ts, utc=True)
    taken = np.zeros(len(rows), dtype=bool)
    for day, g in rows.groupby("day", sort=False):
        open_until = pd.Timestamp.min.tz_localize("UTC")
        pl = 0.0
        for i in g.index:
            if pl <= -day_stop or f[i] < open_until:
                continue
            taken[i] = True
            open_until = x[i]
            pl += rows.at[i, "dollars"]
    return rows[taken]


def price(b: pd.DataFrame) -> dict:
    b = b.sort_values(["day", "fill_ts"], kind="mergesort")
    out = {"n": len(b), "days": b.day.nunique(), "net": float(b.dollars.sum()),
           "wr": float((b.R > 0).mean()), "r": float(b.R.mean()),
           "dd": maxdd(b.dollars.reset_index(drop=True))}
    for era in ("2025", "2026"):
        g = b[b.era == era]
        out[era] = (f"{len(g)}/{(g.R > 0).mean() * 100:.0f}%/{g.R.mean():+.2f}"
                    if len(g) else "—")
    twins = int((b.groupby(ORDER_KEY).size() > 1).sum())
    over = 0
    bb = b.assign(f=pd.to_datetime(b.fill_ts, utc=True),
                  x=pd.to_datetime(b.exit_ts, utc=True))
    for day, g in bb.groupby("day"):
        g = g.sort_values("f")
        for i in range(1, len(g)):
            if (g.iloc[:i].x > g.iloc[i].f).sum():
                over += 1
    out["twins"] = twins
    out["overlaps"] = over
    return out


def prow(name: str, p: dict) -> str:
    return (f"| {name} | {p['n']} | {p['days']} | ${p['net']:+,.0f} | "
            f"{p['wr'] * 100:.0f}% | {p['r']:+.3f} | ${p['dd']:,.0f} | "
            f"{p['2025']} | {p['2026']} | {p['twins']} | {p['overlaps']} |\n")


def main() -> None:
    rng = np.random.default_rng(SEED)
    P = tag_orders(load_pop("fit"))
    P["mins"] = lonmins(P.fill)
    Pc = P[P.mins < CUT_MIN]

    b = lon_book(Pc, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    bf = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    R, eras = b.R.values.astype(float), b.era.values
    base_r = float(b.R.mean())

    L = ["# London TF conviction — twins, backing, and the per-TF ledger\n",
         "\n**FIT ONLY. Sealed 2023/24 untouched. The frozen book is unchanged by this "
         "doc — variants are measurements, adoption is an ANGUS ruling.**\n"]

    # ---------------- 0. integrity finding
    p0 = price(b)
    pop_groups = int((P.groupby(ORDER_KEY).size() > 1).sum())
    pop_rows = int(P.groupby(ORDER_KEY).size().pipe(lambda s: s[s > 1].sum()))
    L.append(f"\n## 0. Integrity finding (REPORTED, NOT FIXED)\n\n"
             f"Same-order twins: **{pop_groups} population groups / {pop_rows} rows** "
             f"(TF grids detecting one level 1-4 min apart, converging on identical "
             f"direction+entry+stop+fill — one resting order, simulated 2-4 times). On "
             f"the cut book: **{p0['twins']} twin groups survive selection** = a doubled "
             f"position at flat-1-lot sizing; plus **{p0['overlaps']}/{p0['n']} entries "
             f"while a prior position was open** (doc §5 violation). Doc §1's "
             f"'simultaneous triggers → highest TF' can never fire as written (zero "
             f"same-minute census collisions) and is not live-causal anyway — the "
             f"LOWEST TF triggers first in 290/329 groups, so live behaviour is "
             f"first-order-wins. ENGINE FLAG for Pat: 46/329 twin groups produce "
             f"divergent simulated exits from the identical order (V8 management "
             f"context leaks from the trigger candle); live there is one exit.\n")

    # ---------------- 1. per-TF cells
    L.append("\n## 1. Per-TF cells on the book as it stands (cut@09:30; charged "
             "worst-of-4)\n\n| tf | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | "
             "p(worst-of-4) | grade | full-book n/WR/R |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
    tf_masks = [(tf, (b.tf == tf).values) for tf in ("1min", "2min", "3min", "5min")]
    M = np.column_stack([m.astype(float) for _, m in tf_masks])
    null_tf = perm_max_null(R, eras, M, rng)
    for tf, m in tf_masks:
        c = era_cells(b, m)
        lift = c["pool"]["r"] - base_r
        p = float((null_tf >= abs(lift)).mean())
        gf = bf[bf.tf == tf]
        L.append(f"| {tf} | {fmt_cell(c)} | {lift:+.3f} | {p:.3f} | {grade(c)} | "
                 f"{len(gf)}/{(gf.R > 0).mean() * 100:.0f}%/{gf.R.mean():+.2f} |\n")
    L.append("\n(Composition, not entry-rule quality — a TF cell mixes solo triggers "
             "with twin members. Sections 2-4 are the causal reads.)\n")

    # ---------------- 2. level backing
    L.append("\n## 2. Level backing — distinct TFs converging on the taken trade's "
             "order (the honest 'concurring timeframes' signal; charged worst-of-K)\n\n"
             "| backing | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | "
             "p(worst-of-K) | grade |\n|---|---|---|---|---|---|---|---|---|---|\n")
    b["backing_c"] = np.minimum(b.backing, 3)
    cm = [(int(v), (b.backing_c == v).values) for v in sorted(b.backing_c.unique())]
    MC = np.column_stack([m.astype(float) for _, m in cm])
    null_c = perm_max_null(R, eras, MC, rng)
    for v, m in cm:
        c = era_cells(b, m)
        lift = c["pool"]["r"] - base_r
        p = float((null_c >= abs(lift)).mean())
        lab = f"{v}+" if v == 3 else str(v)
        L.append(f"| {lab} | {fmt_cell(c)} | {lift:+.3f} | {p:.3f} | {grade(c)} |\n")
    L.append("\n(Backing counts twin rows in the book double where both survived "
             "selection; the count itself is knowable by fill time — every twin trigger "
             "precedes the shared fill. Prereg H1 declared this axis underpowered on "
             "candidates; same verdict applies unless the cells below say otherwise.)\n")

    # ---------------- 3. constitution variants
    dedup_first = lon_book(Pc[Pc.keep_first], floor=9.5, lifetime=math.inf, cap=999)
    dedup_high = lon_book(Pc[Pc.keep_high], floor=9.5, lifetime=math.inf, cap=999)
    ser = serial_walk(b)
    both = serial_walk(dedup_first)
    L.append("\n## 3. Constitution variants, priced (cut@09:30 baseline)\n\n"
             "| variant | n | days | net | WR | mean R | maxDD | 2025 | 2026 | "
             "twin groups | overlapped entries |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
    L.append(prow("V0 as-is (frozen)", p0))
    L.append(prow("V-DEDUP-FIRST (live-causal)", price(dedup_first)))
    L.append(prow("V-DEDUP-HIGH (doc reading)", price(dedup_high)))
    L.append(prow("V-SERIAL one-at-a-time", price(ser)))
    L.append(prow("V-BOTH dedup-first + serial", price(both)))

    # ---------------- 4. single-TF gates
    L.append("\n## 4. Single-TF gate counterfactuals (a GATE change — hypothesis-grade "
             "by construction, own prereg if ever pursued)\n\n"
             "| gate | n | days | net | WR | mean R | maxDD | 2025 | 2026 | "
             "twin groups | overlapped entries |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
    for tf in ("1min", "2min", "3min", "5min"):
        bt = lon_book(Pc[Pc.tf == tf], floor=9.5, lifetime=math.inf, cap=999)
        L.append(prow(f"{tf} only", price(bt)))

    L.append("\n## Read this before quoting\n\n"
             "- The §0 finding needs an ANGUS ruling regardless of the TF question: "
             "either doc §1/§5 bind London (a dedup/serial variant becomes the book → "
             "prereg re-anchors, runner re-rehearses) or the London rulings supersede "
             "them (frozen book stands; divergence recorded as a London ruling). What "
             "may NOT happen is opening the holdout under one reading and quoting it "
             "under another.\n"
             "- Single-TF nets do not sum to the book: dropping TFs frees day-stop "
             "budget and slots on shared days.\n"
             "- Every inferential number is charged worst-of-K within its section; "
             "nothing here re-opens the frozen config on its own.\n")
    write("LONDON-TF-CONVICTION.md", "".join(L))


if __name__ == "__main__":
    main()
