#!/usr/bin/env python3
"""NYA-IBC-01 stage 3 — THE SINGLE SEALED-MONTHS LOOK, per
docs/OOF-DECLARATION-ibc-legB.md (frozen before this script ran). Three
specs (B0/B1/B8), six sealed months, decision rule pre-committed. This
script is run ONCE.

    python -m scripts.nya_ibc_oof_look
"""
from __future__ import annotations

import sys
from glob import glob
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import footprint as _fp  # noqa: E402  # band-clean / sealed-span chokepoint

NY = "America/New_York"
FR = 1.0
MONTHS = ("2023-07", "2023-09", "2023-11", "2024-03", "2024-04", "2024-10")


def build_flow():
    """Minute delta from the sealed footprint files.

    SIGN CORRECTED 2026-08-06. 'B' is the BUYER-aggressor (lifted the offer), so
    delta = B - A. This function computed A - B, i.e. the exact negative. Settled
    empirically against realised direction over 287 London sessions (r = +0.78 on
    large moves for B - A); see src/engine/footprint for the audit.

    ANGUS: the committed output of this script was produced under the INVERTED sign,
    and this is a spent NY holdout look. Whether its recorded conclusion survives the
    correction is a ruling, not an engineering call — nothing here has been re-run and
    no artifact has been regenerated.
    """
    frames = []
    for m in MONTHS:
        # allow_holdout: this script IS the declared NY out-of-fit look. No band is
        # supplied — deriving one for the sealed days would itself be a look
        # (VALIDATION-PROCESS §4.1), so the tape here is NOT band-cleaned.
        f = _fp.load_footprint(
            [ROOT / f"data/reference/cvd/footprint_holdout_{m}.parquet"],
            bands=None, allow_holdout=True, report=False)
        ts = pd.to_datetime(f.ts_minute, utc=True).dt.tz_convert(NY)
        f = f.assign(mi=ts)
        piv = f.pivot_table(index="mi", columns="side", values="volume", aggfunc="sum").fillna(0)
        delta = piv.get("B", 0) - piv.get("A", 0)
        frames.append(delta.rename("delta"))
    D = pd.concat(frames).sort_index()
    out = pd.DataFrame({"delta": D})
    out["gday"] = pd.Series((out.index + pd.Timedelta(hours=6)).date, index=out.index).astype(str)
    out["clock"] = out.index.strftime("%H:%M")
    return out.set_index(["gday", "clock"])


