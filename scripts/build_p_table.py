"""P-TABLE build driver — SPEC-pxl-p-table.md Part B (Stage 1).

Produces:
  output/p_table.parquet                 fit-era main table
  output/p_table_tf.parquet              fit-era per-timeframe sibling table
  output/p_table_candidates.parquet      fit-era candidate lifecycle sidecar
  output/sealed/p_table_sealed.parquet   sealed rows, written UNREAD (count only)
  output/sealed/p_table_tf_sealed.parquet
  output/sealed/p_table_candidates_sealed.parquet
  output/sealed/SHA256SUMS
  output/p_table_exclusion_log.csv
  output/p_table_build_stats.json        fit-era-only statistics for the B5 report

Run from the repo root:  python3 scripts/build_p_table.py [--cache DIR]
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date as Date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import (CONFIG, NY, TICK, UTC, build_session_minutes,
                         run_session, session_window_utc, tick_round)

OHLCV_FILES = [
    "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
    "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst",
]
OUTRIGHT = re.compile(r"^NQ[HMUZ]\d$")
FLOW_MANIFEST = "output/flow_coverage_manifest.json"
PRICE_FIXED_SCALE = 1e-9


# ------------------------------------------------------------------ bar loading

def load_front_minutes(cache_dir: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """All front-month 1m bars (full 24h), deduped across file overlaps.
    Front month per UTC date = max total daily volume among NQ outrights."""
    os.makedirs(cache_dir, exist_ok=True)
    cache_pq = os.path.join(cache_dir, "front_minutes.parquet")
    cache_map = os.path.join(cache_dir, "front_map.json")
    if os.path.exists(cache_pq) and os.path.exists(cache_map):
        return pd.read_parquet(cache_pq), json.load(open(cache_map))

    import zstandard
    vol: dict[tuple[str, str], int] = defaultdict(int)
    for f in OHLCV_FILES:
        dctx = zstandard.ZstdDecompressor()
        with open(f, "rb") as fh:
            r = csv.reader(io.TextIOWrapper(dctx.stream_reader(fh), encoding="utf-8"))
            h = next(r)
            ix = {c: i for i, c in enumerate(h)}
            for row in r:
                sym = row[ix["symbol"]]
                if OUTRIGHT.match(sym):
                    vol[(row[ix["ts_event"]][:10], sym)] += int(row[ix["volume"]])
    front: dict[str, str] = {}
    by_date: dict[str, dict[str, int]] = defaultdict(dict)
    for (d, s), v in vol.items():
        by_date[d][s] = v
    for d, syms in by_date.items():
        front[d] = max(syms.items(), key=lambda kv: kv[1])[0]

    rows = []
    seen: set[str] = set()
    for f in OHLCV_FILES:
        dctx = zstandard.ZstdDecompressor()
        with open(f, "rb") as fh:
            r = csv.reader(io.TextIOWrapper(dctx.stream_reader(fh), encoding="utf-8"))
            h = next(r)
            ix = {c: i for i, c in enumerate(h)}
            for row in r:
                ts = row[ix["ts_event"]]
                if front.get(ts[:10]) != row[ix["symbol"]]:
                    continue
                if ts in seen:      # file-overlap dedup on (ts, symbol==front)
                    continue
                seen.add(ts)
                rows.append((ts, float(row[ix["open"]]), float(row[ix["high"]]),
                             float(row[ix["low"]]), float(row[ix["close"]]),
                             int(row[ix["volume"]])))
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df.to_parquet(cache_pq)
    json.dump(front, open(cache_map, "w"))
    return df, front


def minute_map_for_day_window(df: pd.DataFrame, t0: datetime, t1: datetime):
    sub = df[(df.ts >= t0) & (df.ts < t1)]
    return {ts.to_pydatetime(): (o, h, l, c, v) for ts, o, h, l, c, v in
            zip(sub.ts, sub.open, sub.high, sub.low, sub.close, sub.volume)}


# ------------------------------------------------------------------ day context

def et_trading_date(ts: pd.Timestamp) -> Date:
    et = ts.tz_convert(NY)
    d = et.date()
    return d + timedelta(days=1) if et.hour >= 17 else d


def build_day_context_index(df: pd.DataFrame):
    """Per ET trading day: high/low (for PDH/PDL); plus epoch-anchored 15m/1h
    close series for HTF alignment lookups."""
    tdates = df.ts.map(et_trading_date)
    day_hl = {}
    for d, sub in df.groupby(tdates):
        day_hl[d] = (float(sub.high.max()), float(sub.low.min()))
    ordered = sorted(day_hl)

    def prior_day(d: Date):
        i = bisect.bisect_left(ordered, d)
        return ordered[i - 1] if i > 0 else None

    htf = {}
    for mins in (15, 60):
        g = df.set_index("ts")
        bars = g.resample(f"{mins}min", label="right", closed="left")["close"].last().dropna()
        htf[mins] = (list(bars.index.to_pydatetime()), list(bars.values))
    return day_hl, ordered, prior_day, htf


def make_day_context(d: Date, session: str, df: pd.DataFrame,
                     day_hl, prior_day, htf):
    w_utc, s_utc, e_utc = session_window_utc(d, session)
    pd_ = prior_day(d)
    ctx: dict = {}
    if pd_ is not None:
        ctx["pdh"], ctx["pdl"] = day_hl[pd_]
    else:
        ctx["pdh"] = ctx["pdl"] = float("nan")
    on = df[(df.ts >= datetime.combine(d - timedelta(days=3), datetime.min.time(), UTC))
            & (df.ts < s_utc)]
    on = on[on.ts.map(et_trading_date) == d]
    if len(on):
        ctx["onh"], ctx["onl"] = float(on.high.max()), float(on.low.min())
    else:
        ctx["onh"] = ctx["onl"] = float("nan")

    def mk_fn(mins):
        times, closes = htf[mins]

        def fn(ts: datetime) -> float:
            i = bisect.bisect_right(times, ts)
            if i < 2:
                return float("nan")
            return 1 if closes[i - 1] > closes[i - 2] else (
                -1 if closes[i - 1] < closes[i - 2] else 0)
        return fn

    ctx["htf_align_15m_fn"] = mk_fn(15)
    ctx["htf_align_1h_fn"] = mk_fn(60)
    return ctx


# ------------------------------------------------------------------------ flow

def load_flow_day(path: str, family: str):
    """One condensed MBP-10 file -> {minute_close_utc: book dict}. Prices
    normalised to decimal points; per-file scale auto-detected and returned so
    Gate 3 can assert it against the family convention."""
    out = {}
    detected = None
    with open(path) as fh:
        r = csv.reader(fh)
        try:
            h = next(r)
        except StopIteration:
            return out, None
        ix = {c: i for i, c in enumerate(h)}
        for row in r:
            try:
                ts = datetime.fromisoformat(row[ix["ts_event"]])
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            book = {}
            ok = True
            for lvl in range(10):
                for side in ("bid", "ask"):
                    try:
                        px = float(row[ix[f"{side}_px_{lvl:02d}"]])
                        sz = float(row[ix[f"{side}_sz_{lvl:02d}"]])
                    except ValueError:
                        ok = False
                        break
                    # scale detection by MAGNITUDE, per value: fixed-point 1e-9
                    # figures are ~1e13 whether serialized as int or float. A
                    # string-shape test misreads fixed-point written with a
                    # decimal point (Gate 3 catch, 3 files).
                    if px > 1e6:
                        px *= PRICE_FIXED_SCALE
                        if detected is None:
                            detected = "fixed1e9"
                    elif detected is None:
                        detected = "decimal"
                    book[f"{side}_px_{lvl}"] = px
                    book[f"{side}_sz_{lvl}"] = sz
                if not ok:
                    break
            if ok:
                # book state as-of the END of minute ts (ts_recv ~ ts+59s), i.e.
                # as-of the close of the 1m bar that OPENS at ts
                out[ts + timedelta(minutes=1)] = book
    return out, detected


def make_flow_lookup(date_str: str, session: str, books: dict | None,
                     file_ok: bool):
    def lookup(exe, row):
        res = dict(flow_coverage=False, flow_data_object="book_only",
                   delta_decision_bar=float("nan"), delta_3bar=float("nan"),
                   cvd_state=float("nan"), wall_size_ahead=float("nan"),
                   wall_dist_ticks=float("nan"), book_imbalance=float("nan"),
                   depth_censored=None, spread_est_ticks=float("nan"))
        if not books or not file_ok:
            return res
        book = books.get(exe.close_ts)
        if book is None:
            return res
        res["flow_coverage"] = True
        bb, ba = book["bid_px_0"], book["ask_px_0"]
        res["spread_est_ticks"] = round((ba - bb) / TICK, 2)
        sb = sum(book[f"bid_sz_{i}"] for i in range(10))
        sa = sum(book[f"ask_sz_{i}"] for i in range(10))
        res["book_imbalance"] = (sb - sa) / (sb + sa) if (sb + sa) > 0 else float("nan")
        side = "bid" if row["direction"] == -1 else "ask"   # resting size ahead,
        # i.e. between price and the target (below for shorts, above for longs)
        sizes = [(book[f"{side}_sz_{i}"], book[f"{side}_px_{i}"]) for i in range(10)]
        wall_sz, wall_px = max(sizes, key=lambda t: t[0])
        res["wall_size_ahead"] = wall_sz
        res["wall_dist_ticks"] = abs(exe.bar.close - wall_px) / TICK
        tgt = row["target_price"]
        if not (isinstance(tgt, float) and math.isnan(tgt)):
            deepest = book[f"{side}_px_9"]
            res["depth_censored"] = bool(tgt < deepest) if row["direction"] == -1 \
                else bool(tgt > deepest)
        return res
    return lookup


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.environ.get(
        "P_TABLE_CACHE",
        "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache"))
    ap.add_argument("--limit-dates", type=int, default=0, help="debug: first N dates")
    ap.add_argument("--dates", default="", help="debug: comma list of dates")
    ap.add_argument("--shard", default="", help="i/n: process every n-th date, "
                    "write parts to --partdir instead of final outputs")
    ap.add_argument("--partdir", default="")
    ap.add_argument("--merge", default="", help="partdir to merge into final outputs")
    args = ap.parse_args()

    if args.merge:
        merge_parts(args.merge)
        return

    print("[1/6] loading front-month minutes ...", flush=True)
    df, front = load_front_minutes(args.cache)
    print(f"      {len(df):,} minutes, {len(front)} UTC dates", flush=True)

    print("[2/6] day context index ...", flush=True)
    day_hl, ordered_days, prior_day, htf = build_day_context_index(df)

    print("[3/6] flow file index ...", flush=True)
    man = json.load(open(FLOW_MANIFEST))
    flow_files = {}     # (date, session) -> path
    for f in man["per_file"]:
        if f.get("empty") or not f.get("in_ohlcv_span"):
            continue
        if f["family"] == "A":
            flow_files[(f["date"], "ny_am")] = (f["file"], "A")
        elif f["family"] == "B":
            flow_files[(f["date"], "london")] = (f["file"], "B")
    flow_gate_rows = []   # per-file convention-check rows for Gate 3

    session_dates = sorted({et_trading_date(ts) for ts in
                            pd.to_datetime(list(front.keys()), utc=True)})
    if args.dates:
        session_dates = [Date.fromisoformat(x) for x in args.dates.split(",")]
    if args.limit_dates:
        session_dates = session_dates[:args.limit_dates]
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        session_dates = [d for k, d in enumerate(session_dates) if k % n == i]

    main_rows, tf_rows, cand_rows = [], [], []
    excl = []
    sens_counts = {f: Counter() for f in CONFIG["MIN_LEG_RETRACE_SENSITIVITY"]}
    n_sessions = Counter()

    print(f"[4/6] building {len(session_dates)} dates x 2 sessions ...", flush=True)
    for di, d in enumerate(session_dates):
        for session in CONFIG["SESSIONS"]:
            w_utc, s_utc, e_utc = session_window_utc(d, session)
            mm = minute_map_for_day_window(df, w_utc, e_utc)
            built = build_session_minutes(mm, d, session)
            if built is None:
                n_real = len(mm)
                n_total = int((e_utc - w_utc).total_seconds() // 60)
                excl.append(dict(date=d.isoformat(), session=session,
                                 criterion="session_window_incomplete",
                                 n_real_minutes=n_real, n_nominal_minutes=n_total,
                                 note="calendar/coverage based, outcome-independent"))
                continue
            minutes, n_real, n_total = built
            n_sessions[session] += 1
            ctx = make_day_context(d, session, df, day_hl, prior_day, htf)

            fk = flow_files.get((d.isoformat(), session))
            books, file_ok = None, False
            if fk:
                books, detected = load_flow_day(fk[0], fk[1])
                # convention check summary per file (full assert in Gate 3)
                devs = []
                for cts, book in books.items():
                    row = mm.get(cts - timedelta(minutes=1))
                    if row:
                        mid = (book["bid_px_0"] + book["ask_px_0"]) / 2
                        devs.append(abs(mid - row[3]))
                ok = bool(devs) and (sum(x <= 5.0 for x in devs) / len(devs) >= 0.98)
                flow_gate_rows.append(dict(
                    file=fk[0], family=fk[1], date=d.isoformat(), session=session,
                    scale_detected=detected, n_minutes=len(books),
                    n_joined=len(devs),
                    med_dev_pts=(sorted(devs)[len(devs) // 2] if devs else None),
                    frac_within_5pts=(sum(x <= 5.0 for x in devs) / len(devs)
                                      if devs else None),
                    ok=ok))
                file_ok = ok
                if not ok:
                    excl.append(dict(date=d.isoformat(), session=session,
                                     criterion="flow_file_convention_mismatch",
                                     n_real_minutes=len(devs), n_nominal_minutes=len(books),
                                     note=f"{fk[0]}: book vs front-month bar deviation; "
                                          "flow_coverage forced false, rows kept"))
            lookup = make_flow_lookup(d.isoformat(), session, books, file_ok)

            m, t, c = run_session(minutes, d, session, day_context=ctx,
                                  flow_lookup=lookup)
            main_rows += m
            tf_rows += t
            cand_rows += c
            for fr in CONFIG["MIN_LEG_RETRACE_SENSITIVITY"]:
                if fr == CONFIG["MIN_LEG_RETRACE"]:
                    for r in m:
                        sens_counts[fr][(r["session"], r["qualified"])] += 1
                    continue
                m2, _, _ = run_session(minutes, d, session, frac=fr, day_context=ctx)
                for r in m2:
                    sens_counts[fr][(r["session"], r["qualified"])] += 1
        if (di + 1) % 100 == 0:
            print(f"      {di + 1}/{len(session_dates)} dates, "
                  f"{len(main_rows)} rows", flush=True)

    if args.shard:
        os.makedirs(args.partdir, exist_ok=True)
        tag = args.shard.replace("/", "_")
        pd.DataFrame(main_rows).to_parquet(f"{args.partdir}/main_{tag}.parquet")
        pd.DataFrame(tf_rows).to_parquet(f"{args.partdir}/tf_{tag}.parquet")
        pd.DataFrame(cand_rows).to_parquet(f"{args.partdir}/cand_{tag}.parquet")
        json.dump(dict(
            excl=excl, n_sessions=dict(n_sessions), flow_gate_rows=flow_gate_rows,
            sens={str(f): {f"{s}|{qq}": n for (s, qq), n in cnt.items()}
                  for f, cnt in sens_counts.items()}),
            open(f"{args.partdir}/meta_{tag}.json", "w"), default=str)
        print(f"shard {args.shard}: {len(main_rows)} rows -> {args.partdir}")
        return

    print("[5/6] assembling & splitting ...", flush=True)
    dfm = pd.DataFrame(main_rows)
    dft = pd.DataFrame(tf_rows)
    dfc = pd.DataFrame(cand_rows)
    fit_end = CONFIG["FIT_END_DATE"]
    os.makedirs("output/sealed", exist_ok=True)

    fit_m = dfm[dfm.date <= fit_end].reset_index(drop=True)
    sealed_m = dfm[dfm.date > fit_end].reset_index(drop=True)
    fit_t = dft[dft.event_id.isin(set(fit_m.event_id))].reset_index(drop=True)
    sealed_t = dft[~dft.event_id.isin(set(fit_m.event_id))].reset_index(drop=True)
    fit_c = dfc[dfc.date <= fit_end].reset_index(drop=True)
    sealed_c = dfc[dfc.date > fit_end].reset_index(drop=True)

    fit_m.to_parquet("output/p_table.parquet")
    fit_t.to_parquet("output/p_table_tf.parquet")
    fit_c.to_parquet("output/p_table_candidates.parquet")
    sealed_m.to_parquet("output/sealed/p_table_sealed.parquet")
    sealed_t.to_parquet("output/sealed/p_table_tf_sealed.parquet")
    sealed_c.to_parquet("output/sealed/p_table_candidates_sealed.parquet")
    with open("output/sealed/SHA256SUMS", "w") as fh:
        for fn in ("p_table_sealed.parquet", "p_table_tf_sealed.parquet",
                   "p_table_candidates_sealed.parquet"):
            hsh = hashlib.sha256(open(f"output/sealed/{fn}", "rb").read()).hexdigest()
            fh.write(f"{hsh}  {fn}\n")
    pd.DataFrame(excl).to_csv("output/p_table_exclusion_log.csv", index=False)
    pd.DataFrame(flow_gate_rows).to_csv(
        "output/p_table_flow_convention_per_file.csv", index=False)

    # flow-covered non-null assert (format-level; runs across ALL rows incl. sealed,
    # reported as pass/fail + count only — B5 item 2)
    cov = dfm[dfm.flow_coverage == True]  # noqa: E712
    closeloc_ok = bool(cov.closeloc.notna().all()) if len(cov) else True
    rangex_ok = bool(cov.rangex.notna().all()) if len(cov) else True

    print("[6/6] fit-era stats ...", flush=True)
    stats = build_stats(fit_m, fit_t, fit_c, sens_counts, n_sessions,
                        len(sealed_m), len(sealed_t), len(sealed_c),
                        closeloc_ok, rangex_ok, int(len(cov)), excl)
    json.dump(stats, open("output/p_table_build_stats.json", "w"), indent=1,
              default=str)
    print(json.dumps(dict(fit_rows=len(fit_m), sealed_rows=len(sealed_m),
                          fit_tf=len(fit_t), fit_cands=len(fit_c),
                          exclusions=len(excl)), indent=1))


def merge_parts(partdir: str):
    import glob as _g
    dfm = pd.concat([pd.read_parquet(p) for p in sorted(_g.glob(f"{partdir}/main_*.parquet"))],
                    ignore_index=True).sort_values(["date", "session", "ts_decision"]).reset_index(drop=True)
    dft = pd.concat([pd.read_parquet(p) for p in sorted(_g.glob(f"{partdir}/tf_*.parquet"))],
                    ignore_index=True)
    dfc = pd.concat([pd.read_parquet(p) for p in sorted(_g.glob(f"{partdir}/cand_*.parquet"))],
                    ignore_index=True).sort_values(["date", "session", "tf"]).reset_index(drop=True)
    excl, flow_gate_rows = [], []
    n_sessions = Counter()
    sens = {f: Counter() for f in CONFIG["MIN_LEG_RETRACE_SENSITIVITY"]}
    for p in sorted(_g.glob(f"{partdir}/meta_*.json")):
        meta = json.load(open(p))
        excl += meta["excl"]
        flow_gate_rows += meta["flow_gate_rows"]
        for s, n in meta["n_sessions"].items():
            n_sessions[s] += n
        for f, d in meta["sens"].items():
            for k, n in d.items():
                s, qq = k.rsplit("|", 1)
                sens[float(f)][(s, qq == "True")] += n

    fit_end = CONFIG["FIT_END_DATE"]
    os.makedirs("output/sealed", exist_ok=True)
    fit_m = dfm[dfm.date <= fit_end].reset_index(drop=True)
    sealed_m = dfm[dfm.date > fit_end].reset_index(drop=True)
    fit_t = dft[dft.event_id.isin(set(fit_m.event_id))].reset_index(drop=True)
    sealed_t = dft[~dft.event_id.isin(set(fit_m.event_id))].reset_index(drop=True)
    fit_c = dfc[dfc.date <= fit_end].reset_index(drop=True)
    sealed_c = dfc[dfc.date > fit_end].reset_index(drop=True)
    fit_m.to_parquet("output/p_table.parquet")
    fit_t.to_parquet("output/p_table_tf.parquet")
    fit_c.to_parquet("output/p_table_candidates.parquet")
    sealed_m.to_parquet("output/sealed/p_table_sealed.parquet")
    sealed_t.to_parquet("output/sealed/p_table_tf_sealed.parquet")
    sealed_c.to_parquet("output/sealed/p_table_candidates_sealed.parquet")
    with open("output/sealed/SHA256SUMS", "w") as fh:
        for fn in ("p_table_sealed.parquet", "p_table_tf_sealed.parquet",
                   "p_table_candidates_sealed.parquet"):
            hsh = hashlib.sha256(open(f"output/sealed/{fn}", "rb").read()).hexdigest()
            fh.write(f"{hsh}  {fn}\n")
    pd.DataFrame(excl).to_csv("output/p_table_exclusion_log.csv", index=False)
    pd.DataFrame(flow_gate_rows).to_csv(
        "output/p_table_flow_convention_per_file.csv", index=False)
    cov = dfm[dfm.flow_coverage == True]  # noqa: E712
    closeloc_ok = bool(cov.closeloc.notna().all()) if len(cov) else True
    rangex_ok = bool(cov.rangex.notna().all()) if len(cov) else True
    stats = build_stats(fit_m, fit_t, fit_c, sens, n_sessions,
                        len(sealed_m), len(sealed_t), len(sealed_c),
                        closeloc_ok, rangex_ok, int(len(cov)), excl)
    json.dump(stats, open("output/p_table_build_stats.json", "w"), indent=1,
              default=str)
    print(json.dumps(dict(fit_rows=len(fit_m), sealed_rows=len(sealed_m),
                          fit_tf=len(fit_t), sealed_tf=len(sealed_t),
                          fit_cands=len(fit_c), exclusions=len(excl)), indent=1))


def _dist(s: pd.Series):
    s = s.dropna()
    if not len(s):
        return None
    return dict(n=int(len(s)), median=round(float(s.median()), 3),
                p25=round(float(s.quantile(.25)), 3),
                p75=round(float(s.quantile(.75)), 3),
                p90=round(float(s.quantile(.9)), 3))


def build_stats(m, t, c, sens, n_sessions, n_sealed, n_sealed_tf, n_sealed_c,
                closeloc_ok, rangex_ok, n_flow_cov, excl):
    q = m[m.qualified == True]  # noqa: E712
    filled = q[q.filled == True]  # noqa: E712
    unf = q[q.filled == False]  # noqa: E712
    st = dict(
        rows_fit=int(len(m)), rows_sealed_UNREAD=n_sealed,
        tf_rows_fit=int(len(t)), tf_rows_sealed_UNREAD=n_sealed_tf,
        cand_rows_fit=int(len(c)), cand_rows_sealed_UNREAD=n_sealed_c,
        n_sessions_processed=dict(n_sessions),
        exclusion_log_entries=len(excl),
        flow_nonnull_assert=dict(n_flow_covered_rows_all_eras=n_flow_cov,
                                 closeloc_all_nonnull=closeloc_ok,
                                 rangex_all_nonnull=rangex_ok),
        counts_by_session_direction_qualified_reason={
            f"{s}|{'short' if d == -1 else 'long'}|{qq}|{r or '-'}": int(n)
            for (s, d, qq, r), n in
            m.groupby(["session", "direction", "qualified", "reason"],
                      dropna=False).size().items()},
        triggers_per_session_per_day={
            s: dict(all=round(float(len(m[m.session == s]) /
                                    max(1, n_sessions.get(s, 1))), 3),
                    qualified=round(float(len(q[q.session == s]) /
                                          max(1, n_sessions.get(s, 1))), 3))
            for s in n_sessions},
        wick_width_pts=_dist(m.wick_width_pts),
        wick_width_pts_qualified=_dist(q.wick_width_pts),
        stop_dist=dict(
            base=_dist(m.stop_dist_pts_base),
            atr015=_dist(m.stop_dist_pts_atr015),
            atr025=_dist(m.stop_dist_pts_atr025),
            atr033=_dist(m.stop_dist_pts_atr033)),
        # --- deliverable 8: the load-bearing block ---
        fill=dict(
            n_qualified=int(len(q)),
            n_filled=int(len(filled)),
            fill_rate=round(float(len(filled) / len(q)), 4) if len(q) else None,
            cancellation_reasons={
                "expired_target_taken": int(q.expired_target_taken.sum()),
                "expired_invalidated": int(q.expired_invalidated.sum()),
                "expired_session_end": int(q.expired_session_end.sum()),
            },
            cancellation_rates={
                "expired_target_taken": round(float(q.expired_target_taken.mean()), 4),
                "expired_invalidated": round(float(q.expired_invalidated.mean()), 4),
                "expired_session_end": round(float(q.expired_session_end.mean()), 4),
            } if len(q) else {},
            order_never_live=int(q.order_never_live.sum()) if len(q) else 0,
            gap_limit_traded_through=int(q.gap_limit_traded_through.sum()) if len(q) else 0,
            filled_mfe_pts=_dist(filled.mfe_pts),
            filled_mfe_R=_dist(filled.mfe_R),
            unfilled_mfe_pts=_dist(unf.unfilled_mfe_pts),
            unfilled_mfe_pts_target_taken=_dist(
                unf[unf.expired_target_taken == True].unfilled_mfe_pts),  # noqa: E712
            unfilled_mfe_pts_session_end=_dist(
                unf[unf.expired_session_end == True].unfilled_mfe_pts),  # noqa: E712
            filled_stress_2tick_rate=round(float(filled.filled_stress_2tick.mean()), 4)
                                      if len(filled) else None,
            fill_bar_ambiguous_rate=round(float(filled.fill_bar_ambiguous.mean()), 4)
                                     if len(filled) else None,
        ),
        tf_agreement_count=dict(Counter(q.tf_agreement_count.tolist())),
        tf_trigger_distribution=dict(Counter(m.tf_trigger.tolist())),
        events_per_cluster=dict(Counter(m.n_events_in_cluster.tolist())),
        geometry_by_tf={
            str(tf): dict(
                wick_width_pts=_dist(t[t.tf == tf].wick_width_pts),
                stop_dist_pts=_dist(t[t.tf == tf].stop_dist_pts),
                r_available=_dist(t[t.tf == tf].r_available))
            for tf in sorted(t.tf.unique())} if len(t) else {},
        wick_top_mode=CONFIG["WICK_TOP_MODE"],
        body_wick_ratio=_dist(q.body_wick_ratio),
        leg_height_pts=_dist(m.leg_height_pts),
        retrace_frac=_dist(m.retrace_frac),
        min_leg_retrace_sensitivity={
            str(fr): {f"{s}|{'qualified' if qq else 'not_qualified'}": int(n)
                      for (s, qq), n in cnt.items()}
            for fr, cnt in sens.items()},
        zone_pre_penetration=dict(
            n_candidates=int(len(c)),
            n_penetrated=int((c.fate == "penetrated").sum()),
            penetrated_rate=round(float((c.fate == "penetrated").mean()), 4)
                             if len(c) else None,
            born_penetrated=int(c.born_penetrated.sum()),
            fates=dict(Counter(c.fate.tolist()))),
        r_available_qualified=_dist(q.r_available),
        min_1r_pass_rate=round(float(q.min_1r_pass.mean()), 4) if len(q) else None,
        market_ctrl=dict(
            ctrl_R=_dist(q.ctrl_outcome_nearest_draw_R),
            ctrl_R_filled_subset=_dist(filled.ctrl_outcome_nearest_draw_R),
            ctrl_R_unfilled_subset=_dist(unf.ctrl_outcome_nearest_draw_R)),
        limit_outcome_nearest_draw_R=_dist(filled.out_nearest_draw_R),
        target_missing_rate=round(float(q.target_price.isna().mean()), 4)
                             if len(q) else None,
    )
    return st


if __name__ == "__main__":
    main()
