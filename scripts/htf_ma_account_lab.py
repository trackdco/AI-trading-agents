#!/usr/bin/env python3
"""ACCOUNT LAB — B2 redux: price the bust, don't minimise it.

Replaces the B2 grid's "P(bust) vs extraction" framing with a full
LIFECYCLE sim (eval -> funded -> breach -> new eval -> ...) so a bust is
paid for in dollars and downtime rather than counted. Five studies:

  1 PRICE      expected annual NET per account = withdrawals - fees, with
               downtime priced by construction (a busted account earns
               nothing while it re-passes an eval)
  2 WITHDRAW   payout threshold as a free variable (+$4k/+$6k/+$8k/year-end)
               -- the cushion-reset mechanism the B2 grid never modelled
  3 CUSHION    size as a function of distance to the frozen floor
               (DECLARED FRESH HYPOTHESIS -- see docs)
  4 PORTFOLIO  N accounts on ONE signal stream: perfectly correlated,
               calendar-aligned, staggered vs simultaneous starts
  5 HAIRCUT    every study re-run at EV -20% / -40% (per-fight constant
               subtracted; dispersion preserved -- the conservative form)

Account mechanics (LucidFlex shape, all PROVISIONAL pending trader
verification -- see FINDINGS-B2-redux.md):
  eval    50k, $2k EOD-trailing MLL, target +$3k, >=5 qualifying days
  funded  fresh 50k, $2k EOD-trailing MLL; the line LOCKS to the static
          start floor once peak >= +$2k (Initial Trail Balance)
  payout  $2k max per withdrawal, >=5 qualifying days between payouts,
          PAYOUT_CAP sim payouts per funded account (5 = graduate to the
          live review pool; None = uncapped, the old B2 assumption)
  breach  eval -> resettable for RESET_COST; funded -> account DEAD, buy a
          new eval for EVAL_COST (Lucid: "evals resettable, funded not")

    python -m scripts.htf_ma_account_lab [--draws N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED, DRAWS = 20260807, 2000
YEAR = 250                      # trading days
DD = 2000.0                     # EOD trailing MLL (50K Flex, VERIFIED)
EVAL_TARGET = 3000.0            # 50K Flex target (VERIFIED)
EVAL_SIZE = 150.0               # B1's recommended eval config (T=3, $150)
WMIN = 150.0                    # min daily profit, 50K Flex (VERIFIED)
QD = 5                          # qualifying days: eval pass + between payouts
PAYOUT_CAP_PCT = 0.50           # max request = 50% of profit (VERIFIED)
PAYOUT_CAP_ABS = 2000.0         # ...capped at $2,000 on 50K (VERIFIED)
PAYOUT_SPLIT = 0.90             # 90/10 in trader's favour (VERIFIED; whether
                                # the cap is gross or net is NOT resolved)
EVAL_CONSISTENCY = 0.50         # largest day <= 50% of profit AT PASS (Flex
                                # eval only; funded has none) (VERIFIED)
PAYOUT_MIN_BAL = 4000.0         # default: withdraw once cushion reaches this
RESET_COST = 95.0               # 50K Flex reset (SECONDARY, single source)
EVAL_COST = 130.0               # 50K Flex eval list (SECONDARY, stale)
PAYOUT_CAP = 5                  # payouts per funded account, then the account
                                # moves LIVE (VERIFIED — not a modelling knob)


def load_days(haircut: float = 0.0) -> np.ndarray:
    """Per-day (sum_R, n_fights) for the A+S1 book -> per-day R after a
    per-fight haircut delta (dispersion preserved, mean shifted)."""
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    M = pd.read_parquet(ROOT /
                        "output/htf_ma_census/mtable_fit_structclust.parquet")
    F = F.merge(M, on=["sess_day", "t", "arm", "side", "n_attempts"],
                how="left")
    R = F[(F.arm == "reject") & F.out_ship.notna()
          & (F.risk > 0)].sort_values("t")
    bk = R.groupby("structural_cluster_id", as_index=False).first()
    bk = bk[bk.flowconf != 0]
    g = bk.groupby("sess_day").out_ship.agg(["sum", "size"])
    return (g["sum"] - haircut * g["size"]).to_numpy()


def size_for(policy: dict, locked: bool, cushion: float) -> float:
    if not locked:
        return policy["s_pre"]
    if policy.get("mode") == "cushion":
        return float(np.clip(policy["k"] * cushion,
                             policy["s_min"], policy["s_max"]))
    return policy["s_post"]


def run_account(day_r: np.ndarray, seq: np.ndarray, policy: dict,
                start: int = 0, payout_cap=PAYOUT_CAP,
                payout_at: float | None = PAYOUT_MIN_BAL,
                n_days: int | None = None) -> dict:
    """One account over one calendar year (shared market sequence `seq`).
    Returns withdrawals by day, fees, and breach days."""
    state = "eval"
    bal = peak = 0.0
    locked = False
    wins = 0
    payouts = 0
    fees = EVAL_COST                       # the first eval is bought
    wd_days: list[tuple[int, float]] = []
    breaches: list[int] = []
    funded_deaths: list[int] = []          # funded breach = account destroyed
    funded_days = 0
    first_dollar = None
    max_day = 0.0                          # largest single day (eval
    #                                        consistency rule, Flex eval only)
    stop = len(seq) if n_days is None else min(start + n_days, len(seq))
    for d in range(start, stop):
        if state == "graduated":
            break
        size = EVAL_SIZE if state == "eval" else \
            size_for(policy, locked, bal)
        pnl = day_r[seq[d]] * size
        bal += pnl
        max_day = max(max_day, pnl)
        if pnl >= WMIN:
            wins += 1
        peak = max(peak, bal)
        if not locked and peak >= DD:
            locked = True
        line = 0.0 if locked else peak - DD
        if bal <= line:                    # EOD breach
            breaches.append(d)
            if state == "eval":
                fees += RESET_COST
            else:
                funded_days += 1           # the day the account died counts
                funded_deaths.append(d)
                fees += EVAL_COST          # funded is NOT resettable
                payouts = 0                # a NEW funded account gets its
                #                            own 5-payout allowance
            state, bal, peak, locked, wins = "eval", 0.0, 0.0, False, 0
            max_day = 0.0
            continue
        if state == "eval":
            # Flex eval: target AND >=5 qualifying days AND the 50%
            # consistency rule, all measured at the moment of pass
            if (bal >= EVAL_TARGET and wins >= QD
                    and max_day <= EVAL_CONSISTENCY * bal):
                state, bal, peak, locked, wins = "funded", 0.0, 0.0, False, 0
                max_day = 0.0
            continue
        funded_days += 1
        if payout_at is not None and bal >= payout_at and wins >= QD:
            take = min(PAYOUT_CAP_PCT * bal, PAYOUT_CAP_ABS)
            bal -= take
            wd_days.append((d, take * PAYOUT_SPLIT))
            wins = 0
            payouts += 1
            if first_dollar is None:
                first_dollar = d
            if payout_cap is not None and payouts >= payout_cap:
                state = "graduated"        # account moves to LucidLive
    if payout_at is None:                  # year-end sweep policy
        # ONE request is possible at year end: the $2k / 50%-of-profit cap
        # and the 5-qualifying-day gate both still apply
        if (state == "funded" and bal > 0 and wins >= QD
                and (payout_cap is None or payouts < payout_cap)):
            take = min(PAYOUT_CAP_PCT * bal, PAYOUT_CAP_ABS)
            if take > 0:
                wd_days.append((stop - 1, take * PAYOUT_SPLIT))
                payouts += 1
                if first_dollar is None:
                    first_dollar = stop - 1
    return {"wd": wd_days, "fees": fees, "breaches": breaches,
            "funded_deaths": funded_deaths,
            "funded_days": funded_days, "payouts": payouts,
            "first_dollar": first_dollar, "end_state": state,
            "end_bal": bal}


def summarize(runs: list[dict]) -> dict:
    net = [sum(w for _, w in r["wd"]) - r["fees"] for r in runs]
    gross = [sum(w for _, w in r["wd"]) for r in runs]
    nd = [len(r["funded_deaths"]) for r in runs]
    fd = [r["first_dollar"] for r in runs if r["first_dollar"] is not None]
    return {"net": float(np.mean(net)), "net_med": float(np.median(net)),
            "net_p05": float(np.percentile(net, 5)),
            "gross": float(np.mean(gross)), "fees": float(np.mean(
                [r["fees"] for r in runs])),
            "p_death": float(np.mean([n > 0 for n in nd])),
            "deaths": float(np.mean(nd)),
            "funded_days": float(np.mean([r["funded_days"] for r in runs])),
            "p_first_dollar": len(fd) / len(runs),
            "t_first": float(np.median(fd)) if fd else np.nan,
            "p_grad": float(np.mean([r["end_state"] == "graduated"
                                     for r in runs])),
            "payouts": float(np.mean([r["payouts"] for r in runs]))}


def line(tag: str, s: dict) -> str:
    return (f"{tag:26s} net ${s['net']:8,.0f} (p05 ${s['net_p05']:7,.0f}) | "
            f"fees ${s['fees']:5,.0f} | funded-death/yr {s['deaths']:4.2f} "
            f"(P>0 {s['p_death']*100:4.1f}%) | GRAD {s['p_grad']*100:5.1f}% "
            f"| payouts {s['payouts']:4.2f} | t1st "
            f"{s['t_first'] if not np.isnan(s['t_first']) else -1:5.0f}d "
            f"({s['p_first_dollar']*100:4.1f}%)")


def main() -> None:
    draws = DRAWS
    if "--draws" in sys.argv:
        draws = int(sys.argv[sys.argv.index("--draws") + 1])
    rng = np.random.default_rng(SEED)
    base = load_days()
    hair20 = load_days(0.2 * 0.257)
    hair40 = load_days(0.4 * 0.257)
    for nm, arr in (("fit", base), ("-20%", hair20), ("-40%", hair40)):
        print(f"  book {nm}: mean day R {arr.mean():+.3f} "
              f"(x$150 = ${arr.mean()*150:+.0f}/day) sd {arr.std():.2f}")
    seqs = [rng.integers(0, len(base), YEAR) for _ in range(draws)]

    print("\n=== 1+2. WITHDRAWAL POLICY x SIZING, priced (fit book, "
          f"payout cap {PAYOUT_CAP}) ===")
    print("  net = withdrawals - fees; downtime priced by construction")
    for pol_name, pol in (("150->150", {"s_pre": 150., "s_post": 150.}),
                          ("150->300", {"s_pre": 150., "s_post": 300.}),
                          ("150->600", {"s_pre": 150., "s_post": 600.})):
        for wtag, wat in (("wd@$4k", 4000.), ("wd@$6k", 6000.),
                          ("wd@$8k", 8000.), ("wd@yr-end", None)):
            runs = [run_account(base, s, pol, payout_at=wat) for s in seqs]
            print(line(f"{pol_name} {wtag}", summarize(runs)))

    print("\n=== 1a. IMPACT OF THE FLEX EVAL 50% CONSISTENCY RULE ===")
    print("  (newly discovered 2026-08-07; was NOT in the B2 model)")
    global EVAL_CONSISTENCY
    keep = EVAL_CONSISTENCY
    for tag, val in (("consistency OFF", 1e9), ("consistency 50%", 0.50)):
        EVAL_CONSISTENCY = val
        runs = [run_account(base, s, {"s_pre": 150., "s_post": 300.},
                            payout_at=6000.) for s in seqs]
        print(line(f"{tag}", summarize(runs)))
    EVAL_CONSISTENCY = keep

    print("\n=== 1b. SAME, uncapped payouts — COUNTERFACTUAL ONLY. The "
          "5-payout cap is VERIFIED-CURRENT; this block exists to show "
          "what the old B2 framing assumed. ===")
    for pol_name, pol in (("150->150", {"s_pre": 150., "s_post": 150.}),
                          ("150->300", {"s_pre": 150., "s_post": 300.})):
        for wtag, wat in (("wd@$4k", 4000.), ("wd@$6k", 6000.),
                          ("wd@$8k", 8000.)):
            runs = [run_account(base, s, pol, payout_cap=None, payout_at=wat)
                    for s in seqs]
            print(line(f"{pol_name} {wtag}", summarize(runs)))

    print("\n=== 3. CUSHION-PROPORTIONAL SIZING (fresh hypothesis) ===")
    print("  size = clip(k x cushion, s_min, s_max) post-lock; "
          "$150 flat pre-lock")
    for k, smin, smax in ((0.05, 75., 300.), (0.10, 75., 600.),
                          (0.15, 150., 600.), (0.05, 150., 300.)):
        pol = {"s_pre": 150., "mode": "cushion", "k": k,
               "s_min": smin, "s_max": smax}
        runs = [run_account(base, s, pol, payout_at=6000.) for s in seqs]
        print(line(f"k={k} [{smin:.0f},{smax:.0f}] wd@$6k",
                   summarize(runs)))
    print("  reference (flat post-lock, same withdrawal policy):")
    for tag, pol in (("150->150", {"s_pre": 150., "s_post": 150.}),
                     ("150->300", {"s_pre": 150., "s_post": 300.})):
        runs = [run_account(base, s, pol, payout_at=6000.) for s in seqs]
        print(line(f"{tag} wd@$6k", summarize(runs)))

    print("\n=== 3b. CUSHION SIZING, UNCAPPED (where net can actually move) ===")
    for k, smin, smax in ((0.05, 75., 300.), (0.10, 75., 600.),
                          (0.15, 150., 600.), (0.10, 150., 900.)):
        pol = {"s_pre": 150., "mode": "cushion", "k": k,
               "s_min": smin, "s_max": smax}
        runs = [run_account(base, s, pol, payout_cap=None, payout_at=6000.)
                for s in seqs]
        print(line(f"k={k} [{smin:.0f},{smax:.0f}] wd@$6k", summarize(runs)))
    print("  reference (flat post-lock, uncapped, wd@$6k):")
    for tag, pol in (("150->150", {"s_pre": 150., "s_post": 150.}),
                     ("150->300", {"s_pre": 150., "s_post": 300.}),
                     ("150->600", {"s_pre": 150., "s_post": 600.})):
        runs = [run_account(base, s, pol, payout_cap=None, payout_at=6000.)
                for s in seqs]
        print(line(f"{tag} wd@$6k", summarize(runs)))

    print("\n=== 5. HAIRCUT SENSITIVITY (best policies, fit / -20% / -40%) ===")
    for pol_name, pol, wat in (
            ("150->150 wd@$6k", {"s_pre": 150., "s_post": 150.}, 6000.),
            ("150->300 wd@$6k", {"s_pre": 150., "s_post": 300.}, 6000.),
            ("150->300 wd@$4k", {"s_pre": 150., "s_post": 300.}, 4000.)):
        for nm, arr in (("fit", base), ("-20%", hair20), ("-40%", hair40)):
            runs = [run_account(arr, s, pol, payout_at=wat) for s in seqs]
            print(line(f"{pol_name} [{nm}]", summarize(runs)))

    print("\n=== 5b. HAIRCUT, UNCAPPED (the extraction world) ===")
    for pol_name, pol, wat in (
            ("150->150 wd@$6k", {"s_pre": 150., "s_post": 150.}, 6000.),
            ("150->300 wd@$6k", {"s_pre": 150., "s_post": 300.}, 6000.),
            ("cushion k=.05 wd@$6k", {"s_pre": 150., "mode": "cushion",
                                      "k": 0.05, "s_min": 75.,
                                      "s_max": 300.}, 6000.)):
        for nm, arr in (("fit", base), ("-20%", hair20), ("-40%", hair40)):
            runs = [run_account(arr, s, pol, payout_cap=None, payout_at=wat)
                    for s in seqs]
            print(line(f"{pol_name} [{nm}]", summarize(runs)))


if __name__ == "__main__":
    main()
