#!/usr/bin/env python3
"""EXIT-LEVER DIAGNOSTIC — is the substrate's -0.18 E[R]/fill an ENTRY problem or an EXIT problem?

The engine substrate loses -0.18 R/fill raw (2,995 fills) with exit_reason ~73% stop / 12% target.
Two possibilities with opposite implications:
  ENTRY problem  trades never go favorable -> no exit rule can help -> the window is dead, done.
  EXIT problem   trades routinely reach +1R/+2R then reverse -> a fixed target would flip it ->
                 a real, fittable lever we have NOT pulled.

This re-walks each fill's 1-minute path from the engine's fill_ts to its exit_ts and records the
maximum FAVOURABLE excursion (MFE) and adverse excursion (MAE) in R, versus realised R. It then
asks the decisive question: if we OVERRODE the engine's exit with a plain fixed-R target + the
engine's own initial stop, what would E[R] be, per year? A fixed target is evaluated with the
usual intrabar pessimism (stop checked before target on the same bar).

No new fitting of ENTRIES -- same fills, same initial stops. The target level is the only knob,
swept 1.0R..3.0R, reported per year so a cross-regime read is possible (2023-24 vs 2025-26).

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/substrate_mfe.py
"""
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
NY = "America/New_York"
TICK, PV, COMM = 0.25, 20.0, 5.0

print("load ...", flush=True)
F = pd.read_parquet(f"{S}/london_engine_substrate.parquet")
F["fill_ts"] = pd.to_datetime(F.fill, utc=True).dt.tz_convert(NY)
F["exit_ts"] = pd.to_datetime(F.exit, utc=True).dt.tz_convert(NY)
F["risk"] = (F.entry - F.stop).abs()
F = F[F.risk >= 1.0].sort_values("fill_ts").reset_index(drop=True)
F["dir"] = np.where(F.direction == "long", 1, -1)
F["R"] = F.dollars / (F.risk * PV)
F["yr"] = F.day.str[:4]

bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bt = bars.ts.values
bh, bl = bars.high.values.astype(float), bars.low.values.astype(float)

# per-fill path walk: fill bar .. exit bar (engine's own exit), plus a generous EOD cap for
# the fixed-target override (walk to same-session 15:55 ET if the target model would run longer)
print("walk paths ...", flush=True)
k_fill = np.searchsorted(bt, F.fill_ts.values, side="left")
k_exit = np.searchsorted(bt, F.exit_ts.values, side="left")
en = F.entry.values
dr = F["dir"].values
rk = F.risk.values

mfe = np.full(len(F), np.nan)
mae = np.full(len(F), np.nan)
# fixed-target override outcomes for a grid of targets
TG = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
fixed_R = {t: np.full(len(F), np.nan) for t in TG}

# cap the override walk at the engine exit bar + a buffer so it can reach a further target the
# engine's trail cut short; but never beyond the same session's 15:55 ET. Use engine exit bar as
# the horizon (conservative: the override can only exit EARLIER via target, else takes engine R).
for n in range(len(F)):
    kf, ke = int(k_fill[n]), int(k_exit[n])
    if ke < kf:
        ke = kf
    hi_run, lo_run = -np.inf, np.inf
    d = dr[n]
    e = en[n]
    r = rk[n]
    hit = {t: None for t in TG}
    stop_hit_at = None
    for k in range(kf, min(ke + 1, len(bars))):
        adv_hi = d * (bh[k] - e) if d > 0 else d * (bl[k] - e)   # best favourable this bar
        adv_lo = d * (bl[k] - e) if d > 0 else d * (bh[k] - e)   # worst adverse this bar
        hi_run = max(hi_run, adv_hi)
        lo_run = min(lo_run, adv_lo)
        # fixed-target override: engine's initial stop (-1R) vs fixed target; stop first
        if stop_hit_at is None and lo_run <= -r:
            stop_hit_at = k
        for t in TG:
            if hit[t] is None:
                if stop_hit_at is not None and stop_hit_at <= k:
                    hit[t] = -1.0                                # stopped before target
                elif hi_run >= t * r:
                    hit[t] = t                                   # target reached
    mfe[n] = hi_run / r
    mae[n] = lo_run / r
    for t in TG:
        # unresolved by engine-exit horizon -> mark to engine's realised R (trail/eod outcome)
        fixed_R[t][n] = hit[t] if hit[t] is not None else F.R.values[n]

F["mfe"] = mfe
F["mae"] = mae


def blk(sub, lab):
    print(f"  {lab:20s} n={len(sub):5d}  meanR {sub.R.mean():+.3f}  "
          f"meanMFE {sub.mfe.mean():+.2f}  meanMAE {sub.mae.mean():+.2f}  "
          f">=1R {100*(sub.mfe>=1).mean():3.0f}%  >=2R {100*(sub.mfe>=2).mean():3.0f}%  "
          f">=3R {100*(sub.mfe>=3).mean():3.0f}%")


if __name__ == "__main__":
    print("\n" + "=" * 104)
    print("MFE / MAE DECOMPOSITION — do trades go favourable before dying?")
    print("=" * 104)
    blk(F, "ALL")
    for yr in ("2023", "2024", "2025", "2026"):
        blk(F[F.yr == yr], yr)
    print("\n  reference: a real edge shows meanMFE well above |meanMAE| and a high >=2R rate;")
    print("  a dead entry shows MFE ~ MAE and few trades reaching +2R.")

    print("\n" + "=" * 104)
    print("FIXED-TARGET OVERRIDE (engine's initial stop kept; only the target changes)")
    print("=" * 104)
    print(f"  {'target':>7} | {'ALL E[R]':>9} {'2023':>8} {'2024':>8} {'2025':>8} {'2026':>8} | "
          f"{'TRAIN$':>10} {'TEST$':>10}")
    for t in TG:
        col = fixed_R[t]
        dollars = col * rk * PV - COMM
        tr = F.day.values < "2025-01-01"
        row = [col.mean()]
        for yr in ("2023", "2024", "2025", "2026"):
            row.append(col[F.yr.values == yr].mean())
        print(f"  {t:>6.2f}R | {row[0]:>+9.3f} {row[1]:>+8.3f} {row[2]:>+8.3f} {row[3]:>+8.3f} "
              f"{row[4]:>+8.3f} | {dollars[tr].sum():>+10,.0f} {dollars[~tr].sum():>+10,.0f}")
    print("\n  (override exits at the fixed target if MFE reaches it before the initial stop;")
    print("   otherwise inherits the engine's realised R. Horizon = engine exit bar, so this")
    print("   UNDERSTATES a further target -- it is a floor on what a fixed target could do.)")
