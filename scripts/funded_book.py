#!/usr/bin/env python3
"""THE FUNDED BOOK — the official rebuilt-canon configuration. ANGUS sign-off 2026-07-31.

Every parameter below was measured before it was chosen, on the fit span (2025-06..2026-07,
discovery restricted to 2025) and confirmed on the sealed 2023/24 holdout. Nothing here is
a vibe. The full evidence trail: L0-L4 rebuild (docs/HANDOFF-london-rebuild.md §1 recaps),
exit study, aikido autopsy, risk-lab sweep, elite-combo hunt.

ENTRIES (uncapped — the 2/session cap measured as pure cost once the wall cut landed):
  pre  08:00-09:30   W==1  (no wall behind the trade; load-bearing, no surviving adders)
  gold 09:40-10:30   D==1  (wall ahead)  AND NOT (dep_wall_below_d < 2.75 OR WALLSZ == 0)
                     [the aikido wall-quality cut: cut set runs 37-41% WR in all 3 eras]
  risk 7-60pt Layer-0 · E3 limits · orders die at session-window end (no distance cancel)
  · news blackout · V8 exits (nothing mechanical beat them; capture gap = agent layer)

CONVICTION LADDER (risk $ per trade; tiers from era-consistent score cells):
  0.5x $80    gold score<=3 · pre score 2      (the streaky tier; half for DD, not EV)
  1.0x $160   gold score 4  · pre score 3
  1.5x $240   gold score>=5 · pre score 4
  2.0x $320   ELITE: gold TRIG & LONSLOPE & struct_event=='broke' — 70%+ WR in every era
              (pooled 72%, Wilson floor 64%) — MAX ONE PER DAY

RISK SPINE (all causal: decisions see only realized-by-fill P&L + in-flight risk):
  daily budget $800     realized losses + in-flight risk + new risk <= 800, else skip
                        [bounds worst day structurally; realized-loss halts alone fail
                         under overlap — the losses aren't realized when the next fills hit]
                        NOTE worst fit day -$795: five dollars under an $800 hard DLL.
                        budget=750 buys real margin for ~$4k of fit net if ever needed.
  soft de-risk          realized day P&L <= -$280 -> half size (validated both spans)
  live ramp             buffer above the trailing line < $1,000 -> half size
                        [dormant in 19 months of history — pure insurance for a
                         worse-than-history future; ANGUS: required for live]
  micro clamp 40 · micros = round(risk$/(stop_pts*2)), min 1

REFERENCE RESULTS (50k account, $2k EOD-trailing):
  fit      net +$93,935  ($7,226/mo)  worst day -$795  maxDD $1,722  min buffer $1,621  13/13
  holdout  net +$61,158 ($10,193/mo)  worst day -$779  maxDD $1,587  min buffer $1,756   6/6

    python -m scripts.funded_book [--span fit|holdout] [--budget 800]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RISK = {0.5: 80.0, 1.0: 160.0, 1.5: 240.0, 2.0: 320.0}
SOFT_DERISK_AT = 280.0
RAMP_BUFFER = 1000.0
START, TRAIL = 50_000.0, 2_000.0
MICRO_CLAMP = 40


def load_book(span: str) -> pd.DataFrame:
    S = pd.read_parquet(ROOT / f"output/aikido_{span}.parquet")
    V = S[S.valid].copy()
    wall_bad = (V.sess == "gold") & ((V.dep_wall_below_d < 2.75) | (V.WALLSZ == 0))
    V = V[~wall_bad].copy()
    V["fill"] = pd.to_datetime(V.fill_ts, format="mixed", utc=True)
    V["exit"] = pd.to_datetime(V.exit_ts, format="mixed", utc=True)
    s = np.where(V.sess == "gold", V.gold_score, V.pre_score)
    V["tier"] = np.where(V.sess == "gold",
                         np.where(s <= 3, 0.5, np.where(s == 4, 1.0, 1.5)),
                         np.where(s <= 2, 0.5, np.where(s == 3, 1.0, 1.5)))
    V["elite"] = ((V.sess == "gold") & (V.TRIG == 1) & (V.LONSLOPE == 1)
                  & (V.struct_event == "broke"))
    return V.sort_values("fill")


def run(V: pd.DataFrame, budget: float) -> pd.DataFrame:
    rows = []
    bal, line = START, START - TRAIL
    for day, g in V.groupby("day", sort=True):
        buf = bal - line
        ramp = 0.5 if buf < RAMP_BUFFER else 1.0
        taken: list[tuple] = []
        elite_used = False
        for r in g.itertuples():
            tier = 2.0 if (r.elite and not elite_used) else r.tier
            realized = sum(t[1] for t in taken if t[0] <= r.fill)
            inflight = sum(t[2] for t in taken if t[0] > r.fill)
            rd = RISK[tier] * ramp * (0.5 if realized <= -SOFT_DERISK_AT else 1.0)
            if max(0.0, -realized) + inflight + rd > budget:
                continue
            if tier == 2.0:
                elite_used = True
            micros = int(np.clip(round(rd / (r.risk * 2.0)), 1, MICRO_CLAMP))
            pl = micros * r.dollars_1lot / 10.0
            taken.append((r.exit, pl, rd))
            rows.append({"day": day, "ts": r.ts, "sess": r.sess, "tier": tier,
                         "risk_d": rd, "micros": micros, "pl": pl, "month": r.month})
        bal += sum(t[1] for t in taken)
        line = min(START, max(line, bal - TRAIL))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
    ap.add_argument("--budget", type=float, default=800.0)
    a = ap.parse_args()
    B = run(load_book(a.span), a.budget)
    D = B.groupby("day").pl.sum()
    mo = B.groupby("month").pl.sum()
    cum = D.cumsum()
    bal, line, mb = START, START - TRAIL, 1e9
    for p in D:
        bal += p
        mb = min(mb, bal - line)
        line = min(START, max(line, bal - TRAIL))
    print(f"FUNDED BOOK [{a.span}] budget ${a.budget:g}: {len(B)} trades on {len(D)} days")
    print(f"  net ${B.pl.sum():+,.0f} (${B.pl.sum() / len(mo):,.0f}/mo) | worst day ${D.min():+,.0f} "
          f"| maxDD ${(cum.cummax() - cum).max():,.0f} | min buffer ${mb:,.0f}")
    print(f"  months green {(mo > 0).sum()}/{len(mo)} | worst month ${mo.min():+,.0f} | "
          f"tier mix {B.tier.value_counts(normalize=True).round(2).to_dict()}")
    out = ROOT / f"output/funded_book_{a.span}.parquet"
    B.to_parquet(out, index=False)
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
