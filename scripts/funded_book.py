#!/usr/bin/env python3
"""THE FUNDED BOOK — the official rebuilt-canon configuration. ANGUS sign-off 2026-07-29.

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

EXECUTION SEMANTICS (ANGUS rulings 2026-07-30; overlay output/aikido_cr_{span}.parquet is
LAW, scripts/apply_close_reverse.py regenerates; holdout ledger looks #3, #4, #5):
  1. TWO SESSIONS — every pre-session position is market-flattened on the first bar at/
     after 09:30 ("2 different sessions basically"); engine knob pre_flatten_at, re-run
     through the real engine.
  2. CLOSE-AND-REVERSE — an OPPOSING canon fill flattens the open trade at that fill
     (maker price, no slip) and reverses; the flip is the book's strongest exit signal.
     An opposing signal that never fills changes nothing.
  3. ONE PER LEVEL — a same-direction fill is SUPPRESSED while an open same-direction
     position sits within 3pt of its entry or shares its stop ("im all for trades in the
     same direction and all but not double entering off the same level"). Adds at
     genuinely different points still stack. Suppressed trades never existed.
  ONE sequential pass per day applies 3 then 2 on pre-flattened exits. Fit: 68 flips,
  193 suppressed (book 956->763). Holdout: 82 flips, 122 suppressed (637->515).

CONVICTION TIERS (multipliers on the profile base; cells era-consistent):
  0.5x  gold score<=3 · pre score 2      (the streaky tier; half for DD, not EV)
  1.0x  gold score 4  · pre score 3
  1.5x  gold score>=5 · pre score 4
  2.0x  ELITE: gold TRIG & LONSLOPE & struct_event=='broke' — 70%+ WR in every era
        (pooled 72%, Wilson floor 64%) — MAX ONE PER DAY

PROFILES (risk $ = base_eff x tier; budget and soft de-risk scale WITH the base —
ANGUS 2026-07-29: "with more buffer, we have more of a daily budget... the daily loss
should scale with the increased sizing"):
  lucid      base $150 fixed -> ladder $75/150/225/300, budget $800, soft -$280
             [ANGUS 2026-07-29: "static 150 is now the lucid" — supersedes the $80/160
              ladder tested earlier]
  scaled600  base $150 + $75 per full $2k of buffer past +$3k, capped $600
             (first step lands at buffer $5k) -> budget $800..$3,200, soft 35% of it

RISK SPINE (all causal: decisions see only realized-by-fill P&L + in-flight risk):
  daily budget          realized losses + in-flight risk + new risk <= budget, else skip
                        budget = base_eff x 16/3 ($800 at base $150)
                        [bounds worst day structurally; realized-loss halts alone fail
                         under overlap — the losses aren't realized when the next fills hit]
  soft de-risk          realized day P&L <= -35% of budget -> half size (both spans)
  live ramp             half size below $1,000 of buffer above the trailing line, half
                        again below $500 (ANGUS 2026-07-30, checked tightest-step-first)
                        [both steps dormant in 19 months — min buffer $1,621 fit / $1,720
                         holdout — so they change no measured number; pure insurance]
  micro clamp 40 · micros = round(risk$/(stop_pts*2)), min 1

REFERENCE RESULTS (50k account, $2k EOD-trailing, line locks at 50k; ALL THREE rules):
  lucid      fit  +$77,202 ($5,939/mo)   worst day -$670    maxDD $1,268  13/13 green
             holdout +$44,844 ($7,474/mo)  worst day -$685  maxDD $1,398   6/6 green
  scaled600  fit +$271,653 ($20,896/mo)  worst day -$2,319  maxDD $4,892  13/13 green
             holdout +$141,389 ($23,565/mo) worst day -$2,740 maxDD $4,986  6/6 green
  (Ladder, lucid: 2026-07-29 shipped $90,015/$56,409 -> +CR $97,327/$59,407 ->
   +two-session $94,695/$56,756 -> +one-per-level $77,202/$44,844. ANGUS on the
   one-per-level cost: "its fine sacrifcing the profit a bit, big deal" — the multi-TF
   sibling stack was the book's best per-trade cohort (meanR 0.68) and its removal buys
   maxDD $1,603->$1,268 fit, worst days -$762->-$670 / -$780->-$685, and scaled600 worst
   day -$3,242->-$2,319. The one metric that WORSENS: scaled600 holdout maxDD
   $4,061->$4,986 — stated, not hidden. MC funded-yr line below is PRE-rules, pending
   re-run.)
             MC funded-yr (both-span pool, 2000 sims): P(bust) 1.0%, median 28 payouts
             NOTE fit worst day -$3,242 vs that day's $3,200 budget: one day, $42 through
             (last fill's stop-out landed after the budget check passed) — known, accepted

    python -m scripts.funded_book [--span fit|holdout] [--profile lucid|scaled600]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.scorer_ny import ramp_for  # noqa: E402  (one implementation of the ramp)

PROFILES = {
    # base fixed: cap == base disables scaling entirely
    "lucid": dict(base=150.0, per=0.0, step=2000.0, after=3000.0, cap=150.0),
    "scaled600": dict(base=150.0, per=75.0, step=2000.0, after=3000.0, cap=600.0),
}
BUDGET_PER_BASE = 800.0 / 150.0     # $800 daily budget at the $150 base
SOFT_FRAC = 280.0 / 800.0           # soft de-risk at 35% of that day's budget
START, TRAIL = 50_000.0, 2_000.0
MICRO_CLAMP = 40


def load_book(span: str, cr: bool = True) -> pd.DataFrame:
    S = pd.read_parquet(ROOT / f"output/aikido_{span}.parquet")
    V = S[S.valid].copy()
    wall_bad = (V.sess == "gold") & ((V.dep_wall_below_d < 2.75) | (V.WALLSZ == 0))
    V = V[~wall_bad].copy()
    if cr:
        # CLOSE-AND-REVERSE (ANGUS ruling 2026-07-30): an opposing canon fill flattens the
        # open trade at that fill and reverses. The overlay is LAW; regenerate with
        # scripts/apply_close_reverse.py (which builds from cr=False).
        f = ROOT / f"output/aikido_cr_{span}.parquet"
        if not f.exists():
            raise FileNotFoundError(
                f"{f} missing — run `python -m scripts.apply_close_reverse` (canon "
                f"execution semantics, ANGUS 2026-07-30)")
        O = pd.read_parquet(f).set_index(["ts", "direction"])
        if "cr_suppressed" in O.columns:      # rule 3: one-per-level — these never existed
            sup = O[O.cr_suppressed].index
            V = V[~pd.MultiIndex.from_arrays([V.ts, V.direction]).isin(sup)].copy()
            O = O[~O.cr_suppressed]
        idx = pd.MultiIndex.from_arrays([V.ts, V.direction])
        hit = idx.isin(O.index)
        V["flipped"] = hit
        for col, src in (("dollars_1lot", "cr_dollars_1lot"), ("exit_ts", "cr_exit_ts"),
                         ("exit_price", "cr_exit_price")):
            V.loc[hit, col] = O.loc[idx[hit], src].to_numpy()
    else:
        V["flipped"] = False
    V["fill"] = pd.to_datetime(V.fill_ts, format="mixed", utc=True)
    V["exit"] = pd.to_datetime(V.exit_ts, format="mixed", utc=True)
    s = np.where(V.sess == "gold", V.gold_score, V.pre_score)
    V["tier"] = np.where(V.sess == "gold",
                         np.where(s <= 3, 0.5, np.where(s == 4, 1.0, 1.5)),
                         np.where(s <= 2, 0.5, np.where(s == 3, 1.0, 1.5)))
    V["elite"] = ((V.sess == "gold") & (V.TRIG == 1) & (V.LONSLOPE == 1)
                  & (V.struct_event == "broke"))
    # STABLE sort, deliberately. Same-minute fills are common (sibling triggers off one
    # cluster), and pandas' default quicksort orders those ties arbitrarily — which silently
    # decides WHICH trade of a tied group gets the day's single elite 2.0x slot. Caught by
    # tests/test_canon_scorer_ny.py when the live twin could not reproduce 4 rows out of
    # 1,534. Ties now resolve to detection order, which is what the live feed sees.
    return V.sort_values("fill", kind="mergesort")


def base_for_buffer(buf: float, p: dict) -> float:
    if p["per"] <= 0 or buf <= p["after"]:
        return p["base"]
    return min(p["cap"], p["base"] + np.floor((buf - p["after"]) / p["step"]) * p["per"])


def run(V: pd.DataFrame, profile: str) -> pd.DataFrame:
    p = PROFILES[profile]
    rows = []
    bal, line = START, START - TRAIL
    for day, g in V.groupby("day", sort=True):
        buf = bal - line
        base = base_for_buffer(buf, p)
        budget = base * BUDGET_PER_BASE
        soft = budget * SOFT_FRAC
        ramp = ramp_for(buf)
        taken: list[tuple] = []
        elite_used = False
        for r in g.itertuples():
            tier = 2.0 if (r.elite and not elite_used) else r.tier
            realized = sum(t[1] for t in taken if t[0] <= r.fill)
            inflight = sum(t[2] for t in taken if t[0] > r.fill)
            rd = base * tier * ramp * (0.5 if realized <= -soft else 1.0)
            if max(0.0, -realized) + inflight + rd > budget:
                continue
            if tier == 2.0:
                elite_used = True
            micros = int(np.clip(round(rd / (r.risk * 2.0)), 1, MICRO_CLAMP))
            pl = micros * r.dollars_1lot / 10.0
            taken.append((r.exit, pl, rd))
            rows.append({"day": day, "ts": r.ts, "sess": r.sess, "tier": tier,
                         "base": base, "budget": budget, "risk_d": rd,
                         "micros": micros, "pl": pl, "month": r.month})
        bal += sum(t[1] for t in taken)
        line = min(START, max(line, bal - TRAIL))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
    ap.add_argument("--profile", default="lucid", choices=sorted(PROFILES))
    a = ap.parse_args()
    B = run(load_book(a.span), a.profile)
    D = B.groupby("day").pl.sum()
    mo = B.groupby("month").pl.sum()
    cum = D.cumsum()
    bal, line, mb = START, START - TRAIL, 1e9
    for p in D:
        bal += p
        mb = min(mb, bal - line)
        line = min(START, max(line, bal - TRAIL))
    print(f"FUNDED BOOK [{a.span} · {a.profile}]: {len(B)} trades on {len(D)} days")
    print(f"  net ${B.pl.sum():+,.0f} (${B.pl.sum() / len(mo):,.0f}/mo) | worst day ${D.min():+,.0f} "
          f"| maxDD ${(cum.cummax() - cum).max():,.0f} | min buffer ${mb:,.0f}")
    print(f"  months green {(mo > 0).sum()}/{len(mo)} | worst month ${mo.min():+,.0f} | "
          f"tier mix {B.tier.value_counts(normalize=True).round(2).to_dict()}")
    if a.profile != "lucid":
        db = B.groupby("day").base.first()
        print(f"  base: median ${db.median():,.0f} | at cap {(db >= PROFILES[a.profile]['cap']).mean() * 100:.0f}% "
              f"| at floor {(db <= PROFILES[a.profile]['base']).mean() * 100:.0f}%")
    out = ROOT / f"output/funded_book_{a.profile}_{a.span}.parquet"
    B.to_parquet(out, index=False)
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
