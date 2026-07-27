#!/usr/bin/env python3
"""Apply the CANON RULEBOOK, unchanged, to the 2023/24 holdout days.

ANGUS: *"over these randomly selected months, apply the rulebook, and take the trades."*

Takes the candidate fills from `scripts/build_holdout_substrate` (same engine, same config,
both books, every day) and scores them with `scripts.canon_mechanical.build_canon` — the
production scorer, imported, not reimplemented. Every threshold comes from
`config/live_thresholds.json` and the frozen constants inside `build_canon`. Nothing here
derives a threshold from 2023/24 data; that would turn the holdout into a fit.

Feature definitions come from `src/canon/features.py` — the same module the LIVE ingestor
calls, so a holdout row is built the way a live row is built.

    python -m scripts.score_holdout

Writes output/holdout_canon_book.parquet and prints the verdict per year and per month.
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.canon_mechanical import build_canon
from src.canon.features import (
    badpa_features,
    bp5opp,
    depth_at,
    lon_slope_d,
    on_extreme_age_trade,
    tape_features,
    vwap_geometry,
)
from src.engine.indicators import daily_vwap

NY = "America/New_York"
SUB = ROOT / "output/holdout_substrate.parquet"
BARS = ROOT / "data/reference/nq_1m_master.parquet"
DEPTH = ROOT / "data/reference/depth_2023_24"
TRIGS = ROOT / "output/triggers_hist2326_ob_v2.csv"
OUT = ROOT / "output/holdout_canon_book.parquet"

# session windows, NY minutes-of-day (scripts/dayflow_features.win_masks)
W_LON = (2 * 60, 8 * 60)
W_PM = (8 * 60, 9 * 60 + 30)


def sgn_conf(v, direction) -> int:
    """1 when the signed value agrees with the trade's direction (trade_angles.sgn_conf)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0
    return int((v > 0 and direction == "long") or (v < 0 and direction == "short"))


