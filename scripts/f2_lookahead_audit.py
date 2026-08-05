#!/usr/bin/env python3
"""STEP 0 — LOOK-AHEAD AUDIT of retrace_ratio (F2) and disp_delta_magnitude (|F1|).

Run BEFORE any pooled statistics. The question is precise:

    Are F2 and |F1| computable from information available AT OR BEFORE the entry, on every
    dataset, with no future data?

"No future BARS" is the weaker question and all three scripts already assert it. The stronger
question — the one the cap_rules defect taught us to ask — is whether the features read any data
that did not exist at the ENTRY INSTANT. Footprint data is aggregated per MINUTE. An entry that
fills intrabar therefore sits INSIDE its own minute bucket, and including that whole bucket pulls
in up to 59 seconds of post-fill tape.

This script measures exactly that, per card:
  * the exact time boundary each window reads up to
  * how long the retracement window is, in minutes
  * what share of the retracement VOLUME comes from the entry minute alone
  * F2_STRICT = the same ratio with the entry minute EXCLUDED — the largest clean lower bound
  * how many trades change side of the 1.0 threshold between the two
  * rank agreement between them (Spearman), since H2 is tested on an ORDERING

It writes no verdict about H2 or H1. It only decides whether those tests may proceed.

    python -m scripts.f2_lookahead_audit
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.f2_oos_test import flow_frame  # noqa: E402

# The ORB arm locked in STEP 1, before any F2 result was inspected.
ORB_ARM = {"arm_brk": "close", "arm_entry": "retrace", "arm_stop": "fvg"}

# Each card's own scan-window START — the normaliser's session begins here, NOT at midnight.
WIN_START_MIN = {"ash-unicorn-sb": 9 * 60 + 45,      # AM1
                 "zxck-10am-keyopen": 10 * 60,       # the 10:00 key open
                 "orb-fvg-nyopen": 9 * 60 + 30}      # the NY cash open

SOURCES = {
    "ash-unicorn-sb": ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-orderflow-trades.csv",
    "zxck-10am-keyopen": ROOT / "research/_shared/f2-oos-trades.csv",
    "orb-fvg-nyopen": ROOT / "research/orb-fvg/strategies/orb-fvg-nyopen-raw-trades.csv",
}


def load(name: str) -> pd.DataFrame:
    d = pd.read_csv(SOURCES[name])
    if name == "zxck-10am-keyopen":
        d = d[d.src == "zxck-10am-keyopen"] if "src" in d else d
    if name == "orb-fvg-nyopen":
        for k, v in ORB_ARM.items():
            d = d[d[k] == v]
    for c in ("disp_start", "disp_end", "entry_ts"):
        # logs are written across EDT/EST, so parse as UTC then restore NY local
        d[c] = pd.to_datetime(d[c], utc=True).dt.tz_convert("America/New_York")
    return d.reset_index(drop=True)


def audit(name: str, fp: pd.DataFrame) -> dict:
    d = load(name)
    vol = fp.vol
    w0 = WIN_START_MIN[name]
    rows = []
    for r in d.itertuples():
        t0, t1, te = r.disp_start, r.disp_end, r.entry_ts
        disp = vol[(vol.index >= t0) & (vol.index <= t1)]
        ret = vol[(vol.index > t1) & (vol.index <= te)]
        ret_strict = vol[(vol.index > t1) & (vol.index < te)]      # entry minute EXCLUDED
        entry_min = vol[(vol.index >= te) & (vol.index <= te)]
        dv = float(disp.sum())
        # F1 exposure. Its NUMERATOR (delta over the displacement leg) is clean whenever the
        # displacement window ends before the entry minute. Its DENOMINATOR is the session's
        # median minute volume up to AND INCLUDING the entry minute, so the entry minute can
        # still move F1 through the normaliser. Measure that separately.
        s0 = te.normalize() + pd.Timedelta(minutes=w0)
        sess_in = vol[(vol.index >= s0) & (vol.index <= te)]
        sess_ex = vol[(vol.index >= s0) & (vol.index < te)]
        med_in = float(sess_in.median()) if len(sess_in) else np.nan
        med_ex = float(sess_ex.median()) if len(sess_ex) else np.nan
        rows.append({
            "f1_norm_shift": (abs(med_in - med_ex) / med_ex
                              if med_ex and med_ex == med_ex and med_in == med_in else np.nan),
            "sess_minutes": int(len(sess_in)),
            "ret_minutes": int(len(ret)),
            "disp_minutes": int(len(disp)),
            "entry_minute_in_disp": bool(len(disp) and disp.index.max() >= te),
            "ret_vol": float(ret.sum()), "ret_vol_strict": float(ret_strict.sum()),
            "entry_min_vol": float(entry_min.sum()), "disp_vol": dv,
            "F2": float(ret.sum()) / dv if dv > 0 and len(ret) else np.nan,
            "F2_strict": (float(ret_strict.sum()) / dv
                          if dv > 0 and len(ret_strict) else np.nan),
        })
    a = pd.DataFrame(rows)
    n = len(a)
    have = a.F2.notna()
    share = np.where(a.ret_vol > 0, a.entry_min_vol / a.ret_vol, np.nan)
    both = a.F2.notna() & a.F2_strict.notna()
    cross = int(((a.F2[both] < 1.0) != (a.F2_strict[both] < 1.0)).sum())
    rho = (a.F2[both].rank().corr(a.F2_strict[both].rank())
           if both.sum() > 2 else np.nan)
    return {
        "card": name, "n": n, "F2_defined": int(have.sum()),
        "ret_len_p50": float(np.nanmedian(a.ret_minutes)),
        "ret_len_min": int(a.ret_minutes.min()) if n else 0,
        "ret_len_1min": int((a.ret_minutes == 1).sum()),
        "entry_min_share_p50": float(np.nanmedian(share)),
        "entry_min_share_mean": float(np.nanmean(share)),
        "fully_entry_minute": int((a.ret_minutes == 1).sum()),
        "disp_touches_entry_min": int(a.entry_minute_in_disp.sum()),
        "F2_strict_defined": int(a.F2_strict.notna().sum()),
        "threshold_crossings": cross, "spearman": float(rho) if rho == rho else np.nan,
        "f1_norm_shift_p50": float(np.nanmedian(a.f1_norm_shift)),
        "f1_norm_shift_max": float(np.nanmax(a.f1_norm_shift)) if len(a) else np.nan,
        "sess_minutes_p50": float(np.nanmedian(a.sess_minutes)),
        "_frame": a,
    }


def main() -> None:
    fp = flow_frame()
    print("STEP 0 — LOOK-AHEAD AUDIT of retrace_ratio (F2) and disp_delta_magnitude (|F1|)\n")
    print("THE TIME BOUNDARY EACH WINDOW READS UP TO — read from the three implementations:\n")
    print("  card               displacement window        retracement window     normaliser")
    print("  " + "-" * 88)
    print("  ash-unicorn-sb     [FVG start bar, MSS bar]    (MSS bar, ENTRY BAR]   session median")
    print("  zxck-10am-keyopen  [manip bar, close-thru bar] (close-thru, ENTRY]    session median")
    print("  orb-fvg-nyopen     [breakout bar, FVG bar]     (FVG bar, ENTRY BAR]   session median")
    print("\n  All three END the retracement window AT AND INCLUDING THE ENTRY MINUTE.")
    print("  No window reads any bar AFTER the entry bar — the runtime asserts confirm that.\n")

    res = [audit(k, fp) for k in SOURCES]
    hdr = (f"  {'card':<20}{'n':>6}{'F2 def':>8}{'ret len p50':>13}{'ret=1min':>10}"
           f"{'entry-min share of ret vol':>29}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for r in res:
        print(f"  {r['card']:<20}{r['n']:>6}{r['F2_defined']:>8}"
              f"{r['ret_len_p50']:>13.0f}{r['ret_len_1min']:>10}"
              f"{'median ' + format(100*r['entry_min_share_p50'], '.1f') + '%':>29}")

    print("\n  ---- what happens if the entry minute is EXCLUDED (F2_STRICT) ----")
    hdr2 = (f"  {'card':<20}{'F2_strict def':>15}{'undefined':>11}"
            f"{'cross the 1.0 cut':>19}{'Spearman rho':>14}")
    print(hdr2); print("  " + "-" * (len(hdr2) - 2))
    for r in res:
        und = r["F2_defined"] - r["F2_strict_defined"]
        print(f"  {r['card']:<20}{r['F2_strict_defined']:>15}{und:>11}"
              f"{r['threshold_crossings']:>19}{r['spearman']:>14.3f}")

    print("\n  ---- F1 / disp_delta_magnitude exposure ----")
    print(f"  {'card':<20}{'disp touches entry min':>24}{'sess mins p50':>15}"
          f"{'normaliser shift p50':>22}{'max':>9}")
    print("  " + "-" * 88)
    for r in res:
        print(f"  {r['card']:<20}{str(r['disp_touches_entry_min']) + ' of ' + str(r['n']):>24}"
              f"{r['sess_minutes_p50']:>15.0f}"
              f"{100*r['f1_norm_shift_p50']:>21.2f}%{100*r['f1_norm_shift_max']:>8.1f}%")

    print("\n" + "=" * 92)
    worst = max(r["entry_min_share_mean"] for r in res)
    print("FINDING")
    print("=" * 92)
    print("F2 IS NOT COMPUTABLE AT THE ENTRY INSTANT on any of the three cards.")
    print("The retracement window includes the entry MINUTE in full, and the entry fills")
    print("INTRABAR, so F2 as computed contains up to 59 seconds of POST-FILL tape.")
    print(f"Mean share of retracement volume drawn from the entry minute: up to {100*worst:.1f}%.")
    print("\nThis does NOT read future BARS, and the existing asserts are correct as far as they")
    print("go. It is a sub-minute contamination that is intrinsic to pairing minute-aggregated")
    print("footprint data with an intrabar limit fill.")
    print("\nCONSEQUENCE: a filter of the form 'take the trade if F2 < 1.0' is NOT IMPLEMENTABLE")
    print("as tested — at the fill you do not yet know the entry minute's volume.")


if __name__ == "__main__":
    main()
