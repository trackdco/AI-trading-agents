#!/usr/bin/env python3
"""LDN-DEF-01 — level-defense-flow, exactly as declared in
docs/PREREG-london-level-defense-flow.md (16:49:59Z).

Substrate: the LDN-TRAP-01 event set, rebuilt verbatim WITH the level price, asserted to
reproduce the published verdict (161/-2.30, 89/-2.64) before anything runs.

Three absorption measures read from per-(minute, price, aggressor side) footprint over
[t-3, t] within 2 ticks of the defended level, all declared POSITIVE. Threshold-free
primary: Spearman rho + AUC. Fragility ladder first.

SEALED-SPAN GUARD: 2023/24 dropped via fit_only(); holdout footprint files excluded by
name AND asserted absent from the loaded file list. No holdout look.

    python -m scripts.ldn_def01_census
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_flow01_test import auc, holm, min_detectable_rho, rho_ci_p, spearman
from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
TICK = 0.25
BREAK_TICKS, RECLAIM_MIN = 4, 15        # LDN-TRAP-01, declared there
WIN_PRIMARY, WIN_LADDER = 3, (2, 3, 5)  # minutes before t
PROX_PRIMARY, PROX_LADDER = 2, (1, 2, 4)  # ticks from the level
MEASURES = ("ABSORB", "PIN", "ICEBERG")
ERAS = ("2025", "2026")
MIN_N = 30
PUBLISHED = {"2025": (161, -2.30), "2026": (89, -2.64)}


# ------------------------------------------------------------------ events
def trap_events() -> pd.DataFrame:
    """LDN-TRAP-01 verbatim, plus level price and entry timestamp."""
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    prev = {d: days[i - 1] for i, d in enumerate(days) if i}

    rows = []
    for r in sub.itertuples():
        g, pg = by_day.get(r.day), by_day.get(prev.get(r.day, ""))
        if g is None or pg is None:
            continue
        start, end = london_window_et(r.day)
        on = pd.concat([pg[pg.ts >= pg.ts.dt.normalize() + pd.Timedelta(hours=18)],
                        g[g.ts < start]])
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30 or not len(on):
            continue
        levels = [("ONH", float(on.high.max()), +1), ("ONL", float(on.low.min()), -1),
                  ("PDH", r.prior_rth_hi, +1), ("PDL", r.prior_rth_lo, -1)]
        best = None
        for name, lvl, side in levels:
            if lvl is None or pd.isna(lvl):
                continue
            buf = BREAK_TICKS * TICK
            brk = w.index[(w.high > lvl + buf) if side > 0 else (w.low < lvl - buf)]
            if not len(brk):
                continue
            b = int(brk[0])
            seg = w.iloc[b: b + RECLAIM_MIN + 1]
            back = seg.index[(seg.close < lvl) if side > 0 else (seg.close > lvl)]
            if not len(back):
                continue
            t = int(back[0])
            if best is None or t < best["t"]:
                # excursion beyond the level over the break-to-reclaim leg
                exc = (float(w.high.iloc[b:t + 1].max() - lvl) if side > 0
                       else float(lvl - w.low.iloc[b:t + 1].min()))
                best = {"day": r.day, "era": r.day[:4], "level_px": float(lvl),
                        "side": side, "t": t, "ts_entry": w.ts.iloc[t],
                        "excursion_ticks": max(0.0, exc) / TICK,
                        "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * (-side)}
        if best:
            best.pop("t")
            rows.append(best)
    d = pd.DataFrame(rows)
    for era, (n_exp, m_exp) in PUBLISHED.items():
        s = d[d.era == era].signed_ret
        assert len(s) == n_exp, f"{era}: n {len(s)} != published {n_exp}"
        assert abs(s.mean() - m_exp) < 0.005, f"{era}: mean {s.mean():.4f} != {m_exp}"
    print("VERIFIED — trap event set matches the published LDN-TRAP-01 verdict.")
    return d


# ------------------------------------------------------------------ footprint
def footprint() -> pd.DataFrame:
    fs = sorted(glob.glob(str(ROOT / "data/reference/cvd/footprint_*.parquet")))
    keep = [f for f in fs if "holdout" not in f]
    assert not any("holdout" in f for f in keep), "SEALED-SPAN VIOLATION"
    print(f"footprint files loaded: {len(keep)} (holdout excluded: {len(fs) - len(keep)})")
    d = pd.concat([pd.read_parquet(f) for f in keep], ignore_index=True)
    d["ts"] = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
    return d


def measure(ev: pd.DataFrame, fp: pd.DataFrame, win: int, prox: int) -> pd.DataFrame:
    """Absorption at the level over [t-win, t], within prox ticks. Reads nothing after t."""
    band = prox * TICK
    out = []
    by_min = {k: v for k, v in fp.groupby("ts", sort=False)}
    # session median per-minute volume, from minutes at or before t only
    vol_by_min = fp.groupby("ts", sort=False).volume.sum()
    for r in ev.itertuples():
        t = r.ts_entry
        mins = [t - pd.Timedelta(minutes=k) for k in range(win, -1, -1)]
        assert max(mins) <= t, "causality: window ran past t"
        chunks = [by_min[m] for m in mins if m in by_min]
        if not chunks:
            continue
        c = pd.concat(chunks)
        near = c[(c.price >= r.level_px - band) & (c.price <= r.level_px + band)]
        # absorbed aggressors: buyers on an upside break, sellers on a downside break
        want = "B" if r.side > 0 else "A"
        absorbed = near[near.side == want]
        day_start = t.normalize()
        med = float(vol_by_min[(vol_by_min.index >= day_start)
                               & (vol_by_min.index <= t)].median() or 1.0)
        med = med if med > 0 else 1.0
        vol = float(absorbed.volume.sum())
        peak = float(absorbed.groupby("price").volume.sum().max()) if len(absorbed) else 0.0
        out.append({"day": r.day, "era": r.era, "signed_ret": r.signed_ret,
                    "ABSORB": vol / med,
                    "PIN": vol / (r.excursion_ticks + 1.0),
                    "ICEBERG": peak / med})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ report
def main() -> None:
    ev = trap_events()
    fp = footprint()
    lo, hi = fp.ts.min(), fp.ts.max()
    ev = ev[(ev.ts_entry >= lo) & (ev.ts_entry <= hi)]
    print(f"footprint span {lo:%Y-%m-%d} -> {hi:%Y-%m-%d}")

    d = measure(ev, fp, WIN_PRIMARY, PROX_PRIMARY)
    print(f"\nevents in footprint span: {len(d)}  "
          f"{', '.join(f'{e}: {int((d.era == e).sum())}' for e in ERAS)}")
    for e in ERAS:
        n = int((d.era == e).sum())
        if n < MIN_N:
            print(f"  WARNING {e}: n={n} BELOW n>=30")

    print("\n" + "=" * 88)
    print("FRAGILITY LADDER (prereg §6) — runs BEFORE the primary is read")
    print("=" * 88)
    dead = []
    cache = {(WIN_PRIMARY, PROX_PRIMARY): d}
    for w_, p_ in [(w, PROX_PRIMARY) for w in WIN_LADDER] + \
                  [(WIN_PRIMARY, p) for p in PROX_LADDER]:
        if (w_, p_) not in cache:
            cache[(w_, p_)] = measure(ev, fp, w_, p_)
    for m in MEASURES:
        print(f"\n  {m}")
        for era in ERAS:
            s = d[d.era == era]
            full = spearman(s[m].to_numpy(float), s.signed_ret.to_numpy(float))
            parts = [f"full {full:+.3f}"]
            o = s.signed_ret.abs().sort_values().index
            for k in (1, 3, 5, 10):
                tt = s.loc[o[:-k]]
                r = spearman(tt[m].to_numpy(float), tt.signed_ret.to_numpy(float))
                parts.append(f"drop{k} {r:+.3f}")
                if k <= 3 and np.isfinite(r) and np.sign(r) != np.sign(full):
                    dead.append(f"{m}/{era}@drop{k}")
            print(f"    {era} trim : " + " | ".join(parts))
        for label, keys in (("win ", [(w, PROX_PRIMARY) for w in WIN_LADDER]),
                            ("prox", [(WIN_PRIMARY, p) for p in PROX_LADDER])):
            for era in ERAS:
                vals, parts = [], []
                for k in keys:
                    sl = cache[k][cache[k].era == era]
                    r = spearman(sl[m].to_numpy(float), sl.signed_ret.to_numpy(float))
                    vals.append(np.sign(r))
                    parts.append(f"{k[0] if label == 'win ' else k[1]}:{r:+.3f}")
                if len({v for v in vals if v != 0}) > 1:
                    dead.append(f"{m}/{era}@{label.strip()}-ladder")
                print(f"    {era} {label}: " + " | ".join(parts))
    print(f"\n  FRAGILITY: {'FIRES -> ' + ', '.join(sorted(set(dead))) if dead else 'CLEAR'}")

    print("\n" + "=" * 88)
    print("PRIMARY — Spearman rho vs outcome. All three declared POSITIVE.")
    print("=" * 88)
    print(f"{'measure':<9}{'era':<6}{'n':>5}{'rho':>8}{'95% CI':>18}{'p1':>8}{'AUC':>8}   read")
    print("-" * 88)
    pvals, rho_by = {}, {}
    for m in MEASURES:
        for era in ERAS:
            s = d[d.era == era]
            x, y = s[m].to_numpy(float), s.signed_ret.to_numpy(float)
            r = spearman(x, y)
            clo, chi, p = rho_ci_p(r, len(s))
            a = auc(x, y)
            rho_by[(m, era)] = (r, clo, chi, p, a, len(s))
            if era == "2026":
                pvals[m] = p
            print(f"{m:<9}{era:<6}{len(s):>5}{r:>+8.3f}"
                  f"{f'[{clo:+.3f}, {chi:+.3f}]':>18}{p:>8.3f}{a:>8.3f}   "
                  f"{'declared sign' if r > 0 else 'WRONG SIGN'}")

    print("\nminimum detectable rho @80%: " + ", ".join(
        f"{e} (n={int((d.era == e).sum())}) {min_detectable_rho(int((d.era == e).sum())):.3f}"
        for e in ERAS))
    hb = holm(pvals)
    print(f"Holm-Bonferroni across the three: "
          f"{'survivors: ' + ', '.join(k for k, v in hb.items() if v) if any(hb.values()) else 'NO measure survives'}")

    print("\n" + "=" * 88)
    print("MEDIAN SPLIT — does high absorption remove losers? (no threshold searched)")
    print("=" * 88)
    print(f"{'measure':<9}{'era':<6}{'half':<7}{'n':>5}{'mean pts':>11}{'win rate':>11}")
    print("-" * 88)
    for m in MEASURES:
        for era in ERAS:
            s = d[d.era == era]
            med = s[m].median()
            for lab, sel in (("high", s[s[m] > med]), ("low", s[s[m] <= med])):
                if not len(sel):
                    continue
                print(f"{m:<9}{era:<6}{lab:<7}{len(sel):>5}"
                      f"{sel.signed_ret.mean():>+11.2f}"
                      f"{100 * (sel.signed_ret > 0).mean():>10.1f}%")

    print("\n" + "=" * 88)
    for m in MEASURES:
        r25, _, _, p25, _, n25 = rho_by[(m, "2025")]
        r26, l26, h26, p26, _, n26 = rho_by[(m, "2026")]
        if any(k.startswith(m) for k in dead):
            v = "FAIL (fragility)"
        elif (p25 <= 0.05 and p26 <= 0.05 and r25 > 0 and r26 > 0
              and min(n25, n26) >= MIN_N and hb.get(m, False)):
            v = "PASS"
        elif (not (l26 <= r25 <= h26)) and (l26 <= 0 <= h26):
            v = "FAIL"
        else:
            v = "INCONCLUSIVE ON POWER"
        print(f"VERDICT {m:<9} {v}")
    print("=" * 88)


if __name__ == "__main__":
    main()