def minute_tape() -> pd.DataFrame:
    """Per-minute b/a/vol/delta/vwp from the HOLDOUT footprint — same shape as fp_minutes."""
    frames = []
    for p in sorted(glob.glob(str(ROOT / "data/reference/cvd/footprint_holdout_*.parquet"))):
        d = pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"])
        d["volume"] = d["volume"].astype("int64")
        ny = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
        f = pd.DataFrame({"mi": ny.dt.floor("min"), "price": d.price.to_numpy(),
                          "side": d.side.to_numpy(), "volume": d.volume.to_numpy()})
        f["pv"] = f.price * f.volume
        g = f.groupby(["mi", "side"]).agg(vol=("volume", "sum"), pv=("pv", "sum")).unstack("side")
        m = pd.DataFrame({
            "b": g[("vol", "B")] if ("vol", "B") in g else 0.0,
            "a": g[("vol", "A")] if ("vol", "A") in g else 0.0,
            "pv": g[("pv", "B")].add(g[("pv", "A")], fill_value=0.0) if ("pv", "B") in g
                  else g[("pv", "A")]}).fillna(0.0)
        m["vol"] = m.b + m.a
        m["delta"] = m.b - m.a
        m["vwp"] = m.pv / m.vol.replace(0, np.nan)
        frames.append(m.drop(columns="pv"))
    M = pd.concat(frames).sort_index()
    M = M[~M.index.duplicated(keep="first")]
    hm = M.index.hour * 60 + M.index.minute
    M["hm"] = hm
    # session day: the CME 18:00 boundary — an evening minute belongs to the NEXT day
    d = pd.Series(M.index.date, index=M.index)
    M["sday"] = np.where(hm >= 18 * 60,
                         (pd.to_datetime(d) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d"),
                         pd.to_datetime(d).dt.strftime("%Y-%m-%d"))
    M["cum"] = M.groupby("sday").delta.cumsum()
    M["runmin"] = M.groupby("sday").cum.cummin()
    M["runmax"] = M.groupby("sday").cum.cummax()
    return M


def build_features(S: pd.DataFrame, M: pd.DataFrame, bars: pd.DataFrame,
                   trig_times: dict) -> pd.DataFrame:
    """One canon feature row per candidate fill, via src/canon/features.py."""
    bars = bars.copy()
    bt = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    ind = daily_vwap(bars)
    bars = bars.assign(mi=bt.dt.floor("min"), hm=bt.dt.hour * 60 + bt.dt.minute,
                       vw=ind["vwap"].to_numpy(), up1=ind["upper_1"].to_numpy())
    bars_i = bars.set_index("mi").sort_index()

    dep_cache: dict[str, pd.DataFrame] = {}
    rows = []
    for i, t in enumerate(S.itertuples(), 1):
        fill = pd.Timestamp(t.fill)
        if fill.tzinfo is None:
            fill = fill.tz_localize(NY)
        fill = fill.tz_convert(NY)
        day, direction, entry = str(t.day), t.direction, float(t.entry)
        r: dict = {"day": day, "book": t.book, "fill": fill, "direction": direction,
                   "entry": entry, "stop": float(t.stop), "exit_price": t.exit_price,
                   "dollars": float(t.dollars), "pattern": t.pattern, "tf": t.tf}
        r["risk"] = abs(entry - float(t.stop))
        r["R"] = r["dollars"] / (r["risk"] * 20.0) if r["risk"] > 0 else np.nan
        r["fillhm"] = fill.hour * 60 + fill.minute
        r["win_"] = "pre" if r["fillhm"] < 570 else "gold"
        r["yr"] = int(day[:4])

        upto = M[M.index < fill]
        sday_m = M[M.sday == day]
        daymed = float(sday_m.vol.median()) if len(sday_m) else np.nan
        if len(upto):
            r.update(tape_features(upto, direction, fill, daymed))
        pre_bars = bars_i.loc[: fill - pd.Timedelta(minutes=1)]
        if len(pre_bars):
            r.update(vwap_geometry(pre_bars.reset_index(), entry, direction))
            r.update(badpa_features(pre_bars, upto, entry, fill,
                                    trigger_times=trig_times.get(day)))
            sess0 = (fill - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
            r["on_extreme_age"] = on_extreme_age_trade(pre_bars.loc[sess0:], entry, fill)

        # --- 15-minute tape momentum: Tp (d15) and Tc (d15_conf) ---
        w15 = upto[upto.index >= fill - pd.Timedelta(minutes=15)]
        d15 = float(w15.delta.sum()) if len(w15) else np.nan
        r["d15"] = d15
        r["d15_conf"] = sgn_conf(d15, direction)

        # --- session CVD confirmations: C check ---
        sd = sday_m[sday_m.index < fill]
        cvd_lon = float(sd[(sd.hm >= W_LON[0]) & (sd.hm < W_LON[1])].delta.sum()) if len(sd) else np.nan
        r["cvd_LON"] = cvd_lon
        r["conf_LON"] = sgn_conf(cvd_lon, direction)
        # conf_PM uses the LEAKAGE-CLEAN truncated-at-fill form (canon_news_clean correction 1)
        r["conf_PM"] = int(r.get("pm_sofar_conf", 0) or 0)
        r["cvd_PM"] = float(sd[(sd.hm >= W_PM[0]) & (sd.hm < W_PM[1])].delta.sum()) if len(sd) else np.nan

        # --- depth families ---
        f = DEPTH / f"nq_depth_{day}_ny.csv"
        if f.exists():
            if day not in dep_cache:
                dd = pd.read_csv(f)
                dd["ts"] = pd.to_datetime(dd.ts)
                dep_cache[day] = dd
            r.update(depth_at(dep_cache[day], fill, entry, direction))

        if len(upto):
            r["bp5opp"] = bp5opp(upto, direction, fill)
            r["lon_slope_d"] = lon_slope_d(sd if len(sd) else upto, direction)

        # --- Layer 2d inputs: where the trade stands 3 minutes after the fill ---
        sign = 1.0 if direction == "long" else -1.0
        fwd = bars_i.loc[fill: fill + pd.Timedelta(minutes=3)]
        if len(fwd) and r["risk"] > 0:
            r["r_3"] = sign * (float(fwd.close.iloc[-1]) - entry) / r["risk"]
        else:
            r["r_3"] = np.nan
        fw = M[(M.index > fill) & (M.index <= fill + pd.Timedelta(minutes=3))]
        r["fw_3"] = sign * float(fw.delta.sum()) if len(fw) else np.nan
        rows.append(r)
        if i % 100 == 0:
            print(f"  {i}/{len(S)} fills featured", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    for p in (SUB, BARS):
        if not p.exists():
            raise SystemExit(f"missing {p} — run scripts.build_holdout_substrate first")
    S = pd.read_parquet(SUB)
    print(f"holdout substrate: {len(S)} candidate fills, {S.day.nunique()} days\n")

    print("building minute tape from the holdout footprint ...", flush=True)
    M = minute_tape()
    print(f"  {len(M):,} minutes, {M.sday.nunique()} session days\n")

    bars = pd.read_parquet(BARS)
    days = set(S.day.astype(str))
    tb = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    lo = pd.Timestamp(min(days), tz=NY) - pd.Timedelta(days=5)
    bars = bars[(tb >= lo)].reset_index(drop=True)

    # badpa_features compares trigger stamps against `fill.to_datetime64()`, which is
    # UTC-naive — so the stamps must be UTC-naive too, or the comparison raises.
    tr = pd.read_csv(TRIGS, usecols=["ts"])
    tr["day"] = tr.ts.str[:10]
    trig_times = {d: pd.to_datetime(g.ts.tolist(), utc=True).tz_localize(None).to_numpy()
                  for d, g in tr[tr.day.isin(days)].groupby("day")}
    print(f"trigger stamps for {len(trig_times)} days (for the gold TRIG check)\n")

    print("computing canon features ...", flush=True)
    F = build_features(S, M, bars, trig_times)
    F.to_parquet(ROOT / "output/holdout_trade_matrix.parquet", index=False)
    print(f"\nfeature matrix: {F.shape[0]} rows x {F.shape[1]} cols")

    missing = [c for c in ("W", "F", "Tp", "G", "C") if c not in F.columns]
    print(f"  key inputs present: "
          f"dep_thick {F.dep_thick.notna().mean()*100:.0f}%, "
          f"fill_delta_conf {F.get('fill_delta_conf', pd.Series(dtype=float)).notna().mean()*100:.0f}%, "
          f"d15 {F.d15.notna().mean()*100:.0f}%, "
          f"ent_vs_vwap_sd_dir {F.get('ent_vs_vwap_sd_dir', pd.Series(dtype=float)).notna().mean()*100:.0f}%, "
          f"netpath_30 {F.get('netpath_30', pd.Series(dtype=float)).notna().mean()*100:.0f}%")

    # build_canon reads three auxiliary matrices from FIXED paths. Rather than modify the
    # production scorer (which must stay byte-identical), write holdout versions of exactly
    # those files, run, and put the originals back. Anything else would merge the FIT
    # window's rows against holdout keys and silently produce all-NaN checks.
    F["fill"] = F.fill.dt.strftime("%Y-%m-%dT%H:%M:%S%z").str.replace(
        r"(\d{2})(\d{2})$", r"\1:\2", regex=True)          # match the stored ISO convention
    aux = {
        "output/badpa_matrix.parquet":
            F[["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]],
        "output/intrade_matrix.parquet": F[["day", "book", "fill", "r_3", "fw_3"]],
        "output/gold_quality.parquet": F[["day", "book", "fill", "bp5opp", "lon_slope_d"]],
    }
    # build_canon MERGES these in from the aux files, so they must not already be on the
    # frame — otherwise pandas suffixes them to _x/_y and the scorer reads neither.
    merged_in = ["netpath_30", "bbw_state", "churn_flow_30", "trigdens_30",
                 "r_3", "fw_3", "bp5opp", "lon_slope_d"]
    F_in = F.drop(columns=[c for c in merged_in if c in F.columns])

    backups = {}
    try:
        for path, frame in aux.items():
            p = ROOT / path
            if p.exists():
                backups[p] = p.with_suffix(".parquet.fitbak")
                p.rename(backups[p])
            frame.to_parquet(p, index=False)
        print("\napplying the canon ladder (build_canon, unchanged) ...", flush=True)
        C = build_canon(F_in, dead_zones=[(595, 600)])
    finally:
        for p, bak in backups.items():
            if p.exists():
                p.unlink()
            bak.rename(p)
        print("  (fit-window auxiliary matrices restored)")

    C.to_parquet(OUT, index=False)
    taken = C[C["size"] > 0]

    print("\n" + "=" * 70)
    print("CANON ON THE 2023/24 HOLDOUT — 1-lot basis, unfiltered by funded sizing")
    print("=" * 70)
    print(f"universe {len(C)} candidates | TAKEN {len(taken)} on {taken.day.nunique()} days")
    for yr in sorted(C.yr.unique()):
        d = C[C.yr == yr]
        t = d[d["size"] > 0]
        if not len(t):
            continue
        print(f"  {yr}: ${d.pl.sum():+9,.0f}  {len(t):>3} trades  "
              f"WR {(t.dollars > 0).mean()*100:>3.0f}%  avgR {t.R.mean():+.2f}")
    C["mo"] = C.day.astype(str).str[:7]
    mo = C.groupby("mo").pl.sum()
    print(f"\n  months green: {int((mo > 0).sum())}/{len(mo)}")
    print(mo.round(0).to_string())
    print(f"\n  TOTAL ${C.pl.sum():+,.0f}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
