#!/usr/bin/env python3
"""L1 — LONDON entry mechanics over the L0 census: which candidates does the market let you in.

Mirrors scripts/build_l1_fills.py with the London window rule. Same guarantee: ONE WALK, ALL
POLICIES. Cancel rules only ever REMOVE fills, so L1 walks every trigger once with NO cancel
enforced and records the EVENTS each rule keys on. Rules become derived boolean columns and
any future cancel policy is a filter over this artifact, never a rebuild:

  arm_none    filled                                    LONDON'S SHIPPING RULE (see below)
  arm_dist22  filled & max_away_before_fill < 22        what the OLD substrate actually ran
  arm_struct  filled & struct_event != 'rejected'       the structural-cancel rule

THE SHIPPING RULE FOR LONDON IS arm_none, AND THAT IS A CHANGE FROM THE OLD BOOK.
ANGUS ruling (handoff §5, "ships; verify on London L1 data"): no distance cancel — "the order
lives while its session window lives". But config/strategy.yaml carries
`cancel_if_runs_points: 22.0` globally, and scripts/london_substrate.py builds its config from
that base without overriding it. So output/london_substrate.parquet — and therefore
output/london_canon_book.parquet on top of it — was built WITH a 22pt distance cancel, which
the ruling supersedes. arm_dist22 is retained precisely to measure what that cancel deleted
from the London population; main() reports the delta. Measured on NY/gold before this was
built: the 22pt cancel keeps the worse half of fills (27% WR, -0.19R) and kills the better
half (36% WR, +0.08R). Whether London behaves the same is an L2 question — L1 only has to
preserve the evidence to answer it.

WINDOW / EXPIRY. Orders expire at the LONDON window end, per-day via
run_triggers_london.london_window_et — 05:00 ET normally, 06:00 ET on the ~20 fit-span days
when UK and US clocks disagree. A fixed ET expiry would be wrong on every one of those days,
in the direction of granting an extra hour of fill opportunity.

INDEPENDENT WALKS, DELIBERATELY. simulate() works one order at a time, so a trigger that fires
while an order rests is silently skipped — execution capacity shaping the population, the same
defect class as a trade cap (burn list #5). L1 walks each trigger as if it were the only
order; L4's chronological selection re-imposes one-position-at-a-time when it CHOOSES trades.

E3 LIMITS ONLY (ANGUS: "i never market order"). The E4 momentum book that london_substrate
also built is deliberately not rebuilt here.

FILL MODEL (mirrored from engine.py, gate-verified): limit tick-rounded at placement; first
evaluated on the bar AFTER the trigger bar; fill when the bar trades 1 tick through; gap-open
fills at the open, never better than the first traded price.

    python -m scripts.build_l1_fills_london --gate       # run FIRST — engine-subset fidelity
    python -m scripts.build_l1_fills_london --span fit
    python -m scripts.build_l1_fills_london --span holdout
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_triggers_london import london_window_et  # noqa: E402

NY = "America/New_York"
TICK = 0.25
THROUGH = 1 * TICK              # cfg.through_ticks * cfg.tick
T_CANCEL = 22.0                 # recorded as a column, NEVER enforced in the walk
STRUCT_ACCEPT = 5.0             # pts traded beyond a level = acceptance, not a rejection
STRUCT_REJECT = 8.0             # pts back off a touched level = "rejects hard"

MASTER = ROOT / "data/reference/nq_1m_master.parquet"
# One normal-window day and one DST-shifted day: a gate that skips the shifted case would not
# exercise the window rule at all, which is the whole London-specific risk in this layer.
GATE_DAYS = ["2025-09-17", "2025-10-28"]


def load_bars() -> pd.DataFrame:
    """Master alone — verified byte-identical to nq_1m_feb_jul2026 on all 161,525 overlapping
    2026 rows during L0, so the concat+dedup the NY loader needs is a no-op here."""
    b = pd.read_parquet(MASTER).drop(columns=["roll"], errors="ignore")
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.sort_values("mi").reset_index(drop=True)


def walk_one(bars: dict, t: dict) -> dict:
    """One trigger, one independent walk from its close time to the London window end."""
    s = 1 if t["direction"] == "long" else -1
    # engine parity: limit is tick-rounded at ORDER PLACEMENT, and the working order is first
    # evaluated on the bar AFTER the trigger bar — searchsorted 'right'.
    lim = round(round(t["entry_ref"] / TICK) * TICK, 10)
    close = t["close"]
    mi, o, h, lo = bars["mi"], bars["o"], bars["h"], bars["l"]
    i0 = int(np.searchsorted(mi, np.datetime64(t["ts64"]), side="right"))

    # away-side structural levels: at/beyond the trigger close in the run-away direction
    levels = [(n, p, ty) for n, p, ty in json.loads(t["level_stack"] or "[]")
              if s * (p - close) >= 0]
    touched = [False] * len(levels)
    struct_event = ""            # '' | 'rejected' | 'broke'
    struct_name = struct_type = ""
    struct_price = np.nan
    struct_ts = None

    max_away = 0.0
    fill_i = -1
    for i in range(i0, len(mi)):
        hi_i, lo_i = h[i], lo[i]
        max_away = max(max_away, (hi_i - lim) if s == 1 else (lim - lo_i))
        if not struct_event:
            for j, (n, p, ty) in enumerate(levels):
                if not touched[j] and lo_i <= p <= hi_i:
                    touched[j] = True
                if touched[j]:
                    beyond = (hi_i - p) if s == 1 else (p - lo_i)
                    back = (p - lo_i) if s == 1 else (hi_i - p)
                    if beyond >= STRUCT_ACCEPT:
                        struct_event, struct_name, struct_type = "broke", n, ty
                    elif back >= STRUCT_REJECT:
                        struct_event, struct_name, struct_type = "rejected", n, ty
                    if struct_event:
                        struct_price, struct_ts = p, mi[i]
                        break
        filled = (lo_i <= lim - THROUGH) if s == 1 else (hi_i >= lim + THROUGH)
        if filled:
            fill_i = i
            break

    out = {"max_away_before_fill": round(max_away, 2),
           "struct_event": struct_event, "struct_level": struct_name,
           "struct_level_type": struct_type, "struct_level_price": struct_price,
           "struct_ts": str(struct_ts) if struct_ts is not None else "",
           "n_away_levels": len(levels)}
    if fill_i < 0:
        out |= {"status": "expired", "fill_ts": "", "fill_px": np.nan, "fill_hm": -1,
                "mins_to_fill": -1}
        return out
    fp = min(lim, o[fill_i]) if s == 1 else max(lim, o[fill_i])
    fts = pd.Timestamp(mi[fill_i])
    if fts.tzinfo is None:
        fts = fts.tz_localize("UTC").tz_convert(NY)
    out |= {"status": "filled", "fill_ts": fts.isoformat(), "fill_px": round(float(fp), 2),
            "fill_hm": fts.hour * 60 + fts.minute,
            "mins_to_fill": int((mi[fill_i] - np.datetime64(t["ts64"]))
                                / np.timedelta64(1, "m"))}
    return out


def run(trigs: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    # trigger ts are ET ISO strings whose UTC offset flips across DST — parse via UTC
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(ts_et=ts, day=ts.dt.strftime("%Y-%m-%d"),
                         trig_hm=ts.dt.hour * 60 + ts.dt.minute)
    bday = bars.mi.dt.strftime("%Y-%m-%d")
    rows = []
    for day, g in trigs.groupby("day", sort=True):
        _, end = london_window_et(day)          # DST-correct expiry, never a fixed ET hour
        db = bars[(bday == day) & (bars.mi <= end)]
        if db.empty:
            continue
        arrs = {"mi": db.mi.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(),
                "o": db.open.to_numpy(float), "h": db.high.to_numpy(float),
                "l": db.low.to_numpy(float)}
        for r in g.itertuples():                # ts_et is not underscore-prefixed (burn list #2)
            t = {"direction": r.direction, "entry_ref": float(r.entry_ref),
                 "close": float(r.close), "level_stack": r.level_stack,
                 "ts64": r.ts_et.tz_convert("UTC").tz_localize(None)}
            rows.append({
                "day": day, "ts": r.ts, "tf": r.tf, "direction": r.direction,
                "kind": r.kind, "pattern": r.pattern, "htf_flag": r.htf_flag,
                "trig_hm": int(r.trig_hm), "win_end_hm": end.hour * 60 + end.minute,
                "dst_shifted": end.hour == 6,
                "limit": round(round(r.entry_ref / TICK) * TICK, 10),
                "stop": round(round(r.stop_ref / TICK) * TICK, 10),
                "risk_intended": round(abs(round(round(r.entry_ref / TICK) * TICK, 10)
                                           - round(round(r.stop_ref / TICK) * TICK, 10)), 2),
                "close": float(r.close), "confluence_count": r.confluence_count,
                "cluster_members": r.cluster_members, "level_stack": r.level_stack,
                **walk_one(arrs, t)})
        print(f"  {day}: {len(g):>3} triggers", flush=True)
    F = pd.DataFrame(rows)
    F["arm_none"] = F.status == "filled"                                   # London ships this
    F["arm_dist22"] = F.arm_none & (F.max_away_before_fill < T_CANCEL)     # the old book's rule
    F["arm_struct"] = F.arm_none & (F.struct_event != "rejected")
    return F


def _london_cfg(day: str, t_cancel: float):
    """Uncapped London E3/V8 config for `day`, with the window set from the DAY'S OWN mapping.

    win_start/win_end are wall-clock `time` objects, so they cannot express a window that
    shifts with DST — london_substrate.py handles this by grouping days into 03:00-05:00 and
    04:00-06:00 buckets. Per-day is the same thing without the bucketing.

    Uncapping (max_trades_per_day, stop floors, rulebook gates) only ever ADDS engine fills,
    which strengthens a subset gate: every extra engine fill is another row L1 must reproduce.
    """
    from datetime import time as dtime

    from src.backtest.engine import load_backtest_config
    start, end = london_window_et(day)
    return load_backtest_config().model_copy(update={
        "win_start": dtime(start.hour, start.minute),
        "win_end": dtime(end.hour, end.minute),
        "t_cancel": t_cancel,
        "mgmt_variant": "V8",                 # the E3 book (scripts/grade_window_cap.books)
        "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None,
        "require_bb_vwap": False, "require_vwap_touch": False})


def gate() -> None:
    """GATE — engine subset-reproduction, run BEFORE building anything on top of L1.

    Engine fills are a SUBSET of L1's (its one-order-at-a-time serialization skips triggers L1
    walks independently). Every engine fill must match an L1 row on trigger ts, fill minute and
    entry price, and must not land on a row the corresponding arm excludes.

    Run TWICE, because the cancel rule is exactly what changes for London:
      t_cancel off  -> engine fills must be a subset of arm_none    (the ANGUS shipping rule)
      t_cancel 22   -> engine fills must be a subset of arm_dist22  (what the old book ran)
    Passing both proves the walk reproduces the engine under either policy, which is what makes
    the derived columns trustworthy as policy switches at L4.
    """
    from scripts.build_l0_triggers_london import run_days
    from src.backtest.engine import simulate
    from src.engine.triggers import Trigger

    bars = load_bars()
    raw = pd.read_parquet(MASTER).drop(columns=["roll"], errors="ignore")
    trigs = run_days(raw, GATE_DAYS)
    F = run(trigs, bars)
    tobjs = [Trigger(**r) for r in trigs.to_dict("records")]

    ok = True
    for arm, t_cancel, label in (("arm_none", 1e9, "t_cancel OFF (London shipping rule)"),
                                 ("arm_dist22", T_CANCEL, "t_cancel 22 (old-book rule)")):
        n_eng = 0
        print(f"\n--- {label} -> engine fills must be a subset of {arm} ---")
        for day in GATE_DAYS:
            cfg = _london_cfg(day, t_cancel)
            dtr = [t for t in tobjs if t.ts[:10] == day]
            seg = raw[(raw.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                       - pd.Timedelta(days=30))
                      & (raw.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))]
            tr, _, _ = simulate(seg.reset_index(drop=True), dtr, cfg)
            for e in tr:
                n_eng += 1
                m = F[(F.ts == e.trigger_ts) & (F.status == "filled")]
                row = m.iloc[0] if len(m) else None
                good = (row is not None and bool(row[arm])
                        and abs(row.fill_px - e.entry) < 1e-6
                        and pd.Timestamp(row.fill_ts) == pd.Timestamp(e.fill_ts))
                if not good:
                    ok = False
                    seen = ("no L1 fill" if row is None
                            else (row.fill_ts, row.fill_px, bool(row[arm])))
                    print(f"  MISMATCH {day} {e.trigger_ts}: engine {e.fill_ts} @ {e.entry}"
                          f" vs L1 {seen}")
            print(f"  {day} win {cfg.win_start}-{cfg.win_end}: {len(tr)} engine fills checked")
        print(f"  total engine fills checked: {n_eng}")

    print(f"\nL1 rows: {len(F)} | filled {int(F.arm_none.sum())} | "
          f"arm_dist22 {int(F.arm_dist22.sum())} | arm_struct {int(F.arm_struct.sum())}")
    if not ok:
        raise SystemExit("GATE FAILED — L1 fill mechanics diverge from the engine")
    print("gate OK — every engine fill reproduced exactly under BOTH cancel policies; "
          "L1 is the engine's fill model minus serialization and cancels")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.gate:
        return gate()
    if not a.span:
        raise SystemExit("--span or --gate required")

    trigs = pd.read_parquet(ROOT / f"output/l0_triggers_london_{a.span}.parquet")
    F = run(trigs, load_bars())
    out = Path(a.out) if a.out else ROOT / f"output/l1_fills_london_{a.span}.parquet"
    F.to_parquet(out, index=False)

    fl = F[F.arm_none]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} candidates on {F.day.nunique()} days")
    print(f"filled {len(fl)} ({len(fl) / max(len(F), 1) * 100:.0f}%) | "
          f"arm_dist22 {int(F.arm_dist22.sum())} | arm_struct {int(F.arm_struct.sum())}")
    print(f"struct events on filled: {fl.struct_event.value_counts().to_dict()}")
    print(f"median mins_to_fill: {fl.mins_to_fill.median():.0f} | "
          f"median risk_intended: {fl.risk_intended.median():.1f}pt")

    # What the old book's 22pt cancel deleted — the ANGUS ruling says London should not have
    # had it. This is the population delta the L2 outcomes will price.
    cut = int(F.arm_none.sum() - F.arm_dist22.sum())
    print(f"\n22pt distance cancel would delete {cut} of {int(F.arm_none.sum())} fills "
          f"({cut / max(int(F.arm_none.sum()), 1) * 100:.1f}%) — the ANGUS ruling removes it; "
          f"L2 prices whether those fills were better or worse than the ones it kept")
    print(f"struct-cancel would delete {int(F.arm_none.sum() - F.arm_struct.sum())}")
    if F.dst_shifted.any():
        d = F[F.dst_shifted]
        print(f"\nDST-shifted rows: {len(d)} on {d.day.nunique()} days "
              f"(expiry 06:00 ET) | filled {int(d.arm_none.sum())}")


if __name__ == "__main__":
    main()
