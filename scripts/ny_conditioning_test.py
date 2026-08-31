#!/usr/bin/env python3
"""NY CONDITIONING VARIABLE TEST — does the overnight tell you how to trade NY?

    python -m scripts.ny_conditioning_test

His question (2026-08-31): "How does asia and London effect New York and does
trading according to that knowledge affect WR do variable test."

Eight overnight/London-derived conditions applied as candidate filters on the
NY window of the v2 full-day corpus, each scored by mechanical 2R-rate,
split-half validated: IS = first half of session-days, OOS = second half.
A condition earns anything only if its spread holds sign and size in BOTH
halves — one-half spreads are noise by construction here.

Variables (all as-of 09:30, no lookahead):
  onp      overnight (18:00->09:30) range percentile vs trailing 120 days,
           quartile buckets (needs 40-day warmup; early days excluded)
  eff      overnight efficiency |net|/range >= 0.45 -> trend_on else chop_on
  ldir     candidate side WITH vs AGAINST the London net drift
  llate    candidate side WITH vs AGAINST the late-London (08:30->09:29) drift
  pd_pos   09:29 close vs prior session-day high/low: above/inside/below
  va_pos   09:29 close vs prior session-day value area: above/inside/below
  va_side  open outside value only: candidate trading TOWARD value vs away
  pd_side  open outside prior range only: candidate trading BACK INTO the
           prior range vs breakout continuation

Outcome model = the corpus's crude mech model (decision-close entry,
last-15m-extreme stop, 2R-or-stop at 120m) — a ranker, not a P&L. Any
survivor is a PREREG CANDIDATE for the seven-gate treatment, not doctrine.
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import volume_profile                  # noqa: E402


def main() -> int:
    bars = OB.get_bars()
    src = ROOT / "output/analysis/candidate_corpus_fullday_v2.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(src, "rt")]
    ny = [r for r in rows if r["window"] == "NY" and r.get("mech_outcome")]
    days_with_ny = sorted({r["sess_day"] for r in ny})

    V = {}
    onr_hist = []
    for d in days_with_ny:
        t0 = pd.Timestamp(f"{d} 18:00", tz=OB.NY)
        on = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=15, minutes=30))]
        A = on[on.index < t0 + pd.Timedelta(hours=9)]
        L = on[on.index >= t0 + pd.Timedelta(hours=9)]
        before = bars[bars.index < t0]
        if len(on) < 500 or len(A) < 300 or len(L) < 250 or not len(before):
            continue
        onr = float(on.high.max() - on.low.min())
        net = float(on.close.iloc[-1] - on.open.iloc[0])
        lnet = float(L.close.iloc[-1] - L.open.iloc[0])
        llast = L[L.index >= t0 + pd.Timedelta(hours=14, minutes=30)]
        llate = float(llast.close.iloc[-1] - llast.open.iloc[0]) if len(llast) else 0
        last = before.index[-1]
        pa = last.normalize() + pd.Timedelta(hours=18)
        if last < pa:
            pa -= pd.Timedelta(days=1)
        pseg = before[(before.index >= pa) & (before.index < pa + pd.Timedelta(hours=23))]
        open930 = float(on.close.iloc[-1])
        pd_pos = va_pos = None
        if len(pseg) >= 300:
            ph, pl = float(pseg.high.max()), float(pseg.low.min())
            pd_pos = "above" if open930 > ph else ("below" if open930 < pl else "inside")
            poc, val, vah = volume_profile(pseg)
            va_pos = "above" if open930 > vah else ("below" if open930 < val else "inside")
        onp = (np.array(onr_hist[-120:]) < onr).mean() if len(onr_hist) >= 40 else None
        onr_hist.append(onr)
        V[d] = dict(onp=onp, eff=abs(net) / onr if onr else 0, ldir=np.sign(lnet),
                    llate=np.sign(llate), pd_pos=pd_pos, va_pos=va_pos)

    half = days_with_ny[len(days_with_ny) // 2]

    def wr(rs):
        n = len(rs)
        return (sum(1 for x in rs if x["mech_outcome"] == "2R") / n if n else 0.0, n)

    def bucket_of(r, var):
        v = V.get(r["sess_day"])
        if not v:
            return None
        if var == "onp":
            return None if v["onp"] is None else "Q" + str(min(3, int(v["onp"] * 4)) + 1)
        if var == "eff":
            return "trend_on" if v["eff"] >= 0.45 else "chop_on"
        if var == "ldir":
            return "with_london" if (v["ldir"] > 0) == (r["side"] == "long") else "against_london"
        if var == "llate":
            return "with_late" if (v["llate"] > 0) == (r["side"] == "long") else "against_late"
        if var == "pd_pos":
            return v["pd_pos"]
        if var == "va_pos":
            return v["va_pos"]
        if var == "va_side":
            if v["va_pos"] in (None, "inside"):
                return None
            t = (v["va_pos"] == "above" and r["side"] == "short") or \
                (v["va_pos"] == "below" and r["side"] == "long")
            return "toward_value" if t else "away_from_value"
        if var == "pd_side":
            if v["pd_pos"] in (None, "inside"):
                return None
            b = (v["pd_pos"] == "above" and r["side"] == "short") or \
                (v["pd_pos"] == "below" and r["side"] == "long")
            return "back_into_range" if b else "breakout_continuation"
        return None

    bi = wr([r for r in ny if r["sess_day"] < half])
    bo = wr([r for r in ny if r["sess_day"] >= half])
    print(f"split-half boundary (first OOS day): {half}")
    print(f"BASELINE NY 2R-rate: in-sample {bi[0]:.1%} (n={bi[1]}) | out-sample {bo[0]:.1%} (n={bo[1]})\n")
    print(f"{'variable':10}{'bucket':24}{'IS 2R%':>8}{'IS n':>7}{'OOS 2R%':>9}{'OOS n':>7}")
    for var in ("onp", "eff", "ldir", "llate", "pd_pos", "va_pos", "va_side", "pd_side"):
        seen = defaultdict(lambda: ([], []))
        for r in ny:
            b = bucket_of(r, var)
            if b is None:
                continue
            (seen[b][0] if r["sess_day"] < half else seen[b][1]).append(r)
        for b in sorted(seen):
            i, o = wr(seen[b][0]), wr(seen[b][1])
            print(f"{var:10}{b:24}{i[0]:>8.1%}{i[1]:>7}{o[0]:>9.1%}{o[1]:>7}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
