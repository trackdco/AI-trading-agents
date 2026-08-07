#!/usr/bin/env python3
"""L2 LONDON — the outcome of every L0 London candidate, through the REAL engine.

Authorised by docs/PREREG-london-canon-rebuild.md.

NO RE-IMPLEMENTATION. Each trigger goes through `simulate()` itself, one trigger per
call, so entry vetoes, V8 management, partials, target resolution and the session flatten
are the engine's own code path. The champion-vs-canon lesson stands: a faithful-to-spec
rewrite once shared 14% of its trades with the thing it rewrote.

WHAT CHANGES vs NY, and only this:

  window        the LONDON window, per day, DST-correct (03:00-05:00 ET, or 04:00-06:00
                on misaligned weeks). NY hardcodes 07:45-11:00. The config is rebuilt for
                each day rather than fixed once, which is the whole reason this file exists.
  cap 99        the cap is L4 policy, not physics
  min_stop 0    the London 9.5pt Layer-0 risk gate is a HYPOTHESIS to re-test on the honest
                population (handoff §2), not a rule to import. It is off here; L2 measures
                the risk bands and L4 decides.
  max_stop None same
  t_cancel off  London's standing ruling is no distance cancel; cancel rules are L1-derived
                columns anyway, and an outcome depends only on the fill

WHAT SURVIVES INSIDE THE ENGINE, DELIBERATELY: tick rounding, the bad-geometry veto, the §6
target menu with `rr_floor = 2.0` at order time (ANGUS: hard 2R minimum every trade — part
of the base strategy, not selection), V8 management. A candidate the engine refuses to order
is recorded WITH its veto as the status, so the census stays complete.

THE WHOLE CENSUS IS WALKED, not just the deduped setups. `setup_id` / `setup_first` /
`setup_htf` are joined back as columns, so both tie-break arms are answerable from one run
and neither is baked into the outcomes.

    python -m scripts.build_l2_outcomes_london --gate
    python -m scripts.build_l2_outcomes_london --span fit [--procs 4]
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l0_triggers_london import window_et  # noqa: E402
from scripts.build_l2_outcomes import load_bars  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
LOOKBACK_DAYS = 7
PREREG = "docs/PREREG-london-canon-rebuild.md"
IN_L0 = ROOT / "output/l0_triggers_london_fit_std.parquet"
IN_L1 = ROOT / "output/l1_fills_london_fit_dedup.parquet"
OUT = ROOT / "output/l2_outcomes_london_fit.parquet"

_BARS: pd.DataFrame | None = None


ENTRY_VARIANT = "EC"        # overridden by --entry; see prereg §9
_RRFLOOR = None             # None = keep the config's 2.0. 0.0 = NEXT structural level.
_ARM = ""                   # census arm suffix, e.g. "_pp" (prior-session profile levels)
_CFG_OVERRIDES: dict = {}   # exit-lab sweep: arbitrary config overrides applied LAST


def in_l0(arm: str = "") -> Path:
    return ROOT / f"output/l0_triggers_london_fit_std{arm}.parquet"


def in_l1(arm: str = "") -> Path:
    return ROOT / f"output/l1_fills_london_fit{arm}_dedup.parquet"


def l2_cfg(day: str, entry: str = "EC"):
    """Config for ONE London day. The window is rebuilt per day because London's ET hours
    move with the UK/US DST misalignment — hardcoding them is burn-list item 1.

    `no_premarket_high_impact` is OFF, and this is a correction, not a relaxation.
    The engine's rule is *"on a high-impact pre-open release day the ENTIRE pre-market is
    blocked -> no entries until 09:30"*, written for NY. London runs 03:00-05:00 ET, which
    satisfies `tod < 09:30`, so it was standing London down for US releases that had not
    happened yet. Measured on this calendar:

        408 of 409 high-impact pre-09:30 releases land at 08:15 ET or later
        exactly 1 of 409 could touch a London 03:00-06:00 window
        the veto deleted 1,086 candidates on 34 sessions -- 168 of the 1,426 ruled
        setups, 11.8% -- for an event 2.5 to 5.5 hours in their future

    The London trade is flat long before the release exists. `docs/HANDOFF-london-rebuild.md`
    §5 flagged this in advance: *"news blackout ... NY-scoped 8:30 events -- check which
    events touch the London window before applying"*. This is that check, and it fails.

    OPEN, recorded rather than silently dropped: London has no news stand-down at all now.
    A correctly scoped one needs a UK/EU calendar (an 08:30 London release is 03:30 ET,
    squarely inside the window) and we do not hold one. Declared as owed at L4.
    """
    start, end = window_et(day, ("08:00", "10:00"))
    return load_backtest_config().model_copy(update={
        "win_start": start.time(), "win_end": end.time(), "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None, "t_cancel": 100000.0,
        "no_premarket_high_impact": False, "mgmt_variant": "V8",
        "entry_variant": entry,
        **({} if _RRFLOOR is None else
           # ANGUS 2026-08-05: "it should be the next structural level not 2r floor
           # minimum" -- and then "can u run that for the full london raw trigger set?".
           # Identical semantics to the NY script: walkout_under_floor walks the menu
           # OUTWARD past the nearest level, so a 2.0 floor DISCARDS the near target and
           # vetoes the trade when nothing clears. Floor 0 with walkout off takes the
           # first level in the menu -- the next structural level, whatever R that is.
           {"rr_floor": _RRFLOOR, "rr_floor_partial": min(_RRFLOOR, 1.5),
            "walkout_under_floor": False}),
        # exit-lab sweep overrides go LAST so an arm can set anything, including putting
        # `walkout_under_floor` back on (the --rr-floor block above forces it off, which is
        # right for "next structural level" but wrong for "aim for at least X R").
        **_CFG_OVERRIDES})


def _init_pool(prior_profile: bool, rrfloor=..., overrides: dict | None = None) -> None:
    """Per-worker setup. The engine's `default_target_resolver` calls `build_snapshot`, which
    reads `_include_prior_profile()` from its own module globals — so patching `snapshot` is
    what puts yesterday's POC/VAH/VAL into the TARGET MENU. Applied per worker so it holds
    under a spawn start method as well as fork."""
    if prior_profile:
        import src.engine.snapshot as _snap
        _snap._include_prior_profile = lambda: True
    # the sweep drives workers directly, so its arm settings must be re-established here —
    # a spawn start method does not inherit the parent's module globals
    global _RRFLOOR, _CFG_OVERRIDES
    if rrfloor is not ...:
        _RRFLOOR = rrfloor
    if overrides is not None:
        _CFG_OVERRIDES = overrides


def day_outcomes(args) -> list[dict]:
    day, recs, lookback, entry = args
    global _BARS
    if _BARS is None:
        _BARS = load_bars()
    seg = _BARS[(_BARS.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                 - pd.Timedelta(days=lookback))
                & (_BARS.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))
                ].reset_index(drop=True)
    cfg = l2_cfg(day, entry)
    out = []
    for rec in recs:
        t = Trigger(**{k: v for k, v in rec.items() if k in Trigger.model_fields})
        trades, verdicts, _ = simulate(seg, [t], cfg)
        row = {"day": day, "ts": t.ts, "tf": t.tf, "direction": t.direction,
               "kind": t.kind, "pattern": t.pattern, "htf_flag": t.htf_flag,
               "confluence_count": t.confluence_count,
               "vwap_touched": bool(rec.get("vwap_touched", False)),
               "cluster_members": rec.get("cluster_members", ""),
               "level_stack": rec.get("level_stack", "")}
        if trades:
            r = trades[0]
            row |= {"status": "outcome", "fill_ts": str(r.fill_ts), "entry": float(r.entry),
                    "stop": float(r.stop_initial),
                    "risk": round(abs(float(r.limit_price) - float(r.stop_initial)), 4),
                    "exit_ts": str(r.exit_ts), "exit_price": float(r.exit_price),
                    "exit_reason": str(r.exit_reason), "target": str(r.target_name),
                    "target_level": float(r.target_level),
                    "working_target": float(r.working_target),
                    "pts": float(r.points), "R": float(r.r_multiple),
                    "dollars_1lot": float(r.dollars)}
        else:
            v = verdicts[0] if verdicts else None
            row |= {"status": v.status if v else "no_verdict", "fill_ts": "",
                    "R": float("nan"), "dollars_1lot": float("nan")}
        out.append(row)
    return out


def run(trigs: pd.DataFrame, procs: int, lookback: int = LOOKBACK_DAYS,
        quiet: bool = False, entry: str = "EC",
        prior_profile: bool = False, overrides: dict | None = None) -> pd.DataFrame:
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(_d=ts.dt.strftime("%Y-%m-%d"))
    jobs = [(day, g.drop(columns=["_d"]).to_dict("records"), lookback, entry)
            for day, g in trigs.groupby("_d", sort=True)]
    rows, done = [], 0
    if procs <= 1:
        _init_pool(prior_profile, _RRFLOOR, overrides if overrides is not None else _CFG_OVERRIDES)
        for j in jobs:
            rows.extend(day_outcomes(j))
    else:
        with Pool(procs, initializer=_init_pool,
                  initargs=(prior_profile, _RRFLOOR,
                            overrides if overrides is not None else _CFG_OVERRIDES)) as p:
            for day_rows in p.imap(day_outcomes, jobs):
                rows.extend(day_rows)
                done += 1
                if not quiet and (done % 20 == 0 or done == len(jobs)):
                    print(f"  [{done}/{len(jobs)}] {day_rows[0]['day'] if day_rows else ''} "
                          f"— {len(rows):,} candidates", flush=True)
    return pd.DataFrame(rows)


def gate(lb: int = LOOKBACK_DAYS) -> bool:
    """GATE — outcome invariance of a `lb`-day lookback against 30 days, on days with real
    fills. A lookback that changes outcomes corrupts every number downstream of L2. NY's
    2-day attempt failed this gate honestly; the handoff expects London to need >= 7 too."""
    days = ["2025-06-10", "2025-07-22", "2025-09-17", "2025-12-03"]
    T = pd.read_parquet(in_l0(_ARM))
    trigs = T[T.day.isin(days)].reset_index(drop=True)
    a = run(trigs, procs=4, lookback=lb, quiet=True)
    b = run(trigs, procs=4, lookback=30, quiet=True)
    cols = ["ts", "status", "fill_ts", "exit_ts"]
    fa, fb = a[a.status == "outcome"], b[b.status == "outcome"]
    same = (a[cols].reset_index(drop=True).equals(b[cols].reset_index(drop=True))
            and len(fa) == len(fb)
            and (fa.dollars_1lot.to_numpy() == fb.dollars_1lot.to_numpy()).all())
    print(f"candidates {len(a)} | outcomes {len(fa)} vs {len(fb)} (30d) | "
          f"1-lot ${fa.dollars_1lot.sum():+,.0f} vs ${fb.dollars_1lot.sum():+,.0f}")
    if not same:
        print(f"GATE FAILED — {lb}d lookback is not outcome-invariant; raise it")
        return False
    if len(fa) == 0:
        print("GATE INCONCLUSIVE — no filled outcomes on the sample days")
        return False
    print(f"gate OK — {lb}d lookback outcome-identical to 30d on {len(fa)} real outcomes")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit"])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--entry", default="EC", choices=["EC", "E4", "E3"])
    ap.add_argument("--rr-floor", type=float, default=None,
                    help="0.0 = next structural level, no minimum R (ANGUS 2026-08-05). "
                         "Omit to keep the config's 2.0 floor.")
    ap.add_argument("--arm", default="",
                    help="census arm suffix, e.g. `_pp` for the prior-session-profile L0. "
                         "Selects that arm's L0 and L1 and suffixes the output.")
    ap.add_argument("--prior-profile", action="store_true",
                    help="put yesterday's POC/VAH/VAL in the engine's TARGET MENU. Separate "
                         "from --arm, which only selects the census: the census answers "
                         "'do these levels make trades', the menu answers 'are they worth "
                         "targeting'. An arm wants both.")
    a = ap.parse_args()
    # Guard. Running the _pp census against the BASELINE target menu tests half the change
    # and reads as a null result -- which is exactly what happened on the first attempt:
    # the book came back with zero prior_profile_* targets and a 100%-identical paired
    # comparison, because the levels created triggers but were absent when the engine chose
    # where to aim. Fail loudly rather than produce that book again.
    if "_pp" in a.arm and not a.prior_profile:
        ap.error("--arm _pp without --prior-profile: the census would carry the new levels "
                 "but the target menu would not. Pass both, or neither.")
    global _RRFLOOR, _ARM
    _RRFLOOR = a.rr_floor           # set BEFORE any Pool fork; workers inherit it
    _ARM = a.arm
    if a.gate:
        return 0 if gate() else 1
    if not a.span:
        ap.error("--span fit or --gate")

    for p in (in_l0(_ARM), in_l1(_ARM)):
        if not p.exists():
            ap.error(f"{p.relative_to(ROOT)} does not exist — build that arm's layer first")
    trigs = pd.read_parquet(in_l0(_ARM))
    print(f"L2 London — {len(trigs):,} candidates over {trigs.day.nunique()} sessions",
          flush=True)
    O = run(trigs, procs=a.procs, entry=a.entry, prior_profile=a.prior_profile)

    # join the L1b setup identity back on, so both tie-break arms are answerable
    flags = ["setup_first", "setup_htf", "vs_first", "vs_htf", "arm_none", "arm_struct"]
    L1 = pd.read_parquet(in_l1(_ARM))[["ts", "setup_id", "setup_size", "vs_id", "vs_size",
                                       *flags]]
    O = O.merge(L1, on="ts", how="left")
    O[flags] = O[flags].fillna(False)
    for c in ("setup_id", "vs_id"):
        O[c] = O[c].fillna(-1).astype(int)
    suffix = (_ARM
              + ("" if a.entry == "E3" else f"_{a.entry}")
              + ("" if a.rr_floor is None else f"_rr{a.rr_floor:g}"))
    out = OUT.with_name(f"l2_outcomes_london_fit{suffix}.parquet")
    O.to_parquet(out, index=False)

    ok = O[O.status == "outcome"]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(O):,} candidates, "
          f"{len(ok):,} with an outcome")
    print(f"engine statuses: {O.status.value_counts().head(8).to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