def build_depth():
    """Per-minute book imbalance from the sealed depth CSVs (last snapshot/min)."""
    rows = []
    for f in sorted(glob(str(ROOT / "data/reference/depth_2023_24/nq_depth_*_ny.csv"))):
        day = Path(f).name.split("_")[2]
        if day[:7] not in MONTHS:
            continue
        d = pd.read_csv(f)
        d["ts"] = pd.to_datetime(d.ts)
        d["mi"] = d.ts.dt.floor("min")
        last = d.groupby("mi").ts.max().rename("last_ts")
        d = d.merge(last, on="mi")
        d = d[d.ts == d.last_ts]
        g = d.pivot_table(index="mi", columns="side", values="size", aggfunc="sum").fillna(0)
        if "bid" not in g or "ask" not in g:
            continue
        imb = g.bid / (g.bid + g.ask).clip(lower=1)
        for mi, v in imb.items():
            rows.append(dict(gday=str((mi + pd.Timedelta(hours=6)).date()),
                             clock=mi.strftime("%H:%M"), imb=float(v)))
    return pd.DataFrame(rows).set_index(["gday", "clock"])


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    F = build_flow()
    D = build_depth()
    print(f"sealed flow minutes: {len(F)} | sealed depth minutes: {len(D)}")

    # causal weekday trailing rates over ALL history (prior days only)
    wd_rows = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200: continue
        ib = r[r.clock < "10:30"]
        if len(ib) < 50: continue
        ibh, ibl = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh][0]; t_lo = ib.index[ib.low <= ibl][0]
        if t_hi == t_lo: continue
        pred = "L" if t_hi < t_lo else "H"
        fb = None
        for _, row in r[r.clock >= "10:30"].iterrows():
            if row.high > ibh: fb = "H"; break
            if row.low < ibl: fb = "L"; break
        wd_rows.append(dict(day=d, wd=pd.Timestamp(d).weekday(), success=int(fb == pred)))
    W = pd.DataFrame(wd_rows).set_index("day").sort_index()
    W["roll_wd"] = W.groupby("wd").success.transform(
        lambda s: s.shift(1).rolling(26, min_periods=13).mean())

    ARMS = {
        "B0_astaught": dict(),
        "B1_cap20": dict(cap=20.0),
        "B8_full": dict(cap=30.0, frontrun=True, cut=True, conv=True),
    }
    rows = []
    for d, r in R.groupby("gday"):
        if d[:7] not in MONTHS:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200: continue
        ib = r[r.clock < "10:30"]
        if len(ib) < 50: continue
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        cummax, cummin = np.maximum.accumulate(H), np.minimum.accumulate(L_)
        ibh_f, ibl_f = ib.high.max(), ib.low.min()
        t_hi = ib.index[ib.high >= ibh_f][0]; t_lo = ib.index[ib.low <= ibl_f][0]
        if t_hi == t_lo: continue
        for k in range(len(r)):
            ck = r.clock.iloc[k]
            if ck < "10:23": continue
            if ck >= "11:30": break
            if ck < "10:30":
                ibh, ibl = cummax[k - 1], cummin[k - 1]
                th = np.argmax(H[:k] >= ibh); tl = np.argmax(L_[:k] <= ibl)
            else:
                ibh, ibl, th, tl = ibh_f, ibl_f, t_hi, t_lo
            if th == tl or C[k] > ibh or C[k] < ibl:
                break
            side = -1 if th < tl else 1
            mid = (ibh + ibl) / 2
            if not (L_[k] <= mid <= H[k]):
                continue
            e = mid
            stop_full = ibh if side < 0 else ibl
            tgt = ibl if side < 0 else ibh
            risk_full = abs(e - stop_full)
            if risk_full <= 0:
                break
            score = 0
            rw = W.roll_wd.get(d, np.nan)
            if rw == rw and rw >= 0.70: score += 1
            clk = r.clock.iloc[k]
            try:
                if np.sign(float(F.loc[(d, clk), "delta"])) == side: score += 1
            except KeyError:
                pass
            try:
                if (float(D.loc[(d, clk), "imb"]) - 0.5) * 2 * side > 0.1: score += 1
            except KeyError:
                pass
            rec = dict(day=d, month=d[:7], score=score)
            for arm, cfg in ARMS.items():
                if cfg.get("frontrun") and clk >= "10:30":
                    continue
                risk = min(risk_full, cfg["cap"]) if cfg.get("cap") else risk_full
                stop = e - side * risk
                pts, mae, cvd = None, 0.0, 0.0
                for m in range(k + 1, len(r)):
                    hi, lo, cl = H[m], L_[m], C[m]
                    adv = (hi - e) if side < 0 else (e - lo)
                    mae = max(mae, adv)
                    try:
                        cvd += float(F.loc[(d, r.clock.iloc[m]), "delta"]) * side
                    except KeyError:
                        pass
                    if (side < 0 and hi >= stop) or (side > 0 and lo <= stop):
                        pts = -risk; break
                    if (side < 0 and lo <= tgt) or (side > 0 and hi >= tgt):
                        pts = abs(tgt - e); break
                    if cfg.get("cut") and (m - k) == 15 and (mae / risk >= 0.5 or cvd <= 0):
                        pts = ((e - cl) if side < 0 else (cl - e)); break
                if pts is None:
                    pts = side * (C[-1] - e)
                units = (1 + score) if cfg.get("conv") else 1
                rec[arm] = units * (pts - FR) / risk
            rows.append(rec)
            break  # wick-death universe: one sequence per day

    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_ibc_oof_look.parquet", index=False)
    print(f"\nSEALED-MONTHS LOOK: {len(T)} leg-B events across {T.month.nunique()} months")
    for arm in ARMS:
        g = T[T[arm].notna()][arm]
        if not len(g):
            print(f"  {arm}: n=0"); continue
        mo = " ".join(f"{m}:{x.sum():+.1f}" for m, x in g.groupby(T.month))
        print(f"  {arm}: n={len(g)} WR {(g>0).mean():.0%} {g.sum():+.1f}R "
              f"${160*g.sum():+,.0f} | {mo}")


if __name__ == "__main__":
    main()
