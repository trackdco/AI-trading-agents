#!/usr/bin/env python3
"""ROOM-TO-RUN ON GOLD — DECLARATIONS-gold-room-to-run.md, written first.

Builds the GC level census and attaches `next_lvl_R` in the SAME per-day pass, so the
level values a row is scored against are the ones its own session produced. Doing it as a
second pass and merging is the documented hazard: `simulate()` drops rows
non-contiguously, so positional pairing silently mismatches signal and context.

`next_lvl_R` is computed exactly as scripts/phase1_build_cols.py computes it, over
`htf_ma_level_census.level_series` rather than a reimplementation. Undefined = OPEN SPACE
= no other locus ahead of entry at all, which BR-53 identified as the half of the BR-32/35
gate that actually works.

    python scripts/gold_room_to_run.py [--days N] [--out PATH]      # build
    python scripts/gold_room_to_run.py --report [--src PATH]        # score
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import htf_ma_level_census as C
from scripts.gold_level_report import cell, first_of_fight
from src.htf_ma.levels import NY, bb_ma_asof
from src.htf_ma.levels import profile_at_minutes as _profile
from src.research.tomtrades import data as D

# Instrument constants, identical to scripts/gold_level_census.py. TICK and the profile
# bin are properties of GC, not choices: the 1.0 default bin is scale-dependent and
# silently destroys the profile loci off NQ.
TICK, COST_PTS, BINW = 0.10, 0.20, 0.40
RISK_FLOOR = 0.2      # gate-selected floor, DECLARATIONS-gold-vah-break
ROOM_THR = 3.0        # BR-32/35's declared threshold, carried over to be tested not used
FLOORS = (1.0, 1.5, 2.0, 3.0, 4.0, 5.0)   # BR-54 sweep
DEFAULT_OUT = "output/gold_room_census.parquet"


def _configure() -> None:
    C.TICK = TICK
    C.COST_PTS = COST_PTS
    C.profile_at_minutes = functools.partial(_profile, bin_width=BINW)


def day_rows_with_room(bars: pd.DataFrame, sess_day: str) -> list[dict]:
    """One session's fights, each carrying `next_lvl_R` and `next_lvl`."""
    rows = C.day_rows(bars, sess_day, C.LOCI)
    if not rows:
        return rows

    # Reconstruct the same window day_rows used, so the level series lines up bar for bar.
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return rows
    ma15, _ = bb_ma_asof(hist, 15)
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return rows
    idx = seg.index
    lv = C.level_series(hist, idx, ma15)
    idxv = idx.values

    for r in rows:
        te = pd.Timestamp(r.get("t_entry"))
        risk = r.get("risk")
        r["next_lvl"], r["next_lvl_R"] = None, np.nan
        if pd.isna(te) or not np.isfinite(risk or np.nan) or (risk or 0) <= 0:
            continue
        j0 = int(np.searchsorted(idxv, te.to_datetime64()))
        if j0 >= len(idx):
            continue
        p = max(j0 - 1, 0)          # as-of the bar BEFORE entry — no lookahead
        d, entry = int(r["direction"]), float(r["entry"])
        best, bname = np.nan, None
        for other in C.LOCI:
            if other == r["locus"]:
                continue
            v = lv[other][p]
            if not np.isfinite(v):
                continue
            dist = d * (v - entry)
            if dist > 0 and (not np.isfinite(best) or dist < best):
                best, bname = dist, other
        if np.isfinite(best):
            r["next_lvl"], r["next_lvl_R"] = bname, best / risk
    return rows


