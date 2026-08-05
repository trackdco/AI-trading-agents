#!/usr/bin/env python3
"""GATE CHECK — zxck-wick-ce detector, shared host for zxck-gap-fill-edge.

COUNTS ONLY. No outcome, no R, no P&L anywhere in this file, so no statistical power is spent
and nothing enters the trial ledger. Per the LDN-DRIVE-01 / LDN-VT-01 lessons the n-floor is
checked on the FULL gate stack INCLUDING the entry trigger, before any baseline is written.

WHY ONE DETECTOR SERVES TWO CARDS
  zxck-gap-fill-edge resolved (Q16) as a LEVEL TYPE inside the wick-CE setup, not an independent
  model — both of his traded examples are 4H wick-CE trades [86DOt135Wts 01:39, 02:04]. So the
  same detected event supports two entry points, which he frames as a choice:
      "you can either use the CE or the 50%, or you can just enter on the beginning of the wick.
       That's kind of up to you."  [6opmiyFvJBA 08:13]
  -> CE entry      = zxck-wick-ce
  -> far-edge entry = zxck-gap-fill-edge
  Paired on identical events. Not two searches.

=========================== MECHANIZED RULESET, WITH PROVENANCE ==========================
[S]=stated by him  [I]=inferred  [U]=stated-by-user  [A]=our assumption  [LOCK]=locked convention

W0  WINDOW [U]   09:45-10:15 ET, dates 2025-06-01 -> 2026-07-15.
    Brake's standing macro rule + "the time we have data for order flow". NEITHER trader states
    a window for this card. See zxck-COMPONENTS.md F000.

W1  THE WICK [S]  a 1-minute bar whose wick on one side is >= WICK_PTS points.
    ⚠️ [A] He gives no size threshold for a rejection wick. His only quantified wick guidance is
    the MANIPULATION floor on the key-open card (2pt "no", 8pt "gray", 10pt ok, 15pt "yes"
    [5pL41Pl7GM4]). We reuse 10pt. THIS IS OURS BY EXTENSION, not his rule for this card.

W2  DIRECTIONAL CLOSE [S]  the bar must CLOSE against its own wick — down-close for an
    upper-wick (short), up-close for a lower-wick (long).
    "it's not a rejection block until this candle closes... that's going to give me actual
    bearish confirmation" [AGmRZ9Te9NY 02:47]. NOT the ICT definition, by his own insistence.

W3  SWEPT LIQUIDITY [S]  the wick must exceed a prior swing extreme formed before the window.
    "We swept liquidity and we had a bearish candle close. You can say that that's good enough."
    [a3LzCUZU5ko 02:24]  -- sweep + close is his stated MINIMUM.

W4  ENGINEERED LIQUIDITY BEYOND THE CE [S/I]  a prior extreme resting > 2.0 points beyond the
    CE and inside the wick's own range.
    "if it's like two points or less away from the CE, I'll just not take it" [xae9AiV5Ps4 02:16]
    ⚠️ Q3 IS UNRESOLVED BY INSTRUCTION. His two statements put this on opposite sides
    ([wS-dBenAIlY 01:11] vs [xae9AiV5Ps4 02:40]). The inside-the-wick reading rides as [inferred].

W5  ENTRY POINTS -- the fork this detector exists to compare, both [S]:
      CE       = the wick's 50%                      -> zxck-wick-ce
      FAR EDGE = the far edge of the FVG at the wick -> zxck-gap-fill-edge  [86DOt135Wts 00:50]
    A trade requires price to RETURN to that price after the wick bar.

W6  STOP [S]  beyond the wick's extreme. Same for both entries, so R differs between them and
    that difference IS the comparison.

--------------------------------- NOT IMPLEMENTED ---------------------------------
N1  PD-array coincidence and the fib -- BONUSES, per the Q8 resolution [tNyT7tHOmGI 16:19].
N2  Displacement validation -- a TELL for where to enter, not a take/skip gate [pMv3USznFdU 07:24].
N3  SMT -- needs ES, which we do not hold and Brake has declined to buy.
N4  Order flow -- computed later, never applied.
==========================================================================================

    python -m scripts.zxck_wick_gate
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import find_fvg, load_bars, swing_levels  # noqa: E402
from scripts.zxck_keyopen_baseline import FOMC, calendar  # noqa: E402

M0, M1 = 9 * 60 + 45, 10 * 60 + 15         # W0
LO, HI = "2025-06-01", "2026-07-15"
WICK_PTS = 10.0                             # W1 — OURS by extension
EL_MIN = 2.0                                # W4 — his number


def scan() -> pd.DataFrame:
    bars = load_bars()
    bars = bars[(bars.day >= LO) & (bars.day <= HI)]
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    rows = []
    for day, g in bars.groupby("day", sort=False):
        g = g.reset_index(drop=True)
        w = g[(g.mins >= M0) & (g.mins <= M1)].reset_index(drop=True)
        rec = {"day": day, "fomc": day in fomc, "window": len(w) >= 20,
               "wick": False, "close": False, "sweep": False, "el": False,
               "fvg": False, "entry_ce": False, "entry_far": False}
        if rec["fomc"] or not rec["window"]:
            rows.append(rec); continue
        hs, ls = swing_levels(g, M0)
        for i in range(len(w) - 1):
            bar = w.iloc[i]
            body_hi, body_lo = max(bar.open, bar.close), min(bar.open, bar.close)
            for side, wick_len, tip, lvls in (
                    (-1, bar.high - body_hi, bar.high, hs),      # upper wick -> short
                    (+1, body_lo - bar.low, bar.low, ls)):       # lower wick -> long
                if wick_len < WICK_PTS:                                          # W1
                    continue
                rec["wick"] = True
                down_close = bar.close < bar.open
                if (side < 0) != down_close:                                     # W2
                    continue
                rec["close"] = True
                swept = [x for x in lvls if (tip > x > body_hi) if side < 0] if side < 0 \
                    else [x for x in lvls if (tip < x < body_lo)]
                if not swept:                                                    # W3
                    continue
                rec["sweep"] = True
                ce = (bar.high + body_hi) / 2 if side < 0 else (bar.low + body_lo) / 2
                el = [x for x in lvls
                      if (side < 0 and ce + EL_MIN < x <= tip)
                      or (side > 0 and tip <= x < ce - EL_MIN)]                  # W4
                if not el:
                    continue
                rec["el"] = True
                fv = find_fvg(w, i, side)                                        # W5 far edge
                if fv is not None:
                    rec["fvg"] = True
                fwd = w.iloc[i + 1:]
                if len(fwd):
                    back_ce = (fwd.high >= ce) if side < 0 else (fwd.low <= ce)
                    if back_ce.any():
                        rec["entry_ce"] = True
                    if fv is not None:
                        far = fv[1]
                        back_far = (fwd.high >= far) if side < 0 else (fwd.low <= far)
                        if back_far.any():
                            rec["entry_far"] = True
                break
            if rec["entry_ce"] or rec["entry_far"]:
                break
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    d = scan()
    d["era"] = np.where(d.day < "2026-01-01", "2025", "2026")
    tot = len(d)
    print("GATE CHECK — zxck-wick-ce host detector. COUNTS ONLY, no outcomes measured.\n")
    print(f"window 09:45-10:15 ET   span {LO} -> {HI}   sessions {tot}")
    print(f"wick floor {WICK_PTS:.0f}pt [OURS by extension]   "
          f"engineered-liquidity min {EL_MIN:.0f}pt [his]\n")
    live = d[~d.fomc & d.window]
    print(f"{'gate':<52}{'2025':>7}{'2026':>7}{'all':>7}   floor n>=30")
    print("-" * 80)
    stack = [("0. sessions in window (FOMC excluded)", live.day.notna()),
             ("1. + a >=10pt wick", live.wick),
             ("2. + candle closes against its own wick", live["close"]),
             ("3. + that wick swept a prior swing extreme", live.sweep),
             ("4. + engineered liquidity >2pt beyond the CE", live.el),
             ("5. + an FVG at the wick", live.fvg),
             ("6a. + price returns to the CE   <- zxck-wick-ce", live.entry_ce),
             ("6b. + price returns to the FAR EDGE <- gap-fill", live.entry_far)]
    for lab, mask in stack:
        n25 = int(mask[live.era == "2025"].sum()); n26 = int(mask[live.era == "2026"].sum())
        allн = int(mask.sum())
        ok = "OK" if min(n25, n26) >= 30 else ("thin" if allн >= 30 else "UNTESTABLE")
        print(f"{lab:<52}{n25:>7}{n26:>7}{allн:>7}   {ok}")
    print(f"\nFOMC/Powell sessions excluded: {int(d.fomc.sum())}   "
          f"no-window sessions: {int((~d.window & ~d.fomc).sum())}")
    print("\nNOT A VERDICT. No outcome measured, no trial recorded.")


if __name__ == "__main__":
    main()
