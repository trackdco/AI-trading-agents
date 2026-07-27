#!/usr/bin/env python3
"""NY candidate substrate — ONE forward path, run identically over the fit window and the
sealed 2023/24 holdout.

WHY THIS EXISTS. `output/trade_matrix.parquet` (the 970-trade universe the armed canon was
scored on) cannot be reproduced by any single engine config. Its own stop distribution runs
smoothly down to 0.25pt — so the engine's `min_stop_points` floor was inactive when those
rows were made — yet re-running with the floor OFF matches it *worse* (57%) than leaving
today's floor ON (81%). Both facts are only consistent if the file was accumulated across
weeks as the config evolved, which is exactly what a research artifact assembled from three
merged upstream parquets (all since deleted) looks like. It is not a reproducible target.

So the holdout is not validated against it. It is validated the way Angus framed it — *"to
see if our mechanical strategy fits out of fit you have to trade exactly the same as our
mechanical canon"* — by running THIS code over BOTH spans and comparing fit to holdout. Same
detector, same engine, same config, same canon. Any pipeline quirk that inflates or deflates
the holdout inflates or deflates the fit number identically, so the comparison survives it.

THE STOP GATE. The canon's Layer 0 is a 7-60pt hard gate applied in `src/canon/scorer.py`,
downstream of here. Whether the ENGINE should also refuse sub-7pt triggers is not cosmetic:
`max_trades_per_day` is enforced at fill time, so an engine veto hands the day's cap slot to
a later trade the rulebook would never have seen. Two defensible readings, so both are
available and both get reported:

  --stop-gate off  (default)  engine takes them, Layer 0 kills them, they BURN a cap slot.
                              Faithful to the substrate the canon was armed on.
  --stop-gate on              engine skips them, the slot passes to the next candidate.
                              Faithful to the LIVE config (min_stop_points 7.0).

THE CAP. `max_trades_per_day` is enforced per simulate() call, so with one 08:00-10:15 window
the two sections SHARE two slots. Measured on the shipped substrate: 0 of 521 day-books ever
carry 2 pre-market fills AND a golden-window fill, and pre+gold never exceeds 2. Pre-market
fires first chronologically, so it takes the slots and the golden window trades on leftovers.

Angus (28-Jul) states the intended shape is 2 per SECTION, not 2 shared. Those are different
systems, so both are buildable here and the answer is measured, not argued:

  --cap-mode section  (default)  08:00-09:30 cap 2 AND 09:40-10:15 cap 2, simulated separately
                                 and concatenated. London is already capped 2 in its own run.
                                 This is the ruling; it is also the shape `grade_window_cap`
                                 calls C and `premarket_actualcap_run` uses.
  --cap-mode day                 one 08:00-10:15 window, cap 2 — what the shipped substrate
                                 happens to contain. Kept only so the difference is measurable.

    python -m scripts.build_ny_substrate --span fit
    python -m scripts.build_ny_substrate --span holdout --cap-mode section
"""
from __future__ import annotations

import argparse
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.grade_window_cap import books, load  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"

# Each span is a list of (months, bar file, trigger files). The fit window needs two segments
# because the 2026 half lives in a different bar file and a different trigger cache; the
# holdout is one segment. Splitting it here keeps run_months() ignorant of the difference.
SEGMENTS = {
    "fit": [
        ([f"2025-{m:02d}" for m in range(6, 13)],
         "data/reference/nq_1m_master.parquet",
         ["output/triggers_hist2326_ob_v2.csv"]),
        ([f"2026-{m:02d}" for m in range(2, 8)],
         "data/reference/nq_1m_feb_jul2026.parquet",
         ["output/triggers_feb_ob_v2.csv", "output/triggers_marjul_ob_v2.csv"]),
    ],
    "holdout": [
        (None,                                    # None = take the months from the seal
         "data/reference/nq_1m_master.parquet",
         ["output/triggers_hist2326_ob_v2.csv"]),
    ],
}

# Bars handed to simulate() for a month start LOOKBACK_DAYS before it. Every management
# indicator is intraday- or daily-anchored, so a generous lookback is result-identical;
# passing the full 1.25M-bar master makes each month re-simulate from 2023 and turns minutes
# into hours.
LOOKBACK_DAYS = 120


PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))


