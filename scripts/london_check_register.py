#!/usr/bin/env python3
"""CONSOLIDATED CHECK REGISTER — every candidate from every order-flow mining workflow.

Six workflows mined ~3,300 variables across 25 families for Angus-style binary checks on the
London 10:00-13:00 UK book. Their results live in separate task outputs and journals. This pulls
them into one ranked table so the keep/cut decision is a single view.

THE BAR EVERY CHECK IS JUDGED AGAINST. Day-block permutation nulls run by the workflow sceptics
say that mining this many variables on ~41 effective days produces a best sign-stable lift of
about +1.5R HALF THE TIME under pure noise. So:

    lift < 1.50R   -> at or below the median of what noise produces. Not evidence.
    lift 1.5-2.0R  -> inside the noise band's upper half. Weak at best.
    lift > 2.0R    -> worth hardening, still needs family-wise correction.

A check also has to clear three structural tests that killed most of the field:
    sign_stable    same sign in H1 and H2 on a threshold frozen in H1
    day count      signals cluster within days; effective n is DAYS, not signals
    not restated   must not re-express the entry rules (MA stack, 50-MA wick, fading volume,
                   5-70pt stop) or another check already in the score

    LONDON_SCRATCH=<dir> python3 scripts/london_check_register.py [--min-lift 0.0]
"""
import glob
import json
import os
import sys

import pandas as pd

TASKS = "/tmp/claude-0/-home-user-AI-trading-agents/c2c5ecfb-26be-555c-a4e7-e400e2cf3ead/tasks"
WFDIR = ("/root/.claude/projects/-home-user-AI-trading-agents/"
         "c2c5ecfb-26be-555c-a4e7-e400e2cf3ead/subagents/workflows")
NOISE_MEDIAN = 1.50

SOURCES = {
    "wvt1a1foj": "depth", "wek61t26w": "tape", "wl9nfn5ft": "geometry",
    "w1f128bm1": "footprint", "wxymlmu7y": "context", "w9cbeoq1h": "priceaction",
}
WF_JOURNALS = {
    "wf_2edf9547-ed1": "depth", "wf_d36c1dfc-5d8": "tape", "wf_775118c5-45f": "geometry",
    "wf_e261d5b5-e65": "footprint", "wf_216ca51b-d2e": "context", "wf_d36569df-ee9": "priceaction",
}

MIN_LIFT = 0.0
if "--min-lift" in sys.argv:
    MIN_LIFT = float(sys.argv[sys.argv.index("--min-lift") + 1])


def norm_wr(x):
    """Miners reported win rate as either a fraction or a percentage. Normalise to percent."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v * 100.0 if 0.0 <= v <= 1.0 else v


def harvest():
    rows, seen_src = [], set()
    # journals are the reliable source: one result line per completed agent
    for wf, fam in WF_JOURNALS.items():
        jp = f"{WFDIR}/{wf}/journal.jsonl"
        if not os.path.exists(jp):
            continue
        for line in open(jp):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "result":
                continue
            r = d.get("result")
            if not isinstance(r, dict) or "checks" not in r:
                continue
            seen_src.add(fam)
            for c in r.get("checks") or []:
                try:
                    lift = float(c["avgr_pass"]) - float(c["avgr_fail"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append(dict(
                    family=fam, name=c.get("name", "?")[:34],
                    verdict=c.get("verdict", "?"),
                    n_pass=c.get("n_pass"),
                    wr_pass=norm_wr(c.get("wr_pass")), wr_fail=norm_wr(c.get("wr_fail")),
                    avgr_pass=c.get("avgr_pass"), avgr_fail=c.get("avgr_fail"),
                    lift=lift,
                    h1=c.get("h1_liftR"), h2=c.get("h2_liftR"),
                    stable=bool(c.get("sign_stable")),
                    rule=(c.get("rule") or "")[:80],
                ))
    return pd.DataFrame(rows), seen_src


if __name__ == "__main__":
    R, fams = harvest()
    if not len(R):
        raise SystemExit("no checks harvested -- workflows may not have written journals yet")
    missing = set(WF_JOURNALS.values()) - fams
    print(f"families harvested: {sorted(fams)}")
    if missing:
        print(f"NOT YET IN (workflow still running): {sorted(missing)}")

    R = R[R.lift.notna()].copy()
    R["decay"] = R.apply(
        lambda r: (abs(r.h2) / abs(r.h1)) if (r.h1 not in (None, 0) and r.h2 is not None
                                              and abs(r.h1) > 1e-9) else float("nan"), axis=1)
    R["tier"] = pd.cut(R.lift, [-99, MIN_LIFT, NOISE_MEDIAN, 2.0, 99],
                       labels=["negative", "below-noise", "noise-band", "above-noise"])

    print(f"\ntotal checks reported: {len(R)}   "
          f"CANDIDATE {int((R.verdict=='CANDIDATE').sum())}  "
          f"WEAK {int((R.verdict=='WEAK').sum())}  NOISE {int((R.verdict=='NOISE').sum())}")
    print(f"\nvs the noise floor (best-of-N median = +{NOISE_MEDIAN:.2f}R):")
    print(R.tier.value_counts().reindex(
        ["above-noise", "noise-band", "below-noise", "negative"]).to_string())

    keep = R[(R.lift > MIN_LIFT) & R.stable].sort_values("lift", ascending=False)
    print(f"\n{'='*118}")
    print("SIGN-STABLE CHECKS, RANKED BY LIFT  (the only ones worth arguing about)")
    print(f"{'='*118}")
    print(f"{'family':<11} {'check':<34} {'n':>4} {'WRp':>5} {'WRf':>5} "
          f"{'lift':>6} {'H1':>6} {'H2':>6} {'keep?':>12}")
    print("-" * 118)
    for _, r in keep.iterrows():
        if r.lift > 2.0:
            flag = "HARDEN"
        elif r.lift >= NOISE_MEDIAN:
            flag = "noise band"
        else:
            flag = "below noise"
        h1 = r.h1 if r.h1 is not None else float("nan")
        h2 = r.h2 if r.h2 is not None else float("nan")
        print(f"{r.family:<11} {r['name']:<34} {r.n_pass:>4} {r.wr_pass:>4.0f}% {r.wr_fail:>4.0f}% "
              f"{r.lift:>+6.2f} {h1:>+6.2f} {h2:>+6.2f} {flag:>12}")

    print(f"\n{'='*118}")
    print("CLEAN NEGATIVES WORTH KEEPING ON RECORD (checks that fired but pointed the wrong way)")
    print(f"{'='*118}")
    neg = R[R.lift < -0.3].sort_values("lift")
    for _, r in neg.head(12).iterrows():
        print(f"  {r.family:<11} {r['name']:<34} lift {r.lift:>+6.2f}   {r.rule[:56]}")

    R.sort_values("lift", ascending=False).to_csv(
        f"{os.environ.get('LONDON_SCRATCH', '.')}/london_check_register.csv", index=False)
    print(f"\nwrote london_check_register.csv  ({len(R)} rows)")
    print("\nNOTE: 'lift' here is the miners' raw in-sample figure. It is NOT corrected for the")
    print("family-wise search. Only the workflow sceptics' FWER p-values settle a check, and only")
    print("PBAL has cleared one so far (FWER p 0.004-0.008).")
