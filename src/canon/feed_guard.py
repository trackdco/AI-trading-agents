"""Feed robustness + warm-start + serve loop (LIVE-STACK live-path hardening).

Everything a live bar feed must survive before it drives real money, unit-tested against
synthetic sequences. Works entirely in tz-aware UTC so it is DST-safe (interval arithmetic
never touches a wall clock). No live transport here — this wraps whatever source the DTC
adapter provides.

  FeedGuard   : dedup, strict ordering (late/out-of-order bars dropped, never a rewind), gap
                detection (records the missing window for backfill), stall detection.
  warm_start  : preload recent history into the ingestor so tape/bars/book are warm before
                the first live bar — no cold-start weeks of wrong levels.
  serve       : the live loop — guard the feed, drive the ingestor, poll the CommandListener
                (/status, /kill) between bars, and halt on a stalled feed.
"""
from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from src.canon.ingestor import CanonIngestor, ReplaySource


class FeedGuard:
    """Clean a raw bar stream. `accept(bar)` returns the bars to actually process (0, 1)."""

    def __init__(self, interval_s: int = 60, stale_after_s: int = 180,
                 on_gap: Callable[[pd.Timestamp, pd.Timestamp], None] | None = None,
                 on_stale: Callable[[pd.Timestamp], None] | None = None):
        self.interval = pd.Timedelta(seconds=interval_s)
        self.stale_after = pd.Timedelta(seconds=stale_after_s)
        self._on_gap = on_gap
        self._on_stale = on_stale
        self._last: pd.Timestamp | None = None
        self.dupes = 0
        self.late = 0
        self.gaps: list[tuple[pd.Timestamp, pd.Timestamp]] = []
        self.stalled = False

    def accept(self, bar: dict) -> list[dict]:
        ts = pd.Timestamp(bar["ts_event"])
        if ts.tz is None:
            raise ValueError("feed bars must be tz-aware (UTC/NY) — DST-safe ordering requires it")
        if self._last is None:
            self._last = ts
            return [bar]
        if ts == self._last:                      # duplicate republish — drop
            self.dupes += 1
            return []
        if ts < self._last:                       # late / out-of-order — drop, never rewind
            self.late += 1
            return []
        if ts > self._last + self.interval:       # gap — emit, record the hole for backfill
            gap = (self._last + self.interval, ts)
            self.gaps.append(gap)
            if self._on_gap is not None:
                self._on_gap(*gap)
        self._last = ts
        return [bar]

    def check_stale(self, now: pd.Timestamp) -> bool:
        """True (and fire on_stale once) if no bar has arrived within stale_after."""
        if self._last is None:
            return False
        stale = pd.Timestamp(now) - self._last > self.stale_after
        if stale and not self.stalled:
            self.stalled = True
            if self._on_stale is not None:
                self._on_stale(self._last)
        elif not stale:
            self.stalled = False
        return stale

    def backfill(self, source_bars: pd.DataFrame) -> list[dict]:
        """Fill recorded gaps from a backfill source (e.g. a historical query on reconnect).
        Returns the missing bars, in order, that fall inside a recorded gap; clears the gaps."""
        if not self.gaps:
            return []
        out = []
        for row in source_bars.sort_values("ts_event").itertuples(index=False):
            ts = pd.Timestamp(row.ts_event)
            if any(lo <= ts < hi for lo, hi in self.gaps):
                out.append({c: getattr(row, c) for c in
                            ("ts_event", "open", "high", "low", "close", "volume")})
        self.gaps.clear()
        return out


def warm_start(ing: CanonIngestor, bars: pd.DataFrame, footprint: pd.DataFrame) -> None:
    """Preload recent history into the ingestor WITHOUT trading it, so the rolling tape/bars
    are warm before the first live bar (the live equivalent of the runner's prime())."""
    ReplaySource(bars, footprint).drive(ing)


def serve(feed_iter, ing: CanonIngestor, guard: FeedGuard, *, listener=None,
          on_bar=None, now_fn=None) -> None:
    """Live loop: guard the feed, drive the ingestor, poll the CommandListener between bars
    so /status and /kill respond, and halt-check staleness. `feed_iter` yields raw bars;
    `now_fn` supplies the clock (injectable for tests). A stalled feed stops the loop."""
    for raw in feed_iter:
        for bar in guard.accept(raw):
            ing.on_bar(bar)
            if on_bar is not None:
                on_bar(bar)
        if listener is not None:
            listener.poll_once(timeout=0)          # never blocks a bar
        if now_fn is not None and guard.check_stale(now_fn()):
            break                                  # fail-closed: stalled feed ends the loop
