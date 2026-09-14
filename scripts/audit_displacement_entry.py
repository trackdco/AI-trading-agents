#!/usr/bin/env python3
"""PILOT — the displacement / market-entry hypothesis (ANGUS 2026-08-05), FIT ONLY.

ANGUS (after the depth-lookahead finding, and London's 1,100 never-filled triggers):
  "the 3-minute closes through both of those levels, and you just market order there
   instead of limit retesting ... stop below that candle, and let it go. I highly
   suspect a lot of the raw triggers we cut would purely have been cut because the
   limit never got filled and the trade just ran."

This measures that on NY's honest L0/L2 population, with a causally clean convention:
  * SIGNAL: the trigger's TF bar. Confirmation = that bar's CLOSE (label convention
    resolved empirically below — start- vs close-labeled ts).
  * ENTRY: the OPEN of the first 1m bar strictly after the signal bar ends (market
    order on confirm; nothing intrabar is used).
  * STOP: the signal TF bar's adverse extreme -/+ 1 tick.
  * WALK: 1m bars, stop-first, to 15:55 ET same day.

Outputs per cohort (never-filled limits / filled / bb_vwap-vetoed, x kind, x session):
risk distribution, reach ladder (1R/2R/3R before stop), WR under a naive 2R-or-stop
rule, EOD-hold meanR, and for the filled cohort the PAIRED comparison vs the actual
limit-entry R.

HOLDOUT IS NOT TOUCHED. A new entry family starts its era discipline from zero:
discover on fit-2025, validate on fit-2026, ONE holdout look for a frozen candidate.

    python -m scripts.audit_displacement_entry
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars  # noqa: E402

NY = "America/New_York"
TICK = 0.25
TFMIN = {"1min": 1, "2min": 2, "3min": 3, "5min": 5}


def tf_bar(day_bars: pd.DataFrame, start: pd.Timestamp, minutes: int):
    """Aggregate the 1m bars of [start, start+minutes) into one TF bar. None if empty."""
    seg = day_bars[(day_bars.mi >= start) & (day_bars.mi < start + pd.Timedelta(minutes=minutes))]
    if seg.empty:
        return None
    return {"open": float(seg.iloc[0].open), "close": float(seg.iloc[-1].close),
            "high": float(seg.high.max()), "low": float(seg.low.min()),
            "end": start + pd.Timedelta(minutes=minutes)}


def resolve_label_convention(L: pd.DataFrame, bars_by_day: dict) -> str:
    """Is ts the TF bar's START or its CLOSE boundary? Test on displacement triggers:
    the signal bar should CLOSE through entry_ref in the trade direction."""
    disp = L[L.kind == "displacement"].sample(n=min(400, (L.kind == "displacement").sum()),
                                              random_state=7)
    hits = {"start": 0, "close": 0, "n": 0}
    for r in disp.itertuples():
        db = bars_by_day.get(r.day)
        if db is None:
            continue
        m = TFMIN[r.tf]
        sgn = 1 if r.direction == "long" else -1
        cand = {"start": tf_bar(db, r.ts_ny, m),
                "close": tf_bar(db, r.ts_ny - pd.Timedelta(minutes=m), m)}
        ok = False
        for k, b in cand.items():
            if b is None:
                continue
            if sgn * (b["close"] - float(r.entry)) > 0:
                hits[k] += 1
                ok = True
        if ok:
            hits["n"] += 1
    return hits


def walk(day_bars: pd.DataFrame, entry_t: pd.Timestamp, entry: float, stop: float,
         sgn: int, day: str):
    """1m walk from entry_t, stop-first. Returns dict or None if no bars."""
    end = pd.Timestamp(f"{day} 15:55", tz=NY)
    seg = day_bars[(day_bars.mi >= entry_t) & (day_bars.mi <= end)]
    if seg.empty:
        return None
    risk = sgn * (entry - stop)
    if risk <= 0:
        return None
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    fav = (hi - entry) / risk if sgn > 0 else (entry - lo) / risk
    stopped = (lo <= stop) if sgn > 0 else (hi >= stop)
    # stop-first per bar: favorable excursion on the stop bar itself doesn't count
    n = len(seg)
    stop_i = int(np.argmax(stopped)) if stopped.any() else n
    max_r = float(fav[:stop_i].max()) if stop_i > 0 else 0.0
    # naive 2R-or-stop: first bar whose favorable extreme >= 2R, stop-first
    tgt_i = next((i for i in range(stop_i) if fav[i] >= 2.0), None)
    r_2r = 2.0 if tgt_i is not None else (-1.0 if stop_i < n else
                                          sgn * (cl[-1] - entry) / risk)
    r_eod = -1.0 if stop_i < n and (tgt_i is None or stop_i <= tgt_i) else None
    # EOD-hold arm (no target): stopped -> -1, else close at end
    r_hold = -1.0 if stop_i < n else sgn * (cl[-1] - entry) / risk
    return {"risk": risk, "max_r": max_r, "stopped_ever": stop_i < n,
            "r_2r": r_2r, "r_hold": r_hold,
            "reach1": max_r >= 1.0, "reach2": max_r >= 2.0, "reach3": max_r >= 3.0}


def main() -> None:
    L = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet").copy()
    L["ts_ny"] = pd.to_datetime(L.ts, utc=True).dt.tz_convert(NY)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars_by_day = {d: g for d, g in bars.groupby(bars.mi.dt.strftime("%Y-%m-%d"))}

    conv = resolve_label_convention(L, bars_by_day)
    print(f"label convention check (displacement closes through level): {conv}")
    label = "start" if conv["start"] >= conv["close"] else "close"
    print(f"-> using ts as TF-bar {label.upper()} label\n")

    rows = []
    for r in L.itertuples():
        db = bars_by_day.get(r.day)
        if db is None:
            continue
        m = TFMIN[r.tf]
        start = r.ts_ny if label == "start" else r.ts_ny - pd.Timedelta(minutes=m)
        b = tf_bar(db, start, m)
        if b is None:
            continue
        sgn = 1 if r.direction == "long" else -1
        stop = (b["low"] - TICK) if sgn > 0 else (b["high"] + TICK)
        nxt = db[db.mi >= b["end"]]
        if nxt.empty:
            continue
        entry_t, entry = nxt.iloc[0].mi, float(nxt.iloc[0].open)
        w = walk(db, entry_t, entry, stop, sgn, r.day)
        if w is None:
            continue
        hm = entry_t.hour * 60 + entry_t.minute
        sess = "pre" if 480 <= hm < 570 else ("gold" if 580 <= hm < 630 else "other")
        rows.append({"day": r.day, "kind": r.kind, "status": r.status, "sess": sess,
                     "era": "2025" if r.day[:4] == "2025" else "2026",
                     "limit_R": r.R if r.status == "outcome" else np.nan, **w})
    A = pd.DataFrame(rows)
    print(f"walked {len(A):,} of {len(L):,} triggers\n")
    print(f"candle-stop risk (pts): median {A.risk.median():.2f} | p10 {A.risk.quantile(.1):.2f} "
          f"| p90 {A.risk.quantile(.9):.2f} | <2pt: {(A.risk<2).mean()*100:.1f}%")

    def block(name, D):
        if len(D) < 30:
            return
        print(f"\n--- {name} (n={len(D):,}) ---")
        for era in ("2025", "2026"):
            d = D[D.era == era]
            if len(d) < 30:
                continue
            print(f"  {era}: n={len(d):>5,} | reach 1R/2R/3R: "
                  f"{d.reach1.mean()*100:.0f}%/{d.reach2.mean()*100:.0f}%/{d.reach3.mean()*100:.0f}% "
                  f"| 2R-or-stop WR {(d.r_2r>0).mean()*100:.1f}% meanR {d.r_2r.mean():+.3f} "
                  f"| EOD-hold meanR {d.r_hold.mean():+.3f}")

    NF = A[A.status == "cancelled_window_end"]
    block("NEVER-FILLED LIMITS — the runners hypothesis", NF)
    block("NEVER-FILLED, displacement kind only", NF[NF.kind == "displacement"])
    block("NEVER-FILLED, gold session", NF[NF.sess == "gold"])
    F = A[A.status == "outcome"]
    block("FILLED (paired vs limit entry below)", F)
    for era in ("2025", "2026"):
        d = F[(F.era == era) & F.limit_R.notna()]
        if len(d) < 30:
            continue
        print(f"  paired {era}: displacement 2R-or-stop meanR {d.r_2r.mean():+.3f} "
              f"vs actual limit-entry meanR {d.limit_R.mean():+.3f} (same triggers, n={len(d):,})")
    block("VETOED bb_vwap (would the veto have mattered?)", A[A.status == "vetoed_bb_vwap"])
    block("ALL triggers, displacement kind", A[A.kind == "displacement"])
    block("ALL triggers, rejection_block kind", A[A.kind == "rejection_block"])
    print("\nNOTE: naive exits (2R-or-stop, EOD-hold), no V8 menu, no risk band, no costs. "
          "This is a direction-finder, not a book. HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
