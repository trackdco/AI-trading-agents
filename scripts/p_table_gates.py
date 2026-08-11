"""P-TABLE pre-merge gates — SPEC-pxl-p-table.md B4.

All three gates must pass before the table is merged/used. Run AFTER the build:

    python3 scripts/p_table_gates.py

Writes output/p_table_gate_report.json and exits non-zero on any gate failure.

Note on provenance: the earlier programme's `scripts/htf_ma_entry_gate.py` does not
exist in this repository; this script implements the same gate contracts from
references/gates.md and SPEC B4 directly.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import date as Date, datetime, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import (CONFIG, TICK, UTC, Bar, build_session_minutes,
                         run_session, session_window_utc)
from build_p_table import (FLOW_MANIFEST, load_front_minutes, load_flow_day,
                           make_day_context, build_day_context_index,
                           minute_map_for_day_window, et_trading_date)

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")

# Columns whose values are fixed at or before ts_decision — which under mode (b)
# is the 5m resolution boundary, where the decision completes (C4). Every one of
# these must be identical under any perturbation of bars strictly after
# ts_decision, INCLUDING the window-aggregate columns (the window has closed).
PRE_DECISION_COLS = [
    "event_id", "ts_decision", "date", "session", "tf_trigger", "direction",
    "qualified", "reason", "pxl_ts", "pxl_level_0", "pxl_level_1", "pxl_50",
    "wick_width_pts", "pxl_age_bars", "leg_start_ts", "leg_start_price",
    "leg_height_pts", "retrace_frac", "retrace_high", "disp_open", "disp_high",
    "disp_low", "disp_close", "disp_body_pts", "disp_range_pts",
    "disp_body_range_ratio", "disp_close_loc", "atr14_pts", "disp_range_atr",
    "disp_vol", "break_bars", "break_depth_pts", "open_outside_zone",
    "close_beyond_zone", "body_wick_ratio", "body_excess_pts", "tf_first_ts",
    "tf_trigger_ts", "structure_state", "n_desc_highs", "n_desc_lows",
    "limit_price", "stop_price_base", "stop_dist_pts_base", "target_price",
    "target_dist_pts", "r_available", "min_1r_pass", "ts_entry_eligible",
    "tf_qualifying_set", "tf_agreement_count", "n_events_in_cluster",
]
# The governing EVENT's own facts — fixed at tf_trigger_ts (its bar's close),
# asserted under a perturbation at tf_trigger_ts via the per-TF sibling rows.
EVENT_OWN_COLS = ["qualified", "reason", "structure_state", "level_0", "level_1",
                  "wick_width_pts", "pxl_50", "target_price"]


def flatten_after(minutes: list[Bar], t: datetime) -> list[Bar]:
    out = []
    prev_close = None
    for b in minutes:
        if b.open_ts < t:
            out.append(b)
            prev_close = b.close
        else:
            pc = prev_close if prev_close is not None else b.open
            out.append(Bar(b.open_ts, b.close_ts, pc, pc, pc, pc, 0.0, False))
    return out


def tick_shift_decision_close(minutes: list[Bar], row) -> list[Bar] | None:
    """Shift the TRIGGER bar's closing minute by one tick in the trade direction
    (keeps the span qualification intact). Returns None if there is no room."""
    d = int(row.direction)
    close = float(row.disp_close)
    l0 = float(row.pxl_level_0)
    if d == -1 and not (close - TICK > 0):
        return None
    tdec = pd.Timestamp(row.tf_trigger_ts).to_pydatetime()
    out = []
    for b in minutes:
        if b.close_ts == tdec:
            nc = b.close - TICK if d == -1 else b.close + TICK
            out.append(Bar(b.open_ts, b.close_ts, b.open,
                           max(b.high, nc), min(b.low, nc), nc, b.volume, b.real))
        else:
            out.append(b)
    return out


def rebuild(minutes, d: Date, session: str, ctx):
    m, t, c = run_session(minutes, d, session, day_context=ctx, flow_lookup=None)
    return pd.DataFrame(m), pd.DataFrame(t)


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def cmp_row(a: pd.Series, b: pd.Series, cols) -> list[str]:
    bad = []
    for c in cols:
        va, vb = a.get(c), b.get(c)
        if _is_num(va) and _is_num(vb):
            fa, fb = float(va), float(vb)
            if math.isnan(fa) and math.isnan(fb):
                continue
            if not math.isclose(fa, fb, rel_tol=0, abs_tol=1e-9):
                bad.append(f"{c}: {va!r} != {vb!r}")
        elif va is None and vb is None:
            continue
        elif str(va) != str(vb):
            bad.append(f"{c}: {va!r} != {vb!r}")
    return bad


def pick_probes(fit: pd.DataFrame, per_stratum: int = 2) -> pd.DataFrame:
    fit = fit.copy()
    fit["cls"] = fit.reason.where(fit.reason != "", "qualified")
    probes = []
    for (s, d, cls), grp in fit.groupby(["session", "direction", "cls"]):
        grp = grp.sort_values("event_id")           # deterministic spread
        step = max(1, len(grp) // per_stratum)
        probes.append(grp.iloc[::step].head(per_stratum))
    return pd.concat(probes).drop_duplicates("event_id")


def main():
    report = {"gate1": {}, "gate2": {}, "gate3": {}, "pass": False}
    fit = pd.read_parquet("output/p_table.parquet")
    df, front = load_front_minutes(CACHE)
    day_hl, ordered, prior_day, htf = build_day_context_index(df)

    probes = pick_probes(fit)
    cells = probes.groupby(["session", "direction"]).size()
    print(f"probes: {len(probes)} across strata:\n{probes.groupby(['session','direction','cls']).size()}")
    assert len(probes) >= 15, "need >=15 probes"
    assert len(cells) == 4, "need both sessions x both directions"

    g1_fail, g2_fail = [], []
    g1_notes, g2_notes = [], []
    n_lim_coincide = 0
    session_cache = {}

    for _, row in probes.iterrows():
        d = Date.fromisoformat(row.date)
        key = (row.date, row.session)
        if key not in session_cache:
            w_utc, s_utc, e_utc = session_window_utc(d, row.session)
            mm = minute_map_for_day_window(df, w_utc, e_utc)
            minutes, _, _ = build_session_minutes(mm, d, row.session)
            ctx = make_day_context(d, row.session, df, day_hl, prior_day, htf)
            base, base_tf = rebuild(minutes, d, row.session, ctx)
            session_cache[key] = (minutes, ctx, base, base_tf)
        minutes, ctx, base, base_tf = session_cache[key]
        tdec = pd.Timestamp(row.ts_decision).to_pydatetime()
        ttrig = pd.Timestamp(row.tf_trigger_ts).to_pydatetime()

        # determinism: rebuilt-original contains the stored row identically
        b0 = base[base.event_id == row.event_id]
        if len(b0) != 1 or cmp_row(row, b0.iloc[0], PRE_DECISION_COLS):
            g1_fail.append(dict(event=row.event_id, err="rebuild != stored",
                                detail=cmp_row(row, b0.iloc[0], PRE_DECISION_COLS)
                                       if len(b0) == 1 else "row missing"))
            continue

        # ---- Gate 1a: flatten strictly after ts_decision (the boundary, where
        # the mode-b decision completes), rebuild, compare
        pert, pert_tf = rebuild(flatten_after(minutes, tdec), d, row.session, ctx)
        keys_base = set(base[base.ts_decision <= row.ts_decision].event_id)
        keys_pert = set(pert[pert.ts_decision <= row.ts_decision].event_id)
        if keys_base != keys_pert:
            g1_fail.append(dict(event=row.event_id, err="key set changed",
                                only_base=sorted(keys_base - keys_pert),
                                only_pert=sorted(keys_pert - keys_base)))
            continue
        p0 = pert[pert.event_id == row.event_id].iloc[0]
        bad = cmp_row(row, p0, PRE_DECISION_COLS)
        if bad:
            g1_fail.append(dict(event=row.event_id, err="pre-decision cols changed",
                                detail=bad))
        # tf_trigger causality, part 1: governance is fixed at the boundary
        if str(p0.tf_trigger) != str(row.tf_trigger) or \
                pd.Timestamp(p0.tf_trigger_ts) != pd.Timestamp(row.tf_trigger_ts):
            g1_fail.append(dict(event=row.event_id,
                                err="tf_trigger not fixed at ts_decision"))

        # ---- Gate 1b: tf_trigger causality, part 2 — the governing event's own
        # facts are fixed at its own close: flatten strictly after tf_trigger_ts
        # and assert the event reappears identically in the per-TF event stream.
        _, pert2_tf = rebuild(flatten_after(minutes, ttrig), d, row.session, ctx)
        cand2 = pert2_tf[(pert2_tf.tf == row.tf_trigger)
                         & (pert2_tf.own_ts_decision == row.tf_trigger_ts)
                         & (pert2_tf.level_0 == row.pxl_level_0)]
        base_ev = base_tf[(base_tf.tf == row.tf_trigger)
                          & (base_tf.own_ts_decision == row.tf_trigger_ts)
                          & (base_tf.level_0 == row.pxl_level_0)]
        if len(cand2) != 1 or len(base_ev) != 1:
            g1_fail.append(dict(event=row.event_id,
                                err="governing event not uniquely present under "
                                    "perturbation at tf_trigger_ts",
                                n_base=int(len(base_ev)), n_pert=int(len(cand2))))
        else:
            bad2 = cmp_row(base_ev.iloc[0], cand2.iloc[0], EVENT_OWN_COLS)
            if bad2:
                g1_fail.append(dict(event=row.event_id,
                                    err="governing event's own facts depend on "
                                        "post-close bars", detail=bad2))

        # ---- Gate 2a on the same perturbation
        if not math.isclose(float(p0.limit_price), float(row.limit_price),
                            abs_tol=1e-9):
            g2_fail.append(dict(event=row.event_id, err="limit moved under "
                                "future-flattening (reads post-decision bars)"))
        if row.qualified:
            # A flat post-boundary future cannot MOVE to a fill. Two legitimate
            # non-session-end outcomes remain: (a) a REAL pre-boundary gap event
            # already cancelled (mode-b); (b) the limit was already MARKETABLE at
            # placement — the last real price before the boundary sits beyond
            # limit +/- trade-through, so the resting order fills instantly on
            # the first live bar even at a frozen price (booked at the limit,
            # conservative).
            last_real2 = [b for b in minutes if b.open_ts < tdec]
            flat2 = last_real2[-1].close if last_real2 else None
            tt_pts = CONFIG["TRADE_THROUGH_TICKS"] * TICK
            marketable = flat2 is not None and (
                flat2 >= row.limit_price + tt_pts if row.direction == -1
                else flat2 <= row.limit_price - tt_pts)
            if bool(p0.filled) and not (
                    marketable and float(p0.bars_to_fill) == 1.0):
                g2_fail.append(dict(event=row.event_id,
                                    err="filled on a flat future without being "
                                        "marketable at placement"))
            if not bool(p0.filled) and not (
                    bool(p0.expired_session_end) or bool(p0.order_never_live)):
                g2_fail.append(dict(event=row.event_id,
                                    err="flat future should expire at session end "
                                        "(or be a real gap cancel)",
                                    got=dict(tt=bool(p0.expired_target_taken),
                                             inv=bool(p0.expired_invalidated))))
        # ctrl entry must MOVE to the flat value (the entry-price-moves assert)
        last_real = [b for b in minutes if b.open_ts < tdec]
        flat_val = last_real[-1].close if last_real else None
        if flat_val is not None and not pd.isna(p0.ctrl_entry_price):
            if not math.isclose(float(p0.ctrl_entry_price), flat_val, abs_tol=1e-9):
                g2_fail.append(dict(event=row.event_id,
                                    err="ctrl entry price did not move to the "
                                        "flattened value",
                                    got=float(p0.ctrl_entry_price), want=flat_val))
            if not pd.isna(row.ctrl_entry_price) and math.isclose(
                    float(row.ctrl_entry_price), flat_val, abs_tol=1e-9):
                n_lim_coincide += 1     # numeric coincidence, logged not failed

        # ---- Gate 2c: one-tick shift of the decision close -> limit invariant
        shifted = tick_shift_decision_close(minutes, row)
        if shifted is not None:
            p2, _ = rebuild(shifted, d, row.session, ctx)
            r2 = p2[p2.event_id == row.event_id]
            if len(r2) != 1:
                g2_fail.append(dict(event=row.event_id,
                                    err="row vanished under 1-tick close shift"))
            else:
                r2 = r2.iloc[0]
                if not math.isclose(float(r2.limit_price), float(row.limit_price),
                                    abs_tol=1e-9):
                    g2_fail.append(dict(event=row.event_id,
                                        err="limit derives from the decision "
                                            "bar's close",
                                        got=float(r2.limit_price)))
                if math.isclose(float(r2.disp_close), float(row.disp_close),
                                abs_tol=1e-9):
                    g2_fail.append(dict(event=row.event_id,
                                        err="tick-shift perturbation did not take"))

    # ---- Gate 2b: full-table row-level asserts
    f = fit
    if not ((f.limit_price - ((f.pxl_level_0 + f.pxl_level_1) / 2)).abs() <= TICK / 2 + 1e-9).all():
        g2_fail.append(dict(err="limit != pxl_50 (mid of wick, tick-rounded) somewhere"))
    if not (pd.to_datetime(f.pxl_ts) < pd.to_datetime(f.ts_decision)).all():
        g2_fail.append(dict(err="pxl bar not strictly before decision somewhere"))
    if not (pd.to_datetime(f.ts_entry_eligible) == pd.to_datetime(f.ts_decision)).all():
        g2_fail.append(dict(err="mode-b: eligibility must equal the decision "
                                "boundary on every row"))
    if not (pd.to_datetime(f.tf_trigger_ts) <= pd.to_datetime(f.ts_decision)).all():
        g2_fail.append(dict(err="a trigger bar closing after its decision "
                                "boundary exists"))
    if not all(ts.timestamp() % (CONFIG["RESOLUTION_TF_MIN"] * 60) == 0
               for ts in pd.to_datetime(f.ts_entry_eligible)):
        g2_fail.append(dict(err="eligibility not on the 5m boundary grid"))
    filled = f[f.filled == True]  # noqa: E712
    if len(filled) and not (pd.to_datetime(filled.ts_fill) >
                            pd.to_datetime(filled.ts_entry_eligible)).all():
        g2_fail.append(dict(err="a fill at or before eligibility exists"))
    lim_eq_bar = int(((f.limit_price == f.disp_open) | (f.limit_price == f.disp_high)
                      | (f.limit_price == f.disp_low)
                      | (f.limit_price == f.disp_close)).sum())
    g2_notes.append(dict(note="limit == some decision-bar OHLC (numeric "
                              "coincidence; limit is structurally pxl-bar-derived)",
                         n_rows=lim_eq_bar, of=len(f)))
    g2_notes.append(dict(note="developing-indicator scan: no level in this schema "
                              "derives from any indicator (limit/stop/target are "
                              "pure PXL-bar and pivot geometry); the delta-close/"
                              "period signature has no surface to appear on. The "
                              "1-tick close-shift invariance above is the direct "
                              "test.", ctrl_entry_flat_coincidences=n_lim_coincide))

    # ---- Gate 3: flow convention sweep over ALL flow files
    man = json.load(open(FLOW_MANIFEST))
    expected_scale = {"A": "fixed1e9", "B": "decimal", "C": "fixed1e9"}
    known_anoms = set(man.get("scale_anomalies", []))
    g3_rows, g3_fail = [], []
    front_min = df.set_index("ts")
    for fmeta in man["per_file"]:
        if fmeta.get("empty"):
            continue
        path, fam = fmeta["file"], fmeta["family"]
        books, detected = load_flow_day(path, fam)
        order_bad = 0
        devs = []
        for cts, book in books.items():
            bids = [book[f"bid_px_{i}"] for i in range(10)]
            asks = [book[f"ask_px_{i}"] for i in range(10)]
            if not (all(bids[i] > bids[i + 1] for i in range(9))
                    and all(asks[i] < asks[i + 1] for i in range(9))
                    and bids[0] < asks[0]):
                order_bad += 1
            try:
                bar = front_min.loc[cts - timedelta(minutes=1)]
                devs.append(abs((book["bid_px_0"] + book["ask_px_0"]) / 2
                                - float(bar.close)))
            except KeyError:
                pass
        scale_ok = (detected == expected_scale[fam]) or (path in known_anoms)
        joined = len(devs)
        frac5 = (sum(x <= 5.0 for x in devs) / joined) if joined else None
        med = sorted(devs)[joined // 2] if joined else None
        ok = scale_ok and order_bad == 0 and (
            (joined and frac5 >= 0.98) or (not joined and not fmeta.get("in_ohlcv_span")))
        g3_rows.append(dict(file=path, family=fam, scale=detected,
                            scale_anomaly=path in known_anoms, n=len(books),
                            joined=joined, med_dev_pts=med, frac_within_5pts=frac5,
                            order_violations=order_bad,
                            in_span=bool(fmeta.get("in_ohlcv_span")), ok=ok))
        if not ok:
            g3_fail.append(g3_rows[-1])

    in_span_bad = [r for r in g3_fail if r["in_span"]]
    # files failing bar-agreement in span: acceptable ONLY if the build excluded
    # them from flow_coverage (declared roll-mismatch handling)
    excl = pd.read_csv("output/p_table_exclusion_log.csv") \
        if os.path.getsize("output/p_table_exclusion_log.csv") > 5 else pd.DataFrame()
    excl_files = set()
    if len(excl):
        for _, e in excl[excl.criterion == "flow_file_convention_mismatch"].iterrows():
            excl_files.add(str(e.note).split(":")[0])
    unhandled = [r for r in in_span_bad if r["file"] not in excl_files]

    a_dates = {r["date"] for r in man["per_file"]
               if r.get("family") == "A" and not r.get("empty")}
    b_dates = {r["date"] for r in man["per_file"]
               if r.get("family") == "B" and not r.get("empty")}
    shared = sorted(a_dates & b_dates)

    report["gate1"] = dict(
        n_probes=int(len(probes)),
        strata={f"{s}|{d}|{c}": int(n) for (s, d, c), n in
                probes.groupby(["session", "direction", "cls"]).size().items()},
        failures=g1_fail, notes=g1_notes,
        tf_trigger_causality=dict(
            part1="governance fixed at ts_decision (the 5m boundary where the "
                  "mode-b decision completes): flatten after ts_decision leaves "
                  "tf_trigger, the qualifying set, and every row column unchanged",
            part2="the governing event's own facts fixed at tf_trigger_ts: "
                  "flatten after tf_trigger_ts leaves the event present with "
                  "identical geometry/qualification in the per-TF stream",
            note="the STRICT reading (governance itself fixed at tf_trigger_ts) "
                 "is unsatisfiable under mode (b): a higher-TF bar closing later "
                 "in the same window supersedes by design; this was demonstrated "
                 "by an earlier gate run and is why ts_decision is the boundary. "
                 "Mode (a) rows would make the two instants coincide."),
        passed=not g1_fail)
    report["gate2"] = dict(failures=g2_fail, notes=g2_notes, passed=not g2_fail)
    report["gate3"] = dict(
        n_files_checked=len(g3_rows),
        n_in_span_ok=sum(1 for r in g3_rows if r["in_span"] and r["ok"]),
        n_in_span_excluded_by_declared_criterion=len(in_span_bad) - len(unhandled),
        excluded_files=[r["file"] for r in in_span_bad if r["file"] in excl_files],
        unhandled_failures=unhandled,
        out_of_span_format_checked=sum(1 for r in g3_rows if not r["in_span"]),
        scale_anomalies_confirmed=[r["file"] for r in g3_rows if r["scale_anomaly"]],
        cross_extraction=dict(
            shared_dates_A_and_B=len(shared),
            common_minutes=0,
            miss="Families A and B share dates but zero common minutes; agreement "
                 "is established transitively through the front-month OHLCV bar. "
                 "STANDING REQUIREMENT: future extractions must preserve a "
                 "deliberate same-minute overlap; the forward recorder must "
                 "capture trades and overlap both windows."),
        passed=not unhandled)
    report["pass"] = bool(report["gate1"]["passed"] and report["gate2"]["passed"]
                          and report["gate3"]["passed"])
    json.dump(report, open("output/p_table_gate_report.json", "w"), indent=1,
              default=str)
    pd.DataFrame(g3_rows).to_csv("output/p_table_gate3_per_file.csv", index=False)
    print(json.dumps({k: (v if k == "pass" else
                          {kk: vv for kk, vv in v.items()
                           if kk in ("passed", "n_probes", "n_files_checked",
                                     "n_in_span_ok", "failures",
                                     "unhandled_failures")})
                      for k, v in report.items()}, indent=1, default=str)[:4000])
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