def canon_windows(stop_gate: bool, cap_mode: str):
    """[(tag, cfg, keep_window)] — one entry per independently-capped window.

    `keep_window` discards fills that landed outside the segment they were simulated for; the
    engine can fill a pending order slightly past win_end, and without the filter the same
    trade could be claimed by two segments.
    """
    upd = {"max_trades_per_day": 2}
    if not stop_gate:
        upd |= {"min_stop_points": 0.0, "post_open_min_stop": 0.0}
    base = load_backtest_config().model_copy(update=upd)
    if cap_mode == "day":
        return [("all", base.model_copy(update={"win_start": dtime(8, 0),
                                                "win_end": dtime(10, 15)}), None)]
    # The 09:30-09:40 gap between the segments IS the cash-open cut, so the config's own
    # no_trade veto would double-count it — disabled here exactly as grade_window_cap does.
    sec = base.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    return [("pre", sec.model_copy(update={"win_start": PRE[0], "win_end": PRE[1]}), PRE),
            ("gold", sec.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1]}), GOLD)]


def run_months(months, trigs, bars, wins) -> pd.DataFrame:
    """Both books, every day, nothing selected — the canon universe."""
    rows = []
    for m in sorted(months):
        seg_trigs = [t for t in trigs if t.ts[:7] == m]
        if not seg_trigs:
            print(f"  {m}: no triggers", flush=True)
            continue
        end = pd.Timestamp(
            (pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        start = pd.Timestamp(m + "-01", tz=NY) - pd.Timedelta(days=LOOKBACK_DAYS)
        seg = bars[(bars.ts_event >= start) & (bars.ts_event <= end)].reset_index(drop=True)
        n0 = len(rows)
        for tag, wcfg, keep in wins:
            cfg_e3, cfg_e4 = books(wcfg)
            for book, cfg in (("E3", cfg_e3), ("E4", cfg_e4)):
                tr, _, _ = simulate(seg, seg_trigs, cfg)
                for r in tr:
                    if keep and not (keep[0] <= pd.Timestamp(r.fill_ts).time() < keep[1]):
                        continue
                    rows.append({
                        "day": r.trade_date, "book": book, "seg": tag, "fill": str(r.fill_ts),
                        "exit": str(r.exit_ts), "direction": r.direction, "entry": r.entry,
                        "stop": r.stop_initial, "exit_price": r.exit_price,
                        "dollars": r.dollars, "pattern": r.pattern, "tf": getattr(r, "tf", "")})
        print(f"  {m}: {len(seg_trigs):>5} triggers -> {len(rows) - n0:>4} fills", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SEGMENTS), required=True)
    ap.add_argument("--stop-gate", choices=["on", "off"], default="off",
                    help="engine-level min_stop_points; Layer 0 gates 7-60pt regardless")
    ap.add_argument("--cap-mode", choices=["section", "day"], default="section",
                    help="2 per section (Angus 28-Jul ruling), or 2 shared across 08:00-10:15")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    wins = canon_windows(a.stop_gate == "on", a.cap_mode)
    shape = " + ".join(f"{t} {c.win_start:%H:%M}-{c.win_end:%H:%M} cap {c.max_trades_per_day}"
                       for t, c, _ in wins)
    print(f"span {a.span} | cap-mode {a.cap_mode}: {shape} | engine stop floor "
          f"{wins[0][1].min_stop_points:g}pt | lookback {LOOKBACK_DAYS}d\n", flush=True)

    sealed = set(pd.read_csv(SEALED, dtype=str)["day"]) if a.span == "holdout" else None
    parts = []
    for months, barfile, trigfiles in SEGMENTS[a.span]:
        if months is None:
            months = sorted({d[:7] for d in sealed})
        bars = pd.read_parquet(ROOT / barfile).drop(columns=["roll"], errors="ignore")
        trigs = load([str(ROOT / t) for t in trigfiles])
        print(f"{barfile}: {len(bars):,} bars | {len(trigs):,} triggers | "
              f"{len(months)} months {months[0]}..{months[-1]}", flush=True)
        parts.append(run_months(months, trigs, bars, wins))

    S = pd.concat(parts, ignore_index=True)
    if sealed is not None:
        S = S[S.day.astype(str).isin(sealed)].reset_index(drop=True)   # sealed days ONLY
    S["yr"] = S.day.astype(str).str[:4].astype(int)
    S["risk"] = (S.entry - S.stop).abs()

    suffix = "" if a.cap_mode == "section" else "_daycap"
    out = Path(a.out) if a.out else ROOT / f"output/ny_substrate_{a.span}{suffix}.parquet"
    S.to_parquet(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)} — {len(S)} candidate fills on {S.day.nunique()} days")
    print(f"\nby year x book:\n{pd.crosstab(S.yr, S.book)}")
    if "seg" in S:
        print(f"\nby section: {S.seg.value_counts().to_dict()}")
    print(f"\npattern: {S.pattern.value_counts().to_dict()}")
    print(f"risk pts: median {S.risk.median():.2f}, "
          f"{(S.risk < 7).sum()} below Layer-0 floor, {(S.risk > 60).sum()} above its cap")
    print(f"raw 1-lot P&L (the UNFILTERED universe, NOT the canon): ${S.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