def build(n_days: int | None, out_path: Path) -> pd.DataFrame:
    _configure()
    gc = D.load(str(ROOT / "data/gc_1m.parquet"))
    bars = (gc.set_index(gc["ts_event"].dt.tz_convert(NY))
              [["open", "high", "low", "close", "volume"]].sort_index())
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    if n_days:
        sess_days = sess_days[-n_days:]
    print(f"GC {len(bars):,} bars · {len(sess_days):,} session-days · "
          f"TICK={TICK} COST_PTS={COST_PTS} BINW={BINW:g}", flush=True)

    rows: list[dict] = []
    for k, d in enumerate(sess_days):
        rows.extend(day_rows_with_room(bars, d))
        if k % 100 == 0:
            print(f"  {k}/{len(sess_days)} days · {len(rows):,} fights", flush=True)
    out = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    opn = 100 * out.next_lvl_R.isna().mean()
    print(f"fights: {len(out):,} · open-space share {opn:.1f}% · wrote {out_path}",
          flush=True)
    return out


def report(src: Path) -> None:
    raw = pd.read_parquet(src)
    df = first_of_fight(raw)
    df = df[df.risk >= RISK_FLOOR].copy()
    df["out"] = df["out_ship"]
    df = df[np.isfinite(df["out"])]
    days = np.sort(df.sess_day.unique())

    print(f"\n{src.name}")
    print(f"{len(raw):,} triggers -> {len(df):,} first-of-fight rows at risk>={RISK_FLOOR}"
          f", {len(days):,} session-days, exit=out_ship cost={COST_PTS}")

    openm = df.next_lvl_R.isna()
    roomm = df.next_lvl_R >= ROOM_THR
    print(f"open space: {100 * openm.mean():.1f}% of rows   "
          f">= {ROOM_THR}R: {100 * roomm.mean():.1f}%   "
          f"level ahead: {100 * (~openm).mean():.1f}%")

    cells = [cell(df, "BASELINE (all, risk>=0.2)", days),
             cell(df[openm], "A · OPEN SPACE", days),
             cell(df[roomm], f"B · ROOM >= {ROOM_THR}R", days),
             cell(df[openm | roomm], "C · BUNDLED (A or B) = BR-32/35 form", days)]
    _table([c for c in cells if c], "PRIMARY — the BR-53 decomposition")

    ahead = df[~openm]
    _table([c for c in (cell(ahead[ahead.next_lvl_R >= f], f"floor {f:.1f}R", days)
                        for f in FLOORS) if c],
           "SECONDARY — BR-54 floor sweep, level-ahead rows only (descriptive)")

    surv = [(m, lbl) for m, lbl in ((openm, "OPEN SPACE"), (roomm, f">={ROOM_THR}R"))]
    for m, lbl in surv:
        sub = df[m]
        rows_ = [cell(sub[sub.arm == a], f"{lbl} · {a}", days) for a in ("break", "reject")]
        _table([c for c in rows_ if c], f"SECONDARY — {lbl} by arm (descriptive)")


def _table(rows: list[dict], title: str) -> None:
    if not rows:
        print(f"\n=== {title} ===\n  (no cell reached the minimum n)")
        return
    t = pd.DataFrame(rows)
    t["ci"] = t.apply(lambda r: f"[{r.lo:+.3f},{r.hi:+.3f}]", axis=1)
    t["eras"] = np.where(t.both_eras_clear, "BOTH", "-")
    print(f"\n=== {title} ===")
    print(t[["cell", "n", "days", "per_day", "win_pct", "ev", "ci",
             "h1_ev", "h2_ev", "eras", "total_r"]].to_string(
        index=False, float_format=lambda v: f"{v:.3f}"))


def main() -> None:
    a = sys.argv
    if "--report" in a:
        src = Path(a[a.index("--src") + 1]) if "--src" in a else ROOT / DEFAULT_OUT
        report(src if src.is_absolute() else ROOT / src)
        return
    n_days = int(a[a.index("--days") + 1]) if "--days" in a else None
    out = Path(a[a.index("--out") + 1]) if "--out" in a else ROOT / DEFAULT_OUT
    build(n_days, out if out.is_absolute() else ROOT / out)


if __name__ == "__main__":
    main()
