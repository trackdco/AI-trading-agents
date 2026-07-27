#!/usr/bin/env python3
"""Apply the NY canon rulebook, unchanged, to a substrate — either span, same code.

ANGUS: *"over these randomly selected months, apply the rulebook, and take the trades"* and
*"to see if our mechanical strategy fits out of fit you have to trade exactly the same as our
mechanical canon."*

The holdout number is only worth reading next to a fit number produced the same way. So this
takes `--span fit` or `--span holdout`, builds canon features through `src/canon/features.py`
(the module the LIVE ingestor calls), and scores them with `scripts.canon_mechanical.build_canon`
— the production scorer, imported, never reimplemented. Every threshold comes from
`config/live_thresholds.json` and the frozen constants inside `build_canon`. Nothing here
derives a threshold from 2023/24 data; that would turn the holdout into a fit.

Run both. If the fit span reproduces roughly the armed shape and the holdout collapses, the
collapse is the regime. If BOTH collapse, the pipeline is what broke, not the strategy.

    python -m scripts.score_canon_span --span fit
    python -m scripts.score_canon_span --span holdout
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.canon_mechanical import build_canon  # noqa: E402
from src.canon.features import (  # noqa: E402
    badpa_features,
    bp5opp,
    depth_at,
    lon_slope_d,
    on_extreme_age_day,
    tape_features,
    vwap_geometry,
)
from src.engine.indicators import daily_vwap  # noqa: E402

NY = "America/New_York"

SPANS = {
    "fit": {
        "sub": "output/ny_substrate_fit.parquet",
        "bars": ["data/reference/nq_1m_master.parquet",
                 "data/reference/nq_1m_feb_jul2026.parquet"],
        "trigs": ["output/triggers_hist2326_ob_v2.csv", "output/triggers_feb_ob_v2.csv",
                  "output/triggers_marjul_ob_v2.csv"],
        "depth": ["data/reference/depth_2025", "data/reference/depth_2026"],
        "tape": "output/fp_minutes.parquet",
    },
    "holdout": {
        "sub": "output/ny_substrate_holdout.parquet",
        "bars": ["data/reference/nq_1m_master.parquet"],
        "trigs": ["output/triggers_hist2326_ob_v2.csv"],
        "depth": ["data/reference/depth_2023_24"],
        "tape": "data/reference/cvd/footprint_holdout_*.parquet",
    },
}

# session windows, NY minutes-of-day (scripts/dayflow_features.win_masks)
W_LON = (2 * 60, 8 * 60)
W_PM = (8 * 60, 9 * 60 + 30)


def sgn_conf(v, direction) -> int:
    """1 when the signed value agrees with the trade's direction (trade_angles.sgn_conf)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0
    return int((v > 0 and direction == "long") or (v < 0 and direction == "short"))


def minute_tape(spec: dict) -> pd.DataFrame:
    """Per-minute b/a/vol/delta/vwp. fp_minutes is already in this shape; the holdout
    footprints are raw tick-level and get folded down to it here — same columns either way."""
    tape = spec["tape"]
    if tape.endswith(".parquet") and "*" not in tape:
        M = pd.read_parquet(ROOT / tape)
        M.index = pd.DatetimeIndex(M.index)
        M = M.sort_index()
    else:
        frames = []
        for p in sorted(glob.glob(str(ROOT / tape))):
            d = pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"])
            d["volume"] = d["volume"].astype("int64")   # uint32 wraps on the B-A subtraction
            ny = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert(NY)
            f = pd.DataFrame({"mi": ny.dt.floor("min"), "price": d.price.to_numpy(),
                              "side": d.side.to_numpy(), "volume": d.volume.to_numpy()})
            f["pv"] = f.price * f.volume
            g = (f.groupby(["mi", "side"])
                  .agg(vol=("volume", "sum"), pv=("pv", "sum")).unstack("side"))
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


def depth_file(dirs, day: str) -> Path | None:
    for d in dirs:
        f = ROOT / d / f"nq_depth_{day}_ny.csv"
        if f.exists():
            return f
    return None


