#!/usr/bin/env python3
"""LDN-FLOW-01 — does order-flow confirmation at entry separate winners from losers?

Exactly as declared in docs/PREREG-london-flow-confirmation.md (16:06:09Z). Four flow
measures, all predicted POSITIVE, tested threshold-free by Spearman rank correlation and
AUC against the event outcome. Fragility ladder runs first.

Every flow minute read lies in [t-L+1, t] — at or before the entry minute. The outcome is
measured over (t, window close]. The two intervals never overlap; asserted at runtime.

SEALED-SPAN GUARD: inherited from fit_only(). 2023/24 dropped. No holdout look.

    python -m scripts.ldn_flow01_test
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_flow01_events import events

NY = "America/New_York"
PHI = NormalDist()
TICK = 0.25
L_PRIMARY = 5
L_LADDER = (3, 5, 10)
MIN_N = 30
MEASURES = ("CONFIRM", "ABSORB", "EFFORT", "TRAPPED")
ERAS = ("2025", "2026")


# ----------------------------------------------------------------- flow assembly
def minute_frame() -> pd.DataFrame:
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp.index = pd.to_datetime(fp.index)
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars = bars.set_index("ts")[["high", "low"]]
    return fp[["vol", "delta"]].join(bars, how="inner").sort_index()


def measure(ev: pd.DataFrame, mf: pd.DataFrame, L: int) -> pd.DataFrame:
    """The four declared measures. Reads only minutes in [t-L+1, t]."""
    idx = mf.index
    pos = pd.Series(np.arange(len(idx)), index=idx)
    out = []
    for r in ev.itertuples():
        if r.ts_entry not in pos.index or r.ts_push_start not in pos.index:
            continue
        j = int(pos.loc[r.ts_entry])
        win = mf.iloc[max(0, j - L + 1): j + 1]
        if len(win) < L:
            continue
        assert win.index.max() <= r.ts_entry, "causality: flow window ran past t"
        d = r.direction
        vol_sum = float(win.vol.sum())
        rng_ticks = float(win.high.max() - win.low.min()) / TICK
        push_delta = float(mf.delta.iloc[int(pos.loc[r.ts_push_start])])
        mean_vol = vol_sum / L
        out.append({
            "day": r.day, "era": r.era, "cand": r.cand, "signed_ret": r.signed_ret,
            "CONFIRM": float(mf.delta.iloc[j]) * d,
            "ABSORB": float(win.delta.sum()) * d,
            "EFFORT": vol_sum / (rng_ticks + 1.0),
            "TRAPPED": -push_delta * d / (mean_vol + 1.0),
        })
    d = pd.DataFrame(out)
    # outcome standardised within candidate x era, per prereg §6
    d["z"] = d.groupby(["cand", "era"]).signed_ret.transform(
        lambda s: (s - s.mean()) / s.std(ddof=1))
    return d


# ----------------------------------------------------------------- statistics
def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def rho_ci_p(rho: float, n: int) -> tuple[float, float, float]:
    """Fisher-z CI and ONE-SIDED p in the declared (positive) direction."""
    if n < 6 or not np.isfinite(rho) or abs(rho) >= 1:
        return float("nan"), float("nan"), float("nan")
    z, se = np.arctanh(rho), 1.0 / np.sqrt(n - 3)
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    return float(lo), float(hi), float(1.0 - PHI.cdf(z / se))


def auc(measure_vals: np.ndarray, outcome: np.ndarray) -> float:
    """P(measure higher on a winner than on a loser). 0.5 = no separation."""
    w = outcome > 0
    n1, n2 = int(w.sum()), int((~w).sum())
    if not n1 or not n2:
        return float("nan")
    ranks = pd.Series(measure_vals).rank().to_numpy()
    return float((ranks[w].sum() - n1 * (n1 + 1) / 2) / (n1 * n2))


def min_detectable_rho(n: int) -> float:
    return float(np.tanh((PHI.inv_cdf(0.95) + PHI.inv_cdf(0.80)) / np.sqrt(n - 3)))


def holm(pvals: dict[str, float]) -> dict[str, bool]:
    """Holm-Bonferroni at family alpha 0.05, declared in prereg §8."""
    order = sorted(pvals, key=lambda k: pvals[k])
    out, m = {}, len(order)
    for i, k in enumerate(order):
        thresh = 0.05 / (m - i)
        prev_ok = all(out[o] for o in order[:i]) if i else True
        out[k] = bool(prev_ok and np.isfinite(pvals[k]) and pvals[k] <= thresh)
    return out


# ----------------------------------------------------------------- report
def main() -> None:
    ev = events()
    mf = minute_frame()
    flow_lo, flow_hi = mf.index.min(), mf.index.max()
    print(f"\nflow span: {flow_lo:%Y-%m-%d} -> {flow_hi:%Y-%m-%d}  "
          f"({len(mf)} minutes)")

    d = measure(ev, mf, L_PRIMARY)
    print(f"\nevents before flow-span restriction: {len(ev)}   after: {len(d)}")
    print(f"{'':<10}{'2025':>18}{'2026':>18}")
    for cand in ("trap", "vwap"):
        cells = [f"{int(((d.cand == cand) & (d.era == e)).sum())}"
                 f" / {int((ev.cand == cand).sum() and ((ev.cand == cand) & (ev.era == e)).sum())}"
                 for e in ERAS]
        print(f"  {cand:<8}{cells[0]:>18}{cells[1]:>18}   (kept / all)")
    for e in ERAS:
        n = int((d.era == e).sum())
        print(f"  pooled {e}: n={n}"
              f"{'' if n >= MIN_N else '   BELOW n>=30'}")

    # ---------------- FRAGILITY FIRST ----------------
    print("\n" + "=" * 88)
    print("FRAGILITY LADDER (prereg §7) — runs BEFORE the primary is read")
    print("=" * 88)
    dead = []
    for m in MEASURES:
        print(f"\n  {m}")
        for era in ERAS:
            s = d[d.era == era]
            full = spearman(s[m].to_numpy(float), s.z.to_numpy(float))
            parts = [f"full {full:+.3f}"]
            o = s.z.abs().sort_values().index
            for k in (1, 3, 5, 10):
                t = s.loc[o[:-k]]
                r = spearman(t[m].to_numpy(float), t.z.to_numpy(float))
                parts.append(f"drop{k} {r:+.3f}")
                if k <= 3 and np.isfinite(r) and np.sign(r) != np.sign(full):
                    dead.append(f"{m}/{era}@drop{k}")
            print(f"    {era} trim : " + " | ".join(parts))
        for era in ERAS:
            parts = []
            for L in L_LADDER:
                dl = measure(ev, mf, L)
                sl = dl[dl.era == era]
                parts.append(f"L={L} {spearman(sl[m].to_numpy(float), sl.z.to_numpy(float)):+.3f}")
            rs = [float(p.split()[-1]) for p in parts]
            if len({np.sign(r) for r in rs if r != 0}) > 1:
                dead.append(f"{m}/{era}@L-ladder")
            print(f"    {era} L    : " + " | ".join(parts))
    print(f"\n  FRAGILITY: {'FIRES -> ' + ', '.join(dead) if dead else 'CLEAR'}")

    # ---------------- PRIMARY ----------------
    print("\n" + "=" * 88)
    print(f"PRIMARY — Spearman rho vs outcome (L={L_PRIMARY}). All four declared POSITIVE.")
    print("=" * 88)
    print(f"{'measure':<9}{'era':<6}{'n':>5}{'rho':>8}{'95% CI':>18}"
          f"{'p1':>8}{'AUC':>8}   read")
    print("-" * 88)
    pvals = {}
    rho_by = {}
    for m in MEASURES:
        for era in ERAS:
            s = d[d.era == era]
            x, y = s[m].to_numpy(float), s.z.to_numpy(float)
            r = spearman(x, y)
            lo, hi, p = rho_ci_p(r, len(s))
            a = auc(x, s.signed_ret.to_numpy(float))
            rho_by[(m, era)] = (r, lo, hi, p, a, len(s))
            if era == "2026":
                pvals[m] = p
            read = ("declared sign" if r > 0 else "WRONG SIGN")
            print(f"{m:<9}{era:<6}{len(s):>5}{r:>+8.3f}"
                  f"{f'[{lo:+.3f}, {hi:+.3f}]':>18}{p:>8.3f}{a:>8.3f}   {read}")

    print(f"\nminimum detectable rho @80% power, one-sided: "
          + ", ".join(f"{e} (n={int((d.era == e).sum())}) {min_detectable_rho(int((d.era == e).sum())):.3f}"
                      for e in ERAS))

    hb = holm(pvals)
    print(f"\nHolm-Bonferroni across the four (family alpha 0.05, declared in advance): "
          f"{'survivors: ' + ', '.join(k for k, v in hb.items() if v) if any(hb.values()) else 'NO measure survives'}")

    # ---------------- MEDIAN SPLIT (readability, no new trial) ----------------
    print("\n" + "=" * 88)
    print("MEDIAN SPLIT — 'would filtering on this remove losers?' (no threshold searched)")
    print("=" * 88)
    print(f"{'measure':<9}{'era':<6}{'half':<8}{'n':>5}{'mean pts':>11}{'win rate':>11}")
    print("-" * 88)
    for m in MEASURES:
        for era in ERAS:
            s = d[d.era == era]
            med = s[m].median()
            for lab, sel in (("high", s[s[m] > med]), ("low", s[s[m] <= med])):
                if not len(sel):
                    continue
                print(f"{m:<9}{era:<6}{lab:<8}{len(sel):>5}"
                      f"{sel.signed_ret.mean():>+11.2f}"
                      f"{100 * (sel.signed_ret > 0).mean():>10.1f}%")

    # ---------------- VERDICT ----------------
    print("\n" + "=" * 88)
    verdicts = {}
    for m in MEASURES:
        r25, _, _, p25, _, n25 = rho_by[(m, "2025")]
        r26, lo26, hi26, p26, _, n26 = rho_by[(m, "2026")]
        if any(k.startswith(m) for k in dead):
            v = "FAIL (fragility)"
        elif (p25 <= 0.05 and p26 <= 0.05 and r25 > 0 and r26 > 0
              and min(n25, n26) >= MIN_N and hb.get(m, False)):
            v = "PASS"
        elif (not (lo26 <= r25 <= hi26)) and (lo26 <= 0 <= hi26):
            v = "FAIL"
        else:
            v = "INCONCLUSIVE ON POWER"
        verdicts[m] = v
        print(f"VERDICT {m:<9} {v}")
    print("=" * 88)

    # ---------------- PER-CANDIDATE COMPANION (descriptive) ----------------
    print("\nPER-CANDIDATE COMPANION (descriptive, not verdict-eligible)")
    print(f"{'measure':<9}{'cand':<7}{'era':<6}{'n':>5}{'rho':>8}")
    for m in MEASURES:
        for cand in ("trap", "vwap"):
            for era in ERAS:
                s = d[(d.cand == cand) & (d.era == era)]
                if len(s) < 10:
                    continue
                print(f"{m:<9}{cand:<7}{era:<6}{len(s):>5}"
                      f"{spearman(s[m].to_numpy(float), s.z.to_numpy(float)):>+8.3f}")


if __name__ == "__main__":
    main()
