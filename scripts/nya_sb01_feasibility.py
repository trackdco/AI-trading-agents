#!/usr/bin/env python3
"""NYA-SB-01 — FEASIBILITY COUNT for the ash10hazard silver-bullet model. NOT A TEST.

Counts only. No outcome, return, direction or P&L anywhere in this file, so no statistical
power is spent and nothing enters the DSR ledger. Per the LDN-DRIVE-01 / LDN-VT-01 lessons
the n-floor is checked on the FULL gate stack INCLUDING the entry trigger, before any
prereg is written.

SPEC SOURCE: research/candidates/ash10hazard-unicorn-silver-bullet.md (rev d), which is
grounded in 8 transcripts. Only the components he actually specifies are gated here:

  1. inside a macro window (MANDATORY per qngA8aIfV0M 03:00 — "even by 5 minutes... No")
  2. a liquidity sweep of a 15-min swing high/low or a session extreme
  3. a market-structure shift against the sweep
  4. a fair value gap printed by the displacement leg
  5. price returns to fill that FVG  <- the entry

DELIBERATELY OMITTED, and this is why a null here could NOT kill the candidate under
§5.9.1 ("tested AS TAUGHT, mandatory triggers included"):
  - the inverse ORDER BLOCK pairing — he never defines how to identify an order block
  - the ES leading trigger — entry fires on ES tapping ITS gap first (qngA8aIfV0M 08:01);
    we hold no ES data at all
  - the multi-timeframe BIAS filter — the per-timeframe rule is stated, the aggregation is not

Span: 2025-07-01 -> 2026-07-15 (bar data ends 2026-07-15). Sealed 2023/24 never touched.

    python -m scripts.nya_sb01_feasibility
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
START, END = "2025-01-01", "2026-07-15"
FLOOR = 30
# his macro schedule, ET local (qngA8aIfV0M 00:27-01:46). 12:45-13:15 is SKIPPED by him.
MACROS = [("AM1", 9 * 60 + 45, 10 * 60 + 15), ("AM2", 10 * 60 + 45, 11 * 60 + 15),
          ("LUNCH", 11 * 60 + 45, 12 * 60 + 15), ("PM", 13 * 60 + 45, 14 * 60 + 15)]
SWING_K = 2          # 15-min fractal: high greater than K bars either side
MSS_LOOKBACK = 20    # 1-min bars back to find the most recent short-term extreme


def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    b = b.assign(ts=pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY))
    lo = pd.Timestamp(START, tz=NY)
    hi = pd.Timestamp(END, tz=NY) + pd.Timedelta(days=1)
    b = b[(b.ts >= lo) & (b.ts < hi)]
    b["day"] = b.ts.dt.strftime("%Y-%m-%d")
    b["mins"] = b.ts.dt.hour * 60 + b.ts.dt.minute
    return b.reset_index(drop=True)


def swing_levels(day_bars: pd.DataFrame, before_mins: int) -> tuple[list, list]:
    """15-min fractal swing highs/lows formed BEFORE the macro opens (frozen)."""
    pre = day_bars[day_bars.mins < before_mins]
    if len(pre) < 60:
        return [], []
    g = pre.set_index("ts").resample("15min").agg({"high": "max", "low": "min"}).dropna()
    if len(g) < 2 * SWING_K + 1:
        return [], []
    hi, lo = g.high.to_numpy(), g.low.to_numpy()
    hs, ls = [], []
    for i in range(SWING_K, len(g) - SWING_K):
        w_h, w_l = hi[i - SWING_K:i + SWING_K + 1], lo[i - SWING_K:i + SWING_K + 1]
        if hi[i] == w_h.max() and (w_h.argmax() == SWING_K):
            hs.append(float(hi[i]))
        if lo[i] == w_l.min() and (w_l.argmin() == SWING_K):
            ls.append(float(lo[i]))
    return hs, ls


def session_extremes(day_bars: pd.DataFrame, prev_bars: pd.DataFrame) -> dict:
    """Asia and London extremes — his named session liquidity (1cMWnAxElA0 02:07)."""
    out = {}
    asia = pd.concat([prev_bars[prev_bars.mins >= 18 * 60], day_bars[day_bars.mins < 3 * 60]])
    lon = day_bars[(day_bars.mins >= 3 * 60) & (day_bars.mins < 9 * 60 + 30)]
    if len(asia):
        out["asia_hi"], out["asia_lo"] = float(asia.high.max()), float(asia.low.min())
    if len(lon):
        out["lon_hi"], out["lon_lo"] = float(lon.high.max()), float(lon.low.min())
    return out


def find_fvg(w: pd.DataFrame, i: int, side: int) -> float | None:
    """3-bar FVG ending at or before i. side=-1 bearish (short), +1 bullish (long).
    Bearish: bar[j-2].low > bar[j].high  -> gap = (bar[j].high, bar[j-2].low)."""
    for j in range(max(2, i - 6), i + 1):
        a, c = w.iloc[j - 2], w.iloc[j]
        if side < 0 and a.low > c.high:
            return float(c.high), float(a.low), j - 2
        if side > 0 and a.high < c.low:
            return float(c.low), float(a.high), j - 2
    return None


def order_block(w, fvg_start: int, side: int, max_back: int = 12):
    """OUR definition, NOT his — he never specifies identification (8 transcripts).

    ICT canon: the last candle opposing the displacement, immediately before the leg that
    broke structure. Short setup -> the last UP candle before the down-displacement.

    Returns (level, idx): the level is the OB's protective extreme — its HIGH for a short,
    LOW for a long. A stop sits just beyond it.
    """
    for j in range(fvg_start, max(-1, fvg_start - max_back), -1):
        if j < 0:
            break
        bar = w.iloc[j]
        up = bar.close > bar.open
        if (side < 0 and up) or (side > 0 and not up):
            return (float(bar.high) if side < 0 else float(bar.low)), j
    return None, None


def scan() -> pd.DataFrame:
    b = load_bars()
    by_day = {d: g.reset_index(drop=True) for d, g in b.groupby("day", sort=False)}
    days = sorted(by_day)
    rows = []
    for k, d in enumerate(days):
        g = by_day[d]
        prev = by_day[days[k - 1]] if k else g.iloc[0:0]
        for name, m0, m1 in MACROS:
            w = g[(g.mins >= m0) & (g.mins <= m1)].reset_index(drop=True)
            if len(w) < 20:
                continue
            hs, ls = swing_levels(g, m0)
            ext = session_extremes(g, prev)
            sell_side = ls + [ext.get("asia_lo"), ext.get("lon_lo")]
            buy_side = hs + [ext.get("asia_hi"), ext.get("lon_hi")]
            sell_side = [x for x in sell_side if x is not None]
            buy_side = [x for x in buy_side if x is not None]

            rec = {"day": d, "macro": name, "swept": False, "mss": False, "fvg": False,
                   "entry": False}
            # gate 2 — a sweep of either side inside the window
            for lv, side in [(x, -1) for x in buy_side] + [(x, +1) for x in sell_side]:
                hit = (w.high > lv) if side < 0 else (w.low < lv)
                if not hit.any():
                    continue
                rec["swept"] = True
                s = int(hit.idxmax())
                # gate 3 — MSS: close beyond the most recent opposite short-term extreme
                seg = w.iloc[max(0, s - MSS_LOOKBACK):s + 1]
                if not len(seg):
                    continue
                ref = float(seg.low.min()) if side < 0 else float(seg.high.max())
                post = w.iloc[s + 1:]
                if not len(post):
                    continue
                brk = (post.close < ref) if side < 0 else (post.close > ref)
                if not brk.any():
                    continue
                rec["mss"] = True
                m = int(brk.idxmax())
                # gate 4 — an FVG left by the displacement
                edge = find_fvg(w, m, side)
                if edge is None:
                    continue
                rec["fvg"] = True
                # gate 5 — price returns to fill it (the entry)
                fwd = w.iloc[m + 1:]
                if len(fwd) and ((fwd.high >= edge).any() if side < 0
                                 else (fwd.low <= edge).any()):
                    rec["entry"] = True
                    break
            rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    d = scan()
    d["era"] = np.where(d.day < "2026-01-01", "2025H2", "2026H1")
    print("NYA-SB-01 GATED FEASIBILITY — ash10hazard silver bullet. COUNTS ONLY, no outcomes.")
    print(f"span {START} -> {END}   macro windows: "
          f"{', '.join(n for n, _, _ in MACROS)} (12:45-13:15 skipped, per him)\n")
    print(f"{'gate stack':<52}{'2025H2':>8}{'2026H1':>8}  floor n>={FLOOR}")
    print("-" * 78)
    stack = [("0. macro windows present", d.index.to_series().notna()),
             ("1. + liquidity sweep (15m swing or session extreme)", d.swept),
             ("2. + market structure shift", d.mss),
             ("3. + fair value gap from the displacement", d.fvg),
             ("4. + price returns to fill the FVG  <- THE ENTRY", d.entry)]
    for label, mask in stack:
        n25 = int(mask[d.era == "2025H2"].sum())
        n26 = int(mask[d.era == "2026H1"].sum())
        ok = "OK" if min(n25, n26) >= FLOOR else "UNTESTABLE"
        print(f"{label:<52}{n25:>8}{n26:>8}  {ok}")
    e = d[d.entry]
    print(f"\nentries per macro window: {dict(e.macro.value_counts())}")
    print(f"trading days covered: {d.day.nunique()}   "
          f"entries/day: {len(e) / max(1, d.day.nunique()):.2f}")
    print("\nOMITTED from this stack (he specifies them, we cannot compute them):")
    print("  - inverse ORDER BLOCK pairing  (he never defines identification)")
    print("  - ES leading trigger           (no ES data held)")
    print("  - multi-timeframe BIAS filter  (aggregation rule never stated)")
    print("Each would only REDUCE the counts above. This is an upper bound.")
    print("\nNOT A VERDICT. No outcome measured, no trial recorded.")


if __name__ == "__main__":
    main()
