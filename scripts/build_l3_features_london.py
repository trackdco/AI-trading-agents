#!/usr/bin/env python3
"""L3 LONDON Stage A — the feature matrix for every L2 outcome.

Authorised by docs/PREREG-london-canon-rebuild.md.

ANGUS 2026-08-05 on sequencing:

    "look at the raw data like we are doing, and try seperate winners from losers before
     putting stop caps and other things... the process u go through to get there should be
     done in the right sequence"

So this runs on the FULL 1,239-outcome population. The 9.5pt risk-band result from L2 is
L4 policy and is deliberately NOT applied here — filtering to it first would bake an L4
decision into the feature evidence and every lift below would be measured on a population
already selected for being profitable.

THREE FAMILIES, all strictly pre-fill:

  tape/flow   d5/d15/d30 + confirmations, fill-minute delta, overnight and ASIA CVD,
              churn, delta z-score. Windows open at the 18:00 ET session anchor and close
              at fill minus one minute.
  geometry    entry vs the daily-VWAP band, overnight-range position, extreme age, netpath,
              level churn, VWAP crosses, wickiness, BB width state.
  depth       NEW HERE, and read at THREE anchors. `t_*` is the book at ORDER PLACEMENT
              (the trigger candle's close) and is the one that can be traded -- see the
              long note in features_one(). The fill-anchored pair is kept only so the
              contamination that motivated the move stays auditable.
              `london_matrix.py` says "EXCEPT depth (heatmap not yet purchased)".
              It has been purchased: data/reference/depth_london, 295 condensed MBP-10 days.
              Read via scripts/london_depth.load_day, last snapshot AT OR BEFORE the fill
              minute — never the fill minute's own later state, which is the lookahead that
              killed NYA-LVL-01.

GATE (--gate): the tape and geometry columns must reproduce `output/london_matrix.parquet`
to 1e-6 on matched fills, joined on (day, fill minute, direction, ENTRY). Entry is in the
key deliberately — burn-list item 4: same-minute sibling triggers share a fill minute with
different limits, and a join without entry compares different trades. Depth columns are
new and excluded from the gate with that reason stated.

    python -m scripts.build_l3_features_london --gate
    python -m scripts.build_l3_features_london --run [--procs 4]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_depth import depth_at, load_day  # noqa: E402
from scripts.score_canon_span import minute_tape  # noqa: E402
from src.engine.indicators import daily_vwap  # noqa: E402

NY = "America/New_York"
PREREG = "docs/PREREG-london-canon-rebuild.md"
IN = ROOT / "output/l2_outcomes_london_fit.parquet"
OUT = ROOT / "output/l3_features_london_fit.parquet"
DEPTH_DIR = ROOT / "data/reference/depth_london"
BARS = [("data/reference/nq_1m_master.parquet", "2025-05-20"),
        ("data/reference/nq_1m_feb_jul2026.parquet", None)]


def load_bars() -> pd.DataFrame:
    frames = []
    for path, since in BARS:
        b = pd.read_parquet(ROOT / path).drop(columns=["roll"], errors="ignore")
        if since:
            b = b[b.ts_event >= pd.Timestamp(since, tz=NY)]
        frames.append(b)
    bars = (pd.concat(frames, ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    ind = daily_vwap(bars, bands=[1, 2])
    return bars.assign(mi=bars.ts_event.dt.tz_convert(NY), vw=ind["vwap"].values,
                       sd1u=ind["upper_1"].values, sd1d=ind["lower_1"].values)


def features_one(f: pd.Timestamp, sgn: int, entry: float, M, B, trig_arr,
                 dep, trig_ts: pd.Timestamp | None = None) -> dict:
    """One trade's features. EVERY window ends at fill-minus-one-minute.

    Formulas are lifted expression-for-expression from scripts/london_matrix.py so the
    --gate reproduction to 1e-6 is meaningful; the depth block is the only new code.
    """
    out: dict = {}
    sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)

    # --- tape / flow, strictly pre-fill ---------------------------------------
    g = M.loc[sess0: f - pd.Timedelta(minutes=1)]
    if len(g) >= 60:
        for k in (5, 15, 30):
            dk = g.delta.tail(k).sum()
            out[f"d{k}"] = dk
            out[f"d{k}_conf"] = int(np.sign(dk) == sgn)
        fd = g.delta.iloc[-1]
        out["fill_delta"] = fd
        out["fill_delta_conf"] = int(np.sign(fd) == sgn)
        out["fill_vol_rel"] = g.vol.iloc[-1] / max(g.vol.median(), 1)
        out["cvd_ON_sofar"] = g.delta.sum()
        out["conf_ON_sofar"] = int(np.sign(g.delta.sum()) == sgn)
        asia = g.loc[: sess0 + pd.Timedelta(hours=8)]            # 18:00-02:00 ET
        out["cvd_ASIA"] = asia.delta.sum() if len(asia) > 60 else np.nan
        out["conf_ASIA"] = (int(np.sign(out["cvd_ASIA"]) == sgn)
                            if out["cvd_ASIA"] == out["cvd_ASIA"] else np.nan)
        g30 = g.tail(30)
        out["churn_flow_30"] = abs(g30.delta.sum()) / max(g30.vol.sum(), 1)
        roll = g.delta.rolling(15).sum().dropna()
        out["deltaz_15"] = (g.delta.tail(15).sum() / max(roll.std(), 1)
                            if len(roll) > 30 else np.nan)

    # --- bars / geometry / price action, strictly pre-fill --------------------
    try:
        w = B.loc[sess0: f - pd.Timedelta(minutes=1)]
        if len(w) >= 90:
            c = w.close
            out["ent_on_pos"] = (entry - w.low.min()) / max(w.high.max() - w.low.min(), 1e-9)
            out["on_range"] = w.high.max() - w.low.min()
            ext_t = (w.high.idxmax() if ((entry - w.low.min()) > (w.high.max() - entry))
                     else w.low.idxmin())
            out["on_extreme_age"] = (f - ext_t).total_seconds() / 60
            sd = (w.sd1u.iloc[-1] - w.vw.iloc[-1])
            out["ent_vs_vwap_sd"] = (entry - w.vw.iloc[-1]) / max(sd, 1e-9)
            out["ent_vs_vwap_sd_dir"] = out["ent_vs_vwap_sd"] * sgn
            w30 = w.tail(30)
            c30 = w30.close
            out["netpath_30"] = (abs(c30.iloc[-1] - c30.iloc[0])
                                 / max(c30.diff().abs().sum(), 1e-9))
            out["rng_30"] = w30.high.max() - w30.low.min()
            s_ = np.sign(c30 - entry)
            out["lvl_churn_30"] = int((pd.Series(s_).diff().abs() > 0).sum())
            sv = np.sign(c30 - w30.vw)
            out["vwap_cross_30"] = int((pd.Series(sv).diff().abs() > 0).sum())
            out["vwap_slope_30"] = abs(w30.vw.iloc[-1] - w30.vw.iloc[0])
            hl = (w30.high - w30.low).replace(0, np.nan)
            out["wicky_10"] = float(((hl - (w30.close - w30.open).abs()) / hl).tail(10).mean())
            out["indec_30"] = float(((w30.close - w30.open).abs() / hl < 0.3).mean())
            std20 = c.rolling(20).std()
            out["bbw_state"] = (float(std20.iloc[-1] / max(std20.median(), 1e-9))
                                if len(c) > 60 else np.nan)
    except Exception:
        pass

    if trig_arr is not None:
        out["trigdens_30"] = int(((trig_arr >= (f - pd.Timedelta(minutes=30)).to_datetime64())
                                  & (trig_arr < f.to_datetime64())).sum())

    # --- depth ---------------------------------------------------------------
    # CAUSALITY, VERIFIED NOT ASSUMED (2026-08-05) -- AND THE CONCLUSION WAS WRONG.
    # SUPERSEDED 2026-08-06, see docs/FINDING-london-depth-timestamp-lookahead.md.
    #
    # The original audit asked exactly the right question -- is the minute boundary an
    # INSTANT at T, or a roll-up of the minute that follows it? -- and its measurements
    # were correct and reproduce today:
    #
    #     depth mid at T vs close of bar T    -> median |err| 0.25 pt, 96% within 1pt
    #     depth mid at T vs open  of bar T    -> median |err| 3.62 pt, 17% within 1pt
    #     depth mid at T vs close of bar T+1  -> median |err| 3.75 pt, 15% within 1pt
    #
    # It concluded "the snapshot is the INSTANTANEOUS book at T, no lookahead here" from
    # a stated premise about a DIFFERENT file: "close-labeled 1m bars (bar stamped T
    # covers (T-1min, T])". The bars are START-labelled -- see
    # data/reference/parity_slice_feb2026.md, and measured: footprint trades stamped
    # ts_minute=T fall inside bar ts_event=T on 98.1% of 42,230 minutes, against 17.5%
    # for the alternative. Under the correct premise the SAME numbers say the opposite:
    # `close of bar T` is the price at T+1min, so a depth mid at label T matching it
    # means the snapshot is the book at T+1min.
    #
    # Settled without bars at all: ts_recv - ts_event has median 59.889s against ~13us of
    # capture latency. ts_event is FLOORED to the minute at extraction. The row labelled T
    # is the book at ~T+59.9s, and reading label M for a decision at M is a ~60s lookahead.
    #
    # scripts.london_depth.load_day now indexes by ts_recv, so every anchor below shifts
    # to true observation time. Consequence for the three anchors: `t_*` (trigger close)
    # needs the row labelled trig_ts-1min, which is what the corrected loader returns;
    # the old `p1_*` fallback was accidentally the closest of the three to honest.
    #
    # Default therefore reads at the fill-minute boundary (freshest legitimate book, and it
    # reproduces london_matrix so downstream comparisons stay meaningful). The one-minute-
    # earlier book is carried alongside as `p1_*` so the standing check adopted from
    # NYA-LVL-01 -- any depth feature beating baseline by >~5pp is recomputed one bar
    # earlier BEFORE it is reported -- is answerable without a re-run.
    if dep is not None:
        side = "long" if sgn > 0 else "short"
        out.update(depth_at(dep, f, entry, side))
        out.update({f"p1_{k}": v for k, v in
                    depth_at(dep, f - pd.Timedelta(minutes=1), entry, side).items()})
        # `t_` -- THE BOOK AT ORDER PLACEMENT. ANGUS 2026-08-05, and it supersedes both
        # of the above as the feature that can actually be traded:
        #
        #   "live book will look at the literal seconds, not minutes. on a limit order, of
        #    course the minute before entry, flow will probably be against us because it is
        #    opposing our direction to get filled before running the way we want it to."
        #
        # Exactly right, and it invalidates the fill-anchored pair. The fill-bar CLOSE
        # contains the answer; the fill-bar OPEN is adverse BY CONSTRUCTION, because a
        # limit fill requires price to travel toward us. Neither brackets the truth.
        #
        # And at-fill book state was never actionable anyway: you cannot cancel an order at
        # the instant it fills. The moment a limit trader can act on is when the order is
        # PLACED -- the trigger candle's close. That book is unambiguous, strictly prior to
        # the limit existing, free of approach bias, and measurable with the minute archive
        # we already hold.
        if trig_ts is not None:
            out.update({f"t_{k}": v for k, v in
                        depth_at(dep, trig_ts, entry, side).items()})
    return out


def build(D: pd.DataFrame, quiet: bool = False) -> pd.DataFrame:
    M = minute_tape({"tape": "output/fp_minutes.parquet"})
    B = load_bars().set_index("mi").sort_index()
    L0 = pd.read_parquet(ROOT / "output/l0_triggers_london_fit_std.parquet")
    lts = pd.to_datetime(L0.ts, utc=True, format="mixed").dt.tz_convert(NY)
    tby = {d: g.sort_values().values for d, g in lts.groupby(lts.dt.strftime("%Y-%m-%d"))}

    rows, dep, dep_day, missing = [], None, None, set()
    for i, t in enumerate(D.itertuples()):
        f = pd.Timestamp(t.fill_ts)
        f = (f.tz_localize(NY) if f.tzinfo is None else f.tz_convert(NY)).floor("min")
        if t.day != dep_day:                       # rows are day-sorted; one load per day
            dep_day = t.day
            dep = load_day(t.day, DEPTH_DIR)
            if dep is None:
                missing.add(t.day)
        tt = pd.Timestamp(t.ts)
        tt = (tt.tz_localize(NY) if tt.tzinfo is None else tt.tz_convert(NY)).floor("min")
        rows.append(features_one(f, 1 if t.direction == "long" else -1,
                                 float(t.entry), M, B, tby.get(t.day), dep, tt))
        if not quiet and (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(D)}", flush=True)
    X = pd.DataFrame(rows, index=D.index)
    if missing and not quiet:
        print(f"  days with no depth file: {len(missing)} "
              f"(features present, depth columns NaN — they stand down, never impute)")
    return pd.concat([D.reset_index(drop=True), X.reset_index(drop=True)], axis=1)


def gate() -> bool:
    """Reproduce london_matrix.parquet to 1e-6 on matched fills.

    Join key includes ENTRY (burn-list item 4): same-minute sibling triggers share a fill
    minute with different limits, so a join without it compares different trades.
    """
    old = pd.read_parquet(ROOT / "output/london_matrix.parquet")
    ofill = pd.to_datetime(old.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    old = old.assign(_k=list(zip(old.day.astype(str).str[:10], ofill,
                                 old.direction, old.entry.round(2))))
    D = pd.read_parquet(IN)
    D = D[D.status == "outcome"].copy()
    nfill = pd.to_datetime(D.fill_ts, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
    D = D.assign(_k=list(zip(D.day.astype(str), nfill, D.direction, D.entry.round(2))))
    shared = set(old._k) & set(D._k)
    if not shared:
        print("GATE INCONCLUSIVE — no matched fills between L2 and the old london_matrix")
        return False
    sub = D[D._k.isin(shared)].head(400).sort_values(["day", "fill_ts"]).reset_index(drop=True)
    print(f"matched fills available {len(shared):,}; gating on {len(sub)}", flush=True)
    new = build(sub, quiet=True)
    om = old.drop_duplicates("_k").set_index("_k")

    # outcome columns are not features: the old matrix's trades came through a DIFFERENT
    # simulate() config (caps, risk gates, the NY news veto), so their exits legitimately
    # differ. Gating on them would compare policies, not feature code.
    OUTCOME = {"day", "direction", "entry", "stop", "pattern", "tf", "risk", "R",
               "exit_price", "exit_ts", "dollars", "dollars_1lot", "pts", "target_level",
               "working_target", "hold_min"}
    cols = [c for c in new.columns if c in om.columns and c not in OUTCOME
            and pd.api.types.is_numeric_dtype(new[c])]
    cols = [c for c in cols if c != "trigdens_30"]      # census stamps differ, by design
    ok, checked = True, 0
    for c in cols:
        a = new[c].to_numpy(float)
        b = om.loc[new._k, c].to_numpy(float)
        m = ~(np.isnan(a) & np.isnan(b))
        if m.sum() == 0:
            continue
        checked += 1
        bad = int((np.abs(np.nan_to_num(a[m]) - np.nan_to_num(b[m])) > 1e-6).sum())
        if bad:
            ok = False
            print(f"  MISMATCH {c}: {bad}/{int(m.sum())} rows differ")
    print(f"columns compared: {checked} (trigdens_30 excluded — fed from the parity-gated "
          f"L0 census, not the old CSVs; depth columns are new)")
    print("gate OK — tape and geometry features reproduce london_matrix to 1e-6"
          if ok else "GATE FAILED — do not build the trial on these features")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--entry", default="E3", choices=["E3", "EC", "E4"],
                    help="which entry arm's L2 book to feature")
    a = ap.parse_args()
    if a.gate:
        return 0 if gate() else 1
    if not a.run:
        ap.error("--run or --gate")

    src = (IN if a.entry == "E3"
           else IN.with_name(f"l2_outcomes_london_fit_{a.entry}.parquet"))
    D = pd.read_parquet(src)
    D = D[D.status == "outcome"].sort_values(["day", "fill_ts"]).reset_index(drop=True)
    print(f"L3 London — featuring {len(D):,} outcomes over {D.day.nunique()} sessions",
          flush=True)
    F = build(D)
    out = (OUT if a.entry == "E3"
           else OUT.with_name(f"l3_features_london_fit_{a.entry}.parquet"))
    F.to_parquet(out, index=False)
    dep_cols = [c for c in F.columns if c.startswith("dep_")]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F):,} rows x {F.shape[1]} cols")
    print(f"depth resolved on {int(F[dep_cols[0]].notna().sum()):,} of {len(F):,} "
          f"({F[dep_cols[0]].notna().mean():.0%})" if dep_cols else "no depth columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
