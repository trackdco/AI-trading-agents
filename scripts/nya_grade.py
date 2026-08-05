#!/usr/bin/env python3
"""NYA-FA-01 — GRADING PACK on the frozen fail-branch spec (deep + G2 + S2,
target min(POC, 0.5w), TS 15:55). §6.0-compliant: DSR's denominator reads the
MERGED machine ledger (output/trial_ledger.parquet), not a hand count.

  DSR   day-level P&L over the full flow-span session universe ($160-risk
        sizing, zeros on flat days), deflated by the ledger's recorded trial
        count and effect variance.
  PBO   CSCV over the day-level series of ALL NINE searched gate x stop cells
        (trial 3's search — the procedure that produced the spec).
  MC    funded shell (50k start, $2k EOD trailing): spec alone, canon alone
        (same days), canon + spec paired.
  CORR  day-level Pearson/Spearman vs the canon (union + both-active),
        in-market minute overlap, shared input families vs the [PROPOSED]
        thresholds.

Writes output/nya_fa_grading.md and the emission-format book
output/emission_nya_fa_fit.parquet.

    python -m scripts.nya_grade
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.dsr import deflated_sharpe_ratio, min_track_record_length  # noqa: E402
from src.validation.pbo import pbo_cscv  # noqa: E402
from src.validation import trial_ledger as TL  # noqa: E402

SEED, N_SIMS, YEAR_DAYS = 7, 2_000, 252
START, TRAIL = 50_000.0, 2_000.0
RISK_DOLLARS, FR = 160.0, 1.0
FAMILIES = {"nya_fa": {"session-structure", "order-flow"},
            "ny_canon": {"depth-walls", "overnight-structure", "order-flow",
                         "vwap", "trigger-density", "structural-events"}}


def ruin(day_pl, rng, n_days):
    busts, nets = 0, []
    for _ in range(N_SIMS):
        path = day_pl[rng.integers(0, len(day_pl), n_days)]
        bal, line = START, START - TRAIL
        for p in path:
            bal += p
            if bal - line <= 0:
                busts += 1; break
            line = min(START, max(line, bal - TRAIL))
        nets.append(bal - START)
    return busts / N_SIMS, float(np.median(nets))


def main() -> None:
    rng = np.random.default_rng(SEED)
    L = []
    say = lambda s="": (print(s), L.append(s))

    E = pd.read_parquet(ROOT / "output/nya_fa_flow_events.parquet")
    E["deep"] = E.extw >= E.extw.median()
    spec = E[E.deep & E.g2].dropna(subset=["S2_halfext"]).copy()
    spec["pl"] = RISK_DOLLARS * (spec.S2_halfext - FR) / spec.S2_halfext_risk
    uni = pd.read_parquet(ROOT / "output/nya_fa_arm_matrix.parquet").index
    s_spec = spec.set_index("day").pl.reindex(uni).fillna(0.0)

    book = spec[["day", "half", "S2_halfext", "S2_halfext_risk", "pl"]].rename(
        columns={"S2_halfext": "net_pts", "S2_halfext_risk": "risk_pts"})
    book.insert(0, "strategy", "nya_fa")
    book.to_parquet(ROOT / "output/emission_nya_fa_fit.parquet", index=False)

    canon = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet")
    canon = canon[canon.day.isin(set(uni))]
    s_canon = canon.groupby("day").pl.sum().reindex(uni).fillna(0.0)

    say("# NYA-FA-01 grading pack — frozen fail-branch spec")
    say("")
    say(f"Book: n={len(spec)} trades, {uni.min()}..{uni.max()} "
        f"({len(uni)} sessions), ${spec.pl.sum():+,.0f} at $160-risk.")
    say("")

    say("## DSR (denominator from the merged machine ledger, §6.0)")
    n_led = TL.n_trials()
    var_led = TL.trial_effect_variance()
    r = s_spec.to_numpy(float)
    d = deflated_sharpe_ratio(r, n_trials=n_led, trial_sr_var=var_led)
    say(f"  ledger: {n_led} trials, effect var {var_led:.4f}")
    say(f"  daily SR {d.sr:+.4f} | SR0 {d.sr0:+.4f} | PSR(0) {d.psr_zero:.3f} | "
        f"DSR {d.dsr:.3f} {'PASS>=.95' if d.significant else '(below .95)'}")
    say(f"  min track vs zero: {min_track_record_length(r):.0f} days (have {len(r)})")
    say("")

    say("## PBO (CSCV over the 9 searched gate x stop cells)")
    cells = {}
    for gname in ("g1", "g2", "g3"):
        for sname in ("S1_extreme", "S2_halfext", "S3_25pt"):
            g = E[E[gname]].dropna(subset=[sname])
            pl = RISK_DOLLARS * (g[sname] - FR) / g[sname + "_risk"]
            cells[f"{gname}x{sname}"] = pl.groupby(g.day).sum()
    M = pd.DataFrame({k: v.reindex(uni).fillna(0.0) for k, v in cells.items()})
    M = M.loc[:, M.std() > 0]
    p = pbo_cscv(M, n_blocks=16)
    say(f"  PBO {p.pbo:.2f} over {p.n_combinations} splits ({p.n_trials} cells, "
        f"{p.n_obs_used} days) — {'OVERFIT >= .50' if p.overfit else 'selection beats noise'}; "
        f"IS->OOS slope {p.slope:+.2f}, P(OOS loss) {p.prob_oos_loss:.2f}")
    say("")

    say("## Funded-shell MC (comparative)")
    for label, s in (("spec alone", s_spec), ("canon alone (same days)", s_canon),
                     ("canon + spec (paired)", s_canon + s_spec)):
        pb, med = ruin(s.to_numpy(float), rng, YEAR_DAYS)
        say(f"  {label:26s} 12mo P(bust) {pb:.1%}  median ${med:+,.0f}")
    say("")

    say("## Correlation battery vs canon")
    act_a, act_b = s_spec != 0, s_canon != 0
    both = act_a & act_b
    xu, yu = s_spec.to_numpy(float), s_canon.to_numpy(float)
    pe = float(np.corrcoef(xu, yu)[0, 1])
    sp = float(pd.Series(xu).rank().corr(pd.Series(yu).rank()))
    say(f"  active {int(act_a.sum())}/{int(act_b.sum())} days, both-active {int(both.sum())}")
    say(f"  union Pearson {pe:+.3f} Spearman {sp:+.3f}")
    if both.sum() >= 3:
        xi, yi = s_spec[both].to_numpy(float), s_canon[both].to_numpy(float)
        say(f"  both-active Pearson {float(np.corrcoef(xi, yi)[0,1]):+.3f} "
            f"(n={int(both.sum())} — below T3's 60-day trust bar: structural rules govern)")
    shared = FAMILIES["nya_fa"] & FAMILIES["ny_canon"]
    say(f"  T5 shared families {len(shared)}/3 ({', '.join(sorted(shared))}): "
        f"{'VETO' if len(shared) >= 3 else 'no veto'}")

    (ROOT / "output/nya_fa_grading.md").write_text("\n".join(L) + "\n")
    print("\nwrote output/nya_fa_grading.md")


if __name__ == "__main__":
    main()
