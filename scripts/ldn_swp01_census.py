#!/usr/bin/env python3
"""LDN-SWP-01 — the Asia-sweep pair census, exactly as declared in
docs/PREREG-london-asia-sweep-pair.md.

THE QUESTION (one census, both candidates): does the TIMING of an Asian-range sweep
predict the direction of the subsequent London move?

    group D   Asia extreme breached 00:00-03:00 ET (the dead hour, before deep liquidity)
    group P   Asia extreme breached ONLY after the 03:00 open, into live liquidity
    outcome   03:00->06:00 ET point return, SIGNED by sweep direction
              (+1 swept high, -1 swept low) => positive means "continued"
    primary   delta = mean signed_ret(D) - mean signed_ret(P), Welch two-sided

Continuation thesis => signed_ret(D) > 0. Reversal thesis => signed_ret(P) < 0.
A null on delta kills BOTH candidates on one run.

FRAGILITY GATE RUNS FIRST (prereg §6): sign flip of delta at any trim depth <=3 in
either era kills the family regardless of everything else. This is bar-independent —
it needs no ratified threshold — so a FAIL here is final.

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_swp01_census
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only

NY = "America/New_York"
PHI = NormalDist()
OPEN_M, CLOSE_M = 180, 360        # 03:00 and 06:00 ET, minutes of day
MIN_N_GROUP = 30                  # §2.2 proposed floor, per group per era


def session_frame() -> pd.DataFrame:
    """Per day: the 03:00->06:00 return, plus the post-open extremes needed for group P."""
    b = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b = b.assign(day=ts.dt.strftime("%Y-%m-%d"), mod=ts.dt.hour * 60 + ts.dt.minute)
    w = b[b["mod"].between(OPEN_M, CLOSE_M)]
    piv = w.pivot_table(index="day", columns="mod", values="close", aggfunc="last")
    lo = piv.reindex(columns=range(OPEN_M, OPEN_M + 6)).bfill(axis=1).iloc[:, 0]
    hi = piv.reindex(columns=range(CLOSE_M - 5, CLOSE_M + 1)).ffill(axis=1).iloc[:, -1]
    agg = w.groupby("day").agg(post_hi=("high", "max"), post_lo=("low", "min"))
    return agg.assign(ret_0300_0600=hi - lo).reset_index()


def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Welch two-sample: (difference, se, two-sided p)."""
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    diff = float(a.mean() - b.mean())
    z = diff / se if se > 0 else float("nan")
    return diff, se, 2 * (1 - PHI.cdf(abs(z)))


def build() -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    d = sub.merge(session_frame(), on="day", how="inner")
    d["era"] = pd.to_datetime(d.day).dt.year.astype(str)
    n0 = len(d)

    # ---- exclusions, all declared in the prereg
    excl = {}
    excl["dst_mismatch"] = int(d.dst_mismatch.sum())
    d = d[~d.dst_mismatch]
    excl["sweep_both"] = int((d.sweep_side_dead == "both").sum())
    d = d[d.sweep_side_dead != "both"]
    excl["missing_outcome"] = int(d.ret_0300_0600.isna().sum())
    d = d.dropna(subset=["ret_0300_0600", "asia_hi", "asia_lo"])

    # ---- group + direction
    dead = d.sweep_side_dead.isin(["high", "low"])
    hi_br = d.post_hi > d.asia_hi
    lo_br = d.post_lo < d.asia_lo
    post_only = (~dead) & (hi_br ^ lo_br)          # XOR: exactly one side, direction defined
    excl["post_both_sides"] = int(((~dead) & hi_br & lo_br).sum())

    d = d.assign(
        group=np.where(dead, "D", np.where(post_only, "P", "")),
        direction=np.where(d.sweep_side_dead == "high", 1.0,
                           np.where(d.sweep_side_dead == "low", -1.0,
                                    np.where(hi_br, 1.0, -1.0))))
    d = d[d.group != ""].copy()
    d["signed_ret"] = d.ret_0300_0600 * d.direction
    d.attrs["excl"] = excl
    d.attrs["n_start"] = n0
    return d


