"""Sierra Chart file-tail data path (Route B, docs/architecture-hermes-v2.md §2.2/§3).

Sierra's DTC server refuses to *serve* market data to an external client under the CME
non-pro / no-redistribution licence ("Market data request not allowed"); orders route fine.
So the live DATA path reads the files Sierra itself writes to local disk — reconstructing
bars from `.scid` (Intraday Data) and the order book from `.depth` (Market Depth Data).
Reading local files Sierra persists is own-use, not redistribution, and needs no compiled
study. The parser is format-first with a thin source shim so ONE record core serves all
three consumers (arch §3): a fixed historical file, a replayed file (drills / the parity
gate), and the live tail of the currently-writing file.

    parse core  :  ScidReader / DepthReader        (binary record readers, resumable)
    aggregate   :  MinuteAggregator                (ticks -> closed 1-min bar + footprint)
    drive       :  SierraFileFeed                  (merge by time -> ingestor push methods)

The reconstructed events feed the SAME CanonIngestor.on_bar / on_minute_tape / on_depth,
so the canon, spine, journaler and parity gate are all untouched.

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  PIN-ON-BOX GATE (arch §2.2 / §3 — NOT closeable offline).                            ║
║  The byte layouts and the .depth Command enum below are the PUBLICLY DOCUMENTED        ║
║  Sierra formats, but the ARCH DOC REQUIRES they be verified against the *installed*    ║
║  SC build and a captured sample day before this path is trusted with money. The        ║
║  offline tests here prove the parser inverts its own writer and that the file-tail     ║
║  path reproduces ReplaySource feature rows — they do NOT prove these bytes match real  ║
║  Sierra output. On the box: dump a real .scid/.depth, confirm HEADER/RECORD sizes and  ║
║  the Command values, adjust the constants in ONE place (here), then run the parity     ║
║  gate. Every layout constant is isolated at the top of this module for that reason.    ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import struct
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.canon.ingestor import CanonIngestor

# --------------------------------------------------------------------------- SCDateTime
# Sierra stores time as microseconds since 1899-12-30 00:00:00 UTC (the SCDateTime epoch).
_SC_EPOCH = pd.Timestamp("1899-12-30", tz="UTC")


def scdt_to_ts(micros: int) -> pd.Timestamp:
    return _SC_EPOCH + pd.Timedelta(microseconds=int(micros))


def ts_to_scdt(ts) -> int:
    return int((pd.Timestamp(ts).tz_convert("UTC") - _SC_EPOCH) // pd.Timedelta(microseconds=1))


# =========================================================================== .scid (bars/ticks)
# Header 56 bytes; record 40 bytes (s_IntradayRecord). PIN-ON-BOX.
SCID_MAGIC = b"SCID"
SCID_HEADER = struct.Struct("<4sIIHHI36s")          # magic, HdrSize, RecSize, Ver, _, UTCStart, reserve
SCID_HEADER_SIZE = 56
SCID_REC = struct.Struct("<q4f4I")                  # DateTime, O,H,L,C, NumTrades,TotVol,BidVol,AskVol
SCID_REC_SIZE = 40
assert SCID_HEADER.size == SCID_HEADER_SIZE and SCID_REC.size == SCID_REC_SIZE


@dataclass(frozen=True)
class ScidRecord:
    ts: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    num_trades: int
    total_volume: int
    bid_volume: int          # volume that traded at the bid  (sell-aggressor)
    ask_volume: int          # volume that traded at the ask  (buy-aggressor)


def write_scid(path, records: list[dict]) -> None:
    """Synthetic .scid writer — dev/test fixtures AND the box round-trip check (dump a real
    file, re-encode from parsed values, diff). Each record dict: ts + open/high/low/close +
    num_trades/total_volume/bid_volume/ask_volume (missing OHLC default to `close`)."""
    p = Path(path)
    with p.open("wb") as f:
        f.write(SCID_HEADER.pack(SCID_MAGIC, SCID_HEADER_SIZE, SCID_REC_SIZE, 1, 0, 0, b"\x00" * 36))
        for r in records:
            c = float(r["close"])
            f.write(SCID_REC.pack(
                ts_to_scdt(r["ts"]),
                float(r.get("open", c)), float(r.get("high", c)),
                float(r.get("low", c)), c,
                int(r.get("num_trades", 1)), int(r["total_volume"]),
                int(r.get("bid_volume", 0)), int(r.get("ask_volume", 0))))


class ScidReader:
    """Resumable binary reader for a .scid file. `records(offset)` yields ScidRecords from a
    byte offset (>= header) to EOF and exposes the new offset via `.offset` for tailing."""

    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self._validated = False

    def _validate(self, f) -> None:
        head = f.read(SCID_HEADER_SIZE)
        if len(head) < SCID_HEADER_SIZE:
            raise ValueError(f"{self.path}: truncated .scid header")
        magic, hsize, rsize, *_ = SCID_HEADER.unpack(head)
        if magic != SCID_MAGIC:
            raise ValueError(f"{self.path}: bad .scid magic {magic!r} (expected {SCID_MAGIC!r})")
        if (hsize, rsize) != (SCID_HEADER_SIZE, SCID_REC_SIZE):
            raise ValueError(f"{self.path}: .scid header/record size {hsize}/{rsize} != "
                             f"{SCID_HEADER_SIZE}/{SCID_REC_SIZE} — PIN-ON-BOX layout mismatch")
        self._validated = True

    def records(self, offset: int | None = None) -> Iterator[ScidRecord]:
        if not self.path.exists():
            return                                       # live tail: file not present yet -> no records
        with self.path.open("rb") as f:
            if not self._validated:
                self._validate(f)
            start = self.offset if offset is None else offset
            start = max(start, SCID_HEADER_SIZE)
            # Never read a partial (still-being-written) trailing record: floor to a record boundary.
            f.seek(0, 2)
            end = f.tell()
            n_full = (end - SCID_HEADER_SIZE) // SCID_REC_SIZE
            stop = SCID_HEADER_SIZE + n_full * SCID_REC_SIZE
            f.seek(start)
            while f.tell() + SCID_REC_SIZE <= stop:
                raw = f.read(SCID_REC_SIZE)
                dt, o, h, lo, c, nt, tv, bv, av = SCID_REC.unpack(raw)
                yield ScidRecord(scdt_to_ts(dt), o, h, lo, c, nt, tv, bv, av)
            self.offset = f.tell()


# =========================================================================== .depth (order book)
# Header 64 bytes; record 24 bytes (s_MarketDepthRecord). PIN-ON-BOX (esp. the Command enum).
DEPTH_MAGIC = b"SCDD"
DEPTH_HEADER = struct.Struct("<4sIIHH48s")          # magic, HdrSize, RecSize, Ver, _, reserve
DEPTH_HEADER_SIZE = 64
DEPTH_REC = struct.Struct("<qBBHfII")               # DateTime, Command, Flags, NumOrders, Price, Qty, _
DEPTH_REC_SIZE = 24
assert DEPTH_HEADER.size == DEPTH_HEADER_SIZE and DEPTH_REC.size == DEPTH_REC_SIZE

# Command byte -> DepthBook action. PIN-ON-BOX: confirm these values against the installed
# build (the .depth Command enum is the least-documented part of the format, arch §2.2). The
# side-in-command layout is one documented variant; if the real build carries side in `Flags`
# instead, only this table + `DepthReader._decode` change.
DCMD_CLEAR = 1
DCMD_SET_BID = 2        # insert/update a bid level (Price, Qty, NumOrders)
DCMD_SET_ASK = 3        # insert/update an ask level
DCMD_DEL_BID = 4        # remove the bid level at Price
DCMD_DEL_ASK = 5        # remove the ask level at Price
_DCMD_ACTION = {DCMD_CLEAR: "R", DCMD_SET_BID: "B", DCMD_SET_ASK: "A",
                DCMD_DEL_BID: "b", DCMD_DEL_ASK: "a"}


def write_depth(path, records: list[dict]) -> None:
    """Synthetic .depth writer — mirrors DepthReader for round-trip tests / box verification.
    Each record dict: ts, command (one of DCMD_*), price, qty, num_orders."""
    p = Path(path)
    with p.open("wb") as f:
        f.write(DEPTH_HEADER.pack(DEPTH_MAGIC, DEPTH_HEADER_SIZE, DEPTH_REC_SIZE, 1, 0, b"\x00" * 48))
        for r in records:
            f.write(DEPTH_REC.pack(
                ts_to_scdt(r["ts"]), int(r["command"]), int(r.get("flags", 0)),
                int(r.get("num_orders", 1)), float(r.get("price", 0.0)),
                int(r.get("qty", 0)), 0))


@dataclass(frozen=True)
class DepthEvent:
    ts: pd.Timestamp
    action: str              # R | B | A | b | a  (see DepthBook)
    price: float
    size: int
    ct: int                  # order count at the level (NumOrders)


class DepthReader:
    """Resumable binary reader for a .depth file → DepthBook-schema events."""

    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self._validated = False

    def _validate(self, f) -> None:
        head = f.read(DEPTH_HEADER_SIZE)
        if len(head) < DEPTH_HEADER_SIZE:
            raise ValueError(f"{self.path}: truncated .depth header")
        magic, hsize, rsize, *_ = DEPTH_HEADER.unpack(head)
        if magic != DEPTH_MAGIC:
            raise ValueError(f"{self.path}: bad .depth magic {magic!r} (expected {DEPTH_MAGIC!r})")
        if (hsize, rsize) != (DEPTH_HEADER_SIZE, DEPTH_REC_SIZE):
            raise ValueError(f"{self.path}: .depth header/record size {hsize}/{rsize} != "
                             f"{DEPTH_HEADER_SIZE}/{DEPTH_REC_SIZE} — PIN-ON-BOX layout mismatch")
        self._validated = True

    @staticmethod
    def _decode(dt: int, cmd: int, flags: int, num_orders: int, price: float,
                qty: int) -> DepthEvent:
        action = _DCMD_ACTION.get(cmd)
        if action is None:
            raise ValueError(f".depth: unknown Command {cmd} — PIN-ON-BOX enum mismatch")
        return DepthEvent(scdt_to_ts(dt), action, float(price), int(qty), int(num_orders))

    def records(self, offset: int | None = None) -> Iterator[DepthEvent]:
        if not self.path.exists():
            return                                       # live tail: file not present yet -> no records
        with self.path.open("rb") as f:
            if not self._validated:
                self._validate(f)
            start = self.offset if offset is None else offset
            start = max(start, DEPTH_HEADER_SIZE)
            f.seek(0, 2)
            end = f.tell()
            n_full = (end - DEPTH_HEADER_SIZE) // DEPTH_REC_SIZE
            stop = DEPTH_HEADER_SIZE + n_full * DEPTH_REC_SIZE
            f.seek(start)
            while f.tell() + DEPTH_REC_SIZE <= stop:
                dt, cmd, flags, no, price, qty, _res = DEPTH_REC.unpack(f.read(DEPTH_REC_SIZE))
                yield self._decode(dt, cmd, flags, no, price, qty)
            self.offset = f.tell()


# =========================================================================== minute aggregation
@dataclass
class MinuteAggregator:
    """Fold .scid tick (or bar) records into CLOSED 1-minute bars + footprint minutes.

    A minute is emitted only when a record from a LATER minute arrives (or on explicit
    `flush()`), so a forming minute is never delivered (feed.py contract). Per closed minute:
      bar   = {ts_event, open, high, low, close, volume}   (OHLC from records, vol = Σ volume)
      tape  = (ts, delta, vol, vwp)   delta = Σ(ask_vol − bid_vol) = signed CVD increment,
              vwp = Σ(close·vol)/Σvol = per-minute VWAP proxy.

    NOTE (PIN-ON-BOX, parity gate): the aggressor delta sign (ask−bid) must be reconciled
    against the backtest — the repo already documents that a naive CVD is the *negative* of
    ours (docs/FINDING-cvd-confirm-vs-fade-signcheck.md). Flip here if the gate says so.
    """
    _cur_min: pd.Timestamp | None = None
    _o: float = 0.0
    _h: float = 0.0
    _l: float = 0.0
    _c: float = 0.0
    _vol: int = 0
    _delta: int = 0
    _pxvol: float = 0.0

    def _reset(self, rec: ScidRecord, minute: pd.Timestamp) -> None:
        self._cur_min = minute
        self._o, self._h, self._l, self._c = rec.open, rec.high, rec.low, rec.close
        self._vol, self._delta, self._pxvol = 0, 0, 0.0
        self._accum(rec)

    def _accum(self, rec: ScidRecord) -> None:
        self._h = max(self._h, rec.high)
        self._l = min(self._l, rec.low)
        self._c = rec.close
        self._vol += rec.total_volume
        self._delta += rec.ask_volume - rec.bid_volume
        self._pxvol += rec.close * rec.total_volume

    def _emit(self) -> dict:
        m = self._cur_min
        vwp = self._pxvol / self._vol if self._vol else self._c
        return {"ts": m,
                "bar": {"ts_event": m, "open": self._o, "high": self._h, "low": self._l,
                        "close": self._c, "volume": float(self._vol)},
                "tape": {"delta": float(self._delta), "vol": float(self._vol), "vwp": vwp}}

    def push(self, rec: ScidRecord) -> list[dict]:
        """Feed one record; return the list of newly-CLOSED minutes (0 or 1)."""
        minute = pd.Timestamp(rec.ts).floor("min")
        if self._cur_min is None:
            self._reset(rec, minute)
            return []
        if minute == self._cur_min:
            self._accum(rec)
            return []
        if minute < self._cur_min:                  # out-of-order tick — drop, never rewind
            return []
        closed = self._emit()
        self._reset(rec, minute)
        return [closed]

    def flush(self) -> list[dict]:
        """Close the buffered (final) minute. Batch mode only — a live tail must NOT flush the
        forming minute, or it would deliver an incomplete bar."""
        if self._cur_min is None:
            return []
        closed = self._emit()
        self._cur_min = None
        return [closed]


# =========================================================================== feed-lag meter
@dataclass
class FeedLag:
    """Observed file-append latency for the Route-B live tail (arch §2.2; FEED-LAG directive).

    Route B reads bars from the file Sierra flushes to disk, so a bar's record only becomes
    readable AFTER Sierra flushes it — a write-latency floor (the configured
    'Intraday File Flush Time in Milliseconds', 1000 on the box; the SC default 0 ≈ 5 s) with
    NO backtest equivalent. We MEASURE the wall-clock delta between a bar's close instant and
    the moment its record is first read on a live poll, journal it per bar, and report a
    summary. We deliberately do NOT 'correct' for it: a time-shifted feed would silently
    diverge from the frozen backtest — the honest move is to surface the number and gate on it.
    """
    flush_ms: int | None = None                        # configured Sierra flush (report baseline)
    samples: list[float] = field(default_factory=list)  # per-bar lag, seconds

    def add(self, lag_s: float) -> None:
        self.samples.append(float(lag_s))

    def summary(self) -> dict:
        """Compact stat for the reconciliation-day gate's reported line item."""
        s = self.samples
        if not s:
            return {"n": 0, "flush_ms": self.flush_ms}
        ss = sorted(s)

        def _pct(p: float) -> float:
            return ss[min(len(ss) - 1, int(round(p * (len(ss) - 1))))]

        return {"n": len(s), "flush_ms": self.flush_ms,
                "min_s": round(ss[0], 4), "median_s": round(_pct(0.5), 4),
                "mean_s": round(sum(s) / len(s), 4), "p95_s": round(_pct(0.95), 4),
                "max_s": round(ss[-1], 4)}


