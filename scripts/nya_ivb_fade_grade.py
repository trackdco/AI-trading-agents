#!/usr/bin/env python3
"""NYA-IVB-01 branch B — trials 7-8: exit/stop tournament (§6.0) + grading
pack + canon correlation, in one pass.

Tournament (default declared in PREREG-fab-ivb promotion rule BEFORE this
run: fade completed-IB extreme touch toward IB mid, stop 0.25xIB beyond, no
BE): challengers C1 BE at halfway-to-mid; C2 full-traverse target (far
extreme); C3 tight stop 0.15xIB; C4 IB length 15 min; C5 IB length 60 min.
PBO (CSCV) over the day-level arm matrix judges the selection; a challenger
displaces the default only per §6.0 (PBO < 0.5 AND holdout) — never rank.

Grading: DSR on the full-span day series at $160-risk (denominator = merged
machine ledger per §6.0), PSR(0) vs the §5.9.5 sleeve floor 0.75, funded MC,
day-level correlation + in-market-minute overlap vs the canon (gold-leg
clock overlap is the known risk).

    python -m scripts.nya_ivb_fade_grade
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

FR, RISK = 1.0, 160.0
SEED, N_SIMS, YEAR_DAYS, START, TRAIL = 7, 2_000, 252, 50_000.0, 2_000.0


def fade_day(r, ib_end: str, be_half: bool, full_target: bool, stop_k: float):
    ib = r[r.clock < ib_end]
    if len(ib) < 12:
        return None
    ibh, ibl = ib.high.max(), ib.low.min()
    rng = ibh - ibl
    if rng <= 0:
        return None
    mid = (ibh + ibl) / 2
    w_end = {"10:00": "10:30", "09:45": "10:15", "10:30": "11:00"}[ib_end]
    win = r[(r.clock >= ib_end) & (r.clock < w_end)]
    touch = None
    for i, row in win.iterrows():
        if row.close > ibh or row.close < ibl:
            return None
        if row.high >= ibh:
            touch = (-1, i); break
        if row.low <= ibl:
            touch = (1, i); break
    if touch is None:
        return None
    side, i0 = touch
    entry = ibh if side < 0 else ibl
    stop = entry - side * stop_k * rng
    target = (ibl if side < 0 else ibh) if full_target else mid
    be_trig = abs(entry - mid) / 2
    cur = stop
    for hi, lo, cl in r.loc[i0 + 1:][["high", "low", "close"]].to_numpy():
        if side < 0:
            if hi >= cur: return entry - cur, abs(entry - stop)
            if lo <= target: return entry - target, abs(entry - stop)
            if be_half and (entry - lo) >= be_trig: cur = min(cur, entry)
        else:
            if lo <= cur: return cur - entry, abs(entry - stop)
            if hi >= target: return target - entry, abs(entry - stop)
            if be_half and (hi - entry) >= be_trig: cur = max(cur, entry)
    cl = r.close.iloc[-1]
    return ((entry - cl) if side < 0 else (cl - entry)), abs(entry - stop)


def main() -> None:
    rng_ = np.random.default_rng(SEED)
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    ARMS = {"E0_default": dict(ib_end="10:00", be_half=False, full_target=False, stop_k=0.25),
            "C1_be": dict(ib_end="10:00", be_half=True, full_target=False, stop_k=0.25),
            "C2_full": dict(ib_end="10:00", be_half=False, full_target=True, stop_k=0.25),
            "C3_tight": dict(ib_end="10:00", be_half=False, full_target=False, stop_k=0.15),
            "C4_ib15": dict(ib_end="09:45", be_half=False, full_target=False, stop_k=0.25),
            "C5_ib60": dict(ib_end="10:30", be_half=False, full_target=False, stop_k=0.25)}
    days = sorted(R.gday.unique())
    M = pd.DataFrame(0.0, index=days, columns=list(ARMS))
    stats = {a: [] for a in ARMS}
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200:
            continue
        era = "23-24" if d[:4] in ("2023", "2024") else d[:4]
        for a, kw in ARMS.items():
            res = fade_day(r, **kw)
            if res is None:
                continue
            pts, risk = res
            M.loc[d, a] = RISK * (pts - FR) / risk
            stats[a].append(dict(pts=pts, risk=risk, era=era))
    M = M.loc[M.abs().sum(1) > 0].reindex(days).fillna(0.0)
    M.to_parquet(ROOT / "output/nya_ivb_fade_arms.parquet")
    print("== tournament (base friction) ==")
    for a in ARMS:
        T = pd.DataFrame(stats[a])
        if not len(T):
            continue
        net = T.pts - FR
        r_ = net / T.risk
        gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
        eras = " ".join(f"{e}:{x.sum():+.0f}" for e, x in net.groupby(T.era))
        print(f"  {a}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
              f"${RISK*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {eras}")
    p = pbo_cscv(M, n_blocks=16)
    print(f"PBO over arms: {p.pbo:.2f} ({p.n_trials} arms) — "
          f"{'OVERFIT' if p.overfit else 'ok'}; P(OOS loss) {p.prob_oos_loss:.2f}")

    s = M["E0_default"]
    n_led, var_led = TL.n_trials(), TL.trial_effect_variance()
    d = deflated_sharpe_ratio(s.to_numpy(float), n_trials=n_led, trial_sr_var=var_led)
    print(f"== grading (default spec, {int((s!=0).sum())} trade-days / {len(s)} sessions) ==")
    print(f"  daily SR {d.sr:+.4f} | PSR(0) {d.psr_zero:.3f} vs sleeve floor 0.75 "
          f"{'PASS' if d.psr_zero >= 0.75 else 'FAIL'} | DSR {d.dsr:.3f} "
          f"(ledger {n_led} trials) | MTRL {min_track_record_length(s.to_numpy(float)):.0f}d")
    busts, nets = 0, []
    x = s.to_numpy(float)
    for _ in range(N_SIMS):
        path = x[rng_.integers(0, len(x), YEAR_DAYS)]
        bal, line = START, START - TRAIL
        for pl in path:
            bal += pl
            if bal - line <= 0: busts += 1; break
            line = min(START, max(line, bal - TRAIL))
        nets.append(bal - START)
    print(f"  MC 12mo: P(bust) {busts/N_SIMS:.1%} median ${np.median(nets):+,.0f}")

    canon = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet")
    sc = canon.groupby("day").pl.sum().reindex(s.index).fillna(0.0)
    ok = sc.index[(sc != 0) | (s != 0)]
    pe = float(np.corrcoef(s.loc[ok], sc.loc[ok])[0, 1])
    both = ((s != 0) & (sc != 0))
    print(f"== canon correlation == union Pearson {pe:+.3f} | both-active {int(both.sum())} days")
    if both.sum() >= 10:
        print(f"  both-active Pearson {float(np.corrcoef(s[both], sc[both])[0,1]):+.3f}")


if __name__ == "__main__":
    main()
