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
from src.canon.features import (
    badpa_features,
    bp5opp,
    depth_at,
    london_session_features,
    lon_slope_d,
    on_extreme_age_day,
    on_extreme_age_trade,
    opp5,
    tape_features,
    vwap_geometry,
)
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

    def __init__(self, book=None) -> None:
        self.tape = MinuteTape()
        # Book is pluggable so the same ingestor serves both data paths with no change to
        # on_depth / feature_row: OrderBook (MBO, order-by-order — Databento/replay) or
        # DepthBook (MBP level data — Sierra .depth file-tail, Route B). Both expose the
        # same apply / long_form interface.
        self.book = book if book is not None else OrderBook()
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

    # ---- frame accessors (for the trade lifecycle / exit driver) -------------
    def bars_frame(self) -> pd.DataFrame:
        """The accumulated engine-shaped 1m bars (ts_event/open/high/low/close/volume) —
        the frame the exit driver drives simulate() over."""
        return pd.DataFrame(self._bars)

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
    def feature_row(self, fill_ts, entry: float, direction: str,
                    trigger_times=None) -> dict:
        """Feature row for a candidate fill — tape/CVD + VWAP-geometry + depth families,
        plus the gold/London families, all via src/canon/features.py (identical definitions
        to the backtest). Uses only state up to `fill_ts` — no lookahead.

        `trigger_times`: the day's engine trigger stamps, for `trigdens_30`. Omitted (None)
        simply leaves that key absent — the ingestor does not own trigger detection, so the
        caller supplies them or the gold TRIG check reads NaN and stands itself down."""
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

        f.update(self._gold_london_features(fill, entry, direction, trigger_times))
        return f

    def _gold_london_features(self, fill: pd.Timestamp, entry: float, direction: str,
                              trigger_times) -> dict:
        """The gold + London families (P2). Every window ends at fill-1min, same as above.

        Kept separate from the three core families because these need frames the others
        don't (session-anchored bars, the overnight tape, the day's trigger stamps) and any
        of them may legitimately be unavailable early in a session — a missing input yields
        a missing key here rather than a fabricated number, so a scorer sees NaN and its
        `.where(...notna())` guard stands the check down instead of scoring on a guess.

        BOTH `on_extreme_age` forms are emitted under DISTINCT keys: the gold scorer and the
        London scorer were fit against different definitions that share that column name
        upstream (see src/canon/features.py). Callers pick the one their lane needs; nothing
        here silently chooses for them."""
        f: dict = {}
        tape = self.tape.frame()
        if tape.empty or not self._bars:
            return f
        upto_tape = tape[tape.index < fill]
        bars = self._bars_with_vwap().set_index("mi").sort_index()
        upto_bars = bars.loc[: fill - pd.Timedelta(minutes=1)]

        f.update(badpa_features(upto_bars, upto_tape, entry, fill,
                                trigger_times=trigger_times))
        f["bp5opp"] = bp5opp(upto_tape, direction, fill)
        f["opp5"] = opp5(upto_tape, direction, fill)

        sday = str(_session_date(pd.Series([fill]), _BOUNDARY).iloc[0])
        sess_tape = upto_tape[upto_tape.get("sday", sday) == sday] \
            if "sday" in upto_tape else upto_tape
        f["lon_slope_d"] = lon_slope_d(sess_tape, direction)

        hm = upto_tape.index.hour * 60 + upto_tape.index.minute
        f["on_extreme_age_day"] = on_extreme_age_day(upto_tape[(hm >= 1080) | (hm < 480)])

        sess0 = (fill - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
        sess_bars = upto_bars.loc[sess0:]
        f["on_extreme_age_trade"] = on_extreme_age_trade(sess_bars, entry, fill)
        f.update(london_session_features(upto_tape.loc[sess0:], sess_bars, entry, sess0))
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
def live_feed(scid_path, depth_path=None, **kw):
    """<<LIVE DATA ADAPTER — Route B: tail Sierra's .scid/.depth files>>.

    Sierra's DTC server will not *serve* market data to an external client under the CME
    non-pro / no-redistribution licence (orders route fine; data is rejected). So the live
    data path reads the files Sierra itself persists to local disk — unambiguous local use,
    no redistribution, no compiled study. This returns a `SierraFileFeed` (see
    src/canon/sierra_files.py) that reads .scid bars + .depth level events and calls the
    SAME on_bar / on_minute_tape / on_depth methods above — so the ingestor, canon, spine,
    journaler and parity gate are all untouched; only this adapter is new.

    Construct the ingestor with a level book for this path:  CanonIngestor(book=DepthBook()).
    """
    from src.canon.sierra_files import SierraFileFeed
    return SierraFileFeed(scid_path, depth_path, **kw)