def delta_for(frame: pd.DataFrame) -> float:
    a = frame[frame.group == "D"].signed_ret.to_numpy(float)
    b = frame[frame.group == "P"].signed_ret.to_numpy(float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    return float(a.mean() - b.mean())


def main() -> None:
    d = build()
    print(f"days in (2025/2026, sealed guard applied): {d.attrs['n_start']}")
    print(f"exclusions: {d.attrs['excl']}")
    print(f"events after grouping: {len(d)}\n")
    print(f"{'era':>6} {'n(D)':>6} {'n(P)':>6} {'mean D':>9} {'mean P':>9} {'delta':>9}")
    for era in ("2025", "2026"):
        e = d[d.era == era]
        a, b = e[e.group == "D"].signed_ret, e[e.group == "P"].signed_ret
        print(f"{era:>6} {len(a):>6} {len(b):>6} {a.mean():>+9.2f} {b.mean():>+9.2f} "
              f"{a.mean() - b.mean():>+9.2f}")

    # ================= FRAGILITY GATE — FIRST, per prereg §6 =================
    print("\n" + "=" * 84)
    print("FRAGILITY GATE (prereg §6) — runs BEFORE the primary result is read")
    print("=" * 84)
    fired = []
    for era in ("2025", "2026"):
        e = d[d.era == era]
        full = delta_for(e)
        order = e.signed_ret.abs().sort_values().index
        row = [f"full {full:+.2f}"]
        for k in (1, 3, 5, 10):
            t = delta_for(e.loc[order].iloc[:-k])
            row.append(f"drop{k} {t:+.2f}")
            if k <= 3 and np.isfinite(t) and np.sign(t) != np.sign(full):
                fired.append(f"{era}@drop{k}")
        w = e.copy()
        q1, q99 = w.signed_ret.quantile([.01, .99])
        w["signed_ret"] = w.signed_ret.clip(q1, q99)
        row.append(f"wins1/99 {delta_for(w):+.2f}")
        print(f"  {era}: " + " | ".join(row))
    print(f"\n  GATE {'FIRES — family dead regardless of everything below' if fired else 'CLEAR'}"
          f"{' (' + ', '.join(fired) + ')' if fired else ''}")

    # ================= PRIMARY =================
    print("\n" + "=" * 84)
    print("PRIMARY — delta = mean signed_ret(D) - mean signed_ret(P), Welch two-sided")
    print("=" * 84)
    res = {}
    for era in ("2025", "2026"):
        e = d[d.era == era]
        a = e[e.group == "D"].signed_ret.to_numpy(float)
        b = e[e.group == "P"].signed_ret.to_numpy(float)
        diff, se, p = welch(a, b)
        res[era] = (diff, se, p, len(a), len(b))
        floor = "ok" if min(len(a), len(b)) >= MIN_N_GROUP else f"BELOW n>={MIN_N_GROUP}"
        print(f"  {era}: delta {diff:>+8.2f}  se {se:>7.2f}  p {p:.3f}  "
              f"n {len(a)}/{len(b)} ({floor})")
        print(f"         D mean {a.mean():+.2f} (continuation reads >0) | "
              f"P mean {b.mean():+.2f} (reversal reads <0)")

    d25, _se25, p25, _, _ = res["2025"]
    d26, se26, p26, na26, nb26 = res["2026"]
    lo, hi = d26 - 1.96 * se26, d26 + 1.96 * se26
    print(f"\n  2026 95% CI on delta: [{lo:+.2f}, {hi:+.2f}]")
    print(f"  excludes 2025 estimate ({d25:+.2f})? {'YES' if not (lo <= d25 <= hi) else 'no'}")
    print(f"  contains 0?                          {'YES' if lo <= 0 <= hi else 'no'}")

    # ================= VERDICT (declared three-way + fragility override) ==========
    npass = (p25 <= 0.05 and p26 <= 0.05 and d25 > 0 and d26 > 0
             and min(res['2025'][3], res['2025'][4], na26, nb26) >= MIN_N_GROUP)
    excl_d25 = not (lo <= d25 <= hi)
    fail = excl_d25 and (lo <= 0 <= hi or d26 < 0)
    verdict = ("FAIL (fragility override)" if fired
               else "PASS" if npass else "FAIL" if fail else "INCONCLUSIVE ON POWER")
    print("\n" + "=" * 84)
    print(f"VERDICT: {verdict}")
    print("=" * 84)

    # ================= SECONDARY — narrow Asia, one pre-specified subset =========
    print("\nSECONDARY (declared): narrow Asia, asia_rng_pctl20 <= 0.2")
    for era in ("2025", "2026"):
        e = d[(d.era == era) & (d.asia_rng_pctl20 <= 0.2)]
        a = e[e.group == "D"].signed_ret.to_numpy(float)
        b = e[e.group == "P"].signed_ret.to_numpy(float)
        if len(a) < 2 or len(b) < 2:
            print(f"  {era}: n too small (D={len(a)}, P={len(b)})")
            continue
        diff, se, p = welch(a, b)
        print(f"  {era}: delta {diff:>+8.2f}  p {p:.3f}  n {len(a)}/{len(b)}  "
              f"(D {a.mean():+.2f} / P {b.mean():+.2f})")

    # ================= POWER (mandatory) =================
    print("\nPOWER (mandatory per prereg)")
    for era, (diff, se, p, na, nb) in res.items():
        mde = (PHI.inv_cdf(0.975) + PHI.inv_cdf(0.80)) * se
        pw = 1 - PHI.cdf(PHI.inv_cdf(0.975) - abs(d25) / se)
        print(f"  {era}: se {se:.2f}  min detectable |delta| @80% = {mde:.2f}  "
              f"power to see the 2025 effect = {pw * 100:.0f}%")

    # ================= dst_mismatch subset, reported never pooled ================
    print(f"\n(dst_mismatch days excluded from all of the above: "
          f"{d.attrs['excl']['dst_mismatch']} — reported separately by design)")


if __name__ == "__main__":
    main()