def _utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


# =========================================================================== the feed (shim)
@dataclass
class SierraFileFeed:
    """Source shim over the parse core (arch §3): one code path for a fixed historical file,
    a replay, and a live tail. Merges .scid-derived minutes and .depth events by time and
    drives a CanonIngestor via its existing push methods.

    Modes:
      drive_batch(ing)      read every currently-available record to EOF, emit all closed
                            minutes (flushing the last), apply all depth events. Historical
                            file / replay / the parity gate.
      poll(ing)            read only records appended since the last poll; emit CLOSED minutes
                            (the forming minute stays buffered) and apply new depth events.
                            Call repeatedly against a growing file for the live tail.
    """
    scid_path: str | Path
    depth_path: str | Path | None = None
    # --- feed-lag instrumentation (live tail only; see FeedLag) -------------------------
    clock: Callable[[], pd.Timestamp] | None = None    # wall-clock source, injectable for tests
    on_lag: Callable[[dict], None] | None = None        # per-bar lag journal sink (fail-soft)
    flush_ms: int | None = None                         # configured Sierra flush, for the report
    _scid: ScidReader = field(init=False)
    _depth: DepthReader | None = field(init=False, default=None)
    _agg: MinuteAggregator = field(init=False, default_factory=MinuteAggregator)
    lag: FeedLag = field(init=False)

    def __post_init__(self):
        self._scid = ScidReader(self.scid_path)
        if self.depth_path is not None:
            self._depth = DepthReader(self.depth_path)
        self.lag = FeedLag(flush_ms=self.flush_ms)
        self._clock = self.clock or _utc_now

    # ---- feed-lag: wall-clock delta between a bar's close and when its record is read -----
    def _record_lag(self, minute_ts, now: pd.Timestamp) -> None:
        """A closed minute became readable at `now`. Its bar CLOSES one minute after the
        minute's open label (the instant the last second of the minute elapses), so the
        observed append latency is `now − (minute + 1min)`. Journal per bar; accumulate for
        the summary. Measured on the live tail only (poll) — in batch replay the wall clock
        is unrelated to the historical bar times, so lag there is meaningless and not taken."""
        close_ts = pd.Timestamp(minute_ts) + pd.Timedelta(minutes=1)
        lag_s = (now - close_ts).total_seconds()
        self.lag.add(lag_s)
        if self.on_lag is not None:
            try:
                self.on_lag({"bar_close": close_ts.isoformat(), "readable_at": now.isoformat(),
                             "lag_s": round(lag_s, 4)})
            except Exception:  # noqa: BLE001 — lag journaling never breaks the feed
                pass

    # ---- one merged, time-ordered pass over whatever records are available now ----------
    def _pull(self, flush: bool, measure_lag: bool = False) -> list[dict]:
        """Read available records from both files, return merged time-ordered events:
        {'kind':'depth', 'ts', 'event':{...}} and {'kind':'minute', 'ts', 'bar', 'tape'}.
        `measure_lag` records per-bar file-append latency (live tail; poll only)."""
        events: list[tuple] = []
        now = self._clock() if measure_lag else None
        for rec in self._scid.records():
            for closed in self._agg.push(rec):
                if measure_lag:
                    self._record_lag(closed["ts"], now)
                events.append((closed["ts"], 1, {"kind": "minute", **closed}))
        if flush:
            for closed in self._agg.flush():
                events.append((closed["ts"], 1, {"kind": "minute", **closed}))
        if self._depth is not None:
            for de in self._depth.records():
                ev = {"action": de.action, "price": de.price, "size": de.size, "ct": de.ct}
                # depth ordered before a same-timestamp minute close (0 < 1) so the book is
                # current as-of the bar; feature_row reads the latest book snapshot anyway.
                events.append((de.ts, 0, {"kind": "depth", "ts": de.ts, "event": ev}))
        events.sort(key=lambda e: (e[0], e[1]))
        return [e[2] for e in events]

    def _apply(self, ing: CanonIngestor, merged: list[dict]) -> int:
        for e in merged:
            if e["kind"] == "minute":
                ing.on_bar(e["bar"])
                ing.on_minute_tape(e["ts"], e["tape"]["delta"], e["tape"]["vol"], e["tape"]["vwp"])
            else:
                ing.on_depth(e["event"])
        return len(merged)

    def drive_batch(self, ing: CanonIngestor) -> int:
        return self._apply(ing, self._pull(flush=True))

    def poll(self, ing: CanonIngestor) -> int:
        """Consume records appended since the last poll (live tail). Returns events applied.
        Records per-bar file-append latency (FeedLag) against the wall clock as it goes."""
        return self._apply(ing, self._pull(flush=False, measure_lag=True))

    def poll_events(self) -> list[dict]:
        """Live-tail poll returning the merged, time-ordered closed-minute + depth events
        (recording per-bar lag) WITHOUT applying them to an ingestor. A fan-out loop uses this
        to dispatch each event to MULTIPLE consumers (champion Bar path + canon ingestor) from
        a single read of the files. Event dicts: {'kind':'minute','ts','bar','tape'} and
        {'kind':'depth','ts','event'}."""
        return self._pull(flush=False, measure_lag=True)

    # ---- roll / per-day retargeting (Route-B live loop) ---------------------------------
    def retarget_depth(self, depth_path) -> None:
        """Point at a new `.depth` file. `.depth` is per-DAY, so the live loop calls this at
        every session boundary (fresh reader/offset for the new day's file). The `.scid`
        reader and the minute aggregator are untouched — the intraday file spans days."""
        self.depth_path = depth_path
        self._depth = DepthReader(depth_path) if depth_path is not None else None

    def retarget_scid(self, scid_path, depth_path=None) -> None:
        """Point at a new `.scid` (and optionally `.depth`) — a CONTRACT ROLL. The `.scid` is
        per-contract, so a roll is a whole new file: reset the reader AND the minute aggregator
        (any forming minute belonged to the old contract). Lag stats carry over."""
        self.scid_path = scid_path
        self._scid = ScidReader(scid_path)
        self._agg = MinuteAggregator()
        if depth_path is not None:
            self.retarget_depth(depth_path)

    def lag_summary(self) -> dict:
        """Observed file-append latency summary for the reconciliation-day report (FeedLag).
        Reported, never corrected. Empty (n=0) until the live tail has polled at least one bar."""
        return self.lag.summary()
