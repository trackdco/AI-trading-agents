#!/usr/bin/env python3
"""LDN-PO3-01 — geometry calibration + event-universe sensitivity.

Authorised by docs/PREREG-london-po3-geometry.md, committed before this file.
Every arm below is declared there. Nothing is searched, tuned or added here.

WHY THIS RUN EXISTS (Angus, 2026-08-05): this family was killed on TWO arms —
F1 (midpoint target) and F2 (far-edge target) — sharing ONE stop rule, while the
shipped IB fade got 28 arms across 13 trials. The stop was never a variable, and
a fixed-R target was never tested once: both declared targets are structural
PRICE LEVELS, so the payoff multiple was whatever the sweep extreme happened to
be that day (F1 median 1.49R, p10 0.47R, p90 3.73R). The expectancy kill was
therefore illegal under 5.9.2 and is vacated.

OBJECTIVE (corrected): profit factor at strict cost, era- and half-consistent,
with trade-sequence max drawdown in dollars reported beside it because the funded
shell's trailing line is a hard constraint that PF cannot see.

The event set is held CONSTANT across the whole grid (MIN_RISK is applied on the
as-taught stop distance, once, at construction) so that stop arms are compared on
identical trades rather than on quietly different populations.

    python -m scripts.london_po3_geometry [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_obk_l1 import (COSTS, DOLLAR_RISK, MIN_BARS,  # noqa: E402
                                   MIN_RISK, PREOPEN, SPAN_END, SPAN_START,
                                   load_bars, lon_window)
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-po3-geometry.md"
OUT_MD = ROOT / "output/london_po3_geometry.md"
OUT_PARQUET = ROOT / "output/london_po3_geometry.parquet"

LON = "Europe/London"
TRIGGER_STD = ("08:00", "10:00")
TRIGGER_WIDE = ("08:00", "11:00")

# --- the declared grid (prereg 4) ------------------------------------------------
STOPS = (
    ("E", None, None, None),            # sweep extreme, as taught -- DEFAULT
    ("E+F8", 8.0, None, None),          # floored at 8 pts
    ("E+F12", 12.0, None, None),        # floored at 12 pts
    ("E~C20", None, 20.0, None),        # capped at 20 pts
    ("E+F8~C20", 8.0, 20.0, None),      # both
    ("FIX15", None, None, 15.0),        # fixed, ignores the extreme
)
TARGETS = ("MID", "FAR", "R1", "R1.5", "R2", "R3", "TRAIL")
DEFAULT_CELL = ("E", "MID")
UNIVERSES = ("U1", "U2", "U3", "U4")


# --- event construction ----------------------------------------------------------

def build_events(bars: pd.DataFrame, reentry: bool, wide: bool
                 ) -> tuple[pd.DataFrame, list[np.ndarray]]:
    """PO3 failure events. Identical trigger grammar to L1; only the universe moves.

    A single event = the pre-open range breaks (close beyond the level), then price
    closes back inside. Entry is the fail bar's CLOSE and the path starts on the
    NEXT bar, so there is no gap between decision and simulation.
    """
    trig_win = TRIGGER_WIDE if wide else TRIGGER_STD
    days = sorted(set(pd.bdate_range(SPAN_START, SPAN_END).strftime("%Y-%m-%d")))
    rows, paths = [], []

    for day in days:
        t_start, t_end = lon_window(day, *trig_win)
        r_start, r_end = lon_window(day, *PREOPEN)
        frame = bars[(bars["ts_event"] >= r_start) & (bars["ts_event"] < t_end)]
        if len(frame) < MIN_BARS:
            continue
        rng = frame[(frame["ts_event"] >= r_start) & (frame["ts_event"] < r_end)]
        trig = frame[frame["ts_event"] >= t_start].reset_index(drop=True)
        if rng.empty or trig.empty:
            continue
        hi, lo = float(rng["high"].max()), float(rng["low"].min())
        width = hi - lo
        if width <= 0:
            continue
        mid = (hi + lo) / 2.0
        mat = trig[["high", "low", "close"]].to_numpy(float)
        closes = mat[:, 2]

        for side, level in ((1, hi), (-1, lo)):
            cursor, cycle = 0, 0
            while cursor < len(trig) - 2:
                beyond = (closes[cursor:] > level) if side > 0 else (closes[cursor:] < level)
                if not beyond.any():
                    break
                i0 = cursor + int(np.flatnonzero(beyond)[0])
                back = ((closes[i0 + 1:] <= hi) if side > 0 else (closes[i0 + 1:] >= lo))
                if not back.any():
                    break
                f = i0 + 1 + int(np.flatnonzero(back)[0])
                if f >= len(trig) - 1:
                    break
                seg = mat[i0:f + 1]
                extreme = float(seg[:, 0].max()) if side > 0 else float(seg[:, 1].min())
                entry = float(mat[f, 2])
                risk_e = abs(entry - extreme)
                cursor = f + 1
                cycle += 1
                # MIN_RISK is applied ONCE, on the as-taught distance, so every stop
                # arm below is scored on exactly the same trades.
                if risk_e < MIN_RISK:
                    continue
                dirn = -side
                far = lo if side > 0 else hi
                rows.append({
                    "day": day, "era": day[:4],
                    "half": day[:4] + ("H1" if int(day[5:7]) <= 6 else "H2"),
                    "side": side, "dirn": dirn, "cycle": cycle,
                    "entry_px": entry, "extreme_px": extreme, "risk_e": risk_e,
                    "mid_px": mid, "far_px": far, "width": width,
                    "entry_ts": trig.loc[f, "ts_event"],
                })
                paths.append(mat[f + 1:])
                if not reentry:
                    break
    return pd.DataFrame(rows), paths


# --- simulation ------------------------------------------------------------------

def stop_distance(risk_e: float, floor, cap, fixed) -> float:
    if fixed is not None:
        return fixed
    d = risk_e
    if floor is not None:
        d = max(d, floor)
    if cap is not None:
        d = min(d, cap)
    return d


def simulate(dirn: int, entry: float, dist: float, target_px, trail: bool,
             path: np.ndarray) -> tuple[float, str]:
    """Conservative intrabar: the stop is checked before the target, always.

    ORDER MATTERS on the trail. The stop in force during a bar is the one set at
    the END of the previous bar, so the stop is tested BEFORE it is advanced.
    """
    stop_px = entry - dirn * dist
    best = 0.0
    for hi, lo, cl in path:
        if (lo <= stop_px) if dirn > 0 else (hi >= stop_px):
            return (stop_px - entry) if dirn > 0 else (entry - stop_px), "stop"
        if target_px is not None:
            if (hi >= target_px) if dirn > 0 else (lo <= target_px):
                return (target_px - entry) if dirn > 0 else (entry - target_px), "target"
        if trail:
            fav = (hi - entry) if dirn > 0 else (entry - lo)
            best = max(best, fav)
            if best >= dist:
                # trail `dist` behind the best excursion; ratchet only, never back off
                cand = entry + dirn * (best - dist)
                stop_px = max(stop_px, cand) if dirn > 0 else min(stop_px, cand)
    cl = float(path[-1][2])
    return ((cl - entry) if dirn > 0 else (entry - cl)), "time"


def run_cell(E: pd.DataFrame, paths: list, stop_id: str, tgt_id: str) -> pd.DataFrame:
    _, floor, cap, fixed = next(s for s in STOPS if s[0] == stop_id)
    out = []
    for i, t in enumerate(E.itertuples()):
        dist = stop_distance(t.risk_e, floor, cap, fixed)
        trail = tgt_id == "TRAIL"
        if tgt_id == "MID":
            tgt = t.mid_px
        elif tgt_id == "FAR":
            tgt = t.far_px
        elif tgt_id == "TRAIL":
            tgt = None
        else:
            tgt = t.entry_px + t.dirn * float(tgt_id[1:]) * dist
        if tgt is not None:
            # a target already reached at entry is not a trade (L1 rule, unchanged)
            if (t.dirn > 0 and tgt <= t.entry_px) or (t.dirn < 0 and tgt >= t.entry_px):
                continue
        pts, why = simulate(t.dirn, t.entry_px, dist, tgt, trail, paths[i])
        out.append({"day": t.day, "era": t.era, "half": t.half, "entry_ts": t.entry_ts,
                    "risk": dist, "pts": pts, "why": why})
    return pd.DataFrame(out)


# --- scoring ---------------------------------------------------------------------

def score(T: pd.DataFrame, cost: float) -> dict | None:
    """Profit factor headline; max drawdown in dollars beside it (prereg 0.1)."""
    if T.empty:
        return None
    T = T.sort_values("entry_ts")          # chronological, for the drawdown path
    net = (T["pts"] - cost).to_numpy(float)
    r = net / T["risk"].to_numpy(float)
    wins, losses = net[net > 0], net[net <= 0]
    gw, gl = wins.sum(), -losses.sum()
    n = len(net)
    # trade-sequence drawdown at fixed dollar risk
    eq = np.concatenate([[0.0], np.cumsum(r * DOLLAR_RISK)])
    dd = float(np.max(np.maximum.accumulate(eq) - eq))
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return {
        "n": n, "wr": float((net > 0).mean()), "pts": float(net.sum()),
        "usd": float(DOLLAR_RISK * r.sum()), "pf": float(gw / max(gl, 1e-9)),
        "r": float(r.mean()), "maxdd": dd,
        "payoff": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses)
        else float("nan"),
        "t": float(r.mean() / se) if se and se == se else 0.0,
    }


def cell_row(label: str, T: pd.DataFrame) -> dict:
    """One grid cell, scored the way the prereg declared."""
    rec = {"cell": label}
    for cost, cl in COSTS:
        s = score(T, cost)
        rec[f"pf_{cl}"] = s["pf"] if s else np.nan
        rec[f"r_{cl}"] = s["r"] if s else np.nan
        rec[f"usd_{cl}"] = s["usd"] if s else np.nan
    s = score(T, 2.0)
    rec.update(n=s["n"] if s else 0, wr=s["wr"] if s else np.nan,
               payoff=s["payoff"] if s else np.nan, maxdd=s["maxdd"] if s else np.nan,
               t=s["t"] if s else 0.0)
    for era in ("2025", "2026"):
        se = score(T[T["era"] == era], 2.0)
        rec[f"pf{era}"] = se["pf"] if se else np.nan
        rec[f"n{era}"] = se["n"] if se else 0
    for half in ("2025H1", "2025H2", "2026H1"):
        sh = score(T[T["half"] == half], 2.0)
        rec[f"pf{half}"] = sh["pf"] if sh else np.nan
    # prereg 5(1): PF-positive at STRICT cost in both eras
    rec["survives"] = bool(rec["pf2025"] > 1.0 and rec["pf2026"] > 1.0)
    return rec


def fmt(v, spec="{:.2f}"):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else spec.format(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bars = load_bars()
    L = ["# LDN-PO3-01 — geometry calibration + universe sensitivity", "",
         f"Authorised by `{PREREG}`, committed before this run. Bars only.",
         "**2023/24, the six sealed months, depth and flow are all untouched — this",
         "stage spends no holdout look of any kind.**", "",
         "Objective per prereg §0.1: **profit factor at strict cost (2 pt)**, era- and",
         "half-consistent, with trade-sequence max drawdown at $160 fixed risk beside",
         "it. Win rate is a reported column, not the objective.", ""]

    # --- section 1: event universes, default geometry only (prereg 3) -------------
    print("building universes ...", flush=True)
    universes = {
        "U1": build_events(bars, reentry=False, wide=False),
        "U2": build_events(bars, reentry=True, wide=False),
        "U3": build_events(bars, reentry=False, wide=True),
        "U4": build_events(bars, reentry=True, wide=True),
    }
    ledger = []
    L += ["## 1. Event-universe sensitivity (§5.11.2) — never run on this family before",
          "", "All four at the DECLARED DEFAULT geometry (`E`/`MID`). **The universe is",
          "not selected from this table** — U1 remains the default for §2 whatever it",
          "says.", "",
          "| universe | events | /day | PF base | PF strict | R/trade | $ | maxDD $ | 25 PF | 26 PF |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    labels = {"U1": "U1 as-is (L1)", "U2": "U2 re-entry",
              "U3": "U3 window→11:00", "U4": "U4 both"}
    for u in UNIVERSES:
        E, P = universes[u]
        T = run_cell(E, P, *DEFAULT_CELL)
        r = cell_row(u, T)
        L.append(f"| {labels[u]} | {r['n']:,} | {r['n']/E['day'].nunique():.2f} | "
                 f"{fmt(r['pf_base'])} | {fmt(r['pf_strict'])} | {fmt(r['r_strict'],'{:+.3f}')} | "
                 f"${r['usd_strict']:+,.0f} | ${r['maxdd']:,.0f} | "
                 f"{fmt(r['pf2025'])} | {fmt(r['pf2026'])} |")
        ledger.append({
            "family": "LDN-PO3-01", "era": "fit", "prereg": PREREG,
            "trial": f"universe {u} at default geometry E/MID",
            "stat_type": "mean", "estimate": round(r["r_strict"], 4), "n": r["n"],
            "t_stat": round(r["t"], 4),
            "effect": round(trial_ledger.effect_from_t(r["t"], r["n"]), 6),
            "verdict": (f"event-universe sensitivity: n={r['n']} PF strict "
                        f"{r['pf_strict']:.2f} (25 {r['pf2025']:.2f} / 26 "
                        f"{r['pf2026']:.2f}), maxDD ${r['maxdd']:,.0f}"),
        })

    # --- section 2: the 42-cell geometry grid on U1 (prereg 4) --------------------
    E, P = universes["U1"]
    print(f"U1: {len(E):,} events over {E['day'].nunique()} sessions — running grid",
          flush=True)
    rows = []
    for sid, *_ in STOPS:
        for tid in TARGETS:
            T = run_cell(E, P, sid, tid)
            r = cell_row(f"{sid}/{tid}", T)
            r["stop"], r["tgt"] = sid, tid
            rows.append(r)
            print(f"  {sid:>9}/{tid:<5} n={r['n']:>4} PF {r['pf_strict']:.2f} "
                  f"(25 {r['pf2025']:.2f} / 26 {r['pf2026']:.2f})"
                  f"{'  <-- survives' if r['survives'] else ''}", flush=True)
            ledger.append({
                "family": "LDN-PO3-01", "era": "fit", "prereg": PREREG,
                "trial": f"geometry {sid}/{tid} R per trade strict cost",
                "stat_type": "mean", "estimate": round(r["r_strict"], 4), "n": r["n"],
                "t_stat": round(r["t"], 4),
                "effect": round(trial_ledger.effect_from_t(r["t"], r["n"]), 6),
                "verdict": (f"geometry grid: PF strict {r['pf_strict']:.2f} "
                            f"(25 {r['pf2025']:.2f} / 26 {r['pf2026']:.2f}) "
                            f"WR {r['wr']:.0%} payoff {r['payoff']:.2f} "
                            f"maxDD ${r['maxdd']:,.0f}; "
                            f"{'PF-positive both eras' if r['survives'] else 'does not survive'}"),
            })
    G = pd.DataFrame(rows)

    L += ["", "## 2. The geometry grid — 42 declared cells on U1", "",
          f"**{len(E):,} events over {E['day'].nunique()} sessions.** The event set is",
          "identical in every cell (the minimum-risk filter is applied once, on the",
          "as-taught distance), so these are the same trades managed differently.", "",
          "Sorted by PF at strict cost. **Rank promotes nothing** (§6.0.1) — the",
          "`survives` column is the only thing the prereg lets this table decide.", "",
          "| cell | n | WR | payoff | PF base | **PF strict** | R/trade | $ | maxDD $ | 2025 | 2026 | survives |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for _, r in G.sort_values("pf_strict", ascending=False).iterrows():
        star = " **←default**" if r["cell"] == "/".join(DEFAULT_CELL) else ""
        L.append(f"| `{r['cell']}`{star} | {r['n']:,} | {r['wr']:.0%} | {fmt(r['payoff'])} | "
                 f"{fmt(r['pf_base'])} | **{fmt(r['pf_strict'])}** | "
                 f"{fmt(r['r_strict'],'{:+.3f}')} | ${r['usd_strict']:+,.0f} | "
                 f"${r['maxdd']:,.0f} | {fmt(r['pf2025'])} | {fmt(r['pf2026'])} | "
                 f"{'**YES**' if r['survives'] else 'no'} |")

    surv = G[G["survives"]]
    L += ["", f"### {len(surv)} of {len(G)} cells are PF-positive at strict cost in "
          "both eras", ""]
    if len(surv):
        L += ["Half-year detail on the survivors (§5.11.5 — era aggregates mask holes):",
              "", "| cell | 2025H1 | 2025H2 | 2026H1 | all halves > 1.0 |",
              "|---|---:|---:|---:|---|"]
        for _, r in surv.sort_values("pf_strict", ascending=False).iterrows():
            hs = [r["pf2025H1"], r["pf2025H2"], r["pf2026H1"]]
            clean = all(np.isfinite(h) and h > 1.0 for h in hs)
            L.append(f"| `{r['cell']}` | {fmt(hs[0])} | {fmt(hs[1])} | {fmt(hs[2])} | "
                     f"{'**YES**' if clean else 'no'} |")
        L += ["", "**These are candidates for the permutation null declared in prereg",
              "§5(2), not results.** Nothing here is promoted, and the null runs next.",
              ""]
    else:
        L += ["**Prereg §6 kill condition FIRES.** No geometry in the declared grid is",
              "PF-positive at strict cost in both eras. The geometry class has now been",
              "searched and the expectancy kill is legal under §5.9.2.", ""]

    # --- section 3: what the default was actually doing ---------------------------
    Td = run_cell(E, P, *DEFAULT_CELL)
    L += ["## 3. What the as-taught default was actually doing", "",
          "| exit | share |", "|---|---:|"]
    for k, v in Td["why"].value_counts(normalize=True).items():
        L.append(f"| {k} | {v:.0%} |")
    L += ["", "Risk distribution on the as-taught stop (the defect the grid tests):", "",
          f"median **{E['risk_e'].median():.1f} pts**, p10 {E['risk_e'].quantile(.1):.1f}, "
          f"p90 {E['risk_e'].quantile(.9):.1f} — a "
          f"{E['risk_e'].quantile(.9)/max(E['risk_e'].quantile(.1),1e-9):.1f}x spread with "
          "no floor and no cap.", ""]

    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    G.to_parquet(OUT_PARQUET, index=False)
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
