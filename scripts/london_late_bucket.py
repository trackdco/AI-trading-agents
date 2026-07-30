#!/usr/bin/env python3
"""LONDON 09:30-10:00 — why it is bad, and what cutting it would do. FIT ONLY. Holdout sealed.

The within-window edge profile is not flat. Bucketed by London fill time, the book runs
+0.371 / +0.759 / +0.734 / +0.119 mean R across the four half-hours of the declared 08:00-10:00
window. The last bucket carries 23% of the trades for 4.4% of the profit. This script establishes
WHY, and then prices the obvious response.

THE DIAGNOSIS, which the numbers below support rather than assume: the late bucket does not have a
payoff problem, it has a HIT-RATE problem, and two measurable things drive it.

  1. ROOM AHEAD is highest there (0.63 vs 0.44-0.54 earlier). That is the loser signature the loss
     anatomy already isolated (docs/LONDON-LOSS-ANATOMY.md: room-ahead AUC 0.382, "losers
     higher") — entries far from value, at the extremes of an extended range, fighting mean
     reversion. By 09:30 the continuation entries are gone and what still triggers is the fades.
  2. STOP/RANGE is lowest there (5.45%) against the LARGEST realized session range (199.8pt). Same
     "the stop sits inside the noise" mechanism as the era diagnosis
     (docs/LONDON-ERA-DIAGNOSIS.md), except intraday rather than across regimes.

NOT truncation by the window close, which was the first hypothesis and is wrong: 37% of late-bucket
trades exit AFTER 10:00, so positions are not force-closed at the window edge and survivors get
their full run.

THE TRAP, stated before the numbers. The bucket is WEAK, not LOSING (+$994). Cutting it therefore
REMOVES PROFIT — the same trap the VWAP filter walked into
(docs/LONDON-VWAP-FILTER.md), where dropping the higher-loss-rate trades cost $5,856 because a
worse win rate is not a negative expectancy. So the case for cutting can only ever be
risk-adjusted, and it is presented that way.

GUARDS. (a) a time-label permutation that takes the MIN bucket in each shuffle, so the statistic
already pays for having searched four buckets; (b) per-era, since a one-era effect is not a
finding; (c) shrinkage charged at the declared 4-bucket breadth off the stage-3 curve.

    python -m scripts.london_late_bucket
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, lon_pop, maxdd, shrink, write  # noqa: E402

LON = "Europe/London"
NQ_PT = 20.0
SEED = 20260730
N_PERM = 5000
BUCKETS = [(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"),
           (540, 570, "09:00-09:30"), (570, 600, "09:30-10:00")]
CUT = "09:30-10:00"
BOUNDARIES = [570, 555, 540]        # declared sensitivity: cut from 09:30 / 09:15 / 09:00


def lonmins(s: pd.Series) -> pd.Series:
    f = pd.to_datetime(s, format="mixed", utc=True).dt.tz_convert(LON)
    return f.dt.hour * 60 + f.dt.minute


def prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["mins"] = lonmins(d.fill_ts).values
    d["exit_mins"] = lonmins(d.exit_ts).values
    d["hold"] = ((pd.to_datetime(d.exit_ts, format="mixed", utc=True)
                  - pd.to_datetime(d.fill_ts, format="mixed", utc=True))
                 .dt.total_seconds() / 60).values
    d["stop_pts"] = d.risk / NQ_PT
    d["era"] = pd.to_datetime(d.day).dt.year.astype(str)
    long = d.direction.values == "long"
    d["room_ahead"] = np.where(long, 1 - d.ent_on_pos, d.ent_on_pos)
    d["bucket"] = pd.cut(d.mins, [b[0] for b in BUCKETS] + [600], right=False,
                         labels=[b[2] for b in BUCKETS])
    return d


def stats(t: pd.DataFrame) -> dict:
    dd = t.groupby("day").dollars.sum()
    return {"n": len(t), "net": float(t.dollars.sum()), "wr": float((t.R > 0).mean()),
            "R": float(t.R.mean()), "dd": maxdd(dd),
            "risk": float(t.risk.sum()), "worst": float(t.dollars.min()),
            "n25": int((t.era == "2025").sum()), "n26": int((t.era == "2026").sum()),
            "net25": float(t[t.era == "2025"].dollars.sum()),
            "net26": float(t[t.era == "2026"].dollars.sum())}


def main() -> None:
    P = lon_pop()
    full = prep(lon_book(P, floor=9.5, lifetime=math.inf, cap=999))
    bs = stats(full)

    L = ["# London 09:30-10:00 — the weak bucket, diagnosed and priced\n",
         "\n**Fit only. Sealed 2023/24 never loaded. London standalone (no NY interaction "
         "measured here, by request).**\n",
         f"\nBook: **{bs['n']} trades, ${bs['net']:+,.0f}, {bs['wr'] * 100:.0f}% win, mean R "
         f"{bs['R']:+.3f}, maxDD ${bs['dd']:,.0f}** at flat 1 NQ lot.\n"]

    # ---------------------------------------------------------------- 1. the profile
    L.append("\n## 1. The edge is not flat across the window\n\n"
             "| London fill time | n | share of trades | win rate | mean R | net $ | "
             "share of net | 2025 R | 2026 R |\n|---|---|---|---|---|---|---|---|---|\n")
    for _lo, _hi, lab in BUCKETS:
        g = full[full.bucket == lab]
        r25, r26 = g[g.era == "2025"].R, g[g.era == "2026"].R
        L.append(f"| {'**' + lab + '**' if lab == CUT else lab} | {len(g)} | "
                 f"{len(g) / bs['n'] * 100:.0f}% | {(g.R > 0).mean() * 100:.0f}% | "
                 f"{g.R.mean():+.3f} | ${g.dollars.sum():+,.0f} | "
                 f"{g.dollars.sum() / bs['net'] * 100:.1f}% | "
                 f"{r25.mean():+.3f} | {r26.mean():+.3f} |\n")
    late = full[full.bucket == CUT]
    L.append(f"\n**{CUT} takes {len(late) / bs['n'] * 100:.0f}% of the trades for "
             f"{late.dollars.sum() / bs['net'] * 100:.1f}% of the profit**, and it is weak in "
             f"BOTH eras ({late[late.era == '2025'].R.mean():+.3f} / "
             f"{late[late.era == '2026'].R.mean():+.3f}) — structural, not a regime artifact.\n")

    # ---------------------------------------------------------------- 2. why
    L.append("\n## 2. Why — a hit-rate problem, not a payoff problem\n\n"
             "| bucket | avg WIN R | avg LOSS R | winners / losers | win rate |\n"
             "|---|---|---|---|---|\n")
    for _lo, _hi, lab in BUCKETS:
        g = full[full.bucket == lab]
        w, l = g[g.R > 0], g[g.R <= 0]
        L.append(f"| {lab} | {w.R.mean():+.2f} | {l.R.mean():+.2f} | {len(w)} / {len(l)} | "
                 f"{(g.R > 0).mean() * 100:.0f}% |\n")
    lw = late[late.R > 0]
    L.append(f"\nWhen a late trade works it pays **{lw.R.mean():+.2f}R** — competitive with the "
             f"best bucket — and its losses are normal. The setups are not junk; the strike rate "
             f"is. So the mechanism has to explain FREQUENCY of failure, not size.\n")

    L.append("\n### It is not the window close truncating them\n\n"
             "First hypothesis, and it is wrong.\n\n"
             "| bucket | median min to 10:00 | median hold | % exiting at/after 10:00 |\n"
             "|---|---|---|---|\n")
    for _lo, _hi, lab in BUCKETS:
        g = full[full.bucket == lab]
        L.append(f"| {lab} | {600 - g.mins.median():.0f} | {g.hold.median():.1f} | "
                 f"{(g.exit_mins >= 600).mean() * 100:.0f}% |\n")
    L.append(f"\n**{(late.exit_mins >= 600).mean() * 100:.0f}% of late-bucket trades exit AFTER "
             f"10:00**, so positions are not force-closed at the window edge and survivors get "
             f"their full run. Median hold is {late.hold.median():.0f} minutes against "
             f"{600 - late.mins.median():.0f} available — they die early, they do not run out of "
             f"clock.\n")

    L.append("\n### The two mechanisms that do explain it\n\n"
             "| bucket | room ahead | session range | **stop / range** | stop (pts) | "
             "pure stop % | reached partial+target % |\n|---|---|---|---|---|---|---|\n")
    mix = pd.crosstab(full.bucket, full.exit_reason, normalize="index") * 100
    for _lo, _hi, lab in BUCKETS:
        g = full[full.bucket == lab]
        L.append(f"| {lab} | {g.room_ahead.median():.2f} | {g.on_range.median():.1f} | "
                 f"**{(g.stop_pts / g.on_range).median() * 100:.2f}%** | "
                 f"{g.stop_pts.median():.2f} | {mix.loc[lab, 'stop']:.0f}% | "
                 f"{mix.loc[lab, 'partial+target']:.0f}% |\n")
    L.append("\n**Both of the project's known pathologies stack in this one bucket.**\n\n"
             "1. **Room ahead is highest here.** That is the loser signature isolated in "
             "`docs/LONDON-LOSS-ANATOMY.md` (AUC 0.382, losers higher): entries far from value, at "
             "the extremes of an already-extended range, fighting mean reversion. By 09:30 the "
             "continuation entries are gone; what still triggers is the fades.\n"
             "2. **Stop/range is lowest here, against the largest realized range.** By 09:30 the "
             "session has printed its widest range, but the structural stop is the smallest "
             "fraction of it. Same mechanism as `docs/LONDON-ERA-DIAGNOSIS.md` — a stop that is "
             "not wide enough for the volatility already realized — except intraday, every day, "
             "rather than across regimes.\n\n"
             "Consistent with the exit mix: the pure-stop rate is highest and the "
             "reached-partial+target rate lowest in exactly this bucket. Three independent "
             "measurements agreeing is why this reads as a mechanism rather than as n=43 noise.\n")

    # ---------------------------------------------------------------- 3. is it real?
    rng = np.random.default_rng(SEED)
    labs = full.bucket.values.copy()
    Rv = full.R.values
    obs_min = min(Rv[labs == lab].mean() for _lo, _hi, lab in BUCKETS)
    obs_gap = full.R.mean() - obs_min
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        sh = rng.permutation(labs)
        null[i] = Rv.mean() - min(Rv[sh == lab].mean() for _lo, _hi, lab in BUCKETS)
    p_time = float((null >= obs_gap).mean())
    L.append(f"\n## 3. Guard — is the time-of-day structure real?\n\n"
             f"Permuting the fill-time label across trades ({N_PERM:,} shuffles, seeded {SEED}) "
             f"and taking the **worst bucket in each shuffle**. Taking the min is deliberate: it "
             f"makes the statistic pay for the fact that four buckets were looked at and the worst "
             f"one chosen, so no separate multiplicity correction is owed.\n\n"
             f"| | mean R gap, book minus worst bucket |\n|---|---|\n"
             f"| observed ({CUT}) | **{obs_gap:+.3f}** |\n"
             f"| permuted median | {np.median(null):+.3f} |\n"
             f"| permuted p95 | {np.percentile(null, 95):+.3f} |\n"
             f"\n**p = {p_time:.4f}.** "
             + ("The late bucket is weaker than the worst bucket a random time-labelling produces, "
                "so the time-of-day structure carries real information.\n" if p_time < 0.05 else
                "A random time-labelling produces a worst-bucket this weak about "
                f"{p_time * 100:.0f}% of the time, so the profile is NOT distinguishable from "
                "chance clustering. The mechanism in section 2 may still be real, but the bucket's "
                "weakness on its own does not clear a null that accounts for having picked the "
                "worst of four.\n"))

    # ---------------------------------------------------------------- 4. price the cut
    L.append("\n## 4. What cutting it would do\n\n"
             "Applied at the POPULATION level and then re-selected, so a skipped trade never "
             "consumes a day-stop budget — the honest form of the counterfactual.\n\n"
             "| book | trades | net $ | win rate | mean R | maxDD | net/maxDD | risk deployed | "
             "2025 / 2026 net |\n|---|---|---|---|---|---|---|---|---|\n")
    rows = {}
    for cut_at, lab in [(None, "full window 08:00-10:00")] + \
                       [(b, f"cut from {b // 60:02d}:{b % 60:02d}") for b in BOUNDARIES]:
        if cut_at is None:
            t = full
        else:
            keep = P[lonmins(P.fill).values < cut_at]
            t = prep(lon_book(keep, floor=9.5, lifetime=math.inf, cap=999))
        s = stats(t)
        rows[lab] = s
        star = "**" if cut_at == 570 else ""
        L.append(f"| {star}{lab}{star} | {s['n']} | ${s['net']:+,.0f} | {s['wr'] * 100:.0f}% | "
                 f"{s['R']:+.3f} | ${s['dd']:,.0f} | {s['net'] / max(s['dd'], 1):.1f} | "
                 f"${s['risk']:,.0f} | ${s['net25']:+,.0f} / ${s['net26']:+,.0f} |\n")
    base, c930 = rows["full window 08:00-10:00"], rows["cut from 09:30"]
    L.append(f"\n**The 09:30 cut, stated plainly.** Net goes "
             f"${base['net']:+,.0f} -> ${c930['net']:+,.0f} "
             f"(**${c930['net'] - base['net']:+,.0f}**) on {base['n'] - c930['n']} fewer trades. "
             f"Win rate {base['wr'] * 100:.0f}% -> {c930['wr'] * 100:.0f}%, mean R "
             f"{base['R']:+.3f} -> {c930['R']:+.3f}, maxDD ${base['dd']:,.0f} -> "
             f"${c930['dd']:,.0f}, and return-on-drawdown "
             f"{base['net'] / max(base['dd'], 1):.1f} -> {c930['net'] / max(c930['dd'], 1):.1f}. "
             f"Total dollar risk deployed falls ${base['risk'] - c930['risk']:,.0f} "
             f"({(1 - c930['risk'] / base['risk']) * 100:.0f}% less capital at risk over the "
             f"span).\n")
    sh = shrink(len(BOUNDARIES))
    L.append(f"\nShrinkage charged at the declared breadth of {len(BOUNDARIES)} boundaries: "
             f"**{sh:+.3f} R** per trade off whichever cut is chosen — negligible, which is the "
             f"benefit of declaring three candidates rather than sweeping every minute.\n")

    # ---------------------------------------------------------------- 5. verdict
    L.append("\n## 5. Verdict\n\n")
    gained = c930["net"] - base["net"]
    ddcut = base["dd"] - c930["dd"]
    L.append(f"**{'Cutting it costs money' if gained < 0 else 'Cutting it adds money'}: "
             f"${gained:+,.0f}.** ")
    if gained < 0:
        L.append(f"The bucket is WEAK, not LOSING — it contributed "
                 f"${late.dollars.sum():+,.0f} — so removing it removes profit. Exactly the trap "
                 f"the VWAP filter fell into: a poor win rate is not a negative expectancy.\n")
    L.append(f"\nThe case, if there is one, is risk-adjusted: maxDD "
             f"{'falls' if ddcut > 0 else 'rises'} ${abs(ddcut):,.0f} and "
             f"{(1 - c930['risk'] / base['risk']) * 100:.0f}% less capital is put at risk, "
             f"for {(abs(gained) / base['net'] * 100):.1f}% of the net. Return-on-drawdown goes "
             f"{base['net'] / max(base['dd'], 1):.1f} -> "
             f"{c930['net'] / max(c930['dd'], 1):.1f}.\n")
    L.append(f"\n**Recommendation: do NOT cut it for this holdout.** Three reasons, in order of "
             f"weight. (1) The time-permutation guard returns p={p_time:.3f}"
             + (" — the profile does not clear a null that pays for picking the worst of four "
                "buckets.\n" if p_time >= 0.05 else " — the structure is real, but that is a "
                "reason to keep studying it, not to change a frozen config mid-flight.\n")
             + "(2) The window is FROZEN in §1 of the pre-registration; narrowing it is a config "
               "change that would invalidate the era-crossing, grid and determinism work already "
               "done against 08:00-10:00. (3) The holdout is already at 2 gated questions on ~84 "
               "projected trades and cannot price a fourth.\n")
    L.append("\n**What to do instead.** Record the profile as a declared prior and check it on the "
             "holdout as part of the primary's descriptive output — if 09:30-10:00 is the weakest "
             "bucket there too, on data owing nothing to this analysis, it becomes a properly "
             "evidenced candidate for a later window change. That costs no alpha, because it "
             "gates no decision.\n")
    write("LONDON-LATE-BUCKET.md", "".join(L))
    print(f"late bucket n={len(late)} ({len(late) / bs['n'] * 100:.0f}% of trades), "
          f"${late.dollars.sum():+,.0f} ({late.dollars.sum() / bs['net'] * 100:.1f}% of net)")
    print(f"time-permutation p = {p_time:.4f}")
    print(f"cut from 09:30: net ${base['net']:+,.0f} -> ${c930['net']:+,.0f} "
          f"({gained:+,.0f}), maxDD ${base['dd']:,.0f} -> ${c930['dd']:,.0f}, "
          f"ROdd {base['net'] / max(base['dd'], 1):.1f} -> {c930['net'] / max(c930['dd'], 1):.1f}")


if __name__ == "__main__":
    main()
