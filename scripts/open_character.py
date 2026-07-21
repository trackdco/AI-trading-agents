#!/usr/bin/env python3
"""OPEN-CHARACTER READER (Angus 21 Jul) — pattern recognition, NOT a PnL test.

Classify each NY open (09:30-09:45 drive) as CONTINUATION vs MANIPULATION using the tape:
  * liquidity sweep  — did the drive take out prior-day / overnight high or low (resting liq)?
  * CVD confirmation — is the drive backed by same-direction aggressive flow, or does flow
                       diverge / get absorbed at the extreme?
  * depth wall       — (heatmap) is there a large opposing resting wall at the extreme (absorb)?

Then VALIDATE as pattern recognition only: did 09:45->10:15 PERSIST the drive (continuation)
or REVERSE through it (manipulation)? Report how often the label called it right. No dollars.

    python -m scripts.open_character
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.champion_journal_cvd import load_cvd_delta   # noqa: E402

NY = "America/New_York"
PRICE = Path("data/reference/nq_1m_feb_jul2026.parquet")
DEPTH_DIR = Path("data/reference/depth_2026")


def _t(df, h, m):
    return df.index.map(lambda x: (x.hour, x.minute) >= (h, m))


def sessions(px):
    px = px.copy()
    px["sd"] = px.ts_event.dt.tz_convert(NY)
    # NY session date: bars from 18:00 belong to the NEXT calendar day's session
    sd = px.ts_event.dt.tz_convert(NY)
    px["session"] = (sd + pd.Timedelta(hours=6)).dt.date   # 18:00 -> next day
    return px


def cvd_sign(px, cvd):
    """Calibrate: does +delta mean aggressive BUYING? Corr of 1m return vs 1m delta."""
    r = px.set_index("ts_event")["close"].diff()
    j = pd.concat([r.rename("ret"), cvd.rename("d")], axis=1).dropna()
    c = np.corrcoef(j.ret, j.d)[0, 1]
    return (1 if c >= 0 else -1), c


def main():
    px = pd.read_parquet(PRICE)
    cvd = load_cvd_delta()
    sgn, corr = cvd_sign(px, cvd)
    print(f"CVD sign calibration: corr(1m return, delta) = {corr:+.3f}  ->  buying = {'+' if sgn>0 else '-'}delta\n")
    px = sessions(px)
    depth_days = {Path(f).stem.split("_")[2] for f in glob.glob(str(DEPTH_DIR / "nq_depth_*_ny.csv"))}

    rows = []
    for sess, day in px.groupby("session"):
        day = day.set_index("ts_event").sort_index()
        idx = day.index  # tz-aware NY timestamps -> x.hour/x.minute are NY local
        hm = np.array([t.hour * 60 + t.minute for t in idx])
        def win(h1, m1, h2, m2):
            return day[(hm >= h1 * 60 + m1) & (hm < h2 * 60 + m2)]
        drive = win(9, 30, 9, 45)
        reso = win(9, 45, 10, 15)       # short horizon (kept for reference)
        morn = win(9, 45, 11, 30)       # morning resolution — "what kind of day is it"
        if len(drive) < 5 or len(reso) < 5 or len(morn) < 10:
            continue
        # reference liquidity: overnight H/L up to the open (causal, pre-09:30)
        on = day[hm < 9 * 60 + 30]
        if len(on) < 10:
            continue
        on_hi, on_lo = on.high.max(), on.low.min()
        o = drive.open.iloc[0]
        d_hi, d_lo = drive.high.max(), drive.low.min()
        up = (drive.close.iloc[-1] - o) >= 0
        dirn = 1 if up else -1
        ext = d_hi if up else d_lo
        # sweep: drive extreme took out overnight liquidity in the drive direction
        swept = (d_hi > on_hi) if up else (d_lo < on_lo)
        # CVD during the drive, calibrated so + = buying
        cvd_drive = sgn * cvd.reindex(drive.index).fillna(0).sum()
        confirmed = (cvd_drive * dirn) > 0 and abs(cvd_drive) > 150   # flow backs the drive
        diverge = (cvd_drive * dirn) < 0 or abs(cvd_drive) < 60       # flow opposes / is hollow
        # depth wall at the extreme (opposing side absorbs): only if we have the day
        wall = None
        ds = str(sess)
        if ds in depth_days:
            dp = pd.read_csv(DEPTH_DIR / f"nq_depth_{ds}_ny.csv", parse_dates=["ts"])
            snap = dp[(dp.ts.dt.hour == 9) & (dp.ts.dt.minute.between(43, 46))]
            opp = "ask" if up else "bid"          # side the drive is pushing INTO
            near = snap[(snap.side == opp) & (snap.price.sub(ext).abs() <= 15)]
            # typical per-minute per-side resting size on this book, as the baseline
            per_min = dp[dp.side == opp].groupby("ts")["size"].sum()
            if len(per_min) and len(near):
                # absorption wall: opposing size stacked at the extreme >> typical minute
                wall = bool(near["size"].sum() >= 2.0 * per_min.mean())
            else:
                wall = False
        # ---- label ----
        if swept and (diverge or wall):
            label = "manipulation"
        elif confirmed and not (swept and diverge):
            label = "continuation"
        else:
            label = "unclear"
        # ---- validation (no PnL): "what kind of day" — did the MORNING (09:45-11:30)
        # resolve WITH the drive (continuation) or AGAINST it (manipulation = fake drive)?
        # Judged on the morning EXTREME beyond the drive, not a single close, so a normal
        # LTF pullback inside a continuation day doesn't count as a reversal. ----
        open_px = o
        cont_ext = (morn.high.max() - open_px) if up else (open_px - morn.low.min())   # extension WITH drive
        rev_ext = (open_px - morn.low.min()) if up else (morn.high.max() - open_px)     # extension AGAINST drive
        if rev_ext > cont_ext and rev_ext > 15:
            outcome = "reversed"        # day resolved opposite the open drive
        elif cont_ext > rev_ext and cont_ext > 15:
            outcome = "persisted"       # day extended in the drive direction
        else:
            outcome = "chop"
        rows.append(dict(session=str(sess), dir=("up" if up else "dn"), swept=swept,
                         cvd=int(cvd_drive), confirmed=confirmed, diverge=diverge,
                         wall=wall, label=label, outcome=outcome))

    R = pd.DataFrame(rows)
    print(f"classified {len(R)} sessions\n")
    print("label distribution:")
    print(R.label.value_counts().to_string(), "\n")
    print("=== PATTERN VALIDATION (no PnL): label vs what 09:45-10:15 actually did ===")
    for lab, exp in (("continuation", "persisted"), ("manipulation", "reversed")):
        s = R[R.label == lab]
        dec = s[s.outcome != "chop"]
        hit = (dec.outcome == exp).mean() * 100 if len(dec) else 0
        print(f"  {lab:13s} n={len(s):3d}  decisive={len(dec):3d}  "
              f"called '{exp}' correctly {hit:4.0f}%   (chop {int((s.outcome=='chop').sum())})")
    print("\ncrosstab label x outcome:")
    print(pd.crosstab(R.label, R.outcome).to_string())
    R.to_csv("output/open_character.csv", index=False)
    print("\n-> output/open_character.csv")
    print("\nsample manipulation days:")
    print(R[R.label == "manipulation"].head(8).to_string(index=False))
    print("\nsample continuation days:")
    print(R[R.label == "continuation"].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
