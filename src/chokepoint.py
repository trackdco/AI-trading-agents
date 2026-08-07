"""Chokepoint loader — the ONLY module permitted to read raw data files.

Every consumer imports from here. Enforced by tests/test_chokepoint_guards.py
(AST taint analysis over the repo; unparseable modules are reported, not
skipped).

What this module applies, per CLAUDE.md §4:
  * cleaning: symbol filtering (calendar spreads share the feed — defect #9),
    fixed-point price-scale normalisation
  * the clock correction for the FLOORED book-snapshot families (defect #2):
    ts_event is minute-floored; the true observation time is ts_recv,
    ~60s later. Correction is fingerprint-guarded in BOTH directions — a file
    that does not show the floored fingerprint is refused, because applying a
    correction to data that doesn't need it is the same size error as the one
    it fixes.
  * the sealed-path guard: any file whose UTC date-span intersects a span in
    docs/sealed_spans.json raises SealedPathError unless the caller passes
    authorize_sealed=True. Guards refuse; they don't warn.

Empirical conventions this loader encodes (evidence: docs/conventions.md,
reproduce: scripts/verify_conventions.py):
  * OHLCV 1m bars are START-labelled: bar stamped T spans [T, T+60s).
  * Book snapshot row stamped T is the last book update inside [T, T+60s),
    observed at ts_recv (median T+59.9s).
"""

from __future__ import annotations

import csv
import glob
import io
import json
import os
from datetime import datetime, timezone

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEALED_SPANS_PATH = os.path.join(_REPO, "docs", "sealed_spans.json")

OHLCV_ARCHIVES = {
    "arch1": "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
    "arch2": "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
    "arch3": "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
    "arch4": "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst",
}

BOOK_FAMILIES = {
    # family -> glob pattern (relative to repo root)
    "london": "glbx-mdp3-*.mbp-10_condensed.csv",
    "ny2025": "condensed_glbx-mdp3-*.mbp-10.csv",
    "ny2026": "condensed_GLBX-20260720-*.csv",
}

# Clock verdicts established empirically on 2026-08-07.
# Evidence and reproduce command: docs/conventions.md §3.
CLOCK_STATUS = {
    "arch1": "UNVERIFIABLE",   # no independent clock covers 2023-01..2024-12
    "arch2": "UNVERIFIABLE",   # no independent clock; 100% row-identical to arch1 on 2025-01..2025-02 overlap
    "arch3": "CLEAN",          # verified against book ts_recv, 78 clean days, median error 1 tick
    "arch4": "CLEAN",          # verified against book ts_recv, 27 clean days, median error <= 0.375 pt
    "london": "FLOORED",       # ts_event minute-floored; 99.97% of rows ts_recv-ts_event in [55,61]s
    "ny2025": "FLOORED",       # 99.90% in [55,61]s
    "ny2026": "FLOORED",       # 99.93% in [55,61]s
    "hand_log": "UNVERIFIABLE",  # single clock, human-recorded
}


class SealedPathError(RuntimeError):
    """Raised when a load touches a sealed span without explicit authorisation."""


class ClockFingerprintError(RuntimeError):
    """Raised when a book file does not show the FLOORED fingerprint the
    correction assumes (or shows it where it must not)."""


def _sealed_spans():
    if not os.path.exists(SEALED_SPANS_PATH):
        return []
    with open(SEALED_SPANS_PATH) as f:
        return json.load(f)["sealed"]


def _check_sealed(dates, source_name, authorize_sealed):
    """dates: iterable of 'YYYY-MM-DD' strings the load will expose."""
    spans = _sealed_spans()
    if not spans:
        return
    hits = []
    for span in spans:
        lo, hi = span["start"], span["end"]
        touched = sorted(d for d in dates if lo <= d <= hi)
        if touched:
            hits.append((span, touched[0], touched[-1]))
    if hits and not authorize_sealed:
        detail = "; ".join(
            f"sealed {s['start']}..{s['end']} ({s.get('reason', 'no reason recorded')}), touched {a}..{b}"
            for s, a, b in hits
        )
        raise SealedPathError(
            f"load of '{source_name}' touches sealed span(s): {detail}. "
            f"Pass authorize_sealed=True only with a written, pre-declared look."
        )


def _ts(s):
    """Parse a raw timestamp: ISO string, or (possibly scientific) nanoseconds."""
    if ":" in s:
        return datetime.fromisoformat(s.replace(" ", "T")).timestamp()
    return float(s) / 1e9


def _px(s):
    """Normalise price scale: Databento fixed-point 1e-9 or plain decimal."""
    v = float(s)
    return v / 1e9 if v > 1e6 else v


