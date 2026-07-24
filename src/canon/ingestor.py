"""Canon ingestor orchestration (LIVE-STACK Step 4) — replay source; live DTC is a seam.

Maintains rolling state continuously and, on a trigger (a candidate fill at a level),
assembles that trade's feature row with the SAME definitions as the backtest
(src/canon/features.py). State kept live, not a file rewritten each tick:

  * minute tape (footprint) — per closed minute: delta, vol, vwp; plus the session-anchored
    running cum (= session CVD), runmin, runmax, hm — exactly the columns
    scripts/trade_matrix.py derives from output/fp_minutes.parquet.
  * bars + daily-VWAP bands — for the VWAP-geometry family.
  * order book — src/canon/book.OrderBook, updated from MBO/depth events; snapshotted
    long-form for the depth family.

The SOURCE is pluggable. `ReplaySource` streams historical minutes from the repo's data.
`<<LIVE DTC FEED>>` (Sierra Chart over DTC) drops in behind the same push methods — marked
in `feed_seam` below; NOT built here.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import time as dtime

import pandas as pd

from src.canon.book import OrderBook
from src.canon.features import depth_at, tape_features, vwap_geometry
from src.engine.data import _session_date
from src.engine.indicators import daily_vwap

NY = "America/New_York"
_BOUNDARY = dtime(18, 0)


# --------------------------------------------------------------------------- minute tape
@dataclass
class MinuteTape:
    """Footprint minutes with session-anchored running state (matches fp_minutes prep in
    scripts/trade_matrix.py: cum = cumsum(delta) per sday, runmin/runmax = cummin/cummax)."""
    rows: list[dict] = field(default_factory=list)
    _cum: dict[str, float] = field(default_factory=dict)
    _runmin: dict[str, float] = field(default_factory=dict)
    _runmax: dict[str, float] = field(default_factory=dict)

    def add_minute(self, ts: pd.Timestamp, delta: float, vol: float, vwp: float) -> None:
        ts = pd.Timestamp(ts)
        sday = str(_session_date(pd.Series([ts]), _BOUNDARY).iloc[0])
        cum = self._cum.get(sday, 0.0) + delta
        self._cum[sday] = cum
        self._runmin[sday] = min(self._runmin.get(sday, cum), cum)
        self._runmax[sday] = max(self._runmax.get(sday, cum), cum)
        self.rows.append({"ts_event": ts, "sday": sday, "delta": float(delta),
                          "vol": float(vol), "vwp": float(vwp),
                          "hm": ts.tz_convert(NY).hour * 60 + ts.tz_convert(NY).minute,
                          "cum": cum, "runmin": self._runmin[sday],
                          "runmax": self._runmax[sday]})

    def frame(self) -> pd.DataFrame:
        df = pd.DataFrame(self.rows)
        if not df.empty:
            df = df.set_index("ts_event")
        return df

    def day_median_vol(self, sday: str) -> float:
        v = [r["vol"] for r in self.rows if r["sday"] == sday]
        return float(pd.Series(v).median()) if v else float("nan")


# --------------------------------------------------------------------------- the ingestor
class CanonIngestor:
    """Rolling live state + on-trigger feature-row assembly. Push methods are what a feed
    calls; the same methods serve replay and (later) the live DTC feed."""

    def __init__(self) -> None:
        self.tape = MinuteTape()
        self.book = OrderBook()
        self._bars: list[dict] = []
        self._vwap_cache: pd.DataFrame | None = None

    # ---- push methods (feed-agnostic) --------------------------------------
    def on_bar(self, bar: dict) -> None:
        """One closed 1-minute OHLCV bar (ts_event tz-aware, open/high/low/close/volume)."""
        self._bars.append(dict(bar))
        self._vwap_cache = None                      # invalidate: bar history changed

    def on_minute_tape(self, ts, delta: float, vol: float, vwp: float) -> None:
        """One closed minute of footprint (signed delta, total volume, per-minute VWAP)."""
        self.tape.add_minute(ts, delta, vol, vwp)

    def on_depth(self, event: dict) -> None:
        """One MBO/depth event (see src/canon/book.OrderBook.apply)."""
        self.book.apply(event)

    # ---- VWAP bands (computed on the accumulated bars) ----------------------
    def _bars_with_vwap(self) -> pd.DataFrame:
        if self._vwap_cache is None:
            bars = pd.DataFrame(self._bars)
            ind = daily_vwap(bars, bands=[1])
            bt = bars.ts_event.dt.tz_convert(NY)
            self._vwap_cache = bars.assign(
                mi=bt.dt.floor("min"), hm=bt.dt.hour * 60 + bt.dt.minute,
                vw=ind["vwap"].to_numpy(), up1=ind["upper_1"].to_numpy())
        return self._vwap_cache

    # ---- on a trigger: assemble the feature row ----------------------------
    def feature_row(self, fill_ts, entry: float, direction: str) -> dict:
        """Feature row for a candidate fill — tape/CVD + VWAP-geometry + depth families,
        all via src/canon/features.py (identical definitions to the backtest). Uses only
        state up to `fill_ts` — no lookahead."""
        fill = pd.Timestamp(fill_ts)
        f: dict = {}

        tape = self.tape.frame()
        if not tape.empty:
            upto = tape[tape.index < fill]
            sday = str(_session_date(pd.Series([fill]), _BOUNDARY).iloc[0])
            f.update(tape_features(upto, direction, fill, self.tape.day_median_vol(sday)))

        if self._bars:
            b = self._bars_with_vwap()
            pre = b[b.mi < fill]
            f.update(vwap_geometry(pre, entry, direction))

        book = pd.DataFrame(self.book.long_form())
        if not book.empty:
            book["ts"] = fill                        # current snapshot is as-of the fill
            f.update(depth_at(book, fill, entry, direction))
        return f


# --------------------------------------------------------------------------- replay source
class ReplaySource:
    """Stream historical minutes (bar + footprint + optional depth snapshot) into an
    ingestor, in chronological order. `depth_rows(ts)` may return long-form book rows to
    seed the book for a day (the batch depth CSVs are per-snapshot, not per-event)."""

    def __init__(self, bars: pd.DataFrame, footprint: pd.DataFrame):
        self.bars = bars.sort_values("ts_event").reset_index(drop=True)
        self.footprint = footprint.sort_index()

    def stream(self) -> Iterator[dict]:
        fp = self.footprint
        for row in self.bars.itertuples(index=False):
            ts = pd.Timestamp(row.ts_event)
            yield {"kind": "bar", "ts": ts, "bar": {c: getattr(row, c) for c in
                   ("ts_event", "open", "high", "low", "close", "volume")}}
            if ts in fp.index:
                r = fp.loc[ts]
                yield {"kind": "tape", "ts": ts, "delta": float(r.delta),
                       "vol": float(r.vol), "vwp": float(r.vwp)}

    def drive(self, ing: CanonIngestor) -> None:
        for ev in self.stream():
            if ev["kind"] == "bar":
                ing.on_bar(ev["bar"])
            elif ev["kind"] == "tape":
                ing.on_minute_tape(ev["ts"], ev["delta"], ev["vol"], ev["vwp"])


# --------------------------------------------------------------------------- live feed seam
def feed_seam() -> None:
    """<<LIVE DTC FEED ADAPTER>> — Sierra Chart over DTC drops in HERE. A real-time source
    calls ingestor.on_bar / on_minute_tape / on_depth as closed bars, footprint minutes, and
    MBO events arrive. NOT built (needs the DTC client, src/desk/dtc_client.py). The ingestor
    above is transport-agnostic, so only this adapter changes."""
    raise NotImplementedError("live DTC feed not built — use ReplaySource (offline)")
