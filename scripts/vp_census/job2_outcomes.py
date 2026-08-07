"""Job 2 — continuation (breakout-arm) outcome columns, spec section 2.

Walks forward from each Job 1 excursion to 16:00 ET and appends
scale-normalised continuation outcomes. Unit = value-area width
W = vah - val of the excursion's own session profile.

Conventions (assistant rulings, ledgered):
- The forward walk starts at the bar AFTER the trigger bar (events
  strictly after excursion_start = the trigger close). The trigger
  bar's own wick is pre-acceptance and does not count as continuation.
- Same-bar ambiguities are scored AGAINST continuation: a bar that
  both closes back inside the VA and touches a target counts as
  reentry-first; a bar that hits both stop and target counts as
  stop-first. Same stance as Job 1's poc_before_stop.
- t_first_reentry is recomputed independently in the walk and asserted
  equal to Job 1's t_return_inside on every row (cross-check, G4/G7
  adjacent).

Usage: job2_outcomes.py <excursions_parquet> <out_parquet>
       (canonical by default; also run for variant sets)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/vp_census")
import vp_lib as V

CONT_T = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
STOP_S = (10, 20, 30, 40, 60, 80)


def outcomes_for_session(rth: pd.DataFrame, exs: pd.DataFrame) -> list[dict]:
    ts = rth["ts_event"].to_numpy()
    close = rth["close"].to_numpy(float)
    high = rth["high"].to_numpy(float)
    low = rth["low"].to_numpy(float)
    n = len(rth)
    # map excursion_start (trigger close = trigger ts_event + 1min) -> index
    idx_of = {pd.Timestamp(t): i for i, t in enumerate(ts)}
    rows = []
    for _, e in exs.iterrows():
        vah, val, poc = float(e.vah), float(e.val), float(e.poc)
        W = vah - val
        side = e.side
        L = vah if side == "above" else val
        sgn = 1.0 if side == "above" else -1.0
        trig_ts = pd.Timestamp(e.excursion_start) - pd.Timedelta(minutes=1)
        i0 = idx_of.get(trig_ts)
        row = dict(session_date=e.session_date, side=side,
                   excursion_start=e.excursion_start, W=W)
        if i0 is None or W <= 0:
            rows.append({**row, "walk_ok": False})
            continue
        start = i0 + 1
        f_hi = high[start:]
        f_lo = low[start:]
        f_cl = close[start:]
        m = len(f_hi)
        inside = (f_cl <= vah) & (f_cl >= val)
        reentry_i = int(np.argmax(inside)) if inside.any() else None
        t_reentry = np.nan
        if reentry_i is not None:
            t_reentry = float((pd.Timestamp(ts[start + reentry_i])
                               + pd.Timedelta(minutes=1)
                               - pd.Timestamp(e.excursion_start))
                              .total_seconds() / 60.0)
        beyond = (f_hi - L) if side == "above" else (L - f_lo)
        mfe_W = float(beyond.max() / W) if m else np.nan
        poc_touch = (f_lo <= poc) & (poc <= f_hi)

        row.update(walk_ok=True, mfe_W=mfe_W,
                   t_first_reentry=t_reentry,
                   returned_to_poc=bool(poc_touch.any()))

        for T in CONT_T:
            tgt = T * W
            hit = beyond >= tgt - 1e-9
            hit_i = int(np.argmax(hit)) if hit.any() else None
            row[f"reached_cont_{T}"] = hit_i is not None
            row[f"t_cont_{T}"] = (
                float((pd.Timestamp(ts[start + hit_i]) + pd.Timedelta(minutes=1)
                       - pd.Timestamp(e.excursion_start)).total_seconds() / 60.0)
                if hit_i is not None else np.nan)
            # cont before first close back inside (same bar -> reentry first)
            if hit_i is None:
                row[f"cont_before_reentry_{T}"] = False
            elif reentry_i is None:
                row[f"cont_before_reentry_{T}"] = True
            else:
                row[f"cont_before_reentry_{T}"] = hit_i < reentry_i
        for S in STOP_S:
            stop_px = L - sgn * S * V.TICK
            stop_hit = (f_lo <= stop_px) if side == "above" else (f_hi >= stop_px)
            tgt_hit = beyond >= 1.0 * W - 1e-9
            s_i = int(np.argmax(stop_hit)) if stop_hit.any() else None
            g_i = int(np.argmax(tgt_hit)) if tgt_hit.any() else None
            if g_i is None:
                row[f"cont_before_stop_{S}"] = False
            elif s_i is None:
                row[f"cont_before_stop_{S}"] = True
            else:
                row[f"cont_before_stop_{S}"] = g_i < s_i  # tie -> stop first
        rows.append(row)
    return rows


def compute(ex: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    by_sess = dict(tuple(bars.groupby("session")))
    out = []
    for d, exs in ex.groupby("session_date"):
        sb = by_sess.get(d)
        if sb is None:
            continue
        dts = pd.Timestamp(d, tz=V.ET)
        m = (sb["ts_event"] >= dts + pd.Timedelta(hours=9, minutes=30)) & \
            (sb["ts_event"] < dts + pd.Timedelta(hours=16))
        rth = sb.loc[m].sort_values("ts_event", kind="mergesort").reset_index(drop=True)
        out.extend(outcomes_for_session(rth, exs))
    oc = pd.DataFrame(out)
    merged = ex.merge(oc, on=["session_date", "side", "excursion_start"],
                      how="left", validate="one_to_one")
    # cross-check: independent reentry walk must reproduce Job 1 exactly
    a = merged["t_first_reentry"].to_numpy()
    b = merged["t_return_inside"].to_numpy()
    same = np.isclose(a, b, equal_nan=True)
    if not same.all():
        bad = merged.loc[~same, ["session_date", "side", "excursion_start",
                                 "t_first_reentry", "t_return_inside"]]
        raise AssertionError(f"reentry mismatch on {len(bad)} rows:\n{bad.head()}")
    return merged


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else "output/vp_census/excursions.parquet"
    dst = sys.argv[2] if len(sys.argv) > 2 else "output/vp_census/excursions_job2.parquet"
    bars = V.load_master_bars()
    ex = pd.read_parquet(src)
    merged = compute(ex, bars)
    merged = merged.sort_values(["session_date", "side", "excursion_start"],
                                kind="mergesort").reset_index(drop=True)
    merged.to_parquet(dst, index=False)
    ok = merged["walk_ok"].fillna(False)
    print(f"{dst}: {len(merged)} rows, walk_ok {int(ok.sum())}, "
          f"reentry cross-check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