def load_ohlcv_1m(archive, *, outrights_only=True, date_range=None, authorize_sealed=False):
    """Yield normalised 1m bars from one OHLCV archive.

    Bar dict: ts_open (epoch seconds, UTC; bar spans [ts_open, ts_open+60)),
    date ('YYYY-MM-DD' of ts_open, UTC), symbol, open, high, low, close,
    volume.

    date_range: optional ('YYYY-MM-DD', 'YYYY-MM-DD') inclusive filter applied
    at read time. Rows are buffered per archive so the sealed-span check runs
    against the actual dates present before anything is yielded.
    """
    fn = os.path.join(_REPO, OHLCV_ARCHIVES[archive])
    rows = []
    with open(fn, "rb") as f:
        import zstandard

        rd = csv.DictReader(
            io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(f))
        )
        for row in rd:
            sym = row["symbol"]
            if outrights_only and "-" in sym:
                continue
            if date_range and not (date_range[0] <= row["ts_event"][:10] <= date_range[1]):
                continue
            t = _ts(row["ts_event"])
            rows.append(
                {
                    "ts_open": t,
                    "date": row["ts_event"][:10],
                    "symbol": sym,
                    "open": _px(row["open"]),
                    "high": _px(row["high"]),
                    "low": _px(row["low"]),
                    "close": _px(row["close"]),
                    "volume": int(row["volume"]),
                }
            )
    _check_sealed({r["date"] for r in rows}, f"ohlcv:{archive}", authorize_sealed)
    yield from rows


def front_month_by_day(bars_iter):
    """Deterministic front-month per UTC date: max summed volume among
    outrights; ties broken by ascending symbol (stable sort — defect #11).

    Returns {date: symbol}. NOTE: diverges from the vendor's NQ.v.0 continuous
    mapping during quarterly roll weeks; the 10 known divergence days are
    listed in docs/conventions.md §5.
    """
    vol = {}
    for b in bars_iter:
        if "-" in b["symbol"]:
            continue
        vol.setdefault(b["date"], {})
        vol[b["date"]][b["symbol"]] = vol[b["date"]].get(b["symbol"], 0) + b["volume"]
    return {
        d: sorted(sym_vol.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for d, sym_vol in vol.items()
    }


_FLOOR_LO, _FLOOR_HI = 55.0, 61.0

# Populated by each load_book_minutes call. Dropped rows are REPORTED here,
# never silently discarded — a check that skips files passes vacuously.
last_load_stats = {"rows_served": 0, "rows_dropped_unparseable": 0, "dropped_by_file": {}}


def load_book_minutes(family, *, authorize_sealed=False, _paths=None):
    """Yield normalised book snapshots for one family, clock-corrected.

    Snapshot dict: ts_true (epoch seconds, from ts_recv — the only valid
    observation time), minute_label_raw (the floored ts_event: NEVER use as a
    time; kept only for joining back to raw rows), date, bids/asks as lists of
    (price, size) from level 00..09, symbol.

    Fingerprint guard, per file: median(ts_recv - ts_event) must lie in
    [55, 61]s — the FLOORED signature this correction exists for. A file
    outside the fingerprint is refused (ClockFingerprintError): the correction
    must not be applied to data that doesn't need it.
    """
    pattern = _paths if _paths is not None else sorted(
        glob.glob(os.path.join(_REPO, BOOK_FAMILIES[family]))
    )
    last_load_stats["rows_served"] = 0
    last_load_stats["rows_dropped_unparseable"] = 0
    last_load_stats["dropped_by_file"] = {}
    out = []
    for fn in pattern:
        offs = []
        rows = []
        with open(fn) as f:
            for row in csv.DictReader(f):
                ev, rc = _ts(row["ts_event"]), _ts(row["ts_recv"])
                offs.append(rc - ev)
                rows.append((ev, rc, row))
        if not rows:
            continue
        offs.sort()
        med = offs[len(offs) // 2]
        if not (_FLOOR_LO <= med <= _FLOOR_HI):
            raise ClockFingerprintError(
                f"{os.path.basename(fn)}: median(ts_recv - ts_event) = {med:.3f}s "
                f"is outside the FLOORED fingerprint [{_FLOOR_LO}, {_FLOOR_HI}]s. "
                f"Refusing to serve this file through the floored-clock correction."
            )
        for ev, rc, row in rows:
            bids, asks = [], []
            ok = True
            for i in range(10):
                try:
                    # sizes are int-typed in most files, float-typed ('1.0') in
                    # the two NQ.c.0 roll-Friday files — int(float()) covers both
                    bids.append((_px(row[f"bid_px_{i:02d}"]), int(float(row[f"bid_sz_{i:02d}"]))))
                    asks.append((_px(row[f"ask_px_{i:02d}"]), int(float(row[f"ask_sz_{i:02d}"]))))
                except (ValueError, KeyError):
                    ok = False
                    break
            if not ok:
                last_load_stats["rows_dropped_unparseable"] += 1
                last_load_stats["dropped_by_file"].setdefault(
                    os.path.basename(fn), 0
                )
                last_load_stats["dropped_by_file"][os.path.basename(fn)] += 1
                continue
            out.append(
                {
                    "ts_true": rc,
                    "minute_label_raw": ev,
                    "date": row["ts_event"][:10],
                    "symbol": row.get("symbol", ""),
                    "bids": bids,
                    "asks": asks,
                }
            )
    last_load_stats["rows_served"] = len(out)
    _check_sealed({r["date"] for r in out}, f"book:{family}", authorize_sealed)
    yield from out


def load_hand_log(*, authorize_sealed=False):
    """Yield rows of the February 2026 manual trade log (UNVERIFIABLE clock)."""
    fn = os.path.join(_REPO, "data", "reference", "feb2026_hand_log.csv")
    with open(fn, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    _check_sealed({"2026-02-01"}, "hand_log", authorize_sealed)
    yield from rows


def load_condition_report():
    """Databento condition report (metadata, not market data)."""
    with open(os.path.join(_REPO, "condition.json")) as f:
        return json.load(f)