def build_features(S, M, bars, trig_times, depth_dirs) -> pd.DataFrame:
    """One canon feature row per candidate fill, via src/canon/features.py."""
    bars = bars.copy()
    bt = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    ind = daily_vwap(bars)
    bars = bars.assign(mi=bt.dt.floor("min"), hm=bt.dt.hour * 60 + bt.dt.minute,
                       vw=ind["vwap"].to_numpy(), up1=ind["upper_1"].to_numpy())
    bars_i = bars.set_index("mi").sort_index()

    dep_cache: dict[str, pd.DataFrame | None] = {}
    rows = []
    for i, t in enumerate(S.itertuples(), 1):
        fill = pd.Timestamp(t.fill)
        fill = (fill.tz_localize(NY) if fill.tzinfo is None else fill).tz_convert(NY)
        day, direction, entry = str(t.day)[:10], t.direction, float(t.entry)
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
        # GOLD's AGE input is on_extreme_age_DAY over the COMPLETED 18:00-08:00 overnight
        # tape — NOT on_extreme_age_trade, which is London's per-trade wall-clock form.
        # src/canon/features.py warns they disagree on 60/60 days; calling the wrong one
        # made AGE fire at 14% against 47% in fit, and that was the bug.
        hm_s = sday_m.index.hour * 60 + sday_m.index.minute
        r["on_extreme_age"] = on_extreme_age_day(sday_m[(hm_s >= 1080) | (hm_s < 480)])

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
        if day not in dep_cache:
            f = depth_file(depth_dirs, day)
            if f is None:
                dep_cache[day] = None
            else:
                dd = pd.read_csv(f)
                dd["ts"] = pd.to_datetime(dd.ts)
                dep_cache[day] = dd
        if dep_cache[day] is not None:
            r.update(depth_at(dep_cache[day], fill, entry, direction))

        if len(upto):
            r["bp5opp"] = bp5opp(upto, direction, fill)
            r["lon_slope_d"] = lon_slope_d(sd if len(sd) else upto, direction)

        # --- Layer 2d inputs: where the trade stands 3 minutes after the fill ---
        sign = 1.0 if direction == "long" else -1.0
        fwd = bars_i.loc[fill: fill + pd.Timedelta(minutes=3)]
        r["r_3"] = (sign * (float(fwd.close.iloc[-1]) - entry) / r["risk"]
                    if len(fwd) and r["risk"] > 0 else np.nan)
        fw = M[(M.index > fill) & (M.index <= fill + pd.Timedelta(minutes=3))]
        r["fw_3"] = sign * float(fw.delta.sum()) if len(fw) else np.nan
        rows.append(r)
        if i % 200 == 0:
            print(f"  {i}/{len(S)} fills featured", flush=True)
    return pd.DataFrame(rows)


