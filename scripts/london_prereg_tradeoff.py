#!/usr/bin/env python3
"""Which hypotheses can a 128-day holdout actually ANSWER? FIT ONLY. Holdout stays sealed.

Three candidates are competing for pre-registration slots against the one already declared:

  S1  floor-5 / wall redundancy          (already in docs/LONDON-PREREGISTRATION.md §3)
  S2  the both-W+FAR vs one-only ladder  (docs/LONDON-TIER-TEST.md)
  S3  mild deep-fade filter, VWAP >= -0.25 (docs/LONDON-VWAP-FILTER.md)
  S4  depth-gated deep fades              (docs/LONDON-FADE-CONVICTION.md)

Adding a question is not free: Sidak correction over k tests tightens every per-test alpha, so a
4th hypothesis makes the PRIMARY harder to confirm. And a hypothesis whose subset is too small to
resolve at that alpha spends a slot to buy a guaranteed shrug. The prereg already applies this
logic once (§3 rejects two combination rules at n~61-67 because "the sealed set is 128 days and
cannot supply it"); this script applies the SAME arithmetic to the new candidates so the decision
is made on power, not enthusiasm.

METHOD. Project each subset's holdout n by scaling the fit rate per available session day (the
holdout's 128-day count is already declared in the prereg; NOTHING is read from the sealed span).
Then compute POWER — the chance the run detects each effect if the fit-measured effect is real
and persists — at the per-test alpha each multiplicity implies.

Power, not a binary "answerable" flag: the difference between 20% and 79% is the difference
between a question worth asking and a slot spent on a shrug, and a flag hides it.

FRAME EACH HYPOTHESIS AS THE DECISION IT DRIVES. This is not cosmetic — it was the single
biggest error in building this script. S1 first scored 2% power as a DIFFERENCE in mean R between
the floor-5 and floor-9.5 books; but those means are nearly equal (+0.590 vs +0.513) and the two
books heavily overlap (floor-5 CONTAINS floor-9.5), so that test asks a question nobody is making
a decision on. The actual decision is "do the ADDED sub-9.5 trades make money", a one-sample
expectancy test on the incremental band — same data, 88% power. Wrong framing turned the
best-powered question on the list into the worst.

    python -m scripts.london_prereg_tradeoff
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, lon_pop, write  # noqa: E402

HOLDOUT_DAYS = 128          # declared in docs/LONDON-PREREGISTRATION.md — not read from the span
DEEP = -0.25
POWER = 0.80


def zq(p: float) -> float:
    """Inverse standard-normal CDF by bisection on erf. No scipy dependency."""
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def mde_two_sample(sd: float, n1: float, n2: float, alpha: float, power: float = POWER) -> float:
    if n1 <= 1 or n2 <= 1:
        return float("inf")
    return (zq(1 - alpha / 2) + zq(power)) * sd * math.sqrt(1 / n1 + 1 / n2)


def mde_one_sample(sd: float, n: float, alpha: float, power: float = POWER) -> float:
    if n <= 1:
        return float("inf")
    return (zq(1 - alpha / 2) + zq(power)) * sd / math.sqrt(n)


def se_of(sd: float, n1: float, n2: float | None) -> float:
    """Standard error of the effect: one-sample if n2 is None, else two-sample."""
    if n2 is None:
        return sd / math.sqrt(n1) if n1 > 1 else float("inf")
    return sd * math.sqrt(1 / n1 + 1 / n2) if (n1 > 1 and n2 > 1) else float("inf")


def power_of(eff: float, se: float, alpha: float) -> float:
    """P(detecting an effect of this size at this alpha). The honest quantity — a binary
    'answerable?' hides the difference between 25% power and 79% power."""
    if not math.isfinite(se) or se <= 0 or eff is None:
        return 0.0
    return 0.5 * (1 + math.erf((abs(eff) / se - zq(1 - alpha / 2)) / math.sqrt(2)))


def main() -> None:
    P = lon_pop()
    t = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).copy()
    t["dir"] = t.ent_vs_vwap_sd_dir
    t["both"] = ((t.W == 1) & (t.FAR == 1))
    sd = float(t.R.std(ddof=1))

    # Available fit session days. The L0 census carries `ts` rather than `day`; a session day is a
    # distinct ET calendar date on which the window produced at least one trigger — the same
    # denominator the holdout's declared 128-day count uses.
    cen = pd.read_parquet(ROOT / "output/l0_triggers_london_fit.parquet")
    fit_days = int(pd.to_datetime(cen.ts, format="mixed", utc=True)
                   .dt.tz_convert("America/New_York").dt.date.nunique())
    scale = HOLDOUT_DAYS / fit_days

    # S1's incremental band: sub-9.5 candidates that pass the wall check. The floor-5 book
    # CONTAINS the floor-9.5 book, so comparing the two books directly compares heavily
    # overlapping sets and understates the variance of the difference.
    sub95 = lon_book(P[(P.risk >= 5.0) & (P.risk < 9.5)], floor=5.0, lifetime=math.inf, cap=999)

    deep = t[t.dir < DEEP]
    sgn = np.where(deep.direction.values == "long", 1.0, -1.0)     # depth gate: the working lens
    imb = deep.dep_imb.values * sgn
    hi = deep[imb > np.nanmedian(imb)]
    ungated = deep[~deep.index.isin(hi.index)]

    # Each hypothesis is framed as the DECISION it drives, and that fixes the test shape. Getting
    # this wrong is not cosmetic: a first pass scored S1 as a DIFFERENCE in mean R between the
    # floor-5 and floor-9.5 books and returned 2% power — but those two means are nearly equal
    # (+0.590 vs +0.513), while the decision being made is "does the extra band make money at
    # all". Framed as a one-sample expectancy test on the incremental band it becomes the
    # best-powered question on the list. Same logic for S3.
    #   "one" -> is this subset's mean R greater than zero?
    #   "two" -> do these two subsets differ from each other?
    subsets = [
        ("PRIMARY — book mean R > 0", "one", len(t), None, float(t.R.mean()),
         float(t.R.std(ddof=1)), "does the edge exist on unseen data"),
        ("S1 — sub-9.5 wall band mean R > 0", "one", len(sub95), None, float(sub95.R.mean()),
         float(sub95.R.std(ddof=1)), "drop the risk floor 9.5 -> 5?"),
        ("S2 — both-W+FAR vs exactly-one", "two", int(t.both.sum()), int((~t.both).sum()),
         float(t[t.both].R.mean() - t[~t.both].R.mean()), sd, "is there a conviction ladder?"),
        ("S3 — deep fades mean R > 0", "one", len(deep), None, float(deep.R.mean()),
         float(deep.R.std(ddof=1)), "filter out deep counter-VWAP fades?"),
        ("S4 — depth-gated vs ungated fades", "two", len(hi), len(ungated),
         float(hi.R.mean() - ungated.R.mean()), sd, "does depth give conviction on fades?"),
    ]

    L = ["# Which hypotheses can the 128-day holdout actually answer?\n",
         "\n**Fit only. The sealed span is NOT read here — the 128-day count is quoted from the "
         "pre-registration, and every holdout n below is a PROJECTION from the fit rate.**\n",
         f"\nFit span: **{fit_days} session days**, book **{len(t)} trades**, R standard deviation "
         f"**{sd:.3f}**. Holdout: **{HOLDOUT_DAYS} days**, so subsets project at **x{scale:.2f}** "
         f"— a projected book of only **~{len(t) * scale:.0f} trades**.\n",
         "\n## The arithmetic that decides this\n\n"
         "Sidak over k tests sets per-test alpha = 1 - (1 - 0.05)^(1/k). More questions means a "
         "tighter bar on EVERY question, the primary included:\n\n"
         "| questions asked | per-test alpha |\n|---|---|\n"]
    ALPHAS = {k: 1 - (1 - 0.05) ** (1 / k) for k in (2, 3, 4, 5)}
    for k, a in ALPHAS.items():
        L.append(f"| {k} | {a:.4f} |\n")

    L.append("\n## Projected size and POWER, per candidate\n\n"
             "Power = the chance this holdout detects the effect **if the fit-measured effect is "
             "real and persists exactly**. It is the honest quantity: a yes/no 'answerable' flag "
             "hides the difference between 20% power and 79% power. Under ~50% is a coin flip "
             "dressed as a test — it will usually return an inconclusive shrug, and a shrug still "
             "costs a slot and still tightens everyone else's alpha.\n\n"
             "| hypothesis | the decision it drives | fit n | projected n | fit effect (mean R) | "
             "k=2 | **k=3** | k=4 | k=5 |\n|---|---|---|---|---|---|---|---|---|\n")
    V = {}
    for name, kind, n1, n2, eff, sdi, drives in subsets:
        p1 = n1 * scale
        p2 = (n2 * scale) if (kind == "two") else None
        se = se_of(sdi, p1, p2)
        pw = {k: power_of(eff, se, a) for k, a in ALPHAS.items()}
        V[name] = dict(eff=eff, se=se, pw=pw, p1=p1, p2=p2, drives=drives)
        nfit = f"{n1}" if kind == "one" else f"{n1} / {n2}"
        nproj = f"~{p1:.0f}" if kind == "one" else f"~{p1:.0f} / ~{p2:.0f}"
        L.append(f"| {name} | {drives} | {nfit} | {nproj} | {eff:+.3f} | "
                 + " | ".join(f"{'**' if k == 3 else ''}{pw[k] * 100:.0f}%"
                              f"{'**' if k == 3 else ''}" for k in (2, 3, 4, 5)) + " |\n")

    prim, S1 = V["PRIMARY — book mean R > 0"], V["S1 — sub-9.5 wall band mean R > 0"]
    S2, S3, S4 = (V["S2 — both-W+FAR vs exactly-one"], V["S3 — deep fades mean R > 0"],
                  V["S4 — depth-gated vs ungated fades"])

    L.append(f"\n**Read the primary row first.** Even at 2 questions it carries only "
             f"**{prim['pw'][2] * 100:.0f}%** power, and ~{prim['p1']:.0f} trades with R's "
             f"standard deviation at {sd:.2f} puts the standard error on holdout mean R at about "
             f"**{prim['se']:.3f}**. A fit-sized effect of {prim['eff']:+.3f} sits roughly "
             f"{abs(prim['eff']) / prim['se']:.1f} standard errors from zero. **This holdout can "
             f"tell 'the edge is real' from 'the edge is absent'. It cannot finely grade "
             f"subsets** — and that single fact decides most of what follows.\n")

    L.append(f"\n## The surprise: the declared secondary is the strongest question\n\n"
             f"S1 is already in the prereg as the single secondary, and on this arithmetic it is "
             f"the **best-powered question available — {S1['pw'][3] * 100:.0f}% at k=3, better "
             f"than the primary itself**. The reason is size: the sub-9.5 wall-passing band is "
             f"**{S1['p1'] / scale:.0f} fit trades — larger than the {len(t)}-trade main book** — "
             f"projecting to ~{S1['p1']:.0f} on the holdout, and it carries mean R "
             f"{S1['eff']:+.3f}, *higher* than the main book's {prim['eff']:+.3f}.\n\n"
             f"It nearly got mis-scored. Framed as 'does the floor-5 book beat the floor-9.5 "
             f"book' it returns **2% power**, because those two means are almost identical and a "
             f"difference-of-means test on overlapping sets asks a question nobody cares about. "
             f"The decision is whether the ADDED trades make money, which is a one-sample "
             f"expectancy test on the incremental band. Same test, same data, 2% vs "
             f"{S1['pw'][3] * 100:.0f}% — the framing was the whole result.\n")

    L.append("\n## The conflict nobody should miss\n\n"
             "**S3 and S4 are not independent — they act on the SAME trades in OPPOSITE "
             "directions.** S3 asks whether to drop the deep fades; S4 asks which of them to "
             "keep. If S3 says drop, S4 has nothing left to gate; if S4 finds a gate, S3 is "
             "refuted. Asking both spends two slots on one question and can return a "
             "contradiction with no declared rule for resolving it. **At most one of S3/S4.**\n")

    L.append("\n## S2 and the sizing freeze\n\n"
             "§1 freezes sizing at **flat 1 NQ lot** on an ANGUS ruling — *\"no sizing until the "
             "validated volume is visible\"*. The tier ladder is a SIZING rule, so adopting it now "
             "would contradict a standing ruling — and it does not need the holdout's permission "
             "to exist later, because the holdout run at 1 lot IS the validated volume that "
             "unlocks the sizing decision afterwards.\n\n"
             "The ladder's UNDERLYING claim — that the both-W+FAR cell carries materially more R "
             "than the exactly-one cell — is a SIGNAL claim, testable at 1 lot without touching "
             "sizing. That version is already half-asked: §2's reporting item 9 is \"W/FAR lift: "
             "mean R of `either` vs `neither`\", and splitting `either` into both-vs-one is a "
             f"small extension of a number the run already reports. But at "
             f"**{S2['pw'][3] * 100:.0f}% power** it will most likely come back inconclusive, so "
             "the honest framing is REPORT IT, do not gate a decision on it.\n")

    def band(pw: float) -> str:
        return "usable" if pw >= 0.50 else ("coin flip" if pw >= 0.30 else "futile")

    L.append("\n## Recommendation\n\n"
             "| candidate | power @ k=3 | verdict |\n|---|---|---|\n"
             f"| **S1** sub-9.5 band expectancy | {S1['pw'][3] * 100:.0f}% "
             f"({band(S1['pw'][3])}) | **KEEP** — best-powered question on the list, and the one "
             f"that would most change the shipped config (floor 5 nearly triples volume) |\n"
             f"| **S2** both-vs-one separation | {S2['pw'][3] * 100:.0f}% ({band(S2['pw'][3])}) | "
             f"**ADD as a REPORTED number, not a gated test** — extends an item §2 already "
             f"reports, respects the sizing freeze, but is underpowered to rule on |\n"
             f"| **S3** deep-fade expectancy | {S3['pw'][3] * 100:.0f}% ({band(S3['pw'][3])}) | "
             f"**DEFER** — ~{S3['p1']:.0f} projected trades cannot resolve it |\n"
             f"| **S4** depth-gated fades | {S4['pw'][3] * 100:.0f}% ({band(S4['pw'][3])}) | "
             f"**DROP** — smallest subset (~{S4['p1']:.0f} vs ~{S4['p2']:.0f}), and mutually "
             f"exclusive with S3 anyway |\n")
    L.append(f"\n**Net recommendation: 3 questions — primary + S1 + S2.** That holds the primary "
             f"at {prim['pw'][3] * 100:.0f}% rather than {prim['pw'][5] * 100:.0f}% at k=5, keeps "
             f"the one genuinely well-powered secondary (S1 at {S1['pw'][3] * 100:.0f}%), and "
             f"reports S2 without pretending the holdout can rule on it.\n")
    L.append("\nS3 and S4 are this week's genuinely new findings, and the honest thing to say is "
             "that **this holdout is the wrong instrument for them**. They live in a "
             f"~{S3['p1']:.0f}-trade subset where nothing resolves at a corrected alpha. They are "
             "recorded with effect sizes and p-values intact in `docs/LONDON-VWAP-FILTER.md` and "
             "`docs/LONDON-FADE-CONVICTION.md`, to be tested on FORWARD data where sample size "
             "can be accumulated rather than rationed. Spending the referendum on them would "
             "answer neither them nor the primary well.\n")
    L.append("\n## Caveat on these projections\n\n"
             f"Every holdout n is the fit rate scaled by days ({HOLDOUT_DAYS}/{fit_days} = "
             f"x{scale:.2f}). If the sealed span trades at a different rate — plausible, 2023/24 "
             f"being a different volatility regime — the counts and the power move with it. The "
             f"ORDERING is robust (S4's subset is smallest under any rate; S1's is largest), but "
             f"the absolute percentages are indicative, not exact. Nothing was read from the "
             f"sealed span to refine them, which is the point.\n")
    write("LONDON-PREREG-TRADEOFF.md", "".join(L))
    print(f"fit days {fit_days}, scale x{scale:.2f}, sd(R) {sd:.3f}, projected book "
          f"~{len(t) * scale:.0f}")
    for k, v in V.items():
        print(f"  {k:36} eff {v['eff']:+.3f}  n~{v['p1']:5.0f}  "
              f"power k=3 {v['pw'][3] * 100:5.1f}%")


if __name__ == "__main__":
    main()