def score(F: pd.DataFrame) -> pd.DataFrame:
    """Run build_canon on F, swapping in matching auxiliary matrices.

    build_canon reads three auxiliary matrices from FIXED paths. Rather than modify the
    production scorer (which must stay byte-identical), write span-matched versions of
    exactly those files, run, and put the originals back. Anything else merges one span's
    rows against the other's keys and silently produces all-NaN checks.
    """
    F = F.copy()
    F["fill"] = F.fill.dt.strftime("%Y-%m-%dT%H:%M:%S%z").str.replace(
        r"(\d{2})(\d{2})$", r"\1:\2", regex=True)          # match the stored ISO convention
    aux = {
        "output/badpa_matrix.parquet":
            F[["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]],
        "output/intrade_matrix.parquet": F[["day", "book", "fill", "r_3", "fw_3"]],
        "output/gold_quality.parquet": F[["day", "book", "fill", "bp5opp", "lon_slope_d"]],
    }
    # build_canon MERGES these in, so they must not already be on the frame — otherwise
    # pandas suffixes them to _x/_y and the scorer reads neither.
    merged_in = ["netpath_30", "bbw_state", "churn_flow_30", "trigdens_30",
                 "r_3", "fw_3", "bp5opp", "lon_slope_d"]
    F_in = F.drop(columns=[c for c in merged_in if c in F.columns])

    backups = {}
    try:
        for path, frame in aux.items():
            p = ROOT / path
            if p.exists():
                backups[p] = p.with_suffix(".parquet.spanbak")
                p.rename(backups[p])
            frame.to_parquet(p, index=False)
        print("\napplying the canon ladder (build_canon, unchanged) ...", flush=True)
        # NO dead_zones — canon_mechanical.main() calls build_canon(T) with none, and the
        # armed +$55,989.81 came from that call. Passing one here would be a different book.
        return build_canon(F_in)
    finally:
        for p, bak in backups.items():
            if p.exists():
                p.unlink()
            bak.rename(p)
        print("  (original auxiliary matrices restored)")


def report(C: pd.DataFrame, span: str) -> None:
    """`pl` here is dollars x ladder size x governor — the 1-LOT NQ basis, not the funded
    account. The arming +$55,989.81 is funded micros (`scripts.baseline_dollar_risk.size_book`:
    risk_$ = min(400, conviction x 200), micros = round(risk_$ / (stop_pts x $2))), which runs
    about 1.56x smaller. Both spans are reported on the same basis so the comparison holds;
    `scripts.holdout_verdict` restates it in funded dollars."""
    taken = C[C["size"] > 0]
    print("\n" + "=" * 74)
    print(f"NY CANON — {span.upper()} SPAN — 1-lot x ladder size (see holdout_verdict for funded)")
    print("=" * 74)
    print(f"universe {len(C)} candidates | TAKEN {len(taken)} on {taken.day.nunique()} days")
    for w in ("pre", "gold"):
        d, t = C[C.win_ == w], taken[taken.win_ == w]
        if not len(t):
            continue
        print(f"  {w:>4}: ${d.pl.sum():+9,.0f}  {len(t):>3} trades  "
              f"WR {(t.dollars > 0).mean()*100:>3.0f}%  avgR {t.R.mean():+.2f}")
    for yr in sorted(C.yr.unique()):
        d = C[C.yr == yr]
        t = d[d["size"] > 0]
        if not len(t):
            continue
        cum = t.groupby("day").pl.sum().cumsum()
        dd = (cum.cummax() - cum).max() if len(cum) else 0
        print(f"  {yr}: ${d.pl.sum():+9,.0f}  {len(t):>3} trades  "
              f"WR {(t.dollars > 0).mean()*100:>3.0f}%  maxDD ${dd:,.0f}")
    C = C.assign(mo=C.day.astype(str).str[:7])
    mo = C.groupby("mo").pl.sum()
    print(f"\n  months green: {int((mo > 0).sum())}/{len(mo)}")
    print(mo.round(0).to_string())
    print(f"\n  TOTAL ${C.pl.sum():+,.0f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), required=True)
    a = ap.parse_args()
    spec = SPANS[a.span]

    sub = ROOT / spec["sub"]
    if not sub.exists():
        raise SystemExit(f"missing {sub} — run scripts.build_ny_substrate --span {a.span} first")
    S = pd.read_parquet(sub)
    print(f"{a.span} substrate: {len(S)} candidate fills, {S.day.nunique()} days\n")

    print("building the minute tape ...", flush=True)
    M = minute_tape(spec)
    print(f"  {len(M):,} minutes, {M.sday.nunique()} session days\n")

    bars = pd.concat([pd.read_parquet(ROOT / b).drop(columns=["roll"], errors="ignore")
                      for b in spec["bars"]], ignore_index=True)
    bars = bars.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    days = set(S.day.astype(str).str[:10])
    lo = pd.Timestamp(min(days), tz=NY) - pd.Timedelta(days=5)
    bars = bars[pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY) >= lo].reset_index(drop=True)

    # badpa_features compares trigger stamps against `fill.to_datetime64()`, which is
    # UTC-naive — so the stamps must be UTC-naive too, or the comparison raises.
    tr = pd.concat([pd.read_csv(ROOT / t, usecols=["ts"]) for t in spec["trigs"]],
                   ignore_index=True)
    tr["day"] = tr.ts.str[:10]
    trig_times = {d: pd.to_datetime(g.ts.tolist(), utc=True).tz_localize(None).to_numpy()
                  for d, g in tr[tr.day.isin(days)].groupby("day")}
    print(f"trigger stamps for {len(trig_times)} days (for the gold TRIG check)\n")

    print("computing canon features ...", flush=True)
    F = build_features(S, M, bars, trig_times, spec["depth"])
    F.to_parquet(ROOT / f"output/ny_matrix_{a.span}.parquet", index=False)
    print(f"\nfeature matrix: {F.shape[0]} rows x {F.shape[1]} cols")
    print(f"  coverage: depth {F.dep_thick.notna().mean()*100:.0f}%, "
          f"d15 {F.d15.notna().mean()*100:.0f}%, "
          f"netpath_30 {F.get('netpath_30', pd.Series(dtype=float)).notna().mean()*100:.0f}%, "
          f"AGE-fires {F.on_extreme_age.notna().mean()*100:.0f}%")

    C = score(F)
    C.to_parquet(ROOT / f"output/ny_canon_{a.span}.parquet", index=False)
    report(C, a.span)
    print(f"\nwrote output/ny_canon_{a.span}.parquet")


if __name__ == "__main__":
    main()
